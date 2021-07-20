"""Test class for Hosts UI

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: tstrych

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import copy
import csv
import os
import random

import pytest
import yaml
from airgun.exceptions import DisabledWidgetError
from airgun.session import Session
from broker.broker import VMBroker
from nailgun import entities
from wait_for import wait_for
from widgetastic.exceptions import NoSuchElementException

from robottelo import manifests
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import create_role_permissions
from robottelo.api.utils import promote
from robottelo.api.utils import publish_puppet_module
from robottelo.api.utils import skip_yum_update_during_provisioning
from robottelo.api.utils import upload_manifest
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_host
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_job_invocation
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_scap_policy
from robottelo.cli.globalparam import GlobalParameter
from robottelo.cli.host import Host
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.proxy import Proxy
from robottelo.cli.scap_policy import Scappolicy
from robottelo.cli.scapcontent import Scapcontent
from robottelo.config import settings
from robottelo.constants import ANY_CONTEXT
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import OSCAP_PERIOD
from robottelo.constants import OSCAP_WEEKDAY
from robottelo.constants import PERMISSIONS
from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.datafactory import gen_string
from robottelo.hosts import ContentHost
from robottelo.ui.utils import create_fake_host


def _get_set_from_list_of_dict(value):
    """Returns a set of tuples representation of each dict sorted by keys

    :param list value: a list of simple dict.
    """
    return {tuple(sorted(list(global_param.items()), key=lambda t: t[0])) for global_param in value}


@pytest.fixture
def scap_policy(scap_content):
    scap_policy = make_scap_policy(
        {
            'name': gen_string('alpha'),
            'deploy-by': 'puppet',
            'scap-content-id': scap_content["scap_id"],
            'scap-content-profile-id': scap_content["scap_profile_id"],
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
        }
    )
    return scap_policy


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_loc(module_org, default_sat):
    location = entities.Location(organization=[module_org]).create()
    smart_proxy = (
        entities.SmartProxy().search(query={'search': f'name={default_sat.hostname}'})[0].read()
    )
    smart_proxy.location.append(entities.Location(id=location.id))
    smart_proxy.update(['location'])
    return location


@pytest.fixture(scope='module')
def module_global_params():
    """Create 3 global parameters and clean up at teardown"""
    global_parameters = []
    for _ in range(3):
        global_parameter = entities.CommonParameter(
            name=gen_string('alpha'), value=gen_string('alphanumeric')
        ).create()
        global_parameters.append(global_parameter)
    yield global_parameters
    # cleanup global parameters
    for global_parameter in global_parameters:
        global_parameter.delete()


@pytest.fixture(scope='module')
def module_host_template(module_org, module_loc):
    host_template = entities.Host(organization=module_org, location=module_loc)
    host_template.create_missing()
    host_template.name = None
    return host_template


@pytest.fixture(scope='module')
def default_partition_table():
    # Get the Partition table ID
    return entities.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0]


@pytest.fixture(scope='module')
def default_architecture():
    # Get the architecture ID
    return entities.Architecture().search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0]


@pytest.fixture(scope='module')
def module_environment(module_org, module_loc):
    # Create new puppet environment
    return entities.Environment(organization=[module_org], location=[module_loc]).create()


@pytest.fixture(scope='module')
def module_os(default_architecture, default_partition_table, module_org, module_loc):
    # Get the OS ID
    os = entities.OperatingSystem().search(
        query={'search': 'name="RedHat" AND major="7"'}
    ) or entities.OperatingSystem().search(query={'search': 'name="RedHat" AND major="6"'})
    os = os[0].read()
    return os


@pytest.fixture(scope='module')
def os_path(module_os):
    # Check what OS was found to use correct media
    if module_os.major == str(RHEL_6_MAJOR_VERSION):
        os_distr_url = settings.repos.rhel6_os
    elif module_os.major == str(RHEL_7_MAJOR_VERSION):
        os_distr_url = settings.repos.rhel7_os
    else:
        raise ValueError('Proposed RHEL version is not supported')
    return os_distr_url


@pytest.fixture(scope='module')
def module_proxy(module_org, module_loc, default_sat):
    # Search for SmartProxy, and associate organization/location
    proxy = entities.SmartProxy().search(query={'search': f'name={default_sat.hostname}'})[0].read()
    return proxy


@pytest.fixture(scope='module')
def module_libvirt_resource(module_org, module_loc):
    # Search if Libvirt compute-resource already exists
    # If so, just update its relevant fields otherwise,
    # Create new compute-resource with 'libvirt' provider.
    resource_url = f'qemu+ssh://root@{settings.compute_resources.libvirt_hostname}/system'
    comp_res = [
        res
        for res in entities.LibvirtComputeResource().search()
        if res.provider == FOREMAN_PROVIDERS['libvirt'] and res.url == resource_url
    ]
    if len(comp_res) > 0:
        computeresource = entities.LibvirtComputeResource(id=comp_res[0].id).read()
        computeresource.location.append(module_loc)
        computeresource.organization.append(module_org)
        computeresource = computeresource.update(['location', 'organization'])
    else:
        # Create Libvirt compute-resource
        computeresource = entities.LibvirtComputeResource(
            provider=FOREMAN_PROVIDERS['libvirt'],
            url=resource_url,
            set_console_password=False,
            display_type='VNC',
            location=[module_loc],
            organization=[module_org],
        ).create()
    return f'{computeresource.name} (Libvirt)'


@pytest.fixture(scope='module')
def module_libvirt_domain(module_org, module_loc, module_proxy, default_sat):
    # Search for existing domain or create new otherwise. Associate org,
    # location and dns to it
    _, _, domain = default_sat.hostname.partition('.')
    domain = entities.Domain().search(query={'search': f'name="{domain}"'})
    if len(domain) > 0:
        domain = domain[0].read()
        domain.location.append(module_loc)
        domain.organization.append(module_org)
        domain.dns = module_proxy
        domain = domain.update(['dns', 'location', 'organization'])
    else:
        domain = entities.Domain(
            dns=module_proxy, location=[module_loc], organization=[module_org]
        ).create()
    return domain


@pytest.fixture(scope='module')
def module_libvirt_subnet(module_org, module_loc, module_libvirt_domain, module_proxy):
    # Search if subnet is defined with given network.
    # If so, just update its relevant fields otherwise,
    # Create new subnet
    network = settings.vlan_networking.subnet
    subnet = entities.Subnet().search(query={'search': f'network={network}'})
    if len(subnet) > 0:
        subnet = subnet[0].read()
        subnet.domain.append(module_libvirt_domain)
        subnet.location.append(module_loc)
        subnet.organization.append(module_org)
        subnet.dns = module_proxy
        subnet.dhcp = module_proxy
        subnet.ipam = 'DHCP'
        subnet.tftp = module_proxy
        subnet.discovery = module_proxy
        subnet = subnet.update(
            ['domain', 'discovery', 'dhcp', 'dns', 'ipam', 'location', 'organization', 'tftp']
        )
    else:
        # Create new subnet
        subnet = entities.Subnet(
            network=network,
            mask=settings.vlan_networking.netmask,
            location=[module_loc],
            organization=[module_org],
            domain=[module_libvirt_domain],
            ipam='DHCP',
            dns=module_proxy,
            dhcp=module_proxy,
            tftp=module_proxy,
            discovery=module_proxy,
        ).create()
    return subnet


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture(scope='module')
def module_product(module_org):
    return entities.Product(organization=module_org).create()


@pytest.fixture(scope='module')
def module_repository(os_path, module_product):
    repo = entities.Repository(product=module_product, url=os_path).create()
    call_entity_method_with_timeout(entities.Repository(id=repo.id).sync, timeout=3600)
    return repo


@pytest.fixture(scope='module')
def module_libvirt_media(module_org, module_loc, os_path, module_os):
    media = entities.Media().search(query={'search': f'path="{os_path}"'})
    if len(media) > 0:
        # Media with this path already exist, make sure it is correct
        media = media[0].read()
        media.organization.append(module_org)
        media.location.append(module_loc)
        media.operatingsystem.append(module_os)
        media.os_family = 'Redhat'
        media = media.update(['organization', 'location', 'operatingsystem', 'os_family'])
    else:
        # Create new media
        media = entities.Media(
            organization=[module_org],
            location=[module_loc],
            operatingsystem=[module_os],
            path_=os_path,
            os_family='Redhat',
        ).create()
    return media


@pytest.fixture(scope='module')
def module_content_view(module_org, module_repository, module_lce):
    # Create, Publish and promote CV
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [module_repository]
    content_view = content_view.update(['repository'])
    call_entity_method_with_timeout(content_view.publish, timeout=3600)
    content_view = content_view.read()
    promote(content_view.version[0], module_lce.id)
    return content_view


@pytest.fixture(scope='module')
def module_libvirt_hostgroup(
    module_org,
    module_loc,
    default_partition_table,
    default_architecture,
    module_os,
    module_libvirt_media,
    module_environment,
    module_libvirt_subnet,
    module_proxy,
    module_libvirt_domain,
    module_lce,
    module_content_view,
):
    return entities.HostGroup(
        architecture=default_architecture,
        domain=module_libvirt_domain,
        subnet=module_libvirt_subnet,
        lifecycle_environment=module_lce,
        content_view=module_content_view,
        location=[module_loc],
        environment=module_environment,
        puppet_proxy=module_proxy,
        puppet_ca_proxy=module_proxy,
        content_source=module_proxy,
        operatingsystem=module_os,
        organization=[module_org],
        ptable=default_partition_table,
        medium=module_libvirt_media,
    ).create()


@pytest.fixture(scope='module')
def manifest_org(module_org):
    """Upload manifest to organization."""
    with manifests.clone() as manifest:
        upload_manifest(module_org.id, manifest.content)
    return module_org


@pytest.fixture(scope='module')
def module_activation_key(manifest_org):
    """Create activation key using default CV and library environment."""
    activation_key = entities.ActivationKey(
        auto_attach=True,
        content_view=manifest_org.default_content_view.id,
        environment=manifest_org.library.id,
        organization=manifest_org,
    ).create()

    # Find the 'Red Hat Employee Subscription' and attach it to the activation key.
    for subs in entities.Subscription(organization=manifest_org).search():
        if subs.name == DEFAULT_SUBSCRIPTION_NAME:
            # 'quantity' must be 1, not subscription['quantity']. Greater
            # values produce this error: 'RuntimeError: Error: Only pools
            # with multi-entitlement product subscriptions can be added to
            # the activation key with a quantity greater than one.'
            activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': subs.id})
            break
    return activation_key


@pytest.mark.tier2
def test_positive_end_to_end(session, module_host_template, module_org, module_global_params):
    """Create a new Host with parameters, config group. Check host presence on
        the dashboard. Update name with 'new' prefix and delete.

    :id: 4821444d-3c86-4f93-849b-60460e025ba0

    :expectedresults: Host is created with parameters, config group. Updated
        and deleted.

    :BZ: 1419161

    :CaseLevel: System
    """
    global_params = [
        global_param.to_json_dict(lambda attr, field: attr in ['name', 'value'])
        for global_param in module_global_params
    ]
    host_parameters = []
    for _ in range(2):
        host_parameters.append(dict(name=gen_string('alpha'), value=gen_string('alphanumeric')))
    expected_host_parameters = copy.deepcopy(host_parameters)
    # override the first global parameter
    overridden_global_parameter = {'name': global_params[0]['name'], 'value': gen_string('alpha')}
    expected_host_parameters.append(overridden_global_parameter)
    expected_global_parameters = copy.deepcopy(global_params)
    for global_param in expected_global_parameters:
        # update with overridden expected value
        if global_param['name'] == overridden_global_parameter['name']:
            global_param['overridden'] = True
        else:
            global_param['overridden'] = False

    config_group = entities.ConfigGroup().create()
    new_name = 'new{}'.format(gen_string("alpha").lower())
    new_host_name = f'{new_name}.{module_host_template.domain.name}'
    with session:
        host_name = create_fake_host(
            session,
            module_host_template,
            host_parameters=host_parameters,
            global_parameters=[overridden_global_parameter],
            extra_values={'puppet_classes.config_groups.assigned': [config_group.name]},
        )
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.read(host_name, widget_names=['parameters', 'puppet_classes'])
        assert _get_set_from_list_of_dict(
            values['parameters']['host_params']
        ) == _get_set_from_list_of_dict(expected_host_parameters)
        assert _get_set_from_list_of_dict(expected_global_parameters).issubset(
            _get_set_from_list_of_dict(values['parameters']['global_params'])
        )

        assert len(values['puppet_classes']['config_groups']['assigned']) == 1
        assert values['puppet_classes']['config_groups']['assigned'][0] == config_group.name
        # check host presence on the dashboard
        dashboard_values = session.dashboard.read('NewHosts')['hosts']
        displayed_host = [row for row in dashboard_values if row['Host'] == host_name][0]
        os_name = '{} {}'.format(
            module_host_template.operatingsystem.name, module_host_template.operatingsystem.major
        )
        assert os_name in displayed_host['Operating System']
        assert displayed_host['Installed'] == '-'
        # update
        session.host.update(host_name, {'host.name': new_name})
        assert not session.host.search(host_name)
        assert session.host.search(new_host_name)[0]['Name'] == new_host_name
        # delete
        session.host.delete(new_host_name)
        assert not session.host.search(new_host_name)


@pytest.mark.tier4
def test_positive_read_from_details_page(session, module_host_template):
    """Create new Host and read all its content through details page

    :id: ffba5d40-918c-440e-afbb-6b910db3a8fb

    :expectedresults: Host is created and has expected content

    :CaseLevel: System
    """
    os_name = '{} {}'.format(
        module_host_template.operatingsystem.name, module_host_template.operatingsystem.major
    )
    interface_id = gen_string('alpha')
    with session:
        host_name = create_fake_host(session, module_host_template, interface_id)
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.get_details(host_name)
        assert values['properties']['properties_table']['Status'] == 'OK'
        assert 'Pending installation' in values['properties']['properties_table']['Build']
        assert (
            values['properties']['properties_table']['Domain'] == module_host_template.domain.name
        )
        assert values['properties']['properties_table']['MAC Address'] == module_host_template.mac
        assert (
            values['properties']['properties_table']['Puppet Environment']
            == module_host_template.environment.name
        )
        assert (
            values['properties']['properties_table']['Architecture']
            == module_host_template.architecture.name
        )
        assert values['properties']['properties_table']['Operating System'] == os_name
        assert (
            values['properties']['properties_table']['Location']
            == module_host_template.location.name
        )
        assert (
            values['properties']['properties_table']['Organization']
            == module_host_template.organization.name
        )
        assert values['properties']['properties_table']['Owner'] == values['current_user']


@pytest.mark.tier4
def test_positive_read_from_edit_page(session, module_host_template):
    """Create new Host and read all its content through edit page

    :id: 758fcab3-b363-4bfc-8f5d-173098a7e72d

    :expectedresults: Host is created and has expected content

    :CaseLevel: System
    """
    os_name = '{} {}'.format(
        module_host_template.operatingsystem.name, module_host_template.operatingsystem.major
    )
    interface_id = gen_string('alpha')
    with session:
        host_name = create_fake_host(session, module_host_template, interface_id)
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.read(host_name)
        assert values['host']['name'] == host_name.partition('.')[0]
        assert values['host']['organization'] == module_host_template.organization.name
        assert values['host']['location'] == module_host_template.location.name
        assert values['host']['lce'] == ENVIRONMENT
        assert values['host']['content_view'] == DEFAULT_CV
        assert values['host']['puppet_environment'] == module_host_template.environment.name
        assert values['operating_system']['architecture'] == module_host_template.architecture.name
        assert values['operating_system']['operating_system'] == os_name
        assert values['operating_system']['media_type'] == 'All Media'
        assert values['operating_system']['media'] == module_host_template.medium.name
        assert values['operating_system']['ptable'] == module_host_template.ptable.name
        assert values['interfaces']['interfaces_list'][0]['Identifier'] == interface_id
        assert values['interfaces']['interfaces_list'][0]['Type'] == 'Interface physical'
        assert values['interfaces']['interfaces_list'][0]['MAC Address'] == module_host_template.mac
        assert values['interfaces']['interfaces_list'][0]['FQDN'] == host_name
        assert values['additional_information']['owned_by'] == values['current_user']
        assert values['additional_information']['enabled'] is True


@pytest.mark.tier3
def test_positive_inherit_puppet_env_from_host_group_when_action(session):
    """Host group puppet environment is inherited to already created
    host when corresponding action is applied to that host

    :id: 3f5af54e-e259-46ad-a2af-7dc1850891f5

    :customerscenario: true

    :expectedresults: Expected puppet environment is inherited to the host

    :BZ: 1414914

    :CaseLevel: System
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    host = entities.Host(organization=org, location=loc).create()
    env = entities.Environment(organization=[org], location=[loc]).create()
    hostgroup = entities.HostGroup(environment=env, organization=[org], location=[loc]).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        session.host.apply_action(
            'Change Environment', [host.name], {'environment': '*Clear environment*'}
        )
        host_values = session.host.search(host.name)
        assert host_values[0]['Host group'] == ''
        assert host_values[0]['Puppet Environment'] == ''
        session.host.apply_action('Change Group', [host.name], {'host_group': hostgroup.name})
        host_values = session.host.search(host.name)
        assert host_values[0]['Host group'] == hostgroup.name
        assert host_values[0]['Puppet Environment'] == ''
        session.host.apply_action(
            'Change Environment', [host.name], {'environment': '*Inherit from host group*'}
        )
        host_values = session.host.search(host.name)
        assert host_values[0]['Puppet Environment'] == env.name
        values = session.host.read(host.name, widget_names='host')
        assert values['host']['hostgroup'] == hostgroup.name
        assert values['host']['puppet_environment'] == env.name


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_create_with_puppet_class(session, module_host_template, module_org, module_loc):
    """Create new Host with puppet class assigned to it

    :id: d883f169-1105-435c-8422-a7160055734a

    :expectedresults: Host is created and contains correct puppet class

    :CaseLevel: System
    """
    pc_name = 'generic_1'
    cv = publish_puppet_module(
        [{'author': 'robottelo', 'name': pc_name}],
        settings.repos.custom_puppet.url,
        organization_id=module_org.id,
    )
    env = (
        entities.Environment()
        .search(query={'search': f'content_view="{cv.name}" and organization_id={module_org.id}'})[
            0
        ]
        .read()
    )
    env = entities.Environment(id=env.id, location=[module_loc]).update(['location'])
    with session:
        host_name = create_fake_host(
            session,
            module_host_template,
            extra_values={
                'host.puppet_environment': env.name,
                'puppet_classes.classes.assigned': [pc_name],
            },
        )
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.read(host_name, widget_names='puppet_classes')
        assert len(values['puppet_classes']['classes']['assigned']) == 1
        assert values['puppet_classes']['classes']['assigned'][0] == pc_name


@pytest.mark.tier2
def test_positive_assign_taxonomies(session, module_org, module_loc):
    """Ensure Host organization and Location can be assigned.

    :id: 52466df5-6f56-4faa-b0f8-42b63731f494

    :expectedresults: Host Assign Organization and Location actions are
        working as expected.

    :CaseLevel: Integration
    """
    host = entities.Host(organization=module_org, location=module_loc).create()
    new_host_org = entities.Organization().create()
    new_host_location = entities.Location(organization=[new_host_org]).create()
    with session:
        assert session.host.search(host.name)[0]['Name'] == host.name
        session.host.apply_action(
            'Assign Organization',
            [host.name],
            {'organization': new_host_org.name, 'on_mismatch': 'Fix Organization on Mismatch'},
        )
        assert not session.host.search(host.name)
        session.organization.select(org_name=new_host_org.name)
        assert session.host.search(host.name)[0]['Name'] == host.name
        session.host.apply_action(
            'Assign Location',
            [host.name],
            {'location': new_host_location.name, 'on_mismatch': 'Fix Location on Mismatch'},
        )
        assert not session.host.search(host.name)
        session.location.select(loc_name=new_host_location.name)
        assert session.host.search(host.name)[0]['Name'] == host.name
        values = session.host.get_details(host.name)
        assert values['properties']['properties_table']['Organization'] == new_host_org.name
        assert values['properties']['properties_table']['Location'] == new_host_location.name


@pytest.mark.skip_if_not_set('oscap')
@pytest.mark.tier2
def test_positive_assign_compliance_policy(session, scap_policy):
    """Ensure host compliance Policy can be assigned.

    :id: 323661a4-e849-4cc2-aa39-4b4a5fe2abed

    :expectedresults: Host Assign/Unassign Compliance Policy action is working as
        expected.

    :BZ: 1862135

    :CaseLevel: Integration
    """
    host = entities.Host().create()
    org = host.organization.read()
    loc = host.location.read()
    # add host organization and location to scap policy
    content = Scapcontent.info({'id': scap_policy['scap-content-id']}, output_format='json')
    organization_ids = [content_org['id'] for content_org in content.get('organizations', [])]
    organization_ids.append(org.id)
    location_ids = [content_loc['id'] for content_loc in content.get('locations', [])]
    location_ids.append(loc.id)
    Scapcontent.update(
        {
            'id': scap_policy['scap-content-id'],
            'organization-ids': organization_ids,
            'location-ids': location_ids,
        }
    )
    Scappolicy.update(
        {
            'id': scap_policy['id'],
            'organization-ids': organization_ids,
            'location-ids': location_ids,
        }
    )
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        assert not session.host.search(f'compliance_policy = {scap_policy["name"]}')
        assert session.host.search(host.name)[0]['Name'] == host.name
        session.host.apply_action(
            'Assign Compliance Policy', [host.name], {'policy': scap_policy['name']}
        )
        assert (
            session.host.search(f'compliance_policy = {scap_policy["name"]}')[0]['Name']
            == host.name
        )
        session.host.apply_action(
            'Assign Compliance Policy', [host.name], {'policy': scap_policy['name']}
        )
        assert (
            session.host.search(f'compliance_policy = {scap_policy["name"]}')[0]['Name']
            == host.name
        )
        session.host.apply_action(
            'Unassign Compliance Policy', [host.name], {'policy': scap_policy['name']}
        )
        assert not session.host.search(f'compliance_policy = {scap_policy["name"]}')


@pytest.mark.skipif((settings.robottelo.webdriver != 'chrome'), reason='Only tested on Chrome')
@pytest.mark.tier3
def test_positive_export(session):
    """Create few hosts and export them via UI

    :id: ffc512ad-982e-4b60-970a-41e940ebc74c

    :expectedresults: csv file contains same values as on web UI

    :CaseLevel: System
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    hosts = [entities.Host(organization=org, location=loc).create() for _ in range(3)]
    expected_fields = {
        (host.name, host.operatingsystem.read().title, host.environment.read().name)
        for host in hosts
    }
    with session:
        session.organization.select(org.name)
        session.location.select(loc.name)
        file_path = session.host.export()
        assert os.path.isfile(file_path)
        with open(file_path, newline='') as csvfile:
            actual_fields = []
            for row in csv.DictReader(csvfile):
                actual_fields.append((row['Name'], row['Operatingsystem'], row['Environment']))
        assert set(actual_fields) == expected_fields


@pytest.mark.tier4
def test_positive_create_with_inherited_params(session):
    """Create a new Host in organization and location with parameters

    :BZ: 1287223

    :id: 628122f2-bda9-4aa1-8833-55debbd99072

    :expectedresults: Host has inherited parameters from organization and
        location

    :CaseImportance: High
    """
    org = entities.Organization().create()
    loc = entities.Location(organization=[org]).create()
    org_param = dict(name=gen_string('alphanumeric'), value=gen_string('alphanumeric'))
    loc_param = dict(name=gen_string('alphanumeric'), value=gen_string('alphanumeric'))
    host_template = entities.Host(organization=org, location=loc)
    host_template.create_missing()
    host_name = f'{host_template.name}.{host_template.domain.name}'
    with session:
        session.organization.update(org.name, {'parameters.resources': org_param})
        session.location.update(loc.name, {'parameters.resources': loc_param})
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        create_fake_host(session, host_template)
        values = session.host.read(host_name, 'parameters')
        expected_params = {
            (org_param['name'], org_param['value']),
            (loc_param['name'], loc_param['value']),
        }
        assert expected_params.issubset(
            {(param['name'], param['value']) for param in values['parameters']['global_params']}
        )


@pytest.mark.tier4
def test_negative_delete_primary_interface(session, module_host_template):
    """Attempt to delete primary interface of a host

    :id: bc747e2c-38d9-4920-b4ae-6010851f704e

    :customerscenario: true

    :BZ: 1417119

    :expectedresults: Interface was not deleted

    :CaseLevel: System
    """
    interface_id = gen_string('alpha')
    with session:
        host_name = create_fake_host(session, module_host_template, interface_id=interface_id)
        with pytest.raises(DisabledWidgetError) as context:
            session.host.delete_interface(host_name, interface_id)
        assert 'Interface Delete button is disabled' in str(context.value)


@pytest.mark.skip_if_open("BZ:1801630")
@pytest.mark.tier2
def test_positive_view_hosts_with_non_admin_user(test_name, module_org, module_loc):
    """View hosts and content hosts as a non-admin user with only view_hosts, edit_hosts
    and view_organization permissions

    :BZ: 1642076

    :id: 19a07026-0550-11ea-bfdc-98fa9b6ecd5a

    :expectedresults: user with only view_hosts, edit_hosts and view_organization permissions
        is able to read content hosts and hosts

    :CaseLevel: System
    """
    user_password = gen_string('alpha')
    role = entities.Role(organization=[module_org]).create()
    create_role_permissions(role, {'Organization': ['view_organizations'], 'Host': ['view_hosts']})
    user = entities.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[module_org],
        location=[module_loc],
        default_organization=module_org,
        default_location=module_loc,
    ).create()
    created_host = entities.Host(location=module_loc, organization=module_org).create()
    with Session(test_name, user=user.login, password=user_password) as session:
        host = session.host.get_details(created_host.name, widget_names='breadcrumb')
        assert host['breadcrumb'] == created_host.name
        content_host = session.contenthost.read(created_host.name, widget_names='breadcrumb')
        assert content_host['breadcrumb'] == created_host.name


@pytest.mark.tier3
def test_positive_remove_parameter_non_admin_user(test_name, module_org, module_loc):
    """Remove a host parameter as a non-admin user with enough permissions

    :id: 598111c1-fdb6-42e9-8c28-fae999b5d112

    :expectedresults: user with sufficient permissions may remove host
        parameter

    :CaseLevel: System
    """
    user_password = gen_string('alpha')
    parameter = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
    role = entities.Role(organization=[module_org]).create()
    create_role_permissions(
        role,
        {
            'Parameter': PERMISSIONS['Parameter'],
            'Host': PERMISSIONS['Host'],
            'Operatingsystem': ['view_operatingsystems'],
        },
    )
    user = entities.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[module_org],
        location=[module_loc],
        default_organization=module_org,
        default_location=module_loc,
    ).create()
    host = entities.Host(
        content_facet_attributes={
            'content_view_id': module_org.default_content_view.id,
            'lifecycle_environment_id': module_org.library.id,
        },
        location=module_loc,
        organization=module_org,
        host_parameters_attributes=[parameter],
    ).create()
    with Session(test_name, user=user.login, password=user_password) as session:
        values = session.host.read(host.name, 'parameters')
        assert values['parameters']['host_params'][0] == parameter
        session.host.update(host.name, {'parameters.host_params': []})
        values = session.host.read(host.name, 'parameters')
        assert not values['parameters']['host_params']


@pytest.mark.tier3
def test_negative_remove_parameter_non_admin_user(test_name, module_org, module_loc):
    """Attempt to remove host parameter as a non-admin user with
    insufficient permissions

    :BZ: 1317868

    :id: 78fd230e-2ec4-4158-823b-ddbadd5e232f

    :customerscenario: true

    :expectedresults: user with insufficient permissions is unable to
        remove host parameter, 'Remove' link is not visible for him

    :CaseLevel: System
    """

    user_password = gen_string('alpha')
    parameter = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
    role = entities.Role(organization=[module_org]).create()
    create_role_permissions(
        role,
        {
            'Parameter': ['view_params'],
            'Host': PERMISSIONS['Host'],
            'Operatingsystem': ['view_operatingsystems'],
        },
    )
    user = entities.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[module_org],
        location=[module_loc],
        default_organization=module_org,
        default_location=module_loc,
    ).create()
    host = entities.Host(
        content_facet_attributes={
            'content_view_id': module_org.default_content_view.id,
            'lifecycle_environment_id': module_org.library.id,
        },
        location=module_loc,
        organization=module_org,
        host_parameters_attributes=[parameter],
    ).create()
    with Session(test_name, user=user.login, password=user_password) as session:
        values = session.host.read(host.name, 'parameters')
        assert values['parameters']['host_params'][0] == parameter
        with pytest.raises(NoSuchElementException) as context:
            session.host.update(host.name, {'parameters.host_params': []})
        assert 'Remove Parameter' in str(context.value)


@pytest.mark.tier3
def test_positive_check_permissions_affect_create_procedure(test_name, module_loc):
    """Verify whether user permissions affect what entities can be selected
    when host is created

    :id: 4502f99d-86fb-4655-a9dc-b2612cf849c6

    :customerscenario: true

    :expectedresults: user with specific permissions can choose only
        entities for create host procedure that he has access to

    :BZ: 1293716

    :CaseLevel: System
    """
    # Create new organization
    org = entities.Organization().create()
    # Create two lifecycle environments
    lc_env = entities.LifecycleEnvironment(organization=org).create()
    filter_lc_env = entities.LifecycleEnvironment(organization=org).create()
    # Create two content views and promote them to one lifecycle
    # environment which will be used in filter
    cv = entities.ContentView(organization=org).create()
    filter_cv = entities.ContentView(organization=org).create()
    for content_view in [cv, filter_cv]:
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], filter_lc_env.id)
    # Create two host groups
    hg = entities.HostGroup(organization=[org]).create()
    filter_hg = entities.HostGroup(organization=[org]).create()
    # Create new role
    role = entities.Role().create()
    # Create lifecycle environment permissions and select one specific
    # environment user will have access to
    create_role_permissions(
        role,
        {
            'Katello::KTEnvironment': [
                'promote_or_remove_content_views_to_environments',
                'view_lifecycle_environments',
            ]
        },
        # allow access only to the mentioned here environment
        search=f'name = {filter_lc_env.name}',
    )
    # Add necessary permissions for content view as we did for lce
    create_role_permissions(
        role,
        {
            'Katello::ContentView': [
                'promote_or_remove_content_views',
                'view_content_views',
                'publish_content_views',
            ]
        },
        # allow access only to the mentioned here cv
        search=f'name = {filter_cv.name}',
    )
    # Add necessary permissions for hosts as we did for lce
    create_role_permissions(
        role,
        {'Host': ['create_hosts', 'view_hosts']},
        # allow access only to the mentioned here host group
        search=f'hostgroup_fullname = {filter_hg.name}',
    )
    # Add necessary permissions for host groups as we did for lce
    create_role_permissions(
        role,
        {'Hostgroup': ['view_hostgroups']},
        # allow access only to the mentioned here host group
        search=f'name = {filter_hg.name}',
    )
    # Add permissions for Organization and Location
    create_role_permissions(
        role, {'Organization': PERMISSIONS['Organization'], 'Location': PERMISSIONS['Location']}
    )
    # Create new user with a configured role
    user_password = gen_string('alpha')
    user = entities.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[org],
        location=[module_loc],
        default_organization=org,
        default_location=module_loc,
    ).create()
    host_fields = [
        {'name': 'host.hostgroup', 'unexpected_value': hg.name, 'expected_value': filter_hg.name},
        {
            'name': 'host.lce',
            'unexpected_value': lc_env.name,
            'expected_value': filter_lc_env.name,
        },
        {
            'name': 'host.content_view',
            'unexpected_value': cv.name,
            'expected_value': filter_cv.name,
            # content view selection needs the right lce to be selected
            'other_fields_values': {'host.lce': filter_lc_env.name},
        },
    ]
    with Session(test_name, user=user.login, password=user_password) as session:
        for host_field in host_fields:
            with pytest.raises(NoSuchElementException) as context:
                values = {host_field['name']: host_field['unexpected_value']}
                values.update(host_field.get('other_fields_values', {}))
                session.host.helper.read_create_view(values)
            error_message = str(context.value)
            assert host_field['unexpected_value'] in error_message
            # After the NoSuchElementException from FilteredDropdown, airgun is not able to
            # navigate to other locations, Note in normal situation we should send Escape key to
            # browser.
            session.browser.refresh()
            values = {host_field['name']: host_field['expected_value']}
            values.update(host_field.get('other_fields_values', {}))
            create_values = session.host.helper.read_create_view(values, host_field['name'])
            tab_name, field_name = host_field['name'].split('.')
            assert create_values[tab_name][field_name] == host_field['expected_value']


@pytest.mark.tier2
def test_positive_search_by_parameter(session, module_org, module_loc):
    """Search for the host by global parameter assigned to it

    :id: 8e61127c-d0a0-4a46-a3c6-22d3b2c5457c

    :expectedresults: Only one specific host is returned by search

    :BZ: 1725686

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    parameters = [{'name': param_name, 'value': param_value}]
    param_host = entities.Host(
        organization=module_org, location=module_loc, host_parameters_attributes=parameters
    ).create()
    additional_host = entities.Host(organization=module_org, location=module_loc).create()
    with session:
        # Check that hosts present in the system
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter returns only one host in the list
        values = session.host.search(f'params.{param_name} = {param_value}')
        assert len(values) == 1
        assert values[0]['Name'] == param_host.name


@pytest.mark.tier4
def test_positive_search_by_parameter_with_different_values(session, module_org, module_loc):
    """Search for the host by global parameter assigned to it by its value

    :id: c3a4551e-d759-4a9d-ba90-8db4cab3db2c

    :expectedresults: Only one specific host is returned by search

    :BZ: 1725686

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha')
    param_values = [gen_string('alpha'), gen_string('alphanumeric')]
    hosts = [
        entities.Host(
            organization=module_org,
            location=module_loc,
            host_parameters_attributes=[{'name': param_name, 'value': param_value}],
        ).create()
        for param_value in param_values
    ]
    with session:
        # Check that hosts present in the system
        for host in hosts:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter returns only one host in the list
        for param_value, host in zip(param_values, hosts):
            values = session.host.search(f'params.{param_name} = {param_value}')
            assert len(values) == 1
            assert values[0]['Name'] == host.name


@pytest.mark.tier2
def test_positive_search_by_parameter_with_prefix(session, module_loc):
    """Search by global parameter assigned to host using prefix 'not' and
    any random string as parameter value to make sure that all hosts will
    be present in the list

    :id: a4affb90-1222-4d9a-94be-213f9e5be573

    :expectedresults: All assigned hosts to organization are returned by
        search

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    search_param_value = gen_string('alphanumeric')
    parameters = [{'name': param_name, 'value': param_value}]
    param_host = entities.Host(
        organization=org, location=module_loc, host_parameters_attributes=parameters
    ).create()
    additional_host = entities.Host(organization=org, location=module_loc).create()
    with session:
        session.organization.select(org_name=org.name)
        # Check that the hosts are present
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter with 'not' prefix returns both hosts
        values = session.host.search(f'not params.{param_name} = {search_param_value}')
        assert {value['Name'] for value in values} == {param_host.name, additional_host.name}


@pytest.mark.tier2
def test_positive_search_by_parameter_with_operator(session, module_loc):
    """Search by global parameter assigned to host using operator '<>' and
    any random string as parameter value to make sure that all hosts will
    be present in the list

    :id: 264065b7-0d04-467d-887a-0aba0d871b7c

    :expectedresults: All assigned hosts to organization are returned by
        search

    :BZ: 1463806

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    param_global_value = gen_string('numeric')
    search_param_value = gen_string('alphanumeric')
    entities.CommonParameter(name=param_name, value=param_global_value).create()
    parameters = [{'name': param_name, 'value': param_value}]
    param_host = entities.Host(
        organization=org, location=module_loc, host_parameters_attributes=parameters
    ).create()
    additional_host = entities.Host(organization=org, location=module_loc).create()
    with session:
        session.organization.select(org_name=org.name)
        # Check that the hosts are present
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter with '<>' operator returns both hosts
        values = session.host.search(f'params.{param_name} <> {search_param_value}')
        assert {value['Name'] for value in values} == {param_host.name, additional_host.name}


@pytest.mark.tier2
def test_positive_search_with_org_and_loc_context(session):
    """Perform usual search for host, but organization and location used
    for host create procedure should have 'All capsules' checkbox selected

    :id: 2ce50df0-2b30-42cc-a40b-0e1f4fde3c6f

    :expectedresults: Search functionality works as expected and correct
        result is returned

    :BZ: 1405496

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    host = entities.Host(organization=org, location=loc).create()
    with session:
        session.organization.update(org.name, {'capsules.all_capsules': True})
        session.location.update(loc.name, {'capsules.all_capsules': True})
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        assert session.host.search(f'name = "{host.name}"')[0]['Name'] == host.name
        assert session.host.search(host.name)[0]['Name'] == host.name


@pytest.mark.tier2
def test_positive_search_by_org(session, module_loc):
    """Search for host by specifying host's organization name

    :id: a3bb5bc5-cb9c-4b56-b383-f3e4d3d4d222

    :customerscenario: true

    :expectedresults: Search functionality works as expected and correct
        result is returned

    :BZ: 1447958

    :CaseLevel: Integration
    """
    host = entities.Host(location=module_loc).create()
    org = host.organization.read()
    with session:
        session.organization.select(org_name=ANY_CONTEXT['org'])
        assert session.host.search(f'organization = "{org.name}"')[0]['Name'] == host.name


@pytest.mark.tier2
def test_positive_validate_inherited_cv_lce(session, module_host_template, default_sat):
    """Create a host with hostgroup specified via CLI. Make sure host
    inherited hostgroup's lifecycle environment, content view and both
    fields are properly reflected via WebUI.

    :id: c83f6819-2649-4a8b-bb1d-ce93b2243765

    :expectedresults: Host's lifecycle environment and content view match
        the ones specified in hostgroup.

    :CaseLevel: Integration

    :BZ: 1391656
    """
    lce = make_lifecycle_environment({'organization-id': module_host_template.organization.id})
    content_view = make_content_view({'organization-id': module_host_template.organization.id})
    ContentView.publish({'id': content_view['id']})
    version_id = ContentView.version_list({'content-view-id': content_view['id']})[0]['id']
    ContentView.version_promote(
        {
            'id': version_id,
            'to-lifecycle-environment-id': lce['id'],
            'organization-id': module_host_template.organization.id,
        }
    )
    hostgroup = make_hostgroup(
        {
            'content-view-id': content_view['id'],
            'lifecycle-environment-id': lce['id'],
            'organization-ids': module_host_template.organization.id,
        }
    )
    puppet_proxy = Proxy.list({'search': f'name = {default_sat.hostname}'})[0]
    host = make_host(
        {
            'architecture-id': module_host_template.architecture.id,
            'domain-id': module_host_template.domain.id,
            'environment-id': module_host_template.environment.id,
            'hostgroup-id': hostgroup['id'],
            'location-id': module_host_template.location.id,
            'medium-id': module_host_template.medium.id,
            'operatingsystem-id': module_host_template.operatingsystem.id,
            'organization-id': module_host_template.organization.id,
            'partition-table-id': module_host_template.ptable.id,
            'puppet-proxy-id': puppet_proxy['id'],
        }
    )
    with session:
        values = session.host.read(host['name'], ['host.lce', 'host.content_view'])
        assert values['host']['lce'] == lce['name']
        assert values['host']['content_view'] == content_view['name']


@pytest.mark.tier2
def test_positive_global_registration_form(
    session, module_activation_key, module_org, module_loc, module_os, default_sat
):
    """Host registration form produces a correct curl command for various inputs

    :id: f81c2ec4-85b1-4372-8e63-464ddbf70296

    :customerscenario: true

    :expectedresults: The curl command contains all required parameters

    :CaseLevel: Integration
    """
    # rex and insigths parameters are only specified in curl when differing from
    # inerited parameters
    result = GlobalParameter().list({'search': 'host_registration_remote_execution'})
    rex_value = not result[0]['value']
    result = GlobalParameter().list({'search': 'host_registration_insights'})
    insights_value = not result[0]['value']
    hostgroup = entities.HostGroup(organization=[module_org], location=[module_loc]).create()
    iface = 'eth0'
    with session:
        cmd = session.host.get_register_command(
            {
                'setup_insights': 'Yes (enforce)' if insights_value else 'No (enforce)',
                'remote_execution': 'Yes (enforce)' if rex_value else 'No (enforce)',
                'insecure': True,
                'hostgroup': hostgroup.name,
                'operatingsystem': module_os.title,
                'activation_keys': module_activation_key.name,
                'remote_execution_interface': iface,
            }
        )
    expected_pairs = [
        f'organization_id={module_org.id}',
        f'activation_key={module_activation_key.name}',
        f'hostgroup_id={hostgroup.id}',
        f'location_id={module_loc.id}',
        f'operatingsystem_id={module_os.id}',
        f'remote_execution_interface={iface}',
        f'setup_insights={"true" if insights_value else "false"}',
        f'setup_remote_execution={"true" if rex_value else "false"}',
        f'{default_sat.hostname}',
        'insecure',
    ]
    for pair in expected_pairs:
        assert pair in cmd


@pytest.mark.tier3
def test_positive_global_registration_end_to_end(
    session, module_activation_key, module_org, module_loc, module_os, module_proxy
):
    """Host registration form produces a correct registration command and host is
    registered successfully with it, remote execution and insights are set up

    :id: a02658bf-097e-47a8-8472-5d9f649ba07a

    :customerscenario: true

    :expectedresults: Host is succesfully registered, remote execution and insights
         client work out of the box

    :CaseLevel: Integration
    """
    # make sure global parameters for rex and insights are set to true
    GlobalParameter().set({'name': 'host_registration_insights', 'value': 1})
    GlobalParameter().set({'name': 'host_registration_remote_execution', 'value': 1})
    # rex interface
    iface = 'eth0'
    # fill in the global registration form
    with session:
        cmd = session.host.get_register_command(
            {
                'capsule': module_proxy.name,
                'operatingsystem': module_os.title,
                'activation_keys': module_activation_key.name,
                'remote_execution_interface': iface,
                'insecure': True,
            }
        )
    expected_pairs = [
        f'organization_id={module_org.id}',
        f'activation_key={module_activation_key.name}',
        f'location_id={module_loc.id}',
        f'operatingsystem_id={module_os.id}',
        f'{module_proxy.name}:9090',
        'insecure',
    ]
    for pair in expected_pairs:
        assert pair in cmd
    # register host
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as client:
        # rhel repo required for insights client installation,
        # syncing it to the satellite would take too long
        client.configure_rhel_repo(settings.repos.rhel7_repo)
        # run curl
        result = client.execute(cmd)
        assert result.status == 0
        result = client.execute('subscription-manager identity')
        assert result.status == 0
        # Connect to host via ip
        Host.set_parameter(
            {
                'host': client.hostname,
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            }
        )
        # run insights-client via REX
        command = "insights-client --status"
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - SSH Default',
                'inputs': f'command={command}',
                'search-query': f"name ~ {client.hostname}",
            }
        )
        result = ' '.join(
            JobInvocation.get_output({'id': invocation_command['id'], 'host': client.hostname})
        )
        assert invocation_command['success'] == '1', result
        assert 'Insights API confirms registration' in result
        # check rex interface is set
        host = Host.info({'name': client.hostname})
        interface = [item for item in host['network-interfaces'] if item['identifier'] == iface]
        assert 'execution' in interface[0]['type']


@pytest.mark.tier2
def test_positive_inherit_puppet_env_from_host_group_when_create(session, module_org, module_loc):
    """Host group puppet environment is inherited to host in create
    procedure

    :id: 05831ecc-3132-4eb7-ad90-155470f331b6

    :customerscenario: true

    :expectedresults: Expected puppet environment is inherited to the form

    :BZ: 1414914

    :CaseLevel: Integration
    """
    hg_name = gen_string('alpha')
    env_name = gen_string('alpha')
    entities.Environment(name=env_name, organization=[module_org], location=[module_loc]).create()
    with session:
        session.hostgroup.create(
            {'host_group.name': hg_name, 'host_group.puppet_environment': env_name}
        )
        assert session.hostgroup.search(hg_name)[0]['Name'] == hg_name
        values = session.host.helper.read_create_view(
            {}, ['host.puppet_environment', 'host.inherit_puppet_environment']
        )
        assert not values['host']['puppet_environment']
        assert values['host']['inherit_puppet_environment'] is False
        values = session.host.helper.read_create_view(
            {'host.hostgroup': hg_name},
            ['host.puppet_environment', 'host.inherit_puppet_environment'],
        )
        assert values['host']['puppet_environment'] == env_name
        assert values['host']['inherit_puppet_environment'] is True
        values = session.host.helper.read_create_view(
            {'host.inherit_puppet_environment': False},
            ['host.puppet_environment', 'host.inherit_puppet_environment'],
        )
        assert values['host']['puppet_environment'] == env_name
        assert values['host']['inherit_puppet_environment'] is False


@pytest.mark.tier2
def test_positive_reset_puppet_env_from_cv(session, module_org, module_loc):
    """Content View puppet environment is inherited to host in create
    procedure and can be rolled back to its value at any moment using
    'Reset Puppet Environment to match selected Content View' button

    :id: f8f35bd9-9e7c-418f-837a-ccec21c05d59

    :customerscenario: true

    :expectedresults: Expected puppet environment is inherited to the field

    :BZ: 1336802

    :CaseLevel: Integration
    """
    puppet_env = gen_string('alpha')
    content_view = gen_string('alpha')
    entities.Environment(name=puppet_env, organization=[module_org], location=[module_loc]).create()
    entities.ContentView(name=content_view, organization=module_org).create()
    with session:
        session.contentview.update(content_view, {'details.force_puppet': True})
        session.contentview.publish(content_view)
        published_puppet_env = [
            env.name
            for env in entities.Environment().search(
                query=dict(search=f'organization_id={module_org.id}', per_page='1000')
            )
            if content_view in env.name
        ][0]
        values = session.host.helper.read_create_view(
            {'host.lce': ENVIRONMENT, 'host.content_view': content_view},
            ['host.puppet_environment'],
        )
        assert values['host']['puppet_environment'] == published_puppet_env
        values = session.host.helper.read_create_view(
            {'host.puppet_environment': puppet_env}, ['host.puppet_environment']
        )
        assert values['host']['puppet_environment'] == puppet_env
        # reset_puppet_environment
        values = session.host.helper.read_create_view(
            {'host.reset_puppet_environment': True}, ['host.puppet_environment']
        )
        assert values['host']['puppet_environment'] == published_puppet_env


@pytest.mark.tier3
def test_positive_set_multi_line_and_with_spaces_parameter_value(session, module_host_template):
    """Check that host parameter value with multi-line and spaces is
    correctly represented in yaml format

    :id: d72b481d-2279-4478-ab2d-128f92c76d9c

    :customerscenario: true

    :expectedresults:
        1. parameter is correctly represented in yaml format without
           line break (special chars should be escaped)
        2. host parameter value is the same when restored from yaml format

    :BZ: 1315282

    :CaseLevel: System
    """
    param_name = gen_string('alpha').lower()
    # long string that should be escaped and affected by line break with
    # yaml dump by default
    param_value = (
        'auth                          include              '
        'password-auth\r\n'
        'account     include                  password-auth'
    )
    host = entities.Host(
        organization=module_host_template.organization,
        architecture=module_host_template.architecture,
        domain=module_host_template.domain,
        environment=module_host_template.environment,
        location=module_host_template.location,
        mac=module_host_template.mac,
        medium=module_host_template.medium,
        operatingsystem=module_host_template.operatingsystem,
        ptable=module_host_template.ptable,
        root_pass=module_host_template.root_pass,
        content_facet_attributes={
            'content_view_id': entities.ContentView(
                organization=module_host_template.organization, name=DEFAULT_CV
            )
            .search()[0]
            .id,
            'lifecycle_environment_id': entities.LifecycleEnvironment(
                organization=module_host_template.organization, name=ENVIRONMENT
            )
            .search()[0]
            .id,
        },
    ).create()
    with session:
        session.host.update(
            host.name, {'parameters.host_params': [dict(name=param_name, value=param_value)]}
        )
        yaml_text = session.host.read_yaml_output(host.name)
        # ensure parameter value is represented in yaml format without
        # line break (special chars should be escaped)
        assert param_value.encode('unicode_escape') in bytes(yaml_text, 'utf-8')
        # host parameter value is the same when restored from yaml format
        yaml_content = yaml.load(yaml_text)
        host_parameters = yaml_content.get('parameters')
        assert host_parameters
        assert param_name in host_parameters
        assert host_parameters[param_name] == param_value


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_bulk_delete_host(session, module_loc):
    """Delete multiple hosts from the list

    :id: 8da2084a-8b50-46dc-b305-18eeb80d01e0

    :expectedresults: All selected hosts should be deleted successfully

    :BZ: 1368026

    :CaseLevel: System
    """
    org = entities.Organization().create()
    host_template = entities.Host(organization=org, location=module_loc)
    host_template.create_missing()
    hosts_names = [
        entities.Host(
            organization=org,
            location=module_loc,
            root_pass=host_template.root_pass,
            architecture=host_template.architecture,
            domain=host_template.domain,
            environment=host_template.environment,
            medium=host_template.medium,
            operatingsystem=host_template.operatingsystem,
            ptable=host_template.ptable,
        )
        .create()
        .name
        for _ in range(3)
    ]
    with session:
        session.organization.select(org_name=org.name)
        values = session.host.read_all()
        assert len(hosts_names) == len(values['table'])
        session.host.delete_hosts('All')
        values = session.host.read_all()
        assert not values['table']


@pytest.mark.on_premises_provisioning
@pytest.mark.tier4
def test_positive_provision_end_to_end(
    session,
    module_org,
    module_loc,
    module_libvirt_domain,
    module_libvirt_hostgroup,
    module_libvirt_resource,
):
    """Provision Host on libvirt compute resource

    :id: 2678f95f-0c0e-4b46-a3c1-3f9a954d3bde

    :expectedresults: Host is provisioned successfully

    :CaseLevel: System
    """
    hostname = gen_string('alpha').lower()
    root_pwd = gen_string('alpha', 15)
    puppet_env = entities.Environment(location=[module_loc], organization=[module_org]).create()
    with session:
        session.host.create(
            {
                'host.name': hostname,
                'host.organization': module_org.name,
                'host.location': module_loc.name,
                'host.hostgroup': module_libvirt_hostgroup.name,
                'host.inherit_deploy_option': False,
                'host.deploy': module_libvirt_resource,
                'host.inherit_puppet_environment': False,
                'host.puppet_environment': puppet_env.name,
                'provider_content.virtual_machine.memory': '2 GB',
                'operating_system.root_password': root_pwd,
                'interfaces.interface.network_type': 'Physical (Bridge)',
                'interfaces.interface.network': settings.vlan_networking.bridge,
                'additional_information.comment': 'Libvirt provision using valid data',
            }
        )
        name = f'{hostname}.{module_libvirt_domain.name}'
        assert session.host.search(name)[0]['Name'] == name
        wait_for(
            lambda: session.host.get_details(name)['properties']['properties_table']['Build']
            != 'Pending installation',
            timeout=1800,
            delay=30,
            fail_func=session.browser.refresh,
            silent_failure=True,
            handle_exception=True,
        )
        entities.Host(id=entities.Host().search(query={'search': f'name={name}'})[0].id).delete()
        assert (
            session.host.get_details(name)['properties']['properties_table']['Build'] == 'Installed'
        )


@pytest.mark.on_premises_provisioning
@pytest.mark.tier4
def test_positive_delete_libvirt(
    session,
    module_org,
    module_loc,
    module_libvirt_domain,
    module_libvirt_hostgroup,
    module_libvirt_resource,
):
    """Create a new Host on libvirt compute resource and delete it
    afterwards

    :id: 6a9175e7-bb96-4de3-bc45-ba6c10dd14a4

    :customerscenario: true

    :expectedresults: Proper warning message is displayed on delete attempt
        and host deleted successfully afterwards

    :BZ: 1243223

    :CaseLevel: System
    """
    hostname = gen_string('alpha').lower()
    root_pwd = gen_string('alpha', 15)
    puppet_env = entities.Environment(location=[module_loc], organization=[module_org]).create()
    with session:
        session.host.create(
            {
                'host.name': hostname,
                'host.organization': module_org.name,
                'host.location': module_loc.name,
                'host.hostgroup': module_libvirt_hostgroup.name,
                'host.inherit_deploy_option': False,
                'host.deploy': module_libvirt_resource,
                'host.inherit_puppet_environment': False,
                'host.puppet_environment': puppet_env.name,
                'provider_content.virtual_machine.memory': '1 GB',
                'operating_system.root_password': root_pwd,
                'interfaces.interface.network_type': 'Physical (Bridge)',
                'interfaces.interface.network': settings.vlan_networking.bridge,
                'additional_information.comment': 'Delete host that provisioned on Libvirt',
            }
        )
        name = f'{hostname}.{module_libvirt_domain.name}'
        assert session.host.search(name)[0]['Name'] == name
        message = session.host.delete(name)
        assert (
            'Are you sure you want to delete host {}? This will delete the VM and '
            'its disks, and is irreversible. This behavior can be changed via global '
            'setting "Destroy associated VM on host delete".'.format(name)
        ) == message
        assert not session.host.search(name)


@pytest.fixture
def gce_template(googleclient):
    max_rhel7_template = max(
        [
            img.name
            for img in googleclient.list_templates(True)
            if str(img.name).startswith('rhel-7')
        ]
    )
    return googleclient.get_template(max_rhel7_template, project='rhel-cloud').uuid


@pytest.fixture
def gce_cloudinit_template(googleclient, gce_cert):
    return googleclient.get_template('customcinit', project=gce_cert['project_id']).uuid


@pytest.fixture
def gce_domain(module_org, module_loc, gce_cert):
    domain_name = f'{settings.gce.zone}.c.{gce_cert["project_id"]}.internal'
    domain = entities.Domain().search(query={'search': f'name={domain_name}'})
    if domain:
        domain = domain[0]
        domain.organization = [module_org]
        domain.location = [module_loc]
        domain.update(['organization', 'location'])
    if not domain:
        domain = entities.Domain(
            name=domain_name, location=[module_loc], organization=[module_org]
        ).create()
    return domain


@pytest.fixture
def gce_resource_with_image(
    gce_template,
    gce_cloudinit_template,
    gce_cert,
    default_architecture,
    module_os,
    module_loc,
    module_org,
):
    with Session('gce_tests') as session:
        # Until the CLI and API support is added for GCE,
        # creating GCE CR from UI
        cr_name = gen_string('alpha')
        vm_user = gen_string('alpha')
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['google'],
                'provider_content.google_project_id': gce_cert['project_id'],
                'provider_content.client_email': gce_cert['client_email'],
                'provider_content.certificate_path': settings.gce.cert_path,
                'provider_content.zone.value': settings.gce.zone,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_loc.name],
            }
        )
    gce_cr = entities.AbstractComputeResource().search(query={'search': f'name={cr_name}'})[0]
    # Finish Image
    entities.Image(
        architecture=default_architecture,
        compute_resource=gce_cr,
        name='autogce_img',
        operatingsystem=module_os,
        username=vm_user,
        uuid=gce_template,
    ).create()
    # Cloud-Init Image
    entities.Image(
        architecture=default_architecture,
        compute_resource=gce_cr,
        name='autogce_img_cinit',
        operatingsystem=module_os,
        username=vm_user,
        uuid=gce_cloudinit_template,
        user_data=True,
    ).create()
    return gce_cr


@pytest.fixture
def gce_hostgroup(
    module_org,
    module_loc,
    default_partition_table,
    default_architecture,
    module_os,
    module_environment,
    module_proxy,
    gce_domain,
    gce_resource_with_image,
    module_lce,
    module_content_view,
):
    return entities.HostGroup(
        architecture=default_architecture,
        compute_resource=gce_resource_with_image,
        domain=gce_domain,
        lifecycle_environment=module_lce,
        content_view=module_content_view,
        location=[module_loc],
        environment=module_environment,
        puppet_proxy=module_proxy,
        puppet_ca_proxy=module_proxy,
        content_source=module_proxy,
        operatingsystem=module_os,
        organization=[module_org],
        ptable=default_partition_table,
    ).create()


@pytest.mark.tier4
@pytest.mark.skip_if_not_set('gce')
def test_positive_gce_provision_end_to_end(
    session, module_org, module_loc, module_os, gce_domain, gce_hostgroup, googleclient
):
    """Provision Host on GCE compute resource

    :id: 8d1877bb-fbc2-4969-a13e-e95e4df4f4cd

    :expectedresults: Host is provisioned successfully

    :CaseLevel: System
    """
    name = f'test{gen_string("alpha", 4).lower()}'
    hostname = f'{name}.{gce_domain.name}'
    gceapi_vmname = hostname.replace('.', '-')
    root_pwd = gen_string('alpha', 15)
    storage = [{'size': 20}]
    with Session('gce_tests') as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_loc.name)
        # Provision GCE Host
        try:
            skip_yum_update_during_provisioning(template='Kickstart default finish')
            session.host.create(
                {
                    'host.name': name,
                    'host.hostgroup': gce_hostgroup.name,
                    'provider_content.virtual_machine.machine_type': 'g1-small',
                    'provider_content.virtual_machine.external_ip': True,
                    'provider_content.virtual_machine.network': 'default',
                    'provider_content.virtual_machine.storage': storage,
                    'operating_system.operating_system': module_os.title,
                    'operating_system.image': 'autogce_img',
                    'operating_system.root_password': root_pwd,
                }
            )
            wait_for(
                lambda: entities.Host()
                .search(query={'search': f'name={hostname}'})[0]
                .build_status_label
                != 'Pending installation',
                timeout=600,
                delay=15,
                silent_failure=True,
                handle_exception=True,
            )
            # 1. Host Creation Assertions
            # 1.1 UI based Assertions
            host_info = session.host.get_details(hostname)
            assert session.host.search(hostname)[0]['Name'] == hostname
            assert host_info['properties']['properties_table']['Build'] == 'Installed clear'
            # 1.2 GCE Backend Assertions
            gceapi_vm = googleclient.get_vm(gceapi_vmname)
            assert gceapi_vm.is_running
            assert gceapi_vm
            assert gceapi_vm.name == gceapi_vmname
            assert gceapi_vm.zone == settings.gce.zone
            assert gceapi_vm.ip == host_info['properties']['properties_table']['IP Address']
            assert 'g1-small' in gceapi_vm.raw['machineType'].split('/')[-1]
            assert 'default' in gceapi_vm.raw['networkInterfaces'][0]['network'].split('/')[-1]
            # 2. Host Deletion Assertions
            message = session.host.delete(hostname)
            # 2.1 UI based Assertions
            assert (
                'Are you sure you want to delete host {}? This will delete the VM and '
                'its disks, and is irreversible. This behavior can be changed via '
                'global setting "Destroy associated VM on host delete".'.format(hostname)
            ) == message
            assert not session.host.search(hostname)
            # 2.2 GCE Backend Assertions
            assert gceapi_vm.is_stopping or gceapi_vm.is_stopped
        except Exception as error:
            gcehost = entities.Host().search(query={'search': f'name={hostname}'})
            if gcehost:
                gcehost[0].delete()
            raise error
        finally:
            skip_yum_update_during_provisioning(template='Kickstart default finish', reverse=True)


@pytest.mark.tier4
@pytest.mark.upgrade
@pytest.mark.skip_if_not_set('gce')
def test_positive_gce_cloudinit_provision_end_to_end(
    session, module_org, module_loc, module_os, gce_domain, gce_hostgroup, googleclient
):
    """Provision Host on GCE compute resource

    :id: 6ee63ec6-2e8e-4ed6-ae48-e68b078233c6

    :expectedresults: Host is provisioned successfully

    :CaseLevel: System
    """
    name = f'test{gen_string("alpha", 4).lower()}'
    hostname = f'{name}.{gce_domain.name}'
    gceapi_vmname = hostname.replace('.', '-')
    storage = [{'size': 20}]
    root_pwd = gen_string('alpha', random.choice([8, 15]))
    with Session('gce_tests') as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_loc.name)
        # Provision GCE Host
        try:
            skip_yum_update_during_provisioning(template='Kickstart default user data')
            session.host.create(
                {
                    'host.name': name,
                    'host.hostgroup': gce_hostgroup.name,
                    'provider_content.virtual_machine.machine_type': 'g1-small',
                    'provider_content.virtual_machine.external_ip': True,
                    'provider_content.virtual_machine.network': 'default',
                    'provider_content.virtual_machine.storage': storage,
                    'operating_system.operating_system': module_os.title,
                    'operating_system.image': 'autogce_img_cinit',
                    'operating_system.root_password': root_pwd,
                }
            )
            # 1. Host Creation Assertions
            # 1.1 UI based Assertions
            host_info = session.host.get_details(hostname)
            assert session.host.search(hostname)[0]['Name'] == hostname
            assert (
                host_info['properties']['properties_table']['Build'] == 'Pending installation clear'
            )
            # 1.2 GCE Backend Assertions
            gceapi_vm = googleclient.get_vm(gceapi_vmname)
            assert gceapi_vm
            assert gceapi_vm.is_running
            assert gceapi_vm.name == gceapi_vmname
            assert gceapi_vm.zone == settings.gce.zone
            assert gceapi_vm.ip == host_info['properties']['properties_table']['IP Address']
            assert 'g1-small' in gceapi_vm.raw['machineType'].split('/')[-1]
            assert 'default' in gceapi_vm.raw['networkInterfaces'][0]['network'].split('/')[-1]
            # 2. Host Deletion Assertions
            message = session.host.delete(hostname)
            # 2.1 UI based Assertions
            assert (
                'Are you sure you want to delete host {}? This will delete the VM and '
                'its disks, and is irreversible. This behavior can be changed via '
                'global setting "Destroy associated VM on host delete".'.format(hostname)
            ) == message
            assert not session.host.search(hostname)
            # 2.2 GCE Backend Assertions
            assert gceapi_vm.is_stopping or gceapi_vm.is_stopped
        except Exception as error:
            gcehost = entities.Host().search(query={'search': f'name={hostname}'})
            if gcehost:
                gcehost[0].delete()
            raise error
        finally:
            skip_yum_update_during_provisioning(
                template='Kickstart default user data', reverse=True
            )


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_cockpit(session, default_sat):
    """Test whether webconsole button and cockpit integration works

    :id: 5a9be063-cdc4-43ce-91b9-7608fbebf8bb

    :expectedresults: Cockpit page is loaded and displays sat host info

    :CaseLevel: System

    """
    with session:
        session.organization.select(org_name='Default Organization')
        session.location.select(loc_name='Any Location')
        hostname_inside_cockpit = session.host.get_webconsole_content(
            entity_name=default_sat.hostname
        )
        assert (
            hostname_inside_cockpit == default_sat.hostname
        ), 'cockpit page shows hostname {} instead of {}'.format(
            hostname_inside_cockpit, default_sat.hostname
        )
