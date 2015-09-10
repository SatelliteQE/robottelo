# -*- encoding: utf-8 -*-
"""Test class for Model CLI"""

from fauxfactory import gen_string
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.model import Model
from robottelo.cli.factory import make_model
from robottelo.decorators import run_only_on
from robottelo.test import MetaCLITestCase


@run_only_on('sat')
class TestModel(MetaCLITestCase):

    factory = make_model
    factory_obj = Model

    def test_create_model_1(self):
        """@Test: Check if Model can be created

        @Feature: Model - Positive Create

        @Assert: Model is created

        """
        try:
            make_model()
        except CLIFactoryError as err:
            self.fail(err)

    def test_create_model_2(self):
        """@Test: Check if Model can be created with specific vendor class

        @Feature: Model - Positive Create

        @Assert: Model is created with specific vendor class

        """
        vendor_class = gen_string('utf8')
        model = make_model({'vendor-class': vendor_class})
        self.assertEqual(model['vendor-class'], vendor_class)

    def test_update_model(self):
        """@Test: Check if Model can be updated

        @Feature: Model - Positive Update

        @Assert: Model is updated

        """

        name = gen_string("alpha")
        try:
            model = self.factory({'name': name})
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(name, model['name'])

        new_name = gen_string("alpha")
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
