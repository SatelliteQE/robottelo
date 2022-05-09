"""Tests for the Incremental Update feature

:Requirement: Inc Updates

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:Assignee: spusater

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime
from datetime import timedelta

import pytest
from nailgun import entities

from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET

pytestmark = [pytest.mark.run_in_one_thread]


@pytest.fixture(scope='module')
def module_lce_library(module_manifest_org):
    """Returns the Library lifecycle environment from chosen organization"""
    return (
        entities.LifecycleEnvironment()
        .search(
            query={'search': f'name={ENVIRONMENT} and organization_id={module_manifest_org.id}'}
        )[0]
        .read()
    )


@pytest.fixture(scope='module')
def dev_lce(module_manifest_org):
    return entities.LifecycleEnvironment(name='DEV', organization=module_manifest_org).create()


@pytest.fixture(scope='module')
def qe_lce(module_manifest_org, dev_lce):
    qe_lce = entities.LifecycleEnvironment(
        name='QE', prior=dev_lce, organization=module_manifest_org
    ).create()
    return qe_lce


@pytest.fixture(scope='module')
def rhel7_sat6tools_repo(module_manifest_org):
    """Enable Sat tools repository"""
    rhel7_sat6tools_repo_id = enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rhel7_sat6tools_repo = entities.Repository(id=rhel7_sat6tools_repo_id).read()
    assert rhel7_sat6tools_repo.sync()['result'] == 'success'
    return rhel7_sat6tools_repo


@pytest.fixture(scope='module')
def custom_repo(module_manifest_org):
    """Enable custom errata repository"""
    custom_repo = entities.Repository(
        url=settings.repos.yum_9.url,
        product=entities.Product(organization=module_manifest_org).create(),
    ).create()
    assert custom_repo.sync()['result'] == 'success'
    return custom_repo


@pytest.fixture(scope='module')
def module_cv(module_manifest_org, rhel7_sat6tools_repo, custom_repo):
    """Publish both repos into module CV"""
    module_cv = entities.ContentView(
        organization=module_manifest_org, repository=[rhel7_sat6tools_repo.id, custom_repo.id]
    ).create()
    module_cv.publish()
    module_cv = module_cv.read()
    return module_cv


@pytest.fixture(scope='module')
def module_ak(module_manifest_org, module_cv, custom_repo, module_lce_library):
    """Create a module AK in Library LCE"""
    ak = entities.ActivationKey(
        content_view=module_cv,
        environment=module_lce_library,
        organization=module_manifest_org,
    ).create()
    # Fetch available subscriptions
    subs = entities.Subscription(organization=module_manifest_org).search()
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
        data={'content_overrides': [{'content_label': REPOS['rhst7']['id'], 'value': '1'}]}
    )
    # Add custom subscription to activation key
    prod = custom_repo.product.read()
    custom_sub = entities.Subscription(organization=module_manifest_org).search(
        query={'search': f'name={prod.name}'}
    )
    ak.add_subscriptions(data={'subscription_id': custom_sub[0].id})
    return ak


@pytest.fixture(scope='module')
def host(
    rhel7_contenthost_module,
    module_manifest_org,
    dev_lce,
    qe_lce,
    custom_repo,
    module_ak,
    module_cv,
    module_target_sat,
):
    # Create client machine and register it to satellite with rhel_7_partial_ak
    rhel7_contenthost_module.install_katello_ca(module_target_sat)
    # Register, enable tools repo and install katello-host-tools.
    rhel7_contenthost_module.register_contenthost(module_manifest_org.label, module_ak.name)
    rhel7_contenthost_module.enable_repo(REPOS['rhst7']['id'])
    rhel7_contenthost_module.install_katello_host_tools()
    # make a note of time for later wait_for_tasks, and include 4 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=4)).strftime('%Y-%m-%d %H:%M')
    # AK added custom repo for errata package, just install it.
    rhel7_contenthost_module.execute(f'yum install -y {FAKE_4_CUSTOM_PACKAGE}')
    rhel7_contenthost_module.execute('katello-package-upload')
    # Wait for applicability update event (in case Satellite system slow)
    wait_for_tasks(
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
def test_positive_noapply_api(module_manifest_org, module_cv, custom_repo, host, dev_lce):
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
    promote(cvv, dev_lce.id)
    # Read CV to pick up LCE ID and next_version
    module_cv = module_cv.read()

    # Get the content view versions and use the recent one. API always
    # returns the versions in ascending order (last in the list is most recent)
    cv_versions = module_cv.version
    # Get the applicable errata
    errata_list = get_applicable_errata(custom_repo)
    assert len(errata_list) > 0

    # Apply incremental update using the first applicable errata
    entities.ContentViewVersion().incremental_update(
        data={
            'content_view_version_environments': [
                {
                    'content_view_version_id': cv_versions[-1].id,
                    'environment_ids': [dev_lce.id],
                }
            ],
            'add_content': {'errata_ids': [errata_list[0].id]},
        }
    )
    # Re-read the content view to get the latest versions
    module_cv = module_cv.read()
    assert len(module_cv.version) > len(cv_versions)
