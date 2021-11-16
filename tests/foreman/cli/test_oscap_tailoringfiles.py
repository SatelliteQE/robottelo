"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_tailoringfile
from robottelo.cli.scap_tailoring_files import TailoringFiles
from robottelo.constants import SNIPPET_DATA_FILE
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.helpers import get_data_file


class TestTailoringFiles:
    """Implements Tailoring Files tests in CLI."""

    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    @pytest.mark.tier1
    def test_positive_create(self, tailoring_file_path, name):
        """Create new Tailoring Files using different values types as name

        :id: e1bb4de2-1b64-4904-bc7c-f0befa9dbd6f

        :steps:

            1. Create valid tailoring file with valid parameter

        :expectedresults: Tailoring file will be added to satellite

        :parametrized: yes
        """
        tailoring_file = make_tailoringfile(
            {'name': name, 'scap-file': tailoring_file_path['satellite']}
        )
        assert tailoring_file['name'] == name

    @pytest.mark.tier1
    def test_positive_create_with_space(self, tailoring_file_path):
        """Create tailoring files with space in name

        :id: c98ef4e7-41c5-4a8b-8a0b-8d53100b75a8

        :steps:

            1. Create valid tailoring file with space in name

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Medium
        """
        name = gen_string('alphanumeric') + ' ' + gen_string('alphanumeric')
        tailoring_file = make_tailoringfile(
            {'name': name, 'scap-file': tailoring_file_path['satellite']}
        )
        assert tailoring_file['name'] == name

    @pytest.mark.tier1
    def test_positive_get_info_of_tailoring_file(self, tailoring_file_path):
        """Get information of tailoring file

        :id: bc201194-e8c8-4385-a577-09f3455f5a4d

        :setup: tailoring file

        :steps:

            1. Create tailoring file with valid parameters
            2. Execute "tailoring-file" command with "info" as sub-command
               with valid parameter

        :expectedresults: Tailoring file information should be displayed

        :CaseImportance: Medium
        """
        name = gen_string('alphanumeric')
        make_tailoringfile({'name': name, 'scap-file': tailoring_file_path['satellite']})
        result = TailoringFiles.info({'name': name})
        assert result['name'] == name

    @pytest.mark.tier1
    def test_positive_list_tailoring_file(self, tailoring_file_path):
        """List all created tailoring files

        :id: 2ea63c4b-eebe-468d-8153-807e86d1b6a2

        :setup: tailoring file

        :steps:

            1. Create different tailoring file with different valid name
            2. Execute "tailoring-file" command with "list" as sub-command

        :expectedresults: Tailoring files list should be displayed

        :CaseImportance: Medium
        """
        name = gen_string('alphanumeric')
        make_tailoringfile({'name': name, 'scap-file': tailoring_file_path['satellite']})
        result = TailoringFiles.list()
        assert name in [tailoringfile['name'] for tailoringfile in result]

    @pytest.mark.tier1
    def test_negative_create_with_invalid_file(self, default_sat):
        """Create Tailoring files with invalid file

        :id: 86f5ce13-856c-4e58-997f-fa21093edd04

        :steps:

            1. Attempt to create tailoring file with invalid file

        :expectedresults: Tailoring file will not be added to satellite

        :CaseImportance: Medium
        """
        default_sat.put(get_data_file(SNIPPET_DATA_FILE), f'/tmp/{SNIPPET_DATA_FILE}')
        name = gen_string('alphanumeric')
        with pytest.raises(CLIFactoryError):
            make_tailoringfile({'name': name, 'scap-file': f'/tmp/{SNIPPET_DATA_FILE}'})

    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    @pytest.mark.tier1
    def test_negative_create_with_invalid_name(self, tailoring_file_path, name):
        """Create Tailoring files with invalid name

        :id: 973eee82-9735-49bb-b534-0de619aa0279

        :steps:

            1. Attempt to create tailoring file with invalid name parameter

        :expectedresults: Tailoring file will not be added to satellite

        :parametrized: yes

        :CaseImportance: Medium
        """
        with pytest.raises(CLIFactoryError):
            make_tailoringfile({'name': name, 'scap-file': tailoring_file_path['satellite']})

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_negative_associate_tailoring_file_with_different_scap(self):
        """Associate a tailoring file with different scap content

        :id: f36be738-eaa1-4f6b-aa6c-9924be5f1e96

        :steps:

            1. Execute "scap-content" command with "create" as sub-command
            2. Upload a Mutually exclusive tailoring file
            3. Associate the scap content with tailoring file

        :CaseAutomation: NotAutomated

        :expectedresults: Association should give some warning

        :CaseImportance: Medium
        """

    @pytest.mark.skip_if_open("BZ:1857572")
    @pytest.mark.tier2
    def test_positive_download_tailoring_file(self, tailoring_file_path, default_sat):

        """Download the tailoring file from satellite

        :id: 75d8c810-19a7-4285-bc3a-a1fb1a0e9088

        :steps:

            1.Create valid tailoring file with valid name
            2.Execute "tailoring-file" command with "download" as sub-command

        :expectedresults: The tailoring file should be downloaded

        BZ: 1857572

        :CaseImportance: Medium
        """
        name = gen_string('alphanumeric')
        file_path = f'/var{tailoring_file_path["satellite"]}'
        tailoring_file = make_tailoringfile(
            {'name': name, 'scap-file': tailoring_file_path['satellite']}
        )
        assert tailoring_file['name'] == name
        result = TailoringFiles.download_tailoring_file({'name': name, 'path': '/var/tmp/'})
        assert file_path in result
        result = default_sat.execute(f'find {file_path} 2> /dev/null')
        assert result.status == 0
        assert file_path == result.stdout.strip()

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_delete_tailoring_file(self, tailoring_file_path):
        """Delete tailoring file

        :id: 8bab5478-1ef1-484f-aafd-98e5cba7b1e7

        :steps:

            1. Create valid tailoring file with valid parameter
            2. Execute "tailoring-file" command with "delete" as sub-command

        :expectedresults: Tailoring file should be deleted

        :CaseImportance: Medium
        """
        tailoring_file = make_tailoringfile({'scap-file': tailoring_file_path['satellite']})
        TailoringFiles.delete({'id': tailoring_file['id']})
        with pytest.raises(CLIReturnCodeError):
            TailoringFiles.info({'id': tailoring_file['id']})

    @pytest.mark.stubbed
    @pytest.mark.tier4
    @pytest.mark.pit_server
    @pytest.mark.pit_client
    @pytest.mark.upgrade
    def test_positive_oscap_run_with_tailoring_file_and_capsule(self):
        """End-to-End Oscap run with tailoring files and default capsule

        :id: 91fd3ccd-6177-4efd-8842-73fd14f53a85

        :steps:

            1. Execute "scap-content" command with "create" as sub-command
            2. Execute "tailoring-file" command with "create" as sub-command
            3. Execute "policy" command with "create" as sub-command
            4. Associate scap content with it’s tailoring file
            5. Associate the policy with a hostgroup
            6. Provision a host using the hostgroup
            7. Puppet should configure and fetch the scap content
               and tailoring file

        :CaseAutomation: NotAutomated

        :expectedresults: ARF report should be sent to satellite reflecting
                         the changes done via tailoring files
        """

    @pytest.mark.stubbed
    @pytest.mark.tier4
    @pytest.mark.upgrade
    def test_positive_oscap_run_with_tailoring_file_and_external_capsule(self):
        """End-to-End Oscap run with tailoring files and external capsule

        :id: 39d2e690-8410-4cc7-b873-bb5f658148cc

        :steps:

            1. Execute "scap-content" command with "create" as sub-command
            2. Execute "tailoring-file" command with "create" as sub-command
            3. Execute "policy" command with "create" as sub-command
            4. Associate scap content with it’s tailoring file
            5. Associate the policy with a hostgroup
            6. Provision a host using the hostgroup
            7. Puppet should configure and fetch the scap content
               and tailoring file from external capsule

        :CaseAutomation: NotAutomated

        :expectedresults: ARF report should be sent to satellite
                         reflecting the changes done via tailoring files
        """

    @pytest.mark.stubbed
    @pytest.mark.tier4
    @pytest.mark.upgrade
    def test_positive_fetch_tailoring_file_information_from_arfreports(self):
        """Fetch Tailoring file Information from Arf-reports

        :id: d8fa1a05-db99-47a9-b1f5-12712a0b1378

        :steps:

            1. Execute "scap-content" command with "create" as sub-command
            2. Execute "tailoring-file" command with "create" as sub-command
            3. Execute "policy" command with "create" as sub-command
            4. Associate scap content with it’s tailoring file
            5. Associate the policy with a hostgroup
            6. Provision a host using the hostgroup
            7. Puppet should configure and fetch the scap content
               and send arf-report to satellite

        :CaseAutomation: NotAutomated

        :expectedresults: ARF report should have information
                          about the tailoring file used, if any

        :CaseImportance: Medium
        """
