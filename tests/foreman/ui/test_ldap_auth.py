"""Test class for installer (UI)"""

from robottelo.decorators import skip_if_not_set, stubbed, tier3
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

        @feature: LDAP Authentication

        @setup: assure properly functioning IPA server for authentication

        @steps:
        1. Login to server with an IPA user.

        @assert: Log in to foreman UI successfully but cannot access
        functional areas of UI

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ipa_basic_roles(self):
        """Login with LDAP - IPA for user with roles/rights

        @feature: LDAP Authentication

        @setup: assure properly functioning IPA server for authentication

        @steps:
        1. Login to server with an IPA user.

        @assert: Log in to foreman UI successfully and can access appropriate
        functional areas in UI

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ipa_user_disabled(self):
        """LDAP - IPA user activity when IPA user account has been
        deleted or deactivated

        @feature: LDAP Authentication

        @steps:
        1. Login to the foreman UI.
        2. Delete or disable user on IPA server side.

        @assert: This is handled gracefully (user is logged out perhaps?)
        and no data corruption

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ad_basic_no_roles(self):
        """Login with LDAP Auth- AD for user with no roles/rights

        @feature: LDAP Authentication

        @setup: assure properly functioning AD server for authentication

        @steps:
        1. Login to server with an AD user.

        @assert: Log in to foreman UI successfully but cannot access
        functional areas of UI

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ad_basic_roles(self):
        """Login with LDAP - AD for user with roles/rights

        @feature: LDAP Authentication

        @setup: assure properly functioning AD server for authentication

        @steps:
        1. Login to server with an AD user.

        @assert: Log in to foreman UI successfully and can access appropriate
        functional areas in UI

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ad_user_disabled(self):
        """LDAP - AD user activity when AD user account has been deleted
        or deactivated

        @feature: LDAP Authentication

        @steps:
        1. Login to the Sat6 UI.
        2. Delete or disable userid on AD server side.

        @assert: This is handled gracefully (user is logged out perhaps?)
        and no data corruption

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_openldap_basic_no_roles(self):
        """Login with LDAP - RHDSLDAP that has no roles / rights

        @feature: LDAP Authentication

        @setup: assure properly functioning RHDSLDAP server for authentication

        @steps:
        1. Login to server with a RHDSLDAP user.

        @assert: Log in to foreman UI successfully but has no access to
        functional areas of UI.

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_rhdsldap_basic_roles(self):
        """Login with LDAP - RHDS LDAP for user with roles/rights
        assigned.

        @feature: LDAP Authentication

        @setup: assure properly functioning RHDS LDAP server for authentication

        @steps:
        1. Login to server with a RHDS LDAP id.

        @assert: Log in to foreman UI successfully and can access appropriate
        functional areas in UI

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_rhdsldap_user_disabled(self):
        """LDAP - RHDSLDAP user activity when RHDS ldap account has been
        deleted or deactivated

        @feature: LDAP Authentication

        @steps:
        1. Login to the foreman UI.
        2. Delete or disable userid on RHDS LDAP server side.

        @assert: This is handled gracefully (user is logged out perhaps?) and
        no data corruption

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_multiple_ldap_backends(self):
        """LDAP - multiple LDAP servers kafo instance

        @feature: LDAP Authentication

        @setup: Assure more than one ldap server backend is provided for
        sat6

        @steps:
        1. Attempt to login with a user that exists on one ldap server.
        2. Logout and attempt to login with a user that exists on other ldap
        server(s).

        @assert: Log in to foreman UI successfully for users on both LDAP
        servers.

        @status: Manual

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

        @feature: LDAP Authentication

        @setup: more than 1 ldap server backend provide for instance with

        @steps:
        1. Attempt to login with a user that exists on one ldap server.
        2. Logout and attempt to login with a user that exists on other
        ldap server(s).

        @assert: Foreman should have some method for distinguishing/specifying
        which server a user comes from.

        @status: Manual

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

        @feature: LDAP Authentication

        @steps:
        1. Try to login with ldap user "admin".

        @assert: Login from local db user "admin" overrides any ldap user
        "admin"

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_negative_ldap_server_down_before_session(self):
        """LDAP - what happens when we have an ldap server that goes
        down before logging in?

        @feature: LDAP Authentication

        @steps:
        1. Try to login with ldap user when server is non-responsive.

        @assert: UI does handles situation gracefully, perhaps informing user
        that LDAP instance is not responding

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_negative_ldap_server_down_during_session(self):
        """LDAP - what happens when we have an ldap server that goes
        down after login?

        @feature: LDAP Authentication

        @steps:
        1. Try to login with ldap user.
        2. While logged in with ldap user, disconnect access to ldap server.

        @assert: Situation is handled gracefully and without serious data
        loss on foreman server

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_usergroup_roles_read(self):
        """Group roles get pushed down to user

        @feature: LDAP Authentication

        @setup: assign roles to an LDAP UserGroup

        @steps:
        1. Login to sat6 with LDAP user that is part of aforementioned
        UserGroup.

        @assert: User has access to all functional areas that are assigned to
        aforementioned UserGroup.

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_usergroup_roles_update(self):
        """Added UserGroup roles get pushed down to user

        @feature: LDAP Authentication

        @setup: assign additional roles to an LDAP UserGroup

        @steps:
        1. Login to sat6 with LDAP user that is part of aforementioned
        UserGroup.

        @assert: User has access to all NEW functional areas that are assigned
        to aforementioned UserGroup.

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_usergroup_roles_delete(self):
        """Deleted UserGroup roles get pushed down to user

        @feature: LDAP Authentication

        @setup: delete roles from an LDAP UserGroup

        @steps:
        1. Login to sat6 with LDAP user that is part of aforementioned
        UserGroup.

        @assert: User no longer has access to all deleted functional areas
        that were assigned to aforementioned UserGroup.

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_usergroup_additional_user_roles(self):
        """Assure that user has roles/can access feature areas for
        additional roles assigned outside any roles assigned by his group

        @feature: LDAP Authentication

        @setup: Assign roles to UserGroup and users to this group;
        subsequently assign specified roles to the user(s) --
        roles that are not part of the larger UserGroup

        @steps:
        1. Login to sat6 with LDAP user and attempt to access areas assigned
        specifically to user.

        @assert: User can access not only those feature areas in his
        UserGroup but those additional feature areas / roles assigned
        specifically to user

        @status: Manual

        """

    @skip_if_not_set('ldap')
    @stubbed()
    @tier3
    def test_positive_ldap_auth_usergroup_user_add(self):
        """New user added to UserGroup inherits roles

        @feature: LDAP Authentication

        @setup: UserGroup with specified roles.

        @steps:
        1. Login to sat6 with LDAP user that is not part of UserGroup.
        2. On LDAP server, assign user to aforementioned UserGroup.
        3. Attempt once more to sign in with user.

        @assert: User can access feature areas as defined by roles in the
        UserGroup of which he is a part.

        @status: Manual

        """
