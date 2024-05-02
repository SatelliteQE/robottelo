"""Test class for Operating System CLI

:Requirement: Provisioning

:CaseAutomation: Automated

:CaseComponent: Provisioning

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_alphanumeric, gen_string
import pytest

from robottelo.constants import DEFAULT_ORG
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import (
    filtered_datapoint,
    invalid_values_list,
    parametrized,
    valid_data_list,
)


@filtered_datapoint
def negative_delete_data():
    """Returns a list of invalid data for operating system deletion"""
    return [{'id': gen_string("alpha")}, {'id': None}, {'id': ""}, {}, {'id': -1}]


class TestOperatingSystem:
    """Test class for Operating System CLI."""

    @pytest.mark.e2e
    @pytest.mark.upgrade
    def test_positive_end_to_end_os(self, target_sat):
        """End-to-end test for Operating system

        :id: 531ab5c0-ccba-45ec-bd52-85b4df250d79

        :steps:
            1. Create OS
            2. Check OS is created with all given fields
            3. Read OS
            4. Update OS
            5. Check OS is updated with all given fields
            6. Delete OS
            7. Check if OS is deleted

        :expectedresults: All CRUD operations are performed successfully.
        """
        name = gen_string('alpha')
        desc = gen_string('alpha')
        os_family = 'Redhat'
        pass_hash = 'SHA256'
        minor_version = gen_string('numeric', 1)
        major_version = gen_string('numeric', 1)
        architecture = target_sat.cli_factory.make_architecture()
        medium = target_sat.cli_factory.make_medium()
        ptable = target_sat.cli_factory.make_partition_table()
        template = target_sat.cli_factory.make_template()
        # Create OS
        os = target_sat.cli.OperatingSys.create(
            {
                'name': name,
                'description': desc,
                'family': os_family,
                'password-hash': pass_hash,
                'major': major_version,
                'minor': minor_version,
                'architecture-ids': architecture['id'],
                'medium-ids': medium['id'],
                'partition-table-ids': ptable['id'],
                'provisioning-template-ids': template['id'],
            }
        )
        assert os['name'] == name
        assert os['title'] == desc
        assert os['family'] == os_family
        assert str(os['major-version']) == major_version
        assert str(os['minor-version']) == minor_version
        assert os['architectures'][0] == architecture['name']
        assert os['installation-media'][0] == medium['name']
        assert ptable['name'] in os['partition-tables']
        assert template['name'] in str(os['templates'])
        # Read OS
        os = target_sat.cli.OperatingSys.list({'search': f'name={name}'})
        assert os[0]['title'] == desc
        os = target_sat.cli.OperatingSys.info({'id': os[0]['id']})
        assert os['name'] == name
        assert os['title'] == desc
        assert os['family'] == os_family
        assert str(os['major-version']) == major_version
        assert str(os['minor-version']) == minor_version
        assert os['architectures'][0] == architecture['name']
        assert ptable['name'] in os['partition-tables']
        assert template['name'] in str(os['templates'])
        new_name = gen_string('alpha')
        new_desc = gen_string('alpha')
        new_os_family = 'Redhat'
        new_pass_hash = 'SHA256'
        new_minor_version = gen_string('numeric', 1)
        new_major_version = gen_string('numeric', 1)
        new_architecture = target_sat.cli_factory.make_architecture()
        new_medium = target_sat.cli_factory.make_medium()
        new_ptable = target_sat.cli_factory.make_partition_table()
        new_template = target_sat.cli_factory.make_template()
        os = target_sat.cli.OperatingSys.update(
            {
                'id': os['id'],
                'name': new_name,
                'description': new_desc,
                'family': new_os_family,
                'password-hash': new_pass_hash,
                'major': new_major_version,
                'minor': new_minor_version,
                'architecture-ids': new_architecture['id'],
                'medium-ids': new_medium['id'],
                'partition-table-ids': new_ptable['id'],
                'provisioning-template-ids': new_template['id'],
            }
        )
        os = target_sat.cli.OperatingSys.list({'search': f'title={new_desc}'})
        os = target_sat.cli.OperatingSys.info({'id': os[0]['id']})
        assert os['name'] == new_name
        assert os['title'] == new_desc
        assert os['family'] == new_os_family
        assert str(os['major-version']) == new_major_version
        assert str(os['minor-version']) == new_minor_version
        assert os['architectures'][0] == new_architecture['name']
        assert os['installation-media'][0] == new_medium['name']
        assert new_ptable['name'] in os['partition-tables']
        assert new_template['name'] in str(os['templates'])
        target_sat.cli.OperatingSys.delete({'id': os['id']})
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.OperatingSys.info({'id': os['id']})

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_with_name(self, name, target_sat):
        """Create Operating System for all variations of name

        :id: d36eba9b-ccf6-4c9d-a07f-c74eebada89b

        :parametrized: yes

        :expectedresults: Operating System is created and can be found

        :CaseImportance: Critical
        """
        os = target_sat.cli_factory.make_os({'name': name})
        assert os['name'] == name

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_name(self, name, target_sat):
        """Create Operating System using invalid names

        :id: 848a20ce-292a-47d8-beea-da5916c43f11

        :parametrized: yes

        :expectedresults: Operating System is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.OperatingSys.create({'name': name})

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, new_name, target_sat):
        """Negative update of system name

        :id: 4b18ff6d-7728-4245-a1ce-38e62c05f454

        :parametrized: yes

        :expectedresults: Operating System name is not updated

        :CaseImportance: Critical
        """
        os = target_sat.cli_factory.make_os({'name': gen_alphanumeric()})
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.OperatingSys.update({'id': os['id'], 'name': new_name})
        result = target_sat.cli.OperatingSys.info({'id': os['id']})
        assert result['name'] == os['name']

    @pytest.mark.tier1
    @pytest.mark.parametrize('test_data', **parametrized(negative_delete_data()))
    def test_negative_delete_by_id(self, test_data, target_sat):
        """Delete Operating System using invalid data

        :id: d29a9c95-1fe3-4a7a-9f7b-127be065856d

        :parametrized: yes

        :expectedresults: Operating System is not deleted

        :CaseImportance: Critical
        """
        os = target_sat.cli_factory.make_os()
        # The delete method requires the ID which we will not pass
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.OperatingSys.delete(test_data)
        # Now make sure that it still exists
        result = target_sat.cli.OperatingSys.info({'id': os['id']})
        assert os['id'] == result['id']
        assert os['name'] == result['name']

    @pytest.mark.tier2
    def test_positive_add_arch(self, target_sat):
        """Add Architecture to operating system

        :id: 99add22d-d936-4232-9441-beff85867040

        :expectedresults: Architecture is added to Operating System

        """
        architecture = target_sat.cli_factory.make_architecture()
        os = target_sat.cli_factory.make_os()
        target_sat.cli.OperatingSys.add_architecture(
            {'architecture-id': architecture['id'], 'id': os['id']}
        )
        os = target_sat.cli.OperatingSys.info({'id': os['id']})
        assert len(os['architectures']) == 1
        assert architecture['name'] == os['architectures'][0]

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_add_template(self, target_sat):
        """Add provisioning template to operating system

        :id: 0ea9eb88-2d27-423d-a9d3-fdd788b4e28a

        :expectedresults: Provisioning template is added to Operating System

        """
        template = target_sat.cli_factory.make_template()
        os = target_sat.cli_factory.make_os()
        default_template_name = os['default-templates'][0]
        target_sat.cli.OperatingSys.add_provisioning_template(
            {'provisioning-template': template['name'], 'id': os['id']}
        )
        os = target_sat.cli.OperatingSys.info({'id': os['id']})
        assert len(os['templates']) == 2
        provision_template_name = f"{template['name']} ({template['type']})"
        assert default_template_name in os['templates']
        assert provision_template_name in os['templates']

    @pytest.mark.tier2
    def test_positive_add_ptable(self, target_sat):
        """Add partition table to operating system

        :id: beba676f-b4e4-48e1-bb0c-18ad91847566

        :expectedresults: Partition table is added to Operating System

        """
        # Create a partition table.
        ptable_name = target_sat.cli_factory.make_partition_table()['name']
        # Create an operating system.
        os_id = target_sat.cli_factory.make_os()['id']
        # Add the partition table to the operating system.
        target_sat.cli.OperatingSys.add_ptable({'id': os_id, 'partition-table': ptable_name})
        # Verify that the operating system has a partition table.
        os = target_sat.cli.OperatingSys.info({'id': os_id})
        assert len(os['partition-tables']) == 1
        assert os['partition-tables'][0] == ptable_name

    @pytest.mark.tier2
    def test_positive_update_parameters_attributes(self, target_sat):
        """Update os-parameters-attributes to operating system

        :id: 5d566eea-b323-4128-9356-3bf39943e4d4

        :BZ: 1713553

        :expectedresults: Os-parameters-attributes are updated to Operating System
        """
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        os_id = target_sat.cli_factory.make_os()['id']
        target_sat.cli.OperatingSys.update(
            {
                'id': os_id,
                'os-parameters-attributes': 'name={}, value={}'.format(
                    param_name + '\\', param_value
                ),
            }
        )
        os = target_sat.cli.OperatingSys.info({'id': os_id}, output_format='json')
        assert param_name == os['parameters'][0]['name']
        assert param_value == os['parameters'][0]['value']


@pytest.mark.tier2
def test_positive_os_list_with_default_organization_set(target_sat):
    """list operating systems when the default organization is set

    :id: 2c1ba416-a5d5-4031-b154-54794569a85b

    :BZ: 1649011

    :customerscenario: true

    :expectedresults: os list should list operating systems when the
        default organization is set
    """
    target_sat.api.OperatingSystem().create()
    os_list_before_default = target_sat.cli.OperatingSys.list()
    assert len(os_list_before_default) > 0
    try:
        target_sat.cli.Defaults.add({'param-name': 'organization', 'param-value': DEFAULT_ORG})
        result = target_sat.execute('hammer defaults list')
        assert result.status == 0
        assert DEFAULT_ORG in result.stdout
        os_list_after_default = target_sat.cli.OperatingSys.list()
        assert len(os_list_after_default) > 0

    finally:
        target_sat.cli.Defaults.delete({'param-name': 'organization'})
        result = target_sat.execute('hammer defaults list')
        assert result.status == 0
        assert DEFAULT_ORG not in result.stdout
