# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI"""
from ddt import ddt
from fauxfactory import gen_string
from os.path import join
from robottelo.common import ssh
from robottelo.common.helpers import prepare_import_data
from robottelo.test import CLITestCase
from robottelo.cli.import_ import Import
from robottelo.cli.org import Org


@ddt
def csv_to_dataset(csv):
    """Converts the csv with header as a first entry to a python dict"""
    keys = csv[0].split(',')
    del csv[0]
    return [
        dict(zip(keys, val.split(',')))
        for val
        in csv
    ]


class TestImport(CLITestCase):
    """Import CLI tests.

    All default tests pass no options to the imprt object
    In such case methods download a default data set from URL
    specified in robottelo.properties.

    """
    def test_import_orgs_default(self):
        """@test: Import all organizations from the default data set
        (predefined source).

        @feature: Import Organizations

        @assert: 3 Organizations are created

        """
        files = prepare_import_data()[1]
        ssh_import = Import.organization({'csv-file': files['users']})
        ssh_cat = ssh.command('cat {0}'.format(files['users']))
        # pop the array as ssh.command appends 1 empty item at the end
        ssh_cat.stdout.pop()

        # now to check whether the orgs from csv appeared in sattelite
        orgs = set(org['name'] for org in Org.list().stdout)
        imporgs = set(
            org['organization'] for
            org in csv_to_dataset(ssh_cat.stdout)
        )

        self.assertEqual(ssh_import.return_code, 0)
        self.assertEqual(
            ssh_import.stdout,
            [
                u'Summary',
                u'  Created {0} organizations.'.format(len(imporgs)),
                u''
            ]
        )
        self.assertEqual(False in [org in orgs for org in imporgs], False)

    def test_import_users_default(self):
        """@test: Import all 3 users from the our default data set (predefined
        source).

        @feature: Import Users

        @assert: 3 Users created

        """
        tmpdir, files = prepare_import_data()
        pwdfile = join(tmpdir, gen_string('alpha', 6))

        ssh_import = Import.user({
            'csv-file': files['users'],
            'new-passwords': pwdfile
        })
        self.assertEqual(ssh_import.return_code, 0)
        self.assertEqual(
            ssh_import.stdout,
            [u'Summary', u'  Created 3 users.', u'']
        )

    def test_reimport_orgs_default(self):
        """@test: Try to Import all organizations from the
        predefined source and try to import them again

        @feature: Import Organizations twice

        @assert: 2nd Import will result in No Action Taken

        """
        files = prepare_import_data()[1]
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).return_code, 0)
        self.assertEqual(
            Import.organization({
                'csv-file': files['users']
            }).stdout, [u'Summary', u'  No action taken.', u'']
        )
