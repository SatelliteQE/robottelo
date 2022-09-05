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
from fauxfactory import gen_string

from robottelo import constants
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.config import settings


def create_http_proxy(sat, org, proxy_type):
    """
    Creates HTTP proxy.

    :param str sat: Satellite to use.
    :param str org: Organization
    :param str proxy_type: 'auth_http_proxy' or 'unauth_http_proxy' http proxy.
    """
    if proxy_type == 'unauth_http_proxy':
        return sat.api.HTTPProxy(
            name=gen_string('alpha', 15),
            url=settings.http_proxy.un_auth_proxy_url,
            organization=[org.id],
        ).create()
    if proxy_type == 'auth_http_proxy':
        return sat.api.HTTPProxy(
            name=gen_string('alpha', 15),
            url=settings.http_proxy.auth_proxy_url,
            username=settings.http_proxy.username,
            password=settings.http_proxy.password,
            organization=[org.id],
        ).create()


@pytest.fixture(scope='function')
def function_http_proxy(request, module_manifest_org, target_sat):
    """Create a new HTTP proxy and set related settings based on proxy"""
    http_proxy = create_http_proxy(target_sat, module_manifest_org, request.param)
    general_proxy = http_proxy.url if request.param == "unauth_http_proxy" else ''
    if request.param == "auth_http_proxy":
        general_proxy = (
            f'http://{settings.http_proxy.username}:'
            f'{settings.http_proxy.password}@{http_proxy.url[7:]}'
        )
    content_proxy_value = target_sat.update_setting(
        'content_default_http_proxy', http_proxy.name if request.param != "no_http_proxy" else ''
    )
    general_proxy_value = target_sat.update_setting(
        'http_proxy', general_proxy if request.param != "no_http_proxy" else ''
    )
    yield http_proxy, request.param
    target_sat.update_setting('content_default_http_proxy', content_proxy_value)
    target_sat.update_setting('http_proxy', general_proxy_value)


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize(
    'function_http_proxy', ['no_http_proxy', 'auth_http_proxy', 'unauth_http_proxy'], indirect=True
)
def test_positive_end_to_end(function_http_proxy, target_sat, module_manifest_org):
    """End-to-end test for HTTP Proxy related scenarios.

    :id: 38df5479-9127-49f3-a30e-26b33655971a

    :steps:
        1. Set Http proxy settings for Satellite.
        2. Enable and sync redhat repository.
        3. Assign Http Proxy to custom repository and perform repo sync.

    :expectedresults: HTTP Proxy works with other satellite components.

    :Assignee: jpathan

    :BZ: 2011303, 2042473

    :parametrized: yes

    :CaseImportance: Critical
    """
    http_proxy, http_proxy_type = function_http_proxy
    http_proxy_id = http_proxy.id if http_proxy_type != 'no_http_proxy' else None
    http_proxy_policy = 'use_selected_http_proxy' if http_proxy_type != 'no_http_proxy' else 'none'
    # Assign http_proxy to Redhat repository and perform repository sync.
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=module_manifest_org.id,
        product=constants.PRDS['rhae'],
        repo=constants.REPOS['rhae2']['name'],
        reposet=constants.REPOSET['rhae2'],
        releasever=None,
    )
    rh_repo = target_sat.api.Repository(
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
    repo = target_sat.api.Repository(**repo_options).create()

    assert repo.http_proxy_policy == http_proxy_policy
    assert repo.http_proxy_id == http_proxy_id
    repo.sync()
    assert repo.read().content_counts['rpm'] >= 1

    # Use global_default_http_proxy
    repo_options['http_proxy_policy'] = 'global_default_http_proxy'
    repo_2 = target_sat.api.Repository(**repo_options).create()
    assert repo_2.http_proxy_policy == 'global_default_http_proxy'

    # Update to selected_http_proxy
    repo_2.http_proxy_policy = 'none'
    repo_2.update(['http_proxy_policy'])
    assert repo_2.http_proxy_policy == 'none'
