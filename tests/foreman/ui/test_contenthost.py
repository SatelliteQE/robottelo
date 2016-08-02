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
from nailgun import entities
from robottelo.cli.factory import (
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.constants import (
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_GROUP,
    FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_0_YUM_REPO,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_1_ERRATA_ID,
    FAKE_2_CUSTOM_PACKAGE,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import run_in_one_thread, skip_if_not_set, tier3
from robottelo.test import UITestCase
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
        })
        setup_org_for_a_custom_repo({
            'url': FAKE_0_YUM_REPO,
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })

    def setUp(self):
        """Create a VM, subscribe it to satellite-tools repo, install
        katello-ca and katello-agent packages"""
        super(ContentHostTestCase, self).setUp()
        self.client = VirtualMachine(distro='rhel71')
        self.client.create()
        self.client.install_katello_ca()
        result = self.client.register_contenthost(
            self.session_org.label, self.activation_key.name)
        self.assertEqual(result.return_code, 0)
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_agent()

    def tearDown(self):
        """Destroy the VM"""
        self.client.destroy()
        super(ContentHostTestCase, self).tearDown()

    @tier3
    def test_positive_install_package(self):
        """Install a package to a host remotely

        @id: 13b9422d-4b7a-4068-9a57-a94602cd6410

        @assert: Package was successfully installed

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

        @Assert: Package was successfully removed

        @CaseLevel: System
        """
        self.client.download_install_rpm(
            FAKE_0_YUM_REPO,
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

        @Assert: Package was successfully upgraded

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
    def test_positive_install_package_group(self):
        """Install a package group to a host remotely

        @id: a43fb21b-5f6a-4f14-8cd6-114ec287540c

        @Assert: Package group was successfully installed

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

        @Assert: Package group was successfully removed

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
    def test_positive_install_errata(self):
        """Install a errata to a host remotely

        @id: 13b9422d-4b7a-4068-9a57-a94602cd6410

        @assert: Errata was successfully installed

        @CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with Session(self.browser):
            result = self.contenthost.install_errata(
                self.client.hostname,
                FAKE_1_ERRATA_ID,
            )
            self.assertEqual(result, 'success')
            self.assertIsNotNone(self.contenthost.package_search(
                self.client.hostname, FAKE_2_CUSTOM_PACKAGE))
