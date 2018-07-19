"""Test class for Operating System UI

:Requirement: Operatingsystem

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.constants import HASH_TYPE
from robottelo.datafactory import gen_string, valid_data_list
from robottelo.decorators import fixture, parametrize, tier2, tier3


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@parametrize('name', **valid_data_list('ui'))
def test_positive_create(session, name):
    major_version = gen_string('numeric', 2)
    with session:
        session.operatingsystem.create({
            'operating_system.name': name,
            'operating_system.major': major_version
        })
        os_full_name = '{} {}'.format(name, major_version)
        assert session.operatingsystem.search(name)[0]['Title'] == os_full_name


@tier2
def test_positive_update_with_params(session):
    """Set Operating System parameter

    :id: 05b504d8-2518-4359-a53a-f577339f1ebe

    :expectedresults: OS is updated with new parameter

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        session.operatingsystem.create({
            'operating_system.name': name,
            'operating_system.major': major_version,
        })
        os_full_name = '{} {}'.format(name, major_version)
        assert session.operatingsystem.search(name)[0]['Title'] == os_full_name
        session.operatingsystem.update(
            os_full_name,
            {'parameters.os_params': {
                'name': param_name, 'value': param_value}}
        )
        values = session.operatingsystem.read(os_full_name)
        assert len(values['parameters']) == 1
        assert values['parameters']['os_params'][0]['name'] == param_name
        assert values['parameters']['os_params'][0]['value'] == param_value


def test_positive_delete(session):
    name = gen_string('alpha')
    major = gen_string('numeric', 2)
    entities.OperatingSystem(name=name, major=major).create()
    os_full_name = '{} {}'.format(name, major)
    with session:
        assert session.operatingsystem.search(name)[0]['Title'] == os_full_name
        session.operatingsystem.delete(os_full_name)
        assert not session.operatingsystem.search(name)


@tier3
def test_positive_end_to_end(session):
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    minor_version = gen_string('numeric', 2)
    description = gen_string('alpha')
    family = 'Red Hat'
    hash = HASH_TYPE['md5']
    architecture = entities.Architecture().create()
    org = entities.Organization().create()
    loc = entities.Location().create()
    ptable = entities.PartitionTable(
        organization=[org],
        location=[loc],
        os_family='Redhat',
    ).create()
    medium = entities.Media(
        organization=[org],
        location=[loc],
    ).create()
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        session.operatingsystem.create({
            'operating_system.name': name,
            'operating_system.major': major_version,
            'operating_system.minor': minor_version,
            'operating_system.description': description,
            'operating_system.family': family,
            'operating_system.password_hash': hash,
            'operating_system.architectures.assigned': [architecture.name],
            'partition_table.resources.assigned': [ptable.name],
            'installation_media.resources.assigned': [medium.name],
            'parameters.os_params': {'name': param_name, 'value': param_value},
        })
        assert session.operatingsystem.search(
            description)[0]['Title'] == description
        os = session.operatingsystem.read(description)
        assert os['operating_system']['name'] == name
        assert os['operating_system']['major'] == major_version
        assert os['operating_system']['minor'] == minor_version
        assert os['operating_system']['description'] == description
        assert os['operating_system']['family'] == family
        assert os['operating_system']['password_hash'] == hash
        assert len(os['operating_system']['architectures']['assigned']) == 1
        assert os['operating_system'][
            'architectures']['assigned'][0] == architecture.name
        assert ptable.name in os['partition_table']['resources']['assigned']
        assert os[
            'installation_media']['resources']['assigned'][0] == medium.name
        assert len(os['parameters']['os_params']) == 1
        assert os['parameters']['os_params'][0]['name'] == param_name
        assert os['parameters']['os_params'][0]['value'] == param_value
        new_description = gen_string('alpha')
        session.operatingsystem.update(
            description,
            {'operating_system.description': new_description}
        )
        assert not session.operatingsystem.search(description)
        assert session.operatingsystem.search(
            new_description)[0]['Title'] == new_description
        assert session.partitiontable.search(
            ptable.name)[0]['Operating Systems'] == new_description
        session.operatingsystem.delete(new_description)
        assert not session.operatingsystem.search(new_description)
