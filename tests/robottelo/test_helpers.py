"""Tests for module ``robottelo.helpers``."""
import os
from collections import defaultdict
from unittest import mock

import pytest

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


class FakeSSHResult(object):
    def __init__(self, stdout=None, return_code=None, stderr=None):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code


class TestGetServerVersion:
    """Tests for method ``get_server_version``."""

    @mock.patch('robottelo.helpers.ssh')
    def test_return_version(self, ssh):
        """get_server_version returns a proper version.

        When the version.rb file is present.
        """
        ssh.command = mock.MagicMock(return_value=FakeSSHResult(['"6.1.4"'], 0))
        assert get_server_version() == '6.1.4'

    @mock.patch('robottelo.helpers.ssh')
    def test_return_none(self, ssh):
        """get_server_version returns None.

        When the versions.rb file is not present.
        """
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([], 0))
        assert get_server_version() is None


class TestGetHostInfo:
    """Tests for method ``get_host_credentials``."""

    @mock.patch('robottelo.helpers.ssh')
    def test_fedora_info(self, ssh):
        ssh.command = mock.MagicMock(
            return_value=FakeSSHResult(['Fedora release 20 (Heisenbug)'], 0)
        )
        assert get_host_info() == ('Fedora', 20, None)

    @mock.patch('robottelo.helpers.ssh')
    def test_rhel_info(self, ssh):
        ssh.command = mock.MagicMock(
            return_value=FakeSSHResult(['Red Hat Enterprise Linux Server release 7.1 (Maipo)'], 0)
        )
        assert get_host_info() == ('Red Hat Enterprise Linux Server', 7, 1)

    @mock.patch('robottelo.helpers.ssh')
    def test_cat_fail(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([], 1, 'stderr'))
        with pytest.raises(HostInfoError) as context:
            get_host_info()
        assert context.match(r'.*Not able to cat /etc/redhat-release "stderr".*')

    @mock.patch('robottelo.helpers.ssh')
    def test_release_parse_fail(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([''], 0))
        with pytest.raises(HostInfoError) as context:
            get_host_info()
        assert context.match(r'.*Not able to parse release string "".*')


class TestEscapeSearch:
    def test_return_type(self):
        """Tests if escape search returns a unicode string"""
        assert isinstance(escape_search('search term'), str)

    def test_escapes_double_quotes(self):
        """Tests if escape search escapes double quotes"""
        assert escape_search('termwith"')[1:-1] == 'termwith\\"'

    def test_escapes_backslash(self):
        """Tests if escape search escapes backslashes"""
        assert escape_search('termwith\\')[1:-1] == 'termwith\\\\'

    def test_escapes_double_quotes_and_backslash(self):
        """Tests if escape search escapes backslashes"""
        assert escape_search('termwith"and\\')[1:-1] == 'termwith\\"and\\\\'

    def test_wraps_in_double_quotes(self):
        """Tests if escape search wraps the term in double quotes"""
        term = escape_search('term')
        assert term[0] == '"'
        assert term[-1] == '"'


class TestStorage:
    def test_dict_converted_to_storage(self):
        d = {'key': 'value'}
        storage = Storage(d)
        assert storage.key == 'value'

    def test_multiple_dicts_converted_to_storage(self):
        d = {'key': 'value'}
        e = {'another_key': 'another value'}
        storage = Storage(d, e, spare_argument='one more value')
        assert storage.key == 'value'
        assert storage.another_key == 'another value'
        assert storage.spare_argument == 'one more value'


class TestBugzillaIssueHandler:
    @pytest.fixture(scope='class', autouse=True)
    def set_env_version(self):
        """Set SAT_VERSION to avoid ssh calls"""
        os.environ['SAT_VERSION'] = '6.6'
        yield
        os.environ.pop('SAT_VERSION', None)

    def test_bz_is_open_pre_processed(self):
        """Assert a pre-processed BZ is considered open"""
        data = {"is_open": True}
        assert is_open("BZ:123456", data)

    def test_bz_is_not_open_pre_processed(self):
        """Assert a pre-processed BZ is considered not open"""
        data = {"is_open": False}
        assert not is_open("BZ:123456", data)

    def test_bz_is_deselected_pre_processed(self):
        """Assert a pre-processed BZ is considered deselected"""
        data = {"is_deselected": True}
        assert _should_deselect("BZ:123456", data)

    def test_bz_is_not_deselected_pre_processed(self):
        """Assert a pre-processed BZ is considered not deselected"""
        data = {"is_deselected": False}
        assert not _should_deselect("BZ:123456", data)

    @pytest.mark.parametrize('status', OPEN_STATUSES)
    def test_bz_is_open_by_status(self, status):
        """Assert status in NEW, ASSIGNED, POST, MODIFIED is open"""
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": status,
                "resolution": "",
                "target_milestone": "Unspecified",
                "flags": [],
            },
        )

    @pytest.mark.parametrize('resolution', WONTFIX_RESOLUTIONS)
    def test_bz_is_open_by_resolution(self, resolution):
        """Assert a closed BZ in WONTFIX resolution is considered open"""
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": resolution,
                "target_milestone": "Unspecified",
                "flags": [],
            },
        )

    def test_bz_is_open_if_server_version_is_lower(self):
        """Assert bug is considered open if TM is set for a future version
        and there are no clones backporting the solution to server version.
        """
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": "ERRATA",
                "target_milestone": "7.0.1",
                "flags": [],
                "clones": [],
            },
        )

    @pytest.mark.parametrize('status', CLOSED_STATUSES)
    def test_bz_is_not_open_if_server_version_is_higher_or_equal_tm(self, status):
        """Assert bug is considered not open if closed status and
        TM is higher or matches the running server version.
        """
        assert not is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": status,
                "resolution": "",
                "target_milestone": "6.6.1",
                "flags": [],
                "clones": [],
            },
        )

    def test_bz_is_open_if_server_version_is_lower_using_flags(self):
        """Assert bug is considered open if flag version is set for a future
        version and there are no clones backporting the solution.
        """
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": "ERRATA",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-7.0.1"}],
                "clones": [],
            },
        )

    @pytest.mark.parametrize('status', CLOSED_STATUSES)
    def test_bz_is_not_open_if_server_version_is_higher_or_equal_flags(self, status):
        """Assert bug is considered not open if closed status and
        min(flags) version is higher or matches the running server version.
        """
        assert not is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": status,
                "resolution": "",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.6.0"}],
                "clones": [],
            },
        )

    def test_bz_is_open_using_dupe_data_higher_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA but on a future version, no clones for
        backport the solution."""

        assert is_open(
            "BZ:123456",
            {
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
            },
        )

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
        assert not is_open("BZ:123456", data)

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
        assert is_open("BZ:123456", data)

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
        assert not is_open("BZ:123456", data)

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
        assert is_open("BZ:123456", data)

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
        assert not is_open("BZ:123456", data)

    @pytest.mark.parametrize('resolution', WONTFIX_RESOLUTIONS)
    def test_bz_should_deselect(self, resolution):
        """Ensure a BZ in resolution WONTFIX,CANTIFX,DEFERRED is deselected"""
        assert _should_deselect(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": resolution,
                "target_milestone": "Unspecified",
                "flags": [],
            },
        )

    @pytest.mark.parametrize('resolution', WONTFIX_RESOLUTIONS)
    def test_bz_should_deselect_if_dupe_is_wontfix(self, resolution):
        """Ensure a BZ in resolution WONTFIX,CANTIFX,DEFERRED is deselected"""
        assert _should_deselect(
            "BZ:123456",
            {
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
            },
        )

    def test_bz_should_not_deselect(self):
        """Ensure a BZ is not deselected if not in WONTFIX_RESOLUTIONS."""
        for status in OPEN_STATUSES:
            assert not _should_deselect(
                "BZ:123456",
                {
                    "id": 123456,
                    "status": status,
                    "resolution": "",
                    "target_milestone": "Unspecified",
                    "flags": [],
                },
            )

        for status in CLOSED_STATUSES:
            for resolution in ('ERRATA', 'CURRENT_RELEASE', 'WORKSFORME'):
                assert not _should_deselect(
                    "BZ:123456",
                    {
                        "id": 123456,
                        "status": status,
                        "resolution": resolution,
                        "target_milestone": "Unspecified",
                        "flags": [],
                    },
                )

    @pytest.mark.parametrize('issue', ["BZ123456", "XX:123456", "KK:89456", "123456", 999999])
    def test_invalid_handler(self, issue):
        """Assert is_open w/ invalid handlers raise AttributeError"""
        with pytest.raises(AttributeError):
            issue_deselect = _should_deselect(issue)
            is_open(issue)
        assert issue_deselect is None


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
