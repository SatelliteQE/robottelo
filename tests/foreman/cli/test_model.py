"""Test for Model CLI

:Requirement: Model

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: pdragun

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_model
from robottelo.cli.model import Model
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list


class TestModel:
    """Test class for Model CLI"""

    @pytest.fixture()
    def class_model(self):
        """Shared model for tests"""
        return make_model()

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'name, new_name',
        **parametrized(list(zip(valid_data_list().values(), valid_data_list().values())))
    )
    def test_positive_crud_with_name(self, name, new_name):
        """Successfully creates, updates and deletes a Model.

        :id: 9ca9d5ff-750a-4d60-91b2-4c4375f0e35f

        :parametrized: yes

        :expectedresults: Model is created, updated and deleted.

        :CaseImportance: High
        """
        model = make_model({'name': name})
        assert model['name'] == name
        Model.update({'id': model['id'], 'new-name': new_name})
        model = Model.info({'id': model['id']})
        assert model['name'] == new_name
        Model.delete({'id': model['id']})
        with pytest.raises(CLIReturnCodeError):
            Model.info({'id': model['id']})

    @pytest.mark.tier1
    def test_positive_create_with_vendor_class(self):
        """Check if Model can be created with specific vendor class

        :id: c36d3490-cd12-4f5f-a453-2ae5d0404496

        :expectedresults: Model is created with specific vendor class

        :CaseImportance: Medium
        """
        vendor_class = gen_string('utf8')
        model = make_model({'vendor-class': vendor_class})
        assert model['vendor-class'] == vendor_class

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_name(self, name):
        """Don't create an Model with invalid data.

        :id: b2eade66-b612-47e7-bfcc-6e363023f498

        :parametrized: yes

        :expectedresults: Model is not created.

        :CaseImportance: High
        """
        with pytest.raises(CLIReturnCodeError):
            Model.create({'name': name})

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, class_model, new_name):
        """Fail to update shared model name

        :id: 98020a4a-1789-4df3-929c-6c132b57f5a1

        :parametrized: yes

        :expectedresults: Model name is not updated

        :CaseImportance: Medium
        """
        with pytest.raises(CLIReturnCodeError):
            Model.update({'id': class_model['id'], 'new-name': new_name})
        result = Model.info({'id': class_model['id']})
        assert class_model['name'] == result['name']

    @pytest.mark.tier1
    @pytest.mark.parametrize('entity_id', **parametrized(invalid_id_list()))
    def test_negative_delete_by_id(self, entity_id):
        """Delete model by wrong ID

        :id: f8b0d428-1b3d-4fc9-9ca1-1eb30c8ac20a

        :parametrized: yes

        :expectedresults: Model is not deleted

        :CaseImportance: High
        """
        with pytest.raises(CLIReturnCodeError):
            Model.delete({'id': entity_id})
