# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Host/System Unification
"""

from basecli import BaseCLI
#import unittest


class TestHostSystemUnificationCLI(BaseCLI):
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

    def test_all_hosts_appear_in_foreman(self):
        """
        @feature: Host/System Unification
        @test: Hosts registered to Katello via rhsm appear in foreman
        @steps:
        1.  Register system to katello via rhsm
        2.  Provision host in Foreman
        3.  Execute hammer cli command to list foreman hosts
        @assert: Hosts/Systems created in both places return in list
        @status: Manual
        """

    def all_hosts_appear_in_katello(self):
        """
        @feature: Host/System Unification
        @test: Hosts provisioned in foreman via appear in katello
        @steps:
        1.  Register system to katello via rhsm
        2.  Provision host in Foreman
        3.  Execute hammer cli command to list katello systems
        @assert: Hosts/Systems created in both places return in list
        @status: Manual
        """
