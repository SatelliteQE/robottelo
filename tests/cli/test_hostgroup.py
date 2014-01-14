# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Hostgroup CLI
"""

from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.factory import make_hostgroup
from tests.cli.basecli import MetaCLI


class TestHostGroup(MetaCLI):

    factory = make_hostgroup
    factory_obj = HostGroup
