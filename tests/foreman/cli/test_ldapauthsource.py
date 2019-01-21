"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_ldap_auth_source
from robottelo.cli.ldapauthsource import LDAPAuthSource
from robottelo.config import settings
from robottelo.constants import LDAP_ATTR, LDAP_SERVER_TYPE
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import run_in_one_thread, skip_if_not_set, tier1, tier2, upgrade
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

        :CaseImportance: Critical
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
