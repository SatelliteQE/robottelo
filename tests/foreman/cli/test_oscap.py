"""Test for oscap cli hammer plugin

:Requirement: Oscap

:CaseComponent: SCAPPlugin

:Team: Endeavour

:CaseImportance: High

:CaseAutomation: Automated

"""

from fauxfactory import gen_string
from nailgun import entities
import pytest

from robottelo.config import settings
from robottelo.constants import OSCAP_DEFAULT_CONTENT, OSCAP_PERIOD, OSCAP_WEEKDAY
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.utils.datafactory import (
    invalid_names_list,
    parametrized,
    valid_data_list,
)


class TestOpenScap:
    """Tests related to the oscap cli hammer plugin"""

    @classmethod
    def fetch_scap_and_profile_id(cls, scap_name, sat):
        """Extracts the scap ID and scap profile id

        :param scap_name: Scap title

        :returns: scap_id and scap_profile_id
        """
        default_content = sat.cli.Scapcontent.info({'title': scap_name}, output_format='json')
        scap_id = default_content['id']
        scap_profile_ids = default_content['scap-content-profiles'][0]['id']
        return scap_id, scap_profile_ids

    @pytest.mark.tier1
    def test_positive_list_default_content_with_admin(self, module_target_sat):
        """List the default scap content with admin account

        :id: 32c41c22-6aef-424e-8e69-a65c00f1c811

        :setup:

            1. Oscap should be enabled.
            2. Default content should already be populated.
            3. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to shell from admin account.
            2. Execute the scap-content command with list as sub-command.

        :expectedresults: Default scap-content are listed.

        :BZ: 1749692

        :customerscenario: true

        :CaseImportance: Medium
        """
        scap_contents = [content['title'] for content in module_target_sat.cli.Scapcontent.list()]
        assert f'Red Hat rhel{module_target_sat.os_version.major} default content' in scap_contents

    @pytest.mark.tier1
    def test_negative_list_default_content_with_viewer_role(
        self, scap_content, default_viewer_role, module_target_sat
    ):
        """List the default scap content by user with viewer role

        :id: 1e909ffc-10d9-4bcd-b4bb-c26981912bb4

        :setup:

            1. Oscap should be enabled.
            2. Default content should already be populated.
            3. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell with viewer role.
            2. Execute the scap-content command with list as sub-Command.
            3. Execute the "scap-content" command with info as sub-command.
            4. Pass valid parameters.

        :expectedresults: The scap-content and it's info is not listed.

        :CaseImportance: Medium
        """
        result = module_target_sat.cli.Scapcontent.with_user(
            default_viewer_role.login, default_viewer_role.password
        ).list()
        assert len(result) == 0
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Scapcontent.with_user(
                default_viewer_role.login, default_viewer_role.password
            ).info({'title': scap_content['title']})

    @pytest.mark.tier1
    def test_positive_view_scap_content_info_admin(self, module_target_sat):
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

        :CaseImportance: Medium
        """
        title = gen_string('alpha')
        module_target_sat.cli_factory.scapcontent(
            {'title': title, 'scap-file': settings.oscap.content_path}
        )
        result = module_target_sat.cli.Scapcontent.info({'title': title})
        assert result['title'] == title

    @pytest.mark.tier1
    def test_negative_info_scap_content(self, module_target_sat):
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

        :CaseImportance: Medium
        """
        invalid_scap_id = gen_string('alpha')
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Scapcontent.info({'id': invalid_scap_id})

    @pytest.mark.parametrize('title', **parametrized(valid_data_list()))
    @pytest.mark.tier1
    def test_positive_create_scap_content_with_valid_title(self, title, module_target_sat):
        """Create scap-content with valid title

        :id: 68e9fbe2-e3c3-48e7-a774-f1260a3b7f4f

        :parametrized: yes

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

        :CaseImportance: Medium
        """
        scap_content = module_target_sat.cli_factory.scapcontent(
            {'title': title, 'scap-file': settings.oscap.content_path}
        )
        assert scap_content['title'] == title

    @pytest.mark.tier1
    def test_negative_create_scap_content_with_same_title(self, module_target_sat):
        """Create scap-content with same title

        :id: a8cbacc9-456a-4f6f-bd0e-4d1167a8b401

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Scap data stream ".xml" file.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Pass valid parameters.
            4. Execute "scap-content" command with "create" as sub-command
               with same title

        :expectedresults: The scap-content is not created.

        :BZ: 1474172

        :CaseAutomation: Automated

        :CaseImportance: Medium
        """
        title = gen_string('alpha')
        scap_content = module_target_sat.cli_factory.scapcontent(
            {'title': title, 'scap-file': settings.oscap.content_path}
        )
        assert scap_content['title'] == title
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.scapcontent(
                {'title': title, 'scap-file': settings.oscap.content_path}
            )

    @pytest.mark.parametrize('title', **parametrized(invalid_names_list()))
    @pytest.mark.tier1
    def test_negative_create_scap_content_with_invalid_title(self, title, module_target_sat):
        """Create scap-content with invalid title

        :id: 90a2590e-a6ff-41f1-9e0a-67d4b16435c0

        :parametrized: yes

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Scap data stream ".xml" file.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Pass valid parameters and invalid title.

        :expectedresults: The scap-content is not created.

        :CaseImportance: Medium
        """
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.scapcontent(
                {'title': title, 'scap-file': settings.oscap.content_path}
            )

    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    @pytest.mark.tier1
    def test_positive_create_scap_content_with_valid_originalfile_name(
        self, name, module_target_sat
    ):
        """Create scap-content with valid original file name

        :id: 25441174-11cb-4d9b-9ec5-b1c69411b5bc

        :parametrized: yes

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Scap data stream ".xml" file.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Pass valid parameters.

        :expectedresults: The scap-content is created.

        :CaseImportance: Medium
        """
        title = gen_string('alpha')
        scap_content = module_target_sat.cli_factory.scapcontent(
            {'original-filename': name, 'scap-file': settings.oscap.content_path, 'title': title}
        )
        assert scap_content['original-filename'] == name

    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    @pytest.mark.tier1
    def test_negative_create_scap_content_with_invalid_originalfile_name(
        self,
        name,
        module_target_sat,
    ):
        """Create scap-content with invalid original file name

        :id: 83feb67a-a6bf-4a99-923d-889e8d1013fa

        :parametrized: yes

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Scap data stream ".xml" file.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Pass valid parameters and invalid title.

        :expectedresults: The scap-content is not created.

        :CaseImportance: Medium

        :BZ: 1482395
        """
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.scapcontent(
                {'original-filename': name, 'scap-file': settings.oscap.content_path}
            )

    @pytest.mark.parametrize('title', **parametrized(valid_data_list()))
    @pytest.mark.tier1
    def test_negative_create_scap_content_without_dsfile(self, title, module_target_sat):
        """Create scap-content without scap data stream xml file

        :id: ea811994-12cd-4382-9382-37fa806cc26f

        :parametrized: yes

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "scap-content" command with "create" as sub-command.
            3. Don't pass the scap-file parameter.

        :expectedresults: The scap-content is not created.

        :CaseImportance: Medium
        """
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.scapcontent({'title': title})

    @pytest.mark.tier1
    def test_positive_update_scap_content_with_newtitle(
        self,
        module_target_sat,
    ):
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

        :CaseImportance: Medium

        :BZ: 1490302
        """
        title = gen_string('alpha')
        new_title = gen_string('alpha')
        scap_content = module_target_sat.cli_factory.scapcontent(
            {'title': title, 'scap-file': settings.oscap.content_path}
        )
        assert scap_content['title'] == title
        module_target_sat.cli.Scapcontent.update({'title': title, 'new-title': new_title})
        result = module_target_sat.cli.Scapcontent.info({'title': new_title}, output_format='json')
        assert result['title'] == new_title

    @pytest.mark.tier1
    def test_positive_delete_scap_content_with_id(self, module_target_sat):
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

        :CaseImportance: Medium
        """
        title = gen_string('alpha')
        scap_content = module_target_sat.cli_factory.scapcontent(
            {'scap-file': settings.oscap.content_path, 'title': title}
        )
        module_target_sat.cli.Scapcontent.delete({'id': scap_content['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Scapcontent.info({'id': scap_content['id']})

    @pytest.mark.tier1
    def test_positive_delete_scap_content_with_title(self, module_target_sat):
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

        :CaseAutomation: Automated

        :CaseImportance: Medium
        """
        title = gen_string('alpha')
        scap_content = module_target_sat.cli_factory.scapcontent(
            {'scap-file': settings.oscap.content_path, 'title': title}
        )
        module_target_sat.cli.Scapcontent.delete({'title': scap_content['title']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Scapcontent.info({'title': scap_content['title']})

    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    @pytest.mark.tier2
    def test_postive_create_scap_policy_with_valid_name(
        self, name, scap_content, module_target_sat
    ):
        """Create scap policy with valid name

        :id: c9327675-62b2-4e22-933a-02818ef68c11

        :parametrized: yes

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters and valid name.

        :expectedresults: The policy is created successfully.

        :CaseImportance: Medium
        """
        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'name': name,
                'deploy-by': 'ansible',
                'scap-content-id': scap_content["scap_id"],
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
            }
        )
        assert scap_policy['name'] == name
        # Deleting policy which created for all valid input (ex- latin1, cjk, utf-8, etc.)
        module_target_sat.cli.Scappolicy.delete({'name': scap_policy['name']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Scappolicy.info({'name': scap_policy['name']})

    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    @pytest.mark.tier2
    def test_negative_create_scap_policy_with_invalid_name(
        self, name, scap_content, module_target_sat
    ):
        """Create scap policy with invalid name

        :id: 0d163968-7759-4cfd-9c4d-98533d8db925

        :parametrized: yes

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters and invalid name.

        :expectedresults: The policy is not created.

        :CaseImportance: Medium
        """
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.make_scap_policy(
                {
                    'name': name,
                    'deploy-by': 'ansible',
                    'scap-content-id': scap_content["scap_id"],
                    'scap-content-profile-id': scap_content["scap_profile_id"],
                    'period': OSCAP_PERIOD['weekly'].lower(),
                    'weekday': OSCAP_WEEKDAY['friday'].lower(),
                }
            )

    @pytest.mark.tier2
    def test_negative_create_scap_policy_without_content(self, scap_content, module_target_sat):
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

        :CaseImportance: Medium
        """
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.make_scap_policy(
                {
                    'deploy-by': 'ansible',
                    'scap-content-profile-id': scap_content["scap_profile_id"],
                    'period': OSCAP_PERIOD['weekly'].lower(),
                    'weekday': OSCAP_WEEKDAY['friday'].lower(),
                }
            )

    @pytest.mark.tier2
    def test_positive_associate_scap_policy_with_hostgroups(self, scap_content, module_target_sat):
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

        :CaseImportance: Medium
        """
        hostgroup = module_target_sat.cli_factory.hostgroup()
        name = gen_string('alphanumeric')
        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'name': name,
                'deploy-by': 'ansible',
                'scap-content-id': scap_content["scap_id"],
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
                'hostgroups': hostgroup['name'],
            }
        )
        assert scap_policy['hostgroups'][0] == hostgroup['name']

    @pytest.mark.tier2
    def test_positive_associate_scap_policy_with_hostgroup_via_ansible(
        self, scap_content, module_target_sat
    ):
        """Associate hostgroup to scap policy via ansible

        :id: 2df303c6-bff5-4977-a865-a3afabfb8726

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Created hostgroup
            4. Ansible role and Ansible variable

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters and deploy option as ansible
            4. Associate hostgroup with policy

        :expectedresults: The policy is created via ansible deploy option and
                          associated successfully.
        """
        hostgroup = module_target_sat.cli_factory.hostgroup()
        name = gen_string('alphanumeric')
        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'name': name,
                'deploy-by': 'ansible',
                'scap-content-id': scap_content["scap_id"],
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
                'hostgroups': hostgroup['name'],
            }
        )
        assert scap_policy['deployment-option'] == 'ansible'
        assert scap_policy['hostgroups'][0] == hostgroup['name']

    @pytest.mark.parametrize('deploy', **parametrized(['manual', 'ansible']))
    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_associate_scap_policy_with_tailoringfiles(
        self, deploy, scap_content, tailoring_file_path, module_target_sat
    ):
        """Associate tailoring file by name/id to scap policy with all deployments

        :id: d0f9b244-b92d-4889-ba6a-8973ea05bf43

        :parametrized: yes

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "create" as sub-command.
            3. Pass valid parameters.
            4. Associate tailoring file by name/id with policy

        :expectedresults: The policy is created and associated successfully.
        """
        tailoring_file_a = module_target_sat.cli_factory.tailoringfile(
            {'scap-file': tailoring_file_path['satellite']}
        )
        tailoring_file_profile_a_id = tailoring_file_a['tailoring-file-profiles'][0]['id']
        tailoring_file_b = module_target_sat.cli_factory.tailoringfile(
            {'scap-file': tailoring_file_path['satellite']}
        )
        tailoring_file_profile_b_id = tailoring_file_b['tailoring-file-profiles'][0]['id']

        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'scap-content-id': scap_content["scap_id"],
                'deploy-by': deploy,
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
                'tailoring-file': tailoring_file_a['name'],
                'tailoring-file-profile-id': tailoring_file_profile_a_id,
            }
        )
        assert scap_policy['deployment-option'] == deploy
        assert scap_policy['tailoring-file-id'] == tailoring_file_a['id']
        assert scap_policy['tailoring-file-profile-id'] == tailoring_file_profile_a_id

        module_target_sat.cli.Scappolicy.update(
            {
                'name': scap_policy['name'],
                'tailoring-file': tailoring_file_b['name'],
                'tailoring-file-profile-id': tailoring_file_profile_b_id,
            }
        )
        scap_info = module_target_sat.cli.Scappolicy.info({'name': scap_policy['name']})
        assert scap_info['tailoring-file-id'] == tailoring_file_b['id']
        assert scap_info['tailoring-file-profile-id'] == tailoring_file_profile_b_id

        module_target_sat.cli.Scappolicy.delete({'name': scap_policy['name']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Scapcontent.info({'name': scap_policy['name']})

        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'scap-content-id': scap_content["scap_id"],
                'deploy-by': deploy,
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
                'tailoring-file-id': tailoring_file_a['id'],
                'tailoring-file-profile-id': tailoring_file_profile_a_id,
            }
        )
        assert scap_policy['deployment-option'] == deploy
        assert scap_policy['tailoring-file-id'] == tailoring_file_a['id']
        assert scap_policy['tailoring-file-profile-id'] == tailoring_file_profile_a_id

        module_target_sat.cli.Scappolicy.update(
            {
                'id': scap_policy['id'],
                'tailoring-file-id': tailoring_file_b['id'],
                'tailoring-file-profile-id': tailoring_file_profile_b_id,
            }
        )
        scap_info = module_target_sat.cli.Scappolicy.info({'id': scap_policy['id']})
        assert scap_info['tailoring-file-id'] == tailoring_file_b['id']
        assert scap_info['tailoring-file-profile-id'] == tailoring_file_profile_b_id

        module_target_sat.cli.Scappolicy.delete({'id': scap_policy['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Scapcontent.info({'name': scap_policy['name']})

    @pytest.mark.parametrize('deploy', **parametrized(['manual', 'ansible']))
    @pytest.mark.upgrade
    @pytest.mark.tier2
    @pytest.mark.e2e
    def test_positive_scap_policy_end_to_end(self, deploy, scap_content, module_target_sat):
        """List all scap policies and read info using id, name

        :id: d14ab43e-c7a9-4eee-b61c-420b07ca1da9

        :parametrized: yes

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. Atleast 1 policy.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "list" as sub-command.
            3. Execute "policy" command with "info" as sub-command.
            4. Pass ID as the parameter.
            5. Pass name as the parameter.

        :expectedresults: The policies are listed successfully and information is displayed.

        :CaseImportance: Critical
        """
        hostgroup = module_target_sat.cli_factory.hostgroup()
        name = gen_string('alphanumeric')
        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'name': name,
                'deploy-by': deploy,
                'scap-content-id': scap_content["scap_id"],
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
                'hostgroups': hostgroup['name'],
            }
        )
        result = module_target_sat.cli.Scappolicy.list()
        assert name in [policy['name'] for policy in result]
        assert (
            module_target_sat.cli.Scappolicy.info({'id': scap_policy['id']})['id']
            == scap_policy['id']
        )
        assert module_target_sat.cli.Scappolicy.info({'name': scap_policy['name']})['name'] == name

        module_target_sat.cli.Scappolicy.update(
            {
                'id': scap_policy['id'],
                'period': OSCAP_PERIOD['monthly'].lower(),
                'day-of-month': 15,
            }
        )
        scap_info = module_target_sat.cli.Scappolicy.info({'name': name})
        assert scap_info['period'] == OSCAP_PERIOD['monthly'].lower()
        assert scap_info['day-of-month'] == '15'
        module_target_sat.cli.Scappolicy.delete({'id': scap_policy['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Scappolicy.info({'id': scap_policy['id']})

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_update_scap_policy_with_hostgroup(self, scap_content, module_target_sat):
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

        :CaseImportance: Medium
        """
        hostgroup = module_target_sat.cli_factory.hostgroup()
        name = gen_string('alphanumeric')
        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'name': name,
                'deploy-by': 'ansible',
                'scap-content-id': scap_content["scap_id"],
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
                'hostgroups': hostgroup['name'],
            }
        )
        assert scap_policy['hostgroups'][0] == hostgroup['name']
        assert scap_policy['deployment-option'] == 'ansible'
        new_hostgroup = module_target_sat.cli_factory.hostgroup()
        module_target_sat.cli.Scappolicy.update(
            {'id': scap_policy['id'], 'deploy-by': 'ansible', 'hostgroups': new_hostgroup['name']}
        )
        scap_info = module_target_sat.cli.Scappolicy.info({'name': name})
        assert scap_info['hostgroups'][0] == new_hostgroup['name']
        # Assert if the deployment is updated
        assert scap_info['deployment-option'] == 'ansible'

    @pytest.mark.tier2
    def test_positive_update_scap_policy_period(self, scap_content, module_target_sat):
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

        :CaseImportance: Medium
        """
        name = gen_string('alphanumeric')
        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'name': name,
                'deploy-by': 'ansible',
                'scap-content-id': scap_content["scap_id"],
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
            }
        )
        assert scap_policy['period'] == OSCAP_PERIOD['weekly'].lower()
        module_target_sat.cli.Scappolicy.update(
            {
                'id': scap_policy['id'],
                'period': OSCAP_PERIOD['monthly'].lower(),
                'day-of-month': 15,
            }
        )
        scap_info = module_target_sat.cli.Scappolicy.info({'name': name})
        assert scap_info['period'] == OSCAP_PERIOD['monthly'].lower()
        assert scap_info['day-of-month'] == '15'

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_update_scap_policy_with_content(self, scap_content, module_target_sat):
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

        :CaseImportance: Medium
        """
        name = gen_string('alphanumeric')
        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'name': name,
                'deploy-by': 'ansible',
                'scap-content-id': scap_content["scap_id"],
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
            }
        )
        assert scap_policy['scap-content-id'] == scap_content["scap_id"]
        scap_id, scap_profile_id = self.fetch_scap_and_profile_id(
            OSCAP_DEFAULT_CONTENT[f'rhel{module_target_sat.os_version.major}_content'],
            module_target_sat,
        )
        module_target_sat.cli.Scappolicy.update(
            {'name': name, 'scap-content-id': scap_id, 'scap-content-profile-id': scap_profile_id}
        )
        scap_info = module_target_sat.cli.Scappolicy.info({'name': name})
        assert scap_info['scap-content-id'] == scap_id
        assert scap_info['scap-content-profile-id'] == scap_profile_id

    @pytest.mark.tier2
    def test_positive_associate_scap_policy_with_single_server(
        self, scap_content, module_target_sat
    ):
        """Assign an audit policy to a single server

        :id: 30566c27-f466-4b4d-beaf-0a5bfda98b89

        :setup:

            1. Oscap should be enabled.
            2. Oscap-cli hammer plugin installed.
            3. At least 1 policy and host.

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "update" as sub-command.
            3. Pass host name as the parameter.

        :expectedresults: The scap policy is updated.

        :CaseImportance: Medium
        """
        host = entities.Host()
        host.create()
        name = gen_string('alpha')
        scap_policy = module_target_sat.cli_factory.make_scap_policy(
            {
                'name': name,
                'deploy-by': 'ansible',
                'scap-content-id': scap_content["scap_id"],
                'scap-content-profile-id': scap_content["scap_profile_id"],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
            }
        )
        host_name = host.name + "." + host.domain.name
        module_target_sat.cli.Scappolicy.update({'id': scap_policy['id'], 'hosts': host_name})
        hosts = module_target_sat.cli.Host.list(
            {'search': 'compliance_policy_id = {}'.format(scap_policy['id'])}
        )
        assert host_name in [host['name'] for host in hosts]

    @pytest.mark.stubbed
    @pytest.mark.tier4
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

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.upgrade
    @pytest.mark.stubbed
    @pytest.mark.tier4
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

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier4
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

        :CaseAutomation: NotAutomated
        """
