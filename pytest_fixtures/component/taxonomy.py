# Contenxt Component fixtures
import pytest
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG


@pytest.fixture(scope='session')
def default_org():
    return entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]


@pytest.fixture(scope='session')
def default_location():
    return entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0]


@pytest.fixture(scope='function')
def function_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='class')
def class_org():
    org = entities.Organization().create()
    yield org
    org.delete()


@pytest.fixture(scope='module')
def module_location(module_org):
    return entities.Location(organization=[module_org]).create()


@pytest.fixture(scope='class')
def class_location(class_org):
    loc = entities.Location(organization=[class_org]).create()
    yield loc
    loc.delete()


@pytest.fixture(scope='function')
def function_location():
    return entities.Location().create()


@pytest.fixture(scope='module')
def module_manifest_org():
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    return org


@pytest.fixture(scope='module')
def module_gt_manifest_org():
    """Creates a new org and loads GT manifest in the new org"""
    org = entities.Organization().create()
    manifest = manifests.clone(org_environment_access=True, name='golden_ticket')
    manifests.upload_manifest_locked(org.id, manifest, interface=manifests.INTERFACE_CLI)
    org.manifest_filename = manifest.filename
    return org


@pytest.fixture(scope='module')
def smart_proxy_location(module_org, module_target_sat):
    location = entities.Location(organization=[module_org]).create()
    smart_proxy = (
        entities.SmartProxy()
        .search(query={'search': f'name={module_target_sat.hostname}'})[0]
        .read()
    )
    smart_proxy.location.append(entities.Location(id=location.id))
    smart_proxy.update(['location'])
    return location
