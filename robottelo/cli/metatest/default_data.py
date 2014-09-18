from fauxfactory import FauxFactory

POSITIVE_CREATE_DATA = (
    {'name': FauxFactory.generate_string("latin1", 10)},
    {'name': FauxFactory.generate_string("utf8", 10)},
    {'name': FauxFactory.generate_string("alpha", 10)},
    {'name': FauxFactory.generate_string("alphanumeric", 10)},
    {'name': FauxFactory.generate_string("numeric", 10)},
    {'name': FauxFactory.generate_string("html", 10)},
)

NEGATIVE_CREATE_DATA = (
    {'name': FauxFactory.generate_string("latin1", 300)},
    {'name': " "},
    {'': FauxFactory.generate_string("alpha", 10)},
    {FauxFactory.generate_string("alphanumeric", 10): " "},
)

POSITIVE_UPDATE_DATA = (
    ({'name': FauxFactory.generate_string("latin1", 10)},
     {'new-name': FauxFactory.generate_string("latin1", 10)}),
    ({'name': FauxFactory.generate_string("utf8", 10)},
     {'new-name': FauxFactory.generate_string("utf8", 10)}),
    ({'name': FauxFactory.generate_string("alpha", 10)},
     {'new-name': FauxFactory.generate_string("alpha", 10)}),
    ({'name': FauxFactory.generate_string("alphanumeric", 10)},
     {'new-name': FauxFactory.generate_string("alphanumeric", 10)}),
    ({'name': FauxFactory.generate_string("numeric", 10)},
     {'new-name': FauxFactory.generate_string("numeric", 10)}),
    ({'name': FauxFactory.generate_string("utf8", 10)},
     {'new-name': FauxFactory.generate_string("html", 6)}),
)

NEGATIVE_UPDATE_DATA = (
    ({'name': FauxFactory.generate_string("utf8", 10)},
     {'new-name': FauxFactory.generate_string("utf8", 300)}),
    ({'name': FauxFactory.generate_string("utf8", 10)},
     {'new-name': ""}),
)

POSITIVE_DELETE_DATA = (
    {'name': FauxFactory.generate_string("latin1", 10)},
    {'name': FauxFactory.generate_string("utf8", 10)},
    {'name': FauxFactory.generate_string("alpha", 10)},
    {'name': FauxFactory.generate_string("alphanumeric", 10)},
    {'name': FauxFactory.generate_string("numeric", 10)},
)

NEGATIVE_DELETE_DATA = (
    {'id': FauxFactory.generate_string("alpha", 10)},
    {'id': None},
    {'id': ""},
    {},
    {'id': -1},
)
