# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Architecture CLI
"""

from basecli import MetaCLI
from robottelo.cli.architecture import Architecture
from robottelo.cli.factory import make_architecture


class TestArchitecture(MetaCLI):
    """
    Architecture CLI related tests.
    """

    factory = make_architecture
    factory_obj = Architecture
