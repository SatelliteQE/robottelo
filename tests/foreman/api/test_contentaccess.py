# -*- encoding: utf-8 -*-
"""Test for Content Access (Golden Ticket) API

:Requirement: Content Access

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: high

:Upstream: No
"""
from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier2,
)
from robottelo.test import APITestCase


class ContentAccessTestCase(APITestCase):
    """Content Access API tests."""

    @classmethod
    def setUp(self):
        """Setup must ensure there is an Org with Golden Ticket enabled.

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

            1. Create a new organization.
            2. Create a Product and CV for org.
            3. Add a repository pointing to a real repo which requires a
               RedHat subscription to access.
            4. Create Content Host and assign that gated repos to it.
            5. Create Host with no attached subscriptions.
            6. Use either option 1 or option 2 (described above) to activate
               the Golden Ticket.
            7. Sync the gated repository.

        """
        super(ContentAccessTestCase, self).setUp()

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_positive_list_hosts_applicable(self):
        """Request `errata/hosts_applicable` and assert the host with no
        attached subscriptions is present.

        :id: 68ed5b10-7a45-4f2d-93ed-cffa737211d5

        :steps:

            1. Request errata/hosts_applicable for organization created on
               setUp.

        :CaseAutomation: notautomated

        :expectedresults:
            1. Assert the host with no attached subscription is listed to have
               access to errata content.
        """
