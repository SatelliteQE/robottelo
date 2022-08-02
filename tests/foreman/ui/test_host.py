"""Test class for Hosts UI

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: pdragun

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import copy
import csv
import os
import random
import re
from datetime import datetime

import pytest
import yaml
from airgun.exceptions import DisabledWidgetError
from airgun.exceptions import NoSuchElementException
from airgun.session import Session
from wait_for import wait_for

from robottelo import constants
from robottelo.api.utils import create_role_permissions
from robottelo.api.utils import cv_publish_promote
from robottelo.api.utils import promote
from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings
from robottelo.constants import ANY_CONTEXT
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FAKE_7_CUSTOM_PACKAGE
from robottelo.constants import FAKE_8_CUSTOM_PACKAGE
from robottelo.constants import FAKE_8_CUSTOM_PACKAGE_NAME
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import OSCAP_PERIOD
from robottelo.constants import OSCAP_WEEKDAY
from robottelo.constants import PERMISSIONS
from robottelo.constants import REPO_TYPE
from robottelo.datafactory import gen_string
from robottelo.ui.utils import create_fake_host


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
    yield ui_user


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


@pytest.fixture(scope='module')
def module_host_template(module_org, smart_proxy_location, module_target_sat):
    host_template = module_target_sat.api.Host(
        organization=module_org, location=smart_proxy_location
    )
    host_template.create_missing()
    host_template.name = None
    return host_template


@pytest.fixture(scope='module')
def module_libvirt_resource(module_org, smart_proxy_location, module_target_sat):
    # Search if Libvirt compute-resource already exists
    # If so, just update its relevant fields otherwise,
    # Create new compute-resource with 'libvirt' provider.
    resource_url = f'qemu+ssh://root@{settings.libvirt.libvirt_hostname}/system'
    comp_res = [
        res
        for res in module_target_sat.api.LibvirtComputeResource().search()
        if res.provider == FOREMAN_PROVIDERS['libvirt'] and res.url == resource_url
    ]
    if len(comp_res) > 0:
        computeresource = module_target_sat.api.LibvirtComputeResource(id=comp_res[0].id).read()
        computeresource.location.append(smart_proxy_location)
        computeresource.organization.append(module_org)
        computeresource = computeresource.update(['location', 'organization'])
    else:
        # Create Libvirt compute-resource
        computeresource = module_target_sat.api.LibvirtComputeResource(
            provider=FOREMAN_PROVIDERS['libvirt'],
            url=resource_url,
            set_console_password=False,
            display_type='VNC',
            location=[smart_proxy_location],
            organization=[module_org],
        ).create()
    return f'{computeresource.name} (Libvirt)'


@pytest.fixture(scope='module')
def module_libvirt_domain(module_org, smart_proxy_location, default_domain):
    default_domain.location.append(smart_proxy_location)
    default_domain.organization.append(module_org)
    default_domain.update(['location', 'organization'])
    return default_domain


@pytest.fixture(scope='module')
def module_libvirt_subnet(
    module_org, smart_proxy_location, module_libvirt_domain, default_smart_proxy, module_target_sat
):
    # Search if subnet is defined with given network.
    # If so, just update its relevant fields otherwise,
    # Create new subnet
    network = settings.vlan_networking.subnet
    subnet = module_target_sat.api.Subnet().search(query={'search': f'network={network}'})
    if len(subnet) > 0:
        subnet = subnet[0].read()
        subnet.domain.append(module_libvirt_domain)
        subnet.location.append(smart_proxy_location)
        subnet.organization.append(module_org)
        subnet.dns = default_smart_proxy
        subnet.dhcp = default_smart_proxy
        subnet.ipam = 'DHCP'
        subnet.tftp = default_smart_proxy
        subnet.discovery = default_smart_proxy
        subnet = subnet.update(
            ['domain', 'discovery', 'dhcp', 'dns', 'ipam', 'location', 'organization', 'tftp']
        )
    else:
        # Create new subnet
        subnet = module_target_sat.api.Subnet(
            network=network,
            mask=settings.vlan_networking.netmask,
            location=[smart_proxy_location],
            organization=[module_org],
            domain=[module_libvirt_domain],
            ipam='DHCP',
            dns=default_smart_proxy,
            dhcp=default_smart_proxy,
            tftp=default_smart_proxy,
            discovery=default_smart_proxy,
        ).create()
    return subnet


@pytest.fixture(scope='module')
def module_libvirt_media(module_org, smart_proxy_location, os_path, default_os, module_target_sat):
    media = module_target_sat.api.Media().search(query={'search': f'path="{os_path}"'})
    if len(media) > 0:
        # Media with this path already exist, make sure it is correct
        media = media[0].read()
        media.organization.append(module_org)
        media.location.append(smart_proxy_location)
        media.operatingsystem.append(default_os)
        media.os_family = 'Redhat'
        media = media.update(['organization', 'location', 'operatingsystem', 'os_family'])
    else:
        # Create new media
        media = module_target_sat.api.Media(
            organization=[module_org],
            location=[smart_proxy_location],
            operatingsystem=[default_os],
            path_=os_path,
            os_family='Redhat',
        ).create()
    return media


@pytest.fixture(scope='module')
def module_libvirt_hostgroup(
    module_org,
    smart_proxy_location,
    default_partition_table,
    default_architecture,
    default_os,
    module_libvirt_media,
    module_libvirt_subnet,
    default_smart_proxy,
    module_libvirt_domain,
    module_lce,
    module_cv_repo,
    module_target_sat,
):
    return module_target_sat.api.HostGroup(
        architecture=default_architecture,
        domain=module_libvirt_domain,
        subnet=module_libvirt_subnet,
        lifecycle_environment=module_lce,
        content_view=module_cv_repo,
        location=[smart_proxy_location],
        operatingsystem=default_os,
        organization=[module_org],
        ptable=default_partition_table,
        medium=module_libvirt_media,
    ).create()


@pytest.fixture(scope='module')
def module_activation_key(module_org_with_manifest, module_target_sat):
    """Create activation key using default CV and library environment."""
    activation_key = module_target_sat.api.ActivationKey(
        auto_attach=True,
        content_view=module_org_with_manifest.default_content_view.id,
        environment=module_org_with_manifest.library.id,
        organization=module_org_with_manifest,
    ).create()

    # Find the 'Red Hat Employee Subscription' and attach it to the activation key.
    for subs in module_target_sat.api.Subscription(organization=module_org_with_manifest).search():
        if subs.name == DEFAULT_SUBSCRIPTION_NAME:
            # 'quantity' must be 1, not subscription['quantity']. Greater
            # values produce this error: 'RuntimeError: Error: Only pools
            # with multi-entitlement product subscriptions can be added to
            # the activation key with a quantity greater than one.'
            activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': subs.id})
            break
    return activation_key


@pytest.fixture(scope='function')
def remove_vm_on_delete(target_sat, setting_update):
    setting_update.value = 'true'
    setting_update.update({'value'})
    assert (
        target_sat.api.Setting().search(query={'search': 'name=destroy_vm_on_host_delete'})[0].value
    )
    yield


@pytest.mark.tier2
def test_positive_end_to_end(
    session, module_host_template, module_org, module_global_params, target_sat
):
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

    new_name = 'new{}'.format(gen_string("alpha").lower())
    new_host_name = f'{new_name}.{module_host_template.domain.name}'
    with session:
        host_name = create_fake_host(
            session,
            module_host_template,
            host_parameters=host_parameters,
            global_parameters=[overridden_global_parameter],
        )
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
        os_name = '{} {}'.format(
            module_host_template.operatingsystem.name, module_host_template.operatingsystem.major
        )
        assert os_name in displayed_host['Operating System']
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


@pytest.mark.tier2
def test_positive_assign_taxonomies(
    session, module_org, smart_proxy_location, target_sat, function_org, function_location_with_org
):
    """Ensure Host organization and Location can be assigned.

    :id: 52466df5-6f56-4faa-b0f8-42b63731f494

    :expectedresults: Host Assign Organization and Location actions are
        working as expected.

    :CaseLevel: Integration
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

    :CaseLevel: Integration
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

    :CaseLevel: System
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
    host_name = f'{host_template.name}.{host_template.domain.name}'
    with session:
        session.organization.update(function_org.name, {'parameters.resources': org_param})
        session.location.update(
            function_location_with_org.name, {'parameters.resources': loc_param}
        )
        session.organization.select(org_name=function_org.name)
        session.location.select(loc_name=function_location_with_org.name)
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

    :CaseLevel: System
    """
    user_password = gen_string('alpha')
    role = target_sat.api.Role(organization=[module_org]).create()
    create_role_permissions(role, {'Organization': ['view_organizations'], 'Host': ['view_hosts']})
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

    :CaseLevel: System
    """
    user_password = gen_string('alpha')
    parameter = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
    role = target_sat.api.Role(organization=[module_org]).create()
    create_role_permissions(
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

    :CaseLevel: System
    """

    user_password = gen_string('alpha')
    parameter = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
    role = target_sat.api.Role(organization=[module_org]).create()
    create_role_permissions(
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

    :CaseLevel: System
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
        promote(content_view.version[0], filter_lc_env.id)
    # Create two host groups
    hg = target_sat.api.HostGroup(organization=[function_org]).create()
    filter_hg = target_sat.api.HostGroup(organization=[function_org]).create()
    # Create lifecycle environment permissions and select one specific
    # environment user will have access to
    create_role_permissions(
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
    create_role_permissions(
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
    create_role_permissions(
        function_role,
        {'Host': ['create_hosts', 'view_hosts']},
        # allow access only to the mentioned here host group
        search=f'hostgroup_fullname = {filter_hg.name}',
    )
    # Add necessary permissions for host groups as we did for lce
    create_role_permissions(
        function_role,
        {'Hostgroup': ['view_hostgroups']},
        # allow access only to the mentioned here host group
        search=f'name = {filter_hg.name}',
    )
    # Add permissions for Organization and Location
    create_role_permissions(
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
def test_positive_search_by_parameter(session, module_org, smart_proxy_location, target_sat):
    """Search for the host by global parameter assigned to it

    :id: 8e61127c-d0a0-4a46-a3c6-22d3b2c5457c

    :expectedresults: Only one specific host is returned by search

    :BZ: 1725686

    :CaseLevel: Integration
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

    :CaseLevel: Integration
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
        for param_value, host in zip(param_values, hosts):
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

    :CaseLevel: Integration
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

    :CaseLevel: Integration
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

    :CaseLevel: Integration
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

    :CaseLevel: Integration
    """
    host = target_sat.api.Host(location=smart_proxy_location).create()
    org = host.organization.read()
    with session:
        session.organization.select(org_name=ANY_CONTEXT['org'])
        assert session.host.search(f'organization = "{org.name}"')[0]['Name'] == host.name


@pytest.mark.tier2
def test_positive_validate_inherited_cv_lce(
    session, module_host_template, target_sat, default_smart_proxy
):
    """Create a host with hostgroup specified via CLI. Make sure host
    inherited hostgroup's lifecycle environment, content view and both
    fields are properly reflected via WebUI.

    :id: c83f6819-2649-4a8b-bb1d-ce93b2243765

    :expectedresults: Host's lifecycle environment and content view match
        the ones specified in hostgroup.

    :CaseLevel: Integration

    :BZ: 1391656
    """
    cv_name = gen_string('alpha')
    lce_name = gen_string('alphanumeric')
    cv = cv_publish_promote(
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
    hostgroup = target_sat.cli_factory.make_hostgroup(
        {
            'content-view-id': cv.id,
            'lifecycle-environment-id': lce.id,
            'organization-ids': module_host_template.organization.id,
        }
    )
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


@pytest.mark.tier2
def test_positive_global_registration_form(
    session, module_activation_key, module_org, smart_proxy_location, default_os, target_sat
):
    """Host registration form produces a correct curl command for various inputs

    :id: f81c2ec4-85b1-4372-8e63-464ddbf70296

    :customerscenario: true

    :expectedresults: The curl command contains all required parameters

    :CaseLevel: Integration
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
                'advanced.activation_keys': module_activation_key.name,
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

    :CaseLevel: Integration
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
                'advanced.activation_keys': module_activation_key.name,
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
    rhel_contenthost.create_custom_repos(yum_3=settings.repos.yum_3['url'])
    rhel_contenthost.execute(f"yum install -y {FAKE_7_CUSTOM_PACKAGE}")
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
    invocation_command = target_sat.cli_factory.make_job_invocation(
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
    task_result = wait_for_tasks(
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

    :CaseLevel: Integration

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
        assert module_ak_with_cv.name in cmd['advanced']['activation_key_helper']
        assert module_lce.name in cmd['advanced']['life_cycle_env_helper']
        assert constants.FAKE_0_CUSTOM_PACKAGE in cmd['advanced']['install_packages_helper']


@pytest.mark.tier2
def test_global_registration_with_capsule_host(
    session,
    capsule_configured,
    rhel7_contenthost,
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

    :CaseLevel: Integration

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. integrate capsule and sync content
        4. open the global registration form and select the same capsule
        5. check host is registered successfully with selected capsule

    :parametrized: yes

    :CaseAutomation: Automated
    """
    client = rhel7_contenthost
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
                'general.orgnization': module_org.name,
                'general.location': module_location.name,
                'general.operating_system': default_os.title,
                'general.capsule': capsule_configured.hostname,
                'advanced.activation_keys': activation_key.name,
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
def test_global_registration_with_gpg_repo_and_default_package(
    session, module_activation_key, default_os, default_smart_proxy, rhel7_contenthost
):
    """Host registration form produces a correct registration command and host is
    registered successfully with gpg repo enabled and have default package
    installed.

    :id: b5738b20-e281-4d0b-ac78-dcdc177b8c9f

    :expectedresults: Host is successfully registered, gpg repo is enabled
        and default package is installed.

    :CaseLevel: Integration

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. update the 'host_packages' parameter in organization with package name e.g. vim
        4. open the global registration form and update the gpg repo and key
        5. check host is registered successfully with installed same package
        6. check gpg repo is exist in registered host

    :parametrized: yes
    """
    client = rhel7_contenthost
    repo_name = 'foreman_register'
    repo_url = settings.repos.gr_yum_repo.url
    repo_gpg_url = settings.repos.gr_yum_repo.gpg_url
    with session:
        cmd = session.host.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.capsule': default_smart_proxy.name,
                'advanced.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.install_packages': 'mlocate vim',
                'advanced.repository': repo_url,
                'advanced.repository_gpg_key_url': repo_gpg_url,
            }
        )

    # rhel repo required for insights client installation,
    # syncing it to the satellite would take too long
    client.create_custom_repos(rhel7=settings.repos.rhel7_os)
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

    :CaseLevel: Integration

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
                'advanced.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.install_packages': 'subscription-manager',
                'advanced.repository': repo_url,
            }
        )

    # run curl
    result = client.execute(cmd)
    assert result.status == 0
    result = client.execute('yum info subscription-manager | grep "From repo"')
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

    :CaseLevel: Integration

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
                'advanced.activation_keys': module_activation_key.name,
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
    session, module_activation_key, rhel7_contenthost, default_os, default_smart_proxy, target_sat
):
    """Global registration token should be only used for registration call, it
    should be restricted for any other api calls.

    :id: 4528b5c6-0a6d-40cd-857a-68b76db2179b

    :expectedresults: global registration token should be restricted for any api calls
        other than the registration

    :CaseLevel: Integration

    :steps:
        1. open the global registration form and generate the curl token
        2. use that curl token to execute other api calls e.g. GET /hosts, /users

    :parametrized: yes
    """
    client = rhel7_contenthost
    with session:
        cmd = session.host.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.capsule': default_smart_proxy.name,
                'advanced.activation_keys': module_activation_key.name,
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
        'Unable to authenticate user' in result.stdout


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_bulk_delete_host(session, smart_proxy_location, target_sat, function_org):
    """Delete multiple hosts from the list

    :id: 8da2084a-8b50-46dc-b305-18eeb80d01e0

    :expectedresults: All selected hosts should be deleted successfully

    :BZ: 1368026

    :CaseLevel: System
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


@pytest.mark.on_premises_provisioning
@pytest.mark.tier4
def test_positive_provision_end_to_end(
    session,
    module_org,
    smart_proxy_location,
    module_libvirt_domain,
    module_libvirt_hostgroup,
    module_libvirt_resource,
    target_sat,
):
    """Provision Host on libvirt compute resource

    :id: 2678f95f-0c0e-4b46-a3c1-3f9a954d3bde

    :expectedresults: Host is provisioned successfully

    :CaseLevel: System
    """
    hostname = gen_string('alpha').lower()
    root_pwd = gen_string('alpha', 15)
    with session:
        session.host.create(
            {
                'host.name': hostname,
                'host.organization': module_org.name,
                'host.location': smart_proxy_location.name,
                'host.hostgroup': module_libvirt_hostgroup.name,
                'host.inherit_deploy_option': False,
                'host.deploy': module_libvirt_resource,
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
        target_sat.api.Host(
            id=target_sat.api.Host().search(query={'search': f'name={name}'})[0].id
        ).delete()
        assert (
            session.host.get_details(name)['properties']['properties_table']['Build'] == 'Installed'
        )


@pytest.mark.on_premises_provisioning
@pytest.mark.run_in_one_thread
@pytest.mark.tier4
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete'], indirect=True)
def test_positive_delete_libvirt(
    session,
    module_org,
    smart_proxy_location,
    module_libvirt_domain,
    module_libvirt_hostgroup,
    module_libvirt_resource,
    setting_update,
    remove_vm_on_delete,
    target_sat,
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
    with session:
        session.host.create(
            {
                'host.name': hostname,
                'host.organization': module_org.name,
                'host.location': smart_proxy_location.name,
                'host.hostgroup': module_libvirt_hostgroup.name,
                'host.inherit_deploy_option': False,
                'host.deploy': module_libvirt_resource,
                'provider_content.virtual_machine.memory': '1 GB',
                'operating_system.root_password': root_pwd,
                'interfaces.interface.network_type': 'Physical (Bridge)',
                'interfaces.interface.network': settings.vlan_networking.bridge,
                'additional_information.comment': 'Delete host that provisioned on Libvirt',
            }
        )
        name = f'{hostname}.{module_libvirt_domain.name}'
        assert session.host.search(name)[0]['Name'] == name
        session.host.delete(name)
        assert not target_sat.api.Host().search(query={'search': f'name="{hostname}"'})


@pytest.fixture
def gce_template(googleclient):
    max_rhel7_template = max(
        img.name for img in googleclient.list_templates(True) if str(img.name).startswith('rhel-7')
    )
    return googleclient.get_template(max_rhel7_template, project='rhel-cloud').uuid


@pytest.fixture
def gce_cloudinit_template(googleclient, gce_cert):
    return googleclient.get_template('customcinit', project=gce_cert['project_id']).uuid


@pytest.fixture
def gce_domain(module_org, smart_proxy_location, gce_cert, target_sat):
    domain_name = f'{settings.gce.zone}.c.{gce_cert["project_id"]}.internal'
    domain = target_sat.api.Domain().search(query={'search': f'name={domain_name}'})
    if domain:
        domain = domain[0]
        domain.organization = [module_org]
        domain.location = [smart_proxy_location]
        domain.update(['organization', 'location'])
    if not domain:
        domain = target_sat.api.Domain(
            name=domain_name, location=[smart_proxy_location], organization=[module_org]
        ).create()
    return domain


@pytest.fixture
def gce_resource_with_image(
    gce_template,
    gce_cloudinit_template,
    gce_cert,
    default_architecture,
    default_os,
    smart_proxy_location,
    module_org,
    target_sat,
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
                'locations.resources.assigned': [smart_proxy_location.name],
            }
        )
    gce_cr = target_sat.api.AbstractComputeResource().search(query={'search': f'name={cr_name}'})[0]
    # Finish Image
    target_sat.api.Image(
        architecture=default_architecture,
        compute_resource=gce_cr,
        name='autogce_img',
        operatingsystem=default_os,
        username=vm_user,
        uuid=gce_template,
    ).create()
    # Cloud-Init Image
    target_sat.api.Image(
        architecture=default_architecture,
        compute_resource=gce_cr,
        name='autogce_img_cinit',
        operatingsystem=default_os,
        username=vm_user,
        uuid=gce_cloudinit_template,
        user_data=True,
    ).create()
    return gce_cr


@pytest.fixture
def gce_hostgroup(
    module_org,
    smart_proxy_location,
    default_partition_table,
    default_architecture,
    default_os,
    gce_domain,
    gce_resource_with_image,
    module_lce,
    module_cv_repo,
    target_sat,
):
    return target_sat.api.HostGroup(
        architecture=default_architecture,
        compute_resource=gce_resource_with_image,
        domain=gce_domain,
        lifecycle_environment=module_lce,
        content_view=module_cv_repo,
        location=[smart_proxy_location],
        operatingsystem=default_os,
        organization=[module_org],
        ptable=default_partition_table,
    ).create()


@pytest.mark.tier4
@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('gce')
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete'], indirect=True)
def test_positive_gce_provision_end_to_end(
    session,
    target_sat,
    module_org,
    smart_proxy_location,
    default_os,
    gce_domain,
    gce_hostgroup,
    googleclient,
    setting_update,
    remove_vm_on_delete,
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
        session.location.select(loc_name=smart_proxy_location.name)
        # Provision GCE Host
        try:
            with target_sat.skip_yum_update_during_provisioning(
                template='Kickstart default finish'
            ):
                session.host.create(
                    {
                        'host.name': name,
                        'host.hostgroup': gce_hostgroup.name,
                        'provider_content.virtual_machine.machine_type': 'g1-small',
                        'provider_content.virtual_machine.external_ip': True,
                        'provider_content.virtual_machine.network': 'default',
                        'provider_content.virtual_machine.storage': storage,
                        'operating_system.operating_system': default_os.title,
                        'operating_system.image': 'autogce_img',
                        'operating_system.root_password': root_pwd,
                    }
                )
                wait_for(
                    lambda: target_sat.api.Host()
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
                session.host.delete(hostname)
                assert not target_sat.api.Host().search(query={'search': f'name="{hostname}"'})
                # 2.2 GCE Backend Assertions
                assert gceapi_vm.is_stopping or gceapi_vm.is_stopped
        except Exception as error:
            gcehost = target_sat.api.Host().search(query={'search': f'name={hostname}'})
            if gcehost:
                gcehost[0].delete()
            raise error
        finally:
            googleclient.disconnect()


@pytest.mark.tier4
@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('gce')
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete'], indirect=True)
def test_positive_gce_cloudinit_provision_end_to_end(
    session,
    target_sat,
    module_org,
    smart_proxy_location,
    default_os,
    gce_domain,
    gce_hostgroup,
    googleclient,
    setting_update,
    remove_vm_on_delete,
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
        session.location.select(loc_name=smart_proxy_location.name)
        # Provision GCE Host
        try:
            with target_sat.skip_yum_update_during_provisioning(
                template='Kickstart default user data'
            ):
                session.host.create(
                    {
                        'host.name': name,
                        'host.hostgroup': gce_hostgroup.name,
                        'provider_content.virtual_machine.machine_type': 'g1-small',
                        'provider_content.virtual_machine.external_ip': True,
                        'provider_content.virtual_machine.network': 'default',
                        'provider_content.virtual_machine.storage': storage,
                        'operating_system.operating_system': default_os.title,
                        'operating_system.image': 'autogce_img_cinit',
                        'operating_system.root_password': root_pwd,
                    }
                )
                # 1. Host Creation Assertions
                # 1.1 UI based Assertions
                host_info = session.host.get_details(hostname)
                assert session.host.search(hostname)[0]['Name'] == hostname
                assert (
                    host_info['properties']['properties_table']['Build']
                    == 'Pending installation clear'
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
                session.host.delete(hostname)
                assert not target_sat.api.Host().search(query={'search': f'name="{hostname}"'})
                # 2.2 GCE Backend Assertions
                assert gceapi_vm.is_stopping or gceapi_vm.is_stopped
        except Exception as error:
            gcehost = target_sat.api.Host().search(query={'search': f'name={hostname}'})
            if gcehost:
                gcehost[0].delete()
            raise error
        finally:
            googleclient.disconnect()


# ------------------------------ NEW HOST UI DETAILS ----------------------------
@pytest.fixture(scope='function')
def enable_new_host_details_ui(target_sat, setting_update):
    setting_update.value = 'true'
    setting_update.update({'value'})
    assert target_sat.api.Setting().search(query={'search': 'name=host_details_ui'})[0].value
    yield


@pytest.mark.tier4
@pytest.mark.parametrize('setting_update', ['host_details_ui'], indirect=True)
def test_positive_read_details_page_from_new_ui(
    session, module_host_template, enable_new_host_details_ui, setting_update
):
    """Create new Host and read all its content through details page

    :id: ef0c5942-9049-11ec-8029-98fa9b6ecd5a

    :expectedresults: Host is created and has expected content

    :CaseLevel: System
    """
    interface_id = gen_string('alpha')
    with session:
        host_name = create_fake_host(
            session, module_host_template, interface_id, new_host_details=True
        )
        assert session.host_new.search(host_name)[0]['Name'] == host_name
        values = session.host_new.get_details(host_name, widget_names='Overview')
        assert values['Overview']['HostStatusCard']['status'] == 'All statuses OK'
        assert (
            values['Overview']['DetailsCard']['details']['mac_address'] == module_host_template.mac
        )
        assert values['Overview']['DetailsCard']['details']['host_owner'] == values['current_user']
        assert values['Overview']['DetailsCard']['details']['comment'] == 'Host with fake data'


@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize('setting_update', ['host_details_ui'], indirect=True)
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': 'rhel8',
            'SatelliteToolsRepository': {},
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
    enable_new_host_details_ui,
    setting_update,
    module_repos_collection_with_manifest,
):
    """Update a package on a host using the new Content tab

    :id: ffc19a40-85f4-4894-a18b-f6d88b2ce377

    :steps:
        1. Navigate to the Content tab.
        2. Install a package on a registered host.
        3. Downgrade package version
        4. Check if the package is in an upgradable state.
        5. Select package and upgrade via rex.
        6. Delete the package

    :expectedresults: The package is updated and deleted

    """
    client = rhel_contenthost
    client.add_rex_key(target_sat)
    module_repos_collection_with_manifest.setup_virtual_machine(client, target_sat)
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        # install package
        session.host_new.install_package(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        task_result = wait_for_tasks(
            search_query=(f'Install package(s) {FAKE_8_CUSTOM_PACKAGE_NAME}'),
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

        # filter packages
        packages = session.host_new.get_packages(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        assert len(packages['table']) == 1
        assert packages['table'][0]['Package'] == FAKE_8_CUSTOM_PACKAGE_NAME
        assert 'Upgradable' in packages['table'][0]['Status']

        # update package
        session.host_new.apply_package_action(
            client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME, "Upgrade via remote execution"
        )
        task_result = wait_for_tasks(
            search_query=(f'Update package(s) {FAKE_8_CUSTOM_PACKAGE_NAME}'),
            search_rate=2,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        packages = session.host_new.get_packages(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        assert 'Up-to date' in packages['table'][0]['Status']

        # remove package
        session.host_new.apply_package_action(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME, "Remove")
        task_result = wait_for_tasks(
            search_query=(f'Remove package(s) {FAKE_8_CUSTOM_PACKAGE_NAME}'),
            search_rate=2,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        packages = session.host_new.get_packages(client.hostname, FAKE_8_CUSTOM_PACKAGE_NAME)
        assert len(packages['table']) == 0
        result = client.run(f'rpm -q {FAKE_8_CUSTOM_PACKAGE}')
        assert result.status != 0


@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize('setting_update', ['host_details_ui'], indirect=True)
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': 'rhel8',
            'SatelliteToolsRepository': {},
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
    enable_new_host_details_ui,
    setting_update,
    module_repos_collection_with_manifest,
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
    module_repos_collection_with_manifest.setup_virtual_machine(client, target_sat)
    client.run(f'yum install -y {FAKE_7_CUSTOM_PACKAGE}')
    result = client.run(f'rpm -q {FAKE_7_CUSTOM_PACKAGE}')
    assert result.status == 0
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        assert session.host_new.search(client.hostname)[0]['Name'] == client.hostname
        # read widget on overview page
        values = session.host_new.get_details(client.hostname, widget_names='Overview')['Overview']
        assert values['InstallableErrataCard']['security_advisory'] == '1 security advisory'
        assert values['InstallableErrataCard']['enhancements'] == '1 enhancement'
        # read errata tab
        values = session.host_new.get_details(client.hostname, widget_names='Content.Errata')
        assert len(values['Content']['Errata']['table']) == 2
        # filter just security erratum
        erratas = session.host_new.get_errata_by_type(client.hostname, 'Security')
        assert len(erratas['Content']['Errata']['table']) == 1
        assert erratas['Content']['Errata']['table'][0]['Errata'] == settings.repos.yum_3.errata[25]
        # apply errata
        session.host_new.apply_erratas(
            client.hostname, f"errata_id == {settings.repos.yum_3.errata[25]}"
        )
        task_result = wait_for_tasks(
            search_query=(
                f'Install errata errata_id == {settings.repos.yum_3.errata[25].lower()}"'
            ),
            search_rate=2,
            max_tries=60,
        )
        assert task_result[0].result == 'success'
        # verify
        values = session.host_new.get_details(client.hostname, widget_names='Content.Errata')
        assert 'table' not in values['Content']['Errata'].keys()
        result = client.run(
            'yum update --assumeno --security | grep "No packages needed for security"'
        )
        assert result.status == 1


@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize('setting_update', ['host_details_ui'], indirect=True)
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': 'rhel8',
            'SatelliteToolsRepository': {},
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
    setting_update,
    enable_new_host_details_ui,
    module_repos_collection_with_manifest,
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
    module_repos_collection_with_manifest.setup_virtual_machine(client, target_sat)
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        streams = session.host_new.get_module_streams(client.hostname, module_name)
        assert streams[0]['Name'] == module_name
        assert streams[0]['State'] == 'Default'

        # enable module stream
        session.host_new.apply_module_streams_action(client.hostname, module_name, "Enable")
        task_result = wait_for_tasks(
            search_query=(f'Module enable {module_name}'),
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
        task_result = wait_for_tasks(
            search_query=(f'Module install {module_name}'),
            search_rate=5,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        streams = session.host_new.get_module_streams(client.hostname, module_name)
        assert streams[0]['Installation status'] == 'Up-to-date'

        # remove
        session.host_new.apply_module_streams_action(client.hostname, module_name, "Remove")
        task_result = wait_for_tasks(
            search_query=(f'Module remove {module_name}'),
            search_rate=5,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        streams = session.host_new.get_module_streams(client.hostname, module_name)
        assert streams[0]['State'] == 'Enabled'
        assert streams[0]['Installation status'] == 'Not installed'

        session.host_new.apply_module_streams_action(client.hostname, module_name, "Reset")
        task_result = wait_for_tasks(
            search_query=(f'Module reset {module_name}'),
            search_rate=5,
            max_tries=60,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
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

    :CaseLevel: System
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

    :CaseLevel: System
    """

    host_template = session_puppet_enabled_sat.api.Host(
        organization=module_puppet_org, location=module_puppet_loc
    )
    host_template.create_missing()

    with session_puppet_enabled_sat.ui_session() as session:
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name='Any Location')
        host_name = create_fake_host(
            session,
            host_template,
            extra_values={
                'host.puppet_environment': module_env_search.name,
                'puppet_enc.classes.assigned': [module_import_puppet_module['puppet_class']],
            },
        )
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

    :CaseLevel: Integration
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

    :CaseLevel: System
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


class TestHostAnsible:
    """Tests for Ansible portion of Hosts"""

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_host_role_information(self):
        """Assign Ansible Role to a Host and an attached Host group and verify that the information
        in the new UI is displayed correctly

        :id: 7da913ef-3b43-4bfa-9a45-d895431c8b56

        :caseComponent: Ansible

        :assignee: sbible

        :CaseLevel: System

        :Steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Create a host group and assign one of the Ansible roles to the host group.
            4. Assign the host to the host group.
            5. Assign one role to the RHEL host.
            6. Navigate to the new UI for the given Host.
            7. Select the 'Ansible' tab, then the 'Inventory' sub-tab.

        :expectedresults: Roles assigned directly to the Host are visible on the subtab, and
            roles assigned to the Host Group are visible by clicking the "view all assigned
            roles" link

        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_role_variable_information(self):
        """Create and assign variables to an Ansible Role and verify that the information in
        the new UI is displayed correctly

        :id: 4ab2813a-6b83-4907-b104-0473465814f5

        :caseComponent: Ansible

        :assignee: sbible

        :CaseLevel: System

        :Steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Create a host group and assign one of the Ansible roles to the host group.
            4. Assign the host to the host group.
            5. Assign one roles to the RHEL host.
            6. Create a variable and associate it with the role assigned to the Host.
            7. Create a variable and associate it with the role assigned to the Hostgroup.
            8. Navigate to the new UI for the given Host.
            9. Select the 'Ansible' tab, then the 'Variables' sub-tab.

        :expectedresults: The variables information for the given Host is visible.

        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_assign_role_in_new_ui(self):
        """Using the new Host UI, assign a role to a Host

        :id: 044f38b4-cff2-4ddc-b93c-7e9f2826d00d

        :caseComponent: Ansible

        :assignee: sbible

        :CaseLevel: System

        :Steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Navigate to the new UI for the given Host.
            4. Select the 'Ansible' tab
            5. Click the 'Assign Ansible Roles' button.
            6. Using the popup, assign a role to the Host.

        :expectedresults: The Role is successfully assigned to the Host, and shows up on the UI

        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_remove_role_in_new_ui(self):
        """Using the new Host UI, remove the role(s) of a Host

        :id: d6de5130-45f6-4349-b490-fbde2aed082c

        :caseComponent: Ansible

        :assignee: sbible

        :CaseLevel: System

        :Steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Assign a role to the host.
            4. Navigate to the new UI for the given Host.
            5. Select the 'Ansible' tab
            6. Click the 'Edit Ansible roles' button.
            7. Using the popup, remove the assigned role from the Host.

        :expectedresults: The Role is successfully removed from the Host, and no longer shows
            up on the UI

        """
