# -*- encoding: utf-8 -*-
"""Test class for SSO (CLI)

@Requirement: Sso

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import stubbed, upgrade
from robottelo.test import CLITestCase


class SingleSignOnTestCase(CLITestCase):
    """Test Class for SSO CLI"""

    # Notes for SSO testing:
    # Of interest... In some testcases I've placed a few comments prefaced with
    # "devnote:" These are -- obviously -- notes from developers that might
    # help reiterate something important or a reminder of way(s) to test
    # something.

    # There may well be more cases that I have missed for this feature, and
    # possibly other LDAP types. These (in particular, the LDAP variations)
    # can be easily added later.

    @stubbed()
    @upgrade
    def test_positive_login_kerberos_user(self):
        """kerberos user can login to CLI

        @id: 59a1b463-67b3-4f18-b851-afaa3c65ccb6

        @setup: kerberos configured against foreman.

        @expectedresults: Log in to hammer cli successfully

        @caseautomation: notautomated
        """

    @stubbed()
    @upgrade
    def test_positive_login_ipa_user(self):
        """IPA user can login to CLI

        @id: cbd0df84-6a4d-4c82-bf30-cecd51f40c03

        @setup: IPA configured against foreman.

        @expectedresults: Log in to hammer cli successfully

        @caseautomation: notautomated
        """

    @stubbed()
    @upgrade
    def test_positive_login_openldap_user(self):
        """OpenLDAP user can login to CLI

        @id: de31d5eb-4e0d-495e-bf31-bc49f9d50d68

        @setup: OpenLDAP configured against foreman.

        @expectedresults: Log in to hammer cli successfully

        @caseautomation: notautomated
        """
