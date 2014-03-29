# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Hostgroup CLI
"""

from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.factory import make_hostgroup
from robottelo.common.helpers import generate_string
from tests.cli.basecli import MetaCLI


class TestHostGroup(MetaCLI):

    factory = make_hostgroup
    factory_obj = HostGroup

    POSITIVE_UPDATE_DATA = (
        ({'id': generate_string("latin1", 10)},
         {'name': generate_string("latin1", 10)}),
        ({'id': generate_string("utf8", 10)},
         {'name': generate_string("utf8", 10)}),
        ({'id': generate_string("alpha", 10)},
         {'name': generate_string("alpha", 10)}),
        ({'id': generate_string("alphanumeric", 10)},
         {'name': generate_string("alphanumeric", 10)}),
        ({'id': generate_string("numeric", 10)},
         {'name': generate_string("numeric", 10)}),
        ({'id': generate_string("utf8", 10)},
         {'name': generate_string("html", 6)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'id': generate_string("utf8", 10)},
         {'name': generate_string("utf8", 300)}),
        ({'id': generate_string("utf8", 10)},
         {'name': ""}),
    )
