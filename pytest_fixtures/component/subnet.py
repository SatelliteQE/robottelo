# Subnet Fixtures
import pytest


@pytest.fixture(scope='module')
def module_default_subnet(module_target_sat, module_org, module_location):
    return module_target_sat.api.Subnet(
        location=[module_location], organization=[module_org]
    ).create()
