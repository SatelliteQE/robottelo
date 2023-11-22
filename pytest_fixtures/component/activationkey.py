# Activation Key Fixtures
import pytest

from robottelo.cli.repository import Repository
from robottelo.utils.manifest import clone


@pytest.fixture(scope='module')
def module_activation_key(module_entitlement_manifest_org, module_target_sat):
    """Create activation key using default CV and library environment."""
    activation_key = module_target_sat.api.ActivationKey(
        auto_attach=True,
        content_view=module_entitlement_manifest_org.default_content_view.id,
        environment=module_entitlement_manifest_org.library.id,
        organization=module_entitlement_manifest_org,
    ).create()
    return activation_key


@pytest.fixture(scope='module')
def module_ak(module_lce, module_org, module_target_sat):
    ak = module_target_sat.api.ActivationKey(
        environment=module_lce,
        organization=module_org,
    ).create()
    return ak


@pytest.fixture(scope='module')
def module_ak_with_cv(module_lce, module_org, module_promoted_cv, module_target_sat):
    ak = module_target_sat.api.ActivationKey(
        content_view=module_promoted_cv,
        environment=module_lce,
        organization=module_org,
    ).create()
    return ak


@pytest.fixture(scope='module')
def module_ak_with_synced_repo(module_org, module_target_sat):
    """Prepare an activation key with synced repository for host registration"""
    with clone(name='golden_ticket') as manifest:
        module_target_sat.upload_manifest(module_org.id, manifest.content)
    new_product = module_target_sat.cli_factory.make_product({'organization-id': module_org.id})
    new_repo = module_target_sat.cli_factory.make_repository(
        {'product-id': new_product['id'], 'content-type': 'yum'}
    )
    Repository.synchronize({'id': new_repo['id']})
    ak = module_target_sat.cli_factory.make_activation_key(
        {
            'lifecycle-environment': 'Library',
            'content-view': 'Default Organization View',
            'organization-id': module_org.id,
            'auto-attach': False,
        }
    )
    return ak
