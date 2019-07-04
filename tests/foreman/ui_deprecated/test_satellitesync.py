# -*- encoding: utf-8 -*-
"""Test class for InterSatellite Sync feature

:Requirement: Satellitesync

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier3,
    upgrade
)
from robottelo.test import UITestCase


class InterSatelliteSyncTestCase(UITestCase):
    """Implements InterSatellite Sync tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_show_repo_export_history(self):
        """Product history shows repo export history on export.

        :id: 01d82253-081b-4d11-9a5b-e6052173fe47

        :steps: Export a repo to a specified location in settings.

        :expectedresults: Repo/Product history should reflect the export
            history with user and time.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_show_cv_export_history(self):
        """CV history shows CV version export history on export.

        :id: 06e26cca-e262-4eff-b8d7-fbca504a8acb

        :steps: Export a CV to a specified location in settings.

        :expectedresults: CV history should reflect the export history with
            user, version, action and time.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_cdn_url(self):
        """Update CDN URL to import from upstream.

        :id: 5ff30764-a1b1-48df-a6a1-0f1d23f883b9

        :steps:

            1. In upstream, Export Redhat repo/CV to a directory.
            2. Copy exported contents to /var/www/html.
            3. In downstream, Update CDN URL with step 2 location to import the
               Redhat contents.
            4. Enable and sync the imported repo from Redhat Repositories page.

        :expectedresults:

            1. The CDN URL is is updated successfully.
            2. The imported repo is enabled and sync.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_cdn_url(self):
        """Update non existing CDN URL to import from upstream.

        :id: 4bf74712-dac8-447b-9c9f-227a41cdec4d

        :steps:

            1. In downstream, Update CDN URL with some non existing url.
            2. Attempt to Enable and sync some repo from Redhat Repositories
               page.

        :expectedresults:

            1. The CDN URL is not allowed to update any non existing url.
            2. None of the repo is allowed to enable and sync.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_restrict_other_redhat_repo_import(self):
        """Restrict the import/sync of non exported repos.

        :id: 7091ca13-7f58-4733-87d5-1fa3670bfcee

        :steps:

            1. Export Red Hat YUM repo to path which will be accessible over
                HTTP.
            2. Define the CDN URL the same as the exported HTTP URL.
            3. Attempt to Import/Enable non exported repos from Redhat
               Repositories page.

        :expectedresults: The import of non exported repos is restricted.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
