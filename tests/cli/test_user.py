# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for User CLI
"""

from robottelo.cli.user import User
from robottelo.cli.factory import make_user
from robottelo.common.helpers import generate_string
from tests.cli.basecli import MetaCLI


class TestUser(MetaCLI):

    factory = make_user
    factory_obj = User
    search_key = 'login'

    POSITIVE_CREATE_DATA = (
        {'login': generate_string("latin1", 10).encode("utf-8")},
        {'login': generate_string("utf8", 10).encode("utf-8")},
        {'login': generate_string("alpha", 10)},
        {'login': generate_string("alphanumeric", 10)},
        {'login': generate_string("numeric", 10)},
        {'login': generate_string("html", 10)},
    )

    NEGATIVE_CREATE_DATA = (
        {'login': generate_string("latin1", 300).encode("utf-8")},
        {'login': " "},
        {'': generate_string("alpha", 10)},
        {generate_string("alphanumeric", 10): " "},
    )

    POSITIVE_UPDATE_DATA = (
        ({'login': generate_string("latin1", 10).encode("utf-8")},
         {'login': generate_string("latin1", 10).encode("utf-8")}),
        ({'login': generate_string("utf8", 10).encode("utf-8")},
         {'login': generate_string("utf8", 10).encode("utf-8")}),
        ({'login': generate_string("alpha", 10)},
         {'login': generate_string("alpha", 10)}),
        ({'login': generate_string("alphanumeric", 10)},
         {'login': generate_string("alphanumeric", 10)}),
        ({'login': generate_string("numeric", 10)},
         {'login': generate_string("numeric", 10)}),
        ({'login': generate_string("utf8", 10).encode("utf-8")},
         {'login': generate_string("html", 6)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'login': generate_string("utf8", 10).encode("utf-8")},
         {'login': generate_string("utf8", 300).encode("utf-8")}),
        ({'login': generate_string("utf8", 10).encode("utf-8")},
         {'login': " "}),
    )

    POSITIVE_DELETE_DATA = (
        {'login': generate_string("latin1", 10).encode("utf-8")},
        {'login': generate_string("utf8", 10).encode("utf-8")},
        {'login': generate_string("alpha", 10)},
        {'login': generate_string("alphanumeric", 10)},
        {'login': generate_string("numeric", 10)},
    )

    NEGATIVE_DELETE_DATA = (
        {'id': generate_string("alpha", 10)},
        {'id': None},
        {'id': " "},
        {},
        {'id': -1},
    )
