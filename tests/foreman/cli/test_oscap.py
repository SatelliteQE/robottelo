"""Test for oscap cli hammer plugin

@Requirement: Oscap

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier2, tier4
from robottelo.test import CLITestCase


class OpenScapTestCase(CLITestCase):
    """Tests related to the oscap cli hammer plugin"""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_list_default_content_with_admin(self):
        """List the default scap content with admin account

        @id: 32c41c22-6aef-424e-8e69-a65c00f1c811

        @setup:

        1. Oscap should be enabled.
        2. Default content should already be populated.
        3. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to shell from admin account.
        2. Execute the scap-content command with list as sub-command.

        @Assert: The scap-content are listed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_list_default_content_with_viewer_role(self):
        """List the default scap content by user with viewer role

        @id: 1e909ffc-10d9-4bcd-b4bb-c26981912bb4

        @setup:

        1. Oscap should be enabled.
        2. Default content should already be populated.
        3. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to shell from user account.
        2. Execute the scap-content command with list as sub-Command.

        @Assert: The scap-content is not listed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_view_scap_content_info_admin(self):
        """View info of scap content with admin account

        @id: 539ea982-0701-43f5-bb91-e566e6687e35

        @setup:

        1. Oscap should be enabled.
        2. Default content should already be populated.
        3. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell as admin.
        2. Execute the "scap-content" command with info as sub-command.
        3. Pass valid "ID" of scap-content as argument.

        @Assert: The info of the scap-content is listed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_info_scap_content_viewer_role(self):
        """View info of scap content with viewer role

        @id: 15eb035b-d301-4dbd-b66a-c4621d2003a3

        @setup:

        1. Oscap should be enabled.
        2. Default content should already be populated.
        3. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell with user with viewer role.
        2. Execute the "scap-content" command with info as sub-command.
        3. Pass valid parameters.

        @Assert: The info of the scap-content is not listed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_info_scap_content(self):
        """View info of scap content with invalid ID as parameter

        @id: 86f44fb1-2e2b-4004-83c1-4a62162ebea9

        @setup:

        1. Oscap should be enabled.
        2. Default content should already be populated.
        3. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell as admin.
        2. Execute the "scap-content" command with info as sub-command.
        3. Pass invalid "ID" of scap-content as argument.

        @Assert: The info of the scap-content is not listed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_scap_content_with_valid_title(self):
        """Create scap-content with valid title

        @id: 68e9fbe2-e3c3-48e7-a774-f1260a3b7f4f

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Scap data stream ".xml" file.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "create" as sub-command.
        3. Pass valid parameters.

        @Assert: The scap-content is created successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_scap_content_with_invalid_title(self):
        """Create scap-content with invalid title

        @id: 90a2590e-a6ff-41f1-9e0a-67d4b16435c0

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Scap data stream ".xml" file.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "create" as sub-command.
        3. Pass valid parameters and invalid title.

        @Assert: The scap-content is not created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_scap_content_with_valid_originalfile_name(self):
        """Create scap-content with valid original file name

        @id: 25441174-11cb-4d9b-9ec5-b1c69411b5bc

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Scap data stream ".xml" file.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "create" as sub-command.
        3. Pass valid parameters.

        @Assert: The scap-content is not created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_scap_content_with_invalid_originalfile_name(self):
        """Create scap-content with invalid original file name

        @id: 83feb67a-a6bf-4a99-923d-889e8d1013fa

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Scap data stream ".xml" file.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "create" as sub-command.
        3. Pass valid parameters and invalid title.

        @Assert: The scap-content is not created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_scap_content_with_dsfile(self):
        """Create scap-content with scap data stream xml file

        @id: 62f1a663-fe0f-4d02-9329-59fa044e2674

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. vaild Scap data stream ".xml" file.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "create" as sub-command.
        3. Pass valid parameters and valid scap ds file.

        @Assert: The scap-content is created successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_scap_content_without_dsfile(self):
        """Create scap-content without scap data stream xml file

        @id: ea811994-12cd-4382-9382-37fa806cc26f

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "create" as sub-command.
        3. Don't pass the scap-file parameter.

        @Assert: The scap-content is not created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_scap_content_with_newtitle(self):
        """Update scap content title

        @id: 2c32e94a-237d-40b9-8a3b-fca2ef26fe79

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "update" as sub-command.
        3. Pass valid parameters and newtitle parameter.

        @Assert: The scap-content is updated successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_scap_content_with_id(self):
        """Delete a scap content with id as parameter

        @id: 11ae7652-65e0-4751-b1e0-246b27919238

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "delete" as sub-command.
        3. Pass ID as parameter.

        @Assert: The scap-content is deleted successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_scap_content_with_name(self):
        """Delete a scap content with name as parameter

        @id: aa4ca830-3250-4517-b40c-0256cdda5e0a

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell.
        2. Execute "scap-content" command with "delete" as sub-command.
        3. Pass name as parameter.

        @Assert: The scap-content is deleted successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_postive_create_scap_policy_with_valid_name(self):
        """Create scap policy with valid name

        @id: c9327675-62b2-4e22-933a-02818ef68c11

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "create" as sub-command.
        3. Pass valid parameters and valid name.

        @Assert: The policy is created successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_create_scap_policy_with_invalid_name(self):
        """Create scap policy with invalid name

        @id: 0d163968-7759-4cfd-9c4d-98533d8db925

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "create" as sub-command.
        3. Pass valid parameters and invalid name.

        @Assert: The policy is not created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_create_scap_policy_without_content(self):
        """Create scap policy without scap content

        @id: 88a8fba3-f45a-4e22-9ee1-f0d701f1135f

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "create" as sub-command.
        3. Pass valid parameters without passing the scap-content-id.

        @Assert: The policy is not created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_associate_scap_policy_with_hostgroups(self):
        """Associate hostgroups to scap policy

        @id: 916403a0-572d-4cf3-9155-3e3d0373577f

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. More than 1 hostgroups

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "create" as sub-command.
        3. Pass valid parameters.
        4. Associate multiple hostgroups with policy

        @Assert: The policy is created and associated successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_scap_policy_without_hostgroups(self):
        """Create scap policy without hostgroups

        @id: de705ba8-a946-4835-a79c-5da9510d591a

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. More than 1 hostgroups.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "create" as sub-command.
        3. Pass valid parameters.
        4. Associate multiple hostgroups with policy.

        @Assert: The policy is created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_list_scap_policy(self):
        """List all scap policies

        @id: d14ab43e-c7a9-4eee-b61c-420b07ca1da9

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "list" as sub-command.

        @Assert: The policies are listed successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_info_scap_policy_with_id(self):
        """View info of policy with id as parameter

        @id: d309000b-777e-4cfb-bf6c-7f02ab130b9d

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "info" as sub-command.
        3. Pass ID as the parameter.

        @Assert: The information is displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_info_scap_policy_with_name(self):
        """View info of policy with name as parameter

        @id: eece98b2-3e6a-4ac0-b742-913482343e9d

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "info" as sub-command.
        3. Pass name as the parameter.

        @Assert: The information is displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_scap_policy_with_hostgroup(self):
        """Update scap policy by addition of hostgroup

        @id: 21b9b82b-7c6c-4944-bc2f-67631e1d4086

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy and hostgroup.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "update" as sub-command.
        3. Pass hostgoups as the parameter.

        @Assert: The scap policy is updated.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_scap_policy_period(self):
        """Update scap policy by updating the period strategy
        from monthly to weekly

        @id: 4892bc3c-d886-49b4-a5b1-250d96b7e278

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "update" as sub-command.
        3. Pass period as parameter and weekday as parameter.

        @Assert: The scap policy is updated.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_scap_policy_with_content(self):
        """Update the scap policy by updating the scap content
        associated with the policy

        @id: 3c9df098-9ff8-4f48-a9a0-2ba21a8e48e0

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "update" as sub-command.
        3. Pass scap-content-id as parameter.

        @Assert: The scap policy is updated.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_delete_scap_policy_with_id(self):
        """Delete the scap policy with id as parameter

        @id: db9d925f-c730-4299-ad8e-5aaa08895f6e

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "delete" as sub-command.
        3. Pass id as parameter.

        @Assert: The scap policy is deleted successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_delete_scap_policy_with_name(self):
        """Delete the scap policy with name as parameter

        @id: 6c167e7b-cbdd-4059-808c-04c686ba9fe8

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "delete" as sub-command.
        3. Pass name as parameter.

        @Assert: The scap policy is deleted successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_list_arf_reports(self):
        """List all arf-reports

        @id: f364ea3c-ba74-4848-be39-df33f80fcd21

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.
        4. A provisioned host with scap enabled.
        5. Reports from the host send to satellite.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "list" as sub-command.

        @Assert: The arf-reports are listed successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_info_arf_report(self):
        """View information of arf-report

        @id: 5ac866f9-fc23-48a1-9766-a8a5f52cfd63

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.
        4. A provisioned host with scap enabled
        5. Reports from the host send to satellite

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "info" as sub-command.
        3. Pass id as parameter.

        @Assert: The information of arf-report is listed successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_delete_arf_report(self):
        """Delete an arf-report

        @id: 85b6d483-eb83-4af5-96d6-3cd74d2c007c

        @setup:

        1. Oscap should be enabled.
        2. Oscap-cli hammer plugin installed.
        3. Atleast 1 policy.
        4. A provisioned host with scap enabled.
        5. Reports from the host send to satellite.

        @steps:

        1. Login to hammer shell.
        2. Execute "policy" command with "delete" as sub-command.
        3. Pass id as parameter.

        @Assert: Arf-report is deleted successfully.

        @caseautomation: notautomated
        """
