# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification"""

from robottelo.decorators import run_only_on, stubbed, tier3
from robottelo.test import UITestCase


class HostSystemUnificationTestCase(UITestCase):
    """Implements Host System Unification tests in UI"""
    # Testing notes for host/system unification in katello/foreman
    # Basically assuring that hosts in foreman/katello bits are joined
    # and information can be associated across both parts of product.
    #
    # Devnote:
    # (the link/join will) "Most likely an internal UUID, not something
    # fuzzy like hostname"

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_register_katello_host(self):
        """Hosts registered to Katello via rhsm appear in foreman

        @feature: Host/System Unification

        @steps:
        1.  Register system to katello via rhsm
        2.  View system in Katello content hosts
        3.  View hosts in foreman

        @assert: Host appears in both places

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_provision_foreman_host(self):
        """Hosts provisioned via foreman appear in katello

        @feature: Host/System Unification

        @steps:
        1.  Provision host in foreman
        2.  View system in Katello content hosts
        3.  View hosts in foreman

        @assert: Host appears in both places

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_rename_foreman_host(self):
        """Hosts renamed in foreman appear in katello

        @feature: Host/System Unification

        @steps:
        1.  Rename a system via katello content hosts
        2.  View system in Katello content hosts
        3.  View hosts in foreman

        @assert: Host appears in both places despite being renamed

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_rename_katello_host(self):
        """Hosts renamed in katello via appear in foreman

        @feature: Host/System Unification

        @steps:
        1.  Rename a host via foreman
        2.  View system in Katello content hosts
        3.  View hosts in foreman

        @assert: Host appears in both places despite being renamed

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_delete_foreman_host(self):
        """Hosts delete in foreman disappear from both sides of UI

        @feature: Host/System Unification

        @steps:
        1.  Delete a system via katello content hosts
        2.  View system in Katello content hosts
        3.  View hosts in foreman

        @assert: Host no longer aappears in either place once removed

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_delete_katello_host(self):
        """Hosts delete in katello disappear from both sides of UI

        @feature: Host/System Unification

        @steps:
        1.  Delete a host via foreman
        2.  View system in Katello content hosts
        3.  View hosts in foreman

        @assert: Host no longer aappears in either place once removed

        @status: Manual

        """
