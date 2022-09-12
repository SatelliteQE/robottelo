import pytest

from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME


@pytest.fixture(scope='module')
def default_subscription(module_target_sat, module_org_with_manifest):
    subscription = module_target_sat.api.Subscription(
        organization=module_org_with_manifest.id
    ).search(query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'})
    assert len(subscription)
    return subscription[0]


@pytest.fixture(scope='module')
def module_subscribe_satellite(module_target_sat):
    """Subscribe Satellite to CDN"""
    module_target_sat.register_to_cdn()
    # Enable extras repo if os_version is RHEL7
    if module_target_sat.os_version.major < 8:
        module_target_sat.enable_repo(
            f'rhel-{module_target_sat.os_version.major}-server-extras-rpms', force=True
        )
    yield
    module_target_sat.unregister()


@pytest.fixture(scope='class')
def class_subscribe_satellite(class_target_sat):
    """Subscribe Satellite to CDN"""
    class_target_sat.register_to_cdn()
    # Enable extras repo if os_version is RHEL7
    if class_target_sat.os_version.major < 8:
        class_target_sat.enable_repo(
            f'rhel-{class_target_sat.os_version.major}-server-extras-rpms', force=True
        )
    yield class_target_sat
    class_target_sat.unregister()


@pytest.fixture
def subscribe_satellite(target_sat):
    """Subscribe Satellite to CDN"""
    target_sat.register_to_cdn()
    # Enable extras repo if os_version is RHEL7
    if target_sat.os_version.major < 8:
        target_sat.enable_repo(f'rhel-{target_sat.os_version.major}-server-extras-rpms', force=True)
    yield
    target_sat.unregister()
