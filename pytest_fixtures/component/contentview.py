# Content View Fixtures
import pytest
from nailgun import entities

from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import promote
from robottelo.constants import DEFAULT_CV


@pytest.fixture(scope='module')
def module_cv(module_org):
    return entities.ContentView(organization=module_org).create()


@pytest.fixture(scope='module')
def module_published_cv(module_org):
    content_view = entities.ContentView(organization=module_org).create()
    content_view.publish()
    return content_view.read()


@pytest.fixture(scope="module")
def module_promoted_cv(module_lce, module_published_cv):
    """Promote published content view"""
    promote(module_published_cv.version[0], environment_id=module_lce.id)
    return module_published_cv


@pytest.fixture(scope='module')
def module_default_org_view(module_org):
    return entities.ContentView(organization=module_org, name=DEFAULT_CV).search()[0]


@pytest.fixture(scope='module')
def module_ak_cv_lce(module_org, module_lce, module_published_cv):
    """Module Activation key with CV promoted to LCE"""
    promote(module_published_cv.version[0], module_lce.id)
    module_published_cv = module_published_cv.read()
    module_ak_with_cv_lce = entities.ActivationKey(
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
    promote(content_view.version[0], module_lce.id)
    return content_view


@pytest.fixture
def set_importing_org(request):
    """
    Sets same CV, product and repository in importing organization as exporting organization
    """
    product_name, repo_name, cv_name, mos = request.param
    importing_org = entities.Organization().create()
    importing_prod = entities.Product(organization=importing_org, name=product_name).create()

    importing_repo = entities.Repository(
        name=repo_name,
        mirror_on_sync=mos,
        download_policy='immediate',
        product=importing_prod,
    ).create()

    importing_cv = entities.ContentView(name=cv_name, organization=importing_org).create()
    importing_cv.repository = [importing_repo]
    importing_cv.update(['repository'])
    yield [importing_cv, importing_org]
