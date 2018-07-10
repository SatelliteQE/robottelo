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
from nailgun import entities

from robottelo.constants import DEFAULT_CV, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import tier3


def create_fake_host(session, host, interface_id=gen_string('alpha')):
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

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    host = entities.Host(organization=org).create()
    env = entities.Environment(
        name=gen_string('alpha'), organization=[org]).create()
    hostgroup = entities.HostGroup(
        environment=env, organization=[org]).create()
    with session:
        session.organization.select(org_name=org.name)
        session.host.change_host_environment(
            [host.name],
            {'environment': '*Clear environment*'})
        host_values = session.host.search(host.name)
        assert host_values[0]['Host group'] == ''
        assert host_values[0]['Puppet Environment'] == ''
        session.host.change_host_group(
            [host.name],
            {'host_group': hostgroup.name})
        host_values = session.host.search(host.name)
        assert host_values[0]['Host group'] == hostgroup.name
        assert host_values[0]['Puppet Environment'] == ''
        session.host.change_host_environment(
            [host.name],
            {'environment': '*Inherit from host group*'})
        host_values = session.host.search(host.name)
        assert host_values[0]['Puppet Environment'] == env.name
        values = session.host.read(host.name)
        assert values['host']['hostgroup'] == hostgroup.name
        assert values['host']['puppet_environment'] == env.name
