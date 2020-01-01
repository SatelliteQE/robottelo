"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: LDAP

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from nailgun import entities
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    make_ldap_auth_source,
    make_usergroup_external,
    make_usergroup
)
from robottelo.cli.auth import Auth
from robottelo.cli.ldapauthsource import LDAPAuthSource
from robottelo.cli.role import Role
from robottelo.cli.usergroup import UserGroup, UserGroupExternal
from robottelo.config import settings
from robottelo.constants import LDAP_ATTR, LDAP_SERVER_TYPE
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import run_in_one_thread, skip_if_not_set, tier1, tier2, tier3, upgrade
from robottelo.test import CLITestCase



@run_in_one_thread
class LDAPAuthSourceTestCase(CLITestCase):
    """Implements Active Directory feature tests in CLI"""

    @classmethod
    @skip_if_not_set('ldap')
    def setUpClass(cls):
        """Fetch necessary properties from settings which can be re-used in
        tests.
        """
        super(LDAPAuthSourceTestCase, cls).setUpClass()
        cls.ldap_user_name = settings.ldap.username
        cls.ldap_user_passwd = settings.ldap.password
        cls.base_dn = settings.ldap.basedn
        cls.group_base_dn = settings.ldap.grpbasedn
        cls.ldap_hostname = settings.ldap.hostname

    @tier1
    @upgrade
    def test_positive_create_withad(self):
        """Create/update/delete LDAP authentication with AD using names of different types

        :id: 093f6abc-91e7-4449-b484-71e4a14ac808

        :expectedresults: Whether creating/upating/deleting LDAP Auth with AD is successful.

        :CaseImportance: Critical
        """
        for server_name in generate_strings_list():
            with self.subTest(server_name):
                auth = make_ldap_auth_source({
                    u'name': server_name,
                    u'onthefly-register': 'true',
                    u'host': self.ldap_hostname,
                    u'server-type': LDAP_SERVER_TYPE['CLI']['ad'],
                    u'attr-login': LDAP_ATTR['login_ad'],
                    u'attr-firstname': LDAP_ATTR['firstname'],
                    u'attr-lastname': LDAP_ATTR['surname'],
                    u'attr-mail': LDAP_ATTR['mail'],
                    u'account': self.ldap_user_name,
                    u'account-password': self.ldap_user_passwd,
                    u'base-dn': self.base_dn,
                    u'groups-base': self.group_base_dn,
                })
                self.assertEqual(auth['server']['name'], server_name)
                self.assertEqual(auth['server']['server'], self.ldap_hostname)
                self.assertEqual(auth['server']['server-type'], LDAP_SERVER_TYPE['CLI']['ad'])
                new_name = gen_string('alpha')
                LDAPAuthSource.update({
                    u'name': server_name,
                    u'new-name': new_name
                })
                updated_auth = LDAPAuthSource.info({u'id': auth['server']['id']})
                self.assertEqual(updated_auth['server']['name'], new_name)
                LDAPAuthSource.delete({
                    u'name': new_name
                })
                with self.assertRaises(CLIReturnCodeError):
                    LDAPAuthSource.info({'name': new_name})


@run_in_one_thread
class IPAAuthSourceTestCase(CLITestCase):
    """Implements FreeIPA ldap auth feature tests in CLI"""

    def _add_user_in_IPA(self, member_username, member_group):
        ssh.command('echo {0} | kinit admin'.format(self.ldap_ipa_user_passwd),
                    hostname=self.ldap_ipa_hostname)
        ssh.command('ipa group-add-member {} --users={}'.format(member_group,
                                                                member_username),
                    hostname=self.ldap_ipa_hostname)

    def _remove_user_in_IPA(self, member_username, member_group):
        ssh.command('echo {0} | kinit admin'.format(self.ldap_ipa_user_passwd),
                    hostname=self.ldap_ipa_hostname)
        result = ssh.command('ipa group-remove-member {} --users={}'.format(member_group,
                                                                            member_username),
                             hostname=self.ldap_ipa_hostname)
        if result.return_code != 0:
            raise AssertionError('failed to remove the user into user-group')

    def _clean_up_previous_ldap(self):
        """clean up the all ldap settings user, usergroup and ldap delete"""
        ldap = entities.AuthSourceLDAP().search()
        for ldap_auth in range(len(ldap)):
            users = entities.User(auth_source=ldap[ldap_auth]).search()
            for user in range(len(users)):
                users[user].delete()
            ldap[ldap_auth].delete()
        user_groups = entities.UserGroup().search()
        for user_group in user_groups:
            user_group.delete()

    @classmethod
    @skip_if_not_set('ipa')
    def setUpClass(cls):
        """Fetch necessary properties from settings which can be re-used in
        tests.
        """
        super(IPAAuthSourceTestCase, cls).setUpClass()
        cls.ldap_ipa_user_name = settings.ipa.username_ipa
        cls.ldap_ipa_user_passwd = settings.ipa.password_ipa
        cls.ipa_base_dn = settings.ipa.basedn_ipa
        cls.ipa_group_base_dn = settings.ipa.grpbasedn_ipa
        cls.ldap_ipa_hostname = settings.ipa.hostname_ipa
        cls.ipa_user = settings.ipa.user_ipa

    @tier2
    @upgrade
    def test_positive_end_to_end_withipa(self):
        """CRUD LDAP authentication with FreeIPA

        :id: 6cb54405-b579-4020-bf99-cb811a6aa28b

        :expectedresults: Whether creating/updating/deleting LDAP Auth with FreeIPA is successful.

        :CaseImportance: High
        """
        for server_name in generate_strings_list():
            with self.subTest(server_name):
                auth = make_ldap_auth_source({
                    u'name': server_name,
                    u'onthefly-register': 'true',
                    u'host': self.ldap_ipa_hostname,
                    u'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
                    u'attr-login': LDAP_ATTR['login'],
                    u'attr-firstname': LDAP_ATTR['firstname'],
                    u'attr-lastname': LDAP_ATTR['surname'],
                    u'attr-mail': LDAP_ATTR['mail'],
                    u'account': self.ldap_ipa_user_name,
                    u'account-password': self.ldap_ipa_user_passwd,
                    u'base-dn': self.ipa_base_dn,
                    u'groups-base': self.ipa_base_dn,
                })
                self.assertEqual(auth['server']['name'], server_name)
                self.assertEqual(auth['server']['server'], self.ldap_ipa_hostname)
                self.assertEqual(auth['server']['server-type'], LDAP_SERVER_TYPE['CLI']['ipa'])
                new_name = gen_string('alpha')
                LDAPAuthSource.update({
                    u'name': server_name,
                    u'new-name': new_name
                })
                updated_auth = LDAPAuthSource.info({u'id': auth['server']['id']})
                self.assertEqual(updated_auth['server']['name'], new_name)
                LDAPAuthSource.delete({
                    u'name': new_name
                })
                with self.assertRaises(CLIReturnCodeError):
                    LDAPAuthSource.info({'name': new_name})

    @tier3
    def test_usergroup_sync_with_refresh(self):
        """Verify the refresh functionality in Ldap Auth Source

        :id: c905eb80-2bd0-11ea-abc3-ddb7dbb3c930

        :expectedresults: external user-group sync works as expected as on-demand
            sync based on refresh works

        :CaseImportance: Medium
        """
        self._clean_up_previous_ldap()
        ldap_ipa_user_name = self.ldap_ipa_user_name
        ipa_group_base_dn = self.ipa_group_base_dn.replace('foobargroup', 'foreman_group')
        member_username = 'foreman_test'
        member_group = 'foreman_group'
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source_name = gen_string('alpha')
        auth_source = make_ldap_auth_source({
            u'name': auth_source_name,
            u'onthefly-register': 'true',
            u'usergroup-sync': 'false',
            u'host': self.ldap_ipa_hostname,
            u'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
            u'attr-login': LDAP_ATTR['login'],
            u'attr-firstname': LDAP_ATTR['firstname'],
            u'attr-lastname': LDAP_ATTR['surname'],
            u'attr-mail': LDAP_ATTR['mail'],
            u'account': ldap_ipa_user_name,
            u'account-password': self.ldap_ipa_user_passwd,
            u'base-dn': self.ipa_base_dn,
            u'groups-base': ipa_group_base_dn,
        })
        auth_source = LDAPAuthSource.info({u'id': auth_source['server']['id']})

        # Adding User in IPA UserGroup
        self._add_user_in_IPA(member_username, member_group)
        viewer_role = Role.info({'name': 'Viewer'})
        user_group = make_usergroup()
        ext_user_group = make_usergroup_external({
            'auth-source-id': auth_source['server']['id'],
            'user-group-id': user_group['id'],
            'name': member_group,
        })
        UserGroup.add_role({'id': user_group['id'], 'role-id': viewer_role['id']})
        assert ext_user_group['auth-source'] == auth_source['server']['name']
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        result = Auth.with_user(username=member_username,
                                password=self.ldap_ipa_user_passwd).status()
        assert LOGEDIN_MSG.format(member_username) in result[0][u'message']
        with self.assertRaises(CLIReturnCodeError) as error:
            Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert 'Missing one of the required permissions' in error.exception.message
        with self.assertNotRaises(CLIReturnCodeError):
            UserGroupExternal.refresh({
                'user-group-id': user_group['id'],
                'name': member_group
            })
        list = Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert len(list) > 1
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 1
        assert user_group['users'][0] == member_username

        # Removing User in IPA UserGroup
        self._remove_user_in_IPA(member_username, member_group)
        with self.assertNotRaises(CLIReturnCodeError):
            UserGroupExternal.refresh({
                'user-group-id': user_group['id'],
                'name': member_group
            })
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        with self.assertRaises(CLIReturnCodeError) as error:
            Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert 'Missing one of the required permissions' in error.exception.message

    @tier3
    def test_usergroup_with_usergroup_sync(self):
        """Verify the usergroup-sync functionality in Ldap Auth Source

        :id: 2b63e886-2c53-11ea-9da5-db3ae0527554

        :expectedresults: external user-group sync works as expected automatically
            based on user-sync

        :CaseImportance: Medium
        """
        self._clean_up_previous_ldap()
        ldap_ipa_user_name = self.ldap_ipa_user_name
        ipa_group_base_dn = self.ipa_group_base_dn.replace('foobargroup', 'foreman_group')
        member_username = 'foreman_test'
        member_group = 'foreman_group'
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source_name = gen_string('alpha')
        auth_source = make_ldap_auth_source({
            u'name': auth_source_name,
            u'onthefly-register': 'true',
            u'usergroup-sync': 'true',
            u'host': self.ldap_ipa_hostname,
            u'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
            u'attr-login': LDAP_ATTR['login'],
            u'attr-firstname': LDAP_ATTR['firstname'],
            u'attr-lastname': LDAP_ATTR['surname'],
            u'attr-mail': LDAP_ATTR['mail'],
            u'account': ldap_ipa_user_name,
            u'account-password': self.ldap_ipa_user_passwd,
            u'base-dn': self.ipa_base_dn,
            u'groups-base': ipa_group_base_dn,
        })
        auth_source = LDAPAuthSource.info({u'id': auth_source['server']['id']})

        # Adding User in IPA UserGroup
        self._add_user_in_IPA(member_username, member_group)
        viewer_role = Role.info({'name': 'Viewer'})
        user_group = make_usergroup()
        ext_user_group = make_usergroup_external({
            'auth-source-id': auth_source['server']['id'],
            'user-group-id': user_group['id'],
            'name': member_group,
        })
        UserGroup.add_role({'id': user_group['id'], 'role-id': viewer_role['id']})
        assert ext_user_group['auth-source'] == auth_source['server']['name']
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        result = Auth.with_user(username=member_username,
                                password=self.ldap_ipa_user_passwd).status()
        assert LOGEDIN_MSG.format(member_username) in result[0][u'message']
        list = Role.with_user(username=member_username,
                              password=self.ldap_ipa_user_passwd).list()
        assert len(list) > 1
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 1
        assert user_group['users'][0] == member_username

        # Removing User in IPA UserGroup
        self._remove_user_in_IPA(member_username, member_group)
        with self.assertRaises(CLIReturnCodeError) as error:
            Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert 'Missing one of the required permissions' in error.exception.message
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
