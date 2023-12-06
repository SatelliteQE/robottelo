"""Tests for the Incremental Update feature

:Requirement: Inc Updates

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime, timedelta

from nailgun import entities
import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_SUBSCRIPTION_NAME,
    ENVIRONMENT,
    FAKE_4_CUSTOM_PACKAGE,
    PRDS,
    REPOS,
    REPOSET,
)

pytestmark = [pytest.mark.run_in_one_thread]


@pytest.fixture(scope='module')
def module_lce_library(module_entitlement_manifest_org):
    """Returns the Library lifecycle environment from chosen organization"""
    return (
        entities.LifecycleEnvironment()
        .search(
            query={
                'search': f'name={ENVIRONMENT} and '
                f'organization_id={module_entitlement_manifest_org.id}'
            }
        )[0]
        .read()
    )


@pytest.fixture(scope='module')
def dev_lce(module_entitlement_manifest_org):
    return entities.LifecycleEnvironment(
        name='DEV', organization=module_entitlement_manifest_org
    ).create()


@pytest.fixture(scope='module')
def qe_lce(module_entitlement_manifest_org, dev_lce):
    qe_lce = entities.LifecycleEnvironment(
        name='QE', prior=dev_lce, organization=module_entitlement_manifest_org
    ).create()
    return qe_lce


@pytest.fixture(scope='module')
def sat_client_repo(module_entitlement_manifest_org, module_target_sat):
    """Enable Sat tools repository"""
    sat_client_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_entitlement_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhsclient7']['name'],
        reposet=REPOSET['rhsclient7'],
        releasever=None,
    )
    sat_client_repo = module_target_sat.api.Repository(id=sat_client_repo_id).read()
    assert sat_client_repo.sync()['result'] == 'success'
    return sat_client_repo


@pytest.fixture(scope='module')
def custom_repo(module_entitlement_manifest_org):
    """Enable custom errata repository"""
    custom_repo = entities.Repository(
        url=settings.repos.yum_9.url,
        product=entities.Product(organization=module_entitlement_manifest_org).create(),
    ).create()
    assert custom_repo.sync()['result'] == 'success'
    return custom_repo


@pytest.fixture(scope='module')
def module_cv(module_entitlement_manifest_org, sat_client_repo, custom_repo):
    """Publish both repos into module CV"""
    module_cv = entities.ContentView(
        organization=module_entitlement_manifest_org,
        repository=[sat_client_repo.id, custom_repo.id],
    ).create()
    module_cv.publish()
    module_cv = module_cv.read()
    return module_cv


@pytest.fixture(scope='module')
def module_ak(module_entitlement_manifest_org, module_cv, custom_repo, module_lce_library):
    """Create a module AK in Library LCE"""
    ak = entities.ActivationKey(
        content_view=module_cv,
        environment=module_lce_library,
        organization=module_entitlement_manifest_org,
    ).create()
    # Fetch available subscriptions
    subs = entities.Subscription(organization=module_entitlement_manifest_org).search()
    assert len(subs) > 0
    # Add default subscription to activation key
    sub_found = False
    for sub in subs:
        if sub.name == DEFAULT_SUBSCRIPTION_NAME:
            ak.add_subscriptions(data={'subscription_id': sub.id})
            sub_found = True
    assert sub_found
    # Enable RHEL product content in activation key
    ak.content_override(
        data={'content_overrides': [{'content_label': REPOS['rhsclient7']['id'], 'value': '1'}]}
    )
    # Add custom subscription to activation key
    prod = custom_repo.product.read()
    custom_sub = entities.Subscription(organization=module_entitlement_manifest_org).search(
        query={'search': f'name={prod.name}'}
    )
    ak.add_subscriptions(data={'subscription_id': custom_sub[0].id})
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
    module_entitlement_manifest_org,
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
        module_entitlement_manifest_org, None, module_ak.name, module_target_sat
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
    entities.RPMContentViewFilter(
        content_view=module_cv, inclusion=True, name='Include Nothing'
    ).create()
    module_cv.publish()
    module_cv = module_cv.read()
    return rhel7_contenthost_module


def get_applicable_errata(repo):
    """Retrieves applicable errata for the given repo"""
    return entities.Errata(repository=repo).search(query={'errata_restrict_applicable': True})


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_noapply_api(
    module_entitlement_manifest_org, module_cv, custom_repo, host, dev_lce
):
    """Check if api incremental update can be done without
    actually applying it

    :id: 481c5ff2-801f-4eff-b1e0-95ea5bb37f95

    :Setup:  get the content view id, Repository id and
        Lifecycle environment id

    :expectedresults: Incremental update completed with no errors and
        Content view has a newer version

    :parametrized: yes

    :CaseLevel: System
    """
    # Promote CV to new LCE
    versions = sorted(module_cv.read().version, key=lambda ver: ver.id)
    cvv = versions[-1].read()
    cvv.promote(data={'environment_ids': dev_lce.id})

    # Get the applicable errata
    errata_list = get_applicable_errata(custom_repo)
    assert len(errata_list) > 0

    # Apply incremental update using the first applicable errata
    outval = entities.ContentViewVersion().incremental_update(
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
