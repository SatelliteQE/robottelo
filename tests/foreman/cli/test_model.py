# -*- encoding: utf-8 -*-
"""Test for Model CLI"""

from fauxfactory import gen_string
from robottelo.cli.model import Model
from robottelo.cli.factory import make_model
from robottelo.decorators import run_only_on
from robottelo.test import MetaCLITestCase


@run_only_on('sat')
class TestModel(MetaCLITestCase):
    """Test class for Model CLI"""
    factory = make_model
    factory_obj = Model

    # pylint: disable=no-self-use
    def test_create_model_1(self):
        """@Test: Check if Model can be created

        @Feature: Model - Positive Create

        @Assert: Model is created

        """
        make_model()

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
        name = gen_string('alpha')
        # pylint: disable=too-many-function-args
        model = self.factory({'name': name})
        self.assertEqual(name, model['name'])
        new_name = gen_string('alpha')
        Model.update({'name': model['name'], 'new-name': new_name})
        model = Model.info({'name': new_name})
        self.assertEqual(model['name'], new_name)
