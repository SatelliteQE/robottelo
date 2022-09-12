"""Tests for http-proxy component.

:Requirement: HttpProxy

:CaseLevel: Acceptance

:CaseComponent: Repositories

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import pytest
from broker import Broker

from robottelo import constants
from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.hosts import ContentHost
from robottelo.hosts import ContentHostError


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize(
    'setup_http_proxy',
    [None, True, False],
    indirect=True,
    ids=['no_http_proxy', 'auth_http_proxy', 'unauth_http_proxy'],
)
def test_positive_end_to_end(setup_http_proxy, module_target_sat, module_manifest_org):
    """End-to-end test for HTTP Proxy related scenarios.

    :id: 38df5479-9127-49f3-a30e-26b33655971a

    :customerscenario: true

    :steps:
        1. Set Http proxy settings for Satellite.
        2. Enable and sync redhat repository.
        3. Assign Http Proxy to custom repository and perform repo sync.
        4. Discover yum type repo.
        5. Discover docker type repo.

    :expectedresults: HTTP Proxy works with other satellite components.

    :Assignee: jpathan

    :BZ: 2011303, 2042473, 2046337

    :parametrized: yes

    :CaseImportance: Critical
    """
    http_proxy, http_proxy_type = setup_http_proxy
    http_proxy_id = http_proxy.id if http_proxy_type is not None else None
    http_proxy_policy = 'use_selected_http_proxy' if http_proxy_type is not None else 'none'
    # Assign http_proxy to Redhat repository and perform repository sync.
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=module_manifest_org.id,
        product=constants.PRDS['rhae'],
        repo=constants.REPOS['rhae2']['name'],
        reposet=constants.REPOSET['rhae2'],
        releasever=None,
    )
    rh_repo = module_target_sat.api.Repository(
        id=rh_repo_id,
        http_proxy_policy=http_proxy_policy,
        http_proxy_id=http_proxy_id,
        download_policy='immediate',
    ).update()
    assert rh_repo.http_proxy_policy == http_proxy_policy
    assert rh_repo.http_proxy_id == http_proxy_id
    assert rh_repo.download_policy == 'immediate'
    rh_repo.sync()
    assert rh_repo.read().content_counts['rpm'] >= 1

    # Assign http_proxy to Repositories and perform repository sync.
    repo_options = {
        'http_proxy_policy': http_proxy_policy,
        'http_proxy_id': http_proxy_id,
    }
    repo = module_target_sat.api.Repository(**repo_options).create()

    assert repo.http_proxy_policy == http_proxy_policy
    assert repo.http_proxy_id == http_proxy_id
    repo.sync()
    assert repo.read().content_counts['rpm'] >= 1

    # Use global_default_http_proxy
    repo_options['http_proxy_policy'] = 'global_default_http_proxy'
    repo_2 = module_target_sat.api.Repository(**repo_options).create()
    assert repo_2.http_proxy_policy == 'global_default_http_proxy'

    # Update to selected_http_proxy
    repo_2.http_proxy_policy = 'none'
    repo_2.update(['http_proxy_policy'])
    assert repo_2.http_proxy_policy == 'none'

    # test scenario for yum type repo discovery.
    repo_name = 'fakerepo01'
    yum_repo = module_target_sat.api.Organization(id=module_manifest_org.id).repo_discover(
        data={
            "id": module_manifest_org.id,
            "url": settings.repos.repo_discovery.url,
            "content_type": "yum",
        }
    )
    assert len(yum_repo['output']) == 1
    assert yum_repo['output'][0] == f'{settings.repos.repo_discovery.url}/{repo_name}/'

    # test scenario for docker type repo discovery.
    yum_repo = module_target_sat.api.Organization(id=module_manifest_org.id).repo_discover(
        data={
            "id": module_manifest_org.id,
            "url": 'quay.io',
            "content_type": "docker",
            "search": 'quay/busybox',
        }
    )
    assert len(yum_repo['output']) >= 1
    assert 'quay/busybox' in yum_repo['output']


@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize(
    'setup_http_proxy',
    [None, True, False],
    indirect=True,
    ids=['no_http_proxy', 'auth_http_proxy', 'unauth_http_proxy'],
)
@pytest.mark.cli_host_subscription
@pytest.mark.tier3
def test_positive_auto_attach(setup_http_proxy, module_target_sat, function_org):
    """Attempt to auto attach a subscription to content host

    :id: cce888b5-e023-4ee2-bffe-efa9260224ee

    :expectedresults: host successfully subscribed, subscription
        repository enabled, and repository package installed

    :parametrized: yes

    :CaseLevel: System
    """
    with manifests.clone() as manifest:
        upload_manifest(function_org.id, manifest.content)
    lce = module_target_sat.api.LifecycleEnvironment(organization=function_org).create()
    content_view = module_target_sat.api.ContentView(organization=function_org).create()
    content_view.publish()
    content_view = content_view.read()
    module_target_sat.api.LifecycleEnvironment(organization=function_org).create()
    promote(content_view.version[0], environment_id=lce.id)
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=function_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    cv = module_target_sat.api.ContentView(id=content_view.id, repository=[rh_repo]).update(
        ["repository"]
    )
    cv.publish()
    cv = cv.read()
    promote(cv.version[-1], environment_id=lce.id)
    subscription = module_target_sat.api.Subscription(organization=function_org.id).search(
        query={'search': f'name="{constants.DEFAULT_SUBSCRIPTION_NAME}"'}
    )
    assert len(subscription)
    activation_key = module_target_sat.api.ActivationKey(
        content_view=cv,
        organization=function_org,
        environment=lce,
        auto_attach=False,
    ).create()
    activation_key.add_subscriptions(data={'subscription_id': subscription[0].id})

    with Broker(nick='rhel7', host_classes={'host': ContentHost}) as vm:
        # Test auto-attach
        module_target_sat.cli.Host.subscription_register(
            {
                'organization-id': function_org.id,
                'content-view-id': content_view.id,
                'lifecycle-environment-id': lce.id,
                'name': vm.hostname,
            }
        )
        host = module_target_sat.cli.Host.info({'name': vm.hostname})
        vm.register_contenthost(org=function_org.name, activation_key=activation_key.name)
        module_target_sat.cli.Host.subscription_auto_attach({'host-id': host['id']})
        vm.enable_repo(REPOS['rhst7']['id'])
        # ensure that katello agent can be installed
        try:
            vm.install_katello_agent()
        except ContentHostError:
            pytest.fail('ContentHostError raised unexpectedly!')
