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
from broker.broker import VMBroker
from fauxfactory import gen_string
from packaging.version import Version

from robottelo import constants
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings
from robottelo.hosts import ContentHost


@pytest.fixture(scope='module')
def module_location(module_manifest_org, module_target_sat):
    return module_target_sat.api.Location(organization=[module_manifest_org]).create()


# use internal Capsule
@pytest.fixture(scope='module')
def provisioning_capsule(module_target_sat, module_location):
    capsule = (
        module_target_sat.api.SmartProxy()
        .search(query={'search': f'name={module_target_sat.hostname}'})[0]
        .read()
    )
    capsule.location = [module_location]
    capsule.update(['location'])
    return capsule


# TODO: sync at the module level?
@pytest.fixture(scope="module")
def provisioning_rhel_content(request, module_target_sat, module_manifest_org):
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
    os = (
        sat.api.OperatingSystem()
        .search(
            query={'search': f'family=Redhat and major={rhel_xy.major} and minor={rhel_xy.minor}'}
        )[0]
        .read()
    )
    # return only the first repo - RHEL X KS or RHEL X BaseOS KS
    return Box(sat=sat, os=os, repo=rh_repos[0])


@pytest.fixture(scope='module')
def provisioning_sat(
    module_target_sat,
    provisioning_rhel_content,
    module_manifest_org,
    module_location,
    default_architecture,
    default_partitiontable,
    provisioning_capsule,
):
    sat = module_target_sat
    host_root_pass = settings.provisioning.host_root_password
    pxe_loader = "PXELinux BIOS"  # TODO: this should be a test parameter
    provisioning_domain_name = f"{gen_string('alpha').lower()}.foo"

    broker_data_out = VMBroker().execute(
        workflow="configure-install-sat-provisioning-rhv",
        artifacts="last",
        target_vlan_id=settings.provisioning.vlan_id,
        target_host=sat.name,
        provisioning_dns_zone=provisioning_domain_name,
        sat_version=str(settings.server.version.release),
        AnsibleTower='testing',
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
    provisioning_iface = broker_data_out.provisioning_iface  # TODO: is this needed?
    provisioning_iface

    provisioning_interface = ipaddress.ip_interface(broker_data_out.provisioning_addr_ipv4)
    provisioning_network = provisioning_interface.network
    # TODO: investigate DNS setup issue on Satellite,
    # we might need to set up Sat as the primary DNS server
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

    hostgroup = sat.api.HostGroup(
        organization=[module_manifest_org],
        location=[module_location],
        architecture=default_architecture,
        domain=domain,
        content_source=provisioning_capsule.id,
        content_view=cv,
        kickstart_repository=provisioning_rhel_content.repo,
        lifecycle_environment=lce,
        root_pass=host_root_pass,
        operatingsystem=provisioning_rhel_content.os,
        ptable=default_partitiontable,
        subnet=subnet,
        pxe_loader=pxe_loader,
    ).create()

    return Box(sat=sat, hostgroup=hostgroup, subnet=subnet, cv=cv, lce=lce)


@pytest.fixture(scope="module")  # TODO: scope="function"?
def provisioning_contenthost():
    vlan_id = settings.provisioning.vlan_id
    vm_firmware = "bios"  # TODO: this should be parametrizable by the test
    cd_iso = ""  # TODO: this should be parametrizable by the test

    with VMBroker(
        workflow="deploy-configure-pxe-provisioning-host-rhv",
        host_classes={'host': ContentHost},
        target_vlan_id=vlan_id,
        target_vm_firmware=vm_firmware,
        target_vm_cd_iso=cd_iso,
        AnsibleTower='testing',
    ) as host:
        yield host

    # TODO: Tell Satellite to access the host by IP address, not FQDN


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
    bios_firmware = "BIOS"  # TODO: teach the test to use this parameter
    bios_firmware
    # TODO fix mac addr nested argument in satlab-tower
    host_mac_addr = provisioning_contenthost._broker_args['provisioning_nic_mac_addr']['address']
    sat = provisioning_sat.sat

    host = sat.api.Host(
        hostgroup=provisioning_sat.hostgroup,
        organization=module_manifest_org,
        location=module_location,
        content_facet_attributes={
            'content_view_id': provisioning_sat.cv.id,
            'lifecycle_environment_id': provisioning_sat.lce.id,
        },
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        operatingsystem=provisioning_rhel_content.os,
        subnet=provisioning_sat.subnet,
        build=True,  # put the host to build mode
    ).create(create_missing=False)

    host

    # Call wrapanapi -> RHVM-02 to start the VM
