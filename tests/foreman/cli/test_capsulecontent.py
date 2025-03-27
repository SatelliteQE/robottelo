"""Capsule-Content related tests being run through CLI.

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Phoenix-content

:CaseImportance: High

"""

import pytest

from robottelo.config import settings
from robottelo.constants import (
    PULP_EXPORT_DIR,
)
from robottelo.constants.repos import ANSIBLE_GALAXY, CUSTOM_FILE_REPO


@pytest.mark.parametrize(
    'repos_collection',
    [
        {
            'distro': 'rhel8',
            'YumRepository': {'url': settings.repos.module_stream_1.url},
            'FileRepository': {'url': CUSTOM_FILE_REPO},
            'DockerRepository': {
                'url': settings.container.registry_hub,
                'upstream_name': settings.container.upstream_name,
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
@pytest.mark.stream
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

    :id: b9cfff16-6a2b-4d9f-8af9-e2adfd8bd1e4

    :parametrized: yes

    :setup:
        1. A content view with repos of all content types (currently yum, file)
           published into CVV and promoted to an LCE.

    :steps:
        1. Assign the Capsule with the LCE where the setup CVV is promoted to.
        2. Check the capsule lists correct LCE, CV and repo names and appropriate
           warning message (no content counts) before sync.
        3. Sync the Capsule and get the content counts again.
        4. Get the content counts from Satellite side and compare them with Capsule.
        5. Remove the LCE from Capsule and ensure it's not listed.

    :expectedresults:
        1. Capsule returs proper warning instead content counts until it is synced.
        2. After sync the content counts from Capsule match those from Satellite.
        3. After LCE removal it's not listed anymore.

    :BZ: 2251019

    """
    expected_keys = {
        'yum': {'packages', 'package-groups', 'module-streams', 'errata'},
        'file': {'files'},
        'docker': {'container-tags', 'container-manifests', 'container-manifest-lists'},
        'ansible_collection': {'ansible-collections'},
    }

    repos_collection.setup_content(function_org.id, function_lce.id)
    cv_id = repos_collection.setup_content_data['content_view']['id']
    cv = target_sat.cli.ContentView.info({'id': cv_id})
    cvv = target_sat.cli.ContentView.version_info({'id': cv['versions'][0]['id']})

    # Assign the Capsule with function LCE
    res = target_sat.cli.Capsule.content_add_lifecycle_environment(
        {
            'id': module_capsule_configured.nailgun_capsule.id,
            'organization-id': function_org.id,
            'environment-id': function_lce.id,
        }
    )
    assert 'environment successfully added' in str(res)

    # Check the capsule lists correct LCE, CV and repo names and appropriate
    # warning message (no content counts) before sync.
    info = target_sat.cli.Capsule.content_info(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': function_org.id}
    )
    assert len(info['lifecycle-environments']) == 1, 'Too many or few LCEs listed'
    lce_info = info['lifecycle-environments']['1']
    assert lce_info['name'] == function_lce.name, 'Wrong LCE name listed'
    assert lce_info['organization']['name'] == function_org.name, 'Wrong ORG name listed'
    assert len(lce_info['content-views']) == 1, 'Too many or few CVs listed'
    cv_info = lce_info['content-views']['1']
    assert cv_info['name']['name'] == cv['name'], 'Wrong CV name listed'
    assert len(cv_info['repositories']) == len(cvv['repositories']), (
        'Too many or few repositories listed'
    )
    cv_info_reponames = set([repo['repository-name'] for repo in cv_info['repositories'].values()])
    cvv_reponames = set([repo['name'] for repo in cvv['repositories']])
    assert cv_info_reponames == cvv_reponames, 'Wrong repo names listed'
    counts = [repo['content-counts'] for repo in cv_info['repositories'].values()]
    assert all(
        'Content view must be synced to see content counts' in i['warning'] for i in counts
    ), 'Expected warning for all repo content counts'

    # Sync, wait for counts to be updated and get them from the Capsule.
    target_sat.cli.Capsule.content_synchronize(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': function_org.id}
    )
    target_sat.wait_for_tasks(
        search_query='label = Actions::Katello::CapsuleContent::UpdateContentCounts',
        search_rate=5,
        max_tries=5,
    )

    # Get the content counts from Satellite side and compare them with Capsule.
    info = target_sat.cli.Capsule.content_info(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': function_org.id}
    )

    caps_counts = [
        repo
        for repo in info['lifecycle-environments']['1']['content-views']['1'][
            'repositories'
        ].values()
    ]
    sat_repos = [
        target_sat.cli.Repository.info({'id': repo['repository-id']}) for repo in caps_counts
    ]

    for s_repo in sat_repos:
        c_repo = next(r for r in caps_counts if r['repository-id'] == s_repo['id'])
        common_keys = set(s_repo['content-counts'].keys()) & set(c_repo['content-counts'].keys())
        assert len(common_keys), f'''No common keys found for type "{s_repo['content-type']}".'''
        assert expected_keys[s_repo['content-type']].issubset(common_keys), (
            'Some fields are missing: expected '
            f"{expected_keys[s_repo['content-type']]} but found {common_keys}"
        )
        assert all(
            [
                s_repo['content-counts'].get(key) == c_repo['content-counts'].get(key)
                for key in common_keys
            ]
        ), 'Some of the content counts do not match'

    # Remove the LCE from Capsule and ensure it's not listed.
    res = target_sat.cli.Capsule.content_remove_lifecycle_environment(
        {
            'id': module_capsule_configured.nailgun_capsule.id,
            'organization-id': function_org.id,
            'environment-id': function_lce.id,
        }
    )
    assert 'environment successfully removed' in str(res)

    info = target_sat.cli.Capsule.content_info(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': function_org.id}
    )
    assert len(info['lifecycle-environments']) == 0, 'The LCE is still listed'


@pytest.mark.stream
@pytest.mark.pit_client
def test_positive_update_counts(target_sat, module_capsule_configured):
    """Verify the update counts functionality

    :id: 5658dbb1-3d3d-4926-804b-1ff221cf5075

    :setup:
        1. Satellite with registered Capsule.

    :steps:
        1. Run capsule content update-counts via hammer.

    :expectedresults:
        1. Update Content Counts task is created and succeeds.

    """
    task = target_sat.cli.Capsule.content_update_counts(
        {'id': module_capsule_configured.nailgun_capsule.id, 'async': True}
    )
    target_sat.wait_for_tasks(
        search_query='label = Actions::Katello::CapsuleContent::UpdateContentCounts'
        f' and id = {task["id"]}',
        search_rate=5,
        max_tries=5,
    )


@pytest.mark.tier4
@pytest.mark.skip_if_not_set('capsule')
def test_positive_exported_imported_content_sync(
    target_sat,
    function_lce,
    function_lce_library,
    function_published_cv,
    function_sca_manifest_org,
    module_capsule_configured,
):
    """Add repo content to a content-view, publish, export the Library content.
    Then, import the content (CVV) to satellite, promote to a Capsule's LCE, sync the Capsule.
    Assign Library environment to Capsule with identical CVs (Export and Import),
    Sync the Capsule once more, to Library now, and check for redundant tasks.

    :id: efb3bb45-fb91-4b40-825a-07c1e9772a55

    :steps:
        1. Assign a non-Library LCE to Capsule.
        2. Setup and sync a custom repo, for an SCA-enabled org.
        3. Export-complete Library content, containing repo's published CV (can take a while).
        4. Import the exported content from Step 3 (can take a while).
        5. Promote the imported CVV (Import-Library) to the Capsule's LCE.
        6. Sync the Capsule with the added Import-Library content.
        7. Remove non-Library LCE from Capsule.
        8. Then, add 'Library' environment to Capsule containing both CVs, sync.

    :expectedresults:
        1. Step 6: Imported content sources assigned to empty Capsule,
            synced successfully using Capsule's LCE.
        2. Step 6: Auxilary created 'Export-Library' CV, made after exporting,
            is not associated with the Capsule, as it is only in 'Library'.
        3. Step 8: Using 'Library', Capsule sync is successful, respositories/sync tasks do not conflict,
            all pending sync tasks complete in one attempt, none are invoked repeatedly.

    :BZ: 2043726, 2059385, 2186765

    :customerscenario: True

    """
    org = function_sca_manifest_org
    # assign the non-Library LCE to Capsule
    target_sat.cli.Capsule.content_add_lifecycle_environment(
        {
            'id': module_capsule_configured.nailgun_capsule.id,
            'organization-id': org.id,
            'lifecycle-environment-id': function_lce.id,
        }
    )
    # Create and sync custom repo, add to CV, publish only (Library)
    target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_3.url,
            'organization-id': org.id,
            'content-view-id': function_published_cv.id,
            'lifecycle-environment-id': function_lce_library.id,
        }
    )
    # Verify export directory is empty
    assert target_sat.validate_pulp_filepath(org, PULP_EXPORT_DIR) == ''
    # Export complete Library with content, verify populated export directory
    exported = target_sat.cli.ContentExport.completeLibrary({'organization-id': org.id})
    assert target_sat.validate_pulp_filepath(org, PULP_EXPORT_DIR)
    import_path = target_sat.move_pulp_archive(org, exported['message'])
    # import content from pulp exports
    target_sat.cli.ContentImport.library({'organization-id': org.id, 'path': import_path})
    import_cv_info = target_sat.cli.ContentView.info(
        {'name': 'Import-Library', 'organization-id': org.id}
    )
    # promote Import-Library to Capsule's LCE
    target_sat.cli.ContentView.version_promote(
        {
            'id': import_cv_info['versions'][0]['id'],
            'organization-id': org.id,
            'to-lifecycle-environment-id': function_lce.id,
        }
    )
    capsule = module_capsule_configured.nailgun_capsule.read()
    # just one LCE found associated to capsule
    assert len(capsule.lifecycle_environments) == 1, (
        f'Expected only one environment for Capsule; {function_lce.name}.'
        f' Found {len(capsule.lifecycle_environments)}:\n{capsule.lifecycle_environments}'
    )
    assert capsule.lifecycle_environments[0]['id'] == function_lce.id
    assert not capsule.lifecycle_environments[0]['library']
    # verify only the Import-Library CV is associated to Capsule,
    # we check the Capsule's LCE, that it only has the single expected CV.
    cv_list = function_lce.read_json()['content_views']
    assert len(cv_list) == 1, (
        f'Found unexpected CV associated to Capsule, expected only one; {import_cv_info["name"]}.'
        f' Capsule LCE:\n{function_lce.read_json()}'
    )
    assert cv_list[0]['name'] == 'Import-Library'
    assert str(cv_list[0]['id']) == str(import_cv_info['id'])
    # Synchronize the Capsule, with the Import content added
    sync_status = module_capsule_configured.nailgun_capsule.content_sync(timeout='90m')
    assert sync_status['result'] == 'success', f'Capsule sync failed. Task: {sync_status}'

    # Remove the LCE from Capsule
    target_sat.cli.Capsule.content_remove_lifecycle_environment(
        {
            'id': module_capsule_configured.nailgun_capsule.id,
            'organization-id': org.id,
            'lifecycle-environment-id': function_lce.id,
        }
    )

    # Add Library to Capsule, containing both CVs, 'immediate' download policy.
    target_sat.cli.Capsule.content_add_lifecycle_environment(
        {
            'id': module_capsule_configured.nailgun_capsule.id,
            'organization-id': org.id,
            'lifecycle-environment-id': function_lce_library.id,
        }
    )
    module_capsule_configured.update_download_policy('immediate')
    # Capsule sync successful, repo sync/associated tasks are not redundant (BZ: 2186765)
    sync_status = module_capsule_configured.nailgun_capsule.content_sync(timeout='90m')
    assert sync_status['result'] == 'success', f'Capsule sync failed. Task: {sync_status}'
    # any in-progress tasks, post sync, are not associated to Capsule or repo
    unexpected_tasks = [
        'Actions::Katello::Repository::Sync',
        'Actions::Katello::Repository::CapsuleSync',
        'Actions::Katello::Repository::MetadataGenerate',
        'Actions::Katello::CapsuleContent::Sync',
        'Actions::Katello::ContentView::CapsuleSync',
    ]
    pending_tasks = target_sat.api.ForemanTask().search(
        query={'search': f'organization_id={org.id} and result=pending'}
    )
    assert all(task.label not in unexpected_tasks for task in pending_tasks), (
        'A repeated, pending task was found for repository or capsule, after capsule sync completed:'
        f'{[task for task in pending_tasks if task.label in unexpected_tasks]}'
    )
    # no need to check content counts, covered by several other cases
