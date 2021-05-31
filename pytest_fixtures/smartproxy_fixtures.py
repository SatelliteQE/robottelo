import pytest
from nailgun import entities

from robottelo.config import settings


@pytest.fixture(scope='session')
def default_smart_proxy():
    smart_proxy = (
        entities.SmartProxy()
        .search(query={'search': f'name={settings.server.hostname}'})[0]
        .read()
    )
    return entities.SmartProxy(id=smart_proxy.id).read()


@pytest.fixture(scope='session')
def import_puppet_classes(default_smart_proxy):
    default_smart_proxy.import_puppetclasses(environment='production')
