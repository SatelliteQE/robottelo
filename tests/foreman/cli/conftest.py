import pytest

from robottelo.cli.factory import make_domain


@pytest.fixture(scope="module")
def module_domain():
    """Create shared domain"""
    return make_domain()
