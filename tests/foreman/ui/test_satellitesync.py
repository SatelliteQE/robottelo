# -*- encoding: utf-8 -*-
"""Test class for InterSatellite Sync feature"""

from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier3
)
from robottelo.test import UITestCase


class InterSatelliteSyncTestCase(UITestCase):
    """Implements InterSatellite Sync tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_show_repo_export_history(self):
        """Product history shows repo export history on export.

        @feature: ISS - Export

        @steps:

        1. Export a repo to a specified location in settings.

        @assert: Repo/Product history should reflect the export history with
        user and time.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_show_cv_export_history(self):
        """CV history shows CV version export history on export.

        @feature: ISS - Export

        @steps:

        1. Export a CV to a specified location in settings.

        @assert: CV history should reflect the export history with user,
        version, action and time.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_cdn_url(self):
        """Update CDN URL to import from upstream.

        @feature: ISS - Import

        @steps:

        1. In upstream, Export Redhat repo/CV to a directory.
        2. Copy exported contents to /var/www/html.
        3. In downstream, Update CDN URL with step 2 location to import the
        Redhat contents.
        4. Enable and sync the imported repo from Redhat Repositories page.

        @assert:

        1. The CDN URL is is updated successfully.
        2. The imported repo is enabled and sync.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_cdn_url(self):
        """Update non existing CDN URL to import from upstream.

        @feature: ISS - Import

        @steps:

        1. In downstream, Update CDN URL with some non existing url.
        4. Attempt to Enable and sync some repo from Redhat Repositories page.

        @assert:

        1. The CDN URL is not allowed to update any non existing url.
        2. None of the repo is allowed to enable and sync.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_restrict_other_redhat_repo_import(self):
        """Restrict the import/sync of non exported repos.

        @feature: ISS - Import

        @steps:

        1. Export Red Hat YUM repo to path which will be accessible over HTTP.
        2. Define the CDN URL the same as the exported HTTP URL.
        3. Attempt to Import/Enable non exported repos from Redhat Repositories
        page.

        @assert: The import of non exported repos is restricted.

        @status: Manual
        """
