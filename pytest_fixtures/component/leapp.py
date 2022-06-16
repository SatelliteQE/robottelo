# LEAPP Fixtures
import pytest


@pytest.fixture(scope="function")
def check_pre_upgrade(target_sat):
    target_sat.execute('yum update')
    target_sat.execute('reboot')
    target_sat.execute('yum install leapp-upgrade')


@pytest.fixture(scope="function")
def verify_post_upgrade_state(target_sat):
    os_version = target_sat.execute('cat /etc/redhat-release')
    kernel_version = target_sat.execute('uname -r')
    return os_version, kernel_version
