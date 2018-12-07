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

from nailgun import entities
import pytest

from robottelo import ssh
from robottelo.cli.factory import make_scap_policy, make_scapcontent
from robottelo.cli.scap_policy import Scappolicy
from robottelo.cli.scapcontent import Scapcontent
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_CV,
    DEFAULT_LOC,
    ENVIRONMENT,
    OSCAP_PROFILE,
    OSCAP_PERIOD,
    OSCAP_WEEKDAY,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import tier2, tier3, skip_if, skip_if_not_set


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


def create_fake_host(session, host, interface_id=gen_string('alpha'),
                     global_parameters=None, host_parameters=None):
    os_name = u'{0} {1}'.format(
        host.operatingsystem.name, host.operatingsystem.major)
    session.host.create({
        'host.name': host.name,
        'host.organization': host.organization.name,
        'host.location': host.location.name,
        'host.lce': ENVIRONMENT,
        'host.content_view': DEFAULT_CV,
        'host.puppet_environment': host.environment.name,
        'operating_system.architecture': host.architecture.name,
        'operating_system.operating_system': os_name,
        'operating_system.media_type': 'All Media',
        'operating_system.media': host.medium.name,
        'operating_system.ptable': host.ptable.name,
        'operating_system.root_password': host.root_pass,
        'interfaces.interface.interface_type': 'Interface',
        'interfaces.interface.device_identifier': interface_id,
        'interfaces.interface.mac': host.mac,
        'interfaces.interface.domain': host.domain.name,
        'interfaces.interface.primary': True,
        'interfaces.interface.interface_additional_data.virtual_nic': False,
        'parameters.global_params': global_parameters,
        'parameters.host_params': host_parameters,
    })


@tier3
def test_positive_create(session):
    """Create a new Host

    :id: 4821444d-3c86-4f93-849b-60460e025ba0

    :expectedresults: Host is created

    :CaseLevel: System
    """
    host = entities.Host()
    host.create_missing()
    host_name = u'{0}.{1}'.format(host.name, host.domain.name)
    with session:
        session.organization.select(org_name=host.organization.name)
        session.location.select(loc_name=host.location.name)
        create_fake_host(session, host)
        assert session.host.search(host_name)[0]['Name'] == host_name


@tier3
def test_positive_read_from_details_page(session):
    """Create new Host and read all its content through details page

    :id: ffba5d40-918c-440e-afbb-6b910db3a8fb

    :expectedresults: Host is created and has expected content

    :CaseLevel: System
    """
    host = entities.Host()
    host.create_missing()
    os_name = u'{0} {1}'.format(
        host.operatingsystem.name, host.operatingsystem.major)
    interface_id = gen_string('alpha')
    host_name = u'{0}.{1}'.format(host.name, host.domain.name)
    with session:
        session.organization.select(org_name=host.organization.name)
        session.location.select(loc_name=host.location.name)
        create_fake_host(session, host, interface_id)
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.get_details(host_name)
        assert values['properties']['properties_table'][
            'Status'] == 'OK'
        assert values['properties']['properties_table'][
            'Build'] == 'Pending installation'
        assert values['properties']['properties_table'][
            'Domain'] == host.domain.name
        assert values['properties']['properties_table'][
            'MAC Address'] == host.mac
        assert values['properties']['properties_table'][
            'Puppet Environment'] == host.environment.name
        assert values['properties']['properties_table'][
            'Architecture'] == host.architecture.name
        assert values['properties']['properties_table'][
            'Operating System'] == os_name
        assert values['properties']['properties_table'][
            'Location'] == host.location.name
        assert values['properties']['properties_table'][
            'Organization'] == host.organization.name
        assert values['properties']['properties_table'][
            'Owner'] == values['current_user']


@tier3
def test_positive_read_from_edit_page(session):
    """Create new Host and read all its content through edit page

    :id: 758fcab3-b363-4bfc-8f5d-173098a7e72d

    :expectedresults: Host is created and has expected content

    :CaseLevel: System
    """
    host = entities.Host()
    host.create_missing()
    os_name = u'{0} {1}'.format(
        host.operatingsystem.name, host.operatingsystem.major)
    interface_id = gen_string('alpha')
    host_name = u'{0}.{1}'.format(host.name, host.domain.name)
    with session:
        session.organization.select(org_name=host.organization.name)
        session.location.select(loc_name=host.location.name)
        create_fake_host(session, host, interface_id)
        assert session.host.search(host_name)[0]['Name'] == host_name
        values = session.host.read(host_name)
        assert values['host']['name'] == host.name
        assert values['host']['organization'] == host.organization.name
        assert values['host']['location'] == host.location.name
        assert values['host']['lce'] == ENVIRONMENT
        assert values['host']['content_view'] == DEFAULT_CV
        assert values['host']['puppet_environment'] == host.environment.name
        assert values[
            'operating_system']['architecture'] == host.architecture.name
        assert values['operating_system']['operating_system'] == os_name
        assert values['operating_system']['media_type'] == 'All Media'
        assert values['operating_system']['media'] == host.medium.name
        assert values['operating_system']['ptable'] == host.ptable.name
        assert values['interfaces']['interfaces_list'][0][
            'Identifier'] == interface_id
        assert values['interfaces']['interfaces_list'][0][
            'Type'] == 'Interface physical'
        assert values['interfaces']['interfaces_list'][0][
            'MAC Address'] == host.mac
        assert values['interfaces']['interfaces_list'][0][
            'FQDN'] == host_name
        assert values['additional_information'][
            'owned_by'] == values['current_user']
        assert values['additional_information']['enabled'] is True


@tier3
def test_positive_delete(session):
    """Delete a Host

    :id: 13735af1-f1c7-466e-a969-80618a1d854d

    :expectedresults: Host is delete

    :CaseLevel: System
    """
    host = entities.Host()
    host.create_missing()
    host_name = u'{0}.{1}'.format(host.name, host.domain.name)
    with session:
        session.organization.select(org_name=host.organization.name)
        session.location.select(loc_name=host.location.name)
        create_fake_host(session, host)
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

    :CaseLevel: System
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
def test_positive_assign_taxonomies(session, module_org):
    """Ensure Host organization and Location can be assigned.

    :id: 52466df5-6f56-4faa-b0f8-42b63731f494

    :expectedresults: Host Assign Organization and Location actions are
        working as expected.

    :CaseLevel: Integration
    """
    default_loc = entities.Location().search(
        query={'search': 'name="{0}"'.format(DEFAULT_LOC)}
    )[0]
    host = entities.Host(
        organization=module_org, location=default_loc).create()
    new_host_org = entities.Organization().create()
    new_host_location = entities.Location(organization=[new_host_org]).create()
    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=default_loc.name)
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
