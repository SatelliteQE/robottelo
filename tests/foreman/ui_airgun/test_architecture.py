from nailgun import entities

from robottelo.datafactory import gen_string, valid_data_list
from robottelo.decorators import parametrize


@parametrize('name', valid_data_list())
def test_positive_create(session, name):
    with session:
        session.architecture.create({'name': name})
        assert session.architecture.search(name) == name


def test_positive_create_with_os(session):
    name = gen_string('alpha')
    os_name = entities.OperatingSystem().create().name
    with session:
        session.architecture.create({
            'name': name,
            'operatingsystems.assigned': [os_name],
        })
        assert session.architecture.search(name) == name
