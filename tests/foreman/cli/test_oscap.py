"""Test for oscap cli hammer plugin

:Requirement: Oscap

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_scapcontent, make_user
from robottelo.cli.role import Role
from robottelo.cli.scapcontent import Scapcontent
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import OSCAP_DEFAULT_CONTENT
from robottelo.datafactory import (
    valid_data_list,
    invalid_names_list,
)
from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier2,
    tier4,
    upgrade,
    skip_if_bug_open,
)
from robottelo.test import CLITestCase


class OpenScapTestCase(CLITestCase):
    """Tests related to the oscap cli hammer plugin"""

    @classmethod
    def create_test_user_viewer_role(cls):
        """Create's a user with Viewer role"""
        cls.login = gen_string('alpha')
        cls.password = gen_string('alpha')
        user = make_user({
            'login': cls.login,
            'password': cls.password,
            'admin': False
        })
        role = Role.info({'name': 'Viewer'})
        User.add_role({
            'login': user['login'],
            'role-id': role['id'],
        })
        return cls.login, cls.password

    @classmethod
    def setUpClass(cls):
        super(OpenScapTestCase, cls).setUpClass()
        file_name = settings.oscap.content_path
        cls.file_name = file_name.split('/')[
                     (file_name.split('/')).__len__() - 1]
        ssh.upload_file(local_file=settings.oscap.content_path,
                        remote_file="/tmp/{0}".format(cls.file_name))

    @run_only_on('sat')
    @tier1
    def test_positive_list_default_content_with_admin(self):
        """List the default scap content with admin account

        :id: 32c41c22-6aef-424e-8e69-a65c00f1c811

        :setup:

            1. Oscap should be enabled.
            2. Default content should already be populated.
            3. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to shell from admin account.
            2. Execute the scap-content command with list as sub-command.

        :expectedresults: The scap-content are listed.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        result = Scapcontent.list()
        self.assertIn(
            OSCAP_DEFAULT_CONTENT['rhel7_content'],
            [str(scap['title']) for scap in result]
        )

    @run_only_on('sat')
    @tier1
    def test_negative_list_default_content_with_viewer_role(self):
        """List the default scap content by user with viewer role

        :id: 1e909ffc-10d9-4bcd-b4bb-c26981912bb4

        :setup:

            1. Oscap should be enabled.
            2. Default content should already be populated.
            3. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to shell from user account.
            2. Execute the scap-content command with list as sub-Command.

        :expectedresults: The scap-content is not listed.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        login, password = self.create_test_user_viewer_role()
        result = Scapcontent.with_user(login, password).list()
        self.assertEqual(len(result), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_view_scap_content_info_admin(self):
        """View info of scap content with admin account

        :id: 539ea982-0701-43f5-bb91-e566e6687e35

        :setup:

            1. Oscap should be enabled.
            2. Default content should already be populated.
            3. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell as admin.
            2. Execute the "scap-content" command with info as sub-command.
            3. Pass valid "ID" of scap-content as argument.

        :expectedresults: The info of the scap-content is listed.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        title = gen_string('alpha')
        make_scapcontent({
            'title': title,
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        result = Scapcontent.info({'title': title})
        self.assertEqual(result['title'], title)

    @run_only_on('sat')
    @tier1
    def test_negative_info_scap_content_viewer_role(self):
        """View info of scap content with viewer role

        :id: 15eb035b-d301-4dbd-b66a-c4621d2003a3

        :setup:

            1. Oscap should be enabled.
            2. Default content should already be populated.
            3. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell with user with viewer role.
            2. Execute the "scap-content" command with info as sub-command.
            3. Pass valid parameters.

        :expectedresults: The info of the scap-content is not listed.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        title = gen_string('alpha')
        make_scapcontent({
            'title': title,
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        login, password = self.create_test_user_viewer_role()
        with self.assertRaises(CLIReturnCodeError):
            Scapcontent.with_user(login, password).info({'title': title})

    @run_only_on('sat')
    @tier1
    def test_negative_info_scap_content(self):
        """View info of scap content with invalid ID as parameter

        :id: 86f44fb1-2e2b-4004-83c1-4a62162ebea9

        :setup:

            1. Oscap should be enabled.
            2. Default content should already be populated.
            3. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell as admin.
            2. Execute the "scap-content" command with info as sub-command.
            3. Pass invalid "ID" of scap-content as argument.

        :expectedresults: The info of the scap-content is not listed.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        scap_id = gen_string('alphanumeric')
        with self.assertRaises(CLIReturnCodeError):
            Scapcontent.info({'id': scap_id})

    @run_only_on('sat')
    @tier1
    def test_positive_create_scap_content_with_valid_title(self):
        """Create scap-content with valid title

        :id: 68e9fbe2-e3c3-48e7-a774-f1260a3b7f4f

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Scap data stream ".xml" file.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Pass valid parameters.

        :expectedresults: The scap-content is created successfully.

        :BZ: 1471801

        :caseautomation: automated

        :CaseImportance: Critical
        """
        for title in valid_data_list():
            with self.subTest(title):
                scap_content = make_scapcontent({
                    'title': title,
                    'scap-file': '/tmp/{0}'.format(self.file_name)})
                self.assertEqual(scap_content['title'], title)

    @run_only_on('sat')
    @tier1
    def test_negative_create_scap_content_with_invalid_title(self):
        """Create scap-content with invalid title

        :id: 90a2590e-a6ff-41f1-9e0a-67d4b16435c0

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Scap data stream ".xml" file.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Pass valid parameters and invalid title.

        :expectedresults: The scap-content is not created.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        for title in invalid_names_list():
            with self.subTest(title):
                with self.assertRaises(CLIFactoryError):
                    make_scapcontent({
                        'title': title,
                        'scap-file': '/tmp/{0}'.format(self.file_name)})

    @run_only_on('sat')
    @tier1
    def test_positive_create_scap_content_with_valid_originalfile_name(self):
        """Create scap-content with valid original file name

        :id: 25441174-11cb-4d9b-9ec5-b1c69411b5bc

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Scap data stream ".xml" file.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Pass valid parameters.

        :expectedresults: The scap-content is created.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                scap_content = make_scapcontent({
                    'original-filename': name,
                    'scap-file': '/tmp/{0}'.format(self.file_name)})
                self.assertEqual(scap_content['original-filename'], name)

    @skip_if_bug_open('bugzilla', 1482395)
    @run_only_on('sat')
    @tier1
    def test_negative_create_scap_content_with_invalid_originalfile_name(self):
        """Create scap-content with invalid original file name

        :id: 83feb67a-a6bf-4a99-923d-889e8d1013fa

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Scap data stream ".xml" file.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Pass valid parameters and invalid title.

        :expectedresults: The scap-content is not created.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_scapcontent({
                        'original-filename': name,
                        'scap-file': '/tmp/{0}'.format(self.file_name)})

    @run_only_on('sat')
    @tier1
    def test_negative_create_scap_content_without_dsfile(self):
        """Create scap-content without scap data stream xml file

        :id: ea811994-12cd-4382-9382-37fa806cc26f

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Don't pass the scap-file parameter.

        :expectedresults: The scap-content is not created.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        for title in valid_data_list():
            with self.subTest(title):
                with self.assertRaises(CLIFactoryError):
                    make_scapcontent({'title': title})

    @skip_if_bug_open('bugzilla', 1490302)
    @run_only_on('sat')
    @tier1
    def test_positive_update_scap_content_with_newtitle(self):
        """Update scap content title

        :id: 2c32e94a-237d-40b9-8a3b-fca2ef26fe79

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "update" as sub-command.
            3. Pass valid parameters and newtitle parameter.

        :expectedresults: The scap-content is updated successfully.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        title = gen_string('alpha')
        new_title = gen_string('alpha')
        scap_content = make_scapcontent({
            'title': title,
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        self.assertEqual(scap_content['title'], title)
        Scapcontent.update({
            'title': title,
            'new-title': new_title})
        self.assertEqual(scap_content['title'], new_title)

    @run_only_on('sat')
    @tier1
    def test_positive_delete_scap_content_with_id(self):
        """Delete a scap content with id as parameter

        :id: 11ae7652-65e0-4751-b1e0-246b27919238

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "delete" as sub-command.
            3. Pass ID as parameter.

        :expectedresults: The scap-content is deleted successfully.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        scap_content = make_scapcontent({
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        Scapcontent.delete({'id': scap_content['id']})
        with self.assertRaises(CLIReturnCodeError):
            Scapcontent.info({'id': scap_content['id']})

    @run_only_on('sat')
    @tier1
    def test_positive_delete_scap_content_with_title(self):
        """Delete a scap content with title as parameter

        :id: aa4ca830-3250-4517-b40c-0256cdda5e0a

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "delete" as sub-command.
            3. Pass name as parameter.

        :expectedresults: The scap-content is deleted successfully.

        :caseautomation: automated

        :CaseImportance: Critical
        """
        scap_content = make_scapcontent({
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        Scapcontent.delete({'title': scap_content['title']})
        with self.assertRaises(CLIReturnCodeError):
            Scapcontent.info({'title': scap_content['title']})

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_postive_create_scap_policy_with_valid_name(self):
        """Create scap policy with valid name

        :id: c9327675-62b2-4e22-933a-02818ef68c11

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters and valid name.

        :expectedresults: The policy is created successfully.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_create_scap_policy_with_invalid_name(self):
        """Create scap policy with invalid name

        :id: 0d163968-7759-4cfd-9c4d-98533d8db925

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters and invalid name.

        :expectedresults: The policy is not created.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_create_scap_policy_without_content(self):
        """Create scap policy without scap content

        :id: 88a8fba3-f45a-4e22-9ee1-f0d701f1135f

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters without passing the scap-content-id.

        :expectedresults: The policy is not created.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_associate_scap_policy_with_hostgroups(self):
        """Associate hostgroups to scap policy

        :id: 916403a0-572d-4cf3-9155-3e3d0373577f

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. More than 1 hostgroups

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters.
            4. Associate multiple hostgroups with policy

        :expectedresults: The policy is created and associated successfully.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_associate_scap_policy_with_tailoringfiles_id(self):
        """Associate tailoring file by id to scap policy

        :id: 4d60333d-ffd7-4c6c-9ba5-6a311ccf2910

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters.
            4. Associate tailoring file by "tailoring-file-id" with policy

        :expectedresults: The policy is created and associated successfully.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_associate_scap_policy_with_tailoringfiles_name(self):
        """Associate tailoring file by name to scap policy

        :id: d0f9b244-b92d-4889-ba6a-8973ea05bf43

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters.
            4. Associate tailoring file by "tailoring-file" with policy

        :expectedresults: The policy is created and associated successfully.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_scap_policy_without_hostgroups(self):
        """Create scap policy without hostgroups

        :id: de705ba8-a946-4835-a79c-5da9510d591a

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. More than 1 hostgroups.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters.
            4. Associate multiple hostgroups with policy.

        :expectedresults: The policy is created.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_list_scap_policy(self):
        """List all scap policies

        :id: d14ab43e-c7a9-4eee-b61c-420b07ca1da9

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "list" as sub-command.

        :expectedresults: The policies are listed successfully.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_info_scap_policy_with_id(self):
        """View info of policy with id as parameter

        :id: d309000b-777e-4cfb-bf6c-7f02ab130b9d

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "info" as sub-command.
            3. Pass ID as the parameter.

        :expectedresults: The information is displayed.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_info_scap_policy_with_name(self):
        """View info of policy with name as parameter

        :id: eece98b2-3e6a-4ac0-b742-913482343e9d

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "info" as sub-command.
            3. Pass name as the parameter.

        :expectedresults: The information is displayed.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_scap_policy_with_hostgroup(self):
        """Update scap policy by addition of hostgroup

        :id: 21b9b82b-7c6c-4944-bc2f-67631e1d4086

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy and hostgroup.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "update" as sub-command.
            3. Pass hostgoups as the parameter.

        :expectedresults: The scap policy is updated.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_scap_policy_period(self):
        """Update scap policy by updating the period strategy
        from monthly to weekly

        :id: 4892bc3c-d886-49b4-a5b1-250d96b7e278

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "update" as sub-command.
            3. Pass period as parameter and weekday as parameter.

        :expectedresults: The scap policy is updated.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_scap_policy_with_content(self):
        """Update the scap policy by updating the scap content
        associated with the policy

        :id: 3c9df098-9ff8-4f48-a9a0-2ba21a8e48e0

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "update" as sub-command.
            3. Pass scap-content-id as parameter.

        :expectedresults: The scap policy is updated.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_scap_policy_with_tailoringfiles_id(self):
        """Update the scap policy by updating the scap tailoring file id
        associated with the policy

        :id: 91a25e0b-d5d2-49d8-a3cd-1f3836ac323c

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "update" as sub-command.
            3. Pass tailoring-file-id as parameter.

        :expectedresults: The scap policy is updated.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_scap_policy_with_tailoringfiles_name(self):
        """Update the scap policy by updating the scap tailoring file name
        associated with the policy

        :id: a2403170-51df-4561-9a58-820f77a5e048

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "update" as sub-command.
            3. Pass tailoring-file as parameter.

        :expectedresults: The scap policy is updated.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_delete_scap_policy_with_id(self):
        """Delete the scap policy with id as parameter

        :id: db9d925f-c730-4299-ad8e-5aaa08895f6e

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "delete" as sub-command.
            3. Pass id as parameter.

        :expectedresults: The scap policy is deleted successfully.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_delete_scap_policy_with_name(self):
        """Delete the scap policy with name as parameter

        :id: 6c167e7b-cbdd-4059-808c-04c686ba9fe8

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "delete" as sub-command.
            3. Pass name as parameter.

        :expectedresults: The scap policy is deleted successfully.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_list_arf_reports(self):
        """List all arf-reports

        :id: f364ea3c-ba74-4848-be39-df33f80fcd21

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.
            4. A provisioned host with scap enabled.
            5. Reports from the host send to satellite.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "list" as sub-command.

        :expectedresults: The arf-reports are listed successfully.

        :caseautomation: notautomated
        """

    @upgrade
    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_info_arf_report(self):
        """View information of arf-report

        :id: 5ac866f9-fc23-48a1-9766-a8a5f52cfd63

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.
            4. A provisioned host with scap enabled
            5. Reports from the host send to satellite

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "info" as sub-command.
            3. Pass id as parameter.

        :expectedresults: The information of arf-report is listed successfully.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_delete_arf_report(self):
        """Delete an arf-report

        :id: 85b6d483-eb83-4af5-96d6-3cd74d2c007c

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.
            4. A provisioned host with scap enabled.
            5. Reports from the host send to satellite.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "delete" as sub-command.
            3. Pass id as parameter.

        :expectedresults: Arf-report is deleted successfully.

        :caseautomation: notautomated
        """
