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

from robottelo import constants
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


@pytest.fixture
def subscription_auto_attach_setup(
    subscription_upgrade_shared_satellite,
    upgrade_action,
    rhel_contenthost,
    subscription_upgrade_manifest,
):
    """Create content host and register with Satellite

    :steps:
        1. Before Satellite upgrade.
        2. Create new Organization and Location.
        3. Upload a manifest in it.
        4. Create a AK with 'auto-attach False' and without Subscription add in it.
        5. Create a content host.

    :expectedresults:
        1. Content host should be created.
    """
    target_sat = subscription_upgrade_shared_satellite
    manifest = subscription_upgrade_manifest
    rhel_contenthost._skip_context_checkin = True
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'auto_attach_upgrade_{gen_alpha()}'
        # Simultaneously creating multiple orgs has a high failure rate,
        # so stagger the API calls.
        xdist_worker_splay = int(os.environ.get('PYTEST_XDIST_WORKER')[-1]) * 10
        sleep(xdist_worker_splay)
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        target_sat.upload_manifest(org.id, manifest.content)
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        library_id = int(
            target_sat.cli.LifecycleEnvironment.list(
                {'organization-id': org.id, 'library': 'true'}
            )[0]['id']
        )
        lce = target_sat.api.LifecycleEnvironment(
            name=f'{test_name}_lce', organization=org, prior=library_id
        ).create()
        if rhel_contenthost.os_version.major > 7:
            rh_repo_id = target_sat.api_factory.enable_sync_redhat_repo(
                constants.REPOS[f'rhel{rhel_contenthost.os_version.major}_bos'], org.id
            )
        else:
            rh_repo_id = target_sat.api_factory.enable_sync_redhat_repo(
                constants.REPOS[f'rhel{rhel_contenthost.os_version.major}'], org.id
            )
        rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
        assert rh_repo.content_counts['rpm'] >= 1
        content_view = target_sat.publish_content_view(org, rh_repo, f'{test_name}_content_view')
        content_view.version[-1].promote(data={'environment_ids': lce.id})
        subscription = target_sat.api.Subscription(organization=org.id).search(
            query={'search': f'name="{constants.DEFAULT_SUBSCRIPTION_NAME}"'}
        )
        assert len(subscription)
        activation_key = target_sat.api.ActivationKey(
            name=f'{test_name}_ak',
            content_view=content_view,
            organization=org.id,
            environment=lce,
            auto_attach=False,
        ).create()
        rhel_contenthost.api_register(
            target_sat,
            organization=org,
            location=location,
            activation_keys=[activation_key.name],
        )
        assert rhel_contenthost.subscribed
        test_data = Box(
            {
                'rhel_client': rhel_contenthost,
                'org': org,
                'satellite': target_sat,
            }
        )
        sat_upgrade.ready()
        yield test_data


@pytest.mark.subscription_upgrades
@pytest.mark.rhel_ver_list([7, 8, 9, 10])
@pytest.mark.no_containers
@pytest.mark.manifester
def test_subscription_scenario_auto_attach(subscription_auto_attach_setup):
    """Run subscription auto-attach on pre-upgrade content host registered
    with Satellite.

    :id: 940fc78c-ffa6-4d9a-9c4b-efa1b9480a22

    :steps:
        1. Run subscription auto-attach on content host.
        2. Delete the manifest from the Satellite

    :expectedresults: After upgrade,
        1. Pre-upgrade content host should get subscribed.
        2. All the cleanup should be completed successfully.
    """
    rhel_contenthost = subscription_auto_attach_setup.rhel_client
    target_sat = subscription_auto_attach_setup.satellite
    org = subscription_auto_attach_setup.org
    result = rhel_contenthost.execute('yum install -y zsh')
    assert result.status == 0, 'package was not installed'
    sub = target_sat.api.Subscription(organization=org)
    sub.delete_manifest(data={'organization_id': org.id})
    assert len(sub.search()) == 0
