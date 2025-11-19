"""Test for Repository related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Repositories

:Team: Artemis

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo.config import settings
from robottelo.constants import (
    CONTAINER_MANIFEST_LABELS,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_4_CUSTOM_PACKAGE_NAME,
    LABELLED_REPOS,
)
from robottelo.hosts import ContentHost
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def custom_repo_check_setup(sat_upgrade_chost, content_upgrade_shared_satellite, upgrade_action):
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
    target_sat = content_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'rhel_client': sat_upgrade_chost,
                'lce': None,
                'repo': None,
                'content_view': None,
            }
        )
        test_name = f'repo_upgrade_{gen_alpha()}'  # unique name for the test
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        lce = target_sat.api.LifecycleEnvironment(
            organization=org, name=f'{test_name}_lce', prior=2
        ).create()
        test_data.lce = lce
        product = target_sat.api.Product(organization=org, name=f'{test_name}_prod').create()
        repo = target_sat.api.Repository(
            product=product.id,
            name=f'{test_name}_repo',
            url=settings.repos.yum_1.url,
            content_type='yum',
        ).create()
        test_data.repo = repo
        repo.sync()
        content_view = target_sat.publish_content_view(org, repo, test_name)
        test_data.content_view = content_view
        content_view.version[0].promote(data={'environment_ids': lce.id})
        ak = target_sat.api.ActivationKey(
            content_view=content_view, organization=org.id, environment=lce, name=test_name
        ).create()
        sat_upgrade_chost.api_register(
            target_sat, organization=org, activation_keys=[ak.name], location=None
        )
        sat_upgrade_chost.execute('subscription-manager repos --enable=* && yum clean all')
        result = sat_upgrade_chost.execute(f'yum install -y {FAKE_0_CUSTOM_PACKAGE_NAME}')
        assert result.status == 0
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.content_upgrades
def test_scenario_custom_repo_check(custom_repo_check_setup):
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
    test_data = custom_repo_check_setup
    target_sat = test_data.target_sat
    repo = target_sat.api.Repository(name=test_data.repo.name).search()[0]
    repo.sync()

    content_view = target_sat.api.ContentView(name=test_data.content_view.name).search()[0]
    content_view.publish()

    content_view = target_sat.api.ContentView(name=test_data.content_view.name).search()[0]
    latest_cvv_id = sorted(cvv.id for cvv in content_view.version)[-1]
    target_sat.api.ContentViewVersion(id=latest_cvv_id).promote(
        data={'environment_ids': test_data.lce.id}
    )

    rhel_client = ContentHost.get_host_by_hostname(test_data.rhel_client.hostname)
    result = rhel_client.execute(f'yum install -y {FAKE_4_CUSTOM_PACKAGE_NAME}')
    assert result.status == 0


@pytest.fixture
def container_repo_sync_setup(content_upgrade_shared_satellite, upgrade_action):
    """This is a pre-upgrade fixture to sync container repositories
    with some labels, annotations and bootable and flatpak flags.

    :id: preupgrade-55b82217-7fd0-4b98-bd38-2a08a36f77db

    :steps:
        1. Create bootable container repository with some labels and flags.
        2. Sync the repository and assert sync succeeds.
        3. Create flatpak container repository with some labels and flags.
        4. Sync the repository and assert sync succeeds.

    :expectedresults: Container repositories are synced and ready for upgrade.
    """
    target_sat = content_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'repos': [],
            }
        )
        org = target_sat.api.Organization(name=gen_alpha()).create()
        product = target_sat.api.Product(name=gen_alpha(), organization=org).create()
        for item in LABELLED_REPOS:
            repo = target_sat.api.Repository(
                name=gen_alpha(),
                content_type='docker',
                docker_upstream_name=item['upstream_name'],
                product=product,
                url=settings.container.pulp.registry_hub,
            ).create()
            repo.sync()
            repo = repo.read()
            assert repo.content_counts['docker_manifest'] > 0
            test_data.repos.append(repo.id)
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.content_upgrades
def test_container_repo_sync(container_repo_sync_setup):
    """This is a post-upgrade test to verify the container labels
    were indexed properly in the post-upgrade task.

    :id: postupgrade-1e8f2f4a-6232-4671-9d6f-2ada1b70bc59

    :steps:
        1. Verify all manifests and manifest_lists in each repo contain the expected keys.
        2. Verify the manifests and manifest_lists count matches the repository content counts
           and the expectation.
        3. Verify the values meet the expectations specific for each repo.

    :expectedresults: Container labels were indexed properly.
    """
    test_data = container_repo_sync_setup
    target_sat = test_data.target_sat
    for repo_id in test_data.repos:
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
                (i for i in LABELLED_REPOS if i['upstream_name'] == repo.docker_upstream_name), None
            )
            assert expected_values, f'{repo.docker_upstream_name} not found in {LABELLED_REPOS}'
            expected_values = expected_values[entity_type]
            assert len(entity_data) == repo.content_counts[f'docker_{entity_type}'], (
                f'{entity_type}s count does not match the repository content counts'
            )
            assert len(entity_data) == expected_values['count'], (
                f'{entity_type}s count does not meet the expectation'
            )
            assert all([m['is_bootable'] == expected_values['bootable'] for m in entity_data]), (
                'Unexpected is_bootable flag'
            )
            assert all([m['is_flatpak'] == expected_values['flatpak'] for m in entity_data]), (
                'Unexpected is_flatpak flag'
            )
            assert all(
                [len(m['labels']) == expected_values['labels_count'] for m in entity_data]
            ), 'Unexpected labels count'
            assert all(
                [len(m['annotations']) == expected_values['annotations_count'] for m in entity_data]
            ), 'Unexpected annotations count'
