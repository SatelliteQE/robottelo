import os
from robottelo.decorators import get_sat_version


def test_get_sat_version_from_env_var():
    os.environ['BUGZILLA_SAT_VERSION'] = '42'
    assert get_sat_version() == '42'

    # this affects only this test scope
    del os.environ['BUGZILLA_SAT_VERSION']
