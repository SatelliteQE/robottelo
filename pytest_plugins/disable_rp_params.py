import pytest


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Override Report Portal (RP) service objects attribute
    to prevent it from posting the parameter values of the tests.
    This is to make RP to correctly match and handle the test re-runs.

    We can remove this once we implement a compatible parametrization
    """
    if hasattr(config, 'py_test_service'):
        config.py_test_service.rp_supports_parameters = False
