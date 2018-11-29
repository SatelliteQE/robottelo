# -*- encoding: utf-8 -*-
"""Test class for Host Group UI

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: UI

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities

from robottelo.constants import (DEFAULT_CV, ENVIRONMENT)
from robottelo.decorators import fixture, tier2


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@tier2
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for host group component

    :id: 537d95f2-fe32-4e06-a2cb-21c80fe8e2e2

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    architecture = entities.Architecture().create()
    os = entities.OperatingSystem(architecture=[architecture]).create()
    os_name = u'{0} {1}'.format(os.name, os.major)
    domain = entities.Domain(
        organization=[module_org], location=[module_loc]).create()
    with session:
        # Create host group with some data
        session.hostgroup.create({
            'host_group.name': name,
            'host_group.description': description,
            'host_group.lce': ENVIRONMENT,
            'host_group.content_view': DEFAULT_CV,
            'network.domain': domain.name,
            'operating_system.architecture': architecture.name,
            'operating_system.operating_system': os_name,
        })
        hostgroup_values = session.hostgroup.read(name)
        assert hostgroup_values['host_group']['name'] == name
        assert hostgroup_values['host_group']['description'] == description
        assert hostgroup_values['host_group']['lce'] == ENVIRONMENT
        assert hostgroup_values['host_group']['content_view'] == DEFAULT_CV
        assert hostgroup_values['operating_system']['architecture'] == architecture.name
        assert hostgroup_values['operating_system']['operating_system'] == os_name
        # Update host group with new name
        session.hostgroup.update(name, {'host_group.name': new_name})
        assert session.hostgroup.search(new_name)[0]['Name'] == new_name
        # Delete host group
        session.hostgroup.delete(new_name)
        assert not session.hostgroup.search(new_name)
