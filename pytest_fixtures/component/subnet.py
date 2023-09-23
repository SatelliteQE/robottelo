# Subnet Fixtures
from nailgun import entities
import pytest


@pytest.fixture(scope='module')
def module_default_subnet(module_org, module_location):
    return entities.Subnet(location=[module_location], organization=[module_org]).create()
