# Content View Fixtures
from nailgun.entity_mixins import call_entity_method_with_timeout
import pytest

from robottelo.constants import DEFAULT_CV


@pytest.fixture(scope='module')
def module_cv(module_org, module_target_sat):
    return module_target_sat.api.ContentView(organization=module_org).create()


@pytest.fixture(scope='module')
def module_published_cv(module_org, module_target_sat):
    content_view = module_target_sat.api.ContentView(organization=module_org).create()
    content_view.publish()
    return content_view.read()


@pytest.fixture
def function_published_cv(function_org, target_sat):
    content_view = target_sat.api.ContentView(organization=function_org).create()
    content_view.publish()
    return content_view.read()


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
def module_default_org_view(module_org, module_target_sat):
    return module_target_sat.api.ContentView(organization=module_org, name=DEFAULT_CV).search()[0]


@pytest.fixture(scope='module')
def module_ak_cv_lce(module_org, module_lce, module_published_cv, module_target_sat):
    """Module Activation key with CV promoted to LCE"""
    content_view_version = module_published_cv.version[0]
    content_view_version.promote(data={'environment_ids': module_lce.id})
    module_published_cv = module_published_cv.read()
    return module_target_sat.api.ActivationKey(
        content_view=module_published_cv,
        environment=module_lce,
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


@pytest.fixture(scope='session')
def session_multicv_sat(session_satellite_host):
    """Satellite with multi-CV enabled"""
    session_satellite_host.enable_multicv_setting()
    session_satellite_host.update_setting('allow_multiple_content_views', 'True')
    return session_satellite_host


@pytest.fixture(scope='session')
def session_multicv_org(session_multicv_sat):
    return session_multicv_sat.api.Organization().create()


@pytest.fixture(scope='session')
def session_multicv_default_ak(session_multicv_sat, session_multicv_org):
    return session_multicv_sat.api.ActivationKey(
        organization=session_multicv_org,
        content_view=session_multicv_org.default_content_view.id,
        environment=session_multicv_org.library.id,
    ).create()


@pytest.fixture(scope='session')
def session_multicv_lce(session_multicv_sat, session_multicv_org):
    return session_multicv_sat.api.LifecycleEnvironment(
        organization=session_multicv_org,
    ).create()
