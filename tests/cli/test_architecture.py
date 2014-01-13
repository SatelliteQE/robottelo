# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Architecture CLI
"""

from basecli import BaseCLI
from robottelo.cli.architecture import Architecture
from robottelo.cli.factory import make_architecture
from robottelo.cli.metatest import MetaCLITest


class TestArchitecture(BaseCLI):
    """
    Architecture CLI related tests.
    """

    __metaclass__ = MetaCLITest

    factory = make_architecture
    factory_obj = Architecture
