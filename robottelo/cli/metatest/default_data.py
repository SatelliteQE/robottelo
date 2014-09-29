from fauxfactory import gen_string

POSITIVE_CREATE_DATA = (
    {'name': gen_string("latin1", 10)},
    {'name': gen_string("utf8", 10)},
    {'name': gen_string("alpha", 10)},
    {'name': gen_string("alphanumeric", 10)},
    {'name': gen_string("numeric", 10)},
    {'name': gen_string("html", 10)},
)

NEGATIVE_CREATE_DATA = (
    {'name': gen_string("latin1", 300)},
    {'name': " "},
    {'': gen_string("alpha", 10)},
    {gen_string("alphanumeric", 10): " "},
)

POSITIVE_UPDATE_DATA = (
    ({'name': gen_string("latin1", 10)},
     {'new-name': gen_string("latin1", 10)}),
    ({'name': gen_string("utf8", 10)},
     {'new-name': gen_string("utf8", 10)}),
    ({'name': gen_string("alpha", 10)},
     {'new-name': gen_string("alpha", 10)}),
    ({'name': gen_string("alphanumeric", 10)},
     {'new-name': gen_string("alphanumeric", 10)}),
    ({'name': gen_string("numeric", 10)},
     {'new-name': gen_string("numeric", 10)}),
    ({'name': gen_string("utf8", 10)},
     {'new-name': gen_string("html", 6)}),
)

NEGATIVE_UPDATE_DATA = (
    ({'name': gen_string("utf8", 10)},
     {'new-name': gen_string("utf8", 300)}),
    ({'name': gen_string("utf8", 10)},
     {'new-name': ""}),
)

POSITIVE_DELETE_DATA = (
    {'name': gen_string("latin1", 10)},
    {'name': gen_string("utf8", 10)},
    {'name': gen_string("alpha", 10)},
    {'name': gen_string("alphanumeric", 10)},
    {'name': gen_string("numeric", 10)},
)

NEGATIVE_DELETE_DATA = (
    {'id': gen_string("alpha", 10)},
    {'id': None},
    {'id': ""},
    {},
    {'id': -1},
)
