"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.cli.factory import make_ldap_auth_source
from robottelo.config import settings
from robottelo.constants import LDAP_ATTR, LDAP_SERVER_TYPE
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import skip_if_not_set, tier1, upgrade
from robottelo.test import CLITestCase


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
        """Create LDAP authentication with AD using names of different types

        :id: 093f6abc-91e7-4449-b484-71e4a14ac808

        :expectedresults: Whether creating LDAP Auth with AD is successful.

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
