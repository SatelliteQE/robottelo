import ipaddress

import pytest
from box import Box
from broker.broker import Broker
from fauxfactory import gen_string
from packaging.version import Version

from robottelo import constants
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings
from robottelo.hosts import ContentHost


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
        target_memory='6GiB',
    ) as host:
        yield host
