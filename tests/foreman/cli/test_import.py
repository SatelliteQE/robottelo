# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI"""
import csv
import os
import tempfile
from ddt import ddt
from fauxfactory import gen_string
from robottelo.common import manifests, ssh
from robottelo.common.helpers import prepare_import_data
from robottelo.common.decorators import (
    data,
    bz_bug_is_open,
    skip_if_bug_open,
)
from robottelo.test import CLITestCase
from robottelo.cli.import_ import Import
from robottelo.cli.factory import make_org
from robottelo.cli.org import Org
from robottelo.cli.user import User


def csv_to_dataset(csv_file):
    """Process a remote CSV file.

    Read a remote CSV file, process it and return it.

    :param csv_file: A string. The path to a CSV file that resides
        on a remote server.

    :returns: A dictionary holding the contents of the CSV file.

    """
    ssh_cat = ssh.command('cat {0}'.format(csv_file))
    if ssh_cat.return_code != 0:
        raise Exception(ssh_cat.stderr())
    else:
        ssh_cat.stdout.pop()
        csv = ssh_cat.stdout
    keys = csv[0].split(',')
    del csv[0]
    return [
        dict(zip(keys, val.split(',')))
        for val
        in csv
    ]


def build_csv_file(rows=None):
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
    return file_name


def update_csv_values(csv_file, new_data=None):
    """Build CSV with updated key values provided as an argument
    in order to randomize the dataset with keeping the organization_id
    mappings

    :param csv_file: A string. The path to a CSV file that resides
        on a remote server.
    :param new_data: A list of dictionary objects. Each object has to
        contain an org_id key corresponding to organization_id of the record
        being updated and the key-value pairs of attributes to be changed for
        the particular records. For example::

            [
                {
                    u'org_id': u'1',
                    u'organization': u'updated_organization_name_1',
                    u'username': u'updated_user_name_1',
                },
                {
                    u'org_id': u'2',
                    u'organization': u'updated_organization_name_2',
                    u'username': u'updated_user_name_2',
                }
            ]

    :returns: A string. The path to a locally created CSV file

    """
    # if new_data is not specified, no change happens
    if new_data is None:
        return csv_file

    result = csv_to_dataset(csv_file)
    for change in new_data:
        for record in result:
            if record['organization_id'] == change['organization_id']:
                record.update(change)
    return build_csv_file(result)


def import_org_data():
    """Random data for Organization Import tests"""

    return ([
        {
            u'organization_id': u'1',
            u'organization': gen_string('alphanumeric')
        },
        {
            u'organization_id': u'2',
            u'organization': gen_string('alphanumeric')
        },
        {
            u'organization_id': u'3',
            u'organization': gen_string('alphanumeric')
        },
    ],)


def import_user_data():
    """Random data for User Import tests"""

    return ([
        {
            u'organization_id': u'1',
            u'organization': gen_string('alphanumeric'),
            u'username': gen_string('alphanumeric')
        },
        {
            u'organization_id': u'2',
            u'organization': gen_string('alphanumeric'),
            u'username': gen_string('alphanumeric')
        },
        {
            u'organization_id': u'3',
            u'organization': gen_string('alphanumeric'),
            u'username': gen_string('alphanumeric')
        },
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
        # remove the dataset
        ssh.command('rm -rf {}'.format(cls.default_dataset[0]))

    @data(*import_org_data())
    def test_import_orgs_default(self, test_data):
        """@test: Import all organizations from the default data set
        (predefined source).

        @feature: Import Organizations

        @assert: 3 Organizations are created

        """
        files = dict(self.default_dataset[1])
        new_dataset = update_csv_values(
            files['users'],
            test_data
        )
        ssh.upload_file(new_dataset, new_dataset)
        files['users'] = new_dataset

        ssh_import = Import.organization({'csv-file': files['users']})

        # now to check whether the orgs from csv appeared in sattelite
        orgs = set(org['name'] for org in Org.list().stdout)
        imp_orgs = set(
            org['organization'] for
            org in csv_to_dataset(files['users'])
        )
        os.remove(new_dataset)
        ssh.command('rm -rf ${HOME}/.transition_data')
        self.assertEqual(ssh_import.return_code, 0)
        self.assertEqual(
            ssh_import.stdout,
            [
                u'Summary',
                u'  Created {0} organizations.'.format(len(imp_orgs)),
                u''
            ]
        )
        self.assertTrue(all((org in orgs for org in imp_orgs)))

    @data(*import_org_data())
    def test_import_orgs_manifests(self, test_data):
        """@test: Import all organizations from the default data set
        (predefined source) and upload manifests for each of them

        @feature: Import Organizations including Manifests

        @assert: 3 Organizations are created with 3 manifests uploaded

        """
        files = dict(self.default_dataset[1])
        new_dataset = update_csv_values(
            files['users'],
            test_data
        )
        ssh.upload_file(new_dataset, new_dataset)
        files['users'] = new_dataset
        csv_records = csv_to_dataset(files['users'])
        # create number of manifests corresponding to the number of orgs
        manifest_list = []
        man_dir = ssh.command('mktemp -d').stdout[1]
        for org in set([rec['organization'] for rec in csv_records]):
            for char in [' ', '.', '#']:
                org = org.replace(char, '_')
            man_file = manifests.clone()
            ssh.upload_file(man_file, '{0}/{1}.zip'.format(man_dir, org))
            manifest_list.append('{0}/{1}.zip'.format(man_dir, org))
            os.remove(man_file)
        ssh_import = Import.organization({
            'csv-file': files['users'],
            'upload-manifests-from': man_dir,
        })
        # cleanup the files and perform the assertions
        os.remove(new_dataset)
        ssh.command(
            'rm -rf ${{HOME}}/.transition_data {}'
            .format(man_dir)
        )
        self.assertIn('Created 3 organizations.', ''.join(ssh_import.stdout))
        self.assertIn('Uploaded 3 manifests.', ''.join(ssh_import.stdout))

    @data(*import_org_data())
    def test_reimport_orgs_default_negative(self, test_data):
        """@test: Try to Import all organizations from the
        predefined source and try to import them again

        @feature: Import Organizations twice

        @assert: 2nd Import will result in No Action Taken

        """
        files = dict(self.default_dataset[1])
        new_dataset = update_csv_values(
            files['users'],
            test_data
        )
        ssh.upload_file(new_dataset, new_dataset)
        files['users'] = new_dataset
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).return_code, 0)
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).stdout,
            [u'Summary', u'  No action taken.', u'']
        )
        os.remove(new_dataset)
        ssh.command(
            'rm -rf ${{HOME}}/.transition_data {}'.format(files['users'])
        )

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
        tmp_dir, files = prepare_import_data()
        pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))
        new_dataset = update_csv_values(
            files['users'],
            test_data
        )
        ssh.upload_file(new_dataset, new_dataset)
        files['users'] = new_dataset
        ssh_map = Import.organization({
            'csv-file': files['users'],
            'into-org-id': new_org['id'],
            'verbose': True,
        })
        self.assertIn(u'Mapped 3 organizations.', ''.join(ssh_map.stdout))
        Import.user({'csv-file': files['users'], 'new-passwords': pwdfile})

        # list users by org-id and check whether users from csv are in listing
        users = User().list({u'organization-id': new_org['id']})
        logins = set(user['login'] for user in users.stdout)
        imp_users = set(
            user['username']
            for user in csv_to_dataset(files['users'])
        )
        self.assertTrue(all((user in logins for user in imp_users)))

        # do the cleanup
        os.remove(new_dataset)
        ssh.command(
            'rm -rf ${{HOME}}/.transition_data {0} {1}'
            .format(pwdfile, tmp_dir)
        )

    @data(*import_user_data())
    def test_import_users_default(self, test_data):
        """@test: Import all 3 users from the our default data set (predefined
        source).

        @feature: Import Users

        @assert: 3 Users created

        """
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))

        new_dataset = update_csv_values(
            files['users'],
            test_data
        )
        ssh.upload_file(new_dataset, new_dataset)
        files['users'] = new_dataset
        Import.organization({'csv-file': files['users']})
        ssh_import = Import.user({
            'csv-file': files['users'],
            'new-passwords': pwdfile
        })
        os.remove(new_dataset)
        ssh.command(
            'rm -rf ${{HOME}}/.transition_data {}'
            .format(pwdfile)
        )
        self.assertEqual(
            ssh_import.stdout,
            [u'Summary', u'  Created 3 users.', u'']
        )

    @data(*import_user_data())
    def test_reimport_users_default_negative(self, test_data):
        """@test: Try to Import all users from the
        predefined source and try to import them again

        @feature: Import Users twice

        @assert: 2nd Import will result in No Action Taken

        """
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))
        new_dataset = update_csv_values(
            files['users'],
            test_data
        )
        ssh.upload_file(new_dataset, new_dataset)
        files['users'] = new_dataset
        # Import the organizations first
        self.assertEqual(
            Import.organization({
                'csv-file': files['users'],
            }).return_code, 0)
        self.assertEqual(
            Import.user({
                'csv-file': files['users'],
                'new-passwords': pwdfile,
            }).stderr, '')
        ssh.command(u'rm -rf {}'.format(pwdfile))
        self.assertEqual(
            Import.user({
                'csv-file': files['users'],
                'new-passwords': pwdfile,
            }).stdout,
            [u'Summary', u'  No action taken.', u'']
        )
        os.remove(new_dataset)
        ssh.command(
            'rm -rf ${{HOME}}/.transition_data {}'.format(files['users'])
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
        file_name = build_csv_file([csv_row])

        # create a random org that will be mapped to sat5 org with id = 1
        if bz_bug_is_open(1226981):
            org_data = {'name': gen_string('alphanumeric')}
        else:
            org_data = {'name': gen_string('utf8')}
        org = make_org(org_data)
        trans_header = [u'sat5', u'sat6', u'delete']
        trans_row = [u'1', org['id'], u'']
        trans_file = tempfile.mkstemp(
            prefix='organizations-',
            suffix='.csv',
        )[1]
        with open(trans_file, 'wb') as trans_csv:
            csv_writer = csv.writer(trans_csv)
            csv_writer.writerow(trans_header)
            csv_writer.writerow(trans_row)

        # upload the files and remove them on local
        ssh.command('mkdir -p ~/.transition_data')
        ssh.upload_file(file_name, os.path.basename(file_name))
        ssh.upload_file(
            trans_file, '.transition_data/' + os.path.basename(trans_file),
        )
        os.remove(file_name)
        os.remove(trans_file)
        # run the import command
        self.assertEqual(
            Import.config_file({
                u'csv-file': u'$HOME/{0}'.format(os.path.basename(file_name)),
                u'generate-only': True,
            }).return_code, 0
        )
        # collect the contains of the generated file
        cat_cmd = ssh.command(
            'cat $HOME/puppet_work_dir/{0}-config_1/templates/'
            '_etc_sysconfig_rhn_systemid.erb'.format(org['name'].lower())
        )
        # compare the contains with the expected format
        self.assertEqual(
            cat_cmd.stdout[:-1],
            [fact['name'] + '=' + fact['fact'] for fact in test_data],
        )
        # cleanup the remote part
        ssh.command(u'rm -rf $HOME/.transition_data ~/puppet_work_dir')
        ssh.command(u'rm -rf $HOME/{0}'.format(os.path.basename(file_name)))
