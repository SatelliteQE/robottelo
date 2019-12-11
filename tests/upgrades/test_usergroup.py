"""Test for User Group related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from nailgun.config import ServerConfig
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.constants import LDAP_ATTR, LDAP_SERVER_TYPE
from robottelo.test import APITestCase
from upgrade_tests import post_upgrade, pre_upgrade


class scenario_positive_verify_usergroup_membership(APITestCase):
    """Usergroup membership should not lost post upgrade.

    :id: 0bcaa050-7740-4ef5-ba77-b706b6380113

    :steps:

        1. Create ldap auth pre upgrade.
        2. Login with ldap User in satellite and logout.
        3. Create usergroup and assign ldap user to it.
        4. Perform upgrade.
        5. After upgrade verify ldap user is part of user group.

    :expectedresults: Usergroup membership should not lost post upgrade.

    :BZ: 1753907
    """
    @classmethod
    def setUpClass(cls):
        cls.server_name = 'preupgrade_ldap_ad'
        cls.preupgrade_usergroup = 'preupgrade_usergroup_ad'
        cls.ldap_user_name = settings.ldap.username
        cls.ldap_user_passwd = settings.ldap.password
        cls.base_dn = settings.ldap.basedn
        cls.group_base_dn = settings.ldap.grpbasedn
        cls.ldap_hostname = settings.ldap.hostname
        cls.sat_url = 'https://{}'.format(settings.server.hostname)

    @pre_upgrade
    def test_pre_create_usergroup_with_ldap_user(self):
        """Create Usergroup in preupgrade version.

        :steps:
            1. Create ldap auth pre upgrade.
            2. Login with ldap User in satellite and logout.
            3. Create usergroup and assign ldap user to it.

        :expectedresults: The usergroup, with ldap user as member, should be created successfully.
        """
        authsource = entities.AuthSourceLDAP(
            onthefly_register=True,
            account=self.ldap_user_name,
            account_password=self.ldap_user_passwd,
            base_dn=self.base_dn,
            groups_base=self.group_base_dn,
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login_ad'],
            server_type=LDAP_SERVER_TYPE['API']['ad'],
            attr_mail=LDAP_ATTR['mail'],
            name=self.server_name,
            host=self.ldap_hostname,
            tls=False,
            port='389',
        ).create()
        self.assertEqual(authsource.name, self.server_name)
        sc = ServerConfig(
            auth=(self.ldap_user_name, self.ldap_user_passwd),
            url=self.sat_url,
            verify=False
        )
        with self.assertRaises(HTTPError):
            entities.User(sc).search()
        user_group = entities.UserGroup(name=self.preupgrade_usergroup).create()
        user = entities.User().search(query={'search': u'login={}'.format(
            self.ldap_user_name)})[0]
        user_group.user = [user]
        user_group = user_group.update(['user'])
        self.assertEqual(user.login, user_group.user[0].read().login)

    @post_upgrade
    def test_post_verify_usergroup_membership(self):
        """Verify ldap user is part of user group.

        :steps:
            1. Postupgrade, verify ldap user is part of user group.
            2. Update ldap auth postupgrade.

        :expectedresults: Usergroup membership should not lost post upgrade.
        """
        user_group = entities.UserGroup().search(query={'search': u'name={}'.format(
            self.preupgrade_usergroup)})[0]
        user = entities.User().search(query={'search': u'login={}'.format(self.ldap_user_name)})[0]
        self.assertEqual(user.read().id, user_group.read().user[0].id)
