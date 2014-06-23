# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Host/System Unification
"""
import sys

from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.test import UITestCase

if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest


class TestHostSystemUnificationUI(UITestCase):
    # Testing notes for host/system unification in katello/foreman
    # Basically assuring that hosts in foreman/katello bits are joined
    # and information can be associated across both parts of product.
    #
    # Devnote:
    # (the link/join will) "Most likely an internal UUID, not something
    # fuzzy like hostname"

    @unittest.skip(NOT_IMPLEMENTED)
    def test_katello_host_in_foreman(self):
        """
        @feature: Host/System Unification
        @test: Hosts registered to Katello via rhsm appear in foreman
        @steps:
        1.  Register system to katello via rhsm
        2.  View system in Katello content hosts
        3.  View hosts in foreman
        @assert: Host appears in both places
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_foreman_host_in_katello(self):
        """
        @feature: Host/System Unification
        @test: Hosts provisioned in foreman via appear in katello
        @steps:
        1.  Provision host in foreman
        2.  View system in Katello content hosts
        3.  View hosts in foreman
        @assert: Host appears in both places
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_renamed_host_foreman(self):
        """
        @feature: Host/System Unification
        @test: Hosts renamed in foreman appear in katello
        @steps:
        1.  Rename a system via katello content hosts
        2.  View system in Katello content hosts
        3.  View hosts in foreman
        @assert: Host appears in both places despite being renamed
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_renamed_host_katello(self):
        """
        @feature: Host/System Unification
        @test: Hosts renamed in katello via appear in foreman
        @steps:
        1.  Rename a host via foreman
        2.  View system in Katello content hosts
        3.  View hosts in foreman
        @assert: Host appears in both places despite being renamed
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_deleted_host_foreman(self):
        """
        @feature: Host/System Unification
        @test: Hosts delete in foreman disappear from both sides of UI
        @steps:
        1.  Delete a system via katello content hosts
        2.  View system in Katello content hosts
        3.  View hosts in foreman
        @assert: Host no longer aappears in either place once removed
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_deleted_host_katello(self):
        """
        @feature: Host/System Unification
        @test: Hosts delete in katello disappear from both sides of UI
        @steps:
        1.  Delete a host via foreman
        2.  View system in Katello content hosts
        3.  View hosts in foreman
        @assert: Host no longer aappears in either place once removed
        @status: Manual
        """
        pass
