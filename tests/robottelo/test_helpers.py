"""Tests for module ``robottelo.helpers``."""
import os
from collections import defaultdict
from unittest import mock

import unittest2

from robottelo.constants import CLOSED_STATUSES
from robottelo.constants import OPEN_STATUSES
from robottelo.constants import WONTFIX_RESOLUTIONS
from robottelo.helpers import _add_workaround
from robottelo.helpers import _should_deselect
from robottelo.helpers import escape_search
from robottelo.helpers import get_host_info
from robottelo.helpers import get_server_version
from robottelo.helpers import HostInfoError
from robottelo.helpers import is_open
from robottelo.helpers import slugify_component
from robottelo.helpers import Storage


class GetServerVersionTestCase(unittest2.TestCase):
    """Tests for method ``get_server_version``."""

    @mock.patch('robottelo.helpers.ssh')
    def test_return_version(self, ssh):
        """get_server_version returns a proper version.

        When the version.rb file is present.
        """
        ssh.command = mock.MagicMock(return_value=FakeSSHResult(['"6.1.4"'], 0))
        self.assertEqual(get_server_version(), '6.1.4')

    @mock.patch('robottelo.helpers.ssh')
    def test_return_none(self, ssh):
        """get_server_version returns None.

        When the versions.rb file is not present.
        """
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([], 0))
        self.assertEqual(get_server_version(), None)


class GetHostInfoTestCase(unittest2.TestCase):
    """Tests for method ``get_host_credentials``."""

    @mock.patch('robottelo.helpers.ssh')
    def test_fedora_info(self, ssh):
        ssh.command = mock.MagicMock(
            return_value=FakeSSHResult(['Fedora release 20 (Heisenbug)'], 0)
        )
        self.assertTupleEqual(get_host_info(), ('Fedora', 20, None))

    @mock.patch('robottelo.helpers.ssh')
    def test_rhel_info(self, ssh):
        ssh.command = mock.MagicMock(
            return_value=FakeSSHResult(['Red Hat Enterprise Linux Server release 7.1 (Maipo)'], 0)
        )
        self.assertTupleEqual(get_host_info(), ('Red Hat Enterprise Linux Server', 7, 1))

    @mock.patch('robottelo.helpers.ssh')
    def test_cat_fail(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([], 1, 'stderr'))
        with self.assertRaises(HostInfoError) as context:
            get_host_info()
        self.assertEqual(str(context.exception), 'Not able to cat /etc/redhat-release "stderr"')

    @mock.patch('robottelo.helpers.ssh')
    def test_release_parse_fail(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([''], 0))
        with self.assertRaises(HostInfoError) as context:
            get_host_info()
        message = str(context.exception)
        self.assertEqual(message, 'Not able to parse release string ""')


class FakeSSHResult(object):
    def __init__(self, stdout=None, return_code=None, stderr=None):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code


class EscapeSearchTestCase(unittest2.TestCase):
    def test_return_type(self):
        """Tests if escape search returns a unicode string"""
        self.assertIsInstance(escape_search('search term'), str)

    def test_escapes_double_quotes(self):
        """Tests if escape search escapes double quotes"""
        self.assertEqual(escape_search('termwith"')[1:-1], 'termwith\\"')

    def test_escapes_backslash(self):
        """Tests if escape search escapes backslashes"""
        self.assertEqual(escape_search('termwith\\')[1:-1], 'termwith\\\\')

    def test_escapes_double_quotes_and_backslash(self):
        """Tests if escape search escapes backslashes"""
        self.assertEqual(escape_search('termwith"and\\')[1:-1], 'termwith\\"and\\\\')

    def test_wraps_in_double_quotes(self):
        """Tests if escape search wraps the term in double quotes"""
        term = escape_search('term')
        self.assertEqual(term[0], '"')
        self.assertEqual(term[-1], '"')


class StorageTestCase(unittest2.TestCase):
    def test_dict_converted_to_storage(self):
        d = {'key': 'value'}
        storage = Storage(d)
        self.assertEqual(storage.key, 'value')

    def test_multiple_dicts_converted_to_storage(self):
        d = {'key': 'value'}
        e = {'another_key': 'another value'}
        storage = Storage(d, e, spare_argument='one more value')
        self.assertEqual(storage.key, 'value')
        self.assertEqual(storage.another_key, 'another value')
        self.assertEqual(storage.spare_argument, 'one more value')


class BugzillaIssueHandlerTestCase(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set SAT_VERSION to avoid ssh calls"""
        os.environ['SAT_VERSION'] = '6.6'

    @classmethod
    def tearDownClass(cls):
        """clean env vars"""
        os.environ.pop('SAT_VERSION', None)

    def test_bz_is_open_pre_processed(self):
        """Assert a pre-processed BZ is considered open"""
        data = {"is_open": True}
        self.assertTrue(is_open("BZ:123456", data))

    def test_bz_is_not_open_pre_processed(self):
        """Assert a pre-processed BZ is considered not open"""
        data = {"is_open": False}
        self.assertFalse(is_open("BZ:123456", data))

    def test_bz_is_deselected_pre_processed(self):
        """Assert a pre-processed BZ is considered deselected"""
        data = {"is_deselected": True}
        self.assertTrue(_should_deselect("BZ:123456", data))

    def test_bz_is_not_deselected_pre_processed(self):
        """Assert a pre-processed BZ is considered not deselected"""
        data = {"is_deselected": False}
        self.assertFalse(_should_deselect("BZ:123456", data))

    def test_bz_is_open_by_status(self):
        """Assert status in NEW, ASSIGNED, POST, MODIFIED is open"""
        for status in OPEN_STATUSES:
            with self.subTest(status=status):
                data = {
                    "id": 123456,
                    "status": status,
                    "resolution": "",
                    "target_milestone": "Unspecified",
                    "flags": [],
                }
                self.assertTrue(is_open("BZ:123456", data))

    def test_bz_is_open_by_resolution(self):
        """Assert a closed BZ in WONTFIX resolution is considered open"""
        for resolution in WONTFIX_RESOLUTIONS:
            with self.subTest(resolution=resolution):
                data = {
                    "id": 123456,
                    "status": "CLOSED",
                    "resolution": resolution,
                    "target_milestone": "Unspecified",
                    "flags": [],
                }
                self.assertTrue(is_open("BZ:123456", data))

    def test_bz_is_open_if_server_version_is_lower(self):
        """Assert bug is considered open if TM is set for a future version
        and there are no clones backporting the solution to server version.
        """
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "ERRATA",
            "target_milestone": "7.0.1",
            "flags": [],
            "clones": [],
        }
        self.assertTrue(is_open("BZ:123456", data))

    def test_bz_is_not_open_if_server_version_is_higher_or_equal_tm(self):
        """Assert bug is considered not open if closed status and
        TM is higher or matches the running server version.
        """
        for status in CLOSED_STATUSES:
            with self.subTest(status=status):
                data = {
                    "id": 123456,
                    "status": status,
                    "resolution": "",
                    "target_milestone": "6.6.1",
                    "flags": [],
                    "clones": [],
                }
                self.assertFalse(is_open("BZ:123456", data))

    def test_bz_is_open_if_server_version_is_lower_using_flags(self):
        """Assert bug is considered open if flag version is set for a future
        version and there are no clones backporting the solution.
        """
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "ERRATA",
            "target_milestone": "Unspecified",
            "flags": [{"status": "+", "name": "sat-7.0.1"}],
            "clones": [],
        }
        self.assertTrue(is_open("BZ:123456", data))

    def test_bz_is_not_open_if_server_version_is_higher_or_equal_flags(self):
        """Assert bug is considered not open if closed status and
        min(flags) version is higher or matches the running server version.
        """
        for status in CLOSED_STATUSES:
            with self.subTest(status=status):
                data = {
                    "id": 123456,
                    "status": status,
                    "resolution": "",
                    "target_milestone": "Unspecified",
                    "flags": [{"status": "+", "name": "sat-6.6.0"}],
                    "clones": [],
                }
                self.assertFalse(is_open("BZ:123456", data))

    def test_bz_is_open_using_dupe_data_higher_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA but on a future version, no clones for
        backport the solution."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "ERRATA",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.7.z"}],
            },
        }
        self.assertTrue(is_open("BZ:123456", data))

    def test_bz_is_not_open_using_dupe_data_lower_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA in a previous version."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "ERRATA",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.3.z"}],
            },
        }
        self.assertFalse(is_open("BZ:123456", data))

    def test_bz_is_open_using_dupe_of_dupe_data_higher_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA but on a future version, no clones for
        backport the solution."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.7.z"}],
                "dupe_data": {
                    "id": 888888,
                    "status": "CLOSED",
                    "resolution": "ERRATA",
                    "target_milestone": "Unspecified",
                    "flags": [{"status": "+", "name": "sat-6.7.z"}],
                },
            },
        }
        self.assertTrue(is_open("BZ:123456", data))

    def test_bz_is_not_open_using_dupe_of_dupe_data_lower_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA in a previous version."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.3.z"}],
                "dupe_data": {
                    "id": 888888,
                    "status": "CLOSED",
                    "resolution": "ERRATA",
                    "target_milestone": "Unspecified",
                    "flags": [{"status": "+", "name": "sat-6.3.z"}],
                },
            },
        }
        self.assertFalse(is_open("BZ:123456", data))

    def test_bz_is_open_using_dupe_of_dupe_data_by_status(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA but on a future version, no clones for
        backport the solution."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "dupe_data": {
                    "id": 888888,
                    "status": "NEW",
                    "resolution": "",
                    "target_milestone": "Unspecified",
                },
            },
        }
        self.assertTrue(is_open("BZ:123456", data))

    def test_bz_is_not_open_using_dupe_of_dupe_data_by_status(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA in a previous version."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "dupe_data": {
                    "id": 999999,
                    "status": "CLOSED",
                    "resolution": "ERRATA",
                    "target_milestone": "Unspecified",
                    "flags": [],
                },
            },
        }
        self.assertFalse(is_open("BZ:123456", data))

    def test_bz_should_deselect(self):
        """Ensure a BZ in resolution WONTFIX,CANTIFX,DEFERRED is deselected"""
        for resolution in WONTFIX_RESOLUTIONS:
            with self.subTest(resolution=resolution):
                data = {
                    "id": 123456,
                    "status": "CLOSED",
                    "resolution": resolution,
                    "target_milestone": "Unspecified",
                    "flags": [],
                }
                self.assertTrue(_should_deselect("BZ:123456", data))

    def test_bz_should_deselect_if_dupe_is_wontfix(self):
        """Ensure a BZ in resolution WONTFIX,CANTIFX,DEFERRED is deselected"""
        for resolution in WONTFIX_RESOLUTIONS:
            with self.subTest(resolution=resolution):
                data = {
                    "id": 123456,
                    "status": "CLOSED",
                    "resolution": 'DUPLICATE',
                    "target_milestone": "Unspecified",
                    "flags": [],
                    "dupe_data": {
                        "id": 999999,
                        "status": "CLOSED",
                        "resolution": resolution,
                        "target_milestone": "Unspecified",
                        "flags": [],
                    },
                }
                self.assertTrue(_should_deselect("BZ:123456", data))

    def test_bz_should_not_deselect(self):
        """Ensure a BZ is not deselected if not in WONTFIX_RESOLUTIONS."""
        for status in OPEN_STATUSES:
            with self.subTest(status=status):
                data = {
                    "id": 123456,
                    "status": status,
                    "resolution": "",
                    "target_milestone": "Unspecified",
                    "flags": [],
                }
                self.assertFalse(_should_deselect("BZ:123456", data))

        for status in CLOSED_STATUSES:
            for resolution in ('ERRATA', 'CURRENT_RELEASE', 'WORKSFORME'):
                with self.subTest(status=status, resolution=resolution):
                    data = {
                        "id": 123456,
                        "status": status,
                        "resolution": "",
                        "target_milestone": "Unspecified",
                        "flags": [],
                    }
                    self.assertFalse(_should_deselect("BZ:123456", data))

    def test_invalid_handler_for_is_open_raises_error(self):
        """Assert is_open w/ invalid handlers raise AttributeError"""

        for issue in ("BZ123456", "XX:123456", "KK:89456", "123456", 999999):
            with self.subTest(issue=issue):
                with self.assertRaises(AttributeError):
                    is_open(issue)

    def test_invalid_handler_for_should_deselect_returns_None(self):
        """Assert _should_deselect w/ invalid handlers returns None"""

        for issue in ("BZ123456", "XX:123456", "KK:89456", "123456", 999999):
            with self.subTest(issue=issue):
                self.assertIsNone(_should_deselect(issue))


def test_slugify_component():
    """Assert slugify_component returns proper values"""
    assert slugify_component('ContentViews') == 'contentviews'
    assert slugify_component('File-Management') == 'file-management'
    assert slugify_component('File-Management', False) == 'file_management'
    assert slugify_component('File&Management') == 'filemanagement'
    assert slugify_component('File and Management') == 'filemanagement'


def test_add_workaround():
    """Assert helper function adds corrent items to given data"""
    data = defaultdict(lambda: {"data": {}, "used_in": []})
    matches = [('BZ', '123456'), ('BZ', '789456')]

    _add_workaround(data, matches, 'test', foo='bar')

    _add_workaround(
        data, matches, 'test', validation=lambda *a, **k: False, zaz='traz'  # Should not be added
    )

    for match in matches:
        issue = f"{match[0]}:{match[1]}"
        used_in = data[issue.strip()]['used_in']
        assert {'usage': 'test', 'foo': 'bar'} in used_in
        assert {'usage': 'test', 'zaz': 'traz'} not in used_in
