import pytest
from fauxfactory import gen_string

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
