"""Test class for Hosts UI

:Requirement: Host

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Endeavour

:CaseImportance: High

"""
import copy
import csv
from datetime import datetime
import os
import re

from airgun.exceptions import DisabledWidgetError, NoSuchElementException
from airgun.session import Session
import pytest
from wait_for import wait_for
import yaml

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    DEFAULT_CV,
    DEFAULT_LOC,
    ENVIRONMENT,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_7_CUSTOM_PACKAGE,
    FAKE_8_CUSTOM_PACKAGE,
    FAKE_8_CUSTOM_PACKAGE_NAME,
    OSCAP_PERIOD,
    OSCAP_WEEKDAY,
    PERMISSIONS,
    REPO_TYPE,
)
from robottelo.utils.datafactory import gen_string
from robottelo.utils.issue_handlers import is_open


def _get_set_from_list_of_dict(value):
    """Returns a set of tuples representation of each dict sorted by keys

    :param list value: a list of simple dict.
    """
    return {tuple(sorted(list(global_param.items()), key=lambda t: t[0])) for global_param in value}


# this fixture inherits the fixture called ui_user in confest.py, method name has to be same
@pytest.fixture(scope='module')
def ui_user(ui_user, smart_proxy_location, module_target_sat):
    module_target_sat.api.User(
        id=ui_user.id,
        default_location=smart_proxy_location,
    ).update(['default_location'])
    return ui_user


@pytest.fixture
def scap_policy(scap_content, target_sat):
    scap_policy = target_sat.cli_factory.make_scap_policy(
        {
            'name': gen_string('alpha'),
            'deploy-by': 'ansible',
            'scap-content-id': scap_content["scap_id"],
            'scap-content-profile-id': scap_content["scap_profile_id"],
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
        }
    )
    return scap_policy


@pytest.fixture(scope='module')
def module_global_params(module_target_sat):
    """Create 3 global parameters and clean up at teardown"""
    global_parameters = []
    for _ in range(3):
        global_parameter = module_target_sat.api.CommonParameter(
            name=gen_string('alpha'), value=gen_string('alphanumeric')
        ).create()
        global_parameters.append(global_parameter)
    yield global_parameters
    # cleanup global parameters
    for global_parameter in global_parameters:
        global_parameter.delete()


@pytest.fixture
def tracer_install_host(rex_contenthost, target_sat):
    """Sets up a contenthost with katello-host-tools-tracer enabled,
    to prep it for install later"""
    # create a custom, rhel version-specific OS repo
    rhelver = rex_contenthost.os_version.major
    if rhelver > 7:
        rex_contenthost.create_custom_repos(**settings.repos[f'rhel{rhelver}_os'])
    else:
        rex_contenthost.create_custom_repos(
            **{f'rhel{rhelver}_os': settings.repos[f'rhel{rhelver}_os']}
        )
    return rex_contenthost


@pytest.mark.e2e
@pytest.mark.tier2
def test_positive_end_to_end(session, module_global_params, target_sat, host_ui_options):
    """Create a new Host with parameters, config group. Check host presence on
        the dashboard. Update name with 'new' prefix and delete.

    :id: d2f86309-1a6d-42dc-a865-9e607cd25ae5

    :expectedresults: Host is created with parameters, config group. Updated
        and deleted.

    :BZ: 1419161
    """
    api_values, host_name = host_ui_options
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
    new_name = f"new{gen_string('alpha').lower()}"
    new_host_name = f"{new_name}.{api_values['interfaces.interface.domain']}"
    with session:
        api_values.update(
            {
                'parameters.host_params': host_parameters,
                'parameters.global_params': [overridden_global_parameter],
            }
        )
        session.host.create(api_values)
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.read(host_name, widget_names=['parameters'])
        assert _get_set_from_list_of_dict(
            values['parameters']['host_params']
        ) == _get_set_from_list_of_dict(expected_host_parameters)
        assert _get_set_from_list_of_dict(expected_global_parameters).issubset(
            _get_set_from_list_of_dict(values['parameters']['global_params'])
        )

        # check host presence on the dashboard
        dashboard_values = session.dashboard.read('NewHosts')['hosts']
        displayed_host = [row for row in dashboard_values if row['Host'] == host_name][0]
        assert api_values['operating_system.operating_system'] in displayed_host['Operating System']
        assert displayed_host['Installed'] == 'N/A'
        # update
        session.host.update(host_name, {'host.name': new_name})
        assert not session.host.search(host_name)
        assert session.host.search(new_host_name)[0]['Name'] == new_host_name
        # delete
        session.host.delete(new_host_name)
        assert not target_sat.api.Host().search(query={'search': f'name="{new_host_name}"'})


@pytest.mark.tier4
def test_positive_read_from_details_page(session, module_host_template):
    """Create new Host and read all its content through details page

    :id: ffba5d40-918c-440e-afbb-6b910db3a8fb

    :expectedresults: Host is created and has expected content
    """

    template = module_host_template
    template.name = gen_string('alpha').lower()
    host = template.create()
    os_name = f'{template.operatingsystem.name} {template.operatingsystem.major}'
    host_name = host.name
    with session:
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.get_details(host_name)
        assert values['properties']['properties_table']['Status'] == 'OK'
        assert 'Pending installation' in values['properties']['properties_table']['Build']
        assert values['properties']['properties_table']['Domain'] == template.domain.name
        assert values['properties']['properties_table']['MAC Address'] == host.mac
        assert (
            values['properties']['properties_table']['Architecture'] == template.architecture.name
        )
        assert values['properties']['properties_table']['Operating System'] == os_name
        assert values['properties']['properties_table']['Location'] == template.location.name
        assert (
            values['properties']['properties_table']['Organization'] == template.organization.name
        )
        assert 'Admin User' in values['properties']['properties_table']['Owner']


@pytest.mark.tier4
def test_positive_read_from_edit_page(session, host_ui_options):
    """Create new Host and read all its content through edit page

    :id: 758fcab3-b363-4bfc-8f5d-173098a7e72d

    :expectedresults: Host is created and has expected content
    """
    api_values, host_name = host_ui_options
    with session:
        session.location.select(api_values['host.location'])
        session.host.create(api_values)
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.read(host_name)
        assert values['host']['name'] == host_name.partition('.')[0]
        assert values['host']['organization'] == api_values['host.organization']
        assert values['host']['location'] == api_values['host.location']
        assert values['host']['lce'] == ENVIRONMENT
        assert values['host']['content_view'] == DEFAULT_CV
        assert (
            values['operating_system']['architecture']
            == api_values['operating_system.architecture']
        )
        assert (
            values['operating_system']['operating_system']
            == api_values['operating_system.operating_system']
        )
        assert values['operating_system']['media_type'] == 'All Media'
        assert values['operating_system']['media'] == api_values['operating_system.media']
        assert values['operating_system']['ptable'] == api_values['operating_system.ptable']
        assert (
            values['interfaces']['interfaces_list'][0]['Identifier']
            == api_values['interfaces.interface.device_identifier']
        )
        assert values['interfaces']['interfaces_list'][0]['Type'] == 'Interface physical'
        assert (
            values['interfaces']['interfaces_list'][0]['MAC Address']
            == api_values['interfaces.interface.mac']
        )
        assert values['interfaces']['interfaces_list'][0]['FQDN'] == host_name
        assert session._user in values['additional_information']['owned_by']
        assert values['additional_information']['enabled'] is True


@pytest.mark.tier2
def test_positive_assign_taxonomies(
    session, module_org, smart_proxy_location, target_sat, function_org, function_location_with_org
):
    """Ensure Host organization and Location can be assigned.

    :id: 52466df5-6f56-4faa-b0f8-42b63731f494

    :expectedresults: Host Assign Organization and Location actions are
        working as expected.
    """
    host = target_sat.api.Host(organization=module_org, location=smart_proxy_location).create()
    with session:
        assert session.host.search(host.name)[0]['Name'] == host.name
        session.host.apply_action(
            'Assign Organization',
            [host.name],
            {'organization': function_org.name, 'on_mismatch': 'Fix Organization on Mismatch'},
        )
        assert not target_sat.api.Host(organization=module_org).search(
            query={'search': f'name="{host.name}"'}
        )
        assert (
            len(
                target_sat.api.Host(organization=function_org).search(
                    query={'search': f'name="{host.name}"'}
                )
            )
            == 1
        )
        session.organization.select(org_name=function_org.name)
        assert session.host.search(host.name)[0]['Name'] == host.name
        session.host.apply_action(
            'Assign Location',
            [host.name],
            {
                'location': function_location_with_org.name,
                'on_mismatch': 'Fix Location on Mismatch',
            },
        )
        assert not target_sat.api.Host(location=smart_proxy_location).search(
            query={'search': f'name="{host.name}"'}
        )
        assert (
            len(
                target_sat.api.Host(location=function_location_with_org).search(
                    query={'search': f'name="{host.name}"'}
                )
            )
            == 1
        )
        session.location.select(loc_name=function_location_with_org.name)
        assert session.host.search(host.name)[0]['Name'] == host.name
        values = session.host.get_details(host.name)
        assert values['properties']['properties_table']['Organization'] == function_org.name
        assert (
            values['properties']['properties_table']['Location'] == function_location_with_org.name
        )


@pytest.mark.skip_if_not_set('oscap')
@pytest.mark.tier2
def test_positive_assign_compliance_policy(session, scap_policy, target_sat, function_host):
    """Ensure host compliance Policy can be assigned.

    :id: 323661a4-e849-4cc2-aa39-4b4a5fe2abed

    :expectedresults: Host Assign/Unassign Compliance Policy action is working as
        expected.

    :BZ: 1862135
    """
    org = function_host.organization.read()
    loc = function_host.location.read()
    # add host organization and location to scap policy
    content = target_sat.api.ScapContents(id=scap_policy['scap-content-id']).read()
    content.organization.append(org)
    content.location.append(loc)
    target_sat.api.ScapContents(
        id=scap_policy['scap-content-id'],
        organization=content.organization,
        location=content.location,
    ).update(['organization', 'location'])

    target_sat.api.CompliancePolicies(
        id=scap_policy['id'],
        organization=content.organization,
        location=content.location,
    ).update(['organization', 'location'])
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        assert not session.host.search(f'compliance_policy = {scap_policy["name"]}')
        assert session.host.search(function_host.name)[0]['Name'] == function_host.name
        session.host.apply_action(
            'Assign Compliance Policy', [function_host.name], {'policy': scap_policy['name']}
        )
        assert (
            session.host.search(f'compliance_policy = {scap_policy["name"]}')[0]['Name']
            == function_host.name
        )
        session.host.apply_action(
            'Assign Compliance Policy', [function_host.name], {'policy': scap_policy['name']}
        )
        assert (
            session.host.search(f'compliance_policy = {scap_policy["name"]}')[0]['Name']
            == function_host.name
        )
        session.host.apply_action(
            'Unassign Compliance Policy', [function_host.name], {'policy': scap_policy['name']}
        )
        assert not session.host.search(f'compliance_policy = {scap_policy["name"]}')


@pytest.mark.skipif((settings.ui.webdriver != 'chrome'), reason='Only tested on Chrome')
@pytest.mark.tier3
def test_positive_export(session, target_sat, function_org, function_location):
    """Create few hosts and export them via UI

    :id: ffc512ad-982e-4b60-970a-41e940ebc74c

    :expectedresults: csv file contains same values as on web UI
    """
    hosts = [
        target_sat.api.Host(organization=function_org, location=function_location).create()
        for _ in range(3)
    ]
    expected_fields = {(host.name, host.operatingsystem.read().title) for host in hosts}
    with session:
        session.organization.select(function_org.name)
        session.location.select(function_location.name)
        file_path = session.host.export()
        assert os.path.isfile(file_path)
        with open(file_path, newline='') as csvfile:
            actual_fields = []
            for row in csv.DictReader(csvfile):
                actual_fields.append((row['Name'], row['Operatingsystem']))
        assert set(actual_fields) == expected_fields


@pytest.mark.tier4
def test_positive_create_with_inherited_params(
    session, target_sat, function_org, function_location_with_org
):
    """Create a new Host in organization and location with parameters

    :BZ: 1287223

    :id: 628122f2-bda9-4aa1-8833-55debbd99072

    :expectedresults: Host has inherited parameters from organization and
        location

    :CaseImportance: High
    """
    org_param = dict(name=gen_string('alphanumeric'), value=gen_string('alphanumeric'))
    loc_param = dict(name=gen_string('alphanumeric'), value=gen_string('alphanumeric'))
    host_template = target_sat.api.Host(
        organization=function_org, location=function_location_with_org
    )
    host_template.create_missing()
    host = host_template.create()
    host_name = host.name
    with session:
        session.organization.update(function_org.name, {'parameters.resources': org_param})
        session.location.update(
            function_location_with_org.name, {'parameters.resources': loc_param}
        )
        session.organization.select(org_name=function_org.name)
        session.location.select(loc_name=function_location_with_org.name)
        values = session.host.read(host_name, 'parameters')
        expected_params = {
            (org_param['name'], org_param['value']),
            (loc_param['name'], loc_param['value']),
        }
        assert expected_params.issubset(
            {(param['name'], param['value']) for param in values['parameters']['global_params']}
        )


@pytest.mark.tier4
def test_negative_delete_primary_interface(session, host_ui_options):
    """Attempt to delete primary interface of a host

    :id: bc747e2c-38d9-4920-b4ae-6010851f704e

    :customerscenario: true

    :BZ: 1417119

    :expectedresults: Interface was not deleted
    """
    values, host_name = host_ui_options
    interface_id = values['interfaces.interface.device_identifier']
    with session:
        session.location.select(values['host.location'])
        session.host.create(values)
        with pytest.raises(DisabledWidgetError) as context:
            session.host.delete_interface(host_name, interface_id)
        assert 'Interface Delete button is disabled' in str(context.value)


@pytest.mark.tier2
def test_positive_view_hosts_with_non_admin_user(
    test_name, module_org, smart_proxy_location, target_sat
):
    """View hosts and content hosts as a non-admin user with only view_hosts, edit_hosts
    and view_organization permissions

    :BZ: 1642076, 1801630

    :customerscenario: true

    :id: 19a07026-0550-11ea-bfdc-98fa9b6ecd5a

    :expectedresults: user with only view_hosts, edit_hosts and view_organization permissions
        is able to read content hosts and hosts
    """
    user_password = gen_string('alpha')
    role = target_sat.api.Role(organization=[module_org]).create()
    target_sat.api_factory.create_role_permissions(
        role, {'Organization': ['view_organizations'], 'Host': ['view_hosts']}
    )
    user = target_sat.api.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[module_org],
        location=[smart_proxy_location],
        default_organization=module_org,
        default_location=smart_proxy_location,
    ).create()
    created_host = target_sat.api.Host(
        location=smart_proxy_location, organization=module_org
    ).create()
    with Session(test_name, user=user.login, password=user_password) as session:
        host = session.host.get_details(created_host.name, widget_names='breadcrumb')
        assert host['breadcrumb'] == created_host.name
        content_host = session.contenthost.read(created_host.name, widget_names='breadcrumb')
        assert content_host['breadcrumb'] == created_host.name


@pytest.mark.tier3
def test_positive_remove_parameter_non_admin_user(
    test_name, module_org, smart_proxy_location, target_sat
):
    """Remove a host parameter as a non-admin user with enough permissions

    :BZ: 1996035

    :id: 598111c1-fdb6-42e9-8c28-fae999b5d112

    :expectedresults: user with sufficient permissions may remove host
        parameter
    """
    user_password = gen_string('alpha')
    parameter = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
    role = target_sat.api.Role(organization=[module_org]).create()
    target_sat.api_factory.create_role_permissions(
        role,
        {
            'Parameter': PERMISSIONS['Parameter'],
            'Host': PERMISSIONS['Host'],
            'Operatingsystem': ['view_operatingsystems'],
        },
    )
    user = target_sat.api.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[module_org],
        location=[smart_proxy_location],
        default_organization=module_org,
        default_location=smart_proxy_location,
    ).create()
    host = target_sat.api.Host(
        content_facet_attributes={
            'content_view_id': module_org.default_content_view.id,
            'lifecycle_environment_id': module_org.library.id,
        },
        location=smart_proxy_location,
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
@pytest.mark.skip_if_open("BZ:2059576")
def test_negative_remove_parameter_non_admin_user(
    test_name, module_org, smart_proxy_location, target_sat
):
    """Attempt to remove host parameter as a non-admin user with
    insufficient permissions

    :BZ: 1317868

    :id: 78fd230e-2ec4-4158-823b-ddbadd5e232f

    :customerscenario: true

    :expectedresults: user with insufficient permissions is unable to
        remove host parameter, 'Remove' link is not visible for him
    """

    user_password = gen_string('alpha')
    parameter = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
    role = target_sat.api.Role(organization=[module_org]).create()
    target_sat.api_factory.create_role_permissions(
        role,
        {
            'Parameter': ['view_params'],
            'Host': PERMISSIONS['Host'],
            'Operatingsystem': ['view_operatingsystems'],
        },
    )
    user = target_sat.api.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[module_org],
        location=[smart_proxy_location],
        default_organization=module_org,
        default_location=smart_proxy_location,
    ).create()
    host = target_sat.api.Host(
        content_facet_attributes={
            'content_view_id': module_org.default_content_view.id,
            'lifecycle_environment_id': module_org.library.id,
        },
        location=smart_proxy_location,
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
def test_positive_check_permissions_affect_create_procedure(
    test_name, smart_proxy_location, target_sat, function_org, function_role
):
    """Verify whether user permissions affect what entities can be selected
    when host is created

    :id: 4502f99d-86fb-4655-a9dc-b2612cf849c6

    :customerscenario: true

    :expectedresults: user with specific permissions can choose only
        entities for create host procedure that he has access to

    :BZ: 1293716
    """
    # Create two lifecycle environments
    lc_env = target_sat.api.LifecycleEnvironment(organization=function_org).create()
    filter_lc_env = target_sat.api.LifecycleEnvironment(organization=function_org).create()
    # Create two content views and promote them to one lifecycle
    # environment which will be used in filter
    cv = target_sat.api.ContentView(organization=function_org).create()
    filter_cv = target_sat.api.ContentView(organization=function_org).create()
    for content_view in [cv, filter_cv]:
        content_view.publish()
        content_view = content_view.read()
        content_view.version[0].promote(data={'environment_ids': filter_lc_env.id})
    # Create two host groups
    hg = target_sat.api.HostGroup(organization=[function_org]).create()
    filter_hg = target_sat.api.HostGroup(organization=[function_org]).create()
    # Create lifecycle environment permissions and select one specific
    # environment user will have access to
    target_sat.api_factory.create_role_permissions(
        function_role,
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
    target_sat.api_factory.create_role_permissions(
        function_role,
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
    target_sat.api_factory.create_role_permissions(
        function_role,
        {'Host': ['create_hosts', 'view_hosts']},
        # allow access only to the mentioned here host group
        search=f'hostgroup_fullname = {filter_hg.name}',
    )
    # Add necessary permissions for host groups as we did for lce
    target_sat.api_factory.create_role_permissions(
        function_role,
        {'Hostgroup': ['view_hostgroups']},
        # allow access only to the mentioned here host group
        search=f'name = {filter_hg.name}',
    )
    # Add permissions for Organization and Location
    target_sat.api_factory.create_role_permissions(
        function_role,
        {'Organization': PERMISSIONS['Organization'], 'Location': PERMISSIONS['Location']},
    )
    # Create new user with a configured role
    user_password = gen_string('alpha')
    user = target_sat.api.User(
        role=[function_role],
        admin=False,
        password=user_password,
        organization=[function_org],
        location=[smart_proxy_location],
        default_organization=function_org,
        default_location=smart_proxy_location,
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
            values = {host_field['name']: host_field['unexpected_value']}
            values.update(host_field.get('other_fields_values', {}))
            with pytest.raises(NoSuchElementException) as context:
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
def test_positive_search_by_parameter(session, module_org, smart_proxy_location, target_sat):
    """Search for the host by global parameter assigned to it

    :id: 8e61127c-d0a0-4a46-a3c6-22d3b2c5457c

    :expectedresults: Only one specific host is returned by search

    :BZ: 1725686
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    parameters = [{'name': param_name, 'value': param_value}]
    param_host = target_sat.api.Host(
        organization=module_org,
        location=smart_proxy_location,
        host_parameters_attributes=parameters,
    ).create()
    additional_host = target_sat.api.Host(
        organization=module_org, location=smart_proxy_location
    ).create()
    with session:
        # Check that hosts present in the system
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter returns only one host in the list
        values = session.host.search(f'params.{param_name} = {param_value}')
        assert len(values) == 1
        assert values[0]['Name'] == param_host.name


@pytest.mark.tier4
def test_positive_search_by_parameter_with_different_values(
    session, module_org, smart_proxy_location, target_sat
):
    """Search for the host by global parameter assigned to it by its value

    :id: c3a4551e-d759-4a9d-ba90-8db4cab3db2c

    :expectedresults: Only one specific host is returned by search

    :BZ: 1725686
    """
    param_name = gen_string('alpha')
    param_values = [gen_string('alpha'), gen_string('alphanumeric')]
    hosts = [
        target_sat.api.Host(
            organization=module_org,
            location=smart_proxy_location,
            host_parameters_attributes=[{'name': param_name, 'value': param_value}],
        ).create()
        for param_value in param_values
    ]
    with session:
        # Check that hosts present in the system
        for host in hosts:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter returns only one host in the list
        for param_value, host in zip(param_values, hosts, strict=True):
            values = session.host.search(f'params.{param_name} = {param_value}')
            assert len(values) == 1
            assert values[0]['Name'] == host.name


@pytest.mark.tier2
def test_positive_search_by_parameter_with_prefix(
    session, smart_proxy_location, target_sat, function_org
):
    """Search by global parameter assigned to host using prefix 'not' and
    any random string as parameter value to make sure that all hosts will
    be present in the list

    :id: a4affb90-1222-4d9a-94be-213f9e5be573

    :expectedresults: All assigned hosts to organization are returned by
        search
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    search_param_value = gen_string('alphanumeric')
    parameters = [{'name': param_name, 'value': param_value}]
    param_host = target_sat.api.Host(
        organization=function_org,
        location=smart_proxy_location,
        host_parameters_attributes=parameters,
    ).create()
    additional_host = target_sat.api.Host(
        organization=function_org, location=smart_proxy_location
    ).create()
    with session:
        session.organization.select(org_name=function_org.name)
        # Check that the hosts are present
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter with 'not' prefix returns both hosts
        values = session.host.search(f'not params.{param_name} = {search_param_value}')
        assert {value['Name'] for value in values} == {param_host.name, additional_host.name}


@pytest.mark.tier2
def test_positive_search_by_parameter_with_operator(
    session, smart_proxy_location, target_sat, function_org
):
    """Search by global parameter assigned to host using operator '<>' and
    any random string as parameter value to make sure that all hosts will
    be present in the list

    :id: 264065b7-0d04-467d-887a-0aba0d871b7c

    :expectedresults: All assigned hosts to organization are returned by
        search

    :BZ: 1463806
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    param_global_value = gen_string('numeric')
    search_param_value = gen_string('alphanumeric')
    target_sat.api.CommonParameter(name=param_name, value=param_global_value).create()
    parameters = [{'name': param_name, 'value': param_value}]
    param_host = target_sat.api.Host(
        organization=function_org,
        location=smart_proxy_location,
        host_parameters_attributes=parameters,
    ).create()
    additional_host = target_sat.api.Host(
        organization=function_org, location=smart_proxy_location
    ).create()
    with session:
        session.organization.select(org_name=function_org.name)
        # Check that the hosts are present
        for host in [param_host, additional_host]:
            assert session.host.search(host.name)[0]['Name'] == host.name
        # Check that search by parameter with '<>' operator returns both hosts
        values = session.host.search(f'params.{param_name} <> {search_param_value}')
        assert {value['Name'] for value in values} == {param_host.name, additional_host.name}


@pytest.mark.tier2
def test_positive_search_with_org_and_loc_context(
    session, target_sat, function_org, function_location
):
    """Perform usual search for host, but organization and location used
    for host create procedure should have 'All capsules' checkbox selected

    :id: 2ce50df0-2b30-42cc-a40b-0e1f4fde3c6f

    :expectedresults: Search functionality works as expected and correct
        result is returned

    :BZ: 1405496

    :customerscenario: true
    """
    host = target_sat.api.Host(organization=function_org, location=function_location).create()
    with session:
        session.organization.update(function_org.name, {'capsules.all_capsules': True})
        session.location.update(function_location.name, {'capsules.all_capsules': True})
        session.organization.select(org_name=function_org.name)
        session.location.select(loc_name=function_location.name)
        assert session.host.search(f'name = "{host.name}"')[0]['Name'] == host.name
        assert session.host.search(host.name)[0]['Name'] == host.name


@pytest.mark.tier2
def test_positive_search_by_org(session, smart_proxy_location, target_sat):
    """Search for host by specifying host's organization name

    :id: a3bb5bc5-cb9c-4b56-b383-f3e4d3d4d222

    :customerscenario: true

    :expectedresults: Search functionality works as expected and correct
        result is returned

    :BZ: 1447958
    """
    host = target_sat.api.Host(location=smart_proxy_location).create()
    org = host.organization.read()
    with session:
        session.organization.select(org_name=ANY_CONTEXT['org'])
        assert session.host.search(f'organization = "{org.name}"')[0]['Name'] == host.name


@pytest.mark.tier2
def test_positive_validate_inherited_cv_lce_ansiblerole(session, target_sat, module_host_template):
    """Create a host with hostgroup specified via CLI. Make sure host
    inherited hostgroup's lifecycle environment, content view and both
    fields are properly reflected via WebUI. Also host should be searchable by the
    inherited ansible role.

    :id: c83f6819-2649-4a8b-bb1d-ce93b2243765

    :expectedresults: Host's lifecycle environment, content view and ansible role match
       the ones specified in hostgroup.

    :customerscenario: true

    :BZ: 1391656, 2094912
    """
    SELECTED_ROLE = 'RedHatInsights.insights-client'
    cv_name = gen_string('alpha')
    lce_name = gen_string('alphanumeric')
    cv = target_sat.api_factory.cv_publish_promote(
        name=cv_name, env_name=lce_name, org_id=module_host_template.organization.id
    )
    lce = (
        target_sat.api.LifecycleEnvironment()
        .search(
            query={
                'search': f'name={lce_name} '
                f'and organization_id={module_host_template.organization.id}'
            }
        )[0]
        .read()
    )
    target_sat.cli.Ansible.roles_sync(
        {'role-names': SELECTED_ROLE, 'proxy-id': target_sat.nailgun_smart_proxy.id}
    )
    hostgroup = target_sat.cli_factory.hostgroup(
        {
            'content-view-id': cv.id,
            'lifecycle-environment-id': lce.id,
            'organization-ids': module_host_template.organization.id,
        }
    )
    result = target_sat.cli.HostGroup.ansible_roles_assign(
        {'name': hostgroup.name, 'ansible-roles': SELECTED_ROLE}
    )
    assert 'Ansible roles were assigned to the hostgroup' in result[0]['message']
    result = target_sat.cli.HostGroup.ansible_roles_add(
        {'name': hostgroup.name, 'ansible-role': SELECTED_ROLE}
    )
    assert 'Ansible role has been associated.' in result[0]['message']
    host = target_sat.cli_factory.make_host(
        {
            'architecture-id': module_host_template.architecture.id,
            'domain-id': module_host_template.domain.id,
            'hostgroup-id': hostgroup['id'],
            'location-id': module_host_template.location.id,
            'medium-id': module_host_template.medium.id,
            'operatingsystem-id': module_host_template.operatingsystem.id,
            'organization-id': module_host_template.organization.id,
            'partition-table-id': module_host_template.ptable.id,
        }
    )
    with session:
        values = session.host.read(host['name'], ['host.lce', 'host.content_view'])
        assert values['host']['lce'] == lce.name
        assert values['host']['content_view'] == cv.name
        matching_hosts = target_sat.api.Host().search(
            query={'search': f'ansible_role="{SELECTED_ROLE}"'}
        )
        assert len(matching_hosts), 'Host not found by inherited ansible role'
        assert host.name in [host.name for host in matching_hosts]


@pytest.mark.tier2
def test_positive_global_registration_form(
    session, module_activation_key, module_org, smart_proxy_location, default_os, target_sat
):
    """Host registration form produces a correct curl command for various inputs

    :id: f81c2ec4-85b1-4372-8e63-464ddbf70296

    :customerscenario: true

    :expectedresults: The curl command contains all required parameters
    """
    # rex and insights parameters are only specified in curl when differing from
    # inerited parameters
    result = (
        target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_remote_execution'})[0]
        .read()
    )
    rex_value = not result.value
    result = (
        target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_insights'})[0]
        .read()
    )
    insights_value = not result.value
    hostgroup = target_sat.api.HostGroup(
        organization=[module_org], location=[smart_proxy_location]
    ).create()
    iface = 'eth0'
    with session:
        cmd = session.host.get_register_command(
            {
                'advanced.setup_insights': 'Yes (override)' if insights_value else 'No (override)',
                'advanced.setup_rex': 'Yes (override)' if rex_value else 'No (override)',
                'general.insecure': True,
                'general.host_group': hostgroup.name,
                'general.operating_system': default_os.title,
                'general.activation_keys': module_activation_key.name,
                'advanced.update_packages': True,
                'advanced.rex_interface': iface,
            }
        )
    expected_pairs = [
        f'organization_id={module_org.id}',
        f'activation_keys={module_activation_key.name}',
        f'hostgroup_id={hostgroup.id}',
        f'location_id={smart_proxy_location.id}',
        f'operatingsystem_id={default_os.id}',
        f'remote_execution_interface={iface}',
        f'setup_insights={"true" if insights_value else "false"}',
        f'setup_remote_execution={"true" if rex_value else "false"}',
        f'{target_sat.hostname}',
        'insecure',
        'update_packages=true',
    ]
    for pair in expected_pairs:
        assert pair in cmd


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_global_registration_end_to_end(
    session,
    module_activation_key,
    module_org,
    smart_proxy_location,
    default_os,
    default_smart_proxy,
    rhel_contenthost,
    target_sat,
):
    """Host registration form produces a correct registration command and host is
    registered successfully with it, remote execution and insights are set up

    :id: a02658bf-097e-47a8-8472-5d9f649ba07a

    :customerscenario: true

    :BZ: 1993874

    :expectedresults: Host is successfully registered, remote execution and insights
         client work out of the box

    :parametrized: yes
    """
    # make sure global parameters for rex and insights are set to true
    insights_cp = (
        target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_insights'})[0]
        .read()
    )
    rex_cp = (
        target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_remote_execution'})[0]
        .read()
    )

    if not insights_cp.value:
        target_sat.api.CommonParameter(id=insights_cp.id, value=1).update(['value'])
    if not rex_cp.value:
        target_sat.api.CommonParameter(id=rex_cp.id, value=1).update(['value'])

    # rex interface
    iface = 'eth0'
    # fill in the global registration form
    with session:
        cmd = session.host.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.activation_keys': module_activation_key.name,
                'advanced.update_packages': True,
                'advanced.rex_interface': iface,
                'general.insecure': True,
            }
        )
    expected_pairs = [
        f'organization_id={module_org.id}',
        f'activation_keys={module_activation_key.name}',
        f'location_id={smart_proxy_location.id}',
        f'operatingsystem_id={default_os.id}',
        f'{default_smart_proxy.name}',
        'insecure',
        'update_packages=true',
    ]
    for pair in expected_pairs:
        assert pair in cmd
    # rhel repo required for insights client installation,
    # syncing it to the satellite would take too long
    rhelver = rhel_contenthost.os_version.major
    if rhelver > 7:
        rhel_contenthost.create_custom_repos(**settings.repos[f'rhel{rhelver}_os'])
    else:
        rhel_contenthost.create_custom_repos(
            **{f'rhel{rhelver}_os': settings.repos[f'rhel{rhelver}_os']}
        )
    # make sure there will be package availabe for update
    if rhel_contenthost.os_version.major == '6':
        package = FAKE_1_CUSTOM_PACKAGE
        repo_url = settings.repos.yum_1['url']
    else:
        package = FAKE_7_CUSTOM_PACKAGE
        repo_url = settings.repos.yum_3['url']
    rhel_contenthost.create_custom_repos(fake_yum=repo_url)
    rhel_contenthost.execute(f"yum install -y {package}")
    # run curl
    result = rhel_contenthost.execute(cmd)
    assert result.status == 0
    result = rhel_contenthost.execute('subscription-manager identity')
    assert result.status == 0
    # Assert that a yum update was made this day ("Update" or "I, U" in history)
    timezone_offset = rhel_contenthost.execute('date +"%:z"').stdout.strip()
    tzinfo = datetime.strptime(timezone_offset, '%z').tzinfo
    result = rhel_contenthost.execute('yum history | grep U')
    assert result.status == 0
    assert datetime.now(tzinfo).strftime('%Y-%m-%d') in result.stdout
    # Set "Connect to host using IP address"
    target_sat.api.Parameter(
        host=rhel_contenthost.hostname,
        name='remote_execution_connect_by_ip',
        parameter_type='boolean',
        value='True',
    ).create()
    # run insights-client via REX
    command = "insights-client --status"
    invocation_command = target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Run Command - Script Default',
            'inputs': f'command={command}',
            'search-query': f"name ~ {rhel_contenthost.hostname}",
        }
    )
    # results provide all info but job invocation might not be finished yet
    result = (
        target_sat.api.JobInvocation()
        .search(
            query={'search': f'id={invocation_command["id"]} and host={rhel_contenthost.hostname}'}
        )[0]
        .read()
    )
    # make sure that task is finished
    task_result = target_sat.wait_for_tasks(
        search_query=(f'id = {result.task.id}'), search_rate=2, max_tries=60
    )
    assert task_result[0].result == 'success'
    host = (
        target_sat.api.Host()
        .search(query={'search': f'name={rhel_contenthost.hostname}'})[0]
        .read()
    )
    for interface in host.interface:
        interface_result = target_sat.api.Interface(host=host.id).search(
            query={'search': f'{interface.id}'}
        )[0]
        # more interfaces can be inside the host
        if interface_result.identifier == iface:
            assert interface_result.execution


@pytest.mark.tier2
def test_global_registration_form_populate(
    module_org,
    session,
    module_ak_with_cv,
    module_lce,
    module_promoted_cv,
    default_architecture,
    default_os,
    target_sat,
):
    """Host registration form should be populated automatically based on the host-group

    :id: b949e010-36b8-48b8-9907-36138342c72b

    :expectedresults: Some of the fields in the form should be populated based on host-group
        e.g. activation key, operating system, life-cycle environment, host parameters for
        remote-execution, insights setup.

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. create the host-group with activation key, operating system, host-parameters
        4. Open the global registration form and select the same host-group
        5. check host registration form should be populated automatically based on the host-group

    :BZ: 2056469

    :CaseAutomation: Automated
    """
    hg_name = gen_string('alpha')
    iface = gen_string('alpha')
    group_params = {'name': 'host_packages', 'value': constants.FAKE_0_CUSTOM_PACKAGE}
    target_sat.api.HostGroup(
        name=hg_name,
        organization=[module_org],
        lifecycle_environment=module_lce,
        architecture=default_architecture,
        operatingsystem=default_os,
        content_view=module_promoted_cv,
        group_parameters_attributes=[group_params],
    ).create()
    with session:
        session.hostgroup.update(
            hg_name,
            {
                'activation_keys.activation_keys': module_ak_with_cv.name,
            },
        )
        cmd = session.host.get_register_command(
            {
                'general.host_group': hg_name,
                'advanced.rex_interface': iface,
                'general.insecure': True,
            },
            full_read=True,
        )

        assert hg_name in cmd['general']['host_group']
        assert module_ak_with_cv.name in cmd['general']['activation_key_helper']
        assert module_lce.name in cmd['advanced']['life_cycle_env_helper']
        assert constants.FAKE_0_CUSTOM_PACKAGE in cmd['advanced']['install_packages_helper']


@pytest.mark.tier2
def test_global_registration_with_capsule_host(
    session,
    capsule_configured,
    rhel8_contenthost,
    module_org,
    module_location,
    module_product,
    default_os,
    module_lce_library,
    target_sat,
):
    """Host registration form produces a correct registration command and host is
    registered successfully with selected capsule from form.

    :id: 6356c6d0-ee45-4ad7-8a0e-484d3490bc58

    :expectedresults: Host is successfully registered with capsule host,
        remote execution and insights client work out of the box

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. integrate capsule and sync content
        4. open the global registration form and select the same capsule
        5. check host is registered successfully with selected capsule

    :parametrized: yes

    :CaseAutomation: Automated
    """
    client = rhel8_contenthost
    repo = target_sat.api.Repository(
        url=settings.repos.yum_1.url,
        content_type=REPO_TYPE['yum'],
        product=module_product,
    ).create()
    # Sync all repositories in the product
    module_product.sync()
    capsule = target_sat.api.Capsule(id=capsule_configured.nailgun_capsule.id).search(
        query={'search': f'name={capsule_configured.hostname}'}
    )[0]
    module_org = target_sat.api.Organization(id=module_org.id).read()
    module_org.smart_proxy.append(capsule)
    module_location = target_sat.api.Location(id=module_location.id).read()
    module_location.smart_proxy.append(capsule)
    module_org.update(['smart_proxy'])
    module_location.update(['smart_proxy'])

    # Associate the lifecycle environment with the capsule
    capsule.content_add_lifecycle_environment(data={'environment_id': module_lce_library.id})
    result = capsule.content_lifecycle_environments()
    # TODO result is not used, please add assert once you fix the test

    # Create a content view with the repository
    cv = target_sat.api.ContentView(organization=module_org, repository=[repo]).create()

    # Publish new version of the content view
    cv.publish()
    cv = cv.read()

    assert len(cv.version) == 1

    activation_key = target_sat.api.ActivationKey(
        content_view=cv, environment=module_lce_library, organization=module_org
    ).create()

    # Assert that a task to sync lifecycle environment to the capsule
    # is started (or finished already)
    sync_status = capsule.content_get_sync()
    assert len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']

    # Wait till capsule sync finishes
    for task in sync_status['active_sync_tasks']:
        target_sat.api.ForemanTask(id=task['id']).poll()
    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        cmd = session.host.get_register_command(
            {
                'general.organization': module_org.name,
                'general.location': module_location.name,
                'general.operating_system': default_os.title,
                'general.capsule': capsule_configured.hostname,
                'general.activation_keys': activation_key.name,
                'general.insecure': True,
            }
        )
    client.create_custom_repos(rhel7=settings.repos.rhel7_os)
    # run curl
    client.execute(cmd)
    result = client.execute('subscription-manager identity')
    assert result.status == 0
    assert module_lce_library.name in result.stdout
    assert module_org.name in result.stdout


@pytest.mark.tier2
@pytest.mark.usefixtures('enable_capsule_for_registration')
@pytest.mark.no_containers
def test_global_registration_with_gpg_repo_and_default_package(
    session, module_activation_key, default_os, default_smart_proxy, rhel8_contenthost
):
    """Host registration form produces a correct registration command and host is
    registered successfully with gpg repo enabled and have default package
    installed.

    :id: b5738b20-e281-4d0b-ac78-dcdc177b8c9f

    :expectedresults: Host is successfully registered, gpg repo is enabled
        and default package is installed.

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. update the 'host_packages' parameter in organization with package name e.g. vim
        4. open the global registration form and update the gpg repo and key
        5. check host is registered successfully with installed same package
        6. check gpg repo is exist in registered host

    :parametrized: yes
    """
    client = rhel8_contenthost
    repo_name = 'foreman_register'
    repo_url = settings.repos.gr_yum_repo.url
    repo_gpg_url = settings.repos.gr_yum_repo.gpg_url
    with session:
        cmd = session.host.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.capsule': default_smart_proxy.name,
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.install_packages': 'mlocate vim',
                'advanced.repository': repo_url,
                'advanced.repository_gpg_key_url': repo_gpg_url,
            }
        )

    # rhel repo required for insights client installation,
    # syncing it to the satellite would take too long
    rhelver = client.os_version.major
    if rhelver > 7:
        repos = {f'rhel{rhelver}_os': settings.repos[f'rhel{rhelver}_os']['baseos']}
    else:
        repos = {
            'rhel7_os': settings.repos['rhel7_os'],
            'rhel7_extras': settings.repos['rhel7_extras'],
        }
    client.create_custom_repos(**repos)
    # run curl
    result = client.execute(cmd)
    assert result.status == 0
    result = client.execute('yum list installed | grep mlocate')
    assert result.status == 0
    assert 'mlocate' in result.stdout
    result = client.execute(f'yum -v repolist {repo_name}')
    assert result.status == 0
    assert repo_url in result.stdout


@pytest.mark.tier2
@pytest.mark.rhel_ver_match('[^6].*')
def test_global_registration_upgrade_subscription_manager(
    session, module_activation_key, module_os, rhel_contenthost
):
    """Host registration form produces a correct registration command and
    subscription-manager can be updated from a custom repository before
    registration is completed.

    :id: b7a44f32-90b2-4fd6-b65b-5a3d2a5c5deb

    :customerscenario: true

    :expectedresults: Host is successfully registered, repo is enabled
        on advanced tab and subscription-manager is updated.

    :steps:
        1. Create activation-key
        2. Open the global registration form, add repo and activation key
        3. Add 'subscription-manager' to install packages field
        4. Check subscription-manager was installed from repo_name

    :parametrized: yes

    :BZ: 1923320
    """
    client = rhel_contenthost
    repo_name = 'foreman_register'
    rhel_ver = rhel_contenthost.os_version.major
    repo_url = settings.repos.get(f'rhel{rhel_ver}_os')
    if isinstance(repo_url, dict):
        repo_url = repo_url['baseos']
    # Ensure subs-man is installed from repo_name by removing existing package.
    result = client.execute('rpm --erase --nodeps subscription-manager')
    assert result.status == 0
    with session:
        cmd = session.host.get_register_command(
            {
                'general.operating_system': module_os.title,
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.install_packages': 'subscription-manager',
                'advanced.repository': repo_url,
            }
        )

    # run curl
    result = client.execute(cmd)
    assert result.status == 0
    result = client.execute('yum repolist')
    assert repo_name in result.stdout
    assert result.status == 0


@pytest.mark.tier3
@pytest.mark.usefixtures('enable_capsule_for_registration')
def test_global_re_registration_host_with_force_ignore_error_options(
    session, module_activation_key, default_os, default_smart_proxy, rhel7_contenthost
):
    """If the ignore_error and force checkbox is checked then registered host can
    get re-registered without any error.

    :id: 8f0ecc13-5d18-4adb-acf5-3f3276dccbb7

    :expectedresults: Verify the force and ignore checkbox options

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. open the global registration form and select --force and --Ignore Errors option
        4. registered the host with generated curl command
        5. re-register the same host again and check it is getting registered

    :parametrized: yes
    """
    client = rhel7_contenthost
    with session:
        cmd = session.host.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.capsule': default_smart_proxy.name,
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.ignore_error': True,
            }
        )
    client.execute(cmd)
    result = client.execute('subscription-manager identity')
    assert result.status == 0
    # rerun the register command
    client.execute(cmd)
    result = client.execute('subscription-manager identity')
    assert result.status == 0


@pytest.mark.tier2
@pytest.mark.usefixtures('enable_capsule_for_registration')
def test_global_registration_token_restriction(
    session, module_activation_key, rhel8_contenthost, default_os, default_smart_proxy, target_sat
):
    """Global registration token should be only used for registration call, it
    should be restricted for any other api calls.

    :id: 4528b5c6-0a6d-40cd-857a-68b76db2179b

    :expectedresults: global registration token should be restricted for any api calls
        other than the registration

    :steps:
        1. open the global registration form and generate the curl token
        2. use that curl token to execute other api calls e.g. GET /hosts, /users

    :parametrized: yes
    """
    client = rhel8_contenthost
    with session:
        cmd = session.host.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.capsule': default_smart_proxy.name,
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
            }
        )

    pattern = re.compile("Authorization.*(?=')")
    auth_header = re.search(pattern, cmd).group()

    # build curl
    curl_users = f'curl -X GET -k -H {auth_header} -i {target_sat.url}/api/users/'
    curl_hosts = f'curl -X GET -k -H {auth_header} -i {target_sat.url}/api/hosts/'
    for curl_cmd in (curl_users, curl_hosts):
        result = client.execute(curl_cmd)
        assert result.status == 0
        assert 'Unable to authenticate user' in result.stdout


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_bulk_delete_host(session, smart_proxy_location, target_sat, function_org):
    """Delete multiple hosts from the list

    :id: 8da2084a-8b50-46dc-b305-18eeb80d01e0

    :expectedresults: All selected hosts should be deleted successfully

    :BZ: 1368026
    """
    host_template = target_sat.api.Host(organization=function_org, location=smart_proxy_location)
    host_template.create_missing()
    hosts_names = [
        target_sat.api.Host(
            organization=function_org,
            location=smart_proxy_location,
            root_pass=host_template.root_pass,
            architecture=host_template.architecture,
            domain=host_template.domain,
            medium=host_template.medium,
            operatingsystem=host_template.operatingsystem,
            ptable=host_template.ptable,
        )
        .create()
        .name
        for _ in range(3)
    ]
    with session:
        session.organization.select(org_name=function_org.name)
        values = session.host.read_all()
        assert len(hosts_names) == len(values['table'])
        session.host.delete_hosts('All')
        values = session.host.read_all()
        assert not values['table']


# ------------------------------ NEW HOST UI DETAILS ----------------------------
@pytest.mark.tier4
def test_positive_read_details_page_from_new_ui(session, host_ui_options):
    """Create new Host and read all its content through details page

    :id: ef0c5942-9049-11ec-8029-98fa9b6ecd5a

    :expectedresults: Host is created and has expected content
    """
    with session:
        api_values, host_name = host_ui_options
        session.location.select(api_values['host.location'])
        session.host_new.create(api_values)
        assert session.host_new.search(host_name)[0]['Name'] == host_name
        values = session.host_new.get_details(host_name, widget_names='overview')
        assert values['overview']['host_status']['status'] == 'All statuses OK'
        assert (
            values['overview']['details']['details']['mac_address']
            == api_values['interfaces.interface.mac']
        )
        user = session.host_new.get_details(host_name, widget_names='current_user')['current_user']
        assert values['overview']['details']['details']['host_owner'] == user
        assert values['overview']['details']['details']['comment'] == 'Host with fake data'


@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
def test_rex_new_ui(session, target_sat, rex_contenthost):
    """Run remote execution using the new host details page

    :id: ee625595-4995-43b2-9e6d-633c9b33ff93

    :steps:
        1. Navigate to Overview tab
        2. Schedule a job
        3. Wait for the job to finish
        4. Job is visible in Recent jobs card

    :expectedresults: Remote execution succeeded and the job is visible on Recent jobs card on
        Overview tab
    """
    hostname = rex_contenthost.hostname
    job_args = {
        'job_category': 'Commands',
        'job_template': 'Run Command - Script Default',
        'template_content.command': 'ls',
    }
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        session.host_new.schedule_job(hostname, job_args)
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run ls on {hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        recent_jobs = session.host_new.get_details(hostname, "overview.recent_jobs")['overview']
        assert "Run ls" == recent_jobs['recent_jobs']['finished']['table'][0]['column0']
        assert "succeeded" == recent_jobs['recent_jobs']['finished']['table'][0]['column2']


@pytest.mark.tier4
def test_positive_manage_table_columns(session, current_sat_org, current_sat_location):
    """Set custom columns of the hosts table.

    :id: e5e18982-cc43-11ed-8562-000c2989e153

    :steps:
        1. Navigate to the Hosts page.
        2. Switch to default organization and location, where is at least one host (Satellite).
        3. Set custom columns for the hosts table via the 'Manage columns' dialog.

    :expectedresults: Check if the custom columns were set properly, i.e., are displayed
        or not displayed in the table.

    :BZ: 1813274

    :customerscenario: true
    """
    columns = {
        'Host group': False,
        'Last report': False,
        'Comment': False,
        'Installable updates': True,
        'Registered': True,
        'Last checkin': True,
        'IPv4': True,
        'MAC': True,
        'Sockets': True,
        'Cores': True,
        'RAM': True,
        'Boot time': True,
        'Recommendations': False,
    }
    with session:
        session.organization.select(org_name=current_sat_org)
        session.location.select(loc_name=current_sat_location)
        session.host.manage_table_columns(columns)
        displayed_columns = session.host.get_displayed_table_headers()
        for column, is_displayed in columns.items():
            assert (column in displayed_columns) is is_displayed


@pytest.mark.tier4
def test_positive_host_details_read_templates(
    session, target_sat, current_sat_org, current_sat_location
):
    """Check if all assigned host provisioning templates are correctly reported
    in host detail / Details tab / Provisioning templates card.

    :id: 43ca722e-d28a-11ed-8970-000c2989e153

    :steps:
        1. Go to Hosts page and select the Satellite host machine.
        2. Go to the Details tab.
        3. Gather all names from the `Provisioning templates` card.
        4. Compare them with the host provisioning templates obtained via API.

    :expectedresults: Provisioning templates reported via API and in UI should match.

    :BZ: 2128038

    :customerscenario: true
    """
    host = target_sat.api.Host().search(query={'search': f'name={target_sat.hostname}'})[0]
    api_templates = [template['name'] for template in host.list_provisioning_templates()]
    with session:
        session.organization.select(org_name=current_sat_org)
        session.location.select(loc_name=current_sat_location)
        host_detail = session.host_new.get_details(target_sat.hostname, widget_names='details')
        ui_templates = [
            row['column1'].strip()
            for row in host_detail['details']['provisioning_templates']['templates_table']
        ]
    assert set(api_templates) == set(ui_templates)


@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
@pytest.mark.no_containers
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel8',
            'YumRepository': {'url': settings.repos.yum_3.url},
        }
    ],
    ids=['yum3'],
    indirect=True,
)
def test_positive_update_delete_package(
    session,
    target_sat,
    rhel_contenthost,
    module_repos_collection_with_setup,
):
    """Update a package on a host using the new Content tab

    :id: ffc19a40-85f4-4894-a18b-f6d88b2ce377

    :steps:
        1. Navigate to the Content tab.
        2. Disable repository set
        3. Package from repository cannot be installed
        4. Enable repository set
        5. Install a package on a registered host.
        6. Downgrade package version
        7. Check if the package is in an upgradable state.
        8. Select package and upgrade via rex.
        9. Delete the package

    :expectedresults: The package is updated and deleted
    """
    client = rhel_contenthost
    client.add_rex_key(target_sat)
    module_repos_collection_with_setup.setup_virtual_machine(
        client, target_sat, install_katello_agent=False
    )
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        if not is_open('BZ:2132680'):
            product_name = module_repos_collection_with_setup.custom_product.name
            repos = session.host_new.get_repo_sets(client.hostname, product_name)
            assert 'Enabled' == repos[0].status
            session.host_new.override_repo_sets(
                client.hostname, product_name, "Override to disabled"
            )
            assert 'Disabled' == repos[0].status
            session.host_new.install_package(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
            result = client.run(f'yum install -y {FAKE_7_CUSTOM_PACKAGE}')
            assert result.status != 0
            session.host_new.override_repo_sets(
                client.hostname, product_name, "Override to enabled"
            )
            assert 'Enabled' == repos[0].status
            # refresh repos on system
            client.run('subscription-manager repos')
        # install package
        session.host_new.install_package(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Install package(s) on {client.hostname}'),
            search_rate=4,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        packages = session.host_new.get_packages(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        assert len(packages['table']) == 1
        assert packages['table'][0]['Package'] == FAKE_8_CUSTOM_PACKAGE_NAME
        assert 'Up-to date' in packages['table'][0]['Status']
        result = client.run(f'rpm -q {FAKE_8_CUSTOM_PACKAGE}')
        assert result.status == 0

        # downgrade package version
        client.run(f'yum -y downgrade {FAKE_8_CUSTOM_PACKAGE_NAME}')
        result = client.run(f'rpm -q {FAKE_8_CUSTOM_PACKAGE_NAME}')
        assert result.status == 0

        # this should reload page to update packages table
        session.host_new.get_details(client.hostname, widget_names='overview')

        # filter packages
        packages = session.host_new.get_packages(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        assert len(packages['table']) == 1
        assert packages['table'][0]['Package'] == FAKE_8_CUSTOM_PACKAGE_NAME
        assert 'Upgradable' in packages['table'][0]['Status']

        # update package
        session.host_new.apply_package_action(
            client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME, "Upgrade via remote execution"
        )
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Update package(s) {FAKE_8_CUSTOM_PACKAGE_NAME} on {client.hostname}'),
            search_rate=2,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        packages = session.host_new.get_packages(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        assert 'Up-to date' in packages['table'][0]['Status']

        # remove package
        session.host_new.apply_package_action(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME, "Remove")
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remove package(s) {FAKE_8_CUSTOM_PACKAGE_NAME} on {client.hostname}'),
            search_rate=2,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        packages = session.host_new.get_packages(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        assert 'table' not in packages.keys()
        result = client.run(f'rpm -q {FAKE_8_CUSTOM_PACKAGE}')
        assert result.status != 0


@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
@pytest.mark.no_containers
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel8',
            'YumRepository': {'url': settings.repos.yum_3.url},
        }
    ],
    ids=['yum3'],
    indirect=True,
)
def test_positive_apply_erratum(
    session,
    target_sat,
    rhel_contenthost,
    module_repos_collection_with_setup,
):
    """Apply an erratum on a host using the new Errata tab

    :id: 328e629a-f261-4dc1-ad6f-def27e2fcf07

    :setup:
        1. Valid yum repo with an applicable erratum.

    :steps:
        1. Install a package on a registered host.
        2. Check the Errata card on the Overview tab
        3. Navigate to the Errata tab.
        4. Check for applicable errata.
        5. Select errata and apply via rex.

    :expectedresults: The erratum is applied
    """
    # install package
    client = rhel_contenthost
    client.add_rex_key(target_sat)
    module_repos_collection_with_setup.setup_virtual_machine(
        client, target_sat, install_katello_agent=False
    )
    errata_id = settings.repos.yum_3.errata[25]
    client.run(f'yum install -y {FAKE_7_CUSTOM_PACKAGE}')
    result = client.run(f'rpm -q {FAKE_7_CUSTOM_PACKAGE}')
    assert result.status == 0
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        assert session.host_new.search(client.hostname)[0]['Name'] == client.hostname
        # read widget on overview page
        values = session.host_new.get_details(client.hostname, widget_names='overview')['overview']
        assert values['installable_errata']['security_advisory'] == '1 security advisory'
        assert values['installable_errata']['enhancements'] == '1 enhancement'
        # read errata tab
        values = session.host_new.get_details(client.hostname, widget_names='content.errata')
        assert len(values['content']['errata']['table']) == 2
        # filter just security erratum
        erratas = session.host_new.get_errata_by_type(client.hostname, 'Security')
        assert len(erratas['content']['errata']['table']) == 1
        assert erratas['content']['errata']['table'][0]['Errata'] == errata_id
        # apply errata
        session.host_new.apply_erratas(client.hostname, f"errata_id == {errata_id}")
        task_result = target_sat.wait_for_tasks(
            search_query=(
                f'"Install errata errata_id == {errata_id.lower()} '
                f'and type=security on {client.hostname}"'
            ),
            search_rate=2,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        # verify
        values = session.host_new.get_details(client.hostname, widget_names='content.errata')
        assert 'table' not in values['content']['errata'].keys()
        result = client.run(
            'yum update --assumeno --security | grep "No packages needed for security"'
        )
        assert result.status == 1


@pytest.mark.e2e
@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
@pytest.mark.no_containers
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel8',
            'YumRepository': {'url': settings.repos.module_stream_1.url},
        }
    ],
    ids=['module_stream_1'],
    indirect=True,
)
def test_positive_crud_module_streams(
    session,
    target_sat,
    rhel_contenthost,
    module_repos_collection_with_setup,
):
    """CRUD test for the Module streams new UI tab

    :id: 9800a006-49cc-4c0a-aed8-6a32c4bf0eab

    :setup:
        1. Valid yum repo with Module Streams.

    :steps:
        1. Create Yum Repository which contains module-streams as URL
        2. Enable Module stream
        3. Install Module stream
        4. Delete the Module stream
        5. Reset the Module stream

    :expectedresults: Module streams can be enabled, installed, removed and reset using the new UI.
    """
    module_name = 'duck'
    client = rhel_contenthost
    client.add_rex_key(target_sat)
    module_repos_collection_with_setup.setup_virtual_machine(
        client, target_sat, install_katello_agent=False
    )
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        streams = session.host_new.get_module_streams(client.hostname, module_name)
        assert streams[0]['Name'] == module_name
        assert streams[0]['State'] == 'Default'

        # enable module stream
        session.host_new.apply_module_streams_action(client.hostname, module_name, "Enable")
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Module enable {module_name} on {client.hostname}'),
            search_rate=5,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        streams = session.host_new.get_module_streams(client.hostname, module_name)
        assert streams[0]['State'] == 'Enabled'
        assert streams[0]['Installation status'] == 'Not installed'

        # install
        session.host_new.apply_module_streams_action(client.hostname, module_name, "Install")
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Module install {module_name} on {client.hostname}'),
            search_rate=5,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        streams = session.host_new.get_module_streams(client.hostname, module_name)
        assert streams[0]['Installation status'] == 'Up-to-date'

        # remove
        session.host_new.apply_module_streams_action(client.hostname, module_name, "Remove")
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Module remove {module_name} on {client.hostname}'),
            search_rate=5,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        streams = session.host_new.get_module_streams(client.hostname, module_name)
        assert streams[0]['State'] == 'Enabled'
        assert streams[0]['Installation status'] == 'Not installed'

        session.host_new.apply_module_streams_action(client.hostname, module_name, "Reset")
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Module reset {module_name} on {client.hostname}'),
            search_rate=5,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        # this should reload page to update module streams table
        session.host_new.get_details(client.hostname, widget_names='overview')
        streams = session.host_new.get_module_streams(client.hostname, module_name)
        assert streams[0]['State'] == 'Default'
        assert streams[0]['Installation status'] == 'Not installed'


# ------------------------------ PUPPET ENABLED SAT TESTS ----------------------------
@pytest.fixture(scope='module')
def module_puppet_enabled_proxy_with_loc(
    session_puppet_enabled_sat, module_puppet_loc, session_puppet_enabled_proxy
):
    session_puppet_enabled_proxy.location.append(
        session_puppet_enabled_sat.api.Location(id=module_puppet_loc.id)
    )
    session_puppet_enabled_proxy.update(['location'])


@pytest.mark.tier3
def test_positive_inherit_puppet_env_from_host_group_when_action(
    session_puppet_enabled_sat, module_puppet_org, module_puppet_loc, module_puppet_environment
):
    """Host group puppet environment is inherited to already created
    host when corresponding action is applied to that host

    :id: 3f5af54e-e259-46ad-a2af-7dc1850891f5

    :customerscenario: true

    :expectedresults: Expected puppet environment is inherited to the host

    :BZ: 1414914
    """
    host = session_puppet_enabled_sat.api.Host(
        organization=module_puppet_org, location=module_puppet_loc
    ).create()
    hostgroup = session_puppet_enabled_sat.api.HostGroup(
        environment=module_puppet_environment,
        organization=[module_puppet_org],
        location=[module_puppet_loc],
    ).create()
    with session_puppet_enabled_sat.ui_session() as session:
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name=module_puppet_loc.name)
        session.host.apply_action(
            'Change Environment', [host.name], {'environment': '*Clear environment*'}
        )
        values = session.host.read(host.name, widget_names='host')
        assert values['host']['hostgroup'] == ''
        assert values['host']['puppet_environment'] == ''
        session.host.apply_action('Change Group', [host.name], {'host_group': hostgroup.name})
        values = session.host.read(host.name, widget_names='host')
        assert values['host']['hostgroup'] == hostgroup.name
        assert values['host']['puppet_environment'] == ''
        session.host.apply_action(
            'Change Environment', [host.name], {'environment': '*Inherit from host group*'}
        )
        assert (
            session.host.get_details(host.name)['properties']['properties_table'][
                'Puppet Environment'
            ]
            == module_puppet_environment.name
        )
        values = session.host.read(host.name, widget_names='host')
        assert values['host']['hostgroup'] == hostgroup.name
        assert values['host']['puppet_environment'] == module_puppet_environment.name


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.usefixtures('module_puppet_enabled_proxy_with_loc')
def test_positive_create_with_puppet_class(
    session_puppet_enabled_sat,
    module_puppet_loc,
    module_puppet_org,
    module_env_search,
    module_import_puppet_module,
    module_puppet_enabled_proxy_with_loc,
):
    """Create new Host with puppet class assigned to it

    :id: d883f169-1105-435c-8422-a7160055734a

    :expectedresults: Host is created and contains correct puppet class
    """

    host_template = session_puppet_enabled_sat.api.Host(
        organization=module_puppet_org, location=module_puppet_loc
    )
    host_template.create_missing()
    host_name = f'{host_template.name}.{host_template.domain.name}'
    os_name = f'{host_template.operatingsystem.name} {host_template.operatingsystem.major}'
    values = {
        'host.name': host_template.name,
        'host.organization': host_template.organization.name,
        'host.location': host_template.location.name,
        'host.lce': ENVIRONMENT,
        'host.content_view': DEFAULT_CV,
        'operating_system.architecture': host_template.architecture.name,
        'operating_system.operating_system': os_name,
        'operating_system.media_type': 'All Media',
        'operating_system.media': host_template.medium.name,
        'operating_system.ptable': host_template.ptable.name,
        'operating_system.root_password': host_template.root_pass,
        'interfaces.interface.interface_type': 'Interface',
        'interfaces.interface.device_identifier': gen_string('alpha'),
        'interfaces.interface.mac': host_template.mac,
        'interfaces.interface.domain': host_template.domain.name,
        'interfaces.interface.primary': True,
        'interfaces.interface.interface_additional_data.virtual_nic': False,
        'parameters.global_params': None,
        'parameters.host_params': None,
        'additional_information.comment': 'Host with fake data',
        'host.puppet_environment': module_env_search.name,
        'puppet_enc.classes.assigned': [module_import_puppet_module['puppet_class']],
    }
    with session_puppet_enabled_sat.ui_session() as session:
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name=ANY_CONTEXT['location'])
        session.host.create(values)
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.read(host_name, widget_names='puppet_enc')
        assert len(values['puppet_enc']['classes']['assigned']) == 1
        assert (
            values['puppet_enc']['classes']['assigned'][0]
            == module_import_puppet_module['puppet_class']
        )


@pytest.mark.tier2
def test_positive_inherit_puppet_env_from_host_group_when_create(
    session_puppet_enabled_sat, module_env_search, module_puppet_org, module_puppet_loc
):
    """Host group puppet environment is inherited to host in create
    procedure

    :id: 05831ecc-3132-4eb7-ad90-155470f331b6

    :customerscenario: true

    :expectedresults: Expected puppet environment is inherited to the form

    :BZ: 1414914
    """

    hg_name = gen_string('alpha')
    with session_puppet_enabled_sat.ui_session() as session:
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name=module_puppet_loc.name)
        session.hostgroup.create(
            {'host_group.name': hg_name, 'host_group.puppet_environment': module_env_search.name}
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
        assert values['host']['puppet_environment'] == module_env_search.name
        assert values['host']['inherit_puppet_environment'] is True
        values = session.host.helper.read_create_view(
            {'host.inherit_puppet_environment': False},
            ['host.puppet_environment', 'host.inherit_puppet_environment'],
        )
        assert values['host']['puppet_environment'] == module_env_search.name
        assert values['host']['inherit_puppet_environment'] is False


@pytest.mark.tier3
@pytest.mark.usefixtures('module_puppet_enabled_proxy_with_loc')
def test_positive_set_multi_line_and_with_spaces_parameter_value(
    session_puppet_enabled_sat,
    module_puppet_org,
    module_puppet_loc,
    module_puppet_published_cv,
    module_puppet_lce_library,
):
    """Check that host parameter value with multi-line and spaces is
    correctly represented in yaml format

    :id: d72b481d-2279-4478-ab2d-128f92c76d9c

    :customerscenario: true

    :expectedresults:
        1. parameter is correctly represented in yaml format without
           line break (special chars should be escaped)
        2. host parameter value is the same when restored from yaml format

    :BZ: 1315282
    """
    host_template = session_puppet_enabled_sat.api.Host(
        organization=module_puppet_org, location=module_puppet_loc
    )
    host_template.create_missing()

    param_name = gen_string('alpha').lower()
    # long string that should be escaped and affected by line break with
    # yaml dump by default
    param_value = (
        'auth                          include              '
        'password-auth\r\n'
        'account     include                  password-auth'
    )
    host = session_puppet_enabled_sat.api.Host(
        organization=host_template.organization,
        architecture=host_template.architecture,
        domain=host_template.domain,
        location=host_template.location,
        mac=host_template.mac,
        medium=host_template.medium,
        operatingsystem=host_template.operatingsystem,
        ptable=host_template.ptable,
        root_pass=host_template.root_pass,
        content_facet_attributes={
            'content_view_id': module_puppet_published_cv.id,
            'lifecycle_environment_id': module_puppet_lce_library.id,
        },
    ).create()
    with session_puppet_enabled_sat.ui_session() as session:
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name=module_puppet_loc.name)
        session.host.update(
            host.name, {'parameters.host_params': [dict(name=param_name, value=param_value)]}
        )
        yaml_text = session.host.read_yaml_output(host.name)
        # ensure parameter value is represented in yaml format without
        # line break (special chars should be escaped)
        assert param_value.encode('unicode_escape') in bytes(yaml_text, 'utf-8')
        # host parameter value is the same when restored from yaml format
        yaml_content = yaml.load(yaml_text, yaml.SafeLoader)
        host_parameters = yaml_content.get('parameters')
        assert host_parameters
        assert param_name in host_parameters
        assert host_parameters[param_name] == param_value


@pytest.mark.tier2
@pytest.mark.rhel_ver_match('[^6].*')
def test_positive_tracer_enable_reload(tracer_install_host, target_sat):
    """Using the new Host UI,enable tracer and verify that the page reloads

    :id: c9ebd4a8-6db3-4d0e-92a2-14951c26769b

    :CaseComponent: katello-tracer

    :Team: Phoenix-subscriptions

    :steps:
        1. Register a RHEL host to Satellite.
        2. Prepare katello-tracer to be installed
        3. Navigate to the Traces tab in New Host UI
        4. Enable tracer using the popup

    :expectedresults: The Tracer tab message updates accordingly during the process, and displays
        the state the correct Title
    """
    host = (
        target_sat.api.Host().search(query={'search': tracer_install_host.hostname})[0].read_json()
    )
    with target_sat.ui_session() as session:
        session.organization.select(host['organization_name'])
        tracer = session.host_new.get_tracer(tracer_install_host.hostname)
        assert tracer['title'] == "Traces are not enabled"
        session.host_new.enable_tracer(tracer_install_host.hostname)
        tracer = session.host_new.get_tracer(tracer_install_host.hostname)
        assert tracer['title'] == "Traces are being enabled"
        wait_for(
            lambda: session.host_new.get_tracer(tracer_install_host.hostname)['title']
            != "Traces are being enabled",
            timeout=1800,
            delay=5,
            silent_failure=True,
            handle_exception=True,
        )
        tracer = session.host_new.get_tracer(tracer_install_host.hostname)
        assert tracer['title'] == "No applications to restart"


def test_positive_host_registration_with_non_admin_user(
    test_name,
    module_sca_manifest_org,
    module_location,
    target_sat,
    rhel8_contenthost,
    module_activation_key,
):
    """Register hosts from a non-admin user with only register_hosts, edit_hosts
    and view_organization permissions

    :id: 35458bbc-4556-41b9-ba26-ae0b15179731

    :expectedresults: User with register hosts permission able to register hosts.
    """
    user_password = gen_string('alpha')
    org = module_sca_manifest_org
    role = target_sat.api.Role(organization=[org]).create()

    user_permissions = {
        'Organization': ['view_organizations'],
        'Host': ['view_hosts'],
    }
    target_sat.api_factory.create_role_permissions(role, user_permissions)
    user = target_sat.api.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[org],
        location=[module_location],
        default_organization=org,
        default_location=module_location,
    ).create()
    role = target_sat.cli.Role.info({'name': 'Register hosts'})
    target_sat.cli.User.add_role({'id': user.id, 'role-id': role['id']})

    with Session(test_name, user=user.login, password=user_password) as session:

        cmd = session.host_new.get_register_command(
            {
                'general.insecure': True,
                'general.activation_keys': module_activation_key.name,
            }
        )

        result = rhel8_contenthost.execute(cmd)
        assert result.status == 0, f'Failed to register host: {result.stderr}'

        # Verify server.hostname and server.port from subscription-manager config
        assert target_sat.hostname == rhel8_contenthost.subscription_config['server']['hostname']
        assert constants.CLIENT_PORT == rhel8_contenthost.subscription_config['server']['port']


@pytest.mark.tier2
def test_all_hosts_delete(session, target_sat, function_org, function_location, new_host_ui):
    """Create a host and delete it through All Hosts UI

    :id: 42b4560c-bb57-4c58-928e-e5fd5046b93f

    :expectedresults: Successful deletion of a host through the table dropdown

    :CaseComponent:Hosts-Content

    :Team: Phoenix-subscriptions
    """
    host = target_sat.api.Host(organization=function_org, location=function_location).create()
    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        session.location.select(function_location.name)
        assert session.all_hosts.delete(host.name)


@pytest.mark.tier2
def test_all_hosts_bulk_delete(session, target_sat, function_org, function_location, new_host_ui):
    """Create several hosts, and delete them via Bulk Actions in All Hosts UI

    :id: af1b4a66-dd83-47c3-904b-e8627119cc53

    :expectedresults: Successful deletion of multiple hosts at once through Bulk Action

    :CaseComponent:Hosts-Content

    :Team: Phoenix-subscriptions
    """
    for _ in range(10):
        target_sat.api.Host(organization=function_org, location=function_location).create()
    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        session.location.select(function_location.name)
        assert session.all_hosts.bulk_delete_all()
