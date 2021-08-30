import pytest

from robottelo.config import settings
from robottelo.rhsso_utils import run_command


def unsubscribe():
    """unregisters a machine from cdn"""
    run_command('subscription-manager unregister')
    run_command('subscription-manager clean')


@pytest.fixture(scope='session')
def clean_rhsm():
    """removes pre-existing candlepin certs and resets RHSM."""
    # removing the katello-ca-consumer
    run_command('rpm -qa | grep katello-ca-consumer | xargs -r rpm -e')


@pytest.fixture(scope='session')
def subscribe_satellite(clean_rhsm, default_sat):
    """subscribe satellite to cdn"""
    run_command(
        'subscription-manager register --force --user={} --password={} {}'.format(
            settings.subscription.rhn_username,
            settings.subscription.rhn_password,
            # set release to "7Server" currently with this scope
            f'--release="{default_sat.os_version.major}Server"',
        )
    )
    has_success_msg = 'Successfully attached a subscription'
    attach_cmd = f'subscription-manager attach --pool={settings.subscription.rhn_poolid}'
    result = run_command(attach_cmd)
    if has_success_msg in result:
        run_command(
            f'subscription-manager repos --enable \
                    "rhel-{default_sat.os_version.major}-server-extras-rpms"'
        )
        yield
    else:
        pytest.fail("Failed to attach system to pool. Aborting Test!.")
    unsubscribe()
