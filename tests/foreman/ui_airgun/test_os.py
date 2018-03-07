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
        os_values = session.operatingsystem.read(os_full_name)
        assert len(os_values['ptables']['assigned']) == 1
        assert os_values['ptables']['assigned'][0] == ptable.name


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


def test_positive_create_with_params(session):
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        session.operatingsystem.create({
            'name': name,
            'major': major_version,
            'parameters': {'name': param_name, 'value': param_value},
        })
        os_full_name = '{} {}'.format(name, major_version)
        assert session.operatingsystem.search(name) == os_full_name
        values = session.operatingsystem.read(os_full_name)
        assert len(values['parameters']) == 1
        assert values['parameters'][0]['name'] == param_name
        assert values['parameters'][0]['value'] == param_value


def test_positive_delete(session):
    name = gen_string('alpha')
    major = gen_string('numeric', 2)
    entities.OperatingSystem(name=name, major=major).create()
    with session:
        assert session.operatingsystem.search(name) == '{} {}'.format(
            name, major)
        session.operatingsystem.delete(name)
        assert session.operatingsystem.search(name) is None
