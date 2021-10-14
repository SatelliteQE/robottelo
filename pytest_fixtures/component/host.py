# Host Specific Fixtures
import pytest
from nailgun import entities


@pytest.fixture(scope='module')
def module_host():
    return entities.Host().create()


@pytest.fixture(scope='module')
def module_model():
    return entities.Model().create()
