"""Test class for OpenScap Feature

:Requirement: Openscap

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, tier1, tier2, tier3
from robottelo.test import UITestCase


class OpenScapTestCase(UITestCase):
    """Implements OpenScap feature tests in UI."""

    @stubbed()
    @tier1
    def test_positive_create_policy(self):
        """Create policies for OpenScap.

        :id: 9a7564d6-387a-4a92-b6d6-d28683845b40

        :Steps:

            1. Create an openscap policies.
            2. Provide all the appropriate parameters.

        :expectedresults: Whether creating policies for OpenScap is successful.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_create_policy(self):
        """Create policies for OpenScap with 256 chars.

        :id: e832d9f4-fee1-4502-937e-375c08d5f042

        :expectedresults: Creating policies for OpenScap is unsuccessful.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_delete_policy(self):
        """Delete policies of OpenScap.

        :id: 7324f2a7-a9ad-49e6-b564-4e58a8bb2c42

        :Steps:

            1. Create an openscap policies.
            2. Provide all the appropriate parameters.
            3. Delete the policy.

        :expectedresults: Whether deleting policies for OpenScap is successful.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_create_content(self):
        """Create OpenScap content.

        :id: 35c52cb4-b6c4-431a-b9c8-f5b15b6d67a8

        :Steps:

            1. Create an openscap content.
            2. Provide all the appropriate parameters.

        :expectedresults: Whether creating  content for OpenScap is successful

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_create_content(self):
        """Create OpenScap content with 256 chars.

        :id: 3410fe9b-55ba-4b87-bc7a-ec9138fc035a

        :expectedresults: Creating content for OpenScap is unsuccessful

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_delete_content(self):
        """Create OpenScap content and then delete it.

        :id: 1c6b63b3-c838-4b14-a7f4-a151d3bb49d4

        :Steps:

            1. Create an openscap content.
            2. Provide all the appropriate parameters.
            3. Delete the openscap content.

        :expectedresults: Deleting content for OpenScap is successful

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_access_oscap_reports(self):
        """OpenScap should have it's own Compliance Reporting page.

        :id: b1decf7e-f4e8-45aa-941b-c9b9c5b9efb0

        :expectedresults: Whether separate Compliance Reporting page exists.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_set_periodic_audit(self):
        """Should be able to periodically set OpenScap Audit.

        :id: f750710b-14ed-4448-ae3c-cec2fde4297a

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host as puppet client to default sat6 capsule.
            5. while creating the oscap policy select the period as weekly or
                monthly.
            6. Create oscap policy and associate it to the host-group or host.
            7. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
            8. Make sure the appropriate crontab entries are added as per the
                period selected.

        :expectedresults: Whether OpenScap Audit scans can be periodically set
            as per intervals.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_set_custom_periodic_audit(self):
        """Should be able to periodically set custom OpenScap Audit.

        :id: 595f87d6-ae35-4034-8b0d-50b6bec5d370

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host as puppet client to default sat6 capsule.
            5. while creating the oscap policy select the period as custom.
            6. Create oscap policy and associate it to the host-group or host.
            7. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
            8. Make sure the appropriate crontab entries are added as per the
                period selected.

        :expectedresults: Whether OpenScap Audit scans can be periodically set
            as per custom intervals.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_search_audit(self):
        """Should be able to search OpenScap audit results.

        :id: 77eb277f-c2a6-48fc-aa35-e08b7d595e41

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host as puppet client to default sat6 capsule.
            5. Create oscap policy and associate it to the host-group or host.
            6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
            7. Make sure the scan reports are generated under OSCAP reports.
            8. Search for the audit reports is possible.

        :expectedresults: Whether searching audit results is possible.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_audit_default_capsule(self):
        """OpenScap should be able to audit foreman managed
        infrastructure(Reports from default Capsule.)

        :id: 915b14e0-e41a-4857-b0ae-913c51251126

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host to default sat6 capsule.
            5. Create oscap policy and associate it to the host-group or host.
            6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
            7. Make sure the scan reports are generated under OSCAP reports.

        :expectedresults: Whether audit reports of Foreman managed
            Infrastructure (Hosts from default Capsule) are generated.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_audit_nondefault_capsule(self):
        """OpenScap should be able to audit foreman managed
        infrastructure (Reports from Non-Default Capsule)

        :id: db9db833-56a6-4628-9a91-6b3a9475dfc8

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host to external sat6 capsule.
            5. Create oscap policy and associate it to the host-group or host.
            6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
            7. Make sure the scan reports are generated under OSCAP reports.

        :expectedresults: Whether audit of Foreman managed Infrastructure
            (Hosts from Non-Default Capsule) is possible.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier2
    def test_positive_search_content(self):
        """Should be able to search OpenScap content.

        :id: 4aeef3ae-7e9a-488a-a906-b4aef024592f

        :steps:

            1. Create an openscap content.
            2. Provide valid data-stream.xml file available from
                scap-security-guide. (ssg-rhel6-ds.xml)

        :expectedresults: Whether searching OpenScap content is possible.

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_search_policies(self):
        """Should be able to search OpenScap policies.

        :id: 6a46438a-7248-4e48-90dc-e5b0ee57e1ec

        :Steps:

            1. Create an openscap content.
            2. Provide all the appropriate parameters

        :expectedresults: Whether searching OpenScap policies is possible.

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier3
    def test_positive_search_nonaudited_hosts(self):
        """Should be able to search Non-Audited Hosts/systems

        :id: c7ef2735-3af5-45a0-9ce7-e7e4ee1481eb

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host as puppet client to default sat6 capsule.
            5. Create oscap policy and associate it to the host-group or host.
            6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
            7. Make sure the scan reports are generated under OSCAP reports.
            8. Search for the non audited hosts.

        :expectedresults: Whether searching Non-Audited Hosts/Systems is
            possible.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_search_noncompliant_hosts(self):
        """Should be able to search Non-Compliant "Hosts"/systems

        :id: c75007f8-0567-444c-8f0e-08e535c3753c

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host as puppet client to default sat6 capsule.
            5. Create oscap policy and associate it to the host-group or host.
            6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
            7. Make sure the scan reports are generated under OSCAP reports.
            8. Search for the audit reports for non-compliant hosts.

        :expectedresults: Whether searching Non-Compliant systems is possible.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_compare_audit_results(self):
        """Should be able to compare multiple audit results of
        "Hosts"/systems.

        :id: 4169707c-02e6-4fc3-a478-39cb27379e33

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host as puppet client to default sat6 capsule.
            5. Create oscap policy and associate it to the host-group or host.
            6. Run 'puppet agent' on the host to configure/schedule OSCAP scan.
            7. Make sure the scan reports are generated under OSCAP reports.
            8. Compare audit reports.

        :expectedresults: Whether Comparing multiple audit results of
            Hosts/Systems is possible.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_assign_policies_for_hosts(self):
        """Should be able to assign policies for the hosts.

        :id: 1399ec3e-8f03-4faf-8440-d580e05368d9

        :Steps:

            1. Create oscap content.
            2. Create puppet repo with puppet-foreman_scap_client puppet-module
            3. create cv with the above puppet content, publish and promote.
            4. Register the host as puppet client to default sat6 capsule.
            5. Create oscap policy and associate it to multiple hosts.

        :expectedresults: Whether assigning policies to multiple hosts is
            possible.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier2
    def test_positive_check_dashboard_views(self):
        """Dashboard views that can tell Audited/Un-Audited,
        Compliant/Non-Compliant and trends.

        :id: 41bc8692-0830-4b17-b5be-7a798a13cc4c

        :expectedresults: Expected Dashboard views are visible.

        :caseautomation: notautomated

        :CaseLevel: Integration
        """
