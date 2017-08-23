# -*- encoding: utf-8 -*-
"""Test class for SSO (UI)

:Requirement: Sso

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import stubbed, tier3, upgrade
from robottelo.test import UITestCase


class SingleSignOnTestCase(UITestCase):
    """Implements SSO tests in UI"""
    # Notes for SSO testing:
    # Of interest... In some test cases I've placed a few comments prefaced
    # with "devnote:" These are -- obviously -- notes from developers that
    # might help reiterate something important or a reminder of way(s) to test
    # something.

    # There may well be more cases that I have missed for this feature, and
    # possibly other LDAP types. These (in particular, the LDAP variations)
    # can be easily added later.

    # What is SSO?
    # Once (IPA or AD) user logs in to linux or windows client which is
    # IPA/AD enrolled, there should be no need for the user to again
    # authenticate at the Sat61 WebUI Login form with (IPA or AD user) login
    # details. Instead the IPA or AD user should be able to simply log-in to
    # the Sat61 WebUI automatically upon accessing the sat61 URL.

    # More detailed information at:
    # External authentication:
    # http://theforeman.org/manuals/1.8/index.html#5.7ExternalAuthentication
    # LDAP authentication:
    # http://theforeman.org/manuals/1.8/index.html#4.1.1LDAPAuthentication

    @stubbed()
    @tier3
    def test_positive_sso_kerberos_basic_no_roles(self):
        """SSO - kerberos (IdM or AD) login (basic) that has no roles

        :id: c271d9fd-7528-4b19-b5c6-e9c0148c2047

        :setup: Assure SSO with kerberos (IdM or AD) is set up.

        :steps:
            1. Login using a kerberos (IdM or AD) ID to the client
            2. Login to the Web-UI should be automatic without the need to fill
                in the form.

        :expectedresults: Log in to sat6 UI successfully but cannot access
            anything useful in UI

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_sso_kerberos_basic_roles(self):
        """SSO - kerberos (IdM or AD) login (basic) that has roles
        assigned.

        :id: df55a0e7-1387-4ea5-9b2f-27836dd4815e

        :setup: Assure SSO with kerberos (IdM or AD) is set up.

        :steps:
            1. Login using a kerberos (IdM or AD) ID to the client
            2. Login to the Web-UI should be automatic without the need to fill
                in the form.

        :expectedresults: Log in to sat6 UI successfully and can access
            functional areas in UI

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_sso_kerberos_user_disabled(self):
        """Kerberos (IdM or AD) user activity when kerb (IdM or AD)
        account has been deleted or deactivated.

        :id: ee838e76-2522-470e-ae70-f22d845e683e

        :steps:
            1. Login to the foreman UI
            2. Delete or disable userid on IdM server or AD side.

        :expectedresults: This is handled gracefully (user is logged out
            perhaps?) and no data corruption

        :caseautomation: notautomated

        :CaseLevel: System
        """
