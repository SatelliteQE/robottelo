"""Test class for Architecture UI

:Requirement: Architecture

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.datafactory import gen_string, valid_data_list
from robottelo.decorators import parametrize


@parametrize('name', **valid_data_list('ui'))
def test_positive_create(session, name):
    with session:
        session.architecture.create({'name': name})
        assert session.architecture.search(name)[0]['Name'] == name


def test_positive_create_with_os(session):
    name = gen_string('alpha')
    os_name = entities.OperatingSystem().create().name
    with session:
        session.architecture.create({
            'name': name,
            'operatingsystems.assigned': [os_name],
        })
        assert session.architecture.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_delete(session, name):
    with session:
        session.architecture.create({'name': name})
        session.architecture.delete(name)
        assert not session.architecture.search(name)
