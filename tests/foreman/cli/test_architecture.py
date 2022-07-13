"""Test class for Architecture CLI

:Requirement: Architecture

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: pdragun

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_choice

from robottelo.cli.architecture import Architecture
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_architecture
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list


class TestArchitecture:
    """Architecture CLI related tests."""

    @pytest.fixture(scope='class')
    def class_architecture(self):
        """Shared architecture for tests"""
        return make_architecture()

    @pytest.mark.tier1
    def test_positive_CRUD(self):
        """Create a new Architecture, update the name and delete the Architecture itself.

        :id: cd8654b8-e603-11ea-adc1-0242ac120002

        :expectedresults: Architecture is created, modified and deleted successfully

        :CaseImportance: Critical
        """

        name = gen_choice(list(valid_data_list().values()))
        new_name = gen_choice(list(valid_data_list().values()))

        architecture = make_architecture({'name': name})
        assert architecture['name'] == name
        Architecture.update({'id': architecture['id'], 'new-name': new_name})
        architecture = Architecture.info({'id': architecture['id']})
        assert architecture['name'] == new_name
        Architecture.delete({'id': architecture['id']})
        with pytest.raises(CLIReturnCodeError):
            Architecture.info({'id': architecture['id']})

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_name(self, name):
        """Don't create an Architecture with invalid data.

        :id: cfed972e-9b09-4852-bdd2-b5a8a8aed170

        :parametrized: yes

        :expectedresults: Architecture is not created.

        :CaseImportance: Medium
        """

        with pytest.raises(CLIReturnCodeError) as error:
            Architecture.create({'name': name})

        assert 'Could not create the architecture:' in error.value.message

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, class_architecture, new_name):
        """Create Architecture then fail to update its name

        :id: 037c4892-5e62-46dd-a2ed-92243e870e40

        :parametrized: yes

        :expectedresults: Architecture name is not updated

        :CaseImportance: Medium
        """

        with pytest.raises(CLIReturnCodeError) as error:
            Architecture.update({'id': class_architecture['id'], 'new-name': new_name})

        assert 'Could not update the architecture:' in error.value.message

        result = Architecture.info({'id': class_architecture['id']})
        assert class_architecture['name'] == result['name']

    @pytest.mark.tier1
    @pytest.mark.parametrize('entity_id', **parametrized(invalid_id_list()))
    def test_negative_delete_by_id(self, entity_id):
        """Delete architecture by invalid ID

        :id: 78bae664-6493-4c74-a587-94170f20746e

        :parametrized: yes

        :expectedresults: Architecture is not deleted

        :CaseImportance: Medium
        """
        with pytest.raises(CLIReturnCodeError) as error:
            Architecture.delete({'id': entity_id})

        assert 'Could not delete the architecture' in error.value.message
