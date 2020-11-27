import pytest

from robottelo.rhsso_utils import run_command


@pytest.fixture
def foreman_service_teardown():
    """stop and restart of foreman service"""
    yield
    run_command('foreman-maintain service start --only=foreman')
