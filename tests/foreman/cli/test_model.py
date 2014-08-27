# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Model CLI
"""

from robottelo.cli.model import Model
from robottelo.cli.factory import make_model
from robottelo.common.helpers import generate_string
from robottelo.test import MetaCLITestCase


class TestModel(MetaCLITestCase):

    factory = make_model
    factory_obj = Model

    def test_create_model_1(self):
        """
        @Feature: Model - Positive Create
        @Test: Check if Model can be created
        @Assert: Model is created
        """
        result = self.factory()
        model = Model().info({'name': result['name']})
        self.assertEqual(result['name'], model.stdout['name'])

    def test_create_model_2(self):
        """
        @Feature: Model - Positive Create
        @Test: Check if Model can be created with specific vendor class
        @Assert: Model is created with specific vendor class
        """
        result = self.factory({'vendor-class': generate_string("alpha", 10)})
        # Check that Model was created with proper values
        model = Model().info({'name': result['name']})
        self.assertEqual(result['vendor-class'], model.stdout['vendor-class'])

    def test_update_model(self):
        """
        @Feature: Model - Positive Update
        @Test: Check if Model can be updated
        @Assert: Model is updated
        """
        result = self.factory({'vendor-class': generate_string("alpha", 10)})
        # Check that Model was created with proper values
        model = Model().info({'name': result['name']})
        self.assertEqual(result['vendor-class'], model.stdout['vendor-class'])

        new_name = generate_string("alpha", 10)
        model = Model().update({'name': result['name'], 'new-name': new_name})
        self.assertEqual(model.return_code, 0)
        self.assertEqual(
            len(model.stderr), 0, "There should not be an error here")

        model = Model.info({'name': new_name})
        self.assertEqual(model.return_code, 0)
        self.assertEqual(len(model.stderr), 0)
        self.assertEqual(
            model.stdout['name'],
            new_name,
            "Model name was not updated"
        )
