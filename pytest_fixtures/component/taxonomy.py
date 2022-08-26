# Content Component fixtures
import pytest
from manifester import Manifester

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG


@pytest.fixture(scope='session')
def default_org(session_target_sat):
    return session_target_sat.api.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[
        0
    ]


@pytest.fixture(scope='session')
def default_location(session_target_sat):
    return session_target_sat.api.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0]


@pytest.fixture
def function_org(target_sat):
    return target_sat.api.Organization().create()


@pytest.fixture(scope='module')
def module_org(module_target_sat):
    return module_target_sat.api.Organization().create()


@pytest.fixture(scope='class')
def class_org(class_target_sat):
    org = class_target_sat.api.Organization().create()
    yield org
    org.delete()


@pytest.fixture(scope='module')
def module_location(module_target_sat, module_org):
    return module_target_sat.api.Location(organization=[module_org]).create()


@pytest.fixture(scope='class')
def class_location(class_target_sat, class_org):
    loc = class_target_sat.api.Location(organization=[class_org]).create()
    yield loc
    loc.delete()


@pytest.fixture
def function_location(target_sat):
    return target_sat.api.Location().create()


@pytest.fixture
def function_location_with_org(target_sat, function_org):
    return target_sat.api.Location(organization=[function_org]).create()


@pytest.fixture(scope='module')
def module_manifest_org(module_target_sat):
    org = module_target_sat.api.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    return org


@pytest.fixture(scope='module')
def module_org_with_manifest(module_org):
    """Upload manifest to organization."""
    with manifests.clone() as manifest:
        upload_manifest(module_org.id, manifest.content)
    return module_org


@pytest.fixture(scope='module')
def module_gt_manifest_org(module_target_sat):
    """Creates a new org and loads GT manifest in the new org"""
    org = module_target_sat.api.Organization().create()
    manifest = manifests.clone(org_environment_access=True, name='golden_ticket')
    manifests.upload_manifest_locked(org.id, manifest, interface='CLI')
    org.manifest_filename = manifest.filename
    return org


# Note: Manifester should not be used with the Satellite QE RHSM account until
# subscription needs are scoped and sufficient subscriptions added to the
# Satellite QE RHSM account. Manifester can be safely used locally with personal
# or stage RHSM accounts.


@pytest.fixture(scope='session')
def session_entitlement_manifest():
    """Yields a manifest in entitlement mode with subscriptions determined by the
    `manifest_category.robottelo_automation` setting in manifester_settings.yaml."""
    with Manifester(manifest_category=settings.manifest.entitlement) as manifest:
        yield manifest


@pytest.fixture(scope='session')
def session_sca_manifest():
    """Yields a manifest in Simple Content Access mode with subscriptions determined by the
    `manifest_category.golden_ticket` setting in manifester_settings.yaml."""
    with Manifester(manifest_category=settings.manifest.golden_ticket) as manifest:
        yield manifest


@pytest.fixture(scope='module')
def smart_proxy_location(module_org, module_target_sat, default_smart_proxy):
    location = module_target_sat.api.Location(organization=[module_org]).create()
    default_smart_proxy.location.append(module_target_sat.api.Location(id=location.id))
    default_smart_proxy.update(['location'])
    return location
