"""Pulp artifacts related tests being run through CLI.

:Requirement: Repositories

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

from datetime import datetime
import random

from box import Box
import pytest

from robottelo.config import settings
from robottelo.constants.repos import ANSIBLE_GALAXY, CUSTOM_FILE_REPO
from robottelo.content_info import get_repo_files_urls_by_url


@pytest.fixture(scope='module')
def module_synced_content(
    request,
    module_target_sat,
    module_org,
    module_product,
):
    """
    Create and sync one or more repositories and publish them in a CV.

    :param request: Repo to use - dict with options to create the repo.
    :return: Box with created instances and Repository sync time.
    """
    repo = module_target_sat.api.Repository(product=module_product, **request.param).create()
    sync_time = datetime.utcnow().replace(microsecond=0)
    repo.sync()

    cv = module_target_sat.api.ContentView(organization=module_org, repository=[repo]).create()
    cv.publish()

    return Box(prod=module_product, repo=repo, cv=cv.read(), sync_time=sync_time)


@pytest.mark.parametrize('repair_type', ['repo', 'cv', 'product'])
@pytest.mark.parametrize(
    'module_synced_content',
    [
        {'content_type': 'yum', 'url': settings.repos.yum_0.url},
        {'content_type': 'file', 'url': CUSTOM_FILE_REPO},
        # The following repos should be unique through robottelo to avoid 'No NEW artifacts found'
        {
            'content_type': 'docker',
            'docker_upstream_name': 'libpod/busybox',
            'url': 'https://quay.io',
        },
        {
            'content_type': 'ansible_collection',
            'url': ANSIBLE_GALAXY,
            'ansible_collection_requirements': '{collections: [ \
                    { name: icinga.icinga, version: "0.3.3" }, \
                    { name: icinga.icinga, version: "0.3.2"} ]}',
        },
    ],
    indirect=True,
    ids=['yum', 'file', 'docker', 'AC'],
)
@pytest.mark.parametrize('damage_type', ['destroy', 'corrupt'])
def test_positive_artifact_repair(
    module_target_sat,
    module_org,
    module_lce_library,
    module_synced_content,
    damage_type,
    repair_type,
):
    """Test the verify-checksum task repairs artifacts of each supported content type correctly
    at the Satellite side for repo, CVV and product when the artifacts were removed or corrupted
    before.

    :id: 55c31fdc-bfa1-4af4-9adf-35c996eca974

    :parametrized: yes

    :setup:
        1. Have a blank Satellite to avoid any artifacts already synced by other tests.
        2. Per parameter, create repository of each content type, publish it in a CV.

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

    """
    # Based on the repository content type
    if module_synced_content.repo.content_type in ['yum', 'file']:
        # Find and pick one artifact for particular published file.
        sat_repo_url = module_target_sat.get_published_repo_url(
            org=module_org.label,
            lce=None if repair_type == 'repo' else module_lce_library.label,
            cv=None if repair_type == 'repo' else module_synced_content.cv.label,
            prod=module_synced_content.prod.label,
            repo=module_synced_content.repo.label,
        )
        sat_files_urls = get_repo_files_urls_by_url(
            sat_repo_url,
            extension='rpm' if module_synced_content.repo.content_type == 'yum' else 'iso',
        )
        url = random.choice(sat_files_urls)
        sum = module_target_sat.checksum_by_url(url, sum_type='sha256sum')
        ai = module_target_sat.get_artifact_info(checksum=sum)
    else:
        # Pick one artifact synced recently by the `module_synced_content` fixture.
        artifacts = module_target_sat.get_artifacts(since=module_synced_content.sync_time)
        assert len(artifacts) > 0, 'No NEW artifacts found'
        ai = module_target_sat.get_artifact_info(path=random.choice(artifacts))

    # Cause desired type of damage to the artifact and verify the effect.
    if damage_type == 'destroy':
        module_target_sat.execute(f'rm -f {ai.path}')
        with pytest.raises(FileNotFoundError):
            module_target_sat.get_artifact_info(path=ai.path)
    elif damage_type == 'corrupt':
        res = module_target_sat.execute(f'truncate -s {random.randrange(1, ai.size)} {ai.path}')
        assert res.status == 0, f'Artifact truncation failed: {res.stderr}'
        assert module_target_sat.get_artifact_info(path=ai.path) != ai, 'Artifact corruption failed'
    else:
        raise ValueError(f'Unsupported damage type: {damage_type}')

    # Trigger desired variant of repair (verify_checksum) task.
    if repair_type == 'repo':
        module_target_sat.cli.Repository.verify_checksum({'id': module_synced_content.repo.id})
    elif repair_type == 'cv':
        cvv_id = module_synced_content.cv.version[0].id
        module_target_sat.cli.ContentView.version_verify_checksum({'id': cvv_id})
    elif repair_type == 'product':
        module_target_sat.cli.Product.verify_checksum({'ids': module_synced_content.prod.id})
    else:
        raise ValueError(f'Unsupported repair type: {repair_type}')

    # Check if the artifact is back in shape.
    fixed_ai = module_target_sat.get_artifact_info(path=ai.path)
    assert fixed_ai == ai, f'Artifact restoration failed: {fixed_ai} != {ai}'
