import ipaddress
import os
from tempfile import mkstemp

import pytest
from box import Box
from broker import Broker
from fauxfactory import gen_string
from packaging.version import Version

from robottelo import constants
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings
from robottelo.hosts import ContentHost


@pytest.fixture(scope='module')
def module_provisioning_capsule(module_target_sat, module_location):
    """Assigns the `module_location` to Satellite's internal capsule and returns it"""
    capsule = module_target_sat.internal_capsule
    capsule.location = [module_location]
    return capsule.update(['location'])


@pytest.fixture(scope='module')
def module_provisioning_rhel_content(
    request,
    module_provisioning_sat,
    module_provisioning_capsule,
    module_org_with_manifest,
    module_lce_library,
    module_default_org_view,
    default_subscription,
    module_location,
    default_architecture,
    default_partitiontable,
):
    """
    This fixture sets up kickstart repositories for a specific RHEL version
    that is specified in `request.param`.
    """
    sat = module_provisioning_sat.sat
    rhel_ver = request.param['rhel_version']
    repo_names = [f'rhel{rhel_ver}']
    if int(rhel_ver) > 7:
        repo_names.append(f'rhel{rhel_ver}_aps')

    rh_repos = []
    tasks = []
    for name in repo_names:
        rh_repo_id = enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=module_org_with_manifest.id,
            product=constants.REPOS['kickstart'][name]['product'],
            repo=constants.REPOS['kickstart'][name]['name'],
            reposet=constants.REPOS['kickstart'][name]['reposet'],
            releasever=constants.REPOS['kickstart'][name]['version'],
        )
        # Sync step because repo is not synced by default
        rh_repo = sat.api.Repository(id=rh_repo_id).read()
        task = rh_repo.sync(synchronous=False)
        tasks.append(task)
        rh_repos.append(rh_repo)
    for task in tasks:
        wait_for_tasks(
            search_query=(f'id = {task["id"]}'),
            poll_timeout=2500,
        )
        task_status = sat.api.ForemanTask(id=task['id']).poll()
        assert task_status['result'] == 'success'

    rhel_xy = Version(constants.REPOS['kickstart'][f'rhel{rhel_ver}']['version'])
    o_systems = sat.api.OperatingSystem().search(
        query={'search': f'family=Redhat and major={rhel_xy.major} and minor={rhel_xy.minor}'}
    )
    assert o_systems, f'Operating system RHEL {rhel_xy} was not found'
    os = o_systems[0].read()
    # return only the first kickstart repo - RHEL X KS or RHEL X BaseOS KS
    ksrepo = rh_repos[0]

    ak = sat.api.ActivationKey(
        organization=module_org_with_manifest,
        content_view=module_default_org_view,
        environment=module_lce_library,
    ).create()
    ak.add_subscriptions(data={'subscription_id': default_subscription.id})

    host_root_pass = settings.provisioning.host_root_password
    pxe_loader = "PXELinux BIOS"  # TODO: Make this a fixture parameter

    hostgroup = sat.api.HostGroup(
        organization=[module_org_with_manifest],
        location=[module_location],
        architecture=default_architecture,
        domain=module_provisioning_sat.domain,
        content_source=module_provisioning_capsule.id,
        content_view=module_default_org_view,
        kickstart_repository=ksrepo,
        lifecycle_environment=module_lce_library,
        root_pass=host_root_pass,
        operatingsystem=os,
        ptable=default_partitiontable,
        subnet=module_provisioning_sat.subnet,
        pxe_loader=pxe_loader,
        group_parameters_attributes=[
            {
                'name': 'remote_execution_ssh_keys',
                'parameter_type': 'string',
                'value': settings.provisioning.host_ssh_key_pub,
            },
            # assign AK in order the hosts to be subscribed
            {
                'name': 'kt_activation_keys',
                'parameter_type': 'string',
                'value': ak.name,
            },
        ],
    ).create()

    return Box(
        hostgroup=hostgroup,
    )


@pytest.fixture(scope='module')
def module_provisioning_sat(
    module_target_sat,
    module_org_with_manifest,
    module_location,
    module_provisioning_capsule,
):
    """
    This fixture sets up the Satellite for PXE provisioning.
    It calls a workflow using broker to set up the network and to run satellite-installer.
    It uses the artifacts from the workflow to create all the necessary Satellite entities
    that are later used by the tests.
    """
    sat = module_target_sat
    provisioning_domain_name = f"{gen_string('alpha').lower()}.foo"

    broker_data_out = Broker().execute(
        workflow="configure-install-sat-provisioning-rhv",
        artifacts="last",
        target_vlan_id=settings.provisioning.vlan_id,
        target_host=sat.name,
        provisioning_dns_zone=provisioning_domain_name,
        sat_version=sat.version,
    )

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
        organization=[module_org_with_manifest],
        dns=module_provisioning_capsule.id,
        name=provisioning_domain_name,
    ).create()

    subnet = sat.api.Subnet(
        location=[module_location],
        organization=[module_org_with_manifest],
        network=str(provisioning_network.network_address),
        mask=str(provisioning_network.netmask),
        gateway=broker_data_out.provisioning_gw_ipv4,
        from_=broker_data_out.provisioning_host_range_start,
        to=broker_data_out.provisioning_host_range_end,
        dns_primary=provisioning_upstream_dns_primary,
        dns_secondary=provisioning_upstream_dns_secondary,
        boot_mode='DHCP',
        ipam='DHCP',
        dhcp=module_provisioning_capsule.id,
        tftp=module_provisioning_capsule.id,
        template=module_provisioning_capsule.id,
        dns=module_provisioning_capsule.id,
        httpboot=module_provisioning_capsule.id,
        discovery=module_provisioning_capsule.id,
        remote_execution_proxy=[module_provisioning_capsule.id],
        domain=[domain.id],
    ).create()

    return Box(sat=sat, domain=domain, subnet=subnet)


@pytest.fixture(scope='module')
def module_ssh_key_file():
    _, layout = mkstemp(text=True)
    os.chmod(layout, 0o600)
    with open(layout, 'w') as ssh_key:
        ssh_key.write(settings.provisioning.host_ssh_key_priv)
    return layout


@pytest.fixture()
def provisioning_host(module_ssh_key_file):
    """Fixture to check out blank VM"""
    vlan_id = settings.provisioning.vlan_id
    vm_firmware = "bios"  # TODO: Make this a fixture parameter - bios, uefi
    cd_iso = ""  # TODO: Make this an optional fixture parameter
    with Broker(
        workflow="deploy-configure-pxe-provisioning-host-rhv",
        host_classes={'host': ContentHost},
        target_vlan_id=vlan_id,
        target_vm_firmware=vm_firmware,
        target_vm_cd_iso=cd_iso,
        blank=True,
        target_memory='6GiB',
        auth=module_ssh_key_file,
    ) as host:
        yield host
        # Set host as non-blank to run teardown of the host
        host.blank = False
