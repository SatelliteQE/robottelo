# Activation Key Fixtures
import pytest

from robottelo.cli.repository import Repository


@pytest.fixture(scope='module')
def module_activation_key(module_sca_manifest_org, module_target_sat):
    """Create activation key using default CV and library environment."""
    cvenv_id = module_target_sat.api_factory.get_cvenv_id(
        module_sca_manifest_org.default_content_view,
        module_sca_manifest_org.library,
    )
    return module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_sca_manifest_org,
    ).create()


@pytest.fixture
def function_activation_key(function_sca_manifest_org, target_sat):
    """Create activation key using default CV and library environment."""
    cvenv_id = target_sat.api_factory.get_cvenv_id(
        function_sca_manifest_org.default_content_view,
        function_sca_manifest_org.library,
    )
    return target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=function_sca_manifest_org,
    ).create()


@pytest.fixture(scope='module')
def module_ak(module_org, module_target_sat):
    return module_target_sat.api.ActivationKey(
        organization=module_org,
    ).create()


@pytest.fixture(scope='module')
def module_ak_with_cv(module_lce, module_org, module_promoted_cv, module_target_sat):
    cvenv_id = module_target_sat.api_factory.get_cvenv_id(module_promoted_cv, module_lce)
    return module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()


@pytest.fixture
def function_ak_with_cv(function_lce, function_org, function_promoted_cv, target_sat):
    cvenv_id = target_sat.api_factory.get_cvenv_id(function_promoted_cv, function_lce)
    return target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=function_org,
    ).create()


@pytest.fixture(scope='module')
def module_ak_with_cv_repo(module_lce, module_org, module_cv_repo, module_target_sat):
    cvenv_id = module_target_sat.api_factory.get_cvenv_id(module_cv_repo, module_lce)
    return module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()


@pytest.fixture(scope='module')
def module_ak_with_synced_repo(module_sca_manifest_org, module_target_sat):
    """Prepare an activation key with synced repository for host registration"""
    new_product = module_target_sat.cli_factory.make_product(
        {'organization-id': module_sca_manifest_org.id}
    )
    new_repo = module_target_sat.cli_factory.make_repository(
        {'product-id': new_product['id'], 'content-type': 'yum'}
    )
    Repository.synchronize({'id': new_repo['id']})
    return module_target_sat.cli_factory.make_activation_key(
        {
            'lifecycle-environment': 'Library',
            'content-view': 'Default Organization View',
            'organization-id': module_sca_manifest_org.id,
        }
    )


@pytest.fixture(scope='module')
def module_default_ak(module_target_sat, module_org):
    cvenv_id = module_target_sat.api_factory.get_cvenv_id(
        module_org.default_content_view,
        module_org.library,
    )
    return module_target_sat.api.ActivationKey(
        organization=module_org,
        content_view_environment_ids=[cvenv_id],
    ).create()
