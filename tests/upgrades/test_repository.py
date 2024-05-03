"""Test for Repository related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Repositories

:Team: Phoenix-content

:CaseImportance: High

"""

import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_4_CUSTOM_PACKAGE_NAME,
    REPOS,
)
from robottelo.hosts import ContentHost

UPSTREAM_USERNAME = 'rTtest123'


class TestScenarioRepositoryUpstreamAuthorizationCheck:
    """This test scenario is to verify the upstream username in post-upgrade for a custom
    repository which does have a upstream username but not password set on it in pre-upgrade.

    Test Steps:

        1. Before Satellite upgrade, Create a custom repository and sync it.
        2. Set the upstream username on same repository using foreman-rake.
        3. Upgrade Satellite.
        4. Check if the upstream username value is removed for same repository.
    """

    @pytest.mark.pre_upgrade
    def test_pre_repository_scenario_upstream_authorization(self, target_sat, save_test_data):
        """Create a custom repository and set the upstream username on it.

        :id: preupgrade-11c5ceee-bfe0-4ce9-8f7b-67a835baf522

        :steps:
            1. Create a custom repository and sync it.
            2. Set the upstream username on same repository using foreman-rake.

        :expectedresults:
            1. Upstream username should be set on repository.

        :BZ: 1641785

        :customerscenario: true
        """

        org = target_sat.api.Organization().create()
        custom_repo = target_sat.api_factory.create_sync_custom_repo(org_id=org.id)
        rake_repo = f'repo = Katello::Repository.find_by_id({custom_repo})'
        rake_username = f'; repo.root.upstream_username = "{UPSTREAM_USERNAME}"'
        rake_repo_save = '; repo.save!(validate: false)'
        result = target_sat.execute(
            f"echo '{rake_repo}{rake_username}{rake_repo_save}'|foreman-rake console"
        )
        assert 'true' in result.stdout

        save_test_data({'repo_id': custom_repo})

    @pytest.mark.post_upgrade(depend_on=test_pre_repository_scenario_upstream_authorization)
    def test_post_repository_scenario_upstream_authorization(self, target_sat, pre_upgrade_data):
        """Verify upstream username for pre-upgrade created repository.

        :id: postupgrade-11c5ceee-bfe0-4ce9-8f7b-67a835baf522

        :steps:
            1. Verify upstream username for pre-upgrade created repository using
            foreman-rake.

        :expectedresults:
            1. upstream username should not exists on same repository.

        :BZ: 1641785

        :customerscenario: true
        """

        rake_repo = f"repo = Katello::RootRepository.find_by_id({pre_upgrade_data['repo_id']})"
        rake_username = '; repo.root.upstream_username'
        result = target_sat.execute(f"echo '{rake_repo}{rake_username}'|foreman-rake console")
        assert UPSTREAM_USERNAME not in result.stdout


class TestScenarioCustomRepoCheck:
    """Scenario test to verify if we can create a custom repository and consume it
    via client then we alter the created custom repository and satellite will be able
    to sync back the repo.

    Test Steps:

        1. Before Satellite upgrade.
        2. Create new Organization and Location.
        3. Create Product, custom repo, cv.
        4. Create activation key and add subscription in it.
        5. Create a content host, register and install package on it.
        6. Upgrade Satellite.
        7. Remove Old package and add new package into custom repo.
        8. Sync repo, publish new version of cv.
        9. Try to install new package on client.

    BZ: 1429201,1698549
    """

    @pytest.mark.pre_upgrade
    def test_pre_scenario_custom_repo_check(self, target_sat, sat_upgrade_chost, save_test_data):
        """This is pre-upgrade scenario test to verify if we can create a
         custom repository and consume it via content host.

        :id: preupgrade-eb6831b1-c5b6-4941-a325-994a09467478

        :steps:
            1. Before Satellite upgrade.
            2. Create new Organization, Location.
            3. Create Product, custom repo, cv.
            4. Create activation key and add subscription.
            5. Create a content host, register and install package on it.

        :expectedresults:

            1. Custom repo is created.
            2. Package is installed on Content host.

        """
        org = target_sat.api.Organization().create()
        lce = target_sat.api.LifecycleEnvironment(organization=org).create()

        product = target_sat.api.Product(organization=org).create()
        repo = target_sat.api.Repository(product=product.id, url=settings.repos.yum_1.url).create()
        repo.sync()
        content_view = target_sat.publish_content_view(org, repo)
        content_view.version[0].promote(data={'environment_ids': lce.id})
        ak = target_sat.api.ActivationKey(
            content_view=content_view, organization=org.id, environment=lce
        ).create()
        if not target_sat.is_sca_mode_enabled(org.id):
            subscription = target_sat.api.Subscription(organization=org).search(
                query={'search': f'name={product.name}'}
            )[0]
            ak.add_subscriptions(data={'subscription_id': subscription.id})
        sat_upgrade_chost.install_katello_ca(target_sat)
        sat_upgrade_chost.register_contenthost(org.label, ak.name)
        sat_upgrade_chost.execute('subscription-manager repos --enable=*;yum clean all')
        result = sat_upgrade_chost.execute(f'yum install -y {FAKE_0_CUSTOM_PACKAGE_NAME}')
        assert result.status == 0

        save_test_data(
            {
                'rhel_client': sat_upgrade_chost.hostname,
                'content_view_name': content_view.name,
                'lce_id': lce.id,
                'repo_name': repo.name,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_custom_repo_check)
    def test_post_scenario_custom_repo_check(self, target_sat, pre_upgrade_data):
        """This is post-upgrade scenario test to verify if we can alter the
        created custom repository and satellite will be able to sync back
        the repo.

        :id: postupgrade-5c793577-e573-46a7-abbf-b6fd1f20b06e

        :steps:
            1. Remove old and add new package into custom repo.
            2. Sync repo , publish the new version of cv.
            3. Try to install new package on client.


        :expectedresults: Content host should be able to pull the new rpm.

        """
        client_hostname = pre_upgrade_data.get('rhel_client')
        content_view_name = pre_upgrade_data.get('content_view_name')
        lce_id = pre_upgrade_data.get('lce_id')
        repo_name = pre_upgrade_data.get('repo_name')

        repo = target_sat.api.Repository(name=repo_name).search()[0]
        repo.sync()

        content_view = target_sat.api.ContentView(name=content_view_name).search()[0]
        content_view.publish()

        content_view = target_sat.api.ContentView(name=content_view_name).search()[0]
        latest_cvv_id = sorted(cvv.id for cvv in content_view.version)[-1]
        target_sat.api.ContentViewVersion(id=latest_cvv_id).promote(
            data={'environment_ids': lce_id}
        )

        rhel_client = ContentHost.get_host_by_hostname(client_hostname)
        result = rhel_client.execute(f'yum install -y {FAKE_4_CUSTOM_PACKAGE_NAME}')
        assert result.status == 0


class TestScenarioCustomRepoOverrideCheck:
    """Scenario test to verify that repositories in a non-sca org set to "Enabled"
    should be overridden to "Enabled(Override)" when upgrading to 6.14.

    Test Steps:

        1. Before Satellite upgrade.
        2. Create new Organization, Location.
        3. Create Product, Custom Repository, Content view.
        4. Create Activation Key and add Subscription.
        5. Create a Content Host, register it, and check Repository Sets for enabled Repository.
        6. Upgrade Satellite.
        7. Search Host to verify Repository Set is set to Enabled(Override).

    BZ: 1265120
    """

    @pytest.mark.pre_upgrade
    def test_pre_scenario_custom_repo_sca_toggle(
        self,
        target_sat,
        function_org,
        function_product,
        function_lce,
        sat_upgrade_chost,
        save_test_data,
        default_location,
    ):
        """This is a pre-upgrade scenario test to verify that repositories in a non-sca org
        set to "Enabled" should be overridden to "Enabled(Override)" when upgrading to 6.14.

        :id: preupgrade-65e1e312-a743-4605-b226-f580f523377f

        :steps:
            1. Before Satellite upgrade.
            2. Create new Organization, Location.
            3. Create Product, Custom Repository, Content view.
            4. Create Activation Key and add Subscription.
            5. Create a Content Host, register it, and check Repository Sets for enabled Repository.

        :expectedresults:

            1. Custom Repository is created.
            2. Custom Repository is enabled on Host.

        """
        repo = target_sat.api.Repository(
            product=function_product.id, url=settings.repos.yum_1.url
        ).create()
        repo.sync()
        content_view = target_sat.publish_content_view(function_org, repo)
        content_view.version[0].promote(data={'environment_ids': function_lce.id})
        ak = target_sat.api.ActivationKey(
            content_view=content_view, organization=function_org.id, environment=function_lce
        ).create()
        if not target_sat.is_sca_mode_enabled(function_org.id):
            subscription = target_sat.api.Subscription(organization=function_org).search(
                query={'search': f'name={function_product.name}'}
            )[0]
            ak.add_subscriptions(data={'subscription_id': subscription.id})
        sat_upgrade_chost.register(function_org, default_location, ak.name, target_sat)
        product_details = sat_upgrade_chost.execute('subscription-manager repos --list')
        assert 'Enabled:   1' in product_details.stdout

        save_test_data(
            {
                'rhel_client': sat_upgrade_chost.hostname,
                'org_name': function_org.name,
                'product_name': function_product.name,
                'repo_name': repo.name,
                'product_details': product_details.stdout,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_custom_repo_sca_toggle)
    def test_post_scenario_custom_repo_sca_toggle(self, pre_upgrade_data):
        """This is a post-upgrade scenario test to verify that repositories in a non-sca
        Organization set to "Enabled" should be overridden to "Enabled(Override)"
        when upgrading to 6.14.

        :id: postupgrade-cc392ce3-f3bb-4cf3-afd5-c062e3a5d109

        :steps:
            1. After upgrade, search Host to verify Repository Set is set to
            Enabled(Override).


        :expectedresults: Repository on Host should be overridden.

        """
        client_hostname = pre_upgrade_data.get('rhel_client')
        org_name = pre_upgrade_data.get('org_name')
        product_name = pre_upgrade_data.get('product_name')
        repo_name = pre_upgrade_data.get('repo_name')
        rhel_client = ContentHost.get_host_by_hostname(client_hostname)
        result = rhel_client.execute('subscription-manager repo-override --list')
        assert 'enabled: 1' in result.stdout
        assert f'{org_name}_{product_name}_{repo_name}' in result.stdout


class TestScenarioLargeRepoSyncCheck:
    """Scenario test to verify that large repositories can be synced without
    failure after an upgrade.

    Test Steps:

        1. Before Satellite upgrade.
        2. Enable and sync large RH repository.
        3. Upgrade Satellite.
        4. Enable and sync a second large repository.

    BZ: 2043144

    :customerscenario: true
    """

    @pytest.mark.pre_upgrade
    def test_pre_scenario_sync_large_repo(
        self, target_sat, module_entitlement_manifest_org, save_test_data
    ):
        """This is a pre-upgrade scenario to verify that users can sync large repositories
        before an upgrade

        :id: afb957dc-c509-4009-ac85-4b71b64d3c74

        :steps:
            1. Enable a large redhat repository
            2. Sync repository and assert sync succeeds

        :expectedresults: Large Repositories should succeed when synced
        """
        rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=module_entitlement_manifest_org.id,
            product=REPOS['rhel8_bos']['product'],
            repo=REPOS['rhel8_bos']['name'],
            reposet=REPOS['rhel8_bos']['reposet'],
            releasever=REPOS['rhel8_bos']['releasever'],
        )
        repo = target_sat.api.Repository(id=rh_repo_id).read()
        res = repo.sync(timeout=2000)
        assert res['result'] == 'success'
        save_test_data({'org_id': module_entitlement_manifest_org.id})

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_sync_large_repo)
    def test_post_scenario_sync_large_repo(self, target_sat, pre_upgrade_data):
        """This is a post-upgrade scenario to verify that large repositories can be
        synced after an upgrade

        :id: 7bdbb2ac-7197-4e1a-8163-5852943eb49b

        :steps:
            1. Sync large repository
            2. Upgrade satellite
            3. Sync a second large repository in that same organization

        :expectedresults: Large repositories should succeed after an upgrade
        """
        org_id = pre_upgrade_data.get('org_id')
        rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=org_id,
            product=REPOS['rhel8_aps']['product'],
            repo=REPOS['rhel8_aps']['name'],
            reposet=REPOS['rhel8_aps']['reposet'],
            releasever=REPOS['rhel8_aps']['releasever'],
        )
        repo = target_sat.api.Repository(id=rh_repo_id).read()
        res = repo.sync(timeout=4000)
        assert res['result'] == 'success'
