import pytest

from robottelo.config import settings
from robottelo.hosts import ProxyHost


@pytest.fixture(scope='session')
def session_auth_proxy(session_target_sat):
    """Instantiates authenticated HTTP proxy as a session-scoped fixture"""
    return ProxyHost(settings.http_proxy.auth_proxy_url)


@pytest.fixture
def setup_http_proxy(request, module_sca_manifest_org, target_sat):
    """Create a new HTTP proxy and set related settings based on proxy"""
    content_proxy = target_sat.api.Setting().search(
        query={'search': 'name=content_default_http_proxy'}
    )[0]
    content_proxy_value = '' if content_proxy.value is None else content_proxy.value
    general_proxy = target_sat.api.Setting().search(query={'search': 'name=http_proxy'})[0]
    general_proxy_value = '' if general_proxy.value is None else general_proxy.value

    http_proxy = target_sat.api_factory.make_http_proxy(module_sca_manifest_org, request.param)
    content_proxy = target_sat.api.Setting().search(
        query={'search': 'name=content_default_http_proxy'}
    )[0]
    assert content_proxy.value == (http_proxy.name if request.param is not None else '')

    if request.param is not None:
        general_proxy = (
            f'http://{settings.http_proxy.username}:{settings.http_proxy.password}@{http_proxy.url[7:]}'
            if request.param
            else http_proxy.url
        )
        target_sat.update_setting('http_proxy', general_proxy)
    else:
        target_sat.update_setting('content_default_http_proxy', '')
        target_sat.update_setting('http_proxy', '')

    yield http_proxy, request.param
    target_sat.update_setting('content_default_http_proxy', content_proxy_value)
    target_sat.update_setting('http_proxy', general_proxy_value)
    if http_proxy:
        http_proxy.delete()


@pytest.fixture
def setup_http_proxy_without_global_settings(request, module_sca_manifest_org, target_sat):
    """Create a new HTTP proxy but don't set it as global or content proxy"""
    http_proxy = target_sat.api_factory.make_http_proxy(module_sca_manifest_org, request.param)
    yield http_proxy, request.param
    if http_proxy:
        http_proxy.delete()


@pytest.fixture
def setup_http_proxy_global(request, target_sat):
    """Create a new HTTP proxy and set related settings based on proxy"""
    if request.param:
        hostname = settings.http_proxy.auth_proxy_url[7:]
        general_proxy = (
            f'http://{settings.http_proxy.username}:{settings.http_proxy.password}@{hostname}'
        )
    else:
        general_proxy = settings.http_proxy.un_auth_proxy_url
    general_proxy_value = target_sat.update_setting(
        'http_proxy', general_proxy if request.param is not None else ''
    )
    yield general_proxy, request.param
    target_sat.update_setting('http_proxy', general_proxy_value)
