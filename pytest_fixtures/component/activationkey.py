# Activation Key Fixtures
import pytest
from nailgun import entities


@pytest.fixture(scope='module')
def module_activation_key(module_org):
    return entities.ActivationKey(organization=module_org).create()


@pytest.fixture(scope='module')
def module_ak(module_lce, module_org):
    ak = entities.ActivationKey(
        environment=module_lce,
        organization=module_org,
    ).create()
    return ak


@pytest.fixture(scope='module')
def module_ak_with_cv(module_lce, module_org, module_promoted_cv):
    ak = entities.ActivationKey(
        content_view=module_promoted_cv,
        environment=module_lce,
        organization=module_org,
    ).create()
    return ak
