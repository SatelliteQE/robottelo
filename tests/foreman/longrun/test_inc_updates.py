"""Tests for the Incremental Update feature

:Requirement: Inc Updates

:CaseAutomation: Automated

:CaseComponent: Hosts-Content

:team: Phoenix-subscriptions

:CaseImportance: High

"""

from datetime import datetime, timedelta

import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    ENVIRONMENT,
    FAKE_4_CUSTOM_PACKAGE,
    PRDS,
    REAL_RHEL8_1_ERRATA_ID,
    REPOS,
    REPOSET,
)
from robottelo.logging import logger

pytestmark = [pytest.mark.run_in_one_thread]


@pytest.fixture(scope='module')
def module_lce_library(module_target_sat, module_sca_manifest_org):
    """Returns the Library lifecycle environment from chosen organization"""
    return (
        module_target_sat.api.LifecycleEnvironment()
        .search(
            query={
                'search': f'name={ENVIRONMENT} and ' f'organization_id={module_sca_manifest_org.id}'
            }
        )[0]
        .read()
    )


@pytest.fixture(scope='module')
def dev_lce(module_target_sat, module_sca_manifest_org):
    return module_target_sat.api.LifecycleEnvironment(
        name='DEV', organization=module_sca_manifest_org
    ).create()


@pytest.fixture(scope='module')
def qe_lce(module_target_sat, module_sca_manifest_org, dev_lce):
    return module_target_sat.api.LifecycleEnvironment(
        name='QE', prior=dev_lce, organization=module_sca_manifest_org
    ).create()


@pytest.fixture(scope='module')
def sat_client_repo(module_sca_manifest_org, module_target_sat):
    """Enable Sat tools repository"""
    sat_client_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_sca_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhsclient7']['name'],
        reposet=REPOSET['rhsclient7'],
        releasever=None,
    )
    sat_client_repo = module_target_sat.api.Repository(id=sat_client_repo_id).read()
    assert sat_client_repo.sync()['result'] == 'success'
    return sat_client_repo


@pytest.fixture(scope='module')
def custom_repo(module_sca_manifest_org, module_target_sat):
    """Enable custom errata repository"""
    custom_repo = module_target_sat.api.Repository(
        url=settings.repos.yum_9.url,
        product=module_target_sat.api.Product(organization=module_sca_manifest_org).create(),
    ).create()
    assert custom_repo.sync()['result'] == 'success'
    return custom_repo


@pytest.fixture(scope='module')
def module_cv(module_target_sat, module_sca_manifest_org, sat_client_repo, custom_repo):
    """Publish both repos into module CV"""
    module_cv = module_target_sat.api.ContentView(
        organization=module_sca_manifest_org,
        repository=[sat_client_repo.id, custom_repo.id],
    ).create()
    module_cv.publish()
    return module_cv.read()


@pytest.fixture(scope='module')
def module_ak(
    module_sca_manifest_org, module_cv, custom_repo, module_lce_library, module_target_sat
):
    """Create a module AK in Library LCE"""
    ak = module_target_sat.api.ActivationKey(
        content_view=module_cv,
        environment=module_lce_library,
        organization=module_sca_manifest_org,
    ).create()
    # Fetch available subscriptions
    subs = module_target_sat.api.Subscription(organization=module_sca_manifest_org).search()
    assert len(subs) > 0
    # Enable rhclient7 client repo in activation key
    ak.content_override(
        data={'content_overrides': [{'content_label': REPOS['rhsclient7']['id'], 'value': '1'}]}
    )

    # Enable custom repo in activation key
    all_content = ak.product_content(data={'content_access_mode_all': '1'})['results']
    for content in all_content:
        if content['name'] == custom_repo.name:
            content_label = content['label']
    ak.content_override(
        data={'content_overrides': [{'content_label': content_label, 'value': '1'}]}
    )
    return ak


@pytest.fixture(scope='module')
def host(
    rhel7_contenthost_module,
    module_sca_manifest_org,
    dev_lce,
    qe_lce,
    custom_repo,
    module_ak,
    module_cv,
    module_target_sat,
):
    # Create client machine and register it to satellite with rhel_7_partial_ak
    # Register, enable tools repo and install katello-host-tools.
    rhel7_contenthost_module.register(
        module_sca_manifest_org, None, module_ak.name, module_target_sat
    )
    rhel7_contenthost_module.enable_repo(REPOS['rhsclient7']['id'])
    # make a note of time for later wait_for_tasks, and include 4 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=4)).strftime('%Y-%m-%d %H:%M')
    # AK added custom repo for errata package, just install it.
    rhel7_contenthost_module.execute(f'yum install -y {FAKE_4_CUSTOM_PACKAGE}')
    rhel7_contenthost_module.execute('subscription-manager repos')
    # Wait for applicability update event (in case Satellite system slow)
    module_target_sat.wait_for_tasks(
        search_query='label = Actions::Katello::Applicability::Hosts::BulkGenerate'
        f' and started_at >= "{timestamp}"'
        f' and state = stopped'
        f' and result = success',
        search_rate=15,
        max_tries=10,
    )
    # Add filter of type include but do not include anything.
    # this will hide all RPMs from selected erratum before publishing.
    module_target_sat.api.RPMContentViewFilter(
        content_view=module_cv, inclusion=True, name='Include Nothing'
    ).create()
    module_cv.publish()
    module_cv = module_cv.read()
    return rhel7_contenthost_module


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_noapply_api(
    module_sca_manifest_org, module_cv, custom_repo, host, dev_lce, module_target_sat
):
    """Check if api incremental update can be done without
    actually applying it

    :id: 481c5ff2-801f-4eff-b1e0-95ea5bb37f95

    :Setup:  get the content view id, Repository id and
        Lifecycle environment id

    :expectedresults: Incremental update completed with no errors and
        Content view has a newer version

    :parametrized: yes
    """
    # Promote CV to new LCE
    versions = sorted(module_cv.read().version, key=lambda ver: ver.id)
    cvv = versions[-1].read()
    cvv.promote(data={'environment_ids': dev_lce.id})

    # Get the applicable errata for the given repo
    errata_list = module_target_sat.api.Errata(repository=custom_repo).search(
        query={'errata_restrict_applicable': True}
    )

    assert len(errata_list) > 0

    # Apply incremental update using the first applicable errata
    outval = module_target_sat.api.ContentViewVersion().incremental_update(
        data={
            'content_view_version_environments': [
                {
                    'content_view_version_id': cvv.id,
                    'environment_ids': [dev_lce.id],
                }
            ],
            'add_content': {'errata_ids': [errata_list[0].id]},
        }
    )
    assert outval['result'] == 'success'
    assert (
        outval['action']
        == 'Incremental Update of 1 Content View Version(s) with 1 Package(s), and 1 Errata'
    )


@pytest.mark.tier3
def test_positive_incremental_update_time(module_target_sat, module_sca_manifest_org):
    """Incremental update should not take a long time.

    :id: a9cdcc58-2d10-42cf-8e24-f7bec3b79d6b

    :steps:
        1. Setup larger rh repositories; rhel8 baseOS, rhst8, rhsc8.
        2. Create content view and add repos, sync and wait.
        3. Publish a content view version with all content.
        4. Using hammer, perform incremental update with errata, on that new version.
            - Log the duration of the incremental update
        5. Publish the full content-view, with added incremental version.
            - Log the duration of the content-view publish

    :expectedresults:
        1. Incremental update takes a short amount of time.
        2. Incremental update takes less time than full content-view publish,
            or the time taken for both was close (within 20%).

    :BZ: 2117760, 1829266

    :customerscenario: true

    """
    # create content view
    cv = module_target_sat.cli_factory.make_content_view(
        {'organization-id': module_sca_manifest_org.id}
    )
    repo_sync_timestamp = (
        datetime.utcnow().replace(microsecond=0) - timedelta(seconds=1)
    ).strftime('%Y-%m-%d %H:%M')
    # setup rh repositories, add to cv, begin sync
    for _repo in ['rhel8_bos', 'rhst8', 'rhsclient8']:
        rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=module_sca_manifest_org.id,
            product=PRDS['rhel8'],
            repo=REPOS[_repo]['name'],
            reposet=REPOSET[_repo],
            releasever=REPOS[_repo]['releasever'],
        )
        module_target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': module_sca_manifest_org.id,
                'repository-id': rh_repo_id,
            }
        )
        module_target_sat.api.Repository(id=rh_repo_id).sync(synchronous=False)

    # wait for all repo sync tasks
    sync_tasks = module_target_sat.wait_for_tasks(
        search_query=(
            'label = Actions::Katello::Repository::Sync'
            f' and started_at >= "{repo_sync_timestamp}"'
        ),
        search_rate=10,
        max_tries=200,
    )
    assert all(task.poll()['result'] == 'success' for task in sync_tasks)
    # publish and fetch new CVV
    module_target_sat.cli.ContentView.publish({'id': cv['id']})
    content_view = module_target_sat.cli.ContentView.info({'id': cv['id']})
    cvv = content_view['versions'][0]

    # update incremental version via hammer, using one errata.
    # expect: incr. "version-1.1" is created
    update_start_time = datetime.utcnow()
    result = module_target_sat.cli.ContentView.version_incremental_update(
        options={'content-view-version-id': cvv['id'], 'errata-ids': REAL_RHEL8_1_ERRATA_ID},
        output_format='base',
    )
    assert f'Content View: {cv.name} version 1.1' in result
    update_duration = (datetime.utcnow() - update_start_time).total_seconds()
    logger.info(
        f'Update of incremental version-1.1, for CV id: {content_view["id"]},'
        f' took {update_duration} seconds.'
    )
    # publish the full CV, containing the added version-1.1
    publish_start_time = datetime.utcnow()
    result = module_target_sat.cli.ContentView.publish({'id': cv['id']})
    publish_duration = (datetime.utcnow() - publish_start_time).total_seconds()
    logger.info(f'Publish for CV id: {content_view["id"]}, took {publish_duration} seconds.')
    # Per BZs: expect update duration was quicker than publish duration,
    # if instead, update took longer, check that they were close,
    # that update did not take ~significantly more time.
    if update_duration >= publish_duration:
        # unexpected: perhaps both tasks were very quick, took a handful of seconds,
        # assert the difference was not significant (within 20%).
        assert (update_duration - publish_duration) / publish_duration <= 0.25, (
            f'Incremental update took longer than publish of entire content-view id: {content_view["id"]}:'
            f' Update took significantly more time, 20% or longer, than publish.'
            f' update duration: {update_duration} s.\n publish duration: {publish_duration} s.'
        )
    # else: base expected condition: update duration was quicker than publish.

    # some arbritrary timeouts, given amount of content in CV from repos.
    assert update_duration <= 20, (
        'Possible performance degradation in incremental update time.',
        f' Took {update_duration} seconds, but expected to not exceed 20 seconds.',
    )
    assert publish_duration <= 30, (
        'Possible performance degradation in content-view publish time, after performing incremental update.',
        f' Took {publish_duration} seconds, but expected to not exceed 30 seconds.',
    )
