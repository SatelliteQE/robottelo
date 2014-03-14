from robottelo.common.helpers import generate_string

POSITIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 10)},
    {'name': generate_string("utf8", 10)},
    {'name': generate_string("alpha", 10)},
    {'name': generate_string("alphanumeric", 10)},
    {'name': generate_string("numeric", 10)},
    {'name': generate_string("html", 10)},
)

NEGATIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 300)},
    {'name': " "},
    {'': generate_string("alpha", 10)},
    {generate_string("alphanumeric", 10): " "},
)

POSITIVE_UPDATE_DATA = (
    ({'name': generate_string("latin1", 10)},
     {'new-name': generate_string("latin1", 10)}),
    ({'name': generate_string("utf8", 10)},
     {'new-name': generate_string("utf8", 10)}),
    ({'name': generate_string("alpha", 10)},
     {'new-name': generate_string("alpha", 10)}),
    ({'name': generate_string("alphanumeric", 10)},
     {'new-name': generate_string("alphanumeric", 10)}),
    ({'name': generate_string("numeric", 10)},
     {'new-name': generate_string("numeric", 10)}),
    ({'name': generate_string("utf8", 10)},
     {'new-name': generate_string("html", 6)}),
)

NEGATIVE_UPDATE_DATA = (
    ({'name': generate_string("utf8", 10)},
     {'new-name': generate_string("utf8", 300)}),
    ({'name': generate_string("utf8", 10)},
     {'new-name': ""}),
)

POSITIVE_DELETE_DATA = (
    {'name': generate_string("latin1", 10)},
    {'name': generate_string("utf8", 10)},
    {'name': generate_string("alpha", 10)},
    {'name': generate_string("alphanumeric", 10)},
    {'name': generate_string("numeric", 10)},
)

NEGATIVE_DELETE_DATA = (
    {'id': generate_string("alpha", 10)},
    {'id': None},
    {'id': ""},
    {},
    {'id': -1},
)
