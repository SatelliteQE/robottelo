# Compute Profile Fixtures
from nailgun import entities
import pytest


@pytest.fixture(scope='module')
def module_compute_profile():
    return entities.ComputeProfile().create()
