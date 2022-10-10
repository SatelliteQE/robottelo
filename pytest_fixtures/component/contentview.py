# Content View Fixtures
import pytest
from nailgun.entity_mixins import call_entity_method_with_timeout

from robottelo.constants import DEFAULT_CV


@pytest.fixture(scope='module')
def module_cv(module_org, module_target_sat):
    return module_target_sat.api.ContentView(organization=module_org).create()


@pytest.fixture(scope='module')
def module_published_cv(module_org, module_target_sat):
    content_view = module_target_sat.api.ContentView(organization=module_org).create()
    content_view.publish()
    return content_view.read()


@pytest.fixture(scope="module")
def module_promoted_cv(module_lce, module_published_cv, module_target_sat):
    """Promote published content view"""
    content_view_version = module_published_cv.version[0]
    content_view_version.promote(data={'environment_ids': module_lce.id})
    return module_published_cv


@pytest.fixture(scope='module')
def module_default_org_view(module_org, module_target_sat):
    return module_target_sat.api.ContentView(organization=module_org, name=DEFAULT_CV).search()[0]


@pytest.fixture(scope='module')
def module_ak_cv_lce(module_org, module_lce, module_published_cv, module_target_sat):
    """Module Activation key with CV promoted to LCE"""
    content_view_version = module_published_cv.version[0]
    content_view_version.promote(data={'environment_ids': module_lce.id})
    module_published_cv = module_published_cv.read()
    module_ak_with_cv_lce = module_target_sat.api.ActivationKey(
        content_view=module_published_cv,
        environment=module_lce,
        organization=module_org,
    ).create()
    return module_ak_with_cv_lce


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


@pytest.fixture
def set_importing_org(request, module_target_sat):
    """
    Sets same CV, product and repository in importing organization as exporting organization
    """
    product_name, repo_name, cv_name, mos = request.param
    importing_org = module_target_sat.api.Organization().create()
    importing_prod = module_target_sat.api.Product(
        organization=importing_org, name=product_name
    ).create()

    importing_repo = module_target_sat.api.Repository(
        name=repo_name,
        mirror_on_sync=mos,
        download_policy='immediate',
        product=importing_prod,
    ).create()

    importing_cv = module_target_sat.api.ContentView(
        name=cv_name, organization=importing_org
    ).create()
    importing_cv.repository = [importing_repo]
    importing_cv.update(['repository'])
    yield [importing_cv, importing_org]
