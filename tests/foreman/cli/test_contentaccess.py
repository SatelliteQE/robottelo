# -*- encoding: utf-8 -*-
""""Test for Content Access (Golden Ticket) CLI

:Requirement: Content Access

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: high

:Upstream: No
"""
from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier2,
)
from robottelo.test import CLITestCase


class ContentAccessTestCase(CLITestCase):
    """Content Access CLI tests."""

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
            5. Use either option 1 or option 2 (described above) to activate
               the Golden Ticket.
            6. Sync the gated repository.
        """
        super(ContentAccessTestCase, self).setUp()

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_positive_list_installable_updates(self):
        """Run `hammer host errata list` and assert all updates are listed on
        packages tab updates and not only those for attached subscriptions.

        :id: 4feb692c-165b-4f96-bb97-c8447bd2cf6e

        :steps:

            1. Run `hammer host errata list` specifying unrestricted org.

        :CaseAutomation: notautomated

        :expectedresults:
            1. All updates are available independent of subscription because
               Golden Ticket is enabled.
        """

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_negative_rct_not_shows_golden_ticket_enabled(self):
        """Assert restricted manifest has no Golden Ticket enabled .

        :id: 754c1be7-468e-4795-bcf9-258a38f3418b

        :steps:

            1. Run `rct cat-manifest /tmp/restricted_manifest.zip`.

        :CaseAutomation: notautomated

        :expectedresults:
            1. Assert `Content Access Mode: org_environment` is not present.
        """

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_positive_rct_shows_golden_ticket_enabled(self):
        """Assert unrestricted manifest has Golden Ticket enabled .

        :id: 0c6e2f88-1a86-4417-9248-d7bd20584197

        :steps:

            1. Run `rct cat-manifest /tmp/unrestricted_manifest.zip`.

        :CaseAutomation: notautomated

        :expectedresults:
            1. Assert `Content Access Mode: org_environment` is present.
        """
