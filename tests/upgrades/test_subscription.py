"""Test for subscription related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: SubscriptionManagement

:Team: Proton

:CaseImportance: High

"""

import pytest


class TestManifestScenarioRefresh:
    """
    The scenario to test the refresh of a manifest created before upgrade.
    """

    @pytest.mark.pre_upgrade
    def test_pre_manifest_scenario_refresh(
        self, sca_manifest_org_for_upgrade, target_sat, save_test_data
    ):
        """Before upgrade, upload & refresh the manifest.

        :id: preupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Before Satellite upgrade, upload and refresh manifest.

        :expectedresults: Manifest should be uploaded and refreshed successfully.
        """
        org = sca_manifest_org_for_upgrade
        history = target_sat.cli.Subscription.manifest_history({'organization-id': org.id})
        assert f'{org.name} file imported successfully.' in ''.join(history)

        sub = target_sat.api.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        assert sub.search()
        save_test_data({'org_name': f'{sca_manifest_org_for_upgrade.name}'})

    @pytest.mark.post_upgrade(depend_on=test_pre_manifest_scenario_refresh)
    def test_post_manifest_scenario_refresh(self, request, target_sat, pre_upgrade_data):
        """After upgrade, Check the manifest refresh and delete functionality.

        :id: postupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Refresh manifest.
            2. Delete manifest.

        :expectedresults: After upgrade,
            1. Pre-upgrade manifest should be refreshed and deleted.
        """
        org_name = pre_upgrade_data.org_name
        org = target_sat.api.Organization().search(query={'search': f'name={org_name}'})[0]
        request.addfinalizer(org.delete)
        sub = target_sat.api.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        assert sub.search()
        sub.delete_manifest(data={'organization_id': org.id})
        assert len(sub.search()) == 0
        history = target_sat.api.Subscription(organization=org).manifest_history(
            data={'organization_id': org.id}
        )
        assert history[0]['statusMessage'] == "Subscriptions deleted by foreman_admin"
