"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseComponent: Authentication

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_string
from nailgun import entities
import pytest

from robottelo.constants import LDAP_ATTR, LDAP_SERVER_TYPE
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import generate_strings_list, parametrized


@pytest.fixture
def ldap_tear_down():
    """Teardown the all ldap settings user, usergroup and ldap delete"""
    yield
    ldap_auth_sources = entities.AuthSourceLDAP().search()
    for ldap_auth in ldap_auth_sources:
        users = entities.User(auth_source=ldap_auth).search()
        for user in users:
            user.delete()
        user_groups = entities.UserGroup().search()
        if user_groups:
            user_groups[0].delete()
        ldap_auth.delete()


@pytest.mark.run_in_one_thread
class TestADAuthSource:
    """Implements Active Directory feature tests in CLI"""

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize('server_name', **parametrized(generate_strings_list()))
    @pytest.mark.usefixtures("ldap_tear_down")
    def test_positive_create_with_ad(self, ad_data, server_name, module_target_sat):
        """Create/update/delete LDAP authentication with AD using names of different types

        :id: 093f6abc-91e7-4449-b484-71e4a14ac808

        :parametrized: yes

        :expectedresults: Whether creating/upating/deleting LDAP Auth with AD is successful.

        :CaseImportance: Critical
        """
        ad_data = ad_data()
        auth = module_target_sat.cli_factory.ldap_auth_source(
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
        module_target_sat.cli.LDAPAuthSource.update({'name': server_name, 'new-name': new_name})
        updated_auth = module_target_sat.cli.LDAPAuthSource.info({'id': auth['server']['id']})
        assert updated_auth['server']['name'] == new_name
        module_target_sat.cli.LDAPAuthSource.delete({'name': new_name})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.LDAPAuthSource.info({'name': new_name})

    @pytest.mark.tier1
    @pytest.mark.parametrize('member_group', ['foobargroup', 'foobar.group'])
    @pytest.mark.usefixtures("ldap_tear_down")
    def test_positive_refresh_usergroup_with_ad(self, member_group, ad_data, module_target_sat):
        """Verify the usergroup-sync functionality in AD Auth Source

        :id: 2e913e76-49c3-11eb-b4c6-d46d6dd3b5b2

        :customerscenario: true

        :CaseImportance: Medium

        :bz: 1901392

        :parametrized: yes

        :expectedresults: external user-group sync works as expected automatically
            based on user-sync
        """
        ad_data = ad_data()
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source = module_target_sat.cli_factory.ldap_auth_source(
            {
                'name': gen_string('alpha'),
                'onthefly-register': 'true',
                'host': ad_data['ldap_hostname'],
                'server-type': LDAP_SERVER_TYPE['CLI']['ad'],
                'attr-login': LDAP_ATTR['login_ad'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': rf"{ad_data['workgroup']}\{ad_data['ldap_user_name']}",
                'account-password': ad_data['ldap_user_passwd'],
                'base-dn': ad_data['base_dn'],
            }
        )
        viewer_role = module_target_sat.cli.Role.info({'name': 'Viewer'})
        user_group = module_target_sat.cli_factory.usergroup()
        module_target_sat.cli_factory.usergroup_external(
            {
                'auth-source-id': auth_source['server']['id'],
                'user-group-id': user_group['id'],
                'name': member_group,
            }
        )
        module_target_sat.cli.UserGroup.add_role(
            {'id': user_group['id'], 'role-id': viewer_role['id']}
        )
        user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
        result = module_target_sat.cli.Auth.with_user(
            username=ad_data['ldap_user_name'], password=ad_data['ldap_user_passwd']
        ).status()
        assert LOGEDIN_MSG.format(ad_data['ldap_user_name']) in result[0]['message']
        module_target_sat.cli.UserGroupExternal.refresh(
            {'user-group-id': user_group['id'], 'name': member_group}
        )
        user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
        list = module_target_sat.cli.Role.with_user(
            username=ad_data['ldap_user_name'], password=ad_data['ldap_user_passwd']
        ).list()
        assert len(list) > 1


@pytest.mark.run_in_one_thread
class TestIPAAuthSource:
    """Implements FreeIPA ldap auth feature tests in CLI"""

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

    @pytest.mark.tier2
    @pytest.mark.parametrize('server_name', **parametrized(generate_strings_list()))
    @pytest.mark.upgrade
    @pytest.mark.e2e
    @pytest.mark.usefixtures("ldap_tear_down")
    def test_positive_end_to_end_with_ipa(self, default_ipa_host, server_name, module_target_sat):
        """CRUD LDAP authentication with FreeIPA

        :id: 6cb54405-b579-4020-bf99-cb811a6aa28b

        :expectedresults: Whether creating/updating/deleting LDAP Auth with FreeIPA is successful.

        :parametrized: yes

        :CaseImportance: High

        """
        auth = module_target_sat.cli_factory.ldap_auth_source(
            {
                'name': server_name,
                'onthefly-register': 'true',
                'host': default_ipa_host.hostname,
                'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
                'attr-login': LDAP_ATTR['login'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': default_ipa_host.ldap_user_cn,
                'account-password': default_ipa_host.ldap_user_passwd,
                'base-dn': default_ipa_host.base_dn,
                'groups-base': default_ipa_host.group_base_dn,
            }
        )
        assert auth['server']['name'] == server_name
        assert auth['server']['server'] == default_ipa_host.hostname
        assert auth['server']['server-type'] == LDAP_SERVER_TYPE['CLI']['ipa']
        new_name = gen_string('alpha')
        module_target_sat.cli.LDAPAuthSource.update({'name': server_name, 'new-name': new_name})
        updated_auth = module_target_sat.cli.LDAPAuthSource.info({'id': auth['server']['id']})
        assert updated_auth['server']['name'] == new_name
        module_target_sat.cli.LDAPAuthSource.delete({'name': new_name})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.LDAPAuthSource.info({'name': new_name})

    @pytest.mark.tier3
    @pytest.mark.usefixtures("ldap_tear_down")
    def test_usergroup_sync_with_refresh(self, default_ipa_host, module_target_sat):
        """Verify the refresh functionality in Ldap Auth Source

        :id: c905eb80-2bd0-11ea-abc3-ddb7dbb3c930

        :expectedresults: external user-group sync works as expected as on-demand
            sync based on refresh works

        :CaseImportance: Medium
        """
        self._clean_up_previous_ldap()
        ipa_group_base_dn = default_ipa_host.group_base_dn.replace('foobargroup', 'foreman_group')
        member_username = 'foreman_test'
        member_group = 'foreman_group'
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source_name = gen_string('alpha')
        auth_source = module_target_sat.cli_factory.ldap_auth_source(
            {
                'name': auth_source_name,
                'onthefly-register': 'true',
                'usergroup-sync': 'false',
                'host': default_ipa_host.hostname,
                'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
                'attr-login': LDAP_ATTR['login'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': default_ipa_host.ldap_user_cn,
                'account-password': default_ipa_host.ldap_user_passwd,
                'base-dn': default_ipa_host.base_dn,
                'groups-base': ipa_group_base_dn,
            }
        )
        auth_source = module_target_sat.cli.LDAPAuthSource.info({'id': auth_source['server']['id']})

        # Adding User in IPA UserGroup
        default_ipa_host.add_user_to_usergroup(member_username, member_group)
        viewer_role = module_target_sat.cli.Role.info({'name': 'Viewer'})
        user_group = module_target_sat.cli_factory.usergroup()
        ext_user_group = module_target_sat.cli_factory.usergroup_external(
            {
                'auth-source-id': auth_source['server']['id'],
                'user-group-id': user_group['id'],
                'name': member_group,
            }
        )
        module_target_sat.cli.UserGroup.add_role(
            {'id': user_group['id'], 'role-id': viewer_role['id']}
        )
        assert ext_user_group['auth-source'] == auth_source['server']['name']
        user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        result = module_target_sat.cli.Auth.with_user(
            username=member_username, password=default_ipa_host.ldap_user_passwd
        ).status()
        assert LOGEDIN_MSG.format(member_username) in result[0]['message']
        with pytest.raises(CLIReturnCodeError) as error:
            module_target_sat.cli.Role.with_user(
                username=member_username, password=default_ipa_host.ldap_user_passwd
            ).list()
        assert 'Missing one of the required permissions' in error.value.message
        module_target_sat.cli.UserGroupExternal.refresh(
            {'user-group-id': user_group['id'], 'name': member_group}
        )
        list = module_target_sat.cli.Role.with_user(
            username=member_username, password=default_ipa_host.ldap_user_passwd
        ).list()
        assert len(list) > 1
        user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 1
        assert user_group['users'][0] == member_username

        # Removing User in IPA UserGroup
        default_ipa_host.remove_user_from_usergroup(member_username, member_group)
        module_target_sat.cli.UserGroupExternal.refresh(
            {'user-group-id': user_group['id'], 'name': member_group}
        )
        user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        with pytest.raises(CLIReturnCodeError) as error:
            module_target_sat.cli.Role.with_user(
                username=member_username, password=default_ipa_host.ldap_user_passwd
            ).list()
        assert 'Missing one of the required permissions' in error.value.message

    @pytest.mark.tier3
    @pytest.mark.usefixtures("ldap_tear_down")
    def test_usergroup_with_usergroup_sync(self, default_ipa_host, module_target_sat):
        """Verify the usergroup-sync functionality in Ldap Auth Source

        :id: 2b63e886-2c53-11ea-9da5-db3ae0527554

        :expectedresults: external user-group sync works as expected automatically
            based on user-sync

        :CaseImportance: Medium
        """
        self._clean_up_previous_ldap()
        ipa_group_base_dn = default_ipa_host.group_base_dn.replace('foobargroup', 'foreman_group')
        member_username = 'foreman_test'
        member_group = 'foreman_group'
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source_name = gen_string('alpha')
        auth_source = module_target_sat.cli_factory.ldap_auth_source(
            {
                'name': auth_source_name,
                'onthefly-register': 'true',
                'usergroup-sync': 'true',
                'host': default_ipa_host.hostname,
                'server-type': LDAP_SERVER_TYPE['CLI']['ipa'],
                'attr-login': LDAP_ATTR['login'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': default_ipa_host.ldap_user_cn,
                'account-password': default_ipa_host.ldap_user_passwd,
                'base-dn': default_ipa_host.base_dn,
                'groups-base': ipa_group_base_dn,
            }
        )
        auth_source = module_target_sat.cli.LDAPAuthSource.info({'id': auth_source['server']['id']})

        # Adding User in IPA UserGroup
        default_ipa_host.add_user_to_usergroup(member_username, member_group)
        viewer_role = module_target_sat.cli.Role.info({'name': 'Viewer'})
        user_group = module_target_sat.cli_factory.usergroup()
        ext_user_group = module_target_sat.cli_factory.usergroup_external(
            {
                'auth-source-id': auth_source['server']['id'],
                'user-group-id': user_group['id'],
                'name': member_group,
            }
        )
        module_target_sat.cli.UserGroup.add_role(
            {'id': user_group['id'], 'role-id': viewer_role['id']}
        )
        assert ext_user_group['auth-source'] == auth_source['server']['name']
        user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0
        result = module_target_sat.cli.Auth.with_user(
            username=member_username, password=default_ipa_host.ldap_user_passwd
        ).status()
        assert LOGEDIN_MSG.format(member_username) in result[0]['message']
        list = module_target_sat.cli.Role.with_user(
            username=member_username, password=default_ipa_host.ldap_user_passwd
        ).list()
        assert len(list) > 1
        user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 1
        assert user_group['users'][0] == member_username

        # Removing User in IPA UserGroup
        default_ipa_host.remove_user_from_usergroup(member_username, member_group)
        with pytest.raises(CLIReturnCodeError) as error:
            module_target_sat.cli.Role.with_user(
                username=member_username, password=default_ipa_host.ldap_user_passwd
            ).list()
        assert 'Missing one of the required permissions' in error.value.message
        user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
        assert len(user_group['users']) == 0


@pytest.mark.run_in_one_thread
class TestOpenLdapAuthSource:
    """Implements OpenLDAP Auth Source tests in CLI"""

    @pytest.mark.tier2
    @pytest.mark.e2e
    @pytest.mark.parametrize('server_name', **parametrized(generate_strings_list()))
    @pytest.mark.upgrade
    def test_positive_end_to_end_with_open_ldap(
        self, open_ldap_data, server_name, module_target_sat
    ):
        """CRUD LDAP Operations with OpenLDAP

        :id: f84db334-0189-11eb-846c-d46d6dd3b5b2

        :parametrized: yes

        :expectedresults: Whether creating/updating/deleting LDAP Auth with OpenLDAP is successful.

        :CaseImportance: High
        """
        auth = module_target_sat.cli_factory.ldap_auth_source(
            {
                'name': server_name,
                'onthefly-register': 'true',
                'host': open_ldap_data['ldap_hostname'],
                'server-type': LDAP_SERVER_TYPE['CLI']['posix'],
                'attr-login': LDAP_ATTR['login_ad'],
                'attr-firstname': LDAP_ATTR['firstname'],
                'attr-lastname': LDAP_ATTR['surname'],
                'attr-mail': LDAP_ATTR['mail'],
                'account': open_ldap_data['ldap_user_name'],
                'account-password': open_ldap_data['ldap_user_passwd'],
                'base-dn': open_ldap_data['base_dn'],
            }
        )
        assert auth['server']['name'] == server_name
        assert auth['server']['server'] == open_ldap_data['ldap_hostname']
        assert auth['server']['server-type'] == LDAP_SERVER_TYPE['CLI']['posix']
        new_name = gen_string('alpha')
        module_target_sat.cli.LDAPAuthSource.update({'name': server_name, 'new-name': new_name})
        updated_auth = module_target_sat.cli.LDAPAuthSource.info({'id': auth['server']['id']})
        assert updated_auth['server']['name'] == new_name
        module_target_sat.cli.LDAPAuthSource.delete({'name': new_name})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.LDAPAuthSource.info({'name': new_name})
