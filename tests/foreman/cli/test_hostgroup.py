# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""Test class for Hostgroup CLI"""

from fauxfactory import FauxFactory
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.factory import make_hostgroup
from robottelo.common.decorators import run_only_on
from robottelo.test import MetaCLITestCase


@run_only_on('sat')
class TestHostGroup(MetaCLITestCase):

    factory = make_hostgroup
    factory_obj = HostGroup

    POSITIVE_UPDATE_DATA = (
        ({'id': FauxFactory.generate_string("latin1", 10)},
         {'name': FauxFactory.generate_string("latin1", 10)}),
        ({'id': FauxFactory.generate_string("utf8", 10)},
         {'name': FauxFactory.generate_string("utf8", 10)}),
        ({'id': FauxFactory.generate_string("alpha", 10)},
         {'name': FauxFactory.generate_string("alpha", 10)}),
        ({'id': FauxFactory.generate_string("alphanumeric", 10)},
         {'name': FauxFactory.generate_string("alphanumeric", 10)}),
        ({'id': FauxFactory.generate_string("numeric", 10)},
         {'name': FauxFactory.generate_string("numeric", 10)}),
        ({'id': FauxFactory.generate_string("utf8", 10)},
         {'name': FauxFactory.generate_string("html", 6)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'id': FauxFactory.generate_string("utf8", 10)},
         {'name': FauxFactory.generate_string("utf8", 300)}),
        ({'id': FauxFactory.generate_string("utf8", 10)},
         {'name': ""}),
    )
