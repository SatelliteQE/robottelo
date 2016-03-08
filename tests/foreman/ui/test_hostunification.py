# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification"""

from robottelo.decorators import run_only_on, stubbed, tier3
from robottelo.test import UITestCase


class HostcontenthostUnificationTestCase(UITestCase):
    """Implements Host and Content-host Unification tests in UI"""
    # Testing notes for host/content-host unification in katello/foreman
    # Basically assuring that hosts in foreman/katello bits are joined
    # and information can be associated across both parts of product.
    #
    # Devnote:
    # (the link/join will) "Most likely an internal UUID, not something
    # fuzzy like hostname"

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_register_host_via_rhsm(self):
        """Register a pre-installed host via rhsm using credentials

        @feature: Host/Content-Host Unification

        @steps:
        1.  Register a host via rhsm using credentials
        2.  View host under content hosts
        3.  View host under 'All Hosts'

        @assert: Hosts registered via rhsm appears under 'All hosts' as well
        as under content-hosts.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_register_host_via_ak(self):
        """Register a pre-installed host via rhsm using activation-key

        @feature: Host/Content-Host Unification

        @steps:
        1.  Register a host via rhsm using activation-key
        2.  View host under content hosts
        3.  View host under 'All Hosts'

        @assert: Hosts registered via activation key appears under 'All hosts'
        as well as under content-hosts

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_validate_org(self):
        """Assign org to host at registration time if not already

        @feature: Host/Content-Host Unification

        @steps:
        1.  Register a host via rhsm by specifying org
        2.  View host under content hosts

        @assert: Registered host should be associated with organization
        specified at registration

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_provision_foreman_host(self):
        """

        @feature: Host/Content-host Unification

        @steps:
        1.  Provision a host via foreman
        2.  View host under content hosts
        3.  View host under 'All Hosts'

        @assert: Hosts provisioned via foreman should appear under 'All hosts'
        as well as under content-hosts.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_rename_foreman_host(self):
        """Hosts renamed in foreman appears in katello under content-hosts

        @feature: Host/Content-host Unification

        @steps:
        1.  Rename a host from 'All Hosts' page
        2.  View host under content-hosts page
        3.  View host under 'All Hosts'

        @assert: Host appears in both places despite being renamed

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_rename_content_host(self):
        """Hosts renamed in katello via content-hosts appear in foreman

        @feature: Host/Content-host Unification

        @steps:
        1.  Rename a host from 'Content-hosts' page
        2.  View host under content-hosts
        3.  View host under 'All Hosts'

        @assert: Host appears in both places despite being renamed

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_delete_from_allhosts(self):
        """Delete a host from 'All hosts'

        @feature: Host/Content-host Unification

        @steps:
        1.  Delete a host from 'All hosts' page
        2.  View host under 'Content-hosts'
        3.  View host under 'All hosts'

        @assert: Host should be removed from 'All hosts' as well as
        content-hosts

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_unregister_content_host(self):
        """Unregister a host from content-hosts page

        @feature: Host/Content-host Unification

        @steps:
        1.  Un-register a host from content-host page
        2.  View host under content hosts
        3.  View host under 'All hosts'

        @assert: Hosts un-registered from content-host should appear in both
        sides of UI

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_re_register_host(self):
        """Re-register a host which was un-registered earlier from content-host

        @feature: Host/Content-host Unification

        @steps:
        1.  Re-register a host which was unregistered before
        2.  View host under content hosts
        3.  View host under 'All hosts'

        @assert: A single entry of host should appear at both places on
        re-registering

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_add_subs_to_unregistered_host(self):
        """Perform a subscription action on a host which is not registered

        @feature: Host/Content-host Unification

        @steps:
        1.  Provision a host via foreman which is not registered via rhsm
        2.  Try to add subscription from content-hosts page

        @assert: User get a warning:
        This Host is not currently registered with subscription-manager.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_add_contents_to_unregistered_host(self):
        """Perform a content action like on a host which is not registered

        @feature: Host/Content-host Unification

        @steps:
        1.  Provision a host via foreman which is not registered via rhsm
        2.  Try to add package from content-hosts page

        @assert: User get a warning:
        This Host is not currently registered with subscription-manager.

        @status: Manual
        """
