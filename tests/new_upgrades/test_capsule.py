"""Test for Capsule related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: ForemanProxy

:Team: Platform

:CaseImportance: High

"""

import json
import os

import pytest

from box import Box
from fauxfactory import gen_alpha
from robottelo import constants
from robottelo.config import settings
from robottelo.content_info import get_repo_files_urls_by_url
from robottelo.utils.shared_resource import SharedResource


def cleanup(target_sat, content_view, repo, product):
    """
    This function is used to perform the cleanup of created content view, repository and product.
    """
    cv_env_details = content_view.read_json()
    for content in cv_env_details['environments']:
        content_view.delete_from_environment(content['id'])
    content_view.delete()
    repo.delete()
    product.delete()

    # To clean the orphaned content for next run, it is used to fix KCS#4820591
    target_sat.execute('foreman-rake katello:delete_orphaned_content')


# class TestCapsuleFeatures:
@pytest.fixture
def test_pre_capsule_features(capsule_upgrade_shared_satellite, capsule_upgrade_shared_capsule, upgrade_action):
# def test_pre_capsule_features(self, pre_configured_capsule, save_test_data):
    """Pre-upgrade scenario that checks for Capsule enabled features

    :steps:
        1. Before Satellite upgrade check for enabled features on a Capsule

    :expectedresults:
        1. List of Capsule features
    """
    target_sat = capsule_upgrade_shared_satellite
    capsule = capsule_upgrade_shared_capsule
    capsule.capsule_setup(sat_host=target_sat)
    with (SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade,
          SharedResource(capsule.hostname, upgrade_action, target_sat=capsule) as cap_upgrade):
        features = json.loads(capsule.get_features())
        test_data = Box({
            'features': features,
            'target_sat': target_sat,
            'capsule': capsule 
        })
        sat_upgrade.ready()
        cap_upgrade.ready()
        target_sat._session = None
        capsule._session = None
        yield test_data

def test_post_capsule_features(test_pre_capsule_features):
    """Post-upgrade scenario that sync capsule from satellite and then
    verifies if the repo/rpm of pre-upgrade scenario is synced to capsule


    :id: 1a50f0ec-482e-11ef-a468-98fa9b11ac24

    :steps:
        1. After satellite upgrade check for enabled features on a Capsule

    :expectedresults:
        1. Capsule features before and after Upgrade match
    """
    pre_features = set(test_pre_capsule_features.features)
    capsule = test_pre_capsule_features.capsule
    post_features = set(json.loads(capsule.get_features()))
    assert (
        post_features == pre_features
    ), 'capsule features after and before upgrade are differrent'
    capsule.nailgun_smart_proxy.refresh()
    refreshed_features = set(json.loads(capsule.get_features()))
    assert refreshed_features == pre_features, 'capsule features after refresh are differrent'


#class TestCapsuleSync:
#    """
#    Test class contains pre-upgrade and post-upgrade scenario to test the capsule sync
#    in the post-upgrade of pre-upgraded repo.
#    """
#
# @pytest.mark.pre_upgrade
# def test_pre_user_scenario_capsule_sync(self, target_sat, default_org, save_test_data):
@pytest.fixture
def capsule_sync_setup(capsule_upgrade_shared_satellite, capsule_upgrade_shared_capsule, upgrade_action):
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
    
    # ak_name = (
    #     settings.upgrade.capsule_ak[settings.upgrade.os]
    #     or settings.upgrade.custom_capsule_ak[settings.upgrade.os]
    # )
    # ak = target_sat.api.ActivationKey(organization=default_org).search(
    #     query={'search': f'name={ak_name}'}
    # )[0]
    # ak_env = ak.environment.read()
    
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade, SharedResource(capsule.hostname, upgrade_action, target_sat=capsule) as cap_upgrade:
        test_name = f'capsule_sync_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        cap_smart_proxy.organization = [org]
        cap_smart_proxy.update(['organization'])
        lce = target_sat.api.LifecycleEnvironment(name=f'{test_name}_lce', organization=org, prior=2).create()
        capsule.nailgun_capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        product = target_sat.api.Product(name=f'{test_name}_prod', organization=org).create()
        repo = target_sat.api.Repository(name=f'{test_name}_repo', product=product, content_type='yum', url=settings.repos.yum_1.url).create()
        repo.sync()
        content_view = target_sat.publish_content_view(org, repo, f'{test_name}_content_view')
        content_view.version[0].promote(data={'environment_ids': lce.id})
        content_view_env_id = [env.id for env in content_view.read().environment]
        ak = target_sat.api.ActivationKey(name=f'{test_name}_ak', organization=org.id, environment=lce, content_view=content_view).create()
        assert lce.id in content_view_env_id
        test_data = Box({
            'target_sat': target_sat,
            'capsule': capsule,
            'org': org,
            'lce': lce,
            'product': product,
            'repo': repo,
            'content_view': content_view,
            'ak': ak,
        })
        sat_upgrade.ready()
        cap_upgrade.ready()
        target_sat._session = None
        yield test_data
    # save_test_data(
    #     {
    #         'ak_id': ak.id,
    #         'repo_id': repo.id,
    #         'product_id': product.id,
    #         'content_view_id': content_view.id,
    #     }
    # )

def test_post_user_scenario_capsule_sync(capsule_sync_setup, request):
#    self, request, target_sat, pre_configured_capsule, pre_upgrade_data
# ):
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
    ak = capsule_sync_setup.ak

    request.addfinalizer(lambda: cleanup(target_sat, content_view, repo, product))
    # ak = target_sat.api.ActivationKey(id=pre_upgrade_data.get('ak_id')).read()
    # repo = target_sat.api.Repository(id=pre_upgrade_data.get('repo_id')).read()
    # product = target_sat.api.Product(id=pre_upgrade_data.get('product_id')).read()
    # ak_env = ak.environment.read()
    # org = ak.organization.read()
    # content_view = target_sat.api.ContentView(id=pre_upgrade_data.get('content_view_id')).read()
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


class TestCapsuleSyncNewRepo:
    """
    Test class contains a post-upgrade scenario to test the capsule sync of newly added yum repo.
    """

    @pytest.mark.post_upgrade
    def test_post_user_scenario_capsule_sync_yum_repo(
        self, request, target_sat, pre_configured_capsule, default_org
    ):
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
        request.addfinalizer(lambda: cleanup(target_sat, content_view, repo, product))
        activation_key = (
            settings.upgrade.capsule_ak[settings.upgrade.os]
            or settings.upgrade.custom_capsule_ak[settings.upgrade.os]
        )
        ak = target_sat.api.ActivationKey(organization=default_org).search(
            query={'search': f'name={activation_key}'}
        )[0]
        ak_env = ak.environment.read()
        product = target_sat.api.Product(organization=default_org).create()
        repo = target_sat.api.Repository(product=product, url=settings.repos.yum_1.url).create()
        repo.sync()
        content_view = target_sat.publish_content_view(default_org, repo)
        content_view.read().version[0].promote(data={'environment_ids': ak_env.id})
        content_view_env = [env.id for env in content_view.read().environment]
        assert ak_env.id in content_view_env
        pre_configured_capsule.nailgun_capsule.content_sync(timeout=7200)

        sat_repo_url = target_sat.get_published_repo_url(
            org=default_org.label,
            lce=ak_env.label,
            cv=content_view.label,
            prod=product.label,
            repo=repo.label,
        )
        cap_repo_url = pre_configured_capsule.get_published_repo_url(
            org=default_org.label,
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
