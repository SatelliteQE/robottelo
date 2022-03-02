import pytest


@pytest.fixture(scope='session')
def clean_rhsm(default_sat):
    """removes pre-existing candlepin certs and resets RHSM."""
    default_sat.remove_katello_ca()


@pytest.fixture(scope='module')
def subscribe_satellite(clean_rhsm, default_sat):
    """subscribe satellite to cdn"""
    from robottelo.config import settings

    if default_sat.os_version.major < 8:
        release_version = f'{default_sat.os_version.major}Server'
    else:
        release_version = f'{default_sat.os_version.major}'
    default_sat.register_contenthost(
        org=None,
        lce=None,
        username=settings.subscription.rhn_username,
        password=settings.subscription.rhn_password,
        releasever=release_version,
    )
    result = default_sat.subscription_manager_attach_pool([settings.subscription.rhn_poolid])[0]
    if 'Successfully attached a subscription' in result.stdout:
        default_sat.enable_repo(
            f'rhel-{default_sat.os_version.major}-server-extras-rpms', force=True
        )
        yield
    else:
        pytest.fail('Failed to attach system to pool. Aborting Test!.')
    default_sat.unregister()
    default_sat.remove_katello_ca()
