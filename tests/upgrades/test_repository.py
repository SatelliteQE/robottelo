"""Test for Repository related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Repositories

:team: Phoenix-content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker import Broker

from robottelo.config import settings
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE_NAME
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

        rhel_client = Broker(host_class=ContentHost).from_inventory(
            filter=f'hostname={client_hostname}'
        )[0]
        result = rhel_client.execute(f'yum install -y {FAKE_4_CUSTOM_PACKAGE_NAME}')
        assert result.status == 0
