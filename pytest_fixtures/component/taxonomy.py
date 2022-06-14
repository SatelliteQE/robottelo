# Content Component fixtures
import pytest

from robottelo import manifests
from robottelo.api.utils import upload_manifest
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
def module_gt_manifest_org(module_target_sat):
    """Creates a new org and loads GT manifest in the new org"""
    org = module_target_sat.api.Organization().create()
    manifest = manifests.clone(org_environment_access=True, name='golden_ticket')
    manifests.upload_manifest_locked(org.id, manifest, interface=manifests.INTERFACE_CLI)
    org.manifest_filename = manifest.filename
    return org


@pytest.fixture(scope='module')
def smart_proxy_location(module_org, module_target_sat, default_smart_proxy):
    location = module_target_sat.api.Location(organization=[module_org]).create()
    default_smart_proxy.location.append(module_target_sat.api.Location(id=location.id))
    default_smart_proxy.update(['location'])
    return location
