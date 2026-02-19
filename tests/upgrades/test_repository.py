"""Test for Repository related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Repositories

:Team: Artemis

:CaseImportance: High

"""

from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.constants import (
    CONTAINER_MANIFEST_LABELS,
    DEFAULT_ARCHITECTURE,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_4_CUSTOM_PACKAGE_NAME,
    LABELLED_REPOS,
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
        4. Create activation key.
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
        # Override/enable all AK repos (disabled by default since 6.15)
        c_labels = [
            i['label'] for i in ak.product_content(data={'content_access_mode_all': '1'})['results']
        ]
        ak.content_override(
            data={
                'content_overrides': [{'content_label': label, 'value': '1'} for label in c_labels]
            }
        )
        sat_upgrade_chost.register(org, None, ak.name, target_sat)
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
    def test_post_scenario_custom_repo_check(self, request, target_sat, pre_upgrade_data):
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
        rhel_client = ContentHost.get_host_by_hostname(client_hostname)

        @request.addfinalizer
        def _cleanup():
            Broker(hosts=[rhel_client]).checkin()

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

        result = rhel_client.execute(f'yum install -y {FAKE_4_CUSTOM_PACKAGE_NAME}')
        assert result.status == 0


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
        self, target_sat, module_sca_manifest_org, save_test_data
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
            org_id=module_sca_manifest_org.id,
            product=REPOS['rhel8_bos']['product'],
            repo=REPOS['rhel8_bos']['name'],
            reposet=REPOS['rhel8_bos']['reposet'],
            releasever=REPOS['rhel8_bos']['releasever'],
        )
        repo = target_sat.api.Repository(id=rh_repo_id).read()
        res = repo.sync(timeout=2000)
        assert res['result'] == 'success'
        save_test_data({'org_id': module_sca_manifest_org.id})

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


class TestScenarioContainerRepoSync:
    """Scenario to verify that container repositories with labels, annotations and other flags
     synced before upgrade are indexed properly after upgrade including labels (as of 6.16).

    Test Steps:

        1. Before Satellite upgrade.
        2. Synchronize container repositories that contains some labels and other flags.
        3. Upgrade Satellite.
        4. Check the labels and other flags were indexed properly in Katello DB via API.
    """

    @pytest.mark.pre_upgrade
    def test_pre_container_repo_sync(
        self,
        target_sat,
        module_org,
        module_product,
        save_test_data,
    ):
        """This is a pre-upgrade test to sync container repositories
        with some labels, annotations and bootable and flatpak flags.

        :id: 55b82217-7fd0-4b98-bd38-2a08a36f77db

        :steps:
            1. Create bootable container repository with some labels and flags.
            2. Sync the repository and assert sync succeeds.
            3. Create flatpak container repository with some labels and flags.
            4. Sync the repository and assert sync succeeds.

        :expectedresults: Container repositories are synced and ready for upgrade.
        """
        repos = dict()
        for item in LABELLED_REPOS:
            repo = target_sat.api.Repository(
                content_type='docker',
                docker_upstream_name=item['upstream_name'],
                product=module_product,
                url=settings.container.pulp.registry_hub,
            ).create()
            repo.sync()
            repo = repo.read()
            assert repo.content_counts['docker_manifest'] > 0
            repos[item['upstream_name']] = repo.id
        save_test_data(repos)

    @pytest.mark.post_upgrade(depend_on=test_pre_container_repo_sync)
    def test_post_container_repo_sync(self, target_sat, pre_upgrade_data):
        """This is a post-upgrade test to verify the container labels
        were indexed properly in the post-upgrade task.

        :id: 1e8f2f4a-6232-4671-9d6f-2ada1b70bc59

        :steps:
            1. Verify all manifests in each repo contain the expected keys.
            2. Verify the manifests count matches the repository content counts and the expectation.
            3. Verify the values meet the expectations specific for each repo.

        :expectedresults: Container labels were indexed properly.
        """
        for repo_id in pre_upgrade_data.values():
            repo = target_sat.api.Repository(id=repo_id).read()
            for entity_type in ['manifest', 'manifest_list']:
                entity_data = (
                    target_sat.api.Repository(id=repo.id).docker_manifests()['results']
                    if entity_type == 'manifest'
                    else target_sat.api.Repository(id=repo.id).docker_manifest_lists()['results']
                )

                assert all([CONTAINER_MANIFEST_LABELS.issubset(m.keys()) for m in entity_data]), (
                    f'Some expected key is missing in the repository {entity_type}s'
                )
                expected_values = next(
                    (i for i in LABELLED_REPOS if i['upstream_name'] == repo.docker_upstream_name),
                    None,
                )
                assert expected_values, f'{repo.docker_upstream_name} not found in {LABELLED_REPOS}'
                expected_values = expected_values[entity_type]
                assert len(entity_data) == repo.content_counts[f'docker_{entity_type}'], (
                    f'{entity_type}s count does not match the repository content counts'
                )
                assert len(entity_data) == expected_values['count'], (
                    f'{entity_type}s count does not meet the expectation'
                )
                assert all(
                    [m['is_bootable'] == expected_values['bootable'] for m in entity_data]
                ), 'Unexpected is_bootable flag'
                assert all([m['is_flatpak'] == expected_values['flatpak'] for m in entity_data]), (
                    'Unexpected is_flatpak flag'
                )
                assert all(
                    [len(m['labels']) == expected_values['labels_count'] for m in entity_data]
                ), 'Unexpected labels count'
                assert all(
                    [
                        len(m['annotations']) == expected_values['annotations_count']
                        for m in entity_data
                    ]
                ), 'Unexpected annotations count'
