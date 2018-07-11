# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery Rules

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_integer, gen_string
from nailgun import entities


def test_positive_create(session):
    name = gen_string('alpha')
    search = '{}\t'.format(gen_string('alpha'))
    org = entities.Organization().create()
    host_group_name = gen_string('alpha')
    with session:
        session.organization.select(org_name=org.name)
        session.hostgroup.create({'name': host_group_name})
        session.discoveryrule.create({
            'name': name,
            'search': search,
            'host_group': host_group_name,
            'hostname': gen_string('alpha'),
            'hosts_limit': str(gen_integer(1, 100)),
            'priority': str(gen_integer(1, 100)),
            'enabled': False,
        })
        disc_rule_values = session.discoveryrule.read_all()
        assert disc_rule_values[0]['Name'] == name


def test_positive_delete(session):
    name = gen_string('alpha')
    search = '{}\t'.format(gen_string('alpha'))
    org = entities.Organization().create()
    host_group_name = gen_string('alpha')
    with session:
        session.organization.select(org_name=org.name)
        session.hostgroup.create({'name': host_group_name})
        session.discoveryrule.create({
            'name': name,
            'search': search,
            'host_group': host_group_name,
            'priority': str(gen_integer(1, 100)),
        })
        session.discoveryrule.delete(name)
        assert not session.discoveryrule.read_all()


def test_positive_update(session):
    name = gen_string('alpha')
    search = '{}\t'.format(gen_string('alpha'))
    org = entities.Organization().create()
    host_group_name = gen_string('alpha')
    location = entities.Location().create()
    with session:
        session.organization.select(org_name=org.name)
        session.hostgroup.create({'name': host_group_name})
        session.discoveryrule.create({
            'name': name,
            'search': search,
            'host_group': host_group_name,
            'priority': str(gen_integer(1, 100)),
        })
        session.discoveryrule.update(
            name, {'locations.resources.assigned': [location.name]})
        dr = session.discoveryrule.read(name)
        assert dr['locations']['resources']['assigned'][0] == location.name


def test_positive_disable_and_enable(session):
    name = gen_string('alpha')
    search = '{}\t'.format(gen_string('alpha'))
    org = entities.Organization().create()
    host_group_name = gen_string('alpha')
    with session:
        session.organization.select(org_name=org.name)
        session.hostgroup.create({'name': host_group_name})
        session.discoveryrule.create({
            'name': name,
            'search': search,
            'host_group': host_group_name,
            'priority': str(gen_integer(1, 100)),
        })
        # enable checkbox is true, by default
        session.discoveryrule.disable(name)
        dr = session.discoveryrule.read_all()
        assert dr[0]['Enabled'] == 'false'
        session.discoveryrule.enable(name)
        dr = session.discoveryrule.read_all()
        assert dr[0]['Enabled'] == 'true'
