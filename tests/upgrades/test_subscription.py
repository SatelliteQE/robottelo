"""Test for subscription related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SubscriptionManagement

:Team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker import Broker
from manifester import Manifester

from robottelo import constants
from robottelo.config import settings


class TestManifestScenarioRefresh:
    """
    The scenario to test the refresh of a manifest created before upgrade.
    """

    @pytest.mark.pre_upgrade
    def test_pre_manifest_scenario_refresh(
        self, upgrade_entitlement_manifest_org, target_sat, save_test_data
    ):
        """Before upgrade, upload & refresh the manifest.

        :id: preupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Before Satellite upgrade, upload and refresh manifest.

        :expectedresults: Manifest should be uploaded and refreshed successfully.
        """
        org = upgrade_entitlement_manifest_org
        history = target_sat.cli.Subscription.manifest_history({'organization-id': org.id})
        assert f'{org.name} file imported successfully.' in ''.join(history)

        sub = target_sat.api.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        assert sub.search()
        save_test_data({'org_name': f'{upgrade_entitlement_manifest_org.name}'})

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
        assert "Subscriptions deleted by foreman_admin" == history[0]['statusMessage']


class TestSubscriptionAutoAttach:
    """
    The scenario to test auto-attachment of subscription on the client registered before
    upgrade.
    """

    @pytest.mark.rhel_ver_list('8')
    @pytest.mark.no_containers
    @pytest.mark.pre_upgrade
    def test_pre_subscription_scenario_auto_attach(
        self,
        target_sat,
        save_test_data,
        rhel_contenthost,
        upgrade_entitlement_manifest_org,
        upgrade_entitlement_manifest,
    ):
        """Create content host and register with Satellite

        :id: preupgrade-940fc78c-ffa6-4d9a-9c4b-efa1b9480a22

        :steps:
            1. Before Satellite upgrade.
            2. Create new Organization and Location.
            3. Upload a manifest in it.
            4. Create a AK with 'auto-attach False' and without Subscription add in it.
            5. Create a content host.

        :expectedresults:
            1. Content host should be created.
        """
        _, manifester = upgrade_entitlement_manifest
        org = upgrade_entitlement_manifest_org
        rhel_contenthost._skip_context_checkin = True
        lce = target_sat.api.LifecycleEnvironment(organization=org).create()
        rh_repo_id = target_sat.api_factory.enable_sync_redhat_repo(
            constants.REPOS['rhel8_bos'], org.id
        )
        rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
        assert rh_repo.content_counts['rpm'] >= 1
        content_view = target_sat.publish_content_view(org, rh_repo)
        content_view.version[-1].promote(data={'environment_ids': lce.id})
        subscription = target_sat.api.Subscription(organization=org.id).search(
            query={'search': f'name="{constants.DEFAULT_SUBSCRIPTION_NAME}"'}
        )
        assert len(subscription)
        activation_key = target_sat.api.ActivationKey(
            content_view=content_view,
            organization=org,
            environment=lce,
            auto_attach=False,
        ).create()
        activation_key.add_subscriptions(data={'subscription_id': subscription[0].id})
        rhel_contenthost.install_katello_ca(target_sat)
        rhel_contenthost.register_contenthost(org=org.name, activation_key=activation_key.name)
        assert rhel_contenthost.subscribed
        save_test_data(
            {
                'rhel_client': rhel_contenthost.hostname,
                'org_name': org.name,
                'allocation_uuid': manifester.allocation_uuid,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_subscription_scenario_auto_attach)
    def test_post_subscription_scenario_auto_attach(self, request, target_sat, pre_upgrade_data):
        """Run subscription auto-attach on pre-upgrade content host registered
        with Satellite.

        :id: postupgrade-940fc78c-ffa6-4d9a-9c4b-efa1b9480a22

        :steps:
            1. Run subscription auto-attach on content host.
            2. Delete the content host, activation key, location & organization.

        :expectedresults: After upgrade,
            1. Pre-upgrade content host should get subscribed.
            2. All the cleanup should be completed successfully.
        """
        rhel_contenthost = Broker().from_inventory(
            filter=f'@inv.hostname == "{pre_upgrade_data.rhel_client}"'
        )[0]
        host = target_sat.api.Host().search(query={'search': f'name={rhel_contenthost.hostname}'})[
            0
        ]
        target_sat.cli.Host.subscription_auto_attach({'host-id': host.id})
        result = rhel_contenthost.execute('yum install -y zsh')
        assert result.status == 0, 'package was not installed'
        org = target_sat.api.Organization().search(
            query={'search': f'name={pre_upgrade_data.org_name}'}
        )[0]
        request.addfinalizer(org.delete)
        sub = target_sat.api.Subscription(organization=org)
        sub.delete_manifest(data={'organization_id': org.id})
        assert len(sub.search()) == 0
        manifester = Manifester(manifest_category=settings.manifest.entitlement)
        manifester.allocation_uuid = pre_upgrade_data.allocation_uuid
        request.addfinalizer(manifester.delete_subscription_allocation)
