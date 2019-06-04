# -*- encoding: utf-8 -*-
"""Test class for UI functions against an isolated capsule

:Requirement: Capsule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import (
    run_in_one_thread,
    stubbed,
    tier1,
    tier3,
    tier4,
    upgrade,
)
from robottelo.test import UITestCase


@run_in_one_thread
class CapsuleTestCase(UITestCase):
    """Implements capsule tests in UI"""

    @stubbed()
    @tier3
    @upgrade
    def test_positive_errata_push(self):
        """User can push errata through to a client on
        an isolated capsule

        :id: f714692d-534b-48e8-b052-c93241f86615

        :Setup: Client on an isolated capsule; errata synced on server

        :Steps: Attempt to install errata via Sat UI against client on an
            isolated capsule - this is a satellite-initiated action.

        :expectedresults: Errata can be installed.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_rpm_push(self):
        """User can install a new errata on a client through
        an isolated capsule - this is a satellite-initiated action

        :id: 682c8c57-461f-46ce-ae7a-9f4da6e09f1b

        :Setup: Client on an isolated capsule; rpms synced (RH, custom content)

        :Steps: attempt to push an RPM install onto client connected to
            isolated capsule - this is a satellite-initiated action.

        :expectedresults: Package is installed

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_puppet_push(self):
        """user can install new puppet module on a client
        through an isolated capsule

        :id: 34582de2-7dd4-472c-89ce-14224750eb21

        :Setup: Client on an isolated capsule; puppet content synced

        :Steps: attempt to push a puppet module install initiated from
            Satellite

        :expectedresults: module is installed

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_chost_selector(self):
        """User can choose, or is given an indication within
        the content hosts UI, any referenced capsule in order to
        learn/setup registration against said capsule(s).

        :id: c9cd3c0e-78c8-4548-8103-be42de408f36

        :Setup: A satellite with at least one capsule configured.

        :Steps:
            1. Go to Hosts > Content Hosts > Register Content Host
            2. Observe the section labeled 'Consuming Content From A Capsule'

        :expectedresults: capsule(s) appear in dropdown and the instructions
            for using subscription-manager update accordingly when choosing
            said capsule(s).

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier1
    def test_positive_capsule_version(self):
        """Check Capsule Version in About Page.

        :id: 24a6e423-9550-453a-a953-9350ff5a57bc

        :Steps:
            1. Navigate to the About Page
            2. Check the versions column of the Capsules.

        :expectedresults: The version of the Capsules exists in the about page.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_capsule_status(self):
        """Check Capsule Status in Index Page.

        :id: ec084b9f-ccb4-4657-8d5b-903156658703

        :Steps:
            1. Navigate to the Capsules Index Page
            2. Check the status of the Proxy.

        :expectedresults: The status of the Capsules is up and running.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_capsule_context(self):
        """Check Capsule has Location and Organization column in Index Page.

        :id: 330da7b9-6f52-4dc0-a824-d7f3af964b7f

        :Steps:
            1. Navigate to the Capsules Index Page
            2. Check the capsule's columns in the Index Page.

        :expectedresults: The Capsules Organization and Location info is
            visible on the index page.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_capsule_url(self):
        """Check Capsule no longer has 'Foreman URL' column in Index page.

        :id: c5f7c1f9-d887-4600-b7d2-902039ffed65

        :Steps:
            1. Navigate to the Capsules Index Page
            2. Check the capsule's columns in the Index Page.

        :expectedresults: The Capsules no longer have the 'Foreman URL' on the
            index page.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_capsule_pulp_storage(self):
        """Check Capsule has pulp_storage Used and Free
        info in the Overview tab of the Capsules show Page.

        :id: 0bce3dbb-8444-4f37-a4c4-ab565927be39

        :Steps:
            1. Navigate to the Capsules Show Page
            2. Check the capsule's overview tab in the show Page.

        :expectedresults: The 'Pulp Storage' used and free info is visible for
            the default capsule in the Overview Tab.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier4
    def test_positive_isolated_capsule_sync(self):
        """Check for Sync button and Syncing for Isolated Capsule in Overview
        tab.

        :id: 6c68984a-1246-4868-bc52-6291e9df9b89

        :Steps:
            1. Navigate to the Capsules Show Page
            2. Check the capsule's overview tab in the show Page.

        :expectedresults: The 'Content Sync' button is visible and sync works
            for the isolated capsule.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier4
    def test_positive_isolated_capsule_cancel_sync(self):
        """Check for Cancel Sync button and whether sync cancels
        for Isolated Capsule in the Overview tab.

        :id: 8f44dadd-00f0-4921-98bc-02dd860bc4fb

        :Steps:
            1. Navigate to the Capsules Show Page
            2. Check the capsule's overview tab in the show Page.

        :expectedresults: The 'Cancel Sync" button is visible and sync cancels
            for the isolated capsule.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier1
    def test_positive_capsule_details(self):
        """Check for details of Capsule in the Overview tab.

        :id: 4c012dc0-4ce3-4f88-b05c-67faa5ad16e4

        :Steps:
            1. Navigate to the Capsules Show Page
            2. Check the capsule's overview tab in the show Page.

        :expectedresults: The Overview tab displays these information 'Status',
            'Verison', 'Uptime', 'Registration Date', 'Packages', 'Location',
            'Puppet', 'Storage' info is displayed.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_capsule_environment(self):
        """Check for environment info of Capsule in the Puppet tab.

        :id: 2b1448c1-e566-49fa-a4dc-3136702fd74f

        :Steps:
            1. Create a CV and add a puppet module to it.
            2. Publish the CV
            3. Navigate to the Capsules Show Page
            4. Check the capsule's Puppet tab in the show Page.
            5. Now check the Enviroments Tab.

        :expectedresults: The puppet environment which got created after adding
            the puppet-module to CV, exists in the Environment column of the
            Puppet Tab.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_capsule_puppet_classes_count(self):
        """Check for Puppet Classes count info of Capsule in Puppet tab.

        :id: 2e657b25-d777-4907-b0a9-19262a0a4e0b

        :Steps:
            1. Create a CV and add a puppet module to it.
            2. Publish the CV and import the classes to puppet-env.
            3. Navigate to the Capsules Show Page
            4. Check the capsule's Puppet tab in the show Page.
            5. Now check the Enviroments Tab.

        :expectedresults: The puppet-classes count is visible in the 'Number of
            classes' column.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_capsule_puppet_hosts_managed_count(self):
        """Check Puppet 'Hosts managed' count info of Capsule in Puppet tab.

        :id: 147e6472-3459-41e1-94fe-39f4db25a4de

        :Steps:
            1. Get any host configured to consume Puppet.
            2. Publish the CV and import the classes to puppet-env.
            3. Navigate to the Capsules Show Page
            4. Check the capsule's Puppet tab in the show Page.
            5. Now check the General Tab.

        :expectedresults: The Puppet Hosts managed count is visible in the
            'Number of classes' column.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_capsule_puppetca_hosts_managed_count(self):
        """Check for Puppet 'Hosts managed' count info of Capsule
        in the Puppet-ca tab.

        :id: 0af8acb3-3765-4cc8-8100-c62dda30513f

        :Steps:
            1. Get any host configured to consume Puppet.
            2. Publish the CV and import the classes to puppet-env.
            3. Navigate to the Capsules Show Page
            4. Check the capsule's Puppet-ca tab in the show Page.
            5. Now check the General Tab.

        :expectedresults: The Puppet 'Hosts managed' count properly is visible.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_capsule_puppetca_certificate_name(self):
        """Check for Hosts certifcate-name is visible in Puppet-ca tab.

        :id: 7b3da902-f602-46c8-aa98-036125127752

        :Steps:
            1. Get any host configured to consume Puppet.
            2. Navigate to the Capsules Show Page
            3. Check the capsule's Puppet-ca tab in the show Page.
            4. Now check the General Tab.

        :expectedresults: The Hosts certificate-name is visible in the Puppet-
            ca Tab.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_capsule_puppetca_certificate_revoked(self):
        """Check for Hosts puppet certifcate can be revoked in Puppet-ca tab.

        :id: 6ce6f088-1542-4df2-9004-eaaf53b1ccc1

        :Steps:
            1. Get any host configured to consume Puppet.
            2. Navigate to the Capsules Show Page
            3. Check the capsule's Puppet-ca tab in the show Page.
            4. Now check the Certificates Tab.
            5. Click the revoke button of the corresponding host.
            6. Puppet runs should now not be possible on the hosts.

        :expectedresults: The puppet runs on hosts are possible after the certs
            are revoked for the host.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_capsule_puppetca_autosign(self):
        """Check for Hosts puppet certifcate can be auto-signed in Puppet-ca
        tab.

        :id: d88d6b8f-d6f1-4785-a949-84a65953e525

        :Steps:
            1. Get any host configured to consume Puppet.
            2. Navigate to the Capsules Show Page
            3. Check the capsule's Puppet-ca tab in the show Page.
            4. Now check the 'autosign entries' Tab.
            5. Click the new button to add a host entry.
            6. Puppet run should now be possible on the host, without having to
               manually sign the certificate.

        :expectedresults: The puppet run on host is possible without having to
            sign the certs manually for the host.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_dns_and_dhcp_enabled_on_capsule(self):
        """Check DNS ana DHCP is enabled on capsule

        :id: 56778d8e-79be-11e6-886c-68f72889dc7f

        :Steps: Enable DHCP and DNS infoblox plugins on capsule

        :expectedresults: DNS and DHCP must be included on capsule features

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
