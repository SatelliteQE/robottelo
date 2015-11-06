# -*- encoding: utf-8 -*-
"""Test for Model CLI"""

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_model
from robottelo.cli.model import Model
from robottelo.datafactory import (
    invalid_id_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import run_only_on
from robottelo.test import CLITestCase


class TestModel(CLITestCase):
    """Test class for Model CLI"""
    def test_positive_create(self):
        """@Test: Successfully creates an Model.

        @Feature: Model

        @Assert: Model is created.
        """
        for name in valid_data_list():
            with self.subTest(name):
                model = make_model({'name': name})
                self.assertEqual(model['name'], name)

    @run_only_on('sat')
    def test_create_model_vendor_class(self):
        """@Test: Check if Model can be created with specific vendor class

        @Feature: Model - Positive Create

        @Assert: Model is created with specific vendor class
        """
        vendor_class = gen_string('utf8')
        model = make_model({'vendor-class': vendor_class})
        self.assertEqual(model['vendor-class'], vendor_class)

    def test_negative_create(self):
        """@Test: Don't create an Model with invalid data.

        @Feature: Model

        @Assert: Model is not created.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    Model.create({'name': name})

    def test_positive_update_name(self):
        """@Test: Successfully update an Model.

        @Feature: Model

        @Assert: Model is updated.
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
    def test_negative_update(self):
        """@test: Create Model then fail to update its name

        @feature: Model

        @assert: Model name is not updated
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
    def test_positive_delete(self):
        """@test: Create Model with valid values then delete it
        by ID

        @feature: Model

        @assert: Model is deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                model = make_model({'name': name})
                Model.delete({'id': model['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Model.info({'id': model['id']})

    @run_only_on('sat')
    def test_negative_delete(self):
        """@test: Create Model then delete it by wrong ID

        @feature: Model

        @assert: Model is not deleted
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Model.delete({'id': entity_id})
