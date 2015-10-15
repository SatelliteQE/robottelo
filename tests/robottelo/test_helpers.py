"""Tests for module ``robottelo.helpers``."""
# (Too many public methods) pylint: disable=R0904
import mock
import unittest2

from robottelo.helpers import (
    HostInfoError,
    escape_search,
    generate_strings_list,
    get_host_info,
    invalid_names_list,
    invalid_values_list,
    InvalidArgumentError,
    valid_data_list,
    valid_names_list,
)


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
            context.exception.message,
            'Not able to cat /etc/redhat-release "stderr"'
        )

    @mock.patch('robottelo.helpers.ssh')
    def test_release_parse_fail(self, ssh):
        ssh.command = mock.MagicMock(return_value=FakeSSHResult([''], 0))
        with self.assertRaises(HostInfoError) as context:
            get_host_info()
        self.assertEqual(
            context.exception.message, 'Not able to parse release string ""')


class FakeSSHResult(object):
    def __init__(self, stdout=None, return_code=None, stderr=None):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code


class ValidNamesListTestCase(unittest2.TestCase):
    def test_return_type(self):
        """Tests if valid names list returns a unicode string"""
        for name in valid_names_list():
            self.assertIsInstance(name, unicode)


class ValidDataListTestCase(unittest2.TestCase):
    def test_return_type(self):
        """Tests if valid data list returns a unicode string"""
        for data in valid_data_list():
            self.assertIsInstance(data, unicode)


class InvalidNamesListTestCase(unittest2.TestCase):
    def test_return_type(self):
        """Tests if invalid names list returns a unicode string"""
        for name in invalid_names_list():
            self.assertIsInstance(name, unicode)


class InvalidValuesListTestCase(unittest2.TestCase):
    def test_return_type(self):
        """Tests if invalid values list returns right values based on input"""
        # Test valid values
        for value in 'api', 'cli', 'ui', None:
            return_value = invalid_values_list(value)
            self.assertIsInstance(return_value, list)
            if value == 'ui':
                self.assertEqual(len(return_value), 9)
            else:
                self.assertEqual(len(return_value), 10)
        # Test invalid values
        self.assertRaises(InvalidArgumentError, invalid_values_list, ' ')
        self.assertRaises(InvalidArgumentError, invalid_values_list, 'UI')
        self.assertRaises(InvalidArgumentError, invalid_values_list, 'CLI')
        self.assertRaises(InvalidArgumentError, invalid_values_list, 'API')
        self.assertRaises(InvalidArgumentError, invalid_values_list, 'invalid')


class GenerateStringListTestCase(unittest2.TestCase):
    def test_return_type(self):
        """Tests if generate string list returns a unicode string"""
        for string in generate_strings_list():
            self.assertIsInstance(string, unicode)


class EscapeSearchTestCase(unittest2.TestCase):
    def test_return_type(self):
        """Tests if escape search returns a unicode string"""
        self.assertIsInstance(escape_search('search term'), unicode)

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
