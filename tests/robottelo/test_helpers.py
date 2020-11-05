"""Tests for module ``robottelo.helpers``."""
from unittest import mock

import pytest

from robottelo.helpers import escape_search
from robottelo.helpers import get_available_capsule_port
from robottelo.helpers import get_host_info
from robottelo.helpers import get_server_version
from robottelo.helpers import HostInfoError
from robottelo.helpers import slugify_component
from robottelo.helpers import Storage


class FakeSSHResult:
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
        with pytest.raises(
            HostInfoError, match=r'.*Not able to cat /etc/redhat-release "stderr".*'
        ):
            get_host_info()

    @mock.patch('robottelo.helpers.ssh')
    def test_release_parse_fail(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([''], 0))
        with pytest.raises(HostInfoError, match=r'.*Not able to parse release string "".*'):
            get_host_info()


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


def test_slugify_component():
    """Assert slugify_component returns proper values"""
    assert slugify_component('ContentViews') == 'contentviews'
    assert slugify_component('File-Management') == 'file-management'
    assert slugify_component('File-Management', False) == 'file_management'
    assert slugify_component('File&Management') == 'filemanagement'
    assert slugify_component('File and Management') == 'filemanagement'


class TestGetAvailableCapsulePort:
    """Tests for method ``get_available_capsule_port``."""

    @mock.patch('robottelo.helpers.ssh')
    def test_return_port(self, ssh):
        """get_available_capsule_port returns a port number."""
        ssh.command = mock.MagicMock(return_value=FakeSSHResult(['""'], 0))
        port = get_available_capsule_port()
        assert port, "No available capsule port found."
