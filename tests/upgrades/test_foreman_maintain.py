"""Test for Foreman-maintain related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from unittest2.case import TestCase
from upgrade_tests import post_upgrade, pre_upgrade


class ScenarioForemanMaintain(TestCase):
    """The test class contains pre-upgrade and post-upgrade scenarios to test
    foreman-maintain utility

    Test Steps:

    1. Before Satellite upgrade, Perform test for
       foreman-maintain list-versions.
    2. Upgrade satellite/capsule.
    3. Perform tests for foreman-maintain list-versions, after upgrade.
    4. Check if tests passed.

    """

    @pre_upgrade
    def test_pre_foreman_maintain_upgrade_list_versions(self):
        """Pre-upgrade scenario that tests list of versions
        satellite can upgrade.

        :id: preupgrade-2d92ce08-0243-4f10-b4d0-b9e8a12f1dbf

        :steps:
            1. Run foreman-maintain upgrade list-versions.

        :expectedresults: Versions should be z-stream and next version.

         """

    @post_upgrade
    def test_post_foreman_maintain_upgrade_list_versions(self):
        """Post-upgrade scenario that tests list of versions
        satellite can upgrade.

        :id: postupgrade-2d92ce08-0243-4f10-b4d0-b9e8a12f1dbf

        :steps:
            1. Run foreman-maintain upgrade list-versions.

        :expectedresults: Versions should be next z-stream.

         """
