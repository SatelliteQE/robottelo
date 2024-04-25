"""Capsule-Content related tests being run through CLI.

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Phoenix-content

:CaseImportance: High

"""
from datetime import datetime
import random

from box import Box
import pytest

from robottelo.config import settings
from robottelo.constants import (
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
    PULP_ARTIFACT_DIR,
)
from robottelo.constants.repos import ANSIBLE_GALAXY, CUSTOM_FILE_REPO
from robottelo.content_info import get_repo_files_urls_by_url


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
    sync_time = datetime.utcnow().replace(microsecond=0)
    module_target_sat.cli.Capsule.content_synchronize(
        {'id': module_capsule_configured.nailgun_capsule.id, 'organization-id': module_org.id}
    )
    module_capsule_configured.wait_for_sync(start_time=sync_time)

    return Box(prod=module_product, repos=repos, cv=cv, lce=module_lce, sync_time=sync_time)


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
    timestamp = datetime.utcnow().replace(microsecond=0)
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


@pytest.mark.parametrize(
    'repos_collection',
    [
        {
            'distro': 'rhel8',
            'YumRepository': {'url': settings.repos.module_stream_1.url},
            'FileRepository': {'url': CUSTOM_FILE_REPO},
            'DockerRepository': {
                'url': CONTAINER_REGISTRY_HUB,
                'upstream_name': CONTAINER_UPSTREAM_NAME,
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

    repos_collection.setup_content(function_org.id, function_lce.id, upload_manifest=False)
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
    assert len(cv_info['repositories']) == len(
        cvv['repositories']
    ), 'Too many or few repositories listed'
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


@pytest.mark.stream
@pytest.mark.parametrize('repair_type', ['repo', 'cv', 'lce'])
@pytest.mark.parametrize(
    'module_synced_content',
    [
        [
            {'content_type': 'yum', 'url': settings.repos.yum_0.url},
            {'content_type': 'file', 'url': CUSTOM_FILE_REPO},
        ]
    ],
    indirect=True,
    ids=['content'],
)
@pytest.mark.parametrize('content_type', ['yum', 'file'])
@pytest.mark.parametrize('damage_type', ['destroy', 'corrupt'])
def test_positive_repair_yum_file_artifacts(
    module_target_sat,
    module_capsule_configured,
    module_capsule_artifact_cleanup,
    module_org,
    module_synced_content,
    damage_type,
    repair_type,
    content_type,
):
    """Test the verify-checksum task repairs particular RPM and FILE artifacts correctly
    at the Capsule side using one of its methods when they were removed or corrupted before.

    :id: f818f537-94b0-4d14-adf1-643ead828ade

    :parametrized: yes

    :setup:
        1. Have a Satellite with registered external Capsule.
        2. Clean up all previously synced artifacts from the Capsule.
        3. Create yum and file type repository, publish it in a CVV and promote to an LCE.
        4. Assign the Capsule with the LCE and sync it.

    :steps:
        1. Pick one of the published files.
        2. Cause desired type of damage to his artifact and verify the effect.
        3. Trigger desired variant of repair (verify_checksum) task.
        4. Check if the artifact is back in shape.

    :expectedresults:
        1. Artifact is stored correctly based on the checksum.
        2. All variants of verify_checksum task are able to repair all types of damage.

    :BZ: 2127537

    :customerscenario: true

    """
    repo = next(repo for repo in module_synced_content.repos if repo.content_type == content_type)

    # Pick one of the published files.
    caps_repo_url = module_capsule_configured.get_published_repo_url(
        org=module_org.label,
        lce=None if repair_type == 'repo' else module_synced_content.lce.label,
        cv=None if repair_type == 'repo' else module_synced_content.cv.label,
        prod=module_synced_content.prod.label,
        repo=repo.label,
    )
    cap_files_urls = get_repo_files_urls_by_url(
        caps_repo_url, extension='rpm' if content_type == 'yum' else 'iso'
    )

    file_url = random.choice(cap_files_urls)
    file_sum = module_target_sat.checksum_by_url(file_url, sum_type='sha256sum')
    file_ai = module_capsule_configured.get_artifact_info(checksum=file_sum)

    # Cause desired type of damage to his artifact and verify the effect.
    if damage_type == 'destroy':
        module_capsule_configured.execute(f'rm -f {file_ai.path}')
        with pytest.raises(FileNotFoundError):
            module_capsule_configured.get_artifact_info(checksum=file_sum)
        with pytest.raises(AssertionError):
            module_target_sat.checksum_by_url(file_url)
    elif damage_type == 'corrupt':
        res = module_capsule_configured.execute(
            f'truncate -s {random.randint(1, file_ai.size)} {file_ai.path}'
        )
        assert res.status == 0, f'Artifact truncation failed: {res.stderr}'
        assert (
            module_capsule_configured.get_artifact_info(checksum=file_sum) != file_ai
        ), 'Artifact corruption failed'
    else:
        raise ValueError(f'Unsupported damage type: {damage_type}')

    # Trigger desired variant of repair (verify_checksum) task.
    opts = {'id': module_capsule_configured.nailgun_capsule.id}
    if repair_type == 'repo':
        opts.update({'repository-id': repo.id})
    elif repair_type == 'cv':
        opts.update({'content-view-id': module_synced_content.cv.id})
    elif repair_type == 'lce':
        opts.update({'lifecycle-environment-id': module_synced_content.lce.id})
    module_target_sat.cli.Capsule.content_verify_checksum(opts)

    # Check if the artifact is back in shape.
    fixed_ai = module_capsule_configured.get_artifact_info(checksum=file_sum)
    assert fixed_ai == file_ai, f'Artifact restoration failed: {fixed_ai} != {file_ai}'


@pytest.mark.parametrize('repair_type', ['repo', 'cv', 'lce'])
@pytest.mark.parametrize(
    'module_synced_content',
    [
        {
            'content_type': 'docker',
            'docker_upstream_name': CONTAINER_UPSTREAM_NAME,
            'url': CONTAINER_REGISTRY_HUB,
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
    ids=['docker', 'AC'],
)
@pytest.mark.parametrize('damage_type', ['destroy', 'corrupt'])
def test_positive_repair_docker_AC_artifacts(
    module_target_sat, module_capsule_configured, module_synced_content, damage_type, repair_type
):
    """Test the verify-checksum task repairs particular docker and ansible-collection artifacts
    correctly at the Capsule side using one of its methods when they were removed or corrupted
    before.

    :id: b0e1a163-bf30-48bf-8d27-68c689ee0896

    :parametrized: yes

    :setup:
        1. Have a Satellite with registered external Capsule.
        2. Create docker and ansible-collection type repository, publish it in a CVV and promote
           to an LCE.
        3. Assign the Capsule with the LCE and sync it.

    :steps:
        1. Get all artifacts synced recently by the `module_synced_content` fixture.
        2. Pick one artifact and cause desired type of damage and verify the effect.
        3. Trigger desired variant of repair (verify_checksum) task.
        4. Check if the artifact is back in shape.

    :expectedresults:
        1. Artifact is stored correctly based on the checksum.
        2. All variants of verify_checksum task are able to repair all types of damage.

    :BZ: 2127537

    :customerscenario: true

    """
    # Get all artifacts synced recently by the `module_synced_content` fixture.
    artifacts = module_capsule_configured.execute(
        f'find {PULP_ARTIFACT_DIR} -type f -newermt "{module_synced_content.sync_time} UTC"'
    ).stdout.splitlines()
    assert len(artifacts) > 0, 'No NEW artifacts found'

    # Pick one artifact and cause desired type of damage and verify the effect.
    ai = module_capsule_configured.get_artifact_info(path=random.choice(artifacts))
    if damage_type == 'destroy':
        module_capsule_configured.execute(f'rm -f {ai.path}')
        with pytest.raises(FileNotFoundError):
            module_capsule_configured.get_artifact_info(path=ai.path)
    elif damage_type == 'corrupt':
        res = module_capsule_configured.execute(
            f'truncate -s {random.randint(1, ai.size)} {ai.path}'
        )
        assert res.status == 0, f'Artifact truncation failed: {res.stderr}'
        assert (
            module_capsule_configured.get_artifact_info(path=ai.path) != ai
        ), 'Artifact corruption failed'
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
