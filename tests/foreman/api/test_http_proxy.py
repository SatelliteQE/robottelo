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
import re
import tempfile
import time
from string import punctuation
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.parse import urlunparse

import pytest
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from requests.exceptions import HTTPError

from robottelo import constants
from robottelo import datafactory
from robottelo import manifests
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import DataFile
from robottelo.constants import repos as repo_constants
from robottelo.datafactory import parametrized
from robottelo.logging import logger


@pytest.fixture
def repo_options(request, module_org, module_product):
    """Return the options that were passed as indirect parameters."""
    options = getattr(request, 'param', {}).copy()
    options['organization'] = module_org
    options['product'] = module_product
    return options


@pytest.fixture
def repo_options_custom_product(request, module_org):
    """Return the options that were passed as indirect parameters."""
    options = getattr(request, 'param', {}).copy()
    options['organization'] = module_org
    options['product'] = entities.Product(organization=module_org).create()
    return options


@pytest.fixture
def env(module_org):
    """Create a new puppet environment."""
    return entities.Environment(organization=[module_org]).create()


@pytest.fixture
def repo(repo_options):
    """Create a new repository."""
    return entities.Repository(**repo_options).create()


@pytest.fixture(scope="function")
def settings_update(request):
    """
    This fixture is used to create an object of the provided settings parameter that we use in
    each test case to update their attributes and once the test case gets completed it helps to
    restore their default value
    """
    setting_object = entities.Setting().search(query={'search': f'name={request.param}'})[0]
    default_setting_value = setting_object.value
    if default_setting_value is None:
        default_setting_value = ''
    yield setting_object
    setting_object.value = default_setting_value
    setting_object.update({'value'})


def create_http_proxy(org, proxy_type):
    """
    Create a HTTP proxy.

    :param str org: Organization
    :param str proxy_type: 'auth_http_proxy' or 'unauth_http_proxy' http proxy.
    """
    if proxy_type == 'unauth_http_proxy':
        return entities.HTTPProxy(
            name=gen_string('alpha', 15),
            url=settings.http_proxy.auth_proxy_url,
            organization=[org.id],
        ).create()
    if proxy_type == 'auth_http_proxy':
        return entities.HTTPProxy(
            name=gen_string('alpha', 15),
            url=settings.http_proxy.auth_proxy_url,
            username=settings.http_proxy.username,
            password=settings.http_proxy.password,
            organization=[org.id],
        ).create()


@pytest.fixture(scope="function")
def restore_settings(request):
    """ds"""
    default_settings = {}
    for setting in request.param:
        setting_object = entities.Setting().search(query={'search': f'name={setting}'})[0]
        default_settings[setting] = setting_object.value
        if default_settings[setting] is None:
            default_settings[setting] = ''
    yield
    for setting, value in default_settings.items():
        setting_object = entities.Setting().search(query={'search': f'name={setting}'})[0]
        setting_object.value = value
        setting_object.update({'value'})


@pytest.fixture(scope='function')
def update_http_proxy_setting(request, module_org):
    """Set HTTP Proxy related settings based on proxy"""
    http_proxy = create_http_proxy(module_org, request.param)
    general_proxy = http_proxy.url if request.param == "unauth_http_proxy" else ''
    if request.param == "auth_http_proxy":
        general_proxy = f'http://{settings.http_proxy.username}:{settings.http_proxy.password}@{http_proxy.url[7:]}'

    setting_entity = entities.Setting().search(query={'search': 'name=content_default_http_proxy'})[0]
    setting_entity.value = http_proxy.name if request.param != "no_http_proxy" else ''
    setting_entity.update({'value'})

    setting_entity = entities.Setting().search(query={'search': 'name=http_proxy'})[0]
    setting_entity.value = general_proxy if request.param != "no_http_proxy" else ''
    setting_entity.update({'value'})


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('restore_settings', [['content_default_http_proxy', 'http_proxy']], indirect=True, ids='')
@pytest.mark.parametrize('update_http_proxy_setting', ['no_http_proxy', 'auth_http_proxy', 'unauth_http_proxy'], indirect=True)
def test_positive_end_to_end(update_http_proxy_setting, restore_settings):
    """Assign http_proxy to Redhat repository and perform repository sync.

    :id: 38df5479-9127-49f3-a30e-26b33655971a

    :expectedresults: HTTP Proxy can be assigned to redhat repository and sync operation
        performed successfully.

    :Assignee: jpathan

    :BZ: 2011303, 2042473

    :CaseImportance: Critical
    """
    print('fsd')
