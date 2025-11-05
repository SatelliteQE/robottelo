"""Test for subscription related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: SubscriptionManagement

:Team: Proton

:CaseImportance: High

"""

import os
from time import sleep

from box import Box
from fauxfactory import gen_alpha
from manifester import Manifester
import pytest

from robottelo.config import settings
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def subscription_upgrade_manifest():
    with Manifester(manifest_category=settings.manifest.golden_ticket) as manifest:
        yield manifest


@pytest.fixture
def manifest_scenario_refresh_setup(
    subscription_upgrade_shared_satellite, upgrade_action, subscription_upgrade_manifest
):
    """Before upgrade, upload & refresh the manifest.

    :steps:
        1. Before Satellite upgrade, upload and refresh manifest.

    :expectedresults: Manifest should be uploaded and refreshed successfully.
    """
    target_sat = subscription_upgrade_shared_satellite
    manifest = subscription_upgrade_manifest
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'subscription_upgrade_{gen_alpha()}'
        # Simultaneously creating multiple orgs has a high failure rate,
        # so stagger the API calls.
        xdist_worker_splay = (int(os.environ.get('PYTEST_XDIST_WORKER')[-1]) + 1) * 50
        sleep(xdist_worker_splay)
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        target_sat.upload_manifest(org.id, manifest.content)
        history = target_sat.cli.Subscription.manifest_history({'organization-id': org.id})
        assert f'{org.name} file imported successfully.' in ''.join(history)

        sub = target_sat.api.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        assert sub.search()
        sat_upgrade.ready()
        test_data = Box(
            {
                'org': org,
                'satellite': target_sat,
            }
        )
        yield test_data


@pytest.mark.subscription_upgrades
@pytest.mark.manifester
def test_manifest_scenario_refresh(manifest_scenario_refresh_setup):
    """After upgrade, Check the manifest refresh and delete functionality.

    :id: 29b246aa-2c7f-49f4-870a-7a0075e184b1

    :steps:
        1. Refresh manifest.
        2. Delete manifest.

    :expectedresults: After upgrade,
        1. Pre-upgrade manifest should be refreshed and deleted.
    """
    org = manifest_scenario_refresh_setup.org
    target_sat = manifest_scenario_refresh_setup.satellite
    sub = target_sat.api.Subscription(organization=org)
    sub.refresh_manifest(data={'organization_id': org.id})
    assert sub.search()
    sub.delete_manifest(data={'organization_id': org.id})
    assert len(sub.search()) == 0
    history = target_sat.api.Subscription(organization=org).manifest_history(
        data={'organization_id': org.id}
    )
    assert history[0]['statusMessage'] == "Subscriptions deleted by foreman_admin"
