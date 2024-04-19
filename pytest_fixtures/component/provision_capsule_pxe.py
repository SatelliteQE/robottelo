import ipaddress

from box import Box
from broker import Broker
from fauxfactory import gen_string
from packaging.version import Version
import pytest

from robottelo import constants
from robottelo.config import settings


@pytest.fixture(scope='module')
def capsule_provisioning_sat(
    request,
    module_target_sat,
    module_sca_manifest_org,
    module_location,
    module_capsule_configured,
):
    """
    This fixture sets up the Satellite for PXE provisioning.
    It calls a workflow using broker to set up the network and to run satellite-installer.
    It uses the artifacts from the workflow to create all the necessary Satellite entities
    that are later used by the tests.
    """
    # Assign org and loc
    capsule = module_capsule_configured.nailgun_smart_proxy
    capsule.location = [module_location]
    capsule.update(['location'])
    capsule.organization = [module_sca_manifest_org]
    capsule.update(['organization'])

    provisioning_type = getattr(request, 'param', '')
    sat = module_target_sat
    provisioning_domain_name = f"{gen_string('alpha').lower()}.foo"
    broker_data_out = Broker().execute(
        workflow=settings.provisioning.provisioning_sat_workflow,
        artifacts='last',
        target_vlan_id=settings.provisioning.vlan_id,
        target_host=module_capsule_configured.name,
        provisioning_dns_zone=provisioning_domain_name,
        sat_version='stream' if sat.is_stream else sat.version,
        deploy_scenario='capsule',
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
        organization=[module_sca_manifest_org],
        dns=capsule.id,
        name=provisioning_domain_name,
    ).create()

    subnet = sat.api.Subnet(
        location=[module_location],
        organization=[module_sca_manifest_org],
        network=str(provisioning_network.network_address),
        mask=str(provisioning_network.netmask),
        gateway=broker_data_out.provisioning_gw_ipv4,
        from_=broker_data_out.provisioning_host_range_start,
        to=broker_data_out.provisioning_host_range_end,
        dns_primary=provisioning_upstream_dns_primary,
        dns_secondary=provisioning_upstream_dns_secondary,
        boot_mode='DHCP',
        ipam='DHCP',
        dhcp=capsule.id,
        tftp=capsule.id,
        template=capsule.id,
        dns=capsule.id,
        httpboot=capsule.id,
        # discovery=capsule.id,
        remote_execution_proxy=[capsule.id],
        domain=[domain.id],
    ).create()

    return Box(
        sat=sat,
        domain=domain,
        subnet=subnet,
        provisioning_type=provisioning_type,
        broker_data=broker_data_out,
    )


@pytest.fixture(scope='module')
def capsule_provisioning_lce_sync_setup(module_capsule_configured, module_lce_library):
    """This fixture adds the lifecycle environment to the capsule and syncs the content"""
    module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
        data={'environment_id': module_lce_library.id}
    )
    sync_status = module_capsule_configured.nailgun_capsule.content_sync(timeout='60m')
    assert sync_status['result'] == 'success', 'Capsule sync task failed.'


@pytest.fixture
def capsule_provisioning_hostgroup(
    module_target_sat,
    capsule_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    default_architecture,
    capsule_provisioning_rhel_content,
    module_lce_library,
    default_partitiontable,
    pxe_loader,
    module_capsule_configured,
):
    capsule = module_capsule_configured.nailgun_smart_proxy
    provisioning_ip = capsule_provisioning_sat.broker_data.provisioning_addr_ipv4
    provisioning_ip = ipaddress.ip_interface(provisioning_ip).ip
    return capsule_provisioning_sat.sat.api.HostGroup(
        organization=[module_sca_manifest_org],
        location=[module_location],
        architecture=default_architecture,
        domain=capsule_provisioning_sat.domain,
        content_source=capsule.id,
        content_view=capsule_provisioning_rhel_content.cv,
        kickstart_repository=capsule_provisioning_rhel_content.ksrepo,
        lifecycle_environment=module_lce_library,
        root_pass=settings.provisioning.host_root_password,
        operatingsystem=capsule_provisioning_rhel_content.os,
        ptable=default_partitiontable,
        subnet=capsule_provisioning_sat.subnet,
        pxe_loader=pxe_loader.pxe_loader,
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
                'value': capsule_provisioning_rhel_content.ak.name,
            },
            {
                'name': 'http_proxy',
                'parameter_type': 'string',
                'value': str(provisioning_ip),
            },
            {
                'name': 'http_proxy_port',
                'parameter_type': 'string',
                'value': '80',
            },
        ],
    ).create()


@pytest.fixture(scope='module')
def capsule_provisioning_rhel_content(
    request,
    capsule_provisioning_sat,
    module_sca_manifest_org,
    module_lce_library,
):
    """
    This fixture sets up kickstart repositories for a specific RHEL version
    that is specified in `request.param`.
    """
    sat = capsule_provisioning_sat.sat
    rhel_ver = request.param['rhel_version']
    repo_names = []
    if int(rhel_ver) <= 7:
        repo_names.append(f'rhel{rhel_ver}')
    else:
        repo_names.append(f'rhel{rhel_ver}_bos')
        repo_names.append(f'rhel{rhel_ver}_aps')
    rh_repos = []
    tasks = []
    rh_repo_id = ""
    content_view = sat.api.ContentView(organization=module_sca_manifest_org).create()

    # Custom Content for Client repo
    custom_product = sat.api.Product(
        organization=module_sca_manifest_org, name=f'rhel{rhel_ver}_{gen_string("alpha")}'
    ).create()
    client_repo = sat.api.Repository(
        organization=module_sca_manifest_org,
        product=custom_product,
        content_type='yum',
        url=settings.repos.SATCLIENT_REPO[f'rhel{rhel_ver}'],
    ).create()
    task = client_repo.sync(synchronous=False)
    tasks.append(task)
    content_view.repository = [client_repo]

    for name in repo_names:
        rh_kickstart_repo_id = sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=module_sca_manifest_org.id,
            product=constants.REPOS['kickstart'][name]['product'],
            repo=constants.REPOS['kickstart'][name]['name'],
            reposet=constants.REPOS['kickstart'][name]['reposet'],
            releasever=constants.REPOS['kickstart'][name]['version'],
        )
        # do not sync content repos for discovery based provisioning.
        if capsule_provisioning_sat.provisioning_type != 'discovery':
            rh_repo_id = sat.api_factory.enable_rhrepo_and_fetchid(
                basearch=constants.DEFAULT_ARCHITECTURE,
                org_id=module_sca_manifest_org.id,
                product=constants.REPOS[name]['product'],
                repo=constants.REPOS[name]['name'],
                reposet=constants.REPOS[name]['reposet'],
                releasever=constants.REPOS[name]['releasever'],
            )

        # Sync step because repo is not synced by default
        for repo_id in [rh_kickstart_repo_id, rh_repo_id]:
            if repo_id:
                rh_repo = sat.api.Repository(id=repo_id).read()
                task = rh_repo.sync(synchronous=False)
                tasks.append(task)
                rh_repos.append(rh_repo)
                content_view.repository.append(rh_repo)
                content_view.update(['repository'])
    for task in tasks:
        sat.wait_for_tasks(
            search_query=(f'id = {task["id"]}'),
            poll_timeout=2500,
        )
        task_status = sat.api.ForemanTask(id=task['id']).poll()
        assert task_status['result'] == 'success'
    rhel_xy = Version(
        constants.REPOS['kickstart'][f'rhel{rhel_ver}']['version']
        if rhel_ver == 7
        else constants.REPOS['kickstart'][f'rhel{rhel_ver}_bos']['version']
    )
    o_systems = sat.api.OperatingSystem().search(
        query={'search': f'family=Redhat and major={rhel_xy.major} and minor={rhel_xy.minor}'}
    )
    assert o_systems, f'Operating system RHEL {rhel_xy} was not found'
    os = o_systems[0].read()
    # return only the first kickstart repo - RHEL X KS or RHEL X BaseOS KS
    ksrepo = rh_repos[0]
    publish = content_view.publish()
    task_status = sat.wait_for_tasks(
        search_query=(f'Actions::Katello::ContentView::Publish and id = {publish["id"]}'),
        search_rate=15,
        max_tries=10,
    )
    assert task_status[0].result == 'success'
    content_view = sat.api.ContentView(
        organization=module_sca_manifest_org, name=content_view.name
    ).search()[0]
    ak = sat.api.ActivationKey(
        organization=module_sca_manifest_org,
        content_view=content_view,
        environment=module_lce_library,
    ).create()

    # Ensure client repo is enabled in the activation key
    content = ak.product_content(data={'content_access_mode_all': '1'})['results']
    client_repo_label = [repo['label'] for repo in content if repo['name'] == client_repo.name][0]
    ak.content_override(
        data={'content_overrides': [{'content_label': client_repo_label, 'value': '1'}]}
    )
    return Box(os=os, ak=ak, ksrepo=ksrepo, cv=content_view)
