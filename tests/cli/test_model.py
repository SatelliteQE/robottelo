# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Model CLI
"""

from basecli import BaseCLI
from robottelo.cli.factory import make_model
from robottelo.cli.model import Model
from robottelo.common.helpers import generate_name


class TestModel(BaseCLI):

    def test_create_model_1(self):
        """Successfully creates a new model"""

        result = make_model()
        model = Model().info({'name': result['name']})
        self.assertEqual(result['name'], model.stdout['Name'])

    def test_create_model_2(self):
        """Create model with specific vendor class"""

        result = make_model({'vendor-class': generate_name()})
        # Check that Model was created with proper values
        model = Model().info({'name': result['name']})
        self.assertEqual(result['vendor-class'], model.stdout['Vendor class'])
