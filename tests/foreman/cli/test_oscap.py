"""Test for oscap cli hammer plugin

:Requirement: Oscap

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import os

import json

import requests

from fauxfactory import gen_string

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_host,
    make_hostgroup,
    make_scapcontent,
    make_scap_policy,
    make_tailoringfile,
    make_user
)
from robottelo.cli.host import Host
from robottelo.cli.role import Role
from robottelo.cli.scap_policy import Scappolicy
from robottelo.cli.scapcontent import Scapcontent
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import (
    OSCAP_DEFAULT_CONTENT,
    OSCAP_PROFILE,
    OSCAP_PERIOD,
    OSCAP_WEEKDAY
)
from robottelo.datafactory import (
    valid_data_list,
    invalid_names_list
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    tier4,
    upgrade
)
from robottelo.datafactory import (
    valid_hosts_list,
)
from robottelo.test import CLITestCase
from nailgun import entities
from nailgun import client
from robottelo.cli.proxy import Proxy


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
    def fetch_scap_and_profile_id(cls, scap_name, scap_profile):
        """Extracts the scap ID and scap profile id

        :param scap_name: Scap title
        :param scap_profile: Scap profile you want to select

        :returns: scap_id and scap_profile_id
        """
        default_content = Scapcontent.info({'title': scap_name},
                                           output_format='json'
                                           )
        scap_id = default_content['id']
        scap_profile_ids = [
            profile['id']
            for profile in default_content['scap-content-profiles']
            if scap_profile in profile['title']
        ]
        return scap_id, scap_profile_ids

    @classmethod
    def setUpClass(cls):
        super(OpenScapTestCase, cls).setUpClass()
        _, cls.file_name = os.path.split(settings.oscap.content_path)
        # uploads the scap content to satellite
        ssh.upload_file(
            local_file=settings.oscap.content_path,
            remote_file="/tmp/{0}".format(cls.file_name)
        )
        cls.title = 'rhel-6-content'
        result = [scap['title'] for scap in Scapcontent.list() if
                  scap.get('title') in cls.title]
        if not result:
            make_scapcontent({
                'title': cls.title,
                'scap-file': '/tmp/{0}'.format(cls.file_name)
            })
        cls.scap_id_rhel6, cls.scap_profile_id_rhel6 = (
            cls.fetch_scap_and_profile_id(
                cls.title,
                OSCAP_PROFILE['common']
            )
        )

    def setUp(self):
        """Find an existing puppet proxy.

        Record information about this puppet proxy as ``self.puppet_proxy``.
        """
        super(OpenScapTestCase, self).setUp()
        # Use the default installation smart proxy
        self.puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]

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

        :CaseImportance: Critical
        """
        result = Scapcontent.list()
        self.assertIn(
            OSCAP_DEFAULT_CONTENT['rhel7_content'],
            [scap['title'] for scap in result]
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

        :CaseImportance: Critical
        """
        invalid_scap_id = gen_string('alpha')
        with self.assertRaises(CLIReturnCodeError):
            Scapcontent.info({'id': invalid_scap_id})

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

        :CaseImportance: Critical
        """
        for title in valid_data_list():
            with self.subTest(title):
                scap_content = make_scapcontent({
                    'title': title,
                    'scap-file': '/tmp/{0}'.format(self.file_name)})
                self.assertEqual(scap_content['title'], title)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1474172)
    @tier1
    def test_negative_create_scap_content_with_same_title(self):
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

        :caseautomation: automated

        :CaseImportance: Critical
        """
        title = gen_string('alpha')
        scap_content = make_scapcontent({
            'title': title,
            'scap-file': '/tmp/{0}'.format(self.file_name)
        })
        self.assertEqual(scap_content['title'], title)
        with self.assertRaises(CLIFactoryError):
            make_scapcontent({
                'title': title,
                'scap-file': '/tmp/{0}'.format(self.file_name)
            })

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

        :CaseImportance: Critical
        """
        title = gen_string('alpha')
        new_title = gen_string('alpha')
        scap_content = make_scapcontent({
            'title': title,
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        self.assertEqual(scap_content['title'], title)
        result = Scapcontent.update({
            'title': title,
            'new-title': new_title})
        if bz_bug_is_open(1496810):
            result = Scapcontent.info({'title': new_title})
        self.assertEqual(result['title'], new_title)

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
        """
        for name in valid_data_list():
            with self.subTest(name):
                scap_policy = make_scap_policy({
                    'name': name,
                    'scap-content-id': self.scap_id_rhel6,
                    'scap-content-profile-id': self.scap_profile_id_rhel6,
                    'period': OSCAP_PERIOD['weekly'].lower(),
                    'weekday': OSCAP_WEEKDAY['friday'].lower()
                })
                self.assertEqual(scap_policy['name'], name)

    @run_only_on('sat')
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
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_scap_policy({
                        'name': name,
                        'scap-content-id': self.scap_id_rhel6,
                        'scap-content-profile-id': self.scap_profile_id_rhel6,
                        'period': OSCAP_PERIOD['weekly'].lower(),
                        'weekday': OSCAP_WEEKDAY['friday'].lower()
                    })

    @run_only_on('sat')
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
        """
        with self.assertRaises(CLIFactoryError):
            make_scap_policy({
                'scap-content-profile-id': self.scap_profile_id_rhel6,
                'period': OSCAP_PERIOD['weekly'].lower(),
                'weekday': OSCAP_WEEKDAY['friday'].lower()
            })

    @run_only_on('sat')
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
        """
        hostgroup = make_hostgroup()
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'hostgroups': hostgroup['name']
        })
        self.assertEqual(scap_policy['hostgroups'][0], hostgroup['name'])

    @run_only_on('sat')
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
        """
        _, file_name = os.path.split(settings.oscap.tailoring_path)
        ssh.upload_file(
            local_file=settings.oscap.tailoring_path,
            remote_file="/tmp/{0}".format(file_name)
        )
        tailoring_file = make_tailoringfile({
            'scap-file': '/tmp/{0}'.format(file_name)
        })
        tailor_profile_id = tailoring_file['tailoring-file-profiles'][0]['id']
        scap_policy = make_scap_policy({
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'tailoring-file-id': tailoring_file['id'],
            'tailoring-file-profile-id': tailor_profile_id
        })
        self.assertEqual(scap_policy['tailoring-file-id'],
                         tailoring_file['id'])
        self.assertEqual(scap_policy['tailoring-file-profile-id'],
                         tailor_profile_id)

    @run_only_on('sat')
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
        """
        _, file_name = os.path.split(settings.oscap.tailoring_path)
        ssh.upload_file(
            local_file=settings.oscap.tailoring_path,
            remote_file="/tmp/{0}".format(file_name)
        )
        tailoring_file = make_tailoringfile({
            'scap-file': '/tmp/{0}'.format(file_name)
        })
        tailor_profile_id = tailoring_file['tailoring-file-profiles'][0]['id']
        scap_policy = make_scap_policy({
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'tailoring-file': tailoring_file['name'],
            'tailoring-file-profile-id': tailor_profile_id
        })
        self.assertEqual(scap_policy['tailoring-file-id'],
                         tailoring_file['id'])
        self.assertEqual(scap_policy['tailoring-file-profile-id'],
                         tailor_profile_id)

    @run_only_on('sat')
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
        """
        name = gen_string('alphanumeric')
        make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower()
        })
        result = Scappolicy.list()
        self.assertIn(name,
                      [policy['name'] for policy in result]
                      )

    @run_only_on('sat')
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
        """
        scap_policy = make_scap_policy({
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower()
        })
        result = Scappolicy.info({'id': scap_policy['id']})
        self.assertEqual(result['id'], scap_policy['id'])

    @run_only_on('sat')
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
        """
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower()
        })
        result = Scappolicy.info({'name': scap_policy['name']})
        self.assertEqual(result['name'], name)

    @run_only_on('sat')
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
        """
        hostgroup = make_hostgroup()
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'hostgroups': hostgroup['name']
        })
        self.assertEqual(scap_policy['hostgroups'][0], hostgroup['name'])
        new_hostgroup = make_hostgroup()
        Scappolicy.update({
            'id': scap_policy['id'],
            'hostgroups': new_hostgroup['name']
        })
        scap_info = Scappolicy.info({'name': name})
        self.assertEqual(scap_info['hostgroups'][0], new_hostgroup['name'])

    @run_only_on('sat')
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
        """
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
        })
        self.assertEqual(scap_policy['period'], OSCAP_PERIOD['weekly'].lower())
        Scappolicy.update({
            'id': scap_policy['id'],
            'period': OSCAP_PERIOD['monthly'].lower(),
            'day-of-month': 15
        })
        scap_info = Scappolicy.info({'name': name})
        self.assertEqual(scap_info['period'], OSCAP_PERIOD['monthly'].lower())
        self.assertEqual(scap_info['day-of-month'], '15')

    @run_only_on('sat')
    @tier2
    @upgrade
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
        """
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
        })
        self.assertEqual(scap_policy['scap-content-id'], self.scap_id_rhel6)
        scap_id, scap_profile_id = self.fetch_scap_and_profile_id(
            OSCAP_DEFAULT_CONTENT['rhel_firefox'],
            OSCAP_PROFILE['firefox']
        )

        Scappolicy.update({
            'name': name,
            'scap-content-id': scap_id,
            'scap-content-profile-id': scap_profile_id,
        })
        scap_info = Scappolicy.info({'name': name})
        self.assertEqual(scap_info['scap-content-id'], scap_id)
        self.assertEqual(scap_info['scap-content-profile-id'],
                         scap_profile_id[0])

    @run_only_on('sat')
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
        """
        _, file_name = os.path.split(settings.oscap.tailoring_path)
        ssh.upload_file(
            local_file=settings.oscap.tailoring_path,
            remote_file="/tmp/{0}".format(file_name)
        )
        tailoring_file = make_tailoringfile({
            'scap-file': '/tmp/{0}'.format(file_name)
        })
        tailor_profile_id = tailoring_file['tailoring-file-profiles'][0]['id']
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
        })
        self.assertEqual(scap_policy['scap-content-id'], self.scap_id_rhel6)
        Scappolicy.update({
            'name': name,
            'tailoring-file-id': tailoring_file['id'],
            'tailoring-file-profile-id': tailor_profile_id
        })
        scap_info = Scappolicy.info({'name': name})
        self.assertEqual(scap_info['tailoring-file-id'], tailoring_file['id'])
        self.assertEqual(scap_info['tailoring-file-profile-id'],
                         tailor_profile_id)

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_update_scap_policy_with_tailoringfiles_name(self):
        """Update the scap policy by updating the scap tailoring file name
        associated with the policy

        :id: a2403170-51df-4561-9a58-820f77a5e048

        :steps:

            1. Login to hammer shell.
            2. Execute "policy" command with "update" as sub-command.
            3. Pass tailoring-file as parameter.

        :expectedresults: The scap policy is updated.
        """
        _, file_name = os.path.split(settings.oscap.tailoring_path)
        ssh.upload_file(
            local_file=settings.oscap.tailoring_path,
            remote_file="/tmp/{0}".format(file_name)
        )
        tailoring_file = make_tailoringfile({
            'scap-file': '/tmp/{0}'.format(file_name)
        })
        tailor_profile_id = tailoring_file['tailoring-file-profiles'][0]['id']
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
        })
        self.assertEqual(scap_policy['scap-content-id'], self.scap_id_rhel6)
        Scappolicy.update({
            'name': name,
            'tailoring-file': tailoring_file['name'],
            'tailoring-file-profile-id': tailor_profile_id
        })
        scap_info = Scappolicy.info({'name': name})
        self.assertEqual(scap_info['tailoring-file-id'], tailoring_file['id'])
        self.assertEqual(scap_info['tailoring-file-profile-id'],
                         tailor_profile_id)

    @run_only_on('sat')
    @tier2
    @upgrade
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
        """
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
        })
        self.assertEqual(scap_policy['name'], name)
        Scappolicy.delete({'id': scap_policy['id']})
        with self.assertRaises(CLIReturnCodeError):
            Scappolicy.info({'id': scap_policy['id']})

    @run_only_on('sat')
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
        """
        name = gen_string('alphanumeric')
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
        })
        self.assertEqual(scap_policy['name'], name)
        Scappolicy.delete({'name': name})
        with self.assertRaises(CLIReturnCodeError):
            Scapcontent.info({'name': scap_policy['name']})

    @run_only_on('sat')
    @tier2
    def test_positive_associate_scap_policy_with_single_server(self):
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
        """
        hostgroup = make_hostgroup()
        for name in valid_hosts_list():
            with self.subTest(name):
                host = entities.Host()
                host.create_missing()
                result = make_host({
                    u'architecture-id': host.architecture.id,
                    u'domain-id': host.domain.id,
                    u'environment-id': host.environment.id,
                    u'location-id': host.location.id,
                    u'mac': host.mac,
                    u'medium-id': host.medium.id,
                    u'name': name,
                    u'operatingsystem-id': host.operatingsystem.id,
                    u'organization-id': host.organization.id,
                    u'partition-table-id': host.ptable.id,
                    u'puppet-proxy-id': self.puppet_proxy['id'],
                    u'root-password': host.root_pass,
                })
        scap_policy = make_scap_policy({
            'name': name,
            'scap-content-id': self.scap_id_rhel6,
            'scap-content-profile-id': self.scap_profile_id_rhel6,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'hostgroups': hostgroup['name']
        })
        Scappolicy.update({
            'id': scap_policy['id'],
            'hosts': result['name'],
        })
        data = entities.Policies(id=scap_policy['id']).read()
        location =
        r = requests.get(location, auth=("admin", "changeme"), verify=False)
        print(r.json())

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
