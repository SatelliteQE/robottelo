# Compute Profile Fixtures
import pytest
from nailgun import entities


@pytest.fixture(scope='module')
def module_compute_profile():
    return entities.ComputeProfile().create()
