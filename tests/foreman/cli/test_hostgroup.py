# -*- encoding: utf-8 -*-
"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI."""

from fauxfactory import gen_string
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.factory import make_hostgroup
from robottelo.common.decorators import run_only_on
from robottelo.test import MetaCLITestCase


@run_only_on('sat')
class TestHostGroup(MetaCLITestCase):

    factory = make_hostgroup
    factory_obj = HostGroup

    POSITIVE_UPDATE_DATA = (
        ({'id': gen_string("latin1", 10)},
         {'name': gen_string("latin1", 10)}),
        ({'id': gen_string("utf8", 10)},
         {'name': gen_string("utf8", 10)}),
        ({'id': gen_string("alpha", 10)},
         {'name': gen_string("alpha", 10)}),
        ({'id': gen_string("alphanumeric", 10)},
         {'name': gen_string("alphanumeric", 10)}),
        ({'id': gen_string("numeric", 10)},
         {'name': gen_string("numeric", 10)}),
        ({'id': gen_string("utf8", 10)},
         {'name': gen_string("html", 6)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'id': gen_string("utf8", 10)},
         {'name': gen_string("utf8", 300)}),
        ({'id': gen_string("utf8", 10)},
         {'name': ""}),
    )
