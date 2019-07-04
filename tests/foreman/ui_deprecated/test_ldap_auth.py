"""Test class for installer (UI)

:Requirement: Ldap Auth

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import (
    skip_if_not_set,
    stubbed,
    tier1,
    tier3,
    upgrade
)
from robottelo.test import UITestCase


class LDAPAuthTestCase(UITestCase):
    """Implements ldap tests in UI"""
    # Notes for SSO testing:
    # Of interest... In some test cases I've placed a few comments prefaced
    # with "devnote:" These are -- obviously -- notes from developers that
    # might help reiterate something important or a reminder of way(s) to test
    # something.

    # There may well be more cases that I have missed for this feature, and
    # possibly other LDAP types. These (in particular, the LDAP variations)
    # can be easily added later.

    # More detailed information at:
    # LDAP authentication:
    # http://theforeman.org/manuals/1.8/index.html#4.1.1LDAPAuthentication
    # LDAP Auth testing involves testing with RHDS(389), IdM(IPA) and AD ldap.
    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ipa_basic_no_roles(self):
        """Login with LDAP Auth- IPA for user with no roles/rights

        :id: e742a9ff-f41b-4fac-b277-b5ab9c9b346f

        :setup: assure properly functioning IPA server for authentication

        :steps: Login to server with an IPA user.

        :expectedresults: Log in to foreman UI successfully but cannot access
            functional areas of UI

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_ipa_basic_roles(self):
        """Login with LDAP - IPA for user with roles/rights

        :id: e7c67103-b863-4576-8d89-d35fa69cc0eb

        :setup: assure properly functioning IPA server for authentication

        :steps: Login to server with an IPA user.

        :expectedresults: Log in to foreman UI successfully and can access
            appropriate functional areas in UI

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ipa_user_disabled(self):
        """LDAP - IPA user activity when IPA user account has been
        deleted or deactivated

        :id: dac8b17a-6644-41f8-9252-c13eb7abe86a

        :steps:
            1. Login to the foreman UI.
            2. Delete or disable user on IPA server side.

        :expectedresults: This is handled gracefully (user is logged out
            perhaps?) and no data corruption

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ad_user_disabled(self):
        """LDAP - AD user activity when AD user account has been deleted
        or deactivated

        :id: a11dfd8e-9935-474b-9374-c7d8824dcf58

        :steps:
            1. Login to the Sat6 UI.
            2. Delete or disable userid on AD server side.

        :expectedresults: This is handled gracefully (user is logged out
            perhaps?) and no data corruption

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_openldap_basic_no_roles(self):
        """Login with LDAP - RHDSLDAP that has no roles / rights

        :id: 24ba9b67-faf5-4abc-a835-2d3ce6ff86cf

        :setup: assure properly functioning RHDSLDAP server for authentication

        :steps: Login to server with a RHDSLDAP user.

        :expectedresults: Log in to foreman UI successfully but has no access
            to functional areas of UI.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_rhdsldap_basic_roles(self):
        """Login with LDAP - RHDS LDAP for user with roles/rights
        assigned.

        :id: fe3ca8b9-470d-4d42-9a3e-7ad6b0ee1783

        :setup: assure properly functioning RHDS LDAP server for authentication

        :steps: Login to server with a RHDS LDAP id.

        :expectedresults: Log in to foreman UI successfully and can access
            appropriate functional areas in UI

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_rhdsldap_user_disabled(self):
        """LDAP - RHDSLDAP user activity when RHDS ldap account has been
        deleted or deactivated

        :id: ec366106-58bd-4904-8014-965506767ea2

        :steps:
            1. Login to the foreman UI.
            2. Delete or disable userid on RHDS LDAP server side.

        :expectedresults: This is handled gracefully (user is logged out
            perhaps?) and no data corruption

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_multiple_ldap_backends(self):
        """LDAP - multiple LDAP servers kafo instance

        :id: fc23ec1b-c637-435c-aa85-28078470b311

        :setup: Assure more than one ldap server backend is provided for sat6

        :steps:
            1. Attempt to login with a user that exists on one ldap server.
            2. Logout and attempt to login with a user that exists on other
                ldap server(s).

        :expectedresults: Log in to foreman UI successfully for users on both
            LDAP servers.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_negative_multiple_ldap_namespaces_collision(self):
        # devnote:
        # users have auth_source which could distinguish them, but validation
        # would fail atm
        """LDAP - multiple LDAP servers colliding namespace
        (e.g "jsmith")

        :id: 936cd280-22de-47c3-b17d-aaffb7bf7c49

        :setup: more than 1 ldap server backend provide for instance with

        :steps:
            1. Attempt to login with a user that exists on one ldap server.
            2. Logout and attempt to login with a user that exists on other
                ldap server(s).

        :expectedresults: Foreman should have some method for
            distinguishing/specifying which server a user comes from.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ldap_user_named_admin(self):
        # devnote:
        # shouldn't be a problem since admin from internal DB will be used at
        # first, worth of testing thou, however if authentication is done by
        # external system (IPA, ...) which can create users in foreman,
        # I'm not sure about result
        """LDAP - what happens when we have an ldap user named "admin"?

        :id: 7dd6fef2-6813-4aa2-b8ba-98d99e92446d

        :steps: Try to login with ldap user "admin".

        :expectedresults: Login from local db user "admin" overrides any ldap
            user "admin"

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_negative_ldap_server_down_before_session(self):
        """LDAP - what happens when we have an ldap server that goes
        down before logging in?

        :id: bc466317-6c7f-4765-b11f-9428e687c6da

        :steps: Try to login with ldap user when server is non-responsive.

        :expectedresults: UI does handles situation gracefully, perhaps
            informing user that LDAP instance is not responding

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_negative_ldap_server_down_during_session(self):
        """LDAP - what happens when we have an ldap server that goes
        down after login?

        :id: de3e7466-b22f-416d-ac68-458d55c98390

        :steps:
            1. Try to login with ldap user.
            2. While logged in with ldap user, disconnect access to ldap
                server.

        :expectedresults: Situation is handled gracefully and without serious
            data loss on foreman server

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_usergroup_roles_read(self):
        """Group roles get pushed down to user

        :id: 95fa0fd9-a5b7-42dc-85fa-7e573e5d34a2

        :setup: assign roles to an LDAP UserGroup

        :steps: Login to sat6 with LDAP user that is part of aforementioned
            UserGroup.

        :expectedresults: User has access to all functional areas that are
            assigned to aforementioned UserGroup.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_usergroup_roles_update(self):
        """Added UserGroup roles get pushed down to user

        :id: e1d93ae4-cbd5-4d2c-b2b9-abc4ae1813c7

        :setup: assign additional roles to an LDAP UserGroup

        :steps: Login to sat6 with LDAP user that is part of aforementioned
            UserGroup.

        :expectedresults: User has access to all NEW functional areas that are
            assigned to aforementioned UserGroup.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_usergroup_roles_delete(self):
        """Deleted UserGroup roles get pushed down to user

        :id: 149e0faf-48c3-4184-adcb-a1e55fe5d953

        :setup: delete roles from an LDAP UserGroup

        :steps: Login to sat6 with LDAP user that is part of aforementioned
            UserGroup.

        :expectedresults: User no longer has access to all deleted functional
            areas that were assigned to aforementioned UserGroup.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_usergroup_additional_user_roles(self):
        """Assure that user has roles/can access feature areas for
        additional roles assigned outside any roles assigned by his group

        :id: 52a2a22f-4862-4cdf-986e-cff18bab08fd

        :setup: Assign roles to UserGroup and users to this group; subsequently
            assign specified roles to the user(s) -- roles that are not part of
            the larger UserGroup

        :steps: Login to sat6 with LDAP user and attempt to access areas
            assigned specifically to user.

        :expectedresults: User can access not only those feature areas in his
            UserGroup but those additional feature areas / roles assigned
            specifically to user

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ldap_auth_usergroup_user_add(self):
        """New user added to UserGroup inherits roles

        :id: 9df694d4-7fa5-4883-ae17-b996c2734f41

        :setup: UserGroup with specified roles.

        :steps:
            1. Login to sat6 with LDAP user that is not part of UserGroup.
            2. On LDAP server, assign user to aforementioned UserGroup.
            3. Attempt once more to sign in with user.

        :expectedresults: User can access feature areas as defined by roles in
            the UserGroup of which he is a part.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier1
    def test_positive_ipa_basic_roles_with_context(self):
        """Login with LDAP - IPA user with org and loc context set.

        :id: 03f75f54-3c60-4b05-b692-d3796ed46796

        :setup:
            1. Assure properly functioning IPA server for authentication.

        :steps:
            1. Ensure the LDAP - IPA Auth source is created with org and loc.
            2. Provide all the values needed in the fields of LDAP Auth Source.
            3. Login to sat6 with IPA User

        :expectedresults: Log in to UI successfully and can access
            appropriate functional areas in UI, with the org and loc context
            set.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier1
    def test_positive_ad_basic_roles_with_context(self):
        """Login with LDAP - AD user with org and loc context set.

        :id: 36447f1f-6fd9-4858-bf98-0022b79e95b4

        :setup:
            1. Assure properly functioning AD server for authentication.

        :steps:
            1. Ensure the LDAP - AD Auth source is created with org and loc.
            2. Provide all the values needed in the fields of LDAP Auth Source.
            3. Login to sat6 with IPA User

        :expectedresults: Log in to UI successfully and can access
            appropriate functional areas in UI, with the org and loc context
            set.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier1
    def test_positive_ad_with_context_multi_org_loc(self):
        """Login with LDAP - AD user with org and loc context set from
           multi org and loc stuff.

        :id: d1d7d55b-617f-4798-a070-2bf02c606ef5

        :setup:
            1. Assure properly functioning AD server for authentication.

        :steps:
            1. Create and/or ensure there are multiple organizations and
               locations.
            2. Ensure the LDAP - AD Auth source is created with org and loc.
            3. Provide all the values needed in the fields of LDAP Auth Source
               locations.
            4. Login to sat6 with AD User

        :expectedresults: Log in to UI successfully and can access
            appropriate functional areas in UI, with the ability to select
            org and loc context from the list.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier1
    def test_positive_ad_with_context_change_org_loc(self):
        """Login with LDAP - AD user with updated org and loc context
           from that set in Auth source.

        :id: 58039aaa-d65c-45ea-8a63-16e3cbb702d7

        :setup:
            1. Assure properly functioning AD server for authentication.

        :steps:
            1. Create and/or ensure there are multiple organizations and
               locations.
            2. Ensure the LDAP - AD Auth source is created with org and loc.
            3. Provide all the values needed in the fields of LDAP Auth Source
               locations.
            4. Login to sat6 with AD User
            5. Login back as Admin user and change the default org and loc
               for the AD user.
            6. Login to sat6 with AD User.

        :expectedresults: Log in to UI successfully and can access
            appropriate functional areas in UI, with the org and
            loc context, which was overriden.

        :CaseAutomation: notautomated
        """
