"""Provisioning tests

:Requirement: Provisioning

:CaseAutomation: NotAutomated

:CaseLevel: System

:CaseComponent: Provisioning

:Assignee: sganar

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import ipaddress
import re

import pytest
from box import Box
from broker.broker import Broker
from fauxfactory import gen_string
from packaging.version import Version
from wait_for import wait_for
from wrapanapi import RHEVMSystem

from robottelo import constants
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings
from robottelo.hosts import ContentHost


@pytest.fixture(scope='module')
def module_location(module_manifest_org, module_target_sat):
    # TODO: should not be needed once there is module_org_with_manifest
    """Create location associated with module_manifest_org"""
    return module_target_sat.api.Location(organization=[module_manifest_org]).create()


# use internal Capsule
@pytest.fixture(scope='module')
def provisioning_capsule(module_target_sat, module_location):
    """Return Satellite's internal capsule"""
    capsule = (
        module_target_sat.api.SmartProxy()
        .search(query={'search': f'name={module_target_sat.hostname}'})[0]
        .read()
    )
    capsule.location = [module_location]
    capsule.update(['location'])
    return capsule


@pytest.fixture(scope='module')
def provisioning_rhel_content(request, module_target_sat, module_manifest_org):
    """
    This fixture sets up kickstart repositories for a specific RHEL version
    that is specified in `request.param`.
    """
    rhel_ver = request.param
    sat = module_target_sat
    repo_names = [f'rhel{rhel_ver}']
    if int(rhel_ver) > 7:
        repo_names.append(f'rhel{rhel_ver}_aps')

    rh_repos = []
    tasks = []
    for name in repo_names:
        rh_repo_id = enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=module_manifest_org.id,
            product=constants.REPOS['kickstart'][name]['product'],
            repo=constants.REPOS['kickstart'][name]['name'],
            reposet=constants.REPOS['kickstart'][name]['reposet'],
            releasever=constants.REPOS['kickstart'][name]['version'],
        )
        # Sync step because repo is not synced by default
        rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
        task = rh_repo.sync(synchronous=False)
        tasks.append(task)
        rh_repos.append(rh_repo)
    for task in tasks:
        wait_for_tasks(
            search_query=(f'id = {task["id"]}'),
            poll_timeout=2500,
        )
        task_status = module_target_sat.api.ForemanTask(id=task['id']).poll()
        assert task_status['result'] == 'success'

    rhel_xy = Version(constants.REPOS['kickstart'][f'rhel{rhel_ver}']['version'])
    o_systems = sat.api.OperatingSystem().search(
        query={'search': f'family=Redhat and major={rhel_xy.major} and minor={rhel_xy.minor}'}
    )
    assert o_systems, f'Operating system RHEL {rhel_xy} was found'
    os = o_systems[0].read()

    # use default Environment
    lce = (
        sat.api.LifecycleEnvironment(organization=module_manifest_org)
        .search(query={'search': f'name={constants.ENVIRONMENT}'})[0]
        .read()
    )

    # use default Content View
    cv = (
        sat.api.ContentView(
            organization=module_manifest_org,
            name=constants.DEFAULT_CV,
        )
        .search()[0]
        .read()
    )

    ak = sat.api.ActivationKey(
        organization=module_manifest_org, content_view=cv, environment=lce
    ).create()

    subs = sat.api.Subscription(organization=module_manifest_org).search(
        query={'search': f'{constants.DEFAULT_SUBSCRIPTION_NAME}'}
    )
    assert subs, f'Subscription "{constants.DEFAULT_SUBSCRIPTION_NAME}" was not found'
    ak.add_subscriptions(data={'subscription_id': subs[0].id})

    # return only the first kickstart repo - RHEL X KS or RHEL X BaseOS KS
    return Box(sat=sat, os=os, ksrepo=rh_repos[0], cv=cv, lce=lce, ak=ak)


@pytest.fixture(scope='module')
def provisioning_sat(
    module_target_sat,  # TODO: add module_org_with_manifest
    provisioning_rhel_content,
    module_manifest_org,
    module_location,
    default_architecture,
    default_partitiontable,
    provisioning_capsule,
):
    """
    This fixture sets up the Satellite for PXE provisioning.
    It calls a workflow using broker to set up the network and to run satellite-installer.
    It uses the artifacts from the workflow to create all the necessary Satellite entities
    that are later used by the tests.
    """
    sat = module_target_sat
    host_root_pass = settings.provisioning.host_root_password
    pxe_loader = "PXELinux BIOS"  # TODO: Make this a fixture parameter
    provisioning_domain_name = f"{gen_string('alpha').lower()}.foo"

    broker_data_out = Broker().execute(
        workflow="configure-install-sat-provisioning-rhv",
        artifacts="last",
        target_vlan_id=settings.provisioning.vlan_id,
        target_host=sat.name,
        provisioning_dns_zone=provisioning_domain_name,
        sat_version=sat.version,
    )

    # temp mock data
    # broker_data_out = {
    #     'data_out': {
    #         'provisioning_addr_ipv4': '10.1.5.57/29',
    #         'provisioning_gw_ipv4': '10.1.5.62',
    #         'provisioning_host_range_end': '10.1.5.61',
    #         'provisioning_host_range_start': '10.1.5.58',
    #         'provisioning_iface': 'eth1',
    #         'provisioning_upstream_dns': ['10.5.30.160', '10.11.5.19'],
    #     }
    # }
    broker_data_out = Box(**broker_data_out['data_out'])
    provisioning_interface = ipaddress.ip_interface(broker_data_out.provisioning_addr_ipv4)
    provisioning_network = provisioning_interface.network
    # TODO: investigate DNS setup issue on Satellite,
    # we might need to set up Sat's DNS server as the primary one on the Sat host
    provisioning_upstream_dns_primary = (
        broker_data_out.provisioning_upstream_dns.pop()
    )  # There should always be at least one upstream DNS
    provisioning_upstream_dns_secondary = (
        broker_data_out.provisioning_upstream_dns.pop()
        if len(broker_data_out.provisioning_upstream_dns)
        else None
    )

    domain = sat.api.Domain(
        location=[module_location],
        organization=[module_manifest_org],
        dns=provisioning_capsule.id,
        name=provisioning_domain_name,
    ).create()

    subnet = sat.api.Subnet(
        location=[module_location],
        organization=[module_manifest_org],
        network=str(provisioning_network.network_address),
        mask=str(provisioning_network.netmask),
        gateway=broker_data_out.provisioning_gw_ipv4,
        from_=broker_data_out.provisioning_host_range_start,
        to=broker_data_out.provisioning_host_range_end,
        dns_primary=provisioning_upstream_dns_primary,
        dns_secondary=provisioning_upstream_dns_secondary,
        boot_mode='DHCP',
        ipam='DHCP',
        dhcp=provisioning_capsule.id,
        tftp=provisioning_capsule.id,
        template=provisioning_capsule.id,
        dns=provisioning_capsule.id,
        httpboot=provisioning_capsule.id,
        discovery=provisioning_capsule.id,
        remote_execution_proxy=[provisioning_capsule.id],
        domain=[domain.id],
    ).create()

    hostgroup = sat.api.HostGroup(
        organization=[module_manifest_org],
        location=[module_location],
        architecture=default_architecture,
        domain=domain,
        content_source=provisioning_capsule.id,
        content_view=provisioning_rhel_content.cv,
        kickstart_repository=provisioning_rhel_content.ksrepo,
        lifecycle_environment=provisioning_rhel_content.lce,
        root_pass=host_root_pass,
        operatingsystem=provisioning_rhel_content.os,
        ptable=default_partitiontable,
        subnet=subnet,
        pxe_loader=pxe_loader,
        group_parameters_attributes=[  # assign AK in order the hosts to be subscribed
            {
                'name': 'kt_activation_keys',
                'parameter_type': 'string',
                'value': provisioning_rhel_content.ak,
            }
        ],
    ).create()

    return Box(sat=sat, hostgroup=hostgroup, subnet=subnet)


@pytest.fixture()
def provisioning_contenthost():
    """Fixture to check out blank VM"""
    vlan_id = settings.provisioning.vlan_id
    vm_firmware = "bios"  # TODO: Make this a fixture parameter
    cd_iso = ""  # TODO: Make this a fixture parameter
    with Broker(
        workflow="deploy-configure-pxe-provisioning-host-rhv",
        host_classes={'host': ContentHost},
        target_vlan_id=vlan_id,
        target_vm_firmware=vm_firmware,
        target_vm_cd_iso=cd_iso,
        blank=True,
    ) as host:
        yield host


@pytest.mark.stubbed
@pytest.mark.on_premises_provisioning
@pytest.mark.tier3
def test_rhel_pxe_provisioning_on_libvirt():
    """Provision RHEL system via PXE on libvirt and make sure it behaves

    :id: a272a594-f758-40ef-95ec-813245e44b63

    :steps:
        1. Provision RHEL system via PXE on libvirt
        2. Check that resulting host is registered to Satellite
        3. Check host can install package from Satellite

    :expectedresults:
        1. Host installs
        2. Host is registered to Satellite and subscription status is 'Success'
        3. Host can install package from Satellite
    """


# @pytest.mark.on_premises_provisioning
@pytest.mark.parametrize(
    "provisioning_rhel_content",
    [v for v in settings.supportability.content_hosts.rhel.versions if re.match('^[7-9]$', str(v))],
    indirect=True,
)
def test_rhel_pxe_provisioning_on_rhv(
    request,
    provisioning_sat,
    module_manifest_org,
    module_location,
    provisioning_contenthost,
    provisioning_rhel_content,
):
    """Provision RHEL system via PXE on RHV and make sure it behaves

    :id: 798b8d0e-e2c8-4860-a3f0-4f99ea0529bf

    :steps:
        1. Provision RHEL system via PXE on RHV
        2. Check that resulting host is registered to Satellite
        3. Check host can install package from Satellite

    :expectedresults:
        1. Host installs
        2. Host is registered to Satellite and subscription status is 'Success'
        3. Host can install package from Satellite
    """
    bios_firmware = "BIOS"  # TODO: Make this a test parameter
    bios_firmware
    host_mac_addr = provisioning_contenthost._broker_args['provisioning_nic_mac_addr']
    sat = provisioning_sat.sat

    host = sat.api.Host(
        hostgroup=provisioning_sat.hostgroup,
        organization=module_manifest_org,
        location=module_location,
        content_facet_attributes={
            'content_view_id': provisioning_rhel_content.cv.id,
            'lifecycle_environment_id': provisioning_rhel_content.lce.id,
        },
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        operatingsystem=provisioning_rhel_content.os,
        subnet=provisioning_sat.subnet,
        host_parameters_attributes=[
            {'name': 'remote_execution_connect_by_ip', 'value': 'true', 'parameter_type': 'boolean'}
        ],
        build=True,  # put the host to build mode
    ).create(create_missing=False)
    # Clean up the host to free IP leases on Satellite.
    # broker should do that as a part of the teardown, putting here just to make sure.
    request.addfinalizer(host.delete)

    # Call RHVM API using wrapanapi to start the VM
    rhv_api = RHEVMSystem(
        hostname=settings.provisioning_rhev.hostname,
        username=settings.provisioning_rhev.username,
        password=settings.provisioning_rhev.password,
        version=settings.provisioning_rhev.version,
        verify=settings.provisioning_rhev.verify,
    )
    rhv_vm = rhv_api.get_vm(provisioning_contenthost.name)
    rhv_vm.start()

    # TODO: Implement Satellite log capturing logic to verify that
    # all the events are captured in the logs.

    # Host should do call back to the Satellite reporting
    # the result of the installation. Wait until Satellite reports that the host is installed.
    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=900,
        delay=30,
    )
    host = host.read()
    assert host.build_status_label == 'Installed'

    # Change the hostname of the host as we know it already.
    # In the current infra environment we do not support
    # addressing hosts using FQDNs, falling back to IP.
    provisioning_contenthost.hostname = host.ip
    # Host is not blank anymore
    provisioning_contenthost.blank = False

    # Wait for the host to be rebooted and SSH daemon to be started.
    try:
        wait_for(
            provisioning_contenthost.connect,
            fail_condition=lambda res: res is not None,
            handle_exception=True,
            raise_original=True,
            timeout=180,
            delay=1,
        )
    except ConnectionRefusedError:
        raise ConnectionRefusedError("Timed out waiting for SSH daemon to start on the host")

    # Perform version check
    host_os = host.operatingsystem.read()
    expected_rhel_version = Version(f'{host_os.major}.{host_os.minor}')
    assert (
        provisioning_contenthost.os_version == expected_rhel_version
    ), 'Different than the expected OS version was installed'

    # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
    template_id = (
        sat.api.JobTemplate().search(query={'search': 'name="Run Command - SSH Default"'})[0].id
    )
    job = sat.api.JobInvocation().run(
        data={
            'job_template_id': template_id,
            'inputs': {
                'command': f'grep KATELLO_SERVER={sat.hostname} /usr/bin/katello-rhsm-consumer'
            },
            'search_query': f"name = {host.name}",
            'targeting_type': 'static_query',
        },
    )
    assert job['result'] == 'success', 'Job invocation failed'

    # assert that the host is subscribed and consumes
    # subsctiption provided by the activation key
    assert provisioning_contenthost.subscribed, 'Host is not subscribed'
