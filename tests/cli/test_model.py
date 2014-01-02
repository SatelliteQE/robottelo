# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Model CLI
"""

from basecli import BaseCLI
from ddt import ddt
from metatest import MetaCLITest
from robottelo.cli.model import Model
from robottelo.cli.factory import make_model
from robottelo.common.helpers import generate_name


@ddt
class TestModel(BaseCLI):

    __metaclass__ = MetaCLITest

    factory = make_model
    factory_obj = Model

    def test_create_model_1(self):
        """Successfully creates a new model"""

        result = self.create()
        model = Model().info({'name': result['name']})
        self.assertEqual(result['name'], model.stdout['name'])

    def test_create_model_2(self):
        """Create model with specific vendor class"""

        result = self.create({'vendor-class': generate_name()})
        # Check that Model was created with proper values
        model = Model().info({'name': result['name']})
        self.assertEqual(result['vendor-class'], model.stdout['vendor-class'])
