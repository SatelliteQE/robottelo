# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification"""

from robottelo.decorators import run_only_on, stubbed
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestHostSystemUnificationCLI(CLITestCase):
    # Testing notes for host/system unification in katello/foreman:
    # Basically assuring that hosts in foreman/katello bits are joined
    # and information can be associated across both parts of product.
    #
    # Wondering if these commands might should be condensed to just one
    # command in the future?
    #
    # Devnote:
    # (the link/join will) "Most likely an internal UUID, not something
    # fuzzy like hostname"

    @stubbed()
    def test_all_hosts_appear_in_foreman(self):
        """@test: Hosts registered to Katello via rhsm appear in foreman

        @feature: Host/System Unification

        @steps:
        1.  Register system to katello via rhsm
        2.  Provision host in Foreman
        3.  Execute hammer cli command to list foreman hosts

        @assert: Hosts/Systems created in both places return in list

        @status: Manual

        """
        pass

    @stubbed()
    def all_hosts_appear_in_katello(self):
        """@test: Hosts provisioned in foreman via appear in katello

        @feature: Host/System Unification

        @steps:
        1.  Register system to katello via rhsm
        2.  Provision host in Foreman
        3.  Execute hammer cli command to list katello systems

        @assert: Hosts/Systems created in both places return in list

        @status: Manual

        """
        pass
