# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI"""
import csv
import os
import re
import tempfile

from ddt import ddt
from fauxfactory import gen_string
from itertools import product
from random import sample
from robottelo import ssh
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import make_org
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.import_ import Import
from robottelo.cli.org import Org
from robottelo.cli.repository import Repository
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.decorators import data, bz_bug_is_open, skip_if_bug_open
from robottelo.helpers import prepare_import_data
from robottelo.test import CLITestCase


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
            csv_writer.writerow({
                key: val.encode('utf8') for key, val in row.items()
            })
    if dirname is None:
        remote_file = file_name
    else:
        remote_file = os.path.join(dirname, os.path.basename(file_name))
    ssh.upload_file(file_name, remote_file)
    os.remove(file_name)
    return remote_file


def update_csv_values(csv_file, key, new_data=None, dirname=None):
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
    result = Import.csv_to_dataset([csv_file])
    for change in new_data:
        for record in result:
            if record.get(key) == change['key_id']:
                record.update(change)
                del record['key_id']
                updated = True
    if updated:
        return build_csv_file(result, dirname)
    else:
        return csv_file


def get_sat6_id(entity_dict, transition_dict, key='sat5'):
    """Updates the dictionary of the import entity with 'sat6' key/value pairs
    for keeping the Satellite 6 referrence to the imported entity

    :param entity_dict: A dictionary holding the info for an entity to be
        imported (typically a product of csv_to_dataset())
    :param transition_dict: A dictionary holding the transition data for the
        imported entity (typically a product of Import.*_with_tr_data())
    :param key: A string identifying a key field to identify an entity id
    :returns: entity_dict updated by 'sat6' key/value pair

    """
    for entity, tr_record in product(entity_dict, transition_dict):
        if tr_record[key] == entity['organization_id']:
            entity.update({'sat6': tr_record['sat6']})
    return entity_dict


def gen_import_org_data():
    """Random data for Organization Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    return ([
        {
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric')
        }
        for i in range(3)
    ], [
        {
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('utf8')
        }
        for i in range(3)
    ],)


def gen_import_user_data():
    """Random data for User Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    return ([
        {
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric'),
            u'username': gen_string('alphanumeric')
        }
        for i in range(3)
    ], [
        {
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('utf8'),
            u'username': gen_string('utf8')
        }
        for i in range(3)
    ],)


def gen_import_hostcol_data():
    """Random data for Organization Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    random_data = {'orgs': [], 'hcs': []}
    for i in range(3):
        random_data['orgs'].append({
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric'),
        })
        random_data['hcs'].append({
            u'key_id': type(u'')(i + 1),
            u'org_id': org_ids[i],
            u'name': gen_string('alphanumeric'),
        })
    return (random_data,)


def gen_import_repo_data():
    """Random data for Repository Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    random_data = {'users': [], 'repositories': []}
    for i in range(3):
        random_data['users'].append({
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric'),
        })
        random_data['repositories'].append({
            u'key_id': type(u'')(i + 1),
            u'org_id': org_ids[i],
        })
    return (random_data,)


def gen_import_cv_data():
    """Random data for Content View Import tests"""

    return (
        {
            u'users': [{
                u'key_id': type(u'')(i + 1),
                u'organization': gen_string('alphanumeric')
            } for i in range(3)],
            u'content-views': [{
                u'key_id': type(u'')(i + 1),
                u'channel_name': gen_string('alphanumeric'),
                u'channel_label': gen_string('alphanumeric'),
            } for i in range(3)]
        },
    )


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
            u'rm -rf "${HOME}"/.transition_data "${HOME}"/puppet_work_dir'
        )

    @data(*gen_import_org_data())
    def test_import_orgs_default(self, test_data):
        """@test: Import all organizations from the default data set
        (predefined source).

        @feature: Import Organizations

        @assert: 3 Organizations are created

        """
        files = dict(self.default_dataset[1])
        files['users'] = update_csv_values(
            files['users'],
            u'organization_id',
            test_data,
            self.default_dataset[0]
        )
        ssh_import = Import.organization({'csv-file': files['users']})
        # now to check whether the orgs from csv appeared in satellite
        self.assertEqual(ssh_import.return_code, 0)
        for org in Import.csv_to_dataset([files['users']]):
            self.assertEqual(
                Org.info({'name': org['organization']}).return_code, 0
            )

    @data(*gen_import_org_data())
    def test_import_orgs_manifests(self, test_data):
        """@test: Import all organizations from the default data set
        (predefined source) and upload manifests for each of them

        @feature: Import Organizations including Manifests

        @assert: 3 Organizations are created with 3 manifests uploaded

        """
        files = dict(self.default_dataset[1])
        files['users'] = update_csv_values(
            files['users'],
            u'organization_id',
            test_data,
            self.default_dataset[0]
        )
        ssh_import = Import.organization_with_tr_data_manifests({
            'csv-file': files['users'],
        })
        # now to check whether the orgs from csv appeared in satellite
        orgs = set(org['name'] for org in Org.list().stdout)
        imp_orgs = set(
            org['organization'] for
            org in Import.csv_to_dataset([files['users']])
        )
        self.assertEqual(ssh_import[0].return_code, 0)
        self.assertTrue(imp_orgs.issubset(orgs))
        for org in imp_orgs:
            manifest_history = Subscription.manifest_history(
                {'organization': org}
            ).stdout[3]
            self.assertIn('SUCCESS', manifest_history)

    @data(*gen_import_org_data())
    def test_reimport_orgs_default_negative(self, test_data):
        """@test: Try to Import all organizations from the
        predefined source and try to import them again

        @feature: Import Organizations twice

        @assert: 2nd Import will result in No Action Taken

        """
        files = dict(self.default_dataset[1])
        files['users'] = update_csv_values(
            files['users'],
            u'organization_id',
            test_data,
            self.default_dataset[0]
        )
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).return_code, 0)
        orgs_before = Org.list().stdout
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).return_code, 0)
        self.assertEqual(orgs_before, Org.list().stdout)

    @data(*gen_import_org_data())
    def test_import_orgs_recovery(self, test_data):
        """@test: Try to Import organizations with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @feature: Import Organizations Recover

        @assert: 2nd Import will result in No Action Taken, 3rd one will rename
        the new organizations, and the 4th one will map them

        """
        # prepare the data
        files = dict(self.default_dataset[1])
        files['users'] = update_csv_values(
            files['users'],
            'organization_id',
            test_data,
            self.default_dataset[0]
        )
        # initial import
        self.assertEqual(
            Import.organization({'csv-file': files['users']}).return_code, 0)
        # clear the .transition_data to clear the transition mapping
        ssh.command('rm -rf "${HOME}"/.transition_data')

        # use the 'none' strategy
        orgs_before = Org.list().stdout
        Import.organization({'csv-file': files['users'], 'recover': 'none'})
        self.assertEqual(orgs_before, Org.list().stdout)

        # use the default (rename) strategy
        ssh_imp_rename = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        self.assertEqual(len(ssh_imp_rename[1]), len(test_data))
        for record in ssh_imp_rename[1]:
            self.assertEqual(Org.info({'id': record['sat6']}).return_code, 0)
        Import.organization({'csv-file': files['users'], 'delete': True})

        # use the 'map' strategy
        ssh_imp_map = Import.organization_with_tr_data({
            'csv-file': files['users'],
            'recover': 'map',
        })
        for record in ssh_imp_map[1]:
            self.assertEqual(
                Org.info({'id': record['sat6']}).return_code, 0
            )
        Import.organization({'csv-file': files['users'], 'delete': True})

    @data(*gen_import_user_data())
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
            u'organization_id',
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
            for user in Import.csv_to_dataset([files['users']])
        )
        self.assertTrue(all((user in logins for user in imp_users)))

    @data(*gen_import_user_data())
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
            u'organization_id',
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
            for user in Import.csv_to_dataset([files['users']])
        )
        self.assertTrue(imp_users.issubset(logins))

    @data(*gen_import_user_data())
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
            u'organization_id',
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

    @data(*gen_import_user_data())
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
            u'organization_id',
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
        ssh.command('rm -rf "${HOME}"/.transition_data/users*')
        # import users using merge-users option
        import_merge = Import.user_with_tr_data({
            'csv-file': files['users'],
            'new-passwords': pwdfiles[1],
            'merge-users': True,
        })
        for record in import_merge[1]:
            self.assertNotEqual(User.info({'id': record['sat6']}).stdout, '')

    @data(*gen_import_user_data())
    def test_import_users_recovery(self, test_data):
        """@test: Try to Import users with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @feature: Import Users Recover

        @assert: 2nd Import will rename new users, 3rd one will result
        in No Action Taken and 4th import will map them

        """
        # prepare the data
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        pwdfiles = [
            os.path.join(tmp_dir, gen_string('alpha', 6)) for _ in range(4)
        ]
        files['users'] = update_csv_values(
            files['users'],
            u'organization_id',
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
        ssh.command('rm -rf "${HOME}"/.transition_data/users*')

        # use the default (rename) strategy
        import_rename = Import.user_with_tr_data({
            'csv-file': files['users'],
            'new-passwords': pwdfiles[1],
        })
        for record in import_rename[1]:
            self.assertEqual(User.info({'id': record['sat6']}).return_code, 0)
        Import.user({'csv-file': files['users'], 'delete': True})

        # use the 'none' strategy
        users_before = set(user['login'] for user in User.list().stdout)
        Import.user({
            'csv-file': files['users'],
            'new-passwords': pwdfiles[2],
            'recover': 'none',
        })
        users_after = set(user['login'] for user in User.list().stdout)
        self.assertEqual(users_before, users_after)

        # use the 'map' strategy
        import_map = Import.user_with_tr_data({
            'csv-file': files['users'],
            'recover': 'map',
            'new-passwords': pwdfiles[3],
        })
        for record in import_map[1]:
            self.assertEqual(
                User.info({'id': record['sat6']}).return_code, 0
            )

        # do the cleanup
        ssh.command(u'rm -rf {}'.format(' '.join(pwdfiles)))

    @data(*gen_import_hostcol_data())
    def test_import_host_collections_default(self, test_data):
        """@test: Import all System Groups from the default data set
        (predefined source) as the Host Collections.

        @feature: Import Host-Collections

        @assert: 3 Host Collections created

        """
        files = dict(self.default_dataset[1])
        for file_ in zip(
            ['users', 'system-groups'],
            [u'organization_id', u'org_id'],
            [u'orgs', u'hcs']
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[2]],
                self.default_dataset[0]
            )
        # import the prerequisities
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        import_hc = Import.host_collection_with_tr_data(
            {'csv-file': files['system-groups']}
        )
        for result in (import_org, import_hc):
            self.assertEqual(result[0].return_code, 0)
        # now to check whether the all HC from csv appeared in satellite
        imp_orgs = get_sat6_id(
            Import.csv_to_dataset([files['users']]),
            import_org[1]
        )
        for imp_org in imp_orgs:
            self.assertNotEqual(
                HostCollection.list(
                    {'organization-id': imp_org['sat6']}
                ).stdout, []
            )

    @data(*gen_import_hostcol_data())
    def test_reimport_host_collections_default_negative(self, test_data):
        """@test: Try to re-import all System Groups from the default data set
        (predefined source) as the Host Collections.

        @feature: Repetitive Import Host-Collections

        @assert: 3 Host Collections created, no action taken on 2nd Import

        """
        files = dict(self.default_dataset[1])
        for file_ in zip(
            ['users', 'system-groups'],
            [u'organization_id', u'org_id'],
            [u'orgs', u'hcs']
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[2]],
                self.default_dataset[0]
            )
        # import the prerequisities
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        import_hc = Import.host_collection(
            {'csv-file': files['system-groups']}
        )
        self.assertEqual(import_org[0].return_code, 0)
        self.assertEqual(import_hc.return_code, 0)
        hcollections_before = [
            HostCollection.list({'organization-id': tr['sat6']}).stdout
            for tr in import_org[1]
        ]
        self.assertNotEqual(hcollections_before, [])
        self.assertEqual(
            Import.host_collection(
                {'csv-file': files['system-groups']}
            ).return_code, 0
        )
        hcollections_after = [
            HostCollection.list({'organization-id': tr['sat6']}).stdout
            for tr in import_org[1]
        ]
        self.assertEqual(hcollections_before, hcollections_after)

    @data(*gen_import_hostcol_data())
    def test_import_host_collections_recovery(self, test_data):
        """@test: Try to Import Collections with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @feature: Import HostCollection Recover

        @assert: 2nd Import will rename the new collections, 3nd import will
        result in No Action Taken and the 4th one will map them

        """
        # prepare the data
        files = dict(self.default_dataset[1])
        for file_ in zip(
            ['users', 'system-groups'],
            [u'organization_id', u'org_id'],
            [u'orgs', u'hcs']
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[2]],
                self.default_dataset[0]
            )
        # initial import
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        for result in (
            import_org,
            Import.host_collection_with_tr_data(
                {'csv-file': files['system-groups']}
            ),
        ):
            self.assertEqual(result[0].return_code, 0)
        # clear the .transition_data to clear the transition mapping
        ssh.command('rm -rf "${HOME}"/.transition_data/host_collections*')

        # use the default (rename) strategy
        import_hc_rename = Import.host_collection_with_tr_data(
            {'csv-file': files['system-groups'], 'verbose': True}
        )
        self.assertEqual(import_hc_rename[0].return_code, 0)
        for record in import_hc_rename[1]:
            self.assertEqual(
                HostCollection.info({'id': record['sat6']}).return_code, 0
            )
        Import.host_collection(
            {'csv-file': files['system-groups'], 'delete': True}
        )

        # use the 'none' strategy
        hc_before = [
            HostCollection.list({'organization-id': tr['sat6']}).stdout
            for tr in import_org[1]
        ]
        Import.host_collection(
            {'csv-file': files['system-groups'], 'recover': 'none'}
        )
        hc_after = [
            HostCollection.list({'organization-id': tr['sat6']}).stdout
            for tr in import_org[1]
        ]
        self.assertEqual(hc_before, hc_after)

        # use the 'map' strategy
        import_hc_map = Import.host_collection_with_tr_data({
            'csv-file': files['system-groups'],
            'recover': 'map',
            'verbose': True,
        })
        self.assertEqual(import_hc_map[0].return_code, 0)
        for record in import_hc_map[1]:
            self.assertEqual(
                HostCollection.info({'id': record['sat6']}).return_code, 0
            )

    @data(*gen_import_repo_data())
    def test_import_repo_default(self, test_data):
        """@test: Import and enable all Repositories from the default data set
        (predefined source)

        @feature: Import Enable Repositories

        @assert: 3 Repositories imported and enabled

        """
        # randomize the values for orgs and repos
        files = dict(self.default_dataset[1])
        for file_ in zip(
            ['users', 'repositories'],
            [u'organization_id', u'org_id'],
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[0]],
                self.default_dataset[0]
            )
        # import the prerequisities
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        # now proceed with importing the repositories
        import_repo = Import.repository_with_tr_data({
            'csv-file': files['repositories'],
            'synchronize': True,
            'wait': True,
        })
        for result in (import_org, import_repo):
            self.assertEqual(result[0].return_code, 0)

        # get the sat6 mapping of the imported organizations
        imp_orgs = get_sat6_id(
            Import.csv_to_dataset([files['users']]),
            import_org[1]
        )
        # now to check whether all repos from csv appeared in satellite
        for imp_org in imp_orgs:
            self.assertNotEqual(
                Repository.list({'organization-id': imp_org['sat6']}).stdout,
                [],
            )

    @data(*gen_import_repo_data())
    def test_reimport_repo_negative(self, test_data):
        """@test: Import and enable all Repositories from the default data set
        (predefined source), then try to Import Repositories from the same CSV
        again.

        @feature: Repetitive Import Enable Repositories
        @assert: 3 Repositories imported and enabled, second run should trigger
        no action.

        """
        # randomize the values for orgs and repos
        files = dict(self.default_dataset[1])
        for file_ in zip(
            ['users', 'repositories'],
            [u'organization_id', u'org_id'],
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[0]],
                self.default_dataset[0]
            )
        # import the prerequisities
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        # now proceed with importing the repositories
        import_repo = Import.repository_with_tr_data({
            'csv-file': files['repositories'],
            'synchronize': True,
            'wait': True,
        })
        for result in (import_org, import_repo):
            self.assertEqual(result[0].return_code, 0)

        # get the sat6 mapping of the imported organizations
        imp_orgs = get_sat6_id(
            Import.csv_to_dataset([files['users']]),
            import_org[1]
        )
        repos_before = [
            Repository.list({'organization-id': imp_org['sat6']}).stdout
            for imp_org in imp_orgs
        ]
        # Reimport the same repos and check for changes in sat6
        self.assertEqual(
            Import.repository({
                'csv-file': files['repositories'],
                'synchronize': True,
                'wait': True,
                }).return_code, 0
        )
        self.assertEqual(
            repos_before,
            [
                Repository.list({'organization-id': imp_org['sat6']}).stdout
                for imp_org in imp_orgs
            ]
        )

    @data(*gen_import_repo_data())
    def test_import_repo_recovery(self, test_data):
        """@test: Try to Import Repos with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @feature: Import Repository Recover

        @assert: 2nd Import will rename the new repos, 3rd import will
        map them and the 4th one will result in No Action Taken

        """
        # prepare the data
        files = dict(self.default_dataset[1])
        # randomize the values for orgs and repos
        files = dict(self.default_dataset[1])
        for file_ in zip(
            ['users', 'repositories'],
            [u'organization_id', u'org_id'],
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[0]],
                self.default_dataset[0]
            )
        # import the prerequisities
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        for result in (
            import_org,
            Import.repository_with_tr_data(
                {'csv-file': files['repositories']}
            ),
        ):
            self.assertEqual(result[0].return_code, 0)
        # clear the .transition_data to clear the transition mapping
        ssh.command('rm -rf "${HOME}"/.transition_data/repositories*')
        ssh.command('rm -rf "${HOME}"/.transition_data/products*')

        # use the default (rename) strategy
        import_repo_rename = Import.repository_with_tr_data(
            {'csv-file': files['repositories'], 'verbose': True}
        )
        self.assertEqual(import_repo_rename[0].return_code, 0)
        for record in import_repo_rename[1][1]:
            self.assertEqual(
                Repository.info({'id': record['sat6']}).return_code, 0
            )
        Import.repository(
            {'csv-file': files['repositories'], 'delete': True}
        )

        # use the 'none' strategy
        repos_before = [
            Repository.list({'organization-id': tr['sat6']}).stdout
            for tr in import_org[1]
        ]
        Import.repository(
            {'csv-file': files['repositories'], 'recover': 'none'}
        )
        self.assertEqual(
            repos_before,
            [Repository.list({'organization-id': tr['sat6']}).stdout
                for tr in import_org[1]],
        )

        # use the 'map' strategy
        import_repo_map = Import.repository_with_tr_data({
            'csv-file': files['repositories'],
            'recover': 'map',
            'verbose': True,
        })
        self.assertEqual(import_repo_map[0].return_code, 0)
        for record in import_repo_map[1][1]:
            self.assertEqual(
                Repository.info({'id': record['sat6']}).return_code, 0
            )

    @data(*gen_import_cv_data())
    def test_import_cv_default(self, test_data):
        """@test: Import and enable all Content Views from the default data set
        (predefined source)

        @feature: Import Enable Content View

        @assert: 3 Content Views imported and enabled

        """
        # randomize the values for orgs and repos
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        files['content-views'] = os.path.join(
            tmp_dir,
            'exports/CHANNELS/export.csv',
        )
        for file_ in zip(
            ['users', 'content-views'],
            [u'organization_id', u'org_id'],
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[0]],
                self.default_dataset[0]
            )
        # import the prerequisities
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        import_repo = Import.repository_with_tr_data({
            'csv-file': files['repositories'],
            'synchronize': True,
            'wait': True,
        })
        # now proceed with Content View import
        import_cv = Import.content_view_with_tr_data({
            'csv-file': files['content-views'],
            'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
        })
        for result in (import_org, import_repo, import_cv):
            self.assertEqual(result[0].return_code, 0)

        # get the sat6 mapping of the imported organizations
        imp_orgs = get_sat6_id(
            Import.csv_to_dataset([files['users']]),
            import_org[1]
        )
        # now to check whether all content views from csv appeared in satellite
        for imp_org in imp_orgs:
            self.assertNotEqual(
                ContentView.list(
                    {'organization-id': imp_org['sat6']}
                ).stdout, []
            )

    @data(*gen_import_cv_data())
    def test_reimport_cv_negative(self, test_data):
        """@test: Import and enable all Content Views from the default data set
        (predefined source), then try to Impor them from the same CSV
        again.

        @feature: Repetitive Import Content Views

        @assert: 3 Content Views imported and enabled, 2nd run should trigger
        no action.

        """
        # randomize the values for orgs and repos
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        files['content-views'] = os.path.join(
            tmp_dir, 'exports/CHANNELS/export.csv'
        )
        for file_ in zip(
            ['users', 'content-views'],
            [u'organization_id', u'org_id'],
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[0]],
                self.default_dataset[0]
            )
        # import the prerequisities
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        import_repo = Import.repository_with_tr_data({
            'csv-file': files['repositories'],
            'synchronize': True,
            'wait': True,
        })
        import_cv = Import.content_view_with_tr_data({
            'csv-file': files['content-views'],
            'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
        })
        for result in (import_org, import_repo, import_cv):
            self.assertEqual(result[0].return_code, 0)

        # get the sat6 mapping of the imported organizations
        imp_orgs = get_sat6_id(
            Import.csv_to_dataset([files['users']]),
            import_org[1]
        )
        cvs_before = [
            ContentView.list({'organization-id': imp_org['sat6']}).stdout
            for imp_org in imp_orgs
        ]
        # Reimport the same content views and check for changes in sat6
        self.assertEqual(
            Import.content_view({
                'csv-file': files['content-views'],
                'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
            }).return_code, 0
        )
        self.assertEqual(
            cvs_before,
            [
                ContentView.list({'organization-id': imp_org['sat6']}).stdout
                for imp_org in imp_orgs
            ]
        )

    @data(*gen_import_cv_data())
    def test_import_cv_recovery(self, test_data):
        """@test: Try to Import Content Views with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @feature: Import Content View Recover

        @assert: 2nd Import will rename the new Content Views, 3rd import will
        map them and the 4th one will result in No Action Taken

        """
        # prepare the data
        tmp_dir = self.default_dataset[0]
        files = dict(self.default_dataset[1])
        files['content-views'] = os.path.join(
            tmp_dir,
            'exports/CHANNELS/export.csv',
        )
        # randomize the values for orgs and repos
        for file_ in zip(
            ['users', 'content-views'],
            [u'organization_id', u'org_id'],
        ):
            files[file_[0]] = update_csv_values(
                files[file_[0]],
                file_[1],
                test_data[file_[0]],
                self.default_dataset[0]
            )
        # import the prerequisities
        import_org = Import.organization_with_tr_data(
            {'csv-file': files['users']}
        )
        for result in (
            import_org,
            Import.repository_with_tr_data(
                {'csv-file': files['repositories']}
            ),
            Import.content_view_with_tr_data({
                'csv-file': files['content-views'],
                'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
            }),
        ):
            self.assertEqual(result[0].return_code, 0)
        # clear the .transition_data to clear the transition mapping
        ssh.command('rm -rf "${HOME}"/.transition_data/repositories*')
        ssh.command('rm -rf "${HOME}"/.transition_data/products*')
        ssh.command('rm -rf "${HOME}"/.transition_data/content_views*')

        # use the default (rename) strategy
        import_cv_rename = Import.content_view_with_tr_data({
            'csv-file': files['content-views'],
            'verbose': True,
            'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
        })
        self.assertEqual(import_cv_rename[0].return_code, 0)
        for record in import_cv_rename[1]:
            self.assertEqual(
                ContentView.info({'id': record['sat6']}).return_code, 0
            )
        Import.content_view(
            {'csv-file': files['content-views'], 'delete': True}
        )

        # use the 'none' strategy
        cvs_before = [
            ContentView.list({'organization-id': tr['sat6']}).stdout
            for tr in import_org[1]
        ]
        Import.content_view({
            'csv-file': files['repositories'],
            'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
            'recover': 'none',
        })
        cvs_after = [
            ContentView.list({'organization-id': tr['sat6']}).stdout
            for tr in import_org[1]
        ]
        self.assertEqual(cvs_before, cvs_after)

        # use the 'map' strategy
        import_cvs_map = Import.content_view_with_tr_data({
            'csv-file': files['content-views'],
            'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
            'recover': 'map',
            'verbose': True,
        })
        self.assertEqual(import_cvs_map[0].return_code, 0)
        for record in import_cvs_map[1]:
            self.assertEqual(
                ContentView.info({'id': record['sat6']}).return_code, 0
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
            u'path': gen_string('utf8') + gen_string('alphanumeric'),
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
        invalid_chars = '[^\da-zA-Z\-\.\_]'
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
        prefix = re.sub(invalid_chars, '', org['name'])
        erb_file = re.sub(invalid_chars, '', csv_row['path'])
        if len(prefix) == 0:
            prefix = u'orgid' + org['id']
        if len(erb_file) == 0:
            erb_file = u'file_id8'
        # collect the contains of the generated file
        cat_cmd = ssh.command(
            u'cat "${{HOME}}"/puppet_work_dir/{0}-config_1/templates/'
            u'{1}.erb'.format(prefix.lower(), erb_file)
        )
        # compare the contains with the expected format
        self.assertEqual(
            cat_cmd.stdout[:-1],
            [fact['name'] + '=' + fact['fact'] for fact in test_data],
        )
