"""Test for Capsule related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: ForemanProxy

:Team: Platform

:CaseImportance: High

"""

import json
import os

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.content_info import get_repo_files_urls_by_url
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture(scope='module')
def capsule_sync_setup(
    capsule_upgrade_shared_satellite, capsule_upgrade_shared_capsule, upgrade_action
):
    """Pre-upgrade scenario that creates and syncs repository with
    rpm in Satellite which will be synced in post upgrade scenario.

    :id: preupgrade-eb8970fa-98cc-4a99-99fb-1c12c4e319c9

    :steps:
        1. Before Satellite upgrade, sync a RPM repo to Satellite

    :expectedresults:
        1. The repo/rpm should be synced to satellite
        2. Activation key's environment id should be available in the content views environment
            id's list
    """
    target_sat = capsule_upgrade_shared_satellite
    capsule = capsule_upgrade_shared_capsule
    capsule.capsule_setup(sat_host=target_sat)
    cap_smart_proxy = target_sat.api.SmartProxy().search(
        query={'search': f'name = {capsule.hostname}'}
    )[0]
    with (
        SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade,
        SharedResource(capsule.hostname, upgrade_action, target_sat=capsule) as cap_upgrade,
    ):
        test_name = f'capsule_sync_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        cap_smart_proxy.organization = [org]
        cap_smart_proxy.update(['organization'])
        features = json.loads(capsule.get_features())
        lce = target_sat.api.LifecycleEnvironment(
            name=f'{test_name}_lce', organization=org, prior=2
        ).create()
        capsule.nailgun_capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        product = target_sat.api.Product(name=f'{test_name}_prod', organization=org).create()
        repo = target_sat.api.Repository(
            name=f'{test_name}_repo',
            product=product,
            content_type='yum',
            url=settings.repos.yum_1.url,
        ).create()
        repo.sync()
        content_view = target_sat.publish_content_view(org, repo, f'{test_name}_content_view')
        content_view.version[0].promote(data={'environment_ids': lce.id})
        content_view_env_id = [env.id for env in content_view.read().environment]
        ak = target_sat.api.ActivationKey(
            name=f'{test_name}_ak', organization=org.id, environment=lce, content_view=content_view
        ).create()
        assert lce.id in content_view_env_id
        test_data = Box(
            {
                'target_sat': target_sat,
                'capsule': capsule,
                'features': features,
                'org': org,
                'lce': lce,
                'product': product,
                'repo': repo,
                'content_view': content_view,
                'ak': ak,
            }
        )
        sat_upgrade.ready()
        cap_upgrade.ready()
        target_sat._session = None
        capsule._session = None
        yield test_data


@pytest.mark.capsule_upgrades
def test_post_capsule_features(capsule_sync_setup):
    """Post-upgrade scenario that sync capsule from satellite and then
    verifies if the repo/rpm of pre-upgrade scenario is synced to capsule


    :id: 1a50f0ec-482e-11ef-a468-98fa9b11ac24

    :steps:
        1. After satellite upgrade check for enabled features on a Capsule

    :expectedresults:
        1. Capsule features before and after Upgrade match
    """
    pre_features = set(capsule_sync_setup.features)
    capsule = capsule_sync_setup.capsule
    post_features = set(json.loads(capsule.get_features()))
    assert post_features == pre_features, 'capsule features after and before upgrade are differrent'
    capsule.nailgun_smart_proxy.refresh()
    refreshed_features = set(json.loads(capsule.get_features()))
    assert refreshed_features == pre_features, 'capsule features after refresh are differrent'


@pytest.mark.capsule_upgrades
def test_post_user_scenario_capsule_sync(capsule_sync_setup):
    """Post-upgrade scenario that sync capsule from satellite and then
    verifies if the repo/rpm of pre-upgrade scenario is synced to capsule


    :id: postupgrade-eb8970fa-98cc-4a99-99fb-1c12c4e319c9

    :steps:
        1. Run capsule sync post upgrade.
        2. Check if the repo/rpm has been synced to capsule.

    :expectedresults:
        1. The capsule sync should be successful
        2. The repos/rpms from satellite should be synced to satellite

    """
    target_sat = capsule_sync_setup.target_sat
    capsule = capsule_sync_setup.capsule
    org = capsule_sync_setup.org
    lce = capsule_sync_setup.lce
    product = capsule_sync_setup.product
    repo = capsule_sync_setup.repo
    content_view = capsule_sync_setup.content_view

    capsule.nailgun_capsule.content_sync(timeout=7200)

    sat_repo_url = target_sat.get_published_repo_url(
        org=org.label,
        lce=lce.label,
        cv=content_view.label,
        prod=product.label,
        repo=repo.label,
    )
    cap_repo_url = capsule.get_published_repo_url(
        org=org.label,
        lce=lce.label,
        cv=content_view.label,
        prod=product.label,
        repo=repo.label,
    )
    sat_files_urls = get_repo_files_urls_by_url(sat_repo_url)
    cap_files_urls = get_repo_files_urls_by_url(cap_repo_url)
    assert (
        len(sat_files_urls) == constants.FAKE_1_YUM_REPOS_COUNT
    ), 'upstream and satellite repo rpm counts are differrent'
    assert len(sat_files_urls) == len(
        cap_files_urls
    ), 'satellite and capsule repo rpm counts are differrent'

    sat_files = {os.path.basename(f) for f in sat_files_urls}
    cap_files = {os.path.basename(f) for f in cap_files_urls}
    assert sat_files == cap_files, 'satellite and capsule rpm basenames are differrent'

    for pkg in constants.FAKE_1_YUM_REPO_RPMS:
        assert pkg in sat_files, f'{pkg=} is not in the {repo=} on satellite'
        assert pkg in cap_files, f'{pkg=} is not in the {repo=} on capsule'

    sat_files_md5 = [target_sat.checksum_by_url(url) for url in sat_files_urls]
    cap_files_md5 = [target_sat.checksum_by_url(url) for url in cap_files_urls]
    assert sat_files_md5 == cap_files_md5, 'satellite and capsule rpm md5sums are differrent'


@pytest.mark.capsule_upgrades
def test_post_user_scenario_capsule_sync_yum_repo(capsule_sync_setup):
    """Post-upgrade scenario that creates and sync repository with
    rpm, sync capsule with satellite and verifies if the repo/rpm in
    satellite is synced to capsule.

    :id: postupgrade-7c1d3441-3e8d-4ac2-8102-30e18274658c

    :steps:
        1. Post Upgrade , Sync a repo/rpm in satellite.
        2. Run capsule sync.
        3. Check if the repo/rpm has been synced to capsule.

    :expectedresults:
        1. The repo/rpm should be synced to satellite
        2. Capsule sync should be successful
        3. The repo/rpm from satellite should be synced to capsule

    """
    target_sat = capsule_sync_setup.target_sat
    capsule = capsule_sync_setup.capsule
    org = capsule_sync_setup.org
    lce = capsule_sync_setup.lce
    product = capsule_sync_setup.product
    repo = target_sat.api.Repository(
        name='post_upgrade_sync_repo',
        product=product,
        content_type='yum',
        url=settings.repos.yum_2.url,
    ).create()
    repo.sync()
    content_view = target_sat.publish_content_view(org, repo, 'post_upgrade_sync_content_view')
    content_view.version[0].promote(data={'environment_ids': lce.id})
    content_view_env_id = [env.id for env in content_view.read().environment]
    ak = target_sat.api.ActivationKey(
        name='post_upgrade_sync_ak', organization=org.id, environment=lce, content_view=content_view
    ).create()
    ak_env = ak.environment.read()
    assert ak_env.id in content_view_env_id
    capsule.nailgun_capsule.content_sync(timeout=7200)

    sat_repo_url = target_sat.get_published_repo_url(
        org=org.label,
        lce=lce.label,
        cv=content_view.label,
        prod=product.label,
        repo=repo.label,
    )
    cap_repo_url = capsule.get_published_repo_url(
        org=org.label,
        lce=ak_env.label,
        cv=content_view.label,
        prod=product.label,
        repo=repo.label,
    )

    sat_files_urls = get_repo_files_urls_by_url(sat_repo_url)
    cap_files_urls = get_repo_files_urls_by_url(cap_repo_url)
    assert (
        len(sat_files_urls) == constants.FAKE_1_YUM_REPOS_COUNT
    ), 'upstream and satellite repo rpm counts are differrent'
    assert len(sat_files_urls) == len(
        cap_files_urls
    ), 'satellite and capsule repo rpm counts are differrent'

    sat_files = {os.path.basename(f) for f in sat_files_urls}
    cap_files = {os.path.basename(f) for f in cap_files_urls}
    assert sat_files == cap_files, 'satellite and capsule rpm basenames are differrent'

    for pkg in constants.FAKE_1_YUM_REPO_RPMS:
        assert pkg in sat_files, f'{pkg=} is not in the {repo=} on satellite'
        assert pkg in cap_files, f'{pkg=} is not in the {repo=} on capsule'

    sat_files_md5 = [target_sat.checksum_by_url(url) for url in sat_files_urls]
    cap_files_md5 = [target_sat.checksum_by_url(url) for url in cap_files_urls]
    assert sat_files_md5 == cap_files_md5, 'satellite and capsule rpm md5sums are differrent'
