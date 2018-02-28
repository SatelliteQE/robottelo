from nailgun import entities

from robottelo.datafactory import gen_string, valid_data_list
from robottelo.decorators import fixture, parametrize


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@parametrize('name', valid_data_list())
def test_positive_create(session, name):
    major_version = gen_string('numeric', 2)
    with session:
        session.operatingsystem.create({
            'name': name, 'major': major_version})
        os_full_name = '{} {}'.format(name, major_version)
        assert session.operatingsystem.search(name) == os_full_name


def test_positive_create_with_arch(session):
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    arch = entities.Architecture().create()
    with session:
        session.operatingsystem.create({
            'name': name,
            'major': major_version,
            'architectures.assigned': [arch.name],
        })
        os_full_name = '{} {}'.format(name, major_version)
        assert session.operatingsystem.search(name) == os_full_name
        arch_values = session.architecture.read(arch.name)
        assert len(arch_values['operatingsystems']['assigned']) == 1
        assert arch_values['operatingsystems']['assigned'][0] == os_full_name


def test_positive_create_with_ptable(session):
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    org = entities.Organization().create()
    loc = entities.Location().create()
    ptable = entities.PartitionTable(
        organization=[org],
        location=[loc],
    ).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        session.operatingsystem.create({
            'name': name,
            'major': major_version,
            'ptables.assigned': [ptable.name],
        })
        os_full_name = '{} {}'.format(name, major_version)
        assert session.operatingsystem.search(name) == os_full_name


def test_positive_create_with_ptable_same_org(module_org, session):
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    ptable = entities.PartitionTable(organization=[module_org]).create()
    with session:
        session.operatingsystem.create({
            'name': name,
            'major': major_version,
            'ptables.assigned': [ptable.name],
        })
        os_full_name = '{} {}'.format(name, major_version)
        assert session.operatingsystem.search(name) == os_full_name


def test_positive_delete(session):
    name = gen_string('alpha')
    major = gen_string('numeric', 2)
    entities.OperatingSystem(name=name, major=major).create()
    with session:
        assert session.operatingsystem.search(name) == '{} {}'.format(
            name, major)
        session.operatingsystem.delete(name)
        assert session.operatingsystem.search(name) == None
