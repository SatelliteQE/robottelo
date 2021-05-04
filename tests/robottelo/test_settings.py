"""Module for testing settings and settings hooks"""
import pytest
import xmltodict

from robottelo.config.base import SharedFunctionSettings


def test_share_timetout_validation():
    """Assert validation can run even with undefined (None) share_timeout"""
    shared_function_settings = SharedFunctionSettings()
    shared_function_settings.storage = 'file'
    shared_function_settings.storage = 'file'
    assert [] == shared_function_settings.validate()


dummy_test = '''import pytest

@pytest.mark.skip_if_not_set({skip_fields})
def test_dummy():
    """A dummy test used to test skip_if_not_set hook.
    Not to be run as a standalone test
    """
    pass
'''


class TestSkipIfNotSet:
    """Tests for :func:`pytest_plugins.settings_skip.skip_if_not_set`."""

    pytestmark = [
        pytest.mark.parametrize(
            'exec_test', ['-n2', '-n0'], ids=['xdist', 'non_xdist'], indirect=True
        )
    ]

    skipped_tests = [
        dummy_test.format(skip_fields=fields)
        for fields in ['"fake_manifest"', '"fake_manifest", "clients"']
    ]

    @pytest.mark.parametrize(
        'dummy_test', skipped_tests, ids=['single', 'multiple'], indirect=True
    )
    def test_skip_if_not_set(self, exec_test):
        """Skip a test method if configuration is missing."""
        with open(exec_test, 'rb') as f:
            junit = xmltodict.parse(f)  # NOQA
        testsuite = junit['testsuites']['testsuite']
        assert int(testsuite['@skipped']) == 1
        assert int(testsuite['@tests']) == 1

    error_test = dummy_test.format(skip_fields='"invalid_settings_field_does_not_exist"')

    @pytest.mark.parametrize('dummy_test', [error_test], ids=['invalid_feature'], indirect=True)
    def test_skip_if_not_set_invalid_feature(self, exec_test):
        """ValueError causes test error state when checking against `settings.all_features`"""
        with open(exec_test, 'rb') as f:
            junit = xmltodict.parse(f)  # NOQA
        testsuite = junit['testsuites']['testsuite']
        assert int(testsuite['@errors']) == 1
        assert int(testsuite['@tests']) == 1
        assert 'failed on setup with "ValueError:' in testsuite['testcase']['error']['@message']

    passing_test = dummy_test.format(skip_fields='"broker"')

    @pytest.mark.parametrize(
        'dummy_test', [passing_test], ids=['validating_feature'], indirect=True
    )
    def test_skip_if_not_set_no_skipping(self, exec_test):
        """ValueError causes test error state when checking against `settings.all_features`"""
        with open(exec_test, 'rb') as f:
            junit = xmltodict.parse(f)  # NOQA
        testsuite = junit['testsuites']['testsuite']
        assert int(testsuite['@errors']) == 0
        assert int(testsuite['@skipped']) == 0
        assert int(testsuite['@failures']) == 0
        assert int(testsuite['@tests']) == 1
