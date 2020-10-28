"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: LDAP

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from time import sleep

import pytest
from airgun.session import Session
from fauxfactory import gen_string
from nailgun import entities

from robottelo import ssh
from robottelo.cli.auth import Auth
from robottelo.cli.auth import AuthLogin
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_ldap_auth_source
from robottelo.cli.factory import make_usergroup
from robottelo.cli.factory import make_usergroup_external
from robottelo.cli.ldapauthsource import LDAPAuthSource
from robottelo.cli.role import Role
from robottelo.cli.task import Task
from robottelo.cli.usergroup import UserGroup
from robottelo.cli.usergroup import UserGroupExternal
from robottelo.config import settings
from robottelo.constants import HAMMER_CONFIG
from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import parametrized
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.rhsso_utils import get_oidc_authorization_endpoint
from robottelo.rhsso_utils import get_oidc_client_id
from robottelo.rhsso_utils import get_oidc_token_endpoint
from robottelo.rhsso_utils import get_two_factor_token_rh_sso_url
from robottelo.rhsso_utils import open_pxssh_session
from robottelo.rhsso_utils import run_command
from robottelo.rhsso_utils import update_client_configuration


@run_in_one_thread
class TestADAuthSource:
    """Implements Active Directory feature tests in CLI"""

    @tier1
    @upgrade
    @pytest.mark.parametrize('server_name', **parametrized(generate_strings_list()))
    def test_positive_create_with_ad(self, ad_data, server_name):
        """Create/update/delete LDAP authentication with AD using names of different types

        :id: 093f6abc-91e7-4449-b484-71e4a14ac808

        :expectedresults: Whether creating/upating/deleting LDAP Auth with AD is successful.

        :CaseImportance: Critical

        :parametrized: yes
        """
        auth = make_ldap_auth_source(
            {
                'name': server_name,
                'onthefly-register': 'true',
                'host': ad_data['ldap_hostname'],
                'server-type': LDAP_SERVER_TYPE['CLI']['ad'],
                'attr-login': LDAP_ATTR['login_ad'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': ad_data['ldap_user_name'],
                'account-password': ad_data['ldap_user_passwd'],
                'base-dn': ad_data['base_dn'],
                'groups-base': ad_data['group_base_dn'],
            }
        )
        assert auth['server']['name'] == server_name
        assert auth['server']['server'] == ad_data['ldap_hostname']
        assert auth['server']['server-type'] == LDAP_SERVER_TYPE['CLI']['ad']
        new_name = gen_string('alpha')
        LDAPAuthSource.update({'name': server_name, 'new-name': new_name})
        updated_auth = LDAPAuthSource.info({'id': auth['server']['id']})
        assert updated_auth['server']['name'] == new_name
        LDAPAuthSource.delete({'name': new_name})
        with pytest.raises(CLIReturnCodeError):
            LDAPAuthSource.info({'name': new_name})


@run_in_one_thread
class TestIPAAuthSource:
    """Implements FreeIPA ldap auth feature tests in CLI"""

    def _add_user_in_IPA_usergroup(self, member_username, member_group):
        ssh.command(
            'echo {0} | kinit admin'.format(self.ldap_ipa_user_passwd),
            hostname=self.ldap_ipa_hostname,
        )
        ssh.command(
            'ipa group-add-member {} --users={}'.format(member_group, member_username),
            hostname=self.ldap_ipa_hostname,
        )

    def _remove_user_in_IPA_usergroup(self, member_username, member_group):
        ssh.command(
            'echo {0} | kinit admin'.format(self.ldap_ipa_user_passwd),
            hostname=self.ldap_ipa_hostname,
        )
        result = ssh.command(
            'ipa group-remove-member {} --users={}'.format(member_group, member_username),
            hostname=self.ldap_ipa_hostname,
        )
        if result.return_code != 0:
            raise AssertionError('failed to remove the user from user-group')

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

    @tier2
    @pytest.mark.parametrize('server_name', **parametrized(generate_strings_list()))
    @upgrade
    def test_positive_end_to_end_with_ipa(self, ipa_data, server_name):
        """CRUD LDAP authentication with FreeIPA

        :id: 6cb54405-b579-4020-bf99-cb811a6aa28b

        :expectedresults: Whether creating/updating/deleting LDAP Auth with FreeIPA is successful.

        :CaseImportance: High

        :parametrized: yes
        """
        auth = make_ldap_auth_source(
            {
                'name': server_name,
                'onthefly-register': 'true',
                'host': ipa_data['ldap_hostname'],
                'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
                'attr-login': LDAP_ATTR['login'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': ipa_data['ldap_user_cn'],
                'account-password': ipa_data['ldap_user_passwd'],
                'base-dn': ipa_data['base_dn'],
                'groups-base': ipa_data['group_base_dn'],
            }
        )
        assert auth['server']['name'] == server_name
        assert auth['server']['server'] == ipa_data['ldap_hostname']
        assert auth['server']['server-type'] == LDAP_SERVER_TYPE['CLI']['ipa']
        new_name = gen_string('alpha')
        LDAPAuthSource.update({'name': server_name, 'new-name': new_name})
        updated_auth = LDAPAuthSource.info({'id': auth['server']['id']})
        assert updated_auth['server']['name'] == new_name
        LDAPAuthSource.delete({'name': new_name})
        with pytest.raises(CLIReturnCodeError):
            LDAPAuthSource.info({'name': new_name})

    @tier3
    def test_usergroup_sync_with_refresh(self, ipa_data):
        """Verify the refresh functionality in Ldap Auth Source

        :id: c905eb80-2bd0-11ea-abc3-ddb7dbb3c930

        :expectedresults: external user-group sync works as expected as on-demand
            sync based on refresh works

        :CaseImportance: Medium
        """
        self._clean_up_previous_ldap()
        self.ldap_ipa_hostname = ipa_data['ldap_hostname']
        self.ldap_ipa_user_passwd = ipa_data['ldap_user_passwd']
        ipa_group_base_dn = ipa_data['group_base_dn'].replace('foobargroup', 'foreman_group')
        member_username = 'foreman_test'
        member_group = 'foreman_group'
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source_name = gen_string('alpha')
        auth_source = make_ldap_auth_source(
            {
                'name': auth_source_name,
                'onthefly-register': 'true',
                'usergroup-sync': 'false',
                'host': ipa_data['ldap_hostname'],
                'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
                'attr-login': LDAP_ATTR['login'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': ipa_data['ldap_user_cn'],
                'account-password': ipa_data['ldap_user_passwd'],
                'base-dn': ipa_data['base_dn'],
                'groups-base': ipa_group_base_dn,
            }
        )
        auth_source = LDAPAuthSource.info({'id': auth_source['server']['id']})

        # Adding User in IPA UserGroup
        self._add_user_in_IPA_usergroup(member_username, member_group)
        viewer_role = Role.info({'name': 'Viewer'})
        user_group = make_usergroup()
        ext_user_group = make_usergroup_external(
            {
                'auth-source-id': auth_source['server']['id'],
                'user-group-id': user_group['id'],
                'name': member_group,
            }
        )
        UserGroup.add_role({'id': user_group['id'], 'role-id': viewer_role['id']})
        assert ext_user_group['auth-source'] == auth_source['server']['name']
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        result = Auth.with_user(
            username=member_username, password=self.ldap_ipa_user_passwd
        ).status()
        assert LOGEDIN_MSG.format(member_username) in result[0]['message']
        with pytest.raises(CLIReturnCodeError) as error:
            Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert 'Missing one of the required permissions' in error.value.message
        UserGroupExternal.refresh({'user-group-id': user_group['id'], 'name': member_group})
        list = Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert len(list) > 1
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 1
        assert user_group['users'][0] == member_username

        # Removing User in IPA UserGroup
        self._remove_user_in_IPA_usergroup(member_username, member_group)
        UserGroupExternal.refresh({'user-group-id': user_group['id'], 'name': member_group})
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        with pytest.raises(CLIReturnCodeError) as error:
            Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert 'Missing one of the required permissions' in error.value.message

    @tier3
    def test_usergroup_with_usergroup_sync(self, ipa_data):
        """Verify the usergroup-sync functionality in Ldap Auth Source

        :id: 2b63e886-2c53-11ea-9da5-db3ae0527554

        :expectedresults: external user-group sync works as expected automatically
            based on user-sync

        :CaseImportance: Medium
        """
        self._clean_up_previous_ldap()
        self.ldap_ipa_hostname = ipa_data['ldap_hostname']
        self.ldap_ipa_user_passwd = ipa_data['ldap_user_passwd']
        ipa_group_base_dn = ipa_data['group_base_dn'].replace('foobargroup', 'foreman_group')
        member_username = 'foreman_test'
        member_group = 'foreman_group'
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source_name = gen_string('alpha')
        auth_source = make_ldap_auth_source(
            {
                'name': auth_source_name,
                'onthefly-register': 'true',
                'usergroup-sync': 'true',
                'host': ipa_data['ldap_hostname'],
                'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
                'attr-login': LDAP_ATTR['login'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': ipa_data['ldap_user_cn'],
                'account-password': ipa_data['ldap_user_passwd'],
                'base-dn': ipa_data['base_dn'],
                'groups-base': ipa_group_base_dn,
            }
        )
        auth_source = LDAPAuthSource.info({'id': auth_source['server']['id']})

        # Adding User in IPA UserGroup
        self._add_user_in_IPA_usergroup(member_username, member_group)
        viewer_role = Role.info({'name': 'Viewer'})
        user_group = make_usergroup()
        ext_user_group = make_usergroup_external(
            {
                'auth-source-id': auth_source['server']['id'],
                'user-group-id': user_group['id'],
                'name': member_group,
            }
        )
        UserGroup.add_role({'id': user_group['id'], 'role-id': viewer_role['id']})
        assert ext_user_group['auth-source'] == auth_source['server']['name']
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        result = Auth.with_user(
            username=member_username, password=self.ldap_ipa_user_passwd
        ).status()
        assert LOGEDIN_MSG.format(member_username) in result[0]['message']
        list = Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert len(list) > 1
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 1
        assert user_group['users'][0] == member_username

        # Removing User in IPA UserGroup
        self._remove_user_in_IPA_usergroup(member_username, member_group)
        with pytest.raises(CLIReturnCodeError) as error:
            Role.with_user(username=member_username, password=self.ldap_ipa_user_passwd).list()
        assert 'Missing one of the required permissions' in error.value.message
        user_group = UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0


@run_in_one_thread
class TestOpenLdapAuthSource:
    """Implements OpenLDAP Auth Source tests in CLI"""

    @tier2
    @pytest.mark.parametrize('server_name', **parametrized(generate_strings_list()))
    @upgrade
    def test_positive_end_to_end_with_open_ldap(self, open_ldap_data, server_name):
        """CRUD LDAP Operations with OpenLDAP

        :id: f84db334-0189-11eb-846c-d46d6dd3b5b2

        :expectedresults: Whether creating/updating/deleting LDAP Auth with OpenLDAP is successful.

        :CaseImportance: High
        """
        auth = make_ldap_auth_source(
            {
                'name': server_name,
                'onthefly-register': 'true',
                'host': open_ldap_data.hostname,
                'server-type': LDAP_SERVER_TYPE['CLI']['posix'],
                'attr-login': LDAP_ATTR['login_ad'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': open_ldap_data.username,
                'account-password': open_ldap_data.password,
                'base-dn': open_ldap_data.base_dn,
            }
        )
        assert auth['server']['name'] == server_name
        assert auth['server']['server'] == open_ldap_data.hostname
        assert auth['server']['server-type'] == LDAP_SERVER_TYPE['CLI']['posix']
        new_name = gen_string('alpha')
        LDAPAuthSource.update({'name': server_name, 'new-name': new_name})
        updated_auth = LDAPAuthSource.info({'id': auth['server']['id']})
        assert updated_auth['server']['name'] == new_name
        LDAPAuthSource.delete({'name': new_name})
        with pytest.raises(CLIReturnCodeError):
            LDAPAuthSource.info({'name': new_name})


class TestRHSSOAuthSource:
    """Implements RH-SSO auth source tests in CLI"""

    def configure_hammer_session(self, enable=True):
        """take backup of the hammer config file and enable use_sessions"""
        run_command(f"cp {HAMMER_CONFIG} {HAMMER_CONFIG}.backup")
        run_command(f"sed -i '/:use_sessions.*/d' {HAMMER_CONFIG}")
        run_command(f"echo '  :use_sessions: {'true' if enable else 'false'}' >> {HAMMER_CONFIG}")

    @pytest.fixture()
    def rh_sso_hammer_auth_setup(self, request):
        """rh_sso hammer setup before running the auth login tests"""
        self.configure_hammer_session()
        client_config = {"publicClient": "true"}
        update_client_configuration(client_config)

        def rh_sso_hammer_auth_cleanup():
            """restore the hammer config backup file and rhsso client settings"""
            run_command(f"mv {HAMMER_CONFIG}.backup {HAMMER_CONFIG}")
            client_config = {"publicClient": "false"}
            update_client_configuration(client_config)

        request.addfinalizer(rh_sso_hammer_auth_cleanup)

    @tier3
    def test_rhsso_login_using_hammer(
        self, enable_external_auth_rhsso, rhsso_setting_setup, rh_sso_hammer_auth_setup
    ):
        """verify the hammer auth login using RHSSO auth source

        :id: 56c09a1a-d0e5-11ea-9024-d46d6dd3b5b2

        :expectedresults: hammer auth login should be suceessful for a rhsso user

        :CaseImportance: High
        """
        result = AuthLogin.oauth(
            {
                'oidc-token-endpoint': get_oidc_token_endpoint(),
                'oidc-client-id': get_oidc_client_id(),
                'username': settings.rhsso.rhsso_user,
                'password': settings.rhsso.password,
            }
        )
        assert f"Successfully logged in as '{settings.rhsso.rhsso_user}'." == result[0]['message']
        result = Auth.with_user(
            username=settings.rhsso.rhsso_user, password=settings.rhsso.password
        ).status()
        assert (
            f"Session exists, currently logged in as '{settings.rhsso.rhsso_user}'."
            == result[0]['message']
        )
        task_list = Task.with_user(
            username=settings.rhsso.rhsso_user, password=settings.rhsso.password
        ).list()
        assert len(task_list) >= 0
        with pytest.raises(CLIReturnCodeError) as error:
            Role.with_user(
                username=settings.rhsso.rhsso_user, password=settings.rhsso.password
            ).list()
        assert 'Missing one of the required permissions' in error.value.message

    @tier3
    def test_rhsso_timeout_using_hammer(
        self,
        enable_external_auth_rhsso,
        rhsso_setting_setup_with_timeout,
        rh_sso_hammer_auth_setup,
    ):
        """verify the hammer auth timeout using RHSSO auth source

        :id: d014cc98-d198-11ea-b526-d46d6dd3b5b2

        :expectedresults: hammer auth login timeout should be suceessful for a rhsso user

        :CaseImportance: Medium
        """
        result = AuthLogin.oauth(
            {
                'oidc-token-endpoint': get_oidc_token_endpoint(),
                'oidc-client-id': get_oidc_client_id(),
                'username': settings.rhsso.rhsso_user,
                'password': settings.rhsso.password,
            }
        )
        assert f"Successfully logged in as '{settings.rhsso.rhsso_user}'." == result[0]['message']
        sleep(70)
        with pytest.raises(CLIReturnCodeError) as error:
            Task.with_user(
                username=settings.rhsso.rhsso_user, password=settings.rhsso.password
            ).list()
        assert 'Unable to authenticate user sat_admin' in error.value.message

    @tier3
    def test_rhsso_two_factor_login_using_hammer(
        self, rhsso_setting_setup, rh_sso_hammer_auth_setup
    ):
        """verify the hammer auth login using RHSSO auth source

        :id: 4018c646-cb64-4eae-a422-7d5257ed2756

        :expectedresults: hammer auth login should be suceessful for a rhsso user

        :CaseImportance: Medium
        """
        with Session(login=False) as rhsso_session:
            two_factor_code = rhsso_session.rhsso_login.get_two_factor_login_code(
                {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.password},
                get_two_factor_token_rh_sso_url(),
            )
            with open_pxssh_session() as ssh_session:
                ssh_session.sendline(
                    f"echo '{two_factor_code['code']}' | hammer auth login oauth "
                    f"--oidc-token-endpoint {get_oidc_token_endpoint()} "
                    f"--oidc-authorization-endpoint {get_oidc_authorization_endpoint()} "
                    f"--oidc-client-id {get_oidc_client_id()} "
                    f"--oidc-redirect-uri 'urn:ietf:wg:oauth:2.0:oob' "
                    f"--two-factor "
                )
                ssh_session.prompt()  # match the prompt
                result = ssh_session.before.decode()
                assert f"Successfully logged in as '{settings.rhsso.rhsso_user}'." in result
