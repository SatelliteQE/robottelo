"""Test class for Operating System UI

:Requirement: Operatingsystem

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.constants import DEFAULT_TEMPLATE
from robottelo.constants import HASH_TYPE
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.mark.tier2
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
        session.operatingsystem.create(
            {'operating_system.name': name, 'operating_system.major': major_version}
        )
        os_full_name = f'{name} {major_version}'
        assert session.operatingsystem.search(name)[0]['Title'] == os_full_name
        session.operatingsystem.update(
            os_full_name, {'parameters.os_params': {'name': param_name, 'value': param_value}}
        )
        values = session.operatingsystem.read(os_full_name)
        assert len(values['parameters']) == 1
        assert values['parameters']['os_params'][0]['name'] == param_name
        assert values['parameters']['os_params'][0]['value'] == param_value


@pytest.mark.tier2
def test_positive_end_to_end(session):
    """Create all possible entities that required for operating system and then
    test all scenarios like create/read/update/delete for it

    :id: 280afff3-ebf4-4a54-af11-200327b8957b

    :expectedresults: All scenarios flows work properly

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
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
        organization=[org], location=[loc], os_family='Redhat'
    ).create()
    medium = entities.Media(organization=[org], location=[loc]).create()
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        session.operatingsystem.create(
            {
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
            }
        )
        assert session.operatingsystem.search(description)[0]['Title'] == description
        os = session.operatingsystem.read(description)
        assert os['operating_system']['name'] == name
        assert os['operating_system']['major'] == major_version
        assert os['operating_system']['minor'] == minor_version
        assert os['operating_system']['description'] == description
        assert os['operating_system']['family'] == family
        assert os['operating_system']['password_hash'] == hash
        assert len(os['operating_system']['architectures']['assigned']) == 1
        assert os['operating_system']['architectures']['assigned'][0] == architecture.name
        assert ptable.name in os['partition_table']['resources']['assigned']
        assert os['installation_media']['resources']['assigned'][0] == medium.name
        assert len(os['parameters']['os_params']) == 1
        assert os['parameters']['os_params'][0]['name'] == param_name
        assert os['parameters']['os_params'][0]['value'] == param_value
        new_description = gen_string('alpha')
        session.operatingsystem.update(
            description, {'operating_system.description': new_description}
        )
        assert not session.operatingsystem.search(description)
        assert session.operatingsystem.search(new_description)[0]['Title'] == new_description
        assert session.partitiontable.search(ptable.name)[0]['Operating Systems'] == new_description
        session.operatingsystem.delete(new_description)
        assert not session.operatingsystem.search(new_description)


@pytest.mark.tier2
def test_positive_update_template(session, module_org):
    """Update operating system with new provisioning template value

    :id: 0b90eb24-8fc9-4e42-8709-6eee8ffbbdb5

    :expectedresults: OS is updated with new template

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    os = entities.OperatingSystem(name=name, major=major_version, family='Redhat').create()
    template = entities.ProvisioningTemplate(
        organization=[module_org],
        snippet=False,
        template_kind=entities.TemplateKind().search(query={'search': 'name="provision"'})[0],
        operatingsystem=[os],
    ).create()
    with session:
        os_full_name = f'{name} {major_version}'
        values = session.operatingsystem.read(os_full_name)
        assert values['templates']['resources']['Provisioning template'] == DEFAULT_TEMPLATE
        session.operatingsystem.update(
            os_full_name, {'templates.resources': {'Provisioning template': template.name}}
        )
        values = session.operatingsystem.read(os_full_name)
        assert values['templates']['resources']['Provisioning template'] == template.name


@pytest.mark.tier2
def test_positive_verify_os_name(session):
    """Check that the Operating System name is displayed correctly

    :id: 2cb9cdcf-1723-4317-ab0a-971e7b2dd161

    :expectedresults: The full operating system name is displayed in the title column.

    :BZ: 1778503

    :CaseLevel: Component

    :CaseImportance: Low
    """
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    os_full_name = f"{name} {major_version}"
    entities.OperatingSystem(name=name, major=major_version).create()
    with session:
        values = session.operatingsystem.search(os_full_name)
        assert values[0]['Title'] == os_full_name
