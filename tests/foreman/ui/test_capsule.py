# -*- encoding: utf-8 -*-
"""Test class for UI functions against an isolated capsule"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier3, tier4
from robottelo.test import UITestCase


class CapsuleTestCase(UITestCase):
    """Implements capsule tests in UI"""

    @stubbed()
    @tier3
    def test_positive_errata_push(self):
        """User can push errata through to a client on
        an isolated capsule

        @Feature: Capsules

        @Setup: Client on an isolated capsule; errata synced
        on server

        @Steps:

        1. Attempt to install errata via Sat UI against client on an
        isolated capsule - this is a satellite-initiated action.

        @Assert: Errata can be installed.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_rpm_push(self):
        """User can install a new errata on a client through
        an isolated capsule - this is a satellite-initiated action

        @Feature: Capsules

        @Setup: Client on an isolated capsule; rpms synced (RH,
        custom content)

        @Steps:

        1. attempt to push an RPM install onto client connected to
        isolated capsule - this is a satellite-initiated action.

        @Assert: Package is installed

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_puppet_push(self):
        """user can install new puppet module on a client
        through an isolated capsule

        @Feature: Capsules

        @Setup: Client on an isolated capsule; puppet content synced

        @Steps:

        1. attempt to push a puppet module install initiated from
        Satellite

        @Assert: module is installed

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_chost_selector(self):
        """User can choose, or is given an indication within
        the content hosts UI, any referenced capsule in order to
        learn/setup registration against said capsule(s).

        @Feature: Capsules

        @Setup: A satellite with at least one capsule configured.

        @Steps:

        1. Go to Hosts > Content Hosts > Register Content Host
        2. Observe the section labeled 'Consuming Content From
           A Capsule'

        @Assert: capsule(s) appear in dropdown and the instructions
        for using subscription-manager update accordingly when
        choosing said capsule(s).

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_capsule_version(self):
        """Check Capsule Version in About Page.

        @Feature: Capsule Management UI

        @Steps:

        1. Navigate to the About Page
        2. Check the versions column of the Capsules.

        @Assert: The version of the Capsules exists in the about page.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_capsule_status(self):
        """Check Capsule Status in Index Page.

        @Feature: Capsule Management UI

        @Steps:

        1. Navigate to the Capsules Index Page
        2. Check the status of the Proxy.

        @Assert: The status of the Capsules
        is up and running.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_capsule_context(self):
        """Check Capsule has Location and Organization column in Index Page.

        @Feature: Capsule Management UI

        @Steps:

        1. Navigate to the Capsules Index Page
        2. Check the capsule's columns in the Index Page.

        @Assert: The Capsules Organization and Location
        info is visible on the index page.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_capsule_url(self):
        """Check Capsule no longer has 'Foreman URL' column in Index page.

        @Feature: Capsule Management UI

        @Steps:

        1. Navigate to the Capsules Index Page
        2. Check the capsule's columns in the Index Page.

        @Assert: The Capsules no longer have the
        'Foreman URL' on the index page.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_capsule_pulp_storage(self):
        """Check Capsule has pulp_storage Used and Free
        info in the Overview tab of the Capsules show Page.

        @Feature: Capsule Management UI

        @Steps:

        1. Navigate to the Capsules Show Page
        2. Check the capsule's overview tab in the show Page.

        @Assert: The 'Pulp Storage' used and free info
        is visible for the default capsule in the
        Overview Tab.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_isolated_capsule_sync(self):
        """Check for Sync button and Syncing for Isolated Capsule in Overview tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Navigate to the Capsules Show Page
        2. Check the capsule's overview tab in the show Page.

        @Assert: The 'Content Sync' button is visible
        and sync works for the isolated capsule.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_isolated_capsule_cancel_sync(self):
        """Check for Cancel Sync button and whether sync cancels
        for Isolated Capsule in the Overview tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Navigate to the Capsules Show Page
        2. Check the capsule's overview tab in the show Page.

        @Assert: The 'Cancel Sync" button is visible
        and sync cancels for the isolated capsule.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_capsule_details(self):
        """Check for details of Capsule in the Overview tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Navigate to the Capsules Show Page
        2. Check the capsule's overview tab in the show Page.

        @Assert: The Overview tab displays these
        information 'Status', 'Verison', 'Uptime',
        'Registration Date', 'Packages', 'Location',
        'Puppet', 'Storage' info is displayed.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_capsule_environment(self):
        """Check for environment info of Capsule in the Puppet tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Create a CV and add a puppet module to it.
        2. Publish the CV
        3. Navigate to the Capsules Show Page
        4. Check the capsule's Puppet tab in the show Page.
        5. Now check the Enviroments Tab.

        @Assert: The puppet environment which got created
        after adding the puppet-module to CV, exists in the
        Environment column of the Puppet Tab.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_capsule_puppet_classes_count(self):
        """Check for Puppet Classes count info of Capsule in Puppet tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Create a CV and add a puppet module to it.
        2. Publish the CV and import the classes to puppet-env.
        3. Navigate to the Capsules Show Page
        4. Check the capsule's Puppet tab in the show Page.
        5. Now check the Enviroments Tab.

        @Assert: The puppet-classes count is visible in the
        'Number of classes' column.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_capsule_puppet_hosts_managed_count(self):
        """Check Puppet 'Hosts managed' count info of Capsule in Puppet tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Get any host configured to consume Puppet.
        2. Publish the CV and import the classes to puppet-env.
        3. Navigate to the Capsules Show Page
        4. Check the capsule's Puppet tab in the show Page.
        5. Now check the General Tab.

        @Assert: The Puppet Hosts managed count is visible in the
        'Number of classes' column.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_capsule_puppetca_hosts_managed_count(self):
        """Check for Puppet 'Hosts managed' count info of Capsule
        in the Puppet-ca tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Get any host configured to consume Puppet.
        2. Publish the CV and import the classes to puppet-env.
        3. Navigate to the Capsules Show Page
        4. Check the capsule's Puppet-ca tab in the show Page.
        5. Now check the General Tab.

        @Assert: The Puppet 'Hosts managed' count properly
        is visible.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_capsule_puppetca_certificate_name(self):
        """Check for Hosts certifcate-name is visible in Puppet-ca tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Get any host configured to consume Puppet.
        2. Navigate to the Capsules Show Page
        3. Check the capsule's Puppet-ca tab in the show Page.
        4. Now check the General Tab.

        @Assert: The Hosts certificate-name is visible in the
        Puppet-ca Tab.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_capsule_puppetca_certificate_revoked(self):
        """Check for Hosts puppet certifcate can be revoked in Puppet-ca tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Get any host configured to consume Puppet.
        2. Navigate to the Capsules Show Page
        3. Check the capsule's Puppet-ca tab in the show Page.
        4. Now check the Certificates Tab.
        5. Click the revoke button of the corresponding host.
        6. Puppet runs should now not be possible on the hosts.

        @Assert: The puppet runs on hosts are possible
        after the certs are revoked for the host.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_capsule_puppetca_autosign(self):
        """Check for Hosts puppet certifcate can be auto-signed in Puppet-ca tab.

        @Feature: Capsule Management UI

        @Steps:

        1. Get any host configured to consume Puppet.
        2. Navigate to the Capsules Show Page
        3. Check the capsule's Puppet-ca tab in the show Page.
        4. Now check the 'autosign entries' Tab.
        5. Click the new button to add a host entry.
        6. Puppet run should now be possible on the host, without
           having to manually sign the certificate.

        @Assert: The puppet run on host is possible
        without having to sign the certs manually for the host.

        @Status: Manual
        """
