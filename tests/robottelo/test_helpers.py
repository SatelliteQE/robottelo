"""Tests for module ``robottelo.common.helpers``."""
# (Too many public methods) pylint: disable=R0904
import unittest
from robottelo.common import conf
from robottelo.common.helpers import (
    escape_search, generate_strings_list, get_server_url,
    get_server_credentials, info_dictionary, invalid_names_list,
    valid_data_list, valid_names_list,
)


class GetServerURLTestCase(unittest.TestCase):
    """Tests for method ``get_server_url``.

    The methods in this class test ``get_server_url`` by setting different
    values in the ``conf`` object and checking that output is as expected.
    There are many permutations of values that can be placed in the test cases,
    so method descriptions only briefly state of the ``conf`` object during
    that particular test.

    """
    def setUp(self):  # noqa pylint:disable=C0103
        """Back up and customize ``conf.properties``."""
        self.conf_properties = conf.properties.copy()
        conf.properties['main.server.hostname'] = 'example.com'
        if 'main.server.scheme' in conf.properties:
            del conf.properties['main.server.scheme']
        if 'main.server.port' in conf.properties:
            del conf.properties['main.server.port']

    def tearDown(self):  # noqa pylint:disable=C0103
        """Restore ``conf.properties``."""
        conf.properties = self.conf_properties

    def test_default_v1(self):
        """Hostname set."""
        self.assertEqual(get_server_url(), 'https://example.com')

    def test_default_v2(self):
        """Hostname set, port blank."""
        conf.properties['main.server.port'] = ''
        self.assertEqual(get_server_url(), 'https://example.com')

    def test_default_v3(self):
        """Hostname set, scheme blank."""
        conf.properties['main.server.scheme'] = ''
        self.assertEqual(get_server_url(), 'https://example.com')

    def test_default_v4(self):
        """Hostname set, scheme and port blank."""
        conf.properties['main.server.port'] = ''
        conf.properties['main.server.scheme'] = ''
        self.assertEqual(get_server_url(), 'https://example.com')

    def test_port(self):
        """Hostname and port set."""
        conf.properties['main.server.port'] = '1234'
        self.assertEqual(get_server_url(), 'https://example.com:1234')

    def test_port_v2(self):
        """Hostname and port set, scheme blank."""
        conf.properties['main.server.port'] = '1234'
        conf.properties['main.server.scheme'] = ''
        self.assertEqual(get_server_url(), 'https://example.com:1234')

    def test_scheme(self):
        """Hostname and scheme set."""
        conf.properties['main.server.scheme'] = 'telnet'
        self.assertEqual(get_server_url(), 'telnet://example.com')

    def test_scheme_v2(self):
        """Hostname and scheme set, port blank."""
        conf.properties['main.server.port'] = ''
        conf.properties['main.server.scheme'] = 'telnet'
        self.assertEqual(get_server_url(), 'telnet://example.com')

    def test_all(self):
        """Hostname, scheme and port set."""
        conf.properties['main.server.port'] = '1234'
        conf.properties['main.server.scheme'] = 'telnet'
        self.assertEqual(get_server_url(), 'telnet://example.com:1234')


class GetServerCredentialsTestCase(unittest.TestCase):
    """Tests for method ``get_server_credentials``."""
    def setUp(self):  # noqa pylint:disable=C0103
        """Back up and customize ``conf.properties``."""
        self.conf_properties = conf.properties.copy()
        conf.properties['foreman.admin.username'] = 'alice'
        conf.properties['foreman.admin.password'] = 'hackme'

    def tearDown(self):  # noqa pylint:disable=C0103
        """Restore ``conf.properties``."""
        conf.properties = self.conf_properties

    def test_default(self):
        """Run method under normal conditions."""
        self.assertEqual(get_server_credentials(), ('alice', 'hackme'))

    def test_missing_username(self):
        """Call method with no username set."""
        del conf.properties['foreman.admin.username']
        with self.assertRaises(KeyError):
            get_server_credentials()

    def test_missing_password(self):
        """Call method with no password set."""
        del conf.properties['foreman.admin.password']
        with self.assertRaises(KeyError):
            get_server_credentials()


class FakeSSHResult(object):
    def __init__(self, stdout=None):
        self.stdout = stdout


class ValidNamesListTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if valid names list returns a unicode string"""
        for name in valid_names_list():
            self.assertIsInstance(name, unicode)


class ValidDataListTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if valid data list returns a unicode string"""
        for data in valid_data_list():
            self.assertIsInstance(data, unicode)


class InvalidNamesListTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if invalid names list returns a unicode string"""
        for name in invalid_names_list():
            self.assertIsInstance(name, unicode)


class GenerateStringListTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if generate string list returns a unicode string"""
        for string in generate_strings_list():
            self.assertIsInstance(string, unicode)


class EscapeSearchTestCase(unittest.TestCase):
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


class InfoDictionaryTestCase(unittest.TestCase):
    def test_parse_simple(self):
        """Can parse a simple info output"""
        output = FakeSSHResult(stdout=[
            'Id:                 19',
            'Full name:          4iv01o2u 10.5',
            'Release name:',
            '',
            'Family:',
            'Name:               4iv01o2u',
            'Major version:      10',
            'Minor version:      5',
        ])

        result = info_dictionary(output)
        self.assertDictEqual(result.stdout, {
            'id': '19',
            'full-name': '4iv01o2u 10.5',
            'release-name': {},
            'family': {},
            'name': '4iv01o2u',
            'major-version': '10',
            'minor-version': '5',
        })

    def test_parse_numbered_list_attributes(self):
        """Can parse numbered list attributes"""
        output = FakeSSHResult(stdout=[
            'Partition tables:',
            ' 1) ptable1',
            ' 2) ptable2',
            ' 3) ptable3',
            ' 4) ptable4',
        ])

        result = info_dictionary(output)
        self.assertDictEqual(result.stdout, {
            'partition-tables': [
                'ptable1',
                'ptable2',
                'ptable3',
                'ptable4',
            ],
        })

    def test_parse_list_attributes(self):
        """Can parse list attributes"""
        output = FakeSSHResult(stdout=[
            'Partition tables:',
            ' ptable1',
            ' ptable2',
            ' ptable3',
            ' ptable4',
        ])

        result = info_dictionary(output)
        self.assertDictEqual(result.stdout, {
            'partition-tables': [
                'ptable1',
                'ptable2',
                'ptable3',
                'ptable4',
            ],
        })

    def test_parse_dict_attributes(self):
        """Can parse dict attributes"""
        output = FakeSSHResult(stdout=[
            'Content:',
            ' 1) Repo Name: repo1',
            '    URL:       /custom/url1',
            ' 2) Repo Name: repo2',
            '    URL:       /custom/url2',
        ])

        result = info_dictionary(output)
        self.assertDictEqual(result.stdout, {
            'content': [{
                'repo-name': 'repo1',
                'url': '/custom/url1',
            }, {
                'repo-name': 'repo2',
                'url': '/custom/url2',
            }],
        })
