# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Architecture CLI
"""

from robottelo.cli.architecture import Architecture
from robottelo.cli.factory import make_architecture
from tests.foreman.cli.basecli import MetaCLI


class TestArchitecture(MetaCLI):
    """
    Architecture CLI related tests.
    """

    factory = make_architecture
    factory_obj = Architecture
