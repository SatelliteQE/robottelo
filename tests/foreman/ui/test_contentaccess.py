# -*- encoding: utf-8 -*-
"""Test for Content Access (Golden Ticket) UI

:Requirement: Content Access

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: high

:Upstream: No
"""
from nailgun import entities
from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier2,
)
from robottelo.test import UITestCase


class ContentAccessTestCase(UITestCase):
    """Implements Content Access (Golden Ticket) tests in UI"""

    @classmethod
    def set_session_org(cls):
        """Create an organization for tests, which will be selected
        automatically

        This method should set `session_org` to a new Org or reuse existing
        org that has Golden ticket enabled
        """
        cls.session_org = entities.Organization().create()

    @classmethod
    def setUp(self):
        """Setup must ensure the current `session_org`  has Golden Ticket
        enabled.

        Option 1) SQL::

            UPDATE
                 cp_owner
            SET
                 content_access_mode = 'org_environment',
                 content_access_mode_list='entitlement,org_environment'
            WHERE account='{org.label}';

        Option 2) manifest::

            Change manifest file as it looks like:

                Consumer:
                    Name: ExampleCorp
                    UUID: c319a1d8-4b30-44cd-b2cf-2ccba4b9a8db
                    Content Access Mode: org_environment
                    Type: satellite

        :steps:

            1. Create a Product and CV for current session_org.
            2. Add a repository pointing to a real repo which requires a
               RedHat subscription to access.
            3. Create Content Host and assign that gated repos to it.
            4. Use either option 1 or option 2 (described above) to activate
               the Golden Ticket.
            5. Sync the gated repository.

        """
        super(ContentAccessTestCase, self).setUp()

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_positive_list_installable_updates(self):
        """Access content hosts and assert all updates are listed on
        packages tab updates and not only those for attached subscriptions.

        :id: 30783c91-c665-4c39-8b3b-b7456bde76f2

        :steps:

            1. Access Content-Host listing page.

        :CaseAutomation: notautomated

        :expectedresults:
            1. All updates are available independent of subscription because
               Golden Ticket is enabled.
        """

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_positive_list_available_packages(self):
        """Access content hosts and assert all packages are listed on
        installable updates and not only those for attached subscriptions.

        :id: 37383e25-7b1d-433e-9e05-faaa8ec70ee8

        :steps:

            1. Access Content-Host Packages tab.

        :CaseAutomation: notautomated

        :expectedresults:
            1. All packages are available independent
               of subscription because Golden Ticket is enabled.
        """

    @run_only_on('sat')
    @tier1
    @stubbed()
    def test_positive_visual_indicator_on_hosts_subscription(self):
        """Access content hosts subscription tab and assert a visual indicator
        is present highlighting that organization hosts have unrestricted
        access to repository content.

        :id: f8fc0bd2-c92f-4706-9921-4e331762170d

        :steps:

            1. Access Content-Host Subscription tab.

        :CaseAutomation: notautomated

        :expectedresults:
            1. A visual alert is present at the top of the subscription tab
               saying: "Access to repositories is unrestricted in
               this organizataion. Hosts can consume all repositories available
               in the Content View they are registered to, regardless of
               subscription status".
        """

    @run_only_on('sat')
    @tier1
    @stubbed()
    def test_positive_visual_indicator_on_activation_key_details(self):
        """Access AK details subscription tab and assert a visual indicator
        is present highlighting that organization hosts have unrestricted
        access to repository content.

        :id: 94ba1113-11cb-43b2-882e-bf45b5355d9b

        :steps:

            1. Access Ak details Subscription tab.

        :CaseAutomation: notautomated

        :expectedresults:
            1. A visual alert is present at the top of the subscription tab
               saying: "Access to repositories is unrestricted in this
               organizataion. Hosts can consume all repositories available in
               the Content View they are registered to, regardless of
               subscription status".
        """

    @run_only_on('sat')
    @tier1
    @stubbed()
    def test_positive_visual_indicator_on_manifest(self):
        """Access org manifest page and assert a visual indicator
        is present highlighting that organization hosts have unrestricted
        access to repository content.

        :id: a9c2d2b7-17ab-441b-978d-24dc80f35a4b

        :steps:

            1. Access org manifest page.

        :CaseAutomation: notautomated

        :expectedresults:
            1. A visual alert is present at the top of the
               subscription tab saying: "Access to repositories is unrestricted
               in this organizataion. Hosts can consume all repositories
               available in the Content View they are registered to, regardless
               of subscription status".
        """

    @run_only_on('sat')
    @tier1
    @stubbed()
    def test_negative_visual_indicator_with_restricted_subscription(self):
        """Access AK details subscription tab and assert a visual indicator
        is NOT present if organization has no Golden Ticket Enabled.

        :id: ce5f3017-a449-45e6-8709-7d4f7b5f7a4d

        :steps:

            1. Change to a restricted organization (with no GT enabled).
            2. Access Ak details Subscription tab.

        :CaseAutomation: notautomated

        :expectedresults:
            1. Assert GoldenTicket  visual alert is NOT present.
        """

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_negative_list_available_packages(self):
        """Access content hosts and assert restricted packages are not listed
        on installable updates but only those for attached subscriptions.

        :id: 87a502ff-bb3c-4da4-ab88-b49a4fcdf3fb

        :steps:

            1. Change to a restricted organization (with no GT enabled).
            2. Access Content-Host Packages tab.

        :CaseAutomation: notautomated

        :expectedresults:
            1. Restricted packages are NOT available but only
               those for atached subscriptions because Golden Ticket is NOT
               enabled.
        """
