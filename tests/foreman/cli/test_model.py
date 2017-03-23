# -*- encoding: utf-8 -*-
"""Test for Model CLI

:Requirement: Model

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_model
from robottelo.cli.model import Model
from robottelo.datafactory import (
    invalid_id_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import run_only_on, tier1
from robottelo.test import CLITestCase


class ModelTestCase(CLITestCase):
    """Test class for Model CLI"""
    @tier1
    def test_positive_create_with_name(self):
        """Successfully creates a Model.

        :id: c8192831-5dde-4c3c-8427-00902ddbc0ac

        :Assert: Model is created.

        :CaseLevel: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                model = make_model({'name': name})
                self.assertEqual(model['name'], name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_vendor_class(self):
        """Check if Model can be created with specific vendor class

        :id: c36d3490-cd12-4f5f-a453-2ae5d0404496

        :Assert: Model is created with specific vendor class

        :CaseLevel: Critical
        """
        vendor_class = gen_string('utf8')
        model = make_model({'vendor-class': vendor_class})
        self.assertEqual(model['vendor-class'], vendor_class)

    @tier1
    def test_negative_create_with_name(self):
        """Don't create an Model with invalid data.

        :id: b2eade66-b612-47e7-bfcc-6e363023f498

        :Assert: Model is not created.

        :CaseLevel: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    Model.create({'name': name})

    @tier1
    def test_positive_update_name(self):
        """Successfully update an Model.

        :id: 66eb6cf2-9ec5-4947-97e0-b612780c5cc3

        :Assert: Model is updated.

        :CaseLevel: Critical
        """
        model = make_model()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                Model.update({
                    'id': model['id'],
                    'new-name': new_name,
                })
                model = Model.info({'id': model['id']})
                self.assertEqual(model['name'], new_name)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Create Model then fail to update its name

        :id: 98020a4a-1789-4df3-929c-6c132b57f5a1

        :assert: Model name is not updated

        :CaseLevel: Critical
        """
        model = make_model()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    Model.update({
                        'id': model['id'],
                        'new-name': new_name,
                    })
                result = Model.info({'id': model['id']})
                self.assertEqual(model['name'], result['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_id(self):
        """Create Model with valid values then delete it
        by ID

        :id: 39f02cec-ac4c-4801-9a4a-11160247213f

        :assert: Model is deleted

        :CaseLevel: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                model = make_model({'name': name})
                Model.delete({'id': model['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Model.info({'id': model['id']})

    @run_only_on('sat')
    @tier1
    def test_negative_delete_by_id(self):
        """Create Model then delete it by wrong ID

        :id: f8b0d428-1b3d-4fc9-9ca1-1eb30c8ac20a

        :assert: Model is not deleted

        :CaseLevel: Critical
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Model.delete({'id': entity_id})
