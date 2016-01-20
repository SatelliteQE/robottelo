"""Test class for OpenScap Feature"""
from robottelo.decorators import stubbed, tier1, tier2, tier3
from robottelo.test import UITestCase


class OpenScapTestCase(UITestCase):
    """Implements OpenScap feature tests in UI."""

    @stubbed()
    @tier1
    def test_positive_create_policy(self):
        """Create policies for OpenScap.

        @Feature: OpenScap - Positive Create.

        @Steps:

        1. Create an openscap policies.
        2. Provide all the appropriate parameters.

        @Assert: Whether creating policies for OpenScap is successful.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_create_policy(self):
        """Create policies for OpenScap with 256 chars.

        @Feature: OpenScap - Negative Create.

        @Assert: Creating policies for OpenScap is unsuccessful.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_delete_policy(self):
        """Delete policies of OpenScap.

        @Feature: OpenScap - Delete.

        @Steps:

        1. Create an openscap policies.
        2. Provide all the appropriate parameters.
        3. Delete the policy.

        @Assert: Whether deleting policies for OpenScap is successful.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_create_content(self):
        """Create OpenScap content.

        @Feature: OpenScap - Positive Create.

        @Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.

        @Assert: Whether creating  content for OpenScap is successful

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_create_content(self):
        """Create OpenScap content with 256 chars.

        @Feature: OpenScap - Negative Create.

        @Assert: Creating content for OpenScap is unsuccessful

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_delete_content(self):
        """Create OpenScap content and then delete it.

        @Feature: OpenScap - Delete

        @Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.
        3. Delete the openscap content.

        @Assert: Deleting content for OpenScap is successful

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_access_oscap_reports(self):
        """OpenScap should have it's own Compliance Reporting page.

        @Feature: OpenScap - Compliance Reporting.

        @Assert: Whether separate Compliance Reporting page exists.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_set_periodic_audit(self):
        """Should be able to periodically set OpenScap Audit.

        @Feature: OpenScap - Periodic Audit.

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host as puppet client to default sat6 capsule.
        5. while creating the oscap policy select the period as weekly
           or monthly.
        6. Create oscap policy and associate it to the host-group or host.
        7. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
        8. Make sure the appropriate crontab entries are added as per the
           period selected.

        @Assert: Whether OpenScap Audit scans can be periodically set as per
        intervals.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_set_custom_periodic_audit(self):
        """Should be able to periodically set custom OpenScap Audit.

        @Feature: OpenScap - Periodic Audit.

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host as puppet client to default sat6 capsule.
        5. while creating the oscap policy select the period as custom.
        6. Create oscap policy and associate it to the host-group or host.
        7. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
        8. Make sure the appropriate crontab entries are added as per the
           period selected.

        @Assert: Whether OpenScap Audit scans can be periodically set as per
        custom intervals.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_search_audit(self):
        """Should be able to search OpenScap audit results.

        @Feature: OpenScap - Search

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host as puppet client to default sat6 capsule.
        5. Create oscap policy and associate it to the host-group or host.
        6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
        7. Make sure the scan reports are generated under OSCAP reports.
        8. Search for the audit reports is possible.

        @Assert: Whether searching audit results is possible.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_audit_default_capsule(self):
        """OpenScap should be able to audit foreman managed
        infrastructure(Reports from default Capsule.)

        @Feature: OpenScap - Audit Foreman Infrastructure.

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host to default sat6 capsule.
        5. Create oscap policy and associate it to the host-group or host.
        6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
        7. Make sure the scan reports are generated under OSCAP reports.

        @Assert: Whether audit reports of Foreman managed Infrastructure
        (Hosts from default Capsule) are generated.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_audit_nondefault_capsule(self):
        """OpenScap should be able to audit foreman managed
        infrastructure (Reports from Non-Default Capsule)

        @Feature: OpenScap - Audit Foreman Infrastructure.

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host to external sat6 capsule.
        5. Create oscap policy and associate it to the host-group or host.
        6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
        7. Make sure the scan reports are generated under OSCAP reports.

        @Assert: Whether audit of Foreman managed Infrastructure
        (Hosts from Non-Default Capsule) is possible.

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_search_content(self):
        """Should be able to search OpenScap content.

        @Feature: OpenScap - Search.

        @steps:

        1. Create an openscap content.
        2. Provide valid data-stream.xml file available from
           scap-security-guide. (ssg-rhel6-ds.xml)

        @Assert: Whether searching OpenScap content is possible.

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_search_policies(self):
        """Should be able to search OpenScap policies.

        @Feature: OpenScap - Search.

        @Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters

        @Assert: Whether searching OpenScap policies is possible.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_search_nonaudited_hosts(self):
        """Should be able to search Non-Audited Hosts/systems

        @Feature: OpenScap - Search.

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host as puppet client to default sat6 capsule.
        5. Create oscap policy and associate it to the host-group or host.
        6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
        7. Make sure the scan reports are generated under OSCAP reports.
        8. Search for the non audited hosts.

        @Assert: Whether searching Non-Audited Hosts/Systems is possible.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_search_noncompliant_hosts(self):
        """Should be able to search Non-Compliant "Hosts"/systems

        @Feature: OpenScap - Search

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host as puppet client to default sat6 capsule.
        5. Create oscap policy and associate it to the host-group or host.
        6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
        7. Make sure the scan reports are generated under OSCAP reports.
        8. Search for the audit reports for non-compliant hosts.

        @Assert: Whether searching Non-Compliant systems is possible.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_compare_audit_results(self):
        """Should be able to compare multiple audit results of
        "Hosts"/systems.

        @Feature: OpenScap - Compare

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host as puppet client to default sat6 capsule.
        5. Create oscap policy and associate it to the host-group or host.
        6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
        7. Make sure the scan reports are generated under OSCAP reports.
        8. Compare audit reports.

        @Assert: Whether Comparing multiple audit results of Hosts/Systems
        is possible.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_assign_policies_for_hosts(self):
        """Should be able to assign policies for the hosts.

        @Feature: OpenScap - Assigning policies.

        @Steps:

        1. Create oscap content.
        2. Create puppet repo with puppet-foreman_scap_client puppet-module
        3. create cv with the above puppet content, publish and promote.
        4. Register the host as puppet client to default sat6 capsule.
        5. Create oscap policy and associate it to multiple hosts.

        @Assert: Whether assigning policies to multiple hosts is possible.

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_check_dashboard_views(self):
        """Dashboard views that can tell Audited/Un-Audited,
        Compliant/Non-Compliant and trends.

        @Feature: OpenScap - Dashboard.

        @Assert: Expected Dashboard views are visible.

        @Status: Manual
        """
