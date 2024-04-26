"""Capsule-Content related tests being run through UI.

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Phoenix-content

:CaseImportance: High

"""

import pytest

from robottelo.config import settings
from robottelo.constants import DEFAULT_CV
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
    repos_collection.setup_content(function_org.id, function_lce.id, upload_manifest=False)
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
            assert (
                'N/A' in details['content'][lce]['top_row_content']['Last sync']
            ), 'LCE should be marked as unsynced'

            assert (
                details['content'][lce][cv.name]['mid_row_content']['Version']
                == f'Version {cvv.version}'
            ), 'CV version does not match'
            assert not details['content'][lce][cv.name]['mid_row_content'][
                'Synced'
            ], 'CV should not be marked as synced'

            repos_details = details['content'][lce][cv.name]['expanded_repo_details'][1:]
            assert all(
                [repo[1] == repo[2] == 'N/A' for repo in repos_details]
            ), 'Expected all content counts as N/A'

            if lce == 'Library':
                # Library should contain the Default Org View too
                assert DEFAULT_CV in details['content'][lce], 'Default Org View not listed'

                assert (
                    details['content'][lce][DEFAULT_CV]['mid_row_content']['Version']
                    == 'Version 1.0'
                ), 'CV version does not match'
                assert not details['content'][lce][DEFAULT_CV]['mid_row_content'][
                    'Synced'
                ], 'CV should not be marked as synced'

                repos_details = details['content'][lce][DEFAULT_CV]['expanded_repo_details'][1:]
                assert all(
                    [repo[1] == repo[2] == 'N/A' for repo in repos_details]
                ), 'Expected all content counts as N/A'

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
            assert (
                'ago' in details['content'][lce]['top_row_content']['Last sync']
            ), 'LCE should be marked as synced'
            assert details['content'][lce][cv.name]['mid_row_content'][
                'Synced'
            ], 'CV should be marked as synced'
            repos_details = details['content'][lce][cv.name]['expanded_repo_details'][1:]

            for s_repo in sat_repos:
                c_repo = next(r for r in repos_details if r[0] == s_repo.name)
                assert c_repo, 'Repository not listed'
                if s_repo.content_type == 'yum':
                    assert (
                        f'{s_repo.content_counts["rpm"]} Packages' in c_repo
                    ), 'RPMs count does not match'
                    assert (
                        f'{s_repo.content_counts["erratum"]} Errata' in c_repo
                    ), 'Errata count does not match'
                    assert (
                        f'{s_repo.content_counts["package_group"]} Package groups' in c_repo
                    ), 'Package groups count does not match'
                    assert (
                        f'{s_repo.content_counts["module_stream"]} Module streams' in c_repo
                    ), 'Module streams count does not match'
                elif s_repo.content_type == 'file':
                    assert (
                        f'{s_repo.content_counts["file"]} Files' in c_repo
                    ), 'Files count does not match'
                elif s_repo.content_type == 'docker':
                    assert (
                        f'{s_repo.content_counts["docker_tag"]} Container tags' in c_repo
                    ), 'Container tags count does not match'
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
