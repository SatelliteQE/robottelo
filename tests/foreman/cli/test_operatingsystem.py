"""Test class for Operating System CLI

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
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_architecture
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_os
from robottelo.cli.factory import make_partition_table
from robottelo.cli.factory import make_template
from robottelo.cli.operatingsys import OperatingSys
from robottelo.constants import DEFAULT_ORG
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list


@filtered_datapoint
def negative_delete_data():
    """Returns a list of invalid data for operating system deletion"""
    return [{'id': gen_string("alpha")}, {'id': None}, {'id': ""}, {}, {'id': -1}]


class TestOperatingSystem:
    """Test class for Operating System CLI."""

    @pytest.mark.tier1
    def test_positive_search_by_name(self):
        """Search for newly created OS by name

        :id: ff9f667c-97ca-49cd-902b-a9b18b5aa021

        :expectedresults: Operating System is created and listed

        :CaseImportance: Critical
        """
        os_list_before = OperatingSys.list()
        os = make_os()
        os_list = OperatingSys.list({'search': 'name=%s' % os['name']})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        assert os['id'] == os_info['id']
        os_list_after = OperatingSys.list()
        assert len(os_list_after) > len(os_list_before)

    @pytest.mark.tier1
    def test_positive_search_by_title(self):
        """Search for newly created OS by title

        :id: a555e848-f1f2-4326-aac6-9de8ff45abee

        :expectedresults: Operating System is created and listed

        :CaseImportance: Critical
        """
        os_list_before = OperatingSys.list()
        os = make_os()
        os_list = OperatingSys.list({'search': 'title=\\"%s\\"' % os['title']})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        assert os['id'] == os_info['id']
        os_list_after = OperatingSys.list()
        assert len(os_list_after) > len(os_list_before)

    @pytest.mark.tier1
    def test_positive_list(self):
        """Displays list for operating system

        :id: fca309c5-edff-4296-a800-55470669935a

        :expectedresults: Operating System is created and listed

        :CaseImportance: Critical
        """
        os_list_before = OperatingSys.list()
        name = gen_string('alpha')
        os = make_os({'name': name})
        os_list = OperatingSys.list({'search': 'name=%s' % name})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        assert os['id'] == os_info['id']
        os_list_after = OperatingSys.list()
        assert len(os_list_after) > len(os_list_before)

    @pytest.mark.tier1
    def test_positive_info_by_id(self):
        """Displays info for operating system by its ID

        :id: b8f23b53-439a-4726-9757-164d99d5ed05

        :expectedresults: Operating System is created and can be looked up by
            its ID

        :CaseImportance: Critical
        """
        os = make_os()
        os_info = OperatingSys.info({'id': os['id']})
        # Info does not return major or minor but a concat of name,
        # major and minor
        assert os['id'] == os_info['id']
        assert os['name'] == os_info['name']
        assert str(os['major-version']) == os_info['major-version']
        assert str(os['minor-version']) == os_info['minor-version']

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_with_name(self, name):
        """Create Operating System for all variations of name

        :id: d36eba9b-ccf6-4c9d-a07f-c74eebada89b

        :parametrized: yes

        :expectedresults: Operating System is created and can be found

        :CaseImportance: Critical
        """
        os = make_os({'name': name})
        assert os['name'] == name

    @pytest.mark.tier1
    def test_positive_create_with_arch_medium_ptable(self):
        """Create an OS pointing to an arch, medium and partition table.

        :id: 05bdb2c6-0d2e-4141-9e07-3ada3933b577

        :expectedresults: An operating system is created.

        :CaseImportance: Critical
        """
        architecture = make_architecture()
        medium = make_medium()
        ptable = make_partition_table()
        operating_system = make_os(
            {
                'architecture-ids': architecture['id'],
                'medium-ids': medium['id'],
                'partition-table-ids': ptable['id'],
            }
        )

        for attr in ('architectures', 'installation-media', 'partition-tables'):
            assert len(operating_system[attr]) == 1
        assert operating_system['architectures'][0] == architecture['name']
        assert operating_system['installation-media'][0] == medium['name']
        assert operating_system['partition-tables'][0] == ptable['name']

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_name(self, name):
        """Create Operating System using invalid names

        :id: 848a20ce-292a-47d8-beea-da5916c43f11

        :parametrized: yes

        :expectedresults: Operating System is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            make_os({'name': name})

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
    def test_positive_update_name(self, new_name):
        """Positive update of operating system name

        :id: 49b655f7-ba9b-4bb9-b09d-0f7140969a40

        :parametrized: yes

        :expectedresults: Operating System name is updated

        :CaseImportance: Critical
        """
        os = make_os({'name': gen_alphanumeric()})
        OperatingSys.update({'id': os['id'], 'name': new_name})
        result = OperatingSys.info({'id': os['id']})
        assert result['id'] == os['id']
        assert result['name'] != os['name']

    @pytest.mark.tier1
    def test_positive_update_major_version(self):
        """Update an Operating System's major version.

        :id: 38a89dbe-6d1c-4602-a4c1-664425668de8

        :expectedresults: Operating System major version is updated

        :CaseImportance: Critical
        """
        os = make_os()
        # New value for major
        major = int(os['major-version']) + 1
        OperatingSys.update({'id': os['id'], 'major': major})
        os = OperatingSys.info({'id': os['id']})
        assert int(os['major-version']) == major

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, new_name):
        """Negative update of system name

        :id: 4b18ff6d-7728-4245-a1ce-38e62c05f454

        :parametrized: yes

        :expectedresults: Operating System name is not updated

        :CaseImportance: Critical
        """
        os = make_os({'name': gen_alphanumeric()})
        with pytest.raises(CLIReturnCodeError):
            OperatingSys.update({'id': os['id'], 'name': new_name})
        result = OperatingSys.info({'id': os['id']})
        assert result['name'] == os['name']

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_delete_by_id(self, name):
        """Successfully deletes Operating System by its ID

        :id: a67a7b01-081b-42f8-a9ab-1f41166d649e

        :parametrized: yes

        :expectedresults: Operating System is deleted

        :CaseImportance: Critical
        """
        os = make_os({'name': name})
        OperatingSys.delete({'id': os['id']})
        with pytest.raises(CLIReturnCodeError):
            OperatingSys.info({'id': os['id']})

    @pytest.mark.tier1
    @pytest.mark.parametrize('test_data', **parametrized(negative_delete_data()))
    def test_negative_delete_by_id(self, test_data):
        """Delete Operating System using invalid data

        :id: d29a9c95-1fe3-4a7a-9f7b-127be065856d

        :parametrized: yes

        :expectedresults: Operating System is not deleted

        :CaseImportance: Critical
        """
        os = make_os()
        # The delete method requires the ID which we will not pass
        with pytest.raises(CLIReturnCodeError):
            OperatingSys.delete(test_data)
        # Now make sure that it still exists
        result = OperatingSys.info({'id': os['id']})
        assert os['id'] == result['id']
        assert os['name'] == result['name']

    @pytest.mark.tier2
    def test_positive_add_arch(self):
        """Add Architecture to operating system

        :id: 99add22d-d936-4232-9441-beff85867040

        :expectedresults: Architecture is added to Operating System

        :CaseLevel: Integration
        """
        architecture = make_architecture()
        os = make_os()
        OperatingSys.add_architecture({'architecture-id': architecture['id'], 'id': os['id']})
        os = OperatingSys.info({'id': os['id']})
        assert len(os['architectures']) == 1
        assert architecture['name'] == os['architectures'][0]

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_add_template(self):
        """Add provisioning template to operating system

        :id: 0ea9eb88-2d27-423d-a9d3-fdd788b4e28a

        :expectedresults: Provisioning template is added to Operating System

        :CaseLevel: Integration
        """
        template = make_template()
        os = make_os()
        OperatingSys.add_provisioning_template(
            {'provisioning-template': template['name'], 'id': os['id']}
        )
        os = OperatingSys.info({'id': os['id']})
        assert len(os['templates']) == 1
        template_name = os['templates'][0]
        assert template_name.startswith(template['name'])

    @pytest.mark.tier2
    def test_positive_add_ptable(self):
        """Add partition table to operating system

        :id: beba676f-b4e4-48e1-bb0c-18ad91847566

        :expectedresults: Partition table is added to Operating System

        :CaseLevel: Integration
        """
        # Create a partition table.
        ptable_name = make_partition_table()['name']
        # Create an operating system.
        os_id = make_os()['id']
        # Add the partition table to the operating system.
        OperatingSys.add_ptable({'id': os_id, 'partition-table': ptable_name})
        # Verify that the operating system has a partition table.
        os = OperatingSys.info({'id': os_id})
        assert len(os['partition-tables']) == 1
        assert os['partition-tables'][0] == ptable_name

    @pytest.mark.tier2
    def test_positive_update_parameters_attributes(self):
        """Update os-parameters-attributes to operating system

        :id: 5d566eea-b323-4128-9356-3bf39943e4d4

        :BZ: 1713553

        :expectedresults: Os-parameters-attributes are updated to Operating System
        """
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        os_id = make_os()['id']
        OperatingSys.update(
            {
                'id': os_id,
                'os-parameters-attributes': 'name={}, value={}'.format(
                    param_name + '\\', param_value
                ),
            }
        )
        os = OperatingSys.info({'id': os_id}, output_format='json')
        assert param_name == os['parameters'][0]['name']
        assert param_value == os['parameters'][0]['value']


@pytest.mark.tier2
@pytest.mark.skip_if_open("BZ:1649011")
def test_positive_os_list_with_default_organization_set(satellite_host):
    """list operating systems when the default organization is set

    :id: 2c1ba416-a5d5-4031-b154-54794569a85b

    :BZ: 1649011

    :expectedresults: os list should list operating systems when the
        default organization is set
    """
    satellite_host.api.OperatingSystem().create()
    os_list_before_default = satellite_host.cli.OperatingSys.list()
    assert len(os_list_before_default) > 0
    try:
        satellite_host.cli.Defaults.add({'param-name': 'organization', 'param-value': DEFAULT_ORG})
        result = satellite_host.execute('hammer defaults list')
        assert result.status == 0
        assert DEFAULT_ORG in ''.join(result.stdout)
        os_list_after_default = satellite_host.cli.OperatingSys.list()
        assert len(os_list_after_default) > 0

    finally:
        satellite_host.cli.Defaults.delete({'param-name': 'organization'})
        result = satellite_host.execute('hammer defaults list')
        assert result.status == 0
        assert DEFAULT_ORG not in ''.join(result.stdout)
