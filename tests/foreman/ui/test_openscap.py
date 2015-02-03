"""Test class for OpenScap Feature"""
from robottelo.test import UITestCase


class OpenScap(UITestCase):
    """Implements OpenScap feature tests in UI."""

    def test_create_policies(self):
        """@Test: Create policies for OpenScap.

        @Feature: OpenScap - Positive Create.

        @Assert: Whether creating policies for OpenScap is successful.

        @status: Manual

        """

    def test_create_content(self):
        """@Test: Create OpenScap content.

        @Feature: OpenScap - Positive Create.

        @Assert: Whether creating content for OpenScap is successful

        @status: Manual

        """

    def test_access_oscap_reports(self):
        """@Test: OpenScap should have it's own Compliance Reporting page.

        @Feature: OpenScap - Compliance Reporting.

        @Assert: Whether separate Compliance Reporting page exists.

        @status: Manual

        """

    def test_periodic_audits(self):
        """@Test: Should be able to periodically set OpenScap Audit.

        @Feature: OpenScap - Periodic Audit.

        @Assert: Whether OpenScap Audit scans can be periodically set as per
        intervals.

        @status: Manual

        """

    def test_search_audits(self):
        """@Test: Should be able to search OpenScap audit results.

        @Feature: OpenScap - Search

        @Assert: Whether searching audit results is possible.

        @status: Manual

        """

    def test_audit_default_capsule(self):
        """@Test: OpenScap should be able to audit foreman managed
        infrastructure(Reports from default Capsule.)

        @Feature: OpenScap - Audit Foreman Infrastructure.

        @Assert: Whether audit of Foreman managed Infrastructure
        (Hosts from default Capsule) is possible.

        @status: Manual

        """

    def test_audit_nondefault_capsule(self):
        """@Test: OpenScap should be able to audit foreman managed
        infrastructure (Reports from Non-Default Capsule)

        @Feature: OpenScap - Audit Foreman Infrastructure.

        @Assert: Whether audit of Foreman managed Infrastructure
        (Hosts from Non-Default Capsule) is possible.

        @status: Manual

        """

    def test_search_content(self):
        """@Test: Should be able to search OpenScap content.

        @Feature: OpenScap - Search.

        @Assert: Whether searching OpenScap content is possible.

        @status: Manual

        """

    def test_search_policies(self):
        """@Test: Should be able to search OpenScap policies.

        @Feature: OpenScap - Search.

        @Assert: Whether searching OpenScap policies is possible.

        @status: Manual

        """

    def test_audit_adhoc_hosts(self):
        """@Test: Should be able to perform Ad-Hoc Audit of a given
        Host/system.

        @Feature: OpenScap - Ad-Hoc

        @Assert: Whether performing Ad-Hoc Audit of a given
        Host/System is possible.

        @status: Manual

        """

    def test_audit_targeted_hosts(self):
        """@Test: Openscap should be able to audit hosts in a targeted
        "Host Collection" and Orgs.

        @Feature: OpenScap - Targeted Audit ("Host Collection" and "Orgs")

        @Assert: Whether we can target a particular "Host Collection"
        and/or "Orgs".

        @status: Manual

        """

    def test_search_nonaudited_hosts(self):
        """@Test: Should be able to search Non-Audited Hosts/systems

        @Feature: OpenScap - Search.

        @Assert: Whether searching Non-Audited Hosts/Systems is possible.

        @status: Manual

        """

    def test_search_noncompliant_hosts(self):
        """@Test: Should be able to search Non-Compliant "Hosts"/systems

        @Feature: OpenScap - Search

        @Assert: Whether searching Non-Compliant systems is possible.

        @status: Manual

        """

    def test_compare_audit_results(self):
        """@Test: Should be able to compare multiple audit results of
        "Hosts"/systems.

        @Feature: OpenScap - Compare

        @Assert: Whether Comparing multiple audit results of Hosts/Systems
        is possible.

        @status: Manual

        """

    def test_assign_policies_for_hosts(self):
        """@Test: Should be able to assign policies for the hosts.

        @Feature: OpenScap - Assigning policies.

        @Assert: Whether assigning policies for Hosts/Systems is possible.

        @status: Manual

        """

    def test_deashboard_Views(self):
        """@Test: Dashboard views that can tell Audited/Un-Audited,
        Compliant/Non-Compliant and trends.

        @Feature: OpenScap - Dashboard.

        @Assert: Whether the mentioned Dashboard views are visible.

        @status: Manual

        """
