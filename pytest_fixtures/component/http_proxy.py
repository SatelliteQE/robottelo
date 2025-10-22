from urllib.parse import urlparse

import pytest

from robottelo.config import settings
from robottelo.hosts import ProxyHost


@pytest.fixture(scope='session')
def session_auth_proxy(session_target_sat):
    """Instantiates authenticated HTTP proxy as a session-scoped fixture"""
    return ProxyHost(settings.http_proxy.auth_proxy_url)


@pytest.fixture
def setup_http_proxy(request, use_ip, module_org, target_sat):
    """Create a new HTTP proxy and set related settings based on proxy"""
    proxy_settings = ['content_default_http_proxy', 'http_proxy']
    saved_proxies = list(
        map(
            lambda x: target_sat.api.Setting().search(query={'search': f'name={x}'})[0],
            proxy_settings,
        )
    )

    http_proxy = target_sat.api_factory.make_http_proxy(module_org, request.param, use_ip)

    if request.param is None:
        target_sat.update_setting('content_default_http_proxy', '')
        target_sat.update_setting('http_proxy', '')
    else:
        content_proxy_setting = target_sat.api.Setting().search(
            query={'search': 'name=content_default_http_proxy'}
        )[0]
        assert content_proxy_setting.value == http_proxy.name
        protocol, hostname_port = http_proxy.url.split('://')
        general_proxy_url = (
            f'{protocol}://{settings.http_proxy.username}:{settings.http_proxy.password}@{hostname_port}'
            if request.param
            else http_proxy.url
        )
        target_sat.update_setting('http_proxy', general_proxy_url)

    yield http_proxy, request.param

    for setting in proxy_settings:
        target_sat.update_setting(setting, saved_proxies.pop(0).value)
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
        parsed_url = urlparse(settings.http_proxy.un_auth_proxy_url)
        protocol = parsed_url.scheme
        hostname = parsed_url.netloc
        general_proxy = (
            f'{protocol}://{settings.http_proxy.username}:{settings.http_proxy.password}@{hostname}'
        )
    else:
        general_proxy = settings.http_proxy.un_auth_proxy_url
    general_proxy_value = target_sat.update_setting(
        'http_proxy', general_proxy if request.param is not None else ''
    )
    yield general_proxy, request.param
    target_sat.update_setting('http_proxy', general_proxy_value)
