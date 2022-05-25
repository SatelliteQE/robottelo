import pytest


@pytest.fixture(scope='session')
def clean_rhsm(session_target_sat):
    """removes pre-existing candlepin certs and resets RHSM."""
    session_target_sat.remove_katello_ca()


@pytest.fixture(scope='module')
def subscribe_satellite(clean_rhsm, module_target_sat):
    """subscribe satellite to cdn"""
    from robottelo.config import settings

    if module_target_sat.os_version.major < 8:
        release_version = f'{module_target_sat.os_version.major}Server'
    else:
        release_version = f'{module_target_sat.os_version.major}'
    module_target_sat.register_contenthost(
        org=None,
        lce=None,
        username=settings.subscription.rhn_username,
        password=settings.subscription.rhn_password,
        releasever=release_version,
    )
    result = module_target_sat.subscription_manager_attach_pool([settings.subscription.rhn_poolid])[
        0
    ]
    if 'Successfully attached a subscription' in result.stdout:
        module_target_sat.enable_repo(
            f'rhel-{module_target_sat.os_version.major}-server-extras-rpms', force=True
        )
        yield
    else:
        pytest.fail('Failed to attach system to pool. Aborting Test!.')
    module_target_sat.unregister()
    module_target_sat.remove_katello_ca()
