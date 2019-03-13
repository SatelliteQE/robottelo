"""Test class for Custom Sync UI

:Requirement: Sync

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import (
    stubbed,
    tier4,
)
from robottelo.test import UITestCase


class SyncTestCase(UITestCase):
    """Implements Custom Sync tests in UI"""

    @stubbed()
    @tier4
    def test_positive_sync_disconnected_to_connected_rh_repos(self):
        """Migrating from disconnected to connected satellite.

        :id: 03b3d904-1697-441b-bb12-8b353a556218

        :Steps:
            1. Update the link to an internal http link where the content has
                been extracted from ISO's.
            2. Import a valid manifest.
            3. Enable few RedHat repos and Sync them.
            4. Now let's revert back the link to CDN's default link which is,
                'https://cdn.redhat.com'.
            5. Now Navigate to the 'Sync Page' and resync the repos synced
                earlier.

        :expectedresults: 1. Syncing should work fine without any issues. 2.
            Only the deltas are re-downloaded and not the entire repo.  [ Could
            be an exception when 7Server was earlier pointing to 7.1 and
            current 7Server points to latest 7.2] 3. After reverting the link
            the repos should not be seen in 'Others Tab' and should be seen
            only in 'RPM's Tab'.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
