"""Test class for Ldapauthsource Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.constants import LDAP_ATTR, LDAP_SERVER_TYPE
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import skip_if_not_set, tier2, upgrade
from robottelo.test import APITestCase


class LDAPAuthSourceTestCase(APITestCase):
    """Implements LDAP authentication with AD feature tests in API"""

    @classmethod
    @skip_if_not_set('ldap')
    def setUpClass(cls):
        """Fetch necessary properties from settings which can be re-used in
        tests.
        """
        super(LDAPAuthSourceTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()
        cls.ldap_user_name = settings.ldap.username
        cls.ldap_user_passwd = settings.ldap.password
        cls.base_dn = settings.ldap.basedn
        cls.group_base_dn = settings.ldap.grpbasedn
        cls.ldap_hostname = settings.ldap.hostname

    @tier2
    @upgrade
    def test_positive_endtoend_withad(self):
        """Create/update/delete LDAP authentication with AD using names of different types

        :id: e3607c97-7c48-4cf6-b119-2bfd895d9325

        :expectedresults: Whether creating/updating/deleting LDAP Auth with AD is successful.

        :CaseImportance: Critical
        """
        for server_name in generate_strings_list():
            with self.subTest(server_name):
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
                    name=server_name,
                    host=self.ldap_hostname,
                    tls=False,
                    port='389',
                    location=[self.loc],
                    organization=[self.org],
                ).create()
                self.assertEqual(authsource.name, server_name)
                for new_name in generate_strings_list():
                    with self.subTest(new_name):
                        authsource.name = new_name
                        authsource = authsource.update(['name'])
                        self.assertEqual(authsource.name, new_name)
                authsource.delete()
                with self.assertRaises(HTTPError):
                    authsource.read()


class IPAAuthSourceTestCase(APITestCase):
    """Implements LDAP authentication with IPA feature tests in API"""

    @classmethod
    @skip_if_not_set('ipa')
    def setUpClass(cls):
        """Fetch necessary properties from settings which can be re-used in
        tests.
        """
        super(IPAAuthSourceTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()
        cls.ldap_ipa_user_name = settings.ipa.username_ipa
        cls.ldap_ipa_user_passwd = settings.ipa.password_ipa
        cls.ipa_base_dn = settings.ipa.basedn_ipa
        cls.ipa_group_base_dn = settings.ipa.grpbasedn_ipa
        cls.ldap_ipa_hostname = settings.ipa.hostname_ipa

    @tier2
    @upgrade
    def test_positive_endtoend_withipa(self):
        """Create/update/delete LDAP authentication with FreeIPA using names of different types

        :id: c17b39ee-922b-47d9-8db3-69639d2a77d0

        :expectedresults: Whether creating/updating/deleting LDAP Auth with FreeIPA is successful.

        :CaseImportance: Critical
        """
        for server_name in generate_strings_list():
            with self.subTest(server_name):
                authsource = entities.AuthSourceLDAP(
                    onthefly_register=True,
                    account=self.ldap_ipa_user_name,
                    account_password=self.ldap_ipa_user_passwd,
                    base_dn=self.ipa_base_dn,
                    groups_base=self.ipa_group_base_dn,
                    attr_firstname=LDAP_ATTR['firstname'],
                    attr_lastname=LDAP_ATTR['surname'],
                    attr_login=LDAP_ATTR['login'],
                    server_type=LDAP_SERVER_TYPE['API']['ipa'],
                    attr_mail=LDAP_ATTR['mail'],
                    name=server_name,
                    host=self.ldap_ipa_hostname,
                    tls=False,
                    port='389',
                    location=[self.loc],
                    organization=[self.org],
                ).create()
                self.assertEqual(authsource.name, server_name)
                for new_name in generate_strings_list():
                    with self.subTest(new_name):
                        authsource.name = new_name
                        authsource = authsource.update(['name'])
                        self.assertEqual(authsource.name, new_name)
                authsource.delete()
                with self.assertRaises(HTTPError):
                    authsource.read()
