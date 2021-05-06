"""Module for testing settings and settings hooks"""
from robottelo.config.base import SharedFunctionSettings


def test_share_timetout_validation():
    """Assert validation can run even with undefined (None) share_timeout"""
    shared_function_settings = SharedFunctionSettings()
    shared_function_settings.storage = 'file'
    shared_function_settings.storage = 'file'
    assert [] == shared_function_settings.validate()
