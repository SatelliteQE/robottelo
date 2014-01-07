from robottelo.common.helpers import generate_string

POSITIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 10).encode("utf-8")},
    {'name': generate_string("utf8", 10).encode("utf-8")},
    {'name': generate_string("alpha", 10)},
    {'name': generate_string("alphanumeric", 10)},
    {'name': generate_string("numeric", 10)},
)


NEGATIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 300).encode("utf-8")},
    {'name': " "},
    {'': generate_string("alpha", 10)},
    {generate_string("alphanumeric", 10): " "},
)

POSITIVE_UPDATE_DATA = ()
NEGATIVE_UPDATE_DATA = ()
POSITIVE_DELETE_DATA = ()
NEGATIVE_DELETE_DATA = ()
