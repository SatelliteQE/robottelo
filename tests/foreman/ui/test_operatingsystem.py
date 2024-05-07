"""Test class for Operating System UI

:Requirement: Provisioning

:CaseAutomation: Automated

:CaseComponent: Provisioning

:Team: Rocket

:CaseImportance: High

"""

import pytest

from robottelo.constants import HASH_TYPE
from robottelo.utils.datafactory import gen_string


@pytest.mark.tier2
def test_positive_end_to_end(session, module_org, module_location, target_sat):
    """Create all possible entities that required for operating system and then
    test all scenarios like create/read/update/delete for it

    :id: 280afff3-ebf4-4a54-af11-200327b8957b

    :expectedresults: All scenarios flows work properly

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    minor_version = gen_string('numeric', 2)
    description = gen_string('alpha')
    family = 'Red Hat'
    hash = HASH_TYPE['md5']
    architecture = target_sat.api.Architecture().create()
    ptable = target_sat.api.PartitionTable(
        organization=[module_org], location=[module_location], os_family='Redhat'
    ).create()
    medium = target_sat.api.Media(organization=[module_org], location=[module_location]).create()
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        # Create
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
        assert os['templates']['resources']['Provisioning template'] == 'Kickstart default'
        assert ptable.name in os['partition_table']['resources']['assigned']
        assert os['installation_media']['resources']['assigned'][0] == medium.name
        assert len(os['parameters']['os_params']) == 1
        assert os['parameters']['os_params'][0]['name'] == param_name
        assert os['parameters']['os_params'][0]['value'] == param_value
        template_name = gen_string('alpha')
        new_description = gen_string('alpha')
        new_name = gen_string('alpha')
        new_major_version = gen_string('numeric', 2)
        new_minor_version = gen_string('numeric', 2)
        new_family = 'Red Hat CoreOS'
        new_hash = HASH_TYPE['sha512']
        new_architecture = target_sat.api.Architecture().create()
        new_ptable = target_sat.api.PartitionTable(
            organization=[module_org], location=[module_location], os_family='Redhat'
        ).create()
        new_medium = target_sat.api.Media(
            organization=[module_org], location=[module_location]
        ).create()
        new_param_value = gen_string('alpha')
        session.provisioningtemplate.create(
            {
                'template.name': template_name,
                'template.default': True,
                'type.snippet': False,
                'template.template_editor.editor': gen_string('alpha'),
                'type.template_type': 'Provisioning template',
                'association.applicable_os.assigned': [os['operating_system']['description']],
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        # Update
        session.operatingsystem.update(
            description,
            {
                'operating_system.name': new_name,
                'templates.resources': {'Provisioning template': template_name},
                'operating_system.description': new_description,
                'operating_system.major': new_major_version,
                'operating_system.minor': new_minor_version,
                'operating_system.family': new_family,
                'operating_system.password_hash': new_hash,
                'operating_system.architectures.assigned': [new_architecture.name],
                'partition_table.resources.assigned': [new_ptable.name],
                'installation_media.resources.assigned': [new_medium.name],
                'parameters.os_params': {'name': param_name, 'value': new_param_value},
            },
        )
        os = session.operatingsystem.read(new_description)
        assert os['operating_system']['name'] == new_name
        assert os['operating_system']['major'] == new_major_version
        assert os['operating_system']['minor'] == new_minor_version
        assert os['operating_system']['description'] == new_description
        assert os['operating_system']['family'] == new_family
        assert os['operating_system']['password_hash'] == new_hash
        assert new_architecture.name in os['operating_system']['architectures']['assigned']
        assert new_ptable.name in os['partition_table']['resources']['assigned']
        assert new_medium.name in os['installation_media']['resources']['assigned']
        assert os['templates']['resources']['Provisioning template'] == template_name
        assert len(os['parameters']['os_params']) == 1
        assert os['parameters']['os_params'][0]['name'] == param_name
        assert os['parameters']['os_params'][0]['value'] == new_param_value
        # Delete
        session.operatingsystem.delete(new_description)
        assert not session.operatingsystem.search(new_description)


@pytest.mark.tier2
def test_positive_verify_os_name(session, target_sat):
    """Check that the Operating System name is displayed correctly

    :id: 2cb9cdcf-1723-4317-ab0a-971e7b2dd161

    :expectedresults: The full operating system name is displayed in the title column.

    :BZ: 1778503

    :CaseImportance: Low
    """
    name = gen_string('alpha')
    major_version = gen_string('numeric', 2)
    os_full_name = f"{name} {major_version}"
    target_sat.api.OperatingSystem(name=name, major=major_version).create()
    with session:
        values = session.operatingsystem.search(os_full_name)
        assert values[0]['Title'] == os_full_name
