# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Model CLI
"""

from robottelo.cli.model import Model
from robottelo.cli.factory import make_model
from robottelo.common.helpers import generate_name
from tests.cli.basecli import MetaCLI


class TestModel(MetaCLI):

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
        result = self.factory({'vendor-class': generate_name()})
        # Check that Model was created with proper values
        model = Model().info({'name': result['name']})
        self.assertEqual(result['vendor-class'], model.stdout['vendor-class'])
