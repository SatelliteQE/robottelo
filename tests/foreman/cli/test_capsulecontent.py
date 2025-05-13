"""Capsule-Content related tests being run through CLI.

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Phoenix-content

:CaseImportance: High

"""

from datetime import UTC, datetime
import random

from box import Box
import pytest

from robottelo.config import settings
from robottelo.constants import (
    FAKE_0_CUSTOM_PACKAGE_NAME,
    PULP_EXPORT_DIR,
)
from robottelo.constants.repos import ANSIBLE_GALAXY, CUSTOM_FILE_REPO
from robottelo.content_info import get_repo_files_urls_by_url
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def module_synced_content(
    request,
    module_target_sat,
    module_capsule_configured,
    module_org,
    module_product,
    module_lce,
    module_lce_library,
):
    """
    Create and sync one or more repositories, publish them in a CV,
    promote to an LCE and sync all of that to an external Capsule.

    :param request: Repo(s) to use - dict or list of dicts with options to create the repo(s).
    :return: Box with created instances and Capsule sync time.
    """
    repos_opts = request.param
    if not isinstance(repos_opts, list):
        repos_opts = [repos_opts]

    repos = []
    for options in repos_opts:
        repo = module_target_sat.api.Repository(product=module_product, **options).create()
        repo.sync()
        repos.append(repo)

    cv = module_target_sat.api.ContentView(organization=module_org, repository=repos).create()
    cv.publish()
    cvv = cv.read().version[0].read()
    cvv.promote(data={'environment_ids': module_lce.id})

    # Assign the Capsule with the LCE (if not assigned yet) and sync it.
    if module_lce.id not in [
        lce['id'] for lce in module_capsule_configured.nailgun_capsule.lifecycle_environments
    ]:
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': [module_lce.id, module_lce_library.id]}
        )
    sync_time = datetime.now(UTC).replace(microsecond=0)
    module_target_sat.cli.Capsule.content_synchronize(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': module_org.id}
    )
    module_capsule_configured.wait_for_sync(start_time=sync_time)

    return Box(prod=module_product, repos=repos, cv=cv, lce=module_lce, sync_time=sync_time)


@pytest.fixture(scope="module")
def module_capsule_setting(module_target_sat, module_capsule_configured):
    """Set appropriate capsule setting for artifact testing,
    immediate download policy and on request sync."""
    setting_entity = module_target_sat.api.Setting().search(
        query={'search': 'name=foreman_proxy_content_auto_sync'}
    )[0]
    original_autosync = setting_entity.value
    original_policy = module_capsule_configured.nailgun_capsule.download_policy
    setting_entity.value = False
    setting_entity.update({'value'})
    module_capsule_configured.update_download_policy('immediate')
    yield
    setting_entity.value = original_autosync
    setting_entity.update({'value'})
    module_capsule_configured.update_download_policy(original_policy)


@pytest.fixture(scope='module')
def module_capsule_artifact_cleanup(
    request,
    module_target_sat,
    module_capsule_configured,
):
    """Unassign all LCEs from the module_capsule_configured and trigger orphan cleanup task.
    This should remove all pulp artifacts from the Capsule.
    """
    # Remove all LCEs from the capsule
    for lce in module_capsule_configured.nailgun_capsule.lifecycle_environments:
        module_capsule_configured.nailgun_capsule.content_delete_lifecycle_environment(
            data={'environment_id': lce['id']}
        )
    # Run orphan cleanup for the capsule.
    timestamp = datetime.now(UTC).replace(microsecond=0)
    module_target_sat.execute(
        'foreman-rake katello:delete_orphaned_content RAILS_ENV=production '
        f'SMART_PROXY_ID={module_capsule_configured.nailgun_capsule.id}'
    )
    module_target_sat.wait_for_tasks(
        search_query=(
            'label = Actions::Katello::OrphanCleanup::RemoveOrphans'
            f' and started_at >= "{timestamp}"'
        ),
        search_rate=5,
        max_tries=10,
    )


def _dictionarize_counts(data):
    """From CLI content counts usually come as a dict with several nested dicts using numbers as
    keys which is not practical for assertions. This helper refactors the dict with entity names
    for keys and grabs just the content counts.
    """
    refactored_data = {}

    for lce_value in data['lifecycle-environments'].values():
        lce_name = lce_value['name']
        cvs_dict = {}

        for cv_value in lce_value['content-views'].values():
            cv_name = cv_value['name']['name']
            repo_dict = {}

            for repo_value in cv_value['repositories'].values():
                repo_name = repo_value['repository-name']
                repo_dict[repo_name] = repo_value['content-counts']

            cvs_dict[cv_name] = repo_dict

        refactored_data[lce_name] = cvs_dict

    return refactored_data


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


@pytest.mark.parametrize('setting_update', ['automatic_content_count_updates=True'], indirect=True)
def test_positive_content_counts_granularity(
    request,
    module_target_sat,
    module_capsule_configured,
    setting_update,
    function_org,
    function_product,
):
    """Verify the Capsule content counts are updated separately for each content view when it is
    promoted to the Capsule's LCEs.

    :id: 14f9dbba-6d12-4faa-b33f-7ba1f328f8b6

    :parametrized: yes

    :verifies: SAT-28337

    :setup:
        1. Satellite with registered external Capsule.

    :steps:
        1. Create two LCEs, assign them to the Capsule.
        2. Create and sync a repo, publish it in two CVs, promote both CVs to both LCEs.
        3. Ensure full counts were calculated for both CVs, both LCEs.
        4. Disable automatic content counts update.
        5. Create a filter for both CVs to change the counts of next version.
        6. Publish new version of both CVs and promote to both LCEs.
           After capsule sync completes we should have changes in all publictions.
        7. Ensure the counts were invalidated in both CVs, both LCEs.
        8. Enable automatic content counts update.
        9. Publish new version of the first CV, promote it to the first LCE.
        10. Ensure counts of the first CV were updated in the first LCE only, nothing else.
        11. Promote the first CV to the second LCE.
        12. Ensure counts for the first CV were updated in the second LCE, no changes for second CV.

    :expectedresults:
        1. Content counts are updated only for particular CVs promoted to particular LCEs.
    """
    wait_query = (
        'label = Actions::Katello::ContentView::CapsuleSync OR '
        'Actions::Katello::CapsuleContent::UpdateContentCounts '
        'AND started_at >= "{}"'
    )

    # Create two LCEs, assign them to the Capsule.
    lce1 = module_target_sat.api.LifecycleEnvironment(organization=function_org).create()
    lce2 = module_target_sat.api.LifecycleEnvironment(
        organization=function_org, prior=lce1
    ).create()
    module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
        data={'environment_id': [lce1.id, lce2.id]}
    )

    # Create and sync a repo, publish it in two CVs, promote both CVs to both LCEs.
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
    module_target_sat.wait_for_tasks(
        search_query=wait_query.format(datetime.now(UTC).replace(microsecond=0)),
        search_rate=5,
        max_tries=5,
    )

    # Ensure full counts were calculated for both CVs, both LCEs.
    info = module_target_sat.cli.Capsule.content_info(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': function_org.id}
    )
    info = _dictionarize_counts(info)

    for lce in [lce1, lce2]:
        for cv in cvs:
            assert int(info[lce.name][cv.name][repo.name]['packages']) == repo.content_counts['rpm']
            assert (
                int(info[lce.name][cv.name][repo.name]['package-groups'])
                == repo.content_counts['package_group']
            )
            assert (
                int(info[lce.name][cv.name][repo.name]['errata']) == repo.content_counts['erratum']
            )

    # Disable automatic content counts update.
    setting_update.value = False
    setting_update = setting_update.update({'value'})

    # Create a filter for both CVs to change the counts of next version.
    for cv in cvs:
        cvf = module_target_sat.cli_factory.make_content_view_filter(
            {
                'content-view-id': cv.id,
                'inclusion': 'true',
                'type': 'rpm',
            },
        )
        module_target_sat.cli_factory.content_view_filter_rule(
            {
                'content-view-filter-id': cvf['filter-id'],
                'name': FAKE_0_CUSTOM_PACKAGE_NAME,
            }
        )

    # Publish new version of both CVs and promote to both LCEs.
    # After capsule sync completes we should have changes in all publictions.
    for cv in cvs:
        cv.publish()
        cv = cv.read()
        cv.version[0].promote(data={'environment_ids': [lce1.id, lce2.id]})
        cv = cv.read()
    module_target_sat.wait_for_tasks(
        search_query=wait_query.format(datetime.now(UTC).replace(microsecond=0)),
        search_rate=5,
        max_tries=5,
    )

    # Ensure the counts were invalidated in both CVs, both LCEs.
    info = module_target_sat.cli.Capsule.content_info(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': function_org.id}
    )
    info = _dictionarize_counts(info)
    assert all(info[lce.name][cv.name][repo.name] == {} for cv in cvs for lce in [lce1, lce2])

    # Enable automatic content counts update.
    setting_update.value = True
    setting_update = setting_update.update({'value'})

    # Publish new version of the first CV, promote it to the first LCE.
    cv1.publish()
    cv1 = cv1.read()
    cv1.version[0].promote(data={'environment_ids': lce1.id})
    cv1 = cv1.read()
    module_target_sat.wait_for_tasks(
        search_query=wait_query.format(datetime.now(UTC).replace(microsecond=0)),
        search_rate=5,
        max_tries=5,
    )

    # Ensure counts of the first CV were updated in the first LCE only, nothing else.
    info = module_target_sat.cli.Capsule.content_info(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': function_org.id}
    )
    info = _dictionarize_counts(info)

    assert int(info[lce1.name][cv1.name][repo.name]['packages']) == 1
    assert int(info[lce1.name][cv1.name][repo.name]['package-groups']) == 1
    assert int(info[lce1.name][cv1.name][repo.name]['errata']) == 1
    assert all(
        info[lce.name][cv.name][repo.name] == {}
        for cv in cvs
        for lce in [lce1, lce2]
        if (cv.name != cv1.name or lce.name != lce1.name)
    )

    # Promote the first CV to the second LCE.
    cv1.version[0].promote(data={'environment_ids': lce2.id})
    cv1 = cv1.read()
    module_target_sat.wait_for_tasks(
        search_query=wait_query.format(datetime.now(UTC).replace(microsecond=0)),
        search_rate=5,
        max_tries=5,
    )

    # Ensure counts for the first CV were updated in the second LCE, no changes for second CV.
    info = module_target_sat.cli.Capsule.content_info(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': function_org.id}
    )
    info = _dictionarize_counts(info)

    assert int(info[lce2.name][cv1.name][repo.name]['packages']) == 1
    assert int(info[lce2.name][cv1.name][repo.name]['package-groups']) == 1
    assert int(info[lce2.name][cv1.name][repo.name]['errata']) == 1
    assert all(info[lce.name][cv2.name][repo.name] == {} for lce in [lce1, lce2])


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


@pytest.mark.parametrize('repair_type', ['repo', 'cv', 'lce'])
@pytest.mark.parametrize(
    'module_synced_content',
    [
        {'content_type': 'yum', 'url': settings.repos.yum_0.url},
        {'content_type': 'file', 'url': CUSTOM_FILE_REPO},
        {
            'content_type': 'docker',
            'docker_upstream_name': settings.container.upstream_name,
            'url': settings.container.registry_hub,
        },
        {
            'content_type': 'ansible_collection',
            'url': ANSIBLE_GALAXY,
            'ansible_collection_requirements': '{collections: [ \
                    { name: theforeman.foreman, version: "2.1.0" }, \
                    { name: theforeman.operations, version: "0.1.0"} ]}',
        },
    ],
    indirect=True,
    ids=['yum', 'file', 'docker', 'AC'],
)
@pytest.mark.parametrize('damage_type', ['destroy', 'corrupt'])
def test_positive_repair_artifacts(
    module_target_sat,
    module_capsule_configured,
    module_capsule_setting,
    module_capsule_artifact_cleanup,
    module_synced_content,
    module_org,
    damage_type,
    repair_type,
):
    """Test the verify-checksum task repairs artifacts of each supported content type correctly
    at the Capsule side using each of its options when they were removed or corrupted before.

    :id: cdc2c4c7-72e1-451a-8bde-7f4340a5b73a

    :parametrized: yes

    :setup:
        1. Have a Satellite with registered external Capsule.
        2. Clean up all previously synced artifacts from the Capsule to ensure new artifacts are
           created on Capsule sync with expected creation time. (the fixtures order matters)
        3. Per parameter, create repository of each content type, publish it in a CV and promote
           to an LCE.
        4. Assign the Capsule with the LCE and sync it.

    :steps:
        1. Based on the repository content type
           - find and pick one artifact for particular published file, or
           - pick one artifact synced recently by the `module_synced_content` fixture.
        2. Cause desired type of damage to the artifact and verify the effect.
        3. Trigger desired variant of the repair (verify_checksum) task.
        4. Check if the artifact is back in shape.

    :expectedresults:
        1. Artifact is stored correctly based on the checksum. (yum and file)
        2. All variants of verify_checksum task are able to repair all types of damage for all
           supported content types.

    :verifies: SAT-16330

    :customerscenario: true

    """
    # Based on the repository content type
    if module_synced_content.repos[0].content_type in ['yum', 'file']:
        # Find and pick one artifact for particular published file.
        caps_repo_url = module_capsule_configured.get_published_repo_url(
            org=module_org.label,
            lce=None if repair_type == 'repo' else module_synced_content.lce.label,
            cv=None if repair_type == 'repo' else module_synced_content.cv.label,
            prod=module_synced_content.prod.label,
            repo=module_synced_content.repos[0].label,
        )
        cap_files_urls = get_repo_files_urls_by_url(
            caps_repo_url,
            extension='rpm' if module_synced_content.repos[0].content_type == 'yum' else 'iso',
        )
        url = random.choice(cap_files_urls)
        sum = module_target_sat.checksum_by_url(url, sum_type='sha256sum')
        ai = module_capsule_configured.get_artifact_info(checksum=sum)
    else:
        # Pick one artifact synced recently by the `module_synced_content` fixture.
        artifacts = module_capsule_configured.get_artifacts(since=module_synced_content.sync_time)
        assert len(artifacts) > 0, 'No NEW artifacts found'
        ai = module_capsule_configured.get_artifact_info(path=random.choice(artifacts))

    # Cause desired type of damage to the artifact and verify the effect.
    if damage_type == 'destroy':
        module_capsule_configured.execute(f'rm -f {ai.path}')
        with pytest.raises(FileNotFoundError):
            module_capsule_configured.get_artifact_info(path=ai.path)
    elif damage_type == 'corrupt':
        res = module_capsule_configured.execute(
            f'truncate -s {random.randrange(1, ai.size)} {ai.path}'
        )
        assert res.status == 0, f'Artifact truncation failed: {res.stderr}'
        assert module_capsule_configured.get_artifact_info(path=ai.path) != ai, (
            'Artifact corruption failed'
        )
    else:
        raise ValueError(f'Unsupported damage type: {damage_type}')

    # Trigger desired variant of repair (verify_checksum) task.
    opts = {'id': module_capsule_configured.nailgun_capsule.id}
    if repair_type == 'repo':
        opts.update({'repository-id': module_synced_content.repos[0].id})
    elif repair_type == 'cv':
        opts.update({'content-view-id': module_synced_content.cv.id})
    elif repair_type == 'lce':
        opts.update({'lifecycle-environment-id': module_synced_content.lce.id})
    module_target_sat.cli.Capsule.content_verify_checksum(opts)

    # Check if the artifact is back in shape.
    fixed_ai = module_capsule_configured.get_artifact_info(path=ai.path)
    assert fixed_ai == ai, f'Artifact restoration failed: {fixed_ai} != {ai}'

    if module_synced_content.repos[0].content_type in ['yum', 'file']:
        assert module_target_sat.checksum_by_url(url, sum_type='sha256sum') == ai.sum, (
            'Published file is unaccessible or corrupted'
        )


@pytest.mark.e2e
@pytest.mark.parametrize('function_flatpak_remote', ['RedHat'], indirect=True)
@pytest.mark.parametrize('setting_update', ['foreman_proxy_content_auto_sync=True'], indirect=True)
def test_sync_consume_flatpak_repo_via_library(
    request,
    module_target_sat,
    module_capsule_configured,
    setting_update,
    module_flatpak_contenthost,
    function_org,
    function_product,
    function_lce_library,
    function_flatpak_remote,
):
    """Verify flatpak repository workflow via capsule end to end.

    :id: 8871b695-18fd-45a8-bb40-664c384996a0

    :parametrized: yes

    :setup:
        1. Registered external capsule.
        2. Flatpak remote created and scanned.

    :steps:
        1. Associate the organization and its Library to the capsule.
        2. Mirror a flatpak repository and sync it, verify the capsule was synced.
        3. Create an AK with the library/default_org_view.
        4. Register a content host using the AK via Capsule.
        5. Configure the contenthost via REX to use Capsule's flatpak index.
        6. Install flatpak app from the repo via REX on the contenthost.
        7. Ensure the app has been installed successfully.

    :expectedresults:
        1. Entire workflow works and allows user to install a flatpak app at the registered
           contenthost.

    """
    sat, caps, host = module_target_sat, module_capsule_configured, module_flatpak_contenthost

    # Associate the organization and its Library to the capsule.
    res = sat.cli.Capsule.update(
        {'name': module_capsule_configured.hostname, 'organization-ids': function_org.id}
    )
    assert 'proxy updated' in str(res)

    caps.nailgun_capsule.content_add_lifecycle_environment(
        data={'environment_id': function_lce_library.id}
    )
    res = caps.nailgun_capsule.content_lifecycle_environments()
    assert len(res['results']) >= 1
    assert function_lce_library.id in [capsule_lce['id'] for capsule_lce in res['results']]

    # Mirror a flatpak repository and sync it, verify the capsule was synced.
    repo_names = ['rhel9/firefox-flatpak', 'rhel9/flatpak-runtime']  # runtime is dependency
    remote_repos = [r for r in function_flatpak_remote.repos if r['name'] in repo_names]
    for repo in remote_repos:
        sat.cli.FlatpakRemote().repository_mirror(
            {
                'flatpak-remote-id': function_flatpak_remote.remote['id'],
                'id': repo['id'],  # or by name
                'product-id': function_product.id,
            }
        )

    local_repos = sat.cli.Repository.list({'product-id': function_product.id})
    assert set([r['name'] for r in local_repos]) == set(repo_names)

    timestamp = datetime.now(UTC)
    for repo in local_repos:
        sat.cli.Repository.synchronize({'id': repo['id']})
    module_capsule_configured.wait_for_sync(start_time=timestamp)

    # Create an AK with the library/default_org_view.
    ak_lib = sat.cli.ActivationKey.create(
        {
            'name': gen_string('alpha'),
            'organization-id': function_org.id,
            'lifecycle-environment': 'Library',
            'content-view': 'Default Organization View',
        }
    )

    # Register a content host using the AK via Capsule.
    res = host.register(function_org, None, ak_lib['name'], caps, force=True)
    assert res.status == 0, (
        f'Failed to register host: {host.hostname}\nStdOut: {res.stdout}\nStdErr: {res.stderr}'
    )
    assert host.subscribed

    # Configure the contenthost via REX to use Capsule's flatpak index.
    remote_name = f'CAPS-remote-{gen_string("alpha")}'
    job = module_target_sat.cli_factory.job_invocation(
        {
            'organization': function_org.name,
            'job-template': 'Flatpak - Set up remote on host',
            'inputs': (
                f'Remote Name={remote_name}, '
                f'Flatpak registry URL={settings.server.scheme}://{caps.hostname}/pulpcore_registry/, '
                f'Username={settings.server.admin_username}, '
                f'Password={settings.server.admin_password}'
            ),
            'search-query': f"name = {host.hostname}",
        }
    )
    res = module_target_sat.cli.JobInvocation.info({'id': job.id})
    assert 'succeeded' in res['status']
    request.addfinalizer(lambda: host.execute(f'flatpak remote-delete {remote_name}'))

    # Install flatpak app from the repo via REX on the contenthost.
    res = host.execute('flatpak remotes')
    assert remote_name in res.stdout

    app_name = 'Firefox'  # or 'org.mozilla.Firefox'
    res = host.execute('flatpak remote-ls')
    assert app_name in res.stdout

    job = module_target_sat.cli_factory.job_invocation(
        {
            'organization': function_org.name,
            'job-template': 'Flatpak - Install application on host',
            'inputs': (
                f'Flatpak remote name={remote_name}, Application name={app_name}, '
                'Launch a session bus instance=true'
            ),
            'search-query': f"name = {host.hostname}",
        },
        timeout='800s',
    )
    res = module_target_sat.cli.JobInvocation.info({'id': job.id})
    assert 'succeeded' in res['status']
    request.addfinalizer(
        lambda: host.execute(f'flatpak uninstall {remote_name} {app_name} com.redhat.Platform -y')
    )

    # Ensure the app has been installed successfully.
    res = host.execute('flatpak list')
    assert app_name in res.stdout
