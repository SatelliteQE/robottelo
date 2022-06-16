import pytest

from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME


@pytest.fixture(scope='module')
def module_clean_rhsm(module_target_sat):
    """removes pre-existing candlepin certs and resets RHSM."""
    module_target_sat.remove_katello_ca()


@pytest.fixture
def func_clean_rhsm(target_sat):
    """removes pre-existing candlepin certs and resets RHSM."""
    target_sat.remove_katello_ca()


@pytest.fixture(scope='module')
def default_subscription(module_target_sat, module_org_with_manifest):
    subscription = module_target_sat.api.Subscription(
        organization=module_org_with_manifest.id
    ).search(query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'})
    assert len(subscription)
    return subscription[0]


def subscribe_satellite(sat):
    from robottelo.config import settings

    if sat.os_version.major < 8:
        release_version = f'{sat.os_version.major}Server'
    else:
        release_version = f'{sat.os_version.major}'
    sat.register_contenthost(
        org=None,
        lce=None,
        username=settings.subscription.rhn_username,
        password=settings.subscription.rhn_password,
        releasever=release_version,
    )
    result = sat.subscription_manager_attach_pool([settings.subscription.rhn_poolid])[0]
    if 'Successfully attached a subscription' in result.stdout:
        # extras is not in RHEL8: https://access.redhat.com/solutions/5331391
        if sat.os_version.major < 8:
            sat.enable_repo(f'rhel-{sat.os_version.major}-server-extras-rpms', force=True)
        yield
    else:
        pytest.fail('Failed to attach system to pool. Aborting Test!.')
    sat.unregister()
    sat.remove_katello_ca()


@pytest.fixture(scope='module')
def module_subscribe_satellite(module_clean_rhsm, module_target_sat):
    """subscribe satellite to cdn"""
    subscribe_satellite(module_target_sat)


@pytest.fixture
def func_subscribe_satellite(func_clean_rhsm, target_sat):
    """subscribe satellite to cdn"""
    subscribe_satellite(target_sat)
