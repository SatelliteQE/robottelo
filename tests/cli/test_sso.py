# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for SSO (CLI)
"""
from basecli import BaseCLI
import unittest

class TestSSOCLI(BaseCLI):

# Notes for SSO testing:
# Of interest... In some testcases I've placed a few comments prefaced with
# "devnote:" These are -- obviously -- notes from developers that might help
# reiterate something important or a reminder of way(s) to test something.

# There may well be more cases that I have missed for this feature, and
# possibly other LDAP types. These (in particular, the LDAP variations)
# can be easily added later.

    def test_sso_kerberos_cli(self):
        """
        @feature: SSO
        @test: kerberos user can login to CLI
        @setup: kerberos configured against foreman.
        @assert: Log in to hammer cli successfully
        @status: Manual
        """

    def test_sso_ipa_cli(self):
        """
        @feature: SSO
        @test: IPA user can login to CLI
        @setup: IPA configured against foreman.
        @assert: Log in to hammer cli successfully
        @status: Manual
        """

    def test_sso_openldap_cli(self):
        """
        @feature: SSO
        @test: OpenLDAP user can login to CLI
        @setup: OpenLDAP configured against foreman.
        @assert: Log in to hammer cli successfully
        @status: Manual
        """