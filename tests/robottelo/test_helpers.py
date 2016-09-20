"""Tests for module ``robottelo.helpers``."""
# (Too many public methods) pylint: disable=R0904
import six
import unittest2
from robottelo.helpers import (
    HostInfoError,
    escape_search,
    get_host_info,
    get_server_version,
    Storage
)

if six.PY2:
    import mock
else:
    from unittest import mock


class GetServerVersionTestCase(unittest2.TestCase):
    """Tests for method ``get_server_version``."""
    @mock.patch('robottelo.helpers.ssh')
    def test_return_version(self, ssh):
        """get_server_version returns a proper version.

        When the version.rb file is present.
        """
        ssh.command = mock.MagicMock(return_value=FakeSSHResult(
            ['"6.1.4"'],
            0
        ))
        self.assertEqual(get_server_version(), '6.1.4')

    @mock.patch('robottelo.helpers.ssh')
    def test_return_none(self, ssh):
        """get_server_version returns None.

        When the versions.rb file is not present.
        """
        ssh.command = mock.MagicMock(return_value=FakeSSHResult(
            [],
            0
        ))
        self.assertEqual(get_server_version(), None)


class GetHostInfoTestCase(unittest2.TestCase):
    """Tests for method ``get_host_credentials``."""

    @mock.patch('robottelo.helpers.ssh')
    def test_fedora_info(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult(
            ['Fedora release 20 (Heisenbug)'],
            0
        ))
        self.assertTupleEqual(get_host_info(), ('Fedora', 20, None))

    @mock.patch('robottelo.helpers.ssh')
    def test_rhel_info(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult(
            ['Red Hat Enterprise Linux Server release 7.1 (Maipo)'],
            0
        ))
        self.assertTupleEqual(
            get_host_info(),
            ('Red Hat Enterprise Linux Server', 7, 1)
        )

    @mock.patch('robottelo.helpers.ssh')
    def test_cat_fail(self, ssh):
        ssh.command = mock.MagicMock(
            return_value=FakeSSHResult([], 1, 'stderr'))
        with self.assertRaises(HostInfoError) as context:
            get_host_info()
        self.assertEqual(
            str(context.exception),
            'Not able to cat /etc/redhat-release "stderr"'
        )

    @mock.patch('robottelo.helpers.ssh')
    def test_release_parse_fail(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([''], 0))
        with self.assertRaises(HostInfoError) as context:
            get_host_info()
        if six.PY2:
            message = context.exception.message
        else:
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
        self.assertIsInstance(escape_search('search term'), six.text_type)

    def test_escapes_double_quotes(self):
        """Tests if escape search escapes double quotes"""
        self.assertEqual(escape_search('termwith"')[1:-1], 'termwith\\"')

    def test_escapes_backslash(self):
        """Tests if escape search escapes backslashes"""
        self.assertEqual(escape_search('termwith\\')[1:-1], 'termwith\\\\')

    def test_escapes_double_quotes_and_backslash(self):
        """Tests if escape search escapes backslashes"""
        self.assertEqual(escape_search('termwith"and\\')[1:-1],
                         'termwith\\"and\\\\')

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
