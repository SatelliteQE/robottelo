# -*- encoding: utf-8 -*-
"""Test class for Hosts UI

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import csv
import copy
import os

import pytest
import yaml

from airgun.exceptions import DisabledWidgetError
from airgun.session import Session
from nailgun import entities
from widgetastic.exceptions import NoSuchElementException

from robottelo import ssh
from robottelo.api.utils import create_role_permissions, promote
from robottelo.cli.factory import (
    make_content_view,
    make_host,
    make_hostgroup,
    make_lifecycle_environment,
    make_scap_policy,
    make_scapcontent,
)
from robottelo.cli.contentview import ContentView
from robottelo.cli.proxy import Proxy
from robottelo.cli.scap_policy import Scappolicy
from robottelo.cli.scapcontent import Scapcontent
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    DEFAULT_CV,
    ENVIRONMENT,
    OSCAP_PROFILE,
    OSCAP_PERIOD,
    OSCAP_WEEKDAY,
    PERMISSIONS,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import tier2, tier3, skip_if, skip_if_not_set, upgrade
from robottelo.ui.utils import create_fake_host


def _get_set_from_list_of_dict(value):
    """Returns a set of tuples representation of each dict sorted by keys

    :param list value: a list of simple dict.
    """
    return {
        tuple(sorted(list(global_param.items()), key=lambda t: t[0]))
        for global_param in value
    }


@pytest.fixture
def scap_content():
    oscap_content_path = settings.oscap.content_path
    _, file_name = os.path.split(oscap_content_path)
    title = 'rhel-content-{0}'.format(gen_string('alpha'))
    ssh.upload_file(
        local_file=oscap_content_path,
        remote_file="/tmp/{0}".format(file_name)
    )
    scap_info = make_scapcontent({
        'title': title,
        'scap-file': '/tmp/{0}'.format(file_name)
    })
    scap_id = scap_info['id']
    scap_info = Scapcontent.info({'id': scap_id}, output_format='json')

    scap_profile_id = [
        profile['id']
        for profile in scap_info['scap-content-profiles']
        if OSCAP_PROFILE['common'] in profile['title']
    ][0]
    return scap_id, scap_profile_id


@pytest.fixture
def scap_policy(scap_content):
    scap_id, scap_profile_id = scap_content
    scap_policy = make_scap_policy({
        'name': gen_string('alpha'),
        'scap-content-id': scap_id,
        'scap-content-profile-id': scap_profile_id,
        'period': OSCAP_PERIOD['weekly'].lower(),
        'weekday': OSCAP_WEEKDAY['friday'].lower()
    })
    return scap_policy


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_global_params():
    """Create 3 global parameters and clean up at teardown"""
    global_parameters = []
    for _ in range(3):
        global_parameter = entities.CommonParameter(
            name=gen_string('alpha'),
            value=gen_string('alphanumeric')
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


@tier3
def test_positive_create(session, module_host_template):
    """Create a new Host

    :id: 4821444d-3c86-4f93-849b-60460e025ba0

    :expectedresults: Host is created

    :CaseLevel: System
    """
    with session:
        host_name = create_fake_host(session, module_host_template)
        assert session.host.search(host_name)[0]['Name'] == host_name


@tier3
def test_positive_read_from_details_page(session, module_host_template):
    """Create new Host and read all its content through details page

    :id: ffba5d40-918c-440e-afbb-6b910db3a8fb

    :expectedresults: Host is created and has expected content

    :CaseLevel: System
    """
    os_name = u'{0} {1}'.format(
        module_host_template.operatingsystem.name, module_host_template.operatingsystem.major)
    interface_id = gen_string('alpha')
    with session:
        host_name = create_fake_host(session, module_host_template, interface_id)
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.get_details(host_name)
        assert values['properties']['properties_table'][
            'Status'] == 'OK'
        assert values['properties']['properties_table'][
            'Build'] == 'Pending installation'
        assert values['properties']['properties_table'][
            'Domain'] == module_host_template.domain.name
        assert values['properties']['properties_table'][
            'MAC Address'] == module_host_template.mac
        assert values['properties']['properties_table'][
            'Puppet Environment'] == module_host_template.environment.name
        assert values['properties']['properties_table'][
            'Architecture'] == module_host_template.architecture.name
        assert values['properties']['properties_table'][
            'Operating System'] == os_name
        assert values['properties']['properties_table'][
            'Location'] == module_host_template.location.name
        assert values['properties']['properties_table'][
            'Organization'] == module_host_template.organization.name
        assert values['properties']['properties_table'][
            'Owner'] == values['current_user']


@tier3
def test_positive_read_from_edit_page(session, module_host_template):
    """Create new Host and read all its content through edit page

    :id: 758fcab3-b363-4bfc-8f5d-173098a7e72d

    :expectedresults: Host is created and has expected content

    :CaseLevel: System
    """
    os_name = u'{0} {1}'.format(
        module_host_template.operatingsystem.name, module_host_template.operatingsystem.major)
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
        assert values[
            'operating_system']['architecture'] == module_host_template.architecture.name
        assert values['operating_system']['operating_system'] == os_name
        assert values['operating_system']['media_type'] == 'All Media'
        assert values['operating_system']['media'] == module_host_template.medium.name
        assert values['operating_system']['ptable'] == module_host_template.ptable.name
        assert values['interfaces']['interfaces_list'][0][
            'Identifier'] == interface_id
        assert values['interfaces']['interfaces_list'][0][
            'Type'] == 'Interface physical'
        assert values['interfaces']['interfaces_list'][0][
            'MAC Address'] == module_host_template.mac
        assert values['interfaces']['interfaces_list'][0][
            'FQDN'] == host_name
        assert values['additional_information'][
            'owned_by'] == values['current_user']
        assert values['additional_information']['enabled'] is True


@tier3
def test_positive_delete(session, module_host_template):
    """Delete a Host

    :id: 13735af1-f1c7-466e-a969-80618a1d854d

    :expectedresults: Host is delete

    :CaseLevel: System
    """
    with session:
        host_name = create_fake_host(session, module_host_template)
        assert session.host.search(host_name)[0]['Name'] == host_name
        session.host.delete(host_name)
        assert not session.host.search(host_name)


@tier3
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
    env = entities.Environment(
        organization=[org], location=[loc]).create()
    hostgroup = entities.HostGroup(
        environment=env, organization=[org], location=[loc]).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        session.host.apply_action(
            'Change Environment',
            [host.name],
            {'environment': '*Clear environment*'})
        host_values = session.host.search(host.name)
        assert host_values[0]['Host group'] == ''
        assert host_values[0]['Puppet Environment'] == ''
        session.host.apply_action(
            'Change Group',
            [host.name],
            {'host_group': hostgroup.name})
        host_values = session.host.search(host.name)
        assert host_values[0]['Host group'] == hostgroup.name
        assert host_values[0]['Puppet Environment'] == ''
        session.host.apply_action(
            'Change Environment',
            [host.name],
            {'environment': '*Inherit from host group*'})
        host_values = session.host.search(host.name)
        assert host_values[0]['Puppet Environment'] == env.name
        values = session.host.read(host.name)
        assert values['host']['hostgroup'] == hostgroup.name
        assert values['host']['puppet_environment'] == env.name


@tier2
def test_positive_create_host_with_parameters(session, module_global_params):
    """"Create new Host with parameters, override one global parameter and read
    all parameters.

    :id: d37be8de-77f0-46c1-a431-bbc4db0eb7f6

    :expectedresults: Host is created and has expected parameters values

    :CaseLevel: Integration
    """
    global_params = [
        global_param.to_json_dict(
            lambda attr, field: attr in ['name', 'value'])
        for global_param in module_global_params
    ]

    host = entities.Host()
    host.create_missing()
    host_name = u'{0}.{1}'.format(host.name, host.domain.name)
    host_parameters = []
    for _ in range(2):
        host_parameters.append(
            dict(name=gen_string('alpha'), value=gen_string('alphanumeric'))
        )
    expected_host_parameters = copy.deepcopy(host_parameters)
    # override the first global parameter
    overridden_global_parameter = {
                'name': global_params[0]['name'],
                'value': gen_string('alpha')
            }
    expected_host_parameters.append(overridden_global_parameter)
    expected_global_parameters = copy.deepcopy(global_params)
    for global_param in expected_global_parameters:
        # update with overridden expected value
        if global_param['name'] == overridden_global_parameter['name']:
            global_param['overridden'] = True
        else:
            global_param['overridden'] = False

    with session:
        session.organization.select(org_name=host.organization.name)
        session.location.select(loc_name=host.location.name)
        create_fake_host(
            session,
            host,
            host_parameters=host_parameters,
            global_parameters=[overridden_global_parameter],
        )
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.read(host_name)
        assert (_get_set_from_list_of_dict(values['parameters']['host_params'])
                == _get_set_from_list_of_dict(expected_host_parameters))
        assert _get_set_from_list_of_dict(
            expected_global_parameters).issubset(
            _get_set_from_list_of_dict(values['parameters']['global_params']))


@tier2
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
            {
                'organization': new_host_org.name,
                'on_mismatch': 'Fix Organization on Mismatch'
            }
        )
        assert not session.host.search(host.name)
        session.organization.select(org_name=new_host_org.name)
        assert session.host.search(host.name)[0]['Name'] == host.name
        session.host.apply_action(
            'Assign Location',
            [host.name],
            {
                'location': new_host_location.name,
                'on_mismatch': 'Fix Location on Mismatch'
            }
        )
        assert not session.host.search(host.name)
        session.location.select(loc_name=new_host_location.name)
        assert session.host.search(host.name)[0]['Name'] == host.name
        values = session.host.get_details(host.name)
        assert (values['properties']['properties_table']['Organization']
                == new_host_org.name)
        assert (values['properties']['properties_table']['Location']
                == new_host_location.name)


@skip_if_not_set('oscap')
@tier2
def test_positive_assign_compliance_policy(session, scap_policy):
    """Ensure host compliance Policy can be assigned.

    :id: 323661a4-e849-4cc2-aa39-4b4a5fe2abed

    :expectedresults: Host Assign Compliance Policy action is working as
        expected.

    :CaseLevel: Integration
    """
    host = entities.Host().create()
    org = host.organization.read()
    loc = host.location.read()
    # add host organization and location to scap policy
    scap_policy = Scappolicy.info(
        {'id': scap_policy['id']}, output_format='json')
    organization_ids = [
        policy_org['id']
        for policy_org in scap_policy.get('organizations', [])
    ]
    organization_ids.append(org.id)
    location_ids = [
        policy_loc['id']
        for policy_loc in scap_policy.get('locations', [])
    ]

    location_ids.append(loc.id)
    Scappolicy.update({
        'id': scap_policy['id'],
        'organization-ids': organization_ids,
        'location-ids': location_ids
    })
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        assert not session.host.search(
            'compliance_policy = {0}'.format(scap_policy['name']))
        assert session.host.search(host.name)[0]['Name'] == host.name
        session.host.apply_action(
            'Assign Compliance Policy',
            [host.name],
            {
                'policy': scap_policy['name'],
            }
        )
        assert (session.host.search(
            'compliance_policy = {0}'.format(scap_policy['name']))[0]['Name']
            ==
            host.name)


@skip_if(settings.webdriver != 'chrome')
@tier3
def test_positive_export(session):
    """Create few hosts and export them via UI

    :id: ffc512ad-982e-4b60-970a-41e940ebc74c

    :expectedresults: csv file contains same values as on web UI

    :CaseLevel: System
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    hosts = [entities.Host(organization=org, location=loc).create() for _ in range(3)]
    expected_fields = set(
        (host.name,
         host.operatingsystem.read().title,
         host.environment.read().name)
        for host in hosts
    )
    with session:
        session.organization.select(org.name)
        session.location.select(loc.name)
        file_path = session.host.export()
        assert os.path.isfile(file_path)
        with open(file_path, newline='') as csvfile:
            actual_fields = []
            for row in csv.DictReader(csvfile):
                actual_fields.append(
                    (row['Name'],
                     row['Operatingsystem'],
                     row['Environment'])
                )
        assert set(actual_fields) == expected_fields


@tier3
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
    host_name = u'{0}.{1}'.format(host_template.name, host_template.domain.name)
    with session:
        session.organization.update(org.name, {'parameters.resources': org_param})
        session.location.update(loc.name, {'parameters.resources': loc_param})
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        create_fake_host(session, host_template)
        values = session.host.read(host_name, 'parameters')
        expected_params = {(org_param['name'], org_param['value']),
                           (loc_param['name'], loc_param['value'])}
        assert expected_params.issubset(
            {(param['name'], param['value']) for param in values['parameters']['global_params']}
        )


@tier3
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


@tier3
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
        }
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


@tier3
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
        }
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


@tier3
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
                'view_lifecycle_environments'
            ]
        },
        # allow access only to the mentioned here environment
        search='name = {0}'.format(filter_lc_env.name)
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
        search='name = {0}'.format(filter_cv.name)
    )
    # Add necessary permissions for hosts as we did for lce
    create_role_permissions(
        role,
        {'Host': ['create_hosts', 'view_hosts']},
        # allow access only to the mentioned here host group
        search='hostgroup_fullname = {0}'.format(filter_hg.name)
    )
    # Add necessary permissions for host groups as we did for lce
    create_role_permissions(
        role,
        {'Hostgroup': ['view_hostgroups']},
        # allow access only to the mentioned here host group
        search='name = {0}'.format(filter_hg.name)
    )
    # Add permissions for Organization and Location
    create_role_permissions(
        role,
        {
            'Organization': PERMISSIONS['Organization'],
            'Location': PERMISSIONS['Location'],
        },
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
        {
            'name': 'host.hostgroup',
            'unexpected_value': hg.name,
            'expected_value': filter_hg.name,
        },
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
            'other_fields_values': {'host.lce': filter_lc_env.name}
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


@tier2
def test_positive_update_name(session, module_host_template):
    """Create a new Host and update its name to valid one

    :id: f1c19599-f613-431d-bf09-62addec1e60b

    :expectedresults: Host is updated successfully

    :CaseLevel: Integration
    """
    new_name = gen_string('alpha').lower()
    new_host_name = '{0}.{1}'.format(new_name, module_host_template.domain.name)
    with session:
        host_name = create_fake_host(session, module_host_template)
        assert session.host.search(host_name)[0]['Name'] == host_name
        session.host.update(host_name, {'host.name': new_name})
        assert not session.host.search(host_name)
        assert session.host.search(new_host_name)[0]['Name'] == new_host_name


@tier2
def test_positive_update_name_with_prefix(session, module_host_template):
    """Create a new Host and update its name to valid one. Host should
    contain word 'new' in its name

    :id: b08cb5c9-bd2c-4dc7-97b1-d1f20d1373d7

    :expectedresults: Host is updated successfully

    :BZ: 1419161

    :CaseLevel: Integration
    """
    new_name = 'new{0}'.format(gen_string("alpha").lower())
    new_host_name = '{0}.{1}'.format(new_name, module_host_template.domain.name)
    with session:
        host_name = create_fake_host(session, module_host_template)
        assert session.host.search(host_name)[0]['Name'] == host_name
        session.host.update(host_name, {'host.name': new_name})
        assert not session.host.search(host_name)
        assert session.host.search(new_host_name)[0]['Name'] == new_host_name


@tier2
def test_positive_search_by_parameter(session, module_org, module_loc):
    """Search for the host by global parameter assigned to it

    :id: 8e61127c-d0a0-4a46-a3c6-22d3b2c5457c

    :expectedresults: Only one specific host is returned by search

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    parameters = [{'name': param_name, 'value': param_value}]
    param_host = entities.Host(
        organization=module_org,
        location=module_loc,
        host_parameters_attributes=parameters,
    ).create()
    additional_host = entities.Host(organization=module_org, location=module_loc).create()
    with session:
        # Check that hosts present in the system
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter returns only one host in the list
        values = session.host.search('params.{0} = {1}'.format(param_name, param_value))
        assert len(values) == 1
        assert values[0]['Name'] == param_host.name


@tier2
def test_positive_search_by_parameter_with_different_values(session, module_org, module_loc):
    """Search for the host by global parameter assigned to it by its value

    :id: c3a4551e-d759-4a9d-ba90-8db4cab3db2c

    :expectedresults: Only one specific host is returned by search

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha')
    param_values = [gen_string('alpha'), gen_string('alphanumeric')]
    hosts = [
        entities.Host(
            organization=module_org,
            location=module_loc,
            host_parameters_attributes=[{'name': param_name, 'value': param_value}]
        ).create()
        for param_value in param_values
    ]
    with session:
        # Check that hosts present in the system
        for host in hosts:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter returns only one host in the list
        for param_value, host in zip(param_values, hosts):
            values = session.host.search('params.{0} = {1}'.format(param_name, param_value))
            assert len(values) == 1
            assert values[0]['Name'] == host.name


@tier2
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
        organization=org,
        location=module_loc,
        host_parameters_attributes=parameters,
    ).create()
    additional_host = entities.Host(organization=org, location=module_loc).create()
    with session:
        session.organization.select(org_name=org.name)
        # Check that the hosts are present
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter with 'not' prefix returns both hosts
        values = session.host.search('not params.{0} = {1}'.format(param_name, search_param_value))
        assert {value['Name'] for value in values} == {param_host.name, additional_host.name}


@tier2
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
    entities.CommonParameter(
        name=param_name,
        value=param_global_value
    ).create()
    parameters = [{'name': param_name, 'value': param_value}]
    param_host = entities.Host(
        organization=org,
        location=module_loc,
        host_parameters_attributes=parameters,
    ).create()
    additional_host = entities.Host(organization=org, location=module_loc).create()
    with session:
        session.organization.select(org_name=org.name)
        # Check that the hosts are present
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter with '<>' operator returns both hosts
        values = session.host.search('params.{0} <> {1}'.format(param_name, search_param_value))
        assert {value['Name'] for value in values} == {param_host.name, additional_host.name}


@tier2
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
        assert session.host.search('name = "{0}"'.format(host.name))[0]['Name'] == host.name
        assert session.host.search(host.name)[0]['Name'] == host.name


@tier2
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
        assert session.host.search('organization = "{0}"'.format(org.name))[0]['Name'] == host.name


@tier2
def test_positive_validate_inherited_cv_lce(session, module_host_template):
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
    ContentView.version_promote({
        'id': version_id,
        'to-lifecycle-environment-id': lce['id'],
        'organization-id': module_host_template.organization.id,
    })
    hostgroup = make_hostgroup({
        'content-view-id': content_view['id'],
        'lifecycle-environment-id': lce['id'],
        'organization-ids': module_host_template.organization.id,
    })
    puppet_proxy = Proxy.list({'search': 'name = {0}'.format(settings.server.hostname)})[0]
    host = make_host({
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
    })
    with session:
        values = session.host.read(host['name'], ['host.lce', 'host.content_view'])
        assert values['host']['lce'] == lce['name']
        assert values['host']['content_view'] == content_view['name']


@tier2
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
        session.hostgroup.create({
            'host_group.name': hg_name,
            'host_group.puppet_environment': env_name
        })
        assert session.hostgroup.search(hg_name)[0]['Name'] == hg_name
        values = session.host.helper.read_create_view(
            {}, ['host.puppet_environment', 'host.inherit_puppet_environment'])
        assert not values['host']['puppet_environment']
        assert values['host']['inherit_puppet_environment'] is False
        values = session.host.helper.read_create_view(
            {'host.hostgroup': hg_name},
            ['host.puppet_environment', 'host.inherit_puppet_environment']
        )
        assert values['host']['puppet_environment'] == env_name
        assert values['host']['inherit_puppet_environment'] is True
        values = session.host.helper.read_create_view(
            {'host.inherit_puppet_environment': False},
            ['host.puppet_environment', 'host.inherit_puppet_environment']
        )
        assert values['host']['puppet_environment'] == env_name
        assert values['host']['inherit_puppet_environment'] is False


@tier2
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
    entities.Environment(
        name=puppet_env, organization=[module_org], location=[module_loc]).create()
    entities.ContentView(name=content_view, organization=module_org).create()
    with session:
        session.contentview.update(content_view, {'details.force_puppet': True})
        session.contentview.publish(content_view)
        published_puppet_env = [
            env.name for env in entities.Environment().search(
                query=dict(search='organization_id={0}'.format(module_org.id), per_page=1000)
            )
            if content_view in env.name
        ][0]
        values = session.host.helper.read_create_view(
            {'host.lce': ENVIRONMENT, 'host.content_view': content_view},
            ['host.puppet_environment']
        )
        assert values['host']['puppet_environment'] == published_puppet_env
        values = session.host.helper.read_create_view(
            {'host.puppet_environment': puppet_env}, ['host.puppet_environment'])
        assert values['host']['puppet_environment'] == puppet_env
        # reset_puppet_environment
        values = session.host.helper.read_create_view(
            {'host.reset_puppet_environment': True},
            ['host.puppet_environment']
        )
        assert values['host']['puppet_environment'] == published_puppet_env


@tier3
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
                organization=module_host_template.organization, name=DEFAULT_CV).search()[0].id,
            'lifecycle_environment_id': entities.LifecycleEnvironment(
                organization=module_host_template.organization, name=ENVIRONMENT).search()[0].id
        }
    ).create()
    with session:
        session.host.update(
            host.name,
            {'parameters.host_params': [dict(name=param_name, value=param_value)]}
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


@tier3
@upgrade
def test_positive_bulk_delete_host(session, module_loc):
    """Delete a multiple hosts from the list

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
        ).create().name
        for _ in range(18)
    ]
    with session:
        session.organization.select(org_name=org.name)
        values = session.host.read_all()
        assert {host['Name'] for host in values['table']} == set(hosts_names)
        session.host.apply_action('Delete Hosts', list(hosts_names))
        values = session.host.read_all()
        assert not values['table']
