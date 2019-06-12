"""Test for subscription related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from robottelo import manifests
from robottelo.test import APITestCase
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import delete_manifest


class Scenario_manifest_refresh(APITestCase):
    """The test class contains pre-upgrade and post-upgrade scenarios to test
    manifest refresh before and after upgrade

    Test Steps:

    1. Before Satellite upgrade, upload a manifest.
    2. Refresh the manifest.
    3. Upgrade satellite.
    4. Refresh the manifest.
    5. Delete the manifest.

    """
    @classmethod
    def setUpClass(cls):
        cls.org_name = 'preupgrade_subscription_org'

    @pre_upgrade
    def test_pre_manifest_scenario_refresh(self):
        """Pre-upgrade scenario that upload and refresh manifest in satellite
         which will be refreshed in post upgrade scenario.


        :id: preupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Before Satellite upgrade, upload and refresh manifest.

        :expectedresults: Manifest should upload and refresh successfully.
         """
        org = entities.Organization(name=self.org_name).create()
        manifests.upload_manifest_locked(org.id, interface=manifests.INTERFACE_API)
        history = entities.Subscription(organization=org).manifest_history(
            data={'organization_id': org.id})
        self.assertEqual(
            "{0} file imported successfully.".format(org.name),
            history[0]['statusMessage'])
        sub = entities.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        self.assertGreater(len(sub.search()), 0)

    @post_upgrade
    def test_post_manifest_scenario_refresh(self):
        """Post-upgrade scenario that verifies manifest refreshed successfully
        and deleted successfully.

        :id: postupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Refresh manifest
            2. Delete manifest

        :expectedresults:
            1. The manifest should refresh and delete successfully.
         """
        org = entities.Organization().search(query={
            'search': 'name={0}'.format(self.org_name)})[0]
        sub = entities.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        self.assertGreater(len(sub.search()), 0)
        delete_manifest(self.org_name)
        history = entities.Subscription(organization=org).manifest_history(
            data={'organization_id': org.id})
        self.assertEqual("Subscriptions deleted by foreman_admin",
                         history[0]['statusMessage'])
