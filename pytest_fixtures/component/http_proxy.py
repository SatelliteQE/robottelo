from urllib.parse import urlparse

import pytest

from robottelo.config import settings
from robottelo.hosts import ProxyHost


@pytest.fixture(scope='session')
def session_auth_proxy(session_target_sat):
    """Instantiates authenticated HTTP proxy as a session-scoped fixture"""
    return ProxyHost(settings.http_proxy.auth_proxy_url)


@pytest.fixture
def satellite_cut_off(target_sat):
    """Cuts the Satellite off the DNS, leaving it with HTTP proxy only"""
    # First create entries in /etc/hosts for HTTP proxies and Satellite itself
    ips = []
    for url in [
        settings.http_proxy.un_auth_proxy_url,
        settings.http_proxy.auth_proxy_url,
        target_sat.url,
    ]:
        hostname = urlparse(url).hostname
        adr = target_sat.execute(
            f"nslookup {hostname} | awk '/^Address: / {{ print $2 }}'"
        ).stdout.strip()
        target_sat.execute(f'echo "{adr} {hostname}" >> /etc/hosts')
        ips.append(adr)
    # Cut off the nameservers
    target_sat.execute('sed -i "s/nameserver/;nameserver/g" /etc/resolv.conf')

    yield

    # Restore the nameservers
    target_sat.execute('sed -i "s/;nameserver/nameserver/g" /etc/resolv.conf')
    # Remove the added entries from /etc/hosts
    for adr in ips:
        target_sat.execute(f'sed -i "/^{adr}/d" /etc/hosts')


@pytest.fixture
def setup_http_proxy(request, module_manifest_org, target_sat):
    """Create a new HTTP proxy and set related settings based on proxy"""
    http_proxy = target_sat.api_factory.make_http_proxy(module_manifest_org, request.param)
    general_proxy = http_proxy.url if request.param is False else ''
    if request.param:
        general_proxy = (
            f'http://{settings.http_proxy.username}:'
            f'{settings.http_proxy.password}@{http_proxy.url[7:]}'
        )
    content_proxy_value = target_sat.update_setting(
        'content_default_http_proxy', http_proxy.name if request.param is not None else ''
    )
    general_proxy_value = target_sat.update_setting(
        'http_proxy', general_proxy if request.param is not None else ''
    )
    yield http_proxy, request.param
    target_sat.update_setting('content_default_http_proxy', content_proxy_value)
    target_sat.update_setting('http_proxy', general_proxy_value)
