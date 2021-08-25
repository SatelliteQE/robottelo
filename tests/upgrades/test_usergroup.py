"""Test for User Group related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Assignee: dsynk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from nailgun.config import ServerConfig
from requests.exceptions import HTTPError
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade

from robottelo.config import settings
from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE


class TestUserGroupMembership:
    """
    Usergroup membership should exist after upgrade.
    """

    @pre_upgrade
    def test_pre_create_usergroup_with_ldap_user(self, request, default_sat):
        """Create Usergroup in preupgrade version.

        :id: preupgrade-4b11d883-f523-4f38-b65a-650ecd90335c

        :steps:
            1. Create ldap auth pre upgrade.
            2. Login with ldap User in satellite and logout.
            3. Create usergroup and assign ldap user to it.

        :expectedresults: The usergroup, with ldap user as member, should be created successfully.
        """
        authsource = default_sat.api.AuthSourceLDAP(
            onthefly_register=True,
            account=settings.ldap.username,
            account_password=settings.ldap.password,
            base_dn=settings.ldap.basedn,
            groups_base=settings.ldap.grpbasedn,
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login_ad'],
            server_type=LDAP_SERVER_TYPE['API']['ad'],
            attr_mail=LDAP_ATTR['mail'],
            name=request.node.name + "_server",
            host=settings.ldap.hostname,
            tls=False,
            port='389',
        ).create()
        assert authsource.name == request.node.name + "_server"
        sc = ServerConfig(
            auth=(settings.ldap.username, settings.ldap.password),
            url=default_sat.url,
            verify=False,
        )

        with pytest.raises(HTTPError):
            entities.User(sc).search()
        user_group = default_sat.api.UserGroup(name=request.node.name + "_user_group").create()
        user = default_sat.api.User().search(query={'search': f'login={settings.ldap.username}'})[0]
        user_group.user = [user]
        user_group = user_group.update(['user'])
        assert user.login == user_group.user[0].read().login

    @post_upgrade(depend_on=test_pre_create_usergroup_with_ldap_user)
    def test_post_verify_usergroup_membership(self, request, dependent_scenario_name):
        """After upgrade, check the LDAP user created before the upgrade still exists and its
         update functionality should work.

        :id: postupgrade-7545fc6a-bd57-4403-90c8-c68a7a3b5bca

        :steps:
            1. verify ldap user(created before upgrade) is part of user group.
            2. Update ldap auth.

        :expectedresults: After upgrade, user group membership should remain the same and LDAP
        auth update should work.
        """
        pre_test_name = dependent_scenario_name
        user_group = entities.UserGroup().search(
            query={'search': f'name={pre_test_name}_user_group'}
        )
        authsource = entities.AuthSourceLDAP().search(
            query={'search': f'name={pre_test_name}_server'}
        )[0]
        request.addfinalizer(authsource.delete)
        request.addfinalizer(user_group[0].delete)
        user = entities.User().search(query={'search': f'login={settings.ldap.username}'})[0]
        request.addfinalizer(user.delete)
        assert user.read().id == user_group[0].read().user[0].id
