"""Test class for Active Directory Feature"""
from ddt import ddt
from robottelo.config import conf
from robottelo.constants import LDAP_SERVER_TYPE, LDAP_ATTR
from robottelo.decorators import data
from robottelo.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_ldapauth
from robottelo.ui.session import Session


@ddt
class LDAPAuthSource(UITestCase):
    """Implements Active Directory feature tests in UI."""

    # TODO: handle when the ldap config is not available
    ldap_user_name = conf.properties.get('main.ldap.username')
    ldap_user_passwd = conf.properties.get('main.ldap.passwd')
    base_dn = conf.properties.get('main.ldap.basedn')
    group_base_dn = conf.properties.get('main.ldap.grpbasedn')
    ldap_hostname = conf.properties.get('main.ldap.hostname')

    @data(*generate_strings_list())
    def test_create_ldap_authsource_withad(self, server_name):
        """@Test: Create LDAP authentication with AD

        @Feature: LDAP Authentication - Active Directory - create LDAP AD

        @steps:

        1. Create a new LDAP Auth source with AD.
        2. Fill in all the fields appropriately for AD.

        @Assert: Whether creating LDAP Auth with AD is successful.

        """
        with Session(self.browser) as session:
            make_ldapauth(
                session,
                name=server_name,
                server=self.ldap_hostname,
                server_type=LDAP_SERVER_TYPE['UI']['ad'],
                login_name=LDAP_ATTR['login_ad'],
                first_name=LDAP_ATTR['firstname'],
                surname=LDAP_ATTR['surname'],
                mail=LDAP_ATTR['mail'],
                account_user=self.ldap_user_name,
                account_passwd=self.ldap_user_passwd,
                account_basedn=self.base_dn,
                account_grpbasedn=self.group_base_dn
            )
            self.assertIsNotNone(self.ldapauthsource.search(server_name))

    @data(*generate_strings_list())
    def test_delete_ldap_auth_withad(self, server_name):
        """@Test: Delete LDAP authentication with AD

        @Feature: LDAP Authentication - Active Directory - delete LDAP AD

        @steps:

        1. Delete LDAP Auth source with AD.
        2. Fill in all the fields appropriately for AD.

        @Assert: Whether deleting LDAP Auth with AD is successful.

        """
        with Session(self.browser) as session:
            make_ldapauth(
                session,
                name=server_name,
                server=self.ldap_hostname,
                server_type=LDAP_SERVER_TYPE['UI']['ad'],
                login_name=LDAP_ATTR['login_ad'],
                first_name=LDAP_ATTR['firstname'],
                surname=LDAP_ATTR['surname'],
                mail=LDAP_ATTR['mail'],
                account_user=self.ldap_user_name,
                account_passwd=self.ldap_user_passwd,
                account_basedn=self.base_dn,
                account_grpbasedn=self.group_base_dn,
            )
            self.assertIsNotNone(self.ldapauthsource.search(server_name))
            self.ldapauthsource.delete(server_name)
