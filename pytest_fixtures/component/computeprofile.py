# Compute Profile Fixtures
import pytest


@pytest.fixture(scope='module')
def module_compute_profile(module_target_sat):
    return module_target_sat.api.ComputeProfile().create()
