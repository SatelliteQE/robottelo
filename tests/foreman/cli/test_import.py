# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI"""
import csv
import os
import random
import tempfile
from ddt import ddt
from fauxfactory import gen_string
from itertools import product
from robottelo.common import manifests, ssh
from robottelo.common.decorators import (
    data,
    bz_bug_is_open,
    skip_if_bug_open,
)
from robottelo.common.helpers import prepare_import_data
from robottelo.cli.import_ import Import
from robottelo.cli.factory import make_org
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.org import Org
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.test import CLITestCase


def csv_to_dataset(csv_files):
    """Process and return remote CSV files.

    Read the remote CSV files, and return a list of dictionaries for them

    :param csv_files: A list of strings, where each string is a path to a CSV
        file on the remote server.

    :returns: A list of dicta, where each dict holds the contents of one CSV
        file.

    """
    result = []
    for csv_file in csv_files:
        ssh_cat = ssh.command(u'cat {0}'.format(csv_file))
        if ssh_cat.return_code != 0:
            raise AssertionError(ssh_cat.stderr)
        csv = ssh_cat.stdout[:-1]
        keys = csv[0].split(',')
        result.extend([
            dict(zip(keys, val.split(',')))
            for val
            in csv[1:]
        ])
    return result


def build_csv_file(rows=None, dirname=None):
    """Generate a csv file, feed it by the provided data
    (a list of dictionary objects) and return a path to it

    """
    if rows is None:
        rows = [{}]
    file_name = tempfile.mkstemp()[1]
    with open(file_name, 'wb') as csv_file:
        csv_writer = csv.DictWriter(
            csv_file, fieldnames=rows[0].keys(), lineterminator='\n'
        )
        csv_writer.writeheader()
        for row in rows:
            csv_writer.writerow(row)
    if dirname is None:
        remote_file = file_name
    else:
        remote_file = os.path.join(dirname, os.path.basename(file_name))
    ssh.upload_file(file_name, remote_file)
    os.remove(file_name)
    return remote_file


def update_csv_values(csv_file, new_data=None, dirname=None):
    """Build CSV with updated key values provided as an argument
    in order to randomize the dataset with keeping the organization_id
    mappings

    :param csv_file: A string. The path to a CSV file that resides
        on a remote server.
    :param new_data: A list of dictionary objects. Each object has to
        contain an key_id key corresponding to org[anization]_id of the
        record being updated and the key-value pairs of attributes to be
        replaced by the particular records. For example::

            [
                {
                    u'key_id': u'1',
                    u'organization': u'updated_organization_name_1',
                    u'username': u'updated_user_name_1',
                },
                {
                    u'key_id': u'2',
                    u'organization': u'updated_organization_name_2',
                    u'username': u'updated_user_name_2',
                }
            ]

    :returns: A string. The path to a remotely created CSV file

    """
    updated = False
    # if new_data is not specified, no change happens
    if new_data is None:
        return csv_file
    result = csv_to_dataset([csv_file])
    for change in new_data:
        for record in result:
            if (record.get('organization_id') == change['key_id'] or
                    record.get('org_id') == change['key_id']):
                record.update(change)
                del record['key_id']
                if record.get('org_id'):
                    record['org_id'] = record.pop('organization_id')
                updated = True
    if updated:
        return build_csv_file(result, dirname)
    else:
        return csv_file


def import_org_data():
    """Random data for Organization Import tests"""

    random_ids = random.sample(range(1, 1000), 3)
    return ([
        {
            u'key_id': u'{}'.format(str(i+1)),
            u'organization_id': u'{}'.format(str(random_ids[i])),
            u'organization': gen_string('alphanumeric')
        }
        for i in range(3)
    ],)


def import_user_data():
    """Random data for User Import tests"""

    random_ids = random.sample(range(1, 1000), 3)
    return ([
        {
            u'key_id': u'{}'.format(str(i+1)),
            u'organization_id': u'{}'.format(str(random_ids[i])),
            u'organization': gen_string('alphanumeric'),
            u'username': gen_string('alphanumeric')
        }
        for i in range(3)
    ],)


@ddt
class TestImport(CLITestCase):
    """Import CLI tests.

    All default tests pass no options to the imprt object
    In such case methods download a default data set from URL
    specified in robottelo.properties.

    """
    @classmethod
    def setUpClass(cls):
        super(TestImport, cls).setUpClass()
        # prepare the default dataset
        cls.default_dataset = prepare_import_data()

    @classmethod
    def tearDownClass(cls):
        super(TestImport, cls).tearDownClass()
        ssh.command(u'rm -r {}'.format(cls.default_dataset[0]))

    def tearDown(self):
        # remove the dataset
        ssh.command(
            u'rm -rf ${HOME}/.transition_data ${HOME}/puppet_work_dir'
        )

    @data(*import_org_data())
    def test_import_orgs_default(self, test_data):
        """@test: Import all organizations from the default data set
        (predefined source).

        @feature: Import Organizations

        @assert: 3 Organizations are created

        """
        files = dict(self.default_dataset[1])
        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        ssh_import = Import.organization({'csv-file': files['users']})
        # now to check whether the orgs from csv appeared in satellite
        orgs = set(org['name'] for org in Org.list().stdout)
        imp_orgs = set(
            org['organization'] for
            org in csv_to_dataset([files['users']])
        )
        self.assertEqual(ssh_import.return_code, 0)
        self.assertTrue(imp_orgs.issubset(orgs))

    @data(*import_org_data())
    def test_import_orgs_manifests(self, test_data):
        """@test: Import all organizations from the default data set
        (predefined source) and upload manifests for each of them

        @feature: Import Organizations including Manifests

        @assert: 3 Organizations are created with 3 manifests uploaded

        """
        files = dict(self.default_dataset[1])
        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        csv_records = csv_to_dataset([files['users']])
        # create number of manifests corresponding to the number of orgs
        manifest_list = []
        man_dir = ssh.command(
            u'mktemp -d -p {}'.format(self.default_dataset[0])
        ).stdout[0]
        for org in set([rec['organization'] for rec in csv_records]):
            for char in [' ', '.', '#']:
                org = org.replace(char, '_')
            man_file = manifests.clone()
            ssh.upload_file(man_file, u'{0}/{1}.zip'.format(man_dir, org))
            manifest_list.append(u'{0}/{1}.zip'.format(man_dir, org))
            os.remove(man_file)
        ssh_import = Import.organization({
            'csv-file': files['users'],
            'upload-manifests-from': man_dir,
        })
        # now to check whether the orgs from csv appeared in satellite
        orgs = set(org['name'] for org in Org.list().stdout)
        imp_orgs = set(
            org['organization'] for
            org in csv_to_dataset([files['users']])
        )
        self.assertEqual(ssh_import.return_code, 0)
        self.assertTrue(imp_orgs.issubset(orgs))
        for org in imp_orgs:
            manifest_history = Subscription.manifest_history(
                {'organization': org}
            ).stdout[3]
            self.assertIn('SUCCESS', manifest_history)

    @data(*import_org_data())
    def test_reimport_orgs_default_negative(self, test_data):
        """@test: Try to Import all organizations from the
        predefined source and try to import them again

        @feature: Import Organizations twice

        @assert: 2nd Import will result in No Action Taken

        """
        files = dict(self.default_dataset[1])
        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).return_code, 0)
        orgs_before = Org.list().stdout
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).return_code, 0)
        self.assertEqual(orgs_before, Org.list().stdout)

    @data(*import_org_data())
    def test_import_orgs_recovery(self, test_data):
        """@test: Try to Import organizations with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @feature: Import Organizations Recover

        @assert: 2nd Import will rename the new organizations, 2nd import will
        map them and the 3rd one will result in No Action Taken

        """
        # prepare the data
        files = dict(self.default_dataset[1])
        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        # initial import
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).return_code, 0)
        # clear the .transition_data to clear the transition mapping
        ssh.command('rm -rf ${HOME}/.transition_data')

        # use the default (rename) strategy
        Import.organization({'csv-file': files['users']})
        transition_data = csv_to_dataset(
            ssh.command(u'ls ${HOME}/.transition_data/org*').stdout[:-1]
        )
        self.assertEqual(len(transition_data), len(test_data))
        for record in transition_data:
            self.assertEqual(Org.info({'id': record['sat6']}).return_code, 0)
        Import.organization({'csv-file': files['users'], 'delete': True})
        ssh.command('rm -rf ${HOME}/.transition_data/org*')

        # use the 'none' strategy
        orgs_before = Org.list().stdout
        Import.organization({'csv-file': files['users'], 'recover': 'none'})
        self.assertEqual(orgs_before, Org.list().stdout)
        Import.organization({'csv-file': files['users'], 'delete': True})
        ssh.command('rm -rf ${HOME}/.transition_data/org*')

        # use the 'map' strategy
        Import.organization({
            'csv-file': files['users'],
            'recover': 'map',
        })
        transition_data = csv_to_dataset(
            ssh.command(u'ls ${HOME}/.transition_data/org*').stdout[:-1]
        )
        for record in transition_data:
            self.assertEqual(
                Org.info({'id': record['sat6']}).return_code, 0
            )
        Import.organization({'csv-file': files['users'], 'delete': True})

    @data(*import_user_data())
    def test_merge_orgs(self, test_data):
        """@test: Try to Import all organizations and their users from CSV
        to a mapped organizaition.

        @feature: Import User Mapped Org

        @assert: 3 Organizations Mapped and their Users created
        in a single Organization

        """
        # create a new Organization and prepare CSV files
        new_org = make_org()
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))
        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        self.assertEqual(
            Import.organization({
                'csv-file': files['users'],
                'into-org-id': new_org['id'],
                'verbose': True,
            }).return_code,
            0
        )
        Import.user({'csv-file': files['users'], 'new-passwords': pwdfile})

        # list users by org-id and check whether users from csv are in listing
        users = User.list({u'organization-id': new_org['id']})
        logins = set(user['login'] for user in users.stdout)
        imp_users = set(
            user['username']
            for user in csv_to_dataset([files['users']])
        )
        self.assertTrue(all((user in logins for user in imp_users)))

    @data(*import_user_data())
    def test_import_users_default(self, test_data):
        """@test: Import all 3 users from the default data set (predefined
        source).

        @feature: Import Users

        @assert: 3 Users created

        """
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))

        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        Import.organization({'csv-file': files['users']})
        ssh_import = Import.user({
            'csv-file': files['users'],
            'new-passwords': pwdfile
        })
        self.assertEqual(ssh_import.return_code, 0)
        # list the users and check whether users from csv are in the listing
        logins = set(user['login'] for user in User.list().stdout)
        imp_users = set(
            user['username']
            for user in csv_to_dataset([files['users']])
        )
        self.assertTrue(imp_users.issubset(logins))

    @data(*import_user_data())
    def test_reimport_users_default_negative(self, test_data):
        """@test: Try to Import all users from the
        predefined source and try to import them again

        @feature: Repetitive User Import

        @assert: 2nd Import will result in No Action Taken

        """
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))
        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        # Import the organizations first
        self.assertEqual(
            Import.organization({
                'csv-file': files['users'],
            }).return_code, 0)
        self.assertEqual(
            Import.user({
                'csv-file': files['users'],
                'new-passwords': pwdfile,
            }).return_code, 0)
        ssh.command(u'rm -rf {}'.format(pwdfile))
        users_before = set(user['login'] for user in User.list().stdout)
        self.assertEqual(
            Import.user({
                'csv-file': files['users'],
                'new-passwords': pwdfile,
            }).return_code, 0)
        users_after = set(user['login'] for user in User.list().stdout)
        self.assertTrue(users_after.issubset(users_before))

    @data(*import_user_data())
    def test_import_users_merge(self, test_data):
        """@test: Try to Merge users with the same name using 'merge-users'
        option.

        @feature: Import Users Map-users

        @assert: Users imported in 2nd import are being mapped to the existing
        ones with the same name

        """
        # prepare the data
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        pwdfiles = [
            os.path.join(tmp_dir, gen_string('alpha', 6)) for _ in range(2)
        ]
        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        # initial import
        for result in (
            Import.organization({'csv-file': files['users']}),
            Import.user({
                'csv-file': files['users'], 'new-passwords': pwdfiles[0],
            }),
        ):
            self.assertEqual(result.return_code, 0)
        # clear the .transition_data to clear the transition mapping
        ssh.command('rm -rf ${HOME}/.transition_data/users*')
        # import users using map-users option
        Import.user({
            'csv-file': files['users'],
            'new-passwords': pwdfiles[1],
            'merge-users': True,
        })
        transition_data = csv_to_dataset(
            ssh.command(u'ls ${HOME}/.transition_data/users*').stdout[:-1]
        )
        for record in transition_data:
            self.assertNotEqual(User.info({'id': record['sat6']}).stdout, '')

    @data(*import_user_data())
    def test_import_users_recovery(self, test_data):
        """@test: Try to Import users with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @feature: Import Users Recover

        @assert: 2nd Import will rename new users, 2nd import will
        map them and the 3rd one will resulit in No Action Taken

        """
        # prepare the data
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        pwdfiles = [
            os.path.join(tmp_dir, gen_string('alpha', 6)) for _ in range(4)
        ]
        files['users'] = update_csv_values(
            files['users'],
            test_data,
            self.default_dataset[0]
        )
        # initial import
        for result in (
            Import.organization({'csv-file': files['users']}),
            Import.user({
                'csv-file': files['users'],
                'new-passwords': pwdfiles[0],
            }),
        ):
            self.assertEqual(result.return_code, 0)
        # clear the .transition_data to clear the transition mapping
        ssh.command('rm -rf ${HOME}/.transition_data/users*')
        # use the default (rename) strategy
        Import.user({
            'csv-file': files['users'],
            'new-passwords': pwdfiles[1],
        })
        transition_data = csv_to_dataset(
            ssh.command(u'ls ${HOME}/.transition_data/users*').stdout[:-1]
        )
        for record in transition_data:
            self.assertEqual(User.info({'id': record['sat6']}).return_code, 0)

        Import.user({'csv-file': files['users'], 'delete': True})
        ssh.command('rm -rf ${HOME}/.transition_data/users*')
        # use the 'none' strategy
        users_before = set(user['login'] for user in User.list().stdout)
        Import.user({
            'csv-file': files['users'],
            'new-passwords': pwdfiles[2],
            'recover': 'none',
        })
        users_after = set(user['login'] for user in User.list().stdout)
        self.assertTrue(users_before.issubset(users_after))
        # use the 'map' strategy
        Import.user({
            'csv-file': files['users'],
            'recover': 'map',
            'new-passwords': pwdfiles[3],
        })
        transition_data = csv_to_dataset(
            ssh.command(u'ls ${HOME}/.transition_data/users*').stdout[:-1]
        )
        for record in transition_data:
            self.assertEqual(
                User.info({'id': record['sat6']}).return_code, 0
            )
        Import.user({'csv-file': files['users'], 'delete': True})
        # do the cleanup
        ssh.command(u'rm -rf {}'.format(' '.join(pwdfiles)))

    @data(*import_org_data())
    def test_import_host_collections_default(self, test_data):
        """@test: Import all System Groups from the default data set
        (predefined source) as the Host Collections.

        @feature: Import Host-Collections

        @assert: 3 Host Collections created

        """
        files = dict(self.default_dataset[1])
        for file_ in ('users', 'system-groups'):
            files[file_] = update_csv_values(
                files[file_],
                test_data,
                self.default_dataset[0]
            )
        # import the prerequisities
        for result in (
            Import.organization({'csv-file': files['users']}),
            Import.host_collection({'csv-file': files['system-groups']}),
        ):
            self.assertEqual(result.return_code, 0)
        transition_data = csv_to_dataset(
            ssh.command(
                u'ls ${HOME}/.transition_data/organizations*'
            ).stdout[:-1]
        )
        # now to check whether the all HC from csv appeared in satellite
        imp_orgs = csv_to_dataset([files['users']])
        for imp_org, transition_record in product(imp_orgs, transition_data):
            if transition_record['sat5'] == imp_org['organization_id']:
                imp_org.update({'sat6': transition_record['sat6']})
        for imp_org in imp_orgs:
            self.assertEqual(
                HostCollection.list(
                    {'organization-id': imp_org['sat6']}
                ).return_code, 0
            )

    @data(*import_org_data())
    def test_reimport_host_collections_default_negative(self, test_data):
        """@test: Import all System Groups from the default data set
        (predefined source) as the Host Collections and try to import
        them again.

        @feature: Repetitive Import Host-Collections

        @assert: 3 Host Collections created

        """
        files = dict(self.default_dataset[1])
        for file_ in ('users', 'system-groups'):
            update_csv_values(
                files[file_],
                test_data,
                self.default_dataset[0]
            )
        # import the prerequisities
        for result in (
            Import.organization({'csv-file': files['users']}),
            Import.host_collection({'csv-file': files['system-groups']}),
        ):
            self.assertEqual(result.return_code, 0)
        transition_data = csv_to_dataset(
            ssh.command(
                u'ls ${HOME}/.transition_data/organization*'
            ).stdout[:-1]
        )
        hcollections_before = [
            HostCollection.list({'organization-id': tr['sat6']}).stdout
            for tr in transition_data
        ]
        self.assertEqual(
            Import.host_collection(
                {'csv-file': files['system-groups']}
            ).return_code, 0
        )
        hcollections_after = [
            HostCollection.list({'organization-id': tr['sat6']}).stdout
            for tr in transition_data
        ]
        self.assertEqual(hcollections_before, hcollections_after)

    @data(*import_org_data())
    def test_import_host_collections_recovery(self, test_data):
        """@test: Try to Import Collections with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @feature: Import HostCollection Recover

        @assert: 2nd Import will rename the new collections, 2nd import will
        map them and the 3rd one will result in No Action Taken

        """
        # prepare the data
        files = dict(self.default_dataset[1])
        for file_ in ('users', 'system-groups'):
            update_csv_values(
                files[file_],
                test_data,
                self.default_dataset[0]
            )
        # initial import
        for result in (
            Import.organization({'csv-file': files['users']}),
            Import.host_collection(
                {'csv-file': files['system-groups']}
            ),
        ):
            self.assertEqual(result.return_code, 0)
        # clear the .transition_data to clear the transition mapping
        ssh.command('rm -rf ${HOME}/.transition_data/host_collections*')

        # use the default (rename) strategy
        self.assertEqual(
            Import.host_collection(
                {'csv-file': files['system-groups'], 'verbose': True}
            ).return_code, 0
        )
        transition_org_data = csv_to_dataset(
            ssh.command(
                u'ls ${HOME}/.transition_data/organizations*'
            ).stdout[:-1]
        )
        transition_data = csv_to_dataset(
            ssh.command(
                u'ls ${HOME}/.transition_data/host_collections*'
            ).stdout[:-1]
        )
        for record in transition_data:
            self.assertEqual(
                HostCollection.info({'id': record['sat6']}).return_code, 0
            )
        Import.host_collection(
            {'csv-file': files['system-groups'], 'delete': True}
        )
        ssh.command('rm -rf ${HOME}/.transition_data/host_collections*')

        # use the 'none' strategy
        hc_before = [
            HostCollection.list({'organization-id': tr['sat6']}).stdout
            for tr in transition_org_data
        ]
        Import.host_collection(
            {'csv-file': files['system-groups'], 'recover': 'none'}
        )
        hc_after = [
            HostCollection.list({'organization-id': tr['sat6']}).stdout
            for tr in transition_org_data
        ]
        self.assertEqual(hc_before, hc_after)

        Import.host_collection(
            {'csv-file': files['system-groups'], 'delete': True}
        )
        ssh.command('rm -rf ${HOME}/.transition_data/host_collections*')

        # use the 'map' strategy
        Import.host_collection({
            'csv-file': files['system-groups'],
            'recover': 'map',
            'verbose': True,
        })
        transition_data = csv_to_dataset(
            ssh.command(
                u'ls ${HOME}/.transition_data/host_collections*'
            ).stdout[:-1]
        )
        for record in transition_data:
            self.assertEqual(
                HostCollection.info({'id': record['sat6']}).return_code, 0
            )
        Import.host_collection(
            {'csv-file': files['system-groups'], 'delete': True}
        )

    @skip_if_bug_open('bugzilla', 1160847)
    def test_bz1160847_translate_macros(self):
        """@test: Check whether all supported Sat5 macros are being
        properly converted to the Puppet facts.
        According to RH Transition Guide (Chapter 3.7.8, Table 3.1)

        @feature: Import config-file --csv-file --generate-only

        @assert: Generated .erb file contains correctly formated puppet facts

        @BZ: 1160847

        """
        # prepare data (craft csv)
        test_data = [
            {
                u'name': u'hostname',
                u'macro': u'{| rhn.system.hostname |}',
                u'fact': u'<%= @fqdn %>',
            },
            {
                u'name': u'sys_ip_address',
                u'macro': u'{| rhn.system.ip_address |}',
                u'fact': u'<%= @ipaddress %>',
            },
            {
                u'name': u'ip_address',
                u'macro': u'{| rhn.system.net_interface'
                          u'.ip_address(eth0) |}',
                u'fact': u'<%= @ipaddress_eth0 %>',
            },
            {
                u'name': u'netmask',
                u'macro': u'{| rhn.system.net_interface'
                          u'.netmask(eth0) |}',
                u'fact': u'<%= @netmask_eth0 %>',
            },
            {
                u'name': u'mac_address',
                u'macro': u'{| rhn.system.net_interface.'
                          u'hardware_address(eth0) |}',
                u'fact': u'<%= @macaddress_eth0 %>',
            },
        ]
        csv_contents = u'\n'.join(
            u'{0}={1}'.format(i['name'], i['macro']) for i in test_data
        )

        csv_row = {
            u'org_id': u'1',
            u'channel_id': u'3',
            u'channel': u'config-1',
            u'channel_type': u'normal',
            u'path': u'/etc/sysconfig/rhn/systemid',
            u'file_type': u'file',
            u'file_id': u'8',
            u'revision': u'1',
            u'is_binary': u'N',
            u'contents': u'{}\n'.format(csv_contents),
            u'delim_start': u'{|',
            u'delim_end': u'|}',
            u'username': u'root',
            u'groupname': u'root',
            u'filemode': u'600',
            u'symbolic_link': u'',
            u'selinux_ctx': u'',
        }
        file_name = build_csv_file([csv_row], self.default_dataset[0])

        # create a random org that will be mapped to sat5 org with id = 1
        if bz_bug_is_open(1226981):
            org_data = {'name': gen_string('alphanumeric')}
        else:
            org_data = {'name': gen_string('utf8')}
        org = make_org(org_data)
        trans_header = [u'sat5', u'sat6', u'delete']
        trans_row = [u'1', org['id'], u'']
        transition_data_file = tempfile.mkstemp(
            prefix='organizations-',
            suffix='.csv',
        )[1]
        with open(transition_data_file, 'wb') as trans_csv:
            csv_writer = csv.writer(trans_csv)
            csv_writer.writerow(trans_header)
            csv_writer.writerow(trans_row)

        ssh.command('mkdir -p ~/.transition_data')
        ssh.upload_file(
            transition_data_file,
            os.path.join(
                '.transition_data/', os.path.basename(transition_data_file)
            )
        )
        os.remove(transition_data_file)
        # run the import command
        self.assertEqual(
            Import.config_file({
                u'csv-file': file_name,
                u'generate-only': True,
            }).return_code, 0
        )
        # collect the contains of the generated file
        cat_cmd = ssh.command(
            u'cat ${{HOME}}/puppet_work_dir/{0}-config_1/templates/'
            u'_etc_sysconfig_rhn_systemid.erb'.format(org['name'].lower())
        )
        # compare the contains with the expected format
        self.assertEqual(
            cat_cmd.stdout[:-1],
            [fact['name'] + '=' + fact['fact'] for fact in test_data],
        )
