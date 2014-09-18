# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Model CLI"""

from fauxfactory import FauxFactory
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.model import Model
from robottelo.cli.factory import make_model
from robottelo.test import MetaCLITestCase


class TestModel(MetaCLITestCase):

    factory = make_model
    factory_obj = Model

    def test_create_model_1(self):
        """@Test: Check if Model can be created

        @Feature: Model - Positive Create

        @Assert: Model is created

        """
        result = self.factory()
        model = Model().info({'name': result['name']})
        self.assertEqual(result['name'], model.stdout['name'])

    def test_create_model_2(self):
        """@Test: Check if Model can be created with specific vendor class

        @Feature: Model - Positive Create

        @Assert: Model is created with specific vendor class

        """
        result = self.factory({
            'vendor-class': FauxFactory.generate_string("alpha", 10),
        })
        # Check that Model was created with proper values
        model = Model().info({'name': result['name']})
        self.assertEqual(result['vendor-class'], model.stdout['vendor-class'])

    def test_update_model(self):
        """@Test: Check if Model can be updated

        @Feature: Model - Positive Update

        @Assert: Model is updated

        """

        name = FauxFactory.generate_string("alpha", 10)
        try:
            model = self.factory({'name': name})
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(name, model['name'])

        new_name = FauxFactory.generate_string("alpha", 10)
        result = Model().update({'name': model['name'], 'new-name': new_name})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            len(result.stderr), 0, "There should not be an error here")

        result = Model.info({'name': new_name})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['name'],
            new_name,
            "Model name was not updated"
        )
