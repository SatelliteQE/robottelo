"""Tests for :mod:`tests.foreman` and its sub-modules."""
from mock import patch
from tests.foreman.api.test_contentview import _check_bz_1186432
from unittest import SkipTest, TestCase


class CheckBz1186432TestCase(TestCase):
    """Tests for function ``_check_bz_1186432``.

    Function is in :mod:`tests.foreman.api.test_contentview`.

    """
    def test_ok(self):
        """Assert that ``_check_bz_1186432`` identifies OK strings.

        ``None`` should be returned when all of the strings passed in are OK.

        """
        error_lists = (
            [
                'RF12-4115 [ProxyAPI::ProxyException]'  # no first letter
                '[RestClient::NotAcceptable]: 406 Not Acceptable',
                'ERF12-4115 [ProxyAPI::ProxyException]'  # no last letter
                '[RestClient::NotAcceptable]: 406 Not Acceptabl',
                'ERF12-4115 [ProxyAPI::ProxyException'  # missing bracket
                '[RestClient::NotAcceptable]: 406 Not Acceptable',
                'foo',  # utterly bogus
            ],
            [],  # no errors at all
        )
        with patch(
                'tests.foreman.api.test_contentview.bz_bug_is_open',
                return_value=True
        ):
            for error_list in error_lists:
                self.assertIsNone(_check_bz_1186432(error_list))

    def test_suspicious(self):
        """Assert that ``_check_bz_1186432`` identifies suspicious strings.

        ``SkipTest`` should be raised when at least one of the strings passed
        in is suspicious.

        """
        error_lists = (
            [  # minimum necessary to make method raise exception
                'ERF12-4115 [ProxyAPI::ProxyException]'
                '[RestClient::NotAcceptable]: 406 Not Acceptable'
            ],
            [  # a more realistic error message
                'ERF12-4115 [ProxyAPI::ProxyException]: Unable to get classes '
                'from Puppet for example_env ([RestClient::NotAcceptable]: '
                '406 Not Acceptable) for proxy https://<snip>:9090/puppet'
            ],
            [
                'This string will not trigger an exception. The next will.',
                'ERF12-4115 [ProxyAPI::ProxyException]'
                '[RestClient::NotAcceptable]: 406 Not Acceptable'
            ],
            [
                'ERF12-4115 [ProxyAPI::ProxyException]'
                '[RestClient::NotAcceptable]: 406 Not Acceptable',
                'This string will not trigger an exception. The prev will.',
            ],
        )
        with patch(
                'tests.foreman.api.test_contentview.bz_bug_is_open',
                return_value=True
        ):
            for error_list in error_lists:
                with self.assertRaises(SkipTest):
                    _check_bz_1186432(error_list)
