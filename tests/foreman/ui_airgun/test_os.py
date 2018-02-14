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
        session.os.create_operating_system({
            'name': name, 'major': major_version})
        assert session.os.search(name) == '{} {}'.format(name, major_version)


def test_positive_create_with_arch(session):
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    arch = entities.Architecture().create()
    with session:
        session.os.create_operating_system({
            'name': name,
            'major': major_version,
            'arch_element.operation': 'Add',
            'arch_element.values': [arch.name],
        })
        os_full_name = '{} {}'.format(name, major_version)
        assert session.os.search(name) == os_full_name
        arch_values = session.architecture.view_architecture(arch.name)
        assert len(arch_values['os_element']['assigned']) == 1
        assert arch_values['os_element']['assigned'][0] == os_full_name


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
        session.os.create_operating_system({
            'name': name,
            'major': major_version,
            'ptable.operation': 'Add',
            'ptable.values': [ptable.name],
        })
        assert session.os.search(name) == '{} {}'.format(name, major_version)


def test_positive_create_with_ptable_same_org(module_org, session):
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    ptable = entities.PartitionTable(organization=[module_org]).create()
    with session:
        session.os.create_operating_system({
            'name': name,
            'major': major_version,
            'ptable.operation': 'Add',
            'ptable.values': [ptable.name],
        })
        assert session.os.search(name) == '{} {}'.format(name, major_version)
