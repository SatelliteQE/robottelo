# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for installer (UI)
"""
import unittest
from tests.ui.baseui import BaseUI


class TestSSOUI(BaseUI):

# Notes for SSO testing:
# Of interest... In some test cases I've placed a few comments prefaced with
# "devnote:" These are -- obviously -- notes from developers that might help
# reiterate something important or a reminder of way(s) to test something.

# There may well be more cases that I have missed for this feature, and
# possibly other LDAP types. These (in particular, the LDAP variations)
# can be easily added later.

    def test_sso_kerberos_basic_no_roles(self):
        """
        @feature: SSO
        @test: SSO - kerberos login (basic) that has no rights
        @setup: assure SSO with kerberos is set up.
        @steps:
        1.  attempt to login using a kerberos ID
        @assert: Log in to foreman UI successfully but cannot access anything
        useful in UI
        @status: Manual
        """

    def test_sso_kerberos_basic_roles(self):
        """
        @feature: SSO
        @test: SSO - kerberos login (basic) that has rights assigned
        @setup: assure SSO with kerberos is set up.
        @steps:
        1.  attempt to login using a kerberos ID
        @assert: Log in to foreman UI successfully and can access functional
        areas in UI
        @status: Manual
        """

    def test_sso_kerberos_user_disabled(self):
        """
        @feature: SSO
        @test: Kerberos user activity when kerb account has been deleted or
        deactivated
        @steps:
        1.  Login to the foreman UI
        2. Delete or disable userid on kerb server side
        @assert: This is handled gracefully (user is logged out perhaps?)
        and no data corruption
        @status: Manual
        """

    def test_sso_ipa_basic_no_roles(self):
        """
        @feature: SSO
        @test: Login with LDAP - IPA for user with no roles/rights
        @setup: assure properly functioning IPA server for authentication
        @steps:
        1. Login to server with an IPA id
        @assert: Log in to foreman UI successfully but cannot access
        functional areas of UI
        @status: Manual
        """

    def test_sso_ipa_basic_roles(self):
        """
        @feature: SSO
        @test: Login with LDAP - IPA for user with roles/rights
        @setup: assure properly functioning IPA server for authentication
        @steps:
        1. Login to server with an IPA id
        @assert: Log in to foreman UI successfully and can access appropriate
        functional areas in UI
        @status: Manual
        """

    def test_sso_ipa_user_disabled(self):
        """
        @feature: SSO
        @test: LDAP - IPA user activity when IPA account has been deleted
        or deactivated
        @steps:
        1.  Login to the foreman UI
        2. Delete or disable userid on IPA server side
        @assert: This is handled gracefully (user is logged out perhaps?)
        and no data corruption
        @status: Manual
        """

    def test_sso_openldap_basic_no_roles(self):
        """
        @feature: SSO
        @test: Login with LDAP - OpenLDAP that has no roles / rights
        @setup: assure properly functioning OpenLDAP server for authentication
        @steps:
        1. Login to server with an OpenLDAP id
        @assert: Log in to foreman UI successfully but has no access to
        functional areas of UI.
        @status: Manual
        """

    def test_sso_openldap_basic_roles(self):
        """
        @feature: SSO
        @test: Login with LDAP - OpenLDAP for user with roles/rights assigned
        @setup: assure properly functioning OpenLDAP server for authentication
        @steps:
        1. Login to server with an OpenLDAP id
        @assert: Log in to foreman UI successfully and can access appropriate
        functional areas in UI
        @status: Manual
        """

    def test_sso_openldap_user_disabled(self):
        """
        @feature: SSO
        @test: LDAP - OpenLDAP user activity when OpenLDAP account has been
        deleted or deactivated
        @steps:
        1.  Login to the foreman UI
        2. Delete or disable userid on OpenLDAP server side
        @assert: This is handled gracefully (user is logged out perhaps?) and
        no data corruption
        @status: Manual
        """

    def test_sso_multiple_ldap_backends(self):
        """
        @feature: SSO
        @test: SSO - multiple LDAP servers
        @setup: assure more than one ldap server backend is provide for sat6 /
        kafo instance
        @steps:
        1. Attempt to login with a user that exists on one ldap server
        2. Logout and attempt to login with a user that exists on other ldap
        server(s)
        @assert: Log in to foreman UI successfully for users on both LDAP
        servers.
        @status: Manual
        """

    def test_sso_multiple_ldap_namespace_collision(self):
        # devnote:
        # users have auth_source which could distinguish them, but validation
        # would fail atm
        """
        @feature: SSO
        @test: SSO - multiple LDAP servers
        @setup: more than 1 ldap server backend provide for instance with
        colliding namespace (i.e "jsmith")
        @steps:
        1. Attempt to login with a user that exists on one ldap server
        2. Logout and attempt to login with a user that exists on other
        ldap server(s)
        @assert: Foreman should have some method for distinguishing/specifying
        which server a user comes from.
        @status: Manual
        """

    def test_sso_ldap_user_named_admin(self):
        # devnote:  
        # shouldn't be a problem since admin from internal DB will be used at
        # first, worth of testing thou, however if authentication is done by
        # external system (IPA, ...) which can create users in foreman,
        # I'm not sure about result
        """
        @feature: SSO
        @test: SSO - what happens when we have an ldap user named "admin"?
        @steps:
        1. Try to login with ldap user "admin"
        @assert: Login from local db user "admin" overrides any ldap user "admin"
        @status: Manual
        """

    def test_sso_ldap_server_down_before_session(self):
        """
        @feature: SSO
        @test: SSO - what happens when we have an ldap server that goes down
        before logging in?
        @steps:
        1. Try to login with ldap user when server is non-responsive
        @assert: UI does handles situation gracefully, perhaps informing user
        that LDAP instance is not responding
        @status: Manual
        """

    def test_sso_ldap_server_down_during_session(self):
        """
        @feature: SSO
        @test: SSO - what happens when we have an ldap server that goes down
        after login?
        @steps:
        1. Try to login with ldap user
        2. While logged in with ldap user, disconnect access to ldap server.
        @assert: Situation is handled gracefully and without serious data
        loss on foreman server
        @status: Manual
        """

    def test_sso_usergroup_roles_read(self):
        """
        @feature: SSO
        @test: Usergroups: group roles get pushed down to user
        @setup: assign roles to an LDAP usergroup
        @steps:
        1.  Login to foreman with LDAP user that is part of aforementioned
        usergroup
        @assert: User has access to all functional areas that are assigned to
        aforementioned usergroup.
        @status: Manual
        """

    def test_sso_usergroup_roles_update(self):
        """
        @feature: SSO
        @test: Usergroups: added usergroup roles get pushed down to user
        @setup: assign additional roles to an LDAP usergroup
        @steps:
        1.  Login to foreman with LDAP user that is part of aforementioned
        usergroup
        @assert: User has access to all NEW functional areas that are assigned
        to aforementioned usergroup.
        @status: Manual
        """

    def test_sso_usergroup_roles_delete(self):
        """
        @feature: SSO
        @test: Usergroups: deleted usergroup roles get pushed down to user
        @setup: delete roles from an LDAP usergroup
        @steps:
        1.  Login to foreman with LDAP user that is part of aforementioned
        usergroup
        @assert: User no longer has access to all deleted functional areas
        that were assigned to aforementioned usergroup.
        @status: Manual
        """

    def test_sso_usergroup_additional_user_roles(self):
        """
        @feature: SSO
        @test: Assure that user has roles/can access feature areas for
        additional roles assigned outside any roles assigned by his group
        @setup: Assign roles to usergroup and users to this group;
        subsequently assign specified roles to the user(s) --
        roles that are not part of the larger usergroup
        @steps:
        1.  Login to foreman with LDAP user and attempt to access areas
         assigned specifically to user.
        @assert: User can access not only those feature areas in his
        usergroup but those additional feature areas / roles assigned
        specifically to user
        @status: Manual
        """

    def test_sso_usergroup_user_add(self):
        """
        @feature: SSO
        @test: Usergroups: new user added to usegroup inherits roles
        @setup: usergroup with specified roles.
        @steps:
        1.  Login to foreman with LDAP user that is not part of usergroup.
        2.  On LDAP server, assign user to aforementioned usergroup.
        3.  Attempt once more to sign in with user
        @assert: User can access feature areas as defined by roles in the
        usergroup of which he is a part.
        @status: Manual
        """