"""Test for User Group related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE


class TestUserGroupMembership:
    """
    User-group membership should exist after upgrade.
    """

    @pytest.mark.pre_upgrade
    def test_pre_create_user_group_with_ldap_user(self, ad_data, target_sat, save_test_data):
        """Create User-group in pre_upgrade version.

        :id: preupgrade-4b11d883-f523-4f38-b65a-650ecd90335c

        :steps:
            1. Create ldap auth pre upgrade.
            2. Login with ldap User in satellite and logout.
            3. Create external user_group viewer role and synced ldap user gets the role.

        :expectedresults: The usergroup, with ldap user as member, should be created successfully.
        """
        ad_data = ad_data()
        member_group = 'foobargroup'
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source = target_sat.cli_factory.make_ldap_auth_source(
            {
                'name': gen_string('alpha'),
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
            }
        )
        viewer_role = target_sat.cli.Role.info({'name': 'Viewer'})
        user_group = target_sat.cli_factory.make_usergroup()
        target_sat.cli_factory.make_usergroup_external(
            {
                'auth-source-id': auth_source['server']['id'],
                'user-group-id': user_group['id'],
                'name': member_group,
            }
        )
        target_sat.cli.UserGroup.add_role({'id': user_group['id'], 'role-id': viewer_role['id']})
        user_group = target_sat.cli.UserGroup.info({'id': user_group['id']})
        result = target_sat.cli.Auth.with_user(
            username=ad_data['ldap_user_name'], password=ad_data['ldap_user_passwd']
        ).status()
        assert LOGEDIN_MSG.format(ad_data['ldap_user_name']) in result[0]['message']
        target_sat.cli.UserGroupExternal.refresh(
            {'user-group-id': user_group['id'], 'name': member_group}
        )
        role_list = target_sat.cli.Role.with_user(
            username=ad_data['ldap_user_name'], password=ad_data['ldap_user_passwd']
        ).list()
        assert len(role_list) > 1
        save_test_data(
            {
                'user_group_name': user_group['name'],
                'auth_source_name': auth_source['server']['name'],
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_create_user_group_with_ldap_user)
    def test_post_verify_user_group_membership(
        self, request, ad_data, target_sat, pre_upgrade_data
    ):
        """After upgrade, check the LDAP user created before the upgrade still exists and its
         update functionality should work.

        :id: postupgrade-7545fc6a-bd57-4403-90c8-c68a7a3b5bca

        :steps:
            1. verify ldap user(created before upgrade) is part of user group.
            2. Update ldap auth.

        :expectedresults: After upgrade, user group membership should remain the same and LDAP
        auth update should work.
        """
        ad_data = ad_data()
        user_group = target_sat.api.UserGroup().search(
            query={'search': f'name={pre_upgrade_data["user_group_name"]}'}
        )
        auth_source = target_sat.api.AuthSourceLDAP().search(
            query={'search': f'name={pre_upgrade_data["auth_source_name"]}'}
        )[0]
        request.addfinalizer(auth_source.delete)
        request.addfinalizer(user_group[0].delete)
        user = target_sat.api.User().search(query={'search': f'login={ad_data["ldap_user_name"]}'})[
            0
        ]
        assert user.read().id == user_group[0].read().user[0].id
        request.addfinalizer(user.delete)
        role_list = target_sat.cli.Role.with_user(
            username=ad_data['ldap_user_name'], password=ad_data['ldap_user_passwd']
        ).list()
        assert len(role_list) > 1
