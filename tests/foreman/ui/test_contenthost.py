# -*- encoding: utf-8 -*-
"""Test class for Content Hosts UI

@Requirement: Content Host

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
import re
from six.moves.urllib.parse import urljoin
from nailgun import entities

from robottelo.cleanup import vm_cleanup
from robottelo.cli.factory import (
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.config import settings
from robottelo.constants import (
    DISTRO_RHEL7,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_GROUP,
    FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_0_YUM_REPO,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    skip_if_not_set,
    tier3,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.locators import locators, tab_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_in_one_thread
class ContentHostTestCase(UITestCase):
    """Implements Content Host tests in UI"""

    @classmethod
    def set_session_org(cls):
        """Create an organization for tests, which will be selected
        automatically"""
        cls.session_org = entities.Organization().create()

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Lifecycle Environment, Content View and Activation key
        """
        super(ContentHostTestCase, cls).setUpClass()
        cls.env = entities.LifecycleEnvironment(
            organization=cls.session_org).create()
        cls.content_view = entities.ContentView(
            organization=cls.session_org).create()
        cls.activation_key = entities.ActivationKey(
            environment=cls.env,
            organization=cls.session_org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        }, force_manifest_upload=True)
        cls.setup_entities = setup_org_for_a_custom_repo({
            'url': FAKE_0_YUM_REPO,
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })
        setup_org_for_a_custom_repo({
            'url': FAKE_6_YUM_REPO,
            'product': cls.setup_ents['product-id'],
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })
        cls.product = entities.Product(
            id=cls.setup_entities['product-id']).read()

    def setUp(self):
        """Create a VM, subscribe it to satellite-tools repo, install
        katello-ca and katello-agent packages"""
        super(ContentHostTestCase, self).setUp()
        self.client = VirtualMachine(distro=DISTRO_RHEL7)
        self.addCleanup(vm_cleanup, self.client)
        self.client.create()
        self.client.install_katello_ca()
        self.client.register_contenthost(
            self.session_org.label, self.activation_key.name)
        self.assertTrue(self.client.subscribed)
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_agent()

    @tier3
    def test_positive_search_by_subscription_status(self):
        """Register host into the system and search for it afterwards by
        subscription status

        @id: b4d24ee7-51b9-43e4-b0c9-7866b6340ce1

        @expectedresults: Validate that host can be found for valid
        subscription status and that host is not present in the list for
        invalid status

        @BZ: 1406855

        @CaseLevel: System
        """
        with Session(self.browser):
            self.assertIsNotNone(self.contenthost.search(self.client.hostname))
            self.assertIsNotNone(
                self.contenthost.search(
                    self.client.hostname,
                    _raw_query='subscription_status = valid',
                )
            )
            self.assertIsNone(
                self.contenthost.search(
                    self.client.hostname,
                    _raw_query='subscription_status != valid',
                )
            )

    @tier3
    def test_positive_install_package(self):
        """Install a package to a host remotely

        @id: 13b9422d-4b7a-4068-9a57-a94602cd6410

        @expectedresults: Package was successfully installed

        @CaseLevel: System
        """
        with Session(self.browser):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Package Install',
                FAKE_0_CUSTOM_PACKAGE_NAME,
            )
            self.assertEqual(result, 'success')
            self.assertIsNotNone(self.contenthost.package_search(
                self.client.hostname, FAKE_0_CUSTOM_PACKAGE_NAME))

    @tier3
    def test_positive_remove_package(self):
        """Remove a package from a host remotely

        @id: 86d8896b-06d9-4c99-937e-f3aa07b4eb69

        @expectedresults: Package was successfully removed

        @CaseLevel: System
        """
        self.client.download_install_rpm(
            FAKE_6_YUM_REPO,
            FAKE_0_CUSTOM_PACKAGE
        )
        with Session(self.browser):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Package Remove',
                FAKE_0_CUSTOM_PACKAGE_NAME,
            )
            self.assertEqual(result, 'success')
            self.assertIsNone(self.contenthost.package_search(
                self.client.hostname, FAKE_0_CUSTOM_PACKAGE_NAME))

    @tier3
    def test_positive_upgrade_package(self):
        """Upgrade a host package remotely

        @id: 1969db93-e7af-4f5f-973d-23c222224db6

        @expectedresults: Package was successfully upgraded

        @CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with Session(self.browser):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Package Update',
                FAKE_1_CUSTOM_PACKAGE_NAME,
            )
            self.assertEqual(result, 'success')
            self.assertIsNotNone(self.contenthost.package_search(
                self.client.hostname, FAKE_2_CUSTOM_PACKAGE))

    @tier3
    @upgrade
    def test_positive_install_package_group(self):
        """Install a package group to a host remotely

        @id: a43fb21b-5f6a-4f14-8cd6-114ec287540c

        @expectedresults: Package group was successfully installed

        @CaseLevel: System
        """
        with Session(self.browser):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Group Install',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            self.assertEqual(result, 'success')
            for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
                self.assertIsNotNone(self.contenthost.package_search(
                    self.client.hostname, package))

    @tier3
    def test_positive_remove_package_group(self):
        """Remove a package group from a host remotely

        @id: dbeea1f2-adf4-4ad8-a989-efad8ce21b98

        @expectedresults: Package group was successfully removed

        @CaseLevel: System
        """
        with Session(self.browser):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Group Install',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            self.assertEqual(result, 'success')
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Group Remove',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            self.assertEqual(result, 'success')
            for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
                self.assertIsNone(self.contenthost.package_search(
                    self.client.hostname, package))

    @tier3
    @upgrade
    def test_positive_install_errata(self):
        """Install a errata to a host remotely

        @id: 42bb96fb-1319-4542-af42-9f3ee24065ea

        @expectedresults: Errata was successfully installed

        @CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with Session(self.browser):
            result = self.contenthost.install_errata(
                self.client.hostname,
                FAKE_2_ERRATA_ID,
            )
            self.assertEqual(result, 'success')
            self.assertIsNotNone(self.contenthost.package_search(
                self.client.hostname, FAKE_2_CUSTOM_PACKAGE))

    @tier3
    def test_positive_fetch_registered_by(self):
        """Register a host with activation key and fetch host's 'Registered by'
        field value.

        @id: 5c6dbb5d-bd26-4439-ab04-536a6ad012b9

        @expectedresults: 'Registered By' field on content host page points to
        activation key which was used to register the host

        @BZ: 1380117

        @CaseLevel: System
        """
        with Session(self.browser):
            result = self.contenthost.fetch_parameters(
                self.client.hostname,
                [['Details', 'Registered By']],
            )
            self.assertEqual(
                result['Registered By'], self.activation_key.name)

    @skip_if_bug_open('bugzilla', 1429468)
    @tier3
    def test_positive_provisioning_host_link(self):
        """Check that the host link in provisioning tab of content host page
         point to the host details page.

        @id: 28f5fb0e-007b-4ee6-876e-9693fb7f5841

        @expectedresults: The Provisioning host details name link at
        content_hosts/provisioning point to host detail page eg: hosts/hostname

        @BZ: 1429468

        @CaseLevel: System
        """
        with Session(self.browser):
            # open the content host
            self.contenthost.search_and_click(self.client.hostname)
            # open the provisioning tab of the content host
            self.contenthost.click(
                tab_locators['contenthost.tab_provisioning_details'])
            # click the name field value that contain the hostname
            self.contenthost.click(
                tab_locators['contenthost.tab_provisioning_details_host_link'])
            # assert that the current url is equal to:
            # server_host_url/hosts/hostname

            host_url = urljoin(settings.server.get_url(),
                               'hosts/{0}'.format(self.client.hostname))
            self.assertEqual(self.browser.current_url, host_url)

    @tier3
    @upgrade
    def test_positive_attached_subscription_link(self):
        """Check that the attached subscriptions link on subscriptions tab
        points to the subscription details page

        @id: bea394a9-b7c9-4128-8803-af5fe698152b

        @expectedresults: Attached subscriptions link points to specific
        subscription details page

        @BZ: 1391200

        @CaseLevel: System
        """
        with Session(self.browser):
            self.contenthost.search_and_click(self.client.hostname)
            self.contenthost.click(
                tab_locators['contenthost.tab_subscriptions'])
            self.contenthost.click(
                tab_locators['contenthost.tab_subscriptions_subscriptions'])
            strategy, value = locators['contenthost.attached_subscription']
            self.contenthost.click((strategy, value % self.product.name))
            # fetch subscription id
            subscription = entities.Subscription().search(query={
                'search': 'name={}'.format(self.product.name)})[0]
            # ensure subscription id is present in current URL
            subs_url_id = re.search(
                '(?<=subscriptions/)([0-9])+', self.browser.current_url)
            self.assertIsNotNone(subs_url_id)
            self.assertEqual(int(subs_url_id.group(0)), subscription.id)
            # ensure subscription details page is displayed by fetching
            # subscription name
            strategy, value = locators['subs.details_field_value']
            name = self.subscriptions.wait_until_element((
                strategy, value % 'Name')).text
            self.assertEqual(name, subscription.name)
