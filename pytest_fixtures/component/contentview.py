# Content View Fixtures
from nailgun.entity_mixins import call_entity_method_with_timeout
import pytest
from requests.exceptions import HTTPError

from robottelo.constants import DEFAULT_CV
from robottelo.logging import logger


@pytest.fixture(scope='module')
def module_cv(module_org, module_target_sat):
    cv = module_target_sat.api.ContentView(organization=module_org).create()
    yield cv
    try:
        cv = cv.read()
        for version in cv.version:
            version.delete()
        cv.delete()
    except HTTPError:
        logger.exception('Exception while deleting module scope content view in teardown')


@pytest.fixture(scope='module')
def module_published_cv(module_org, module_target_sat):
    cv = module_target_sat.api.ContentView(organization=module_org).create()
    cv.publish()
    cv = cv.read()
    yield cv
    try:
        cv = cv.read()
        for version in cv.version:
            version.delete()
        cv.delete()
    except HTTPError:
        logger.exception('Exception while deleting module scope published content view in teardown')


@pytest.fixture
def function_published_cv(function_org, target_sat):
    cv = target_sat.api.ContentView(organization=function_org).create()
    cv.publish()
    cv = cv.read()
    yield cv
    try:
        cv = cv.read()
        for version in cv.version:
            version.delete()
        cv.delete()
    except HTTPError:
        logger.exception(
            'Exception while deleting function scope published content view in teardown'
        )


@pytest.fixture(scope="module")
def module_promoted_cv(module_lce, module_published_cv, module_target_sat):
    """Promote published content view"""
    content_view_version = module_published_cv.version[0]
    content_view_version.promote(data={'environment_ids': module_lce.id})
    return module_published_cv


@pytest.fixture
def function_promoted_cv(function_lce, function_published_cv, target_sat):
    """Promote published content view"""
    content_view_version = function_published_cv.version[0]
    content_view_version.promote(data={'environment_ids': function_lce.id})
    return function_published_cv


@pytest.fixture(scope='module')
def module_rolling_cv(module_org, module_target_sat):
    return module_target_sat.api.ContentView(organization=module_org, rolling=True).create()


@pytest.fixture
def function_rolling_cv(function_org, target_sat):
    return target_sat.api.ContentView(organization=function_org, rolling=True).create()


@pytest.fixture(scope='module')
def module_default_org_view(module_org, module_target_sat):
    return module_target_sat.api.ContentView(organization=module_org, name=DEFAULT_CV).search()[0]


@pytest.fixture(scope='module')
def module_ak_cv_lce(module_org, module_lce, module_published_cv, module_target_sat):
    """Module Activation key with CV promoted to LCE"""
    content_view_version = module_published_cv.version[0]
    content_view_version.promote(data={'environment_ids': module_lce.id})
    module_published_cv = module_published_cv.read()
    cvenv_id = module_target_sat.api_factory.get_cvenv_id(module_published_cv, module_lce)
    return module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()


@pytest.fixture(scope='module')
def module_cv_repo(module_org, module_repository, module_lce, module_target_sat):
    """Create, Publish and promote CV with a repository"""
    content_view = module_target_sat.api.ContentView(organization=module_org).create()
    content_view.repository = [module_repository]
    content_view = content_view.update(['repository'])
    call_entity_method_with_timeout(content_view.publish, timeout=3600)
    content_view = content_view.read()
    content_view.version[0].promote(data={'environment_ids': module_lce.id, 'force': False})
    return content_view
