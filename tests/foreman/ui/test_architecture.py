"""Test class for Architecture UI

:Requirement: Architecture

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: pdragun

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session):
    """Perform end to end testing for architecture component

    :id: eef14b29-9f5a-41aa-805e-73398ed2b112

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    os = entities.OperatingSystem().create()
    os_name = f'{os.name} {os.major}'
    with session:
        # Create new architecture with assigned operating system
        session.architecture.create({'name': name, 'operatingsystems.assigned': [os_name]})
        assert session.architecture.search(name)[0]['Name'] == name
        architecture_values = session.architecture.read(name)
        assert architecture_values['name'] == name
        assert len(architecture_values['operatingsystems']['assigned']) == 1
        assert architecture_values['operatingsystems']['assigned'][0] == os_name
        # Check that architecture is really assigned to operating system
        os_values = session.operatingsystem.read(os_name)
        assert len(os_values['operating_system']['architectures']['assigned']) == 1
        assert os_values['operating_system']['architectures']['assigned'][0] == name
        # Update architecture with new name
        session.architecture.update(name, {'name': new_name})
        assert session.architecture.search(new_name)[0]['Name'] == new_name
        assert not session.architecture.search(name)
        # Delete architecture
        session.architecture.delete(new_name)
        assert not session.architecture.search(new_name)
