"""Capsule-Content related tests being run through UI.

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Artemis

:CaseImportance: High

"""

from datetime import UTC, datetime, timedelta

import pytest

from robottelo.config import settings
from robottelo.constants import DEFAULT_CV, REPOS
from robottelo.constants.repos import ANSIBLE_GALAXY, CUSTOM_FILE_REPO


@pytest.fixture(scope='module', autouse=True)
def capsule_default_org(module_target_sat, module_capsule_configured, default_org):
    """Add new Capsule to the Default Organization"""
    module_target_sat.cli.Capsule.update(
        {
            'name': module_capsule_configured.hostname,
            'organization-ids': default_org.id,
        }
    )


@pytest.mark.parametrize(
    'repos_collection',
    [
        {
            'distro': 'rhel8',
            'YumRepository': {'url': settings.repos.module_stream_1.url},
            'FileRepository': {'url': CUSTOM_FILE_REPO},
            'DockerRepository': {
                'url': 'https://quay.io',
                'upstream_name': 'libpod/testimage',
            },
            'AnsibleRepository': {
                'url': ANSIBLE_GALAXY,
                'requirements': [
                    {'name': 'theforeman.foreman', 'version': '2.1.0'},
                    {'name': 'theforeman.operations', 'version': '0.1.0'},
                ],
            },
        }
    ],
    indirect=True,
)
@pytest.mark.pit_client
def test_positive_content_counts_for_mixed_cv(
    target_sat,
    module_capsule_configured,
    repos_collection,
    function_org,
    function_lce,
    function_lce_library,
):
    """Verify the content counts for a mixed-content CV

    :id: b150f813-ae98-452b-9ad2-7f4ea88277c9

    :parametrized: yes

    :setup:
        1. A content view with repos of all content types
           published into CVV and promoted to an LCE.

    :steps:
        1. Assign the Capsule with the LCE where the setup CVV is promoted to.
        2. Check the capsule lists correct LCE and CV names but no content counts before sync.
        3. Sync the Capsule and get the content counts again.
        4. Get the content counts from Satellite side and compare them with Capsule.
        5. Refresh the counts and check the Counts update task was triggered.
        6. Remove the LCEs from Capsule and ensure they are not listed anymore.

    :expectedresults:
        1. Capsule returns 'N/A' for content counts until it is synced.
        2. After sync the content counts from Capsule match those from Satellite.
        3. Update counts task can be triggered from the UI.
        4. After LCE removal content counts are not listed anymore.
    """
    repos_collection.setup_content(function_org.id, function_lce.id)
    cv_id = repos_collection.setup_content_data['content_view']['id']
    cv = target_sat.api.ContentView(id=cv_id).read()
    cvv = cv.version[-1].read()
    lces = [function_lce.name, function_lce_library.name]

    with target_sat.ui_session() as session:
        session.capsule.edit(
            module_capsule_configured.hostname, add_organizations=[function_org.name]
        )
        session.organization.select(org_name=function_org.name)

        # Assign the Capsule with the LCE where the setup CVV is promoted to.
        session.capsule.edit(
            module_capsule_configured.hostname,
            add_lces=lces,
        )

        # Check the capsule lists correct LCE and CV names but no content counts before sync.
        details = session.capsule.read_details(module_capsule_configured.hostname)
        assert set(lces) == set(details['content']), 'Wrong LCEs listed'
        assert function_lce.name in details['content'], 'Assigned LCE not listed'

        for lce in lces:
            assert cv.name in details['content'][lce], 'Assigned CV not listed'
            assert 'N/A' in details['content'][lce]['top_row_content']['Last sync'], (
                'LCE should be marked as unsynced'
            )

            assert (
                details['content'][lce][cv.name]['mid_row_content']['Version']
                == f'Version {cvv.version}'
            ), 'CV version does not match'
            assert not details['content'][lce][cv.name]['mid_row_content']['Synced'], (
                'CV should not be marked as synced'
            )

            repos_details = details['content'][lce][cv.name]['expanded_repo_details'][1:]
            assert all([repo[1] == repo[2] == 'N/A' for repo in repos_details]), (
                'Expected all content counts as N/A'
            )

            if lce == 'Library':
                # Library should contain the Default Org View too
                assert DEFAULT_CV in details['content'][lce], 'Default Org View not listed'

                assert (
                    details['content'][lce][DEFAULT_CV]['mid_row_content']['Version']
                    == 'Version 1.0'
                ), 'CV version does not match'
                assert not details['content'][lce][DEFAULT_CV]['mid_row_content']['Synced'], (
                    'CV should not be marked as synced'
                )

                repos_details = details['content'][lce][DEFAULT_CV]['expanded_repo_details'][1:]
                assert all([repo[1] == repo[2] == 'N/A' for repo in repos_details]), (
                    'Expected all content counts as N/A'
                )

        # Sync the Capsule and get the content counts again.
        session.capsule.optimized_sync(module_capsule_configured.hostname)
        target_sat.wait_for_tasks(
            search_query='label = Actions::Katello::CapsuleContent::Sync',
            search_rate=10,
            max_tries=10,
        )
        target_sat.wait_for_tasks(
            search_query='label = Actions::Katello::CapsuleContent::UpdateContentCounts',
            search_rate=5,
            max_tries=5,
        )
        details = session.capsule.read_details(module_capsule_configured.hostname)

        # Get the content counts from Satellite side and compare them with Capsule.
        sat_repos = [target_sat.api.Repository(id=repo.id).read() for repo in cvv.repository]
        for lce in lces:
            assert 'ago' in details['content'][lce]['top_row_content']['Last sync'], (
                'LCE should be marked as synced'
            )
            assert details['content'][lce][cv.name]['mid_row_content']['Synced'], (
                'CV should be marked as synced'
            )
            repos_details = details['content'][lce][cv.name]['expanded_repo_details'][1:]

            for s_repo in sat_repos:
                c_repo = next(r for r in repos_details if r[0] == s_repo.name)
                assert c_repo, 'Repository not listed'
                if s_repo.content_type == 'yum':
                    assert f'{s_repo.content_counts["rpm"]} Packages' in c_repo, (
                        'RPMs count does not match'
                    )
                    assert f'{s_repo.content_counts["erratum"]} Errata' in c_repo, (
                        'Errata count does not match'
                    )
                    assert f'{s_repo.content_counts["package_group"]} Package groups' in c_repo, (
                        'Package groups count does not match'
                    )
                    assert f'{s_repo.content_counts["module_stream"]} Module streams' in c_repo, (
                        'Module streams count does not match'
                    )
                elif s_repo.content_type == 'file':
                    assert f'{s_repo.content_counts["file"]} Files' in c_repo, (
                        'Files count does not match'
                    )
                elif s_repo.content_type == 'docker':
                    assert f'{s_repo.content_counts["docker_tag"]} Container tags' in c_repo, (
                        'Container tags count does not match'
                    )
                    assert (
                        f'{s_repo.content_counts["docker_manifest"]} Container manifests' in c_repo
                    ), 'Container manifests count does not match'
                    assert (
                        f'{s_repo.content_counts["docker_manifest_list"]} Container manifest lists'
                        in c_repo
                    ), 'Container manifest lists count does not match'
                elif s_repo.content_type == 'ansible_collection':
                    assert (
                        f'{s_repo.content_counts["ansible_collection"]} Ansible collections'
                        in c_repo
                    ), 'Ansible collections count does not match'

        # Refresh the counts and check the Counts update task was triggered.
        for lce in lces:
            t1 = target_sat.api.ForemanTask().search(
                query={
                    'search': 'label = Actions::Katello::CapsuleContent::UpdateContentCounts',
                    'per_page': '1000',
                }
            )
            session.capsule.refresh_lce_counts(module_capsule_configured.hostname, lce_name=lce)
            target_sat.wait_for_tasks(
                search_query='label = Actions::Katello::CapsuleContent::UpdateContentCounts',
                search_rate=5,
                max_tries=5,
            )
            t2 = target_sat.api.ForemanTask().search(
                query={
                    'search': 'label = Actions::Katello::CapsuleContent::UpdateContentCounts',
                    'per_page': '1000',
                }
            )
            assert len(t2) == len(t1) + 1, 'Update CC task was not triggered'

        # Remove the LCEs from Capsule and ensure they are not listed anymore.
        session.capsule.edit(module_capsule_configured.hostname, remove_all_lces=True)
        details = session.capsule.read_details(module_capsule_configured.hostname)
        assert 'content' not in details, 'Content still listed for removed LCEs'


@pytest.mark.parametrize('setting_update', ['automatic_content_count_updates=False'], indirect=True)
def test_positive_content_counts_granular_update(
    module_target_sat, module_capsule_configured, setting_update, function_org, function_product
):
    """Verify that the capsule content counts can be updated separately for LCEs and CVs.

    :id: 64f241f5-1766-4d11-95c7-f15633c10a80

    :parametrized: yes

    :Verifies: SAT-28338

    :BlockedBy: SAT-29679

    :setup:
        1. Satellite with registered external Capsule.
        2. Disabled automatic content counts update.

    :steps:
        1. Create two LCEs, assign them to the Capsule.
        2. Create and sync a repo, publish it in two CVs, promote both CVs to both LCEs.
        3. Ensure no counts were calculated yet for both CVs, both LCEs.
        4. Refresh counts for the first CV in the first LCE, check entity IDs in the Update task.
        5. Ensure the counts were updated for the first CV and
           the second CV stayed untouched, as well as the second LCE.
        6. Refresh counts for the second LCE, check entity IDs in the Update task.
        7. Ensure the counts were updated for the second LCE and
           the second CV in the first LCE stayed untouched.

    :expectedresults:
        1. Content counts are updated only for the specific LCEs and CVs.

    """
    wait_query = (
        'label = Actions::Katello::ContentView::CapsuleSync OR '
        'Actions::Katello::CapsuleContent::UpdateContentCounts'
    )

    # 1. Create two LCEs, assign them to the Capsule.
    lce1 = module_target_sat.api.LifecycleEnvironment(organization=function_org).create()
    lce2 = module_target_sat.api.LifecycleEnvironment(
        organization=function_org, prior=lce1
    ).create()
    module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
        data={'environment_id': [lce1.id, lce2.id]}
    )

    # 2. Create and sync a repo, publish it in two CVs, promote both CVs to both LCEs.
    repo = module_target_sat.api.Repository(
        product=function_product,
    ).create()
    repo.sync()
    repo = repo.read()
    cvs = []
    for _ in range(2):
        cv = module_target_sat.api.ContentView(
            organization=function_org, repository=[repo]
        ).create()
        cv.publish()
        cv = cv.read()
        cv.version[0].promote(data={'environment_ids': [lce1.id, lce2.id]})
        cvs.append(cv.read())
    cv1, cv2 = cvs
    module_target_sat.wait_for_tasks(search_query=wait_query, search_rate=5, max_tries=5)

    empty_counts = [repo.name, 'N/A', 'N/A']
    valid_counts = [
        repo.name,
        f'{repo.content_counts["rpm"]} Packages',
        f'{repo.content_counts["erratum"]} Errata',
        f'{repo.content_counts["package_group"]} Package groups',
    ]

    with module_target_sat.ui_session() as session:
        session.capsule.edit(
            module_capsule_configured.hostname, add_organizations=[function_org.name]
        )
        session.organization.select(org_name=function_org.name)

        # 3. Ensure no counts were calculated yet for both CVs, both LCEs.
        details = session.capsule.read_details(module_capsule_configured.hostname)
        assert all(
            details['content'][lce.name][cv.name]['expanded_repo_details'][1] == empty_counts
            for lce in [lce1, lce2]
            for cv in cvs
        ), 'Expected "N/A" for content counts displayed'

        # 4. Refresh counts for the first CV in the first LCE, check entity IDs in the Update task.
        session.capsule.refresh_lce_counts(
            module_capsule_configured.hostname, lce_name=lce1.name, cv_name=cv1.name
        )
        timestamp = (datetime.now(UTC) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M')
        task = module_target_sat.api.ForemanTask().search(
            query={
                'search': f'label=Actions::Katello::CapsuleContent::UpdateContentCounts and started_at>="{timestamp}"'
            }
        )[0]
        assert task.input['smart_proxy_id'] == module_capsule_configured.nailgun_capsule.id
        assert task.input['environment_id'] == lce1.id
        assert task.input['content_view_id'] == cv1.id

        # 5. Ensure the counts were updated for the first CV and
        #    the second CV stayed untouched, as well as the second LCE.
        details = session.capsule.read_details(module_capsule_configured.hostname)
        assert details['content'][lce1.name][cv1.name]['expanded_repo_details'][1] == valid_counts
        assert details['content'][lce1.name][cv2.name]['expanded_repo_details'][1] == empty_counts
        assert all(
            details['content'][lce2.name][cv.name]['expanded_repo_details'][1] == empty_counts
            for cv in cvs
        )

        # 6. Refresh counts for the second LCE, check entity IDs in the Update task.
        session.capsule.refresh_lce_counts(module_capsule_configured.hostname, lce_name=lce2.name)
        timestamp = (datetime.now(UTC) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M')
        task = module_target_sat.api.ForemanTask().search(
            query={
                'search': f'label=Actions::Katello::CapsuleContent::UpdateContentCounts and started_at>="{timestamp}"'
            }
        )[0]
        assert task.input['smart_proxy_id'] == module_capsule_configured.nailgun_capsule.id
        assert task.input['environment_id'] == lce2.id
        assert not task.input['content_view_id']

        # 7. Ensure the counts were updated for the second LCE and
        #    the second CV in the first LCE stayed untouched.
        details = session.capsule.read_details(module_capsule_configured.hostname)
        assert all(
            details['content'][lce2.name][cv.name]['expanded_repo_details'][1] == valid_counts
            for cv in cvs
        )
        assert details['content'][lce1.name][cv2.name]['expanded_repo_details'][1] == empty_counts


def test_partially_synced_library(
    module_target_sat, module_capsule_configured, function_sca_manifest_org, function_lce_library
):
    """Verify that partially synced Library shows the correct information on the Content tab

    :id: 7f053fe8-00b8-4811-b880-5c60b0bf73c3

    :parametrized: yes

    :verifies: SAT-21841

    :setup:
        1. Satellite with registered external Capsule.
        2. Function scoped Organization with manifest.

    :steps:
        1. Assign the Org's Library to the Capsule.
        2. Enable two RH repos, sync only one of them.
        3. Wait until the Capsule is synced and content counts calculated.
        4. Ensure the correct content counts are shown for both repositories.

    :expectedresults:
        1. Correct content counts are shown for the synced repository.
        2. No content counts are shown for the unsynced repository.

    """
    # 1. Assign the Org's Library to the Capsule.
    module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
        data={'environment_id': [function_lce_library.id]}
    )

    # 2. Enable two RH repos, sync only one of them.
    rh_repos = []
    for distro in ['rhel8_bos', 'rhel9_bos']:
        repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=function_sca_manifest_org.id,
            product=REPOS['kickstart'][distro]['product'],
            reposet=REPOS['kickstart'][distro]['reposet'],
            repo=REPOS['kickstart'][distro]['name'],
            releasever=REPOS['kickstart'][distro]['version'],
        )
        repo = module_target_sat.api.Repository(id=repo_id).read()
        rh_repos.append(repo)
    rh_repos[0].sync()

    # 3. Wait until the Capsule is synced and content counts calculated.
    wait_query = (
        'label = Actions::Katello::CapsuleContent::Sync OR '
        'Actions::Katello::CapsuleContent::UpdateContentCounts'
    )
    module_target_sat.wait_for_tasks(
        search_query=wait_query, search_rate=5, max_tries=5, poll_rate=10, poll_timeout=300
    )

    # 4. Ensure the correct content counts are shown for both repositories.
    with module_target_sat.ui_session() as session:
        session.capsule.edit(
            module_capsule_configured.hostname, add_organizations=[function_sca_manifest_org.name]
        )
        session.organization.select(org_name=function_sca_manifest_org.name)

        details = session.capsule.read_details(module_capsule_configured.hostname)

        # Get the content counts from Satellite side and compare them with Capsule.
        sat_repos = [module_target_sat.api.Repository(id=repo.id).read() for repo in rh_repos]
        caps_repos = details['content']['Library'][DEFAULT_CV]['expanded_repo_details'][1:]

        for s_repo in sat_repos:
            c_repo = next(r for r in caps_repos if r[0] == s_repo.name)
            assert c_repo, 'Repository not listed in the Capsule content tab'
            if s_repo.last_sync:
                assert f'{s_repo.content_counts["rpm"]} Packages' in c_repo
                assert f'{s_repo.content_counts["package_group"]} Package groups' in c_repo
            else:  # we expect 'N/A's for unsynced repo
                assert all(cnt == 'N/A' for cnt in c_repo[1:])


@pytest.mark.parametrize('setting_update', ['hide_reclaim_space_warning=False'], indirect=True)
def test_hide_reclaim_space_warning(module_target_sat, setting_update):
    """Verify the Reclaim space warning hiding via Settings works as expected.

    :id: aae93b89-0e8d-41e6-9e5f-40916a44d195

    :parametrized: yes

    :Verifies: SAT-18549

    :customerscenario: true

    :setup:
        1. Hiding is turned off.

    :steps:
        1. Navigate to the internal capsule details page, verify the warning is displayed.
        2. Turn the hiding on.
        3. Navigate to the internal capsule details page, verify the warning is gone.

    :expectedresults:
        1. The Reclaim space warning message can be hidden via Settings as needed.
    """
    with module_target_sat.ui_session() as session:
        # Navigate to the internal capsule details page, verify the warning is displayed.
        details = session.capsule.read_details(module_target_sat.hostname)
        assert 'reclaim_space_warning' in details['overview']
        assert (
            'Warning: reclaiming space will delete all cached content'
            in details['overview']['reclaim_space_warning']
        )

        # Turn the hiding on.
        setting_update.value = True
        setting_update.update({'value'})

        # Navigate to the internal capsule details page, verify the warning is gone.
        details = session.capsule.read_details(module_target_sat.hostname)
        assert 'reclaim_space_warning' not in details['overview']
