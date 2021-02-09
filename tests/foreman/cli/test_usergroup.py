"""Test class for User Group CLI

:Requirement: Usergroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_ldap_auth_source
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.factory import make_usergroup
from robottelo.cli.factory import make_usergroup_external
from robottelo.cli.ldapauthsource import LDAPAuthSource
from robottelo.cli.task import Task
from robottelo.cli.user import User
from robottelo.cli.usergroup import UserGroup
from robottelo.cli.usergroup import UserGroupExternal
from robottelo.config import settings
from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE
from robottelo.datafactory import gen_string
from robottelo.datafactory import valid_usernames_list
from robottelo.decorators import skip_if_not_set
from robottelo.test import CLITestCase


class UserGroupTestCase(CLITestCase):
    """User group CLI related tests."""

    @pytest.mark.tier1
    def test_positive_CRUD(self):
        """Create new user group with valid elements that attached group.
           List the user group, update and delete it.

        :id: bacef0e3-31dd-4991-93f7-f54fbe64d0f0

        :expectedresults: User group is created, listed, updated and
             deleted successfully.

        :CaseImportance: Critical
        """
        user = make_user()
        ug_name = random.choice(valid_usernames_list())
        role_name = random.choice(valid_usernames_list())
        role = make_role({'name': role_name})
        sub_user_group = make_usergroup()

        # Create
        user_group = make_usergroup(
            {
                'user-ids': user['id'],
                'name': ug_name,
                'role-ids': role['id'],
                'user-group-ids': sub_user_group['id'],
            }
        )

        self.assertEqual(user_group['name'], ug_name)
        self.assertEqual(user_group['users'][0], user['login'])
        self.assertEqual(len(user_group['roles']), 1)
        self.assertEqual(user_group['roles'][0], role_name)
        self.assertEqual(user_group['user-groups'][0]['usergroup'], sub_user_group['name'])

        # List
        result_list = UserGroup.list({'search': f"name={user_group['name']}"})
        self.assertTrue(len(result_list) > 0)
        self.assertTrue(UserGroup.exists(search=('name', user_group['name'])))

        # Update
        new_name = random.choice(valid_usernames_list())
        UserGroup.update({'id': user_group['id'], 'new-name': new_name})
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(user_group['name'], new_name)

        # Delete
        UserGroup.delete({'name': user_group['name']})
        with self.assertRaises(CLIReturnCodeError):
            UserGroup.info({'name': user_group['name']})

    @pytest.mark.tier1
    def test_positive_create_with_multiple_elements(self):
        """Create new user group using multiple users, roles and user
           groups attached to that group.

        :id: 3b0a3c3c-aab2-4e8a-b043-7462621c7333

        :expectedresults: User group is created successfully and contains all
            expected elements.

        :CaseImportance: Critical
        """
        count = 2
        users = [make_user()['login'] for _ in range(count)]
        roles = [make_role()['name'] for _ in range(count)]
        sub_user_groups = [make_usergroup()['name'] for _ in range(count)]
        user_group = make_usergroup(
            {'users': users, 'roles': roles, 'user-groups': sub_user_groups}
        )
        self.assertEqual(sorted(users), sorted(user_group['users']))
        self.assertEqual(sorted(roles), sorted(user_group['roles']))
        self.assertEqual(
            sorted(sub_user_groups),
            sorted([ug['usergroup'] for ug in user_group['user-groups']]),
        )

    @pytest.mark.tier2
    def test_positive_add_and_remove_elements(self):
        """Create new user group. Add and remove several element from the group.

        :id: a4ce8724-d3c8-4c00-9421-aaa40394134d

        :BZ: 1395229

        :expectedresults: Elements are added to user group and then removed
                          successfully.

        :CaseLevel: Integration
        """
        role = make_role()
        user_group = make_usergroup()
        user = make_user()
        sub_user_group = make_usergroup()

        # Add elements by id
        UserGroup.add_role({'id': user_group['id'], 'role-id': role['id']})
        UserGroup.add_user({'id': user_group['id'], 'user-id': user['id']})
        UserGroup.add_user_group({'id': user_group['id'], 'user-group-id': sub_user_group['id']})

        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(len(user_group['roles']), 1)
        self.assertEqual(user_group['roles'][0], role['name'])
        self.assertEqual(len(user_group['users']), 1)
        self.assertEqual(user_group['users'][0], user['login'])
        self.assertEqual(len(user_group['user-groups']), 1)
        self.assertEqual(user_group['user-groups'][0]['usergroup'], sub_user_group['name'])

        # Remove elements by name
        UserGroup.remove_role({'id': user_group['id'], 'role': role['name']})
        UserGroup.remove_user({'id': user_group['id'], 'user': user['login']})
        UserGroup.remove_user_group({'id': user_group['id'], 'user-group': sub_user_group['name']})

        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(len(user_group['roles']), 0)
        self.assertEqual(len(user_group['users']), 0)
        self.assertEqual(len(user_group['user-groups']), 0)

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_remove_user_assigned_to_usergroup(self):
        """Create new user and assign it to user group. Then remove that user.

        :id: 2a2623ce-4723-4402-aae7-8675473fd8bd

        :expectedresults: User should delete successfully.

        :CaseLevel: Integration

        :BZ: 1667704
        """
        user = make_user()
        user_group = make_usergroup()
        UserGroup.add_user({'id': user_group['id'], 'user-id': user['id']})
        with self.assertNotRaises(CLIReturnCodeError):
            User.delete({'id': user['id']})


@pytest.mark.run_in_one_thread
class ActiveDirectoryUserGroupTestCase(CLITestCase):
    """Implements Active Directory feature tests for user groups in CLI."""

    @classmethod
    @skip_if_not_set('ldap')
    def setUpClass(cls):
        """Read settings and create LDAP auth source that can be re-used in
        tests."""
        super().setUpClass()
        cls.ldap_user_name = settings.ldap.username
        cls.ldap_user_passwd = settings.ldap.password
        cls.base_dn = settings.ldap.basedn
        cls.group_base_dn = settings.ldap.grpbasedn
        cls.ldap_hostname = settings.ldap.hostname
        cls.auth = make_ldap_auth_source(
            {
                'name': gen_string('alpha'),
                'onthefly-register': 'true',
                'host': cls.ldap_hostname,
                'server-type': LDAP_SERVER_TYPE['CLI']['ad'],
                'attr-login': LDAP_ATTR['login_ad'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': cls.ldap_user_name,
                'account-password': cls.ldap_user_passwd,
                'base-dn': cls.base_dn,
                'groups-base': cls.group_base_dn,
            }
        )

    def setUp(self):
        """Create new usergroup per each test"""
        super().setUp()
        self.user_group = make_usergroup()

    def tearDown(self):
        """Delete usergroup per each test"""
        for dict in UserGroup.list():
            if UserGroup.info({'id': dict['id']})['external-user-groups']:
                UserGroup.delete({'id': dict['id']})
        super().tearDown()

    @classmethod
    @skip_if_not_set('ldap')
    def tearDownClass(cls):
        """Delete the AD auth-source afterwards"""
        LDAPAuthSource.delete({'id': cls.auth['server']['id']})
        super().tearDownClass()

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_create_and_refresh_external_usergroup_with_local_user(self):
        """Create and refresh external user group with AD LDAP. Verify Local user
           association from user-group with external group with AD LDAP

        :id: 7431979c-aea8-4984-bb7d-185f5b7c3109

        :expectedresults: User group is created and refreshed successfully.
            Local user is associated from user-group with external group.

        :CaseLevel: Integration

        :BZ: 1412209
        """
        ext_user_group = make_usergroup_external(
            {
                'auth-source-id': self.auth['server']['id'],
                'user-group-id': self.user_group['id'],
                'name': 'foobargroup',
            }
        )
        self.assertEqual(ext_user_group['auth-source'], self.auth['server']['name'])
        with self.assertNotRaises(CLIReturnCodeError):
            UserGroupExternal.refresh(
                {'user-group-id': self.user_group['id'], 'name': 'foobargroup'}
            )
        user = make_user()
        UserGroup.add_user({'user': user['login'], 'id': self.user_group['id']})
        self.assertEqual(
            User.info({'login': user['login']})['user-groups'][0]['usergroup'],
            self.user_group['name'],
        )
        with self.assertNotRaises(CLIReturnCodeError):
            UserGroupExternal.refresh(
                {'user-group-id': self.user_group['id'], 'name': 'foobargroup'}
            )
        self.assertEqual(
            User.info({'login': user['login']})['user-groups'][0]['usergroup'],
            self.user_group['name'],
        )

    @pytest.mark.tier2
    def test_positive_automate_bz1426957(self):
        """Verify role is properly reflected on AD user.

        :id: 1c1209a6-5bb8-489c-a151-bb2fce4dbbfc

        :expectedresults: Roles from usergroup is applied on AD user successfully.

        :CaseLevel: Integration

        :BZ: 1426957, 1667704
        """
        ext_user_group = make_usergroup_external(
            {
                'auth-source-id': self.auth['server']['id'],
                'user-group-id': self.user_group['id'],
                'name': 'foobargroup',
            }
        )
        self.assertEqual(ext_user_group['auth-source'], self.auth['server']['name'])
        role = make_role()
        UserGroup.add_role({'id': self.user_group['id'], 'role-id': role['id']})
        with self.assertNotRaises(CLIReturnCodeError):
            Task.with_user(username=self.ldap_user_name, password=self.ldap_user_passwd).list()
            UserGroupExternal.refresh(
                {'user-group-id': self.user_group['id'], 'name': 'foobargroup'}
            )
        self.assertIn(role['name'], User.info({'login': self.ldap_user_name})['user-groups'])
        User.delete({'login': self.ldap_user_name})

    @pytest.mark.tier2
    def test_negative_automate_bz1437578(self):
        """Verify error message on usergroup create with 'Domain Users' on AD user.

        :id: d4caf33e-b9eb-4281-9e04-fbe1d5b035dc

        :expectedresults: Error message as Domain Users is a special group in AD.

        :CaseLevel: Integration

        :BZ: 1437578
        """
        with self.assertRaises(CLIReturnCodeError):
            result = UserGroupExternal.create(
                {
                    'auth-source-id': self.auth['server']['id'],
                    'user-group-id': self.user_group['id'],
                    'name': 'Domain Users',
                }
            )
            self.assertEqual(
                'Could not create external user group: '
                'Name is not found in the authentication source'
                'Name Domain Users is a special group in AD.'
                ' Unfortunately, we cannot obtain membership information'
                ' from a LDAP search and therefore sync it.',
                result,
            )


@pytest.mark.run_in_one_thread
class FreeIPAUserGroupTestCase(CLITestCase):
    """Implements FreeIPA LDAP feature tests for user groups in CLI."""

    @classmethod
    @skip_if_not_set('ipa')
    def setUpClass(cls):
        """Read settings and create LDAP auth source that can be re-used in
        tests."""
        super().setUpClass()
        cls.ldap_user_name = settings.ipa.username_ipa
        cls.ldap_user_passwd = settings.ipa.password_ipa
        cls.base_dn = settings.ipa.basedn_ipa
        cls.group_base_dn = settings.ipa.grpbasedn_ipa
        cls.ldap_hostname = settings.ipa.hostname_ipa
        cls.auth = make_ldap_auth_source(
            {
                'name': gen_string('alpha'),
                'onthefly-register': 'true',
                'host': cls.ldap_hostname,
                'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
                'attr-login': LDAP_ATTR['login'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': cls.ldap_user_name,
                'account-password': cls.ldap_user_passwd,
                'base-dn': cls.base_dn,
                'groups-base': cls.group_base_dn,
            }
        )

    def setUp(self):
        """Create new usergroup per each test"""
        super().setUp()
        self.user_group = make_usergroup()

    def tearDown(self):
        """Delete usergroup per each test"""
        for dict in UserGroup.list():
            if UserGroup.info({'id': dict['id']})['external-user-groups']:
                UserGroup.delete({'id': dict['id']})
        super().tearDown()

    @classmethod
    @skip_if_not_set('ipa')
    def tearDownClass(cls):
        """Delete the IPA auth-source afterwards"""
        LDAPAuthSource.delete({'id': cls.auth['server']['id']})
        super().tearDownClass()

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_create_and_refresh_external_usergroup_with_local_user(self):
        """Create and Refresh external user group with FreeIPA LDAP. Verify Local user
           association from user-group with external group with FreeIPA LDAP

        :id: bd6152e3-51ac-4e84-b084-8bab1c4eb583

        :expectedresults: User group is created successfully and assigned to correct auth
             source. User group is refreshed successfully. Local user is associated from
             user group with external group.

        :CaseLevel: Integration

        :BZ: 1412209
        """
        ext_user_group = make_usergroup_external(
            {
                'auth-source-id': self.auth['server']['id'],
                'user-group-id': self.user_group['id'],
                'name': 'foobargroup',
            }
        )
        self.assertEqual(ext_user_group['auth-source'], self.auth['server']['name'])
        with self.assertNotRaises(CLIReturnCodeError):
            UserGroupExternal.refresh(
                {'user-group-id': self.user_group['id'], 'name': 'foobargroup'}
            )
        user = make_user()
        UserGroup.add_user({'user': user['login'], 'id': self.user_group['id']})
        self.assertEqual(
            User.info({'login': user['login']})['user-groups'][0]['usergroup'],
            self.user_group['name'],
        )
        with self.assertNotRaises(CLIReturnCodeError):
            UserGroupExternal.refresh(
                {'user-group-id': self.user_group['id'], 'name': 'foobargroup'}
            )
        print(User.info({'login': user['login']}))
        self.assertEqual(
            User.info({'login': user['login']})['user-groups'][0]['usergroup'],
            self.user_group['name'],
        )
