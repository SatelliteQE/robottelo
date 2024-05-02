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
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
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
@pytest.mark.stream
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


@pytest.mark.stream
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
