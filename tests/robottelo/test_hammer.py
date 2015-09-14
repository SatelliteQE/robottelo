# -*- encoding: utf-8 -*-
"""Tests for Robottelo's hammer helpers"""
import unittest2

from robottelo.cli import hammer


class ParseCSVTestCase(unittest2.TestCase):
    """Tests for parsing CSV hammer output"""
    def test_parse_csv(self):
        output_lines = [
            u'Header,Header 2',
            u'header value 1,header with spaces value',
            u'MixEd CaSe ValUe,ALL CAPS VALUE',
            u'"""double quote escaped value""","," escaped value',
            u'unicode,chårs',
        ]
        self.assertEqual(
            hammer.parse_csv(output_lines),
            [
                {
                    u'header': u'header value 1',
                    u'header-2': u'header with spaces value',
                },
                {
                    u'header': u'MixEd CaSe ValUe',
                    u'header-2': u'ALL CAPS VALUE',
                },
                {
                    u'header': u'"double quote escaped value"',
                    u'header-2': u', escaped value',
                },
                {
                    u'header': u'unicode',
                    u'header-2': u'chårs',
                },
            ]
        )


class ParseHelpTestCase(unittest2.TestCase):
    """Tests for parsing hammer help output"""
    def test_parse_help(self):
        """Can parse hammer help output"""
        self.maxDiff = None
        output = [
            'Usage:',
            '    hammer [OPTIONS] SUBCOMMAND [ARG] ...',
            '',
            'Parameters:',
            'SUBCOMMAND                    subcommand',
            '[ARG] ...                     subcommand arguments',
            '',
            'Subcommands:',
            ' activation-key                Manipulate activation keys.',
            ' capsule                       Manipulate capsule',
            ' compute-resource              Manipulate compute resources.',
            ' content-host                  Manipulate content hosts on the',
            '                               server',
            ' gpg                           Manipulate GPG Key actions on the',
            '                               server',

            'Options:',
            ' --autocomplete LINE           Get list of possible endings',
            ' --name, --deprecation-name    An option with a deprecation name',
            ' --csv                         Output as CSV (same as',
            '                               --output=csv)',
            ' --csv-separator SEPARATOR     Character to separate the values',
            ' --output ADAPTER              Set output format. One of [base,',
            '                               table, silent, csv, yaml, json]',
            ' -p, --password PASSWORD       password to access the remote',
            '                               system',
            ' -r, --reload-cache            force reload of Apipie cache',
        ]
        self.assertEqual(
            hammer.parse_help(output),
            {
                'subcommands': [
                    {
                        'name': 'activation-key',
                        'description': 'Manipulate activation keys.',
                    },
                    {
                        'name': 'capsule',
                        'description': 'Manipulate capsule',
                    },
                    {
                        'name': 'compute-resource',
                        'description': 'Manipulate compute resources.',
                    },
                    {
                        'name': 'content-host',
                        'description': (
                            'Manipulate content hosts on the server'
                        ),
                    },
                    {
                        'name': 'gpg',
                        'description': (
                            'Manipulate GPG Key actions on the server'
                        ),
                    },
                ],
                'options': [
                    {
                        'name': 'autocomplete',
                        'shortname': None,
                        'value': 'LINE',
                        'help': 'Get list of possible endings',
                    },
                    {
                        'name': 'name',
                        'shortname': None,
                        'value': None,
                        'help': 'An option with a deprecation name',
                    },
                    {
                        'name': 'csv',
                        'shortname': None,
                        'value': None,
                        'help': 'Output as CSV (same as --output=csv)',
                    },
                    {
                        'name': 'csv-separator',
                        'shortname': None,
                        'value': 'SEPARATOR',
                        'help': 'Character to separate the values',
                    },
                    {
                        'name': 'output',
                        'shortname': None,
                        'value': 'ADAPTER',
                        'help': (
                            'Set output format. One of [base, table, silent, '
                            'csv, yaml, json]'
                        ),
                    },
                    {
                        'name': 'password',
                        'shortname': 'p',
                        'value': 'PASSWORD',
                        'help': 'password to access the remote system',
                    },
                    {
                        'name': 'reload-cache',
                        'shortname': 'r',
                        'value': None,
                        'help': 'force reload of Apipie cache',
                    },
                ],
            }
        )


class ParseInfoTestCase(unittest2.TestCase):
    """Tests for parsing info hammer output"""
    def test_parse_simple(self):
        """Can parse a simple info output"""
        output = [
            'Id:                 19',
            'Full name:          4iv01o2u 10.5',
            'Release name:',
            '',
            'Family:',
            'Name:               4iv01o2u',
            'Major version:      10',
            'Minor version:      5',
        ]
        self.assertDictEqual(
            hammer.parse_info(output),
            {
                'id': '19',
                'full-name': '4iv01o2u 10.5',
                'release-name': {},
                'family': {},
                'name': '4iv01o2u',
                'major-version': '10',
                'minor-version': '5',
            }
        )

    def test_parse_numbered_list_attributes(self):
        """Can parse numbered list attributes"""
        output = [
            'Partition tables:',
            ' 1) ptable1',
            ' 2) ptable2',
            ' 3) ptable3',
            ' 4) ptable4',
        ]
        self.assertDictEqual(
            hammer.parse_info(output),
            {
                'partition-tables': [
                    'ptable1',
                    'ptable2',
                    'ptable3',
                    'ptable4',
                ],
            }
        )

    def test_parse_list_attributes(self):
        """Can parse list attributes"""
        output = [
            'Partition tables:',
            ' ptable1',
            ' ptable2',
            ' ptable3',
            ' ptable4',
        ]
        self.assertDictEqual(
            hammer.parse_info(output),
            {
                'partition-tables': [
                    'ptable1',
                    'ptable2',
                    'ptable3',
                    'ptable4',
                ],
            }
        )

    def test_parse_dict_attributes(self):
        """Can parse dict attributes"""
        output = [
            'Content:',
            ' 1) Repo Name: repo1',
            '    URL:       /custom/url1',
            ' 2) Repo Name: repo2',
            '    URL:       /custom/url2',
        ]
        self.assertDictEqual(
            hammer.parse_info(output),
            {
                'content': [
                    {
                        'repo-name': 'repo1',
                        'url': '/custom/url1',
                    },
                    {
                        'repo-name': 'repo2',
                        'url': '/custom/url2',
                    }
                ],
            }
        )

    def test_parse_info(self):
        """Can parse info output"""
        output = [
            'Sync State:   not_synced',
            'Sync Plan ID:',
            'GPG:',
            '    GPG Key ID: 1',
            '    GPG Key: key name',
            'Organizations:',
            '    1) Org 1',
            '    2) Org 2',
            'Locations:',
            '    Loc 1',
            '    Loc 2',
            'Repositories:',
            ' 1) Repo Name: repo1',
            '    Repo ID:   10',
            ' 2) Repo Name: repo2',
            '    Repo ID:   20',
        ]
        self.assertEqual(
            hammer.parse_info(output),
            {
                'sync-state': 'not_synced',
                'sync-plan-id': {},
                'gpg': {
                    'gpg-key-id': '1',
                    'gpg-key': 'key name'
                },
                'organizations': [
                    'Org 1',
                    'Org 2',
                ],
                'locations': [
                    'Loc 1',
                    'Loc 2',
                ],
                'repositories': [
                    {'repo-id': '10', 'repo-name': 'repo1'},
                    {'repo-id': '20', 'repo-name': 'repo2'},
                ],
            }
        )
