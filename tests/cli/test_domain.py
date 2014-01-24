# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Domain  CLI
"""

from robottelo.cli.domain import Domain
from robottelo.cli.factory import make_domain
from tests.cli.basecli import MetaCLI


class TestDomain(MetaCLI):

    factory = make_domain
    factory_obj = Domain
