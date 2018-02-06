from nailgun import entities

from robottelo.datafactory import gen_string, valid_data_list
from robottelo.decorators import parametrize


@parametrize('name', valid_data_list())
def test_positive_create(session, name):
    major_version = gen_string('numeric', 2)
    with session:
        session.os.create_operating_system({
            'name': name, 'major': major_version})
        assert session.os.search(name) == '{} {}'.format(name, major_version)


def test_positive_create_with_ptable(session):
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    ptable = entities.PartitionTable().create()
    with session:
        session.os.create_operating_system({
            'name': name,
            'major': major_version,
            'ptable.operation': 'Add',
            'ptable.values': [ptable.name],
        })
        assert session.os.search(name) == '{} {}'.format(name, major_version)
