# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI

@Requirement: Import

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
import csv
import os
import re
import tempfile

from fauxfactory import gen_string
from itertools import product
from random import sample
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.contenthost import ContentHost
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import make_org
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.import_ import Import
from robottelo.cli.org import Org
from robottelo.cli.repository import Repository
from robottelo.cli.subscription import Subscription
from robottelo.cli.template import Template
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.decorators import (
    affected_by_bz,
    run_in_one_thread,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier3,
)
from robottelo.test import CLITestCase


def clean_transdata():
    """Remove transition dataset
    """
    ssh.command(u'rm -rf "${HOME}"/.transition_data "${HOME}"/puppet_work_dir')


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


def prepare_import_data(tar_path=None):
    """Fetch and uncompress the CSV files from the source."""
    tmpdir = ssh.command('mktemp -d').stdout[0]
    # if path to tar file not specified, download the default one
    if tar_path is None:
        tar_remote_path = settings.transition.exported_data
        cmd = u'wget {0} -O - | tar -xzvC {1}'.format(tar_remote_path, tmpdir)
    else:
        cmd = u'tar -xzvf {0} -C {1}'.format(tar_path, tmpdir)

    files = {}
    for filename in ssh.command(cmd).stdout:
        for key in ('activation-keys', 'channels', 'config-files-latest',
                    'kickstart-scripts', 'repositories', 'system-groups',
                    'system-profiles', 'users', 'export'):
            if filename.endswith(key + '.csv'):
                if key == 'export':
                    key = 'custom-channels'
                files[key] = os.path.join(tmpdir, filename)
                break
    return tmpdir, files


def import_content_hosts(files, tmp_dir):
    """Import all Content Hosts from the Sat5 export csv file including all
    the required entities.

    :param files: A dictionary of CSV file names and paths
    :param tmp_dir: A path to the dataset
    :returns: A dictionary of Import objects for every entity

    """
    import_org = Import.organization_with_tr_data(
        {'csv-file': files['users']}
    )
    import_repo = Import.repository_with_tr_data({
        'csv-file': files['repositories'],
        'synchronize': True,
        'wait': True,
    })
    import_cv = Import.content_view_with_tr_data({
        u'csv-file': files['custom-channels'],
        u'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
        u'verbose': True
    })
    # WONTFIX if affected_by_bz('1263650'):
    wait_for_publish()
    # proceed with importing the content hosts
    import_chosts = Import.content_host_with_tr_data({
        u'csv-file': files['system-profiles'],
        u'export-directory': tmp_dir,
        u'verbose': True
    })
    return {
        u'organizations': import_org,
        u'repositories': import_repo,
        u'content_views': import_cv,
        u'content_hosts': import_chosts,
    }


def update_csv_values(files, new_data, dirname=None):
    """Build CSV file(s) with updated key values provided as an argument
    in order to randomize the dataset with keeping the organization_id
    mappings

    :param files: A dictionary with transition files and their paths on
        a remote server.
    :param new_data: A dictionary containing a file name as a key and a list
        of dictionaries representing the individual changes to the CSV.
        For example::

            {'users': [
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
            ]}

    :param dirname: A string. Target destination for the new CSV files.
    :returns: A dictionary with updated CSV file paths.

    """
    for file_ in new_data:
        updated = False
        result = Import.csv_to_dataset([files[file_]])
        for change in new_data[file_]:
            key = change.get('key')
            for record in result:
                if record.get(key) == change['key_id']:
                    record.update(change)
                    del record['key_id']
                    del record['key']
                    updated = True
        if updated:
            files[file_] = build_csv_file(result, dirname)
    return files


def verify_rh_repos(tr_data, channels_file):
    """Verifies that appropriate Products and Content Views have been created
    for the enabled Red Hat repository.

    :param tr_data: Transition data of the Import command
    :param channels_file: Sat5 transition file containing the channels to be
        imported/enabled
    :returns: A tuple of lists containing info about all related Products and
        Content Views

    """
    rh_repos = [
        repo for repo in Import.csv_to_dataset([channels_file])
        if (
            repo['channel_name'].startswith('Red Hat') or
            repo['channel_name'].startswith('RHN')
        )
    ]
    repo_list = []
    cv_list = []
    for record in product(rh_repos, tr_data):
        repo_list.append(
            Repository.list({
                u'organization-id': record[1]['sat6'],
                u'name':  Import.repos[record[0]['channel_label']]
            })
        )
        cv_list.append(
            ContentView.info({
                u'organization-id': record[1]['sat6'],
                u'name': record[0]['channel_name']
            })['id']
        )
    return repo_list, cv_list


def get_sat6_id(
    entity_dict, transition_dict, tr_key='sat5', ent_key='organization_id'
):
    """Updates the dictionary of the import entity with 'sat6' key/value pairs
    for keeping the Satellite 6 referrence to the imported entity

    :param entity_dict: A dictionary holding the info for an entity to be
        imported (typically a product of csv_to_dataset())
    :param transition_dict: A dictionary holding the transition data for the
        imported entity (typically a product of Import.*_with_tr_data())
    :param tr_key: A string identifying a transition key field to identify
        an entity id
    :param ent_key: A string identifying entity key field to identify
        an entity id
    :returns: entity_dict updated by 'sat6' key/value pair
    """
    for entity, tr_record in product(entity_dict, transition_dict):
        if tr_record[tr_key] == entity[ent_key]:
            entity.update({'sat6': tr_record['sat6']})
    return entity_dict


def wait_for_publish(delay_step=30):
    from time import sleep
    from robottelo.cli.task import Task
    while [
        t for t in Task.list({'search': 'state=running'})
            if t['task-action'].startswith('Publish')
    ]:
        sleep(delay_step)


def gen_import_org_data():
    """Random data for Organization Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    return (
        {'users': [{
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric')
        } for i in range(len(org_ids))]},
        {'users': [{
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('utf8')
        } for i in range(len(org_ids))]},
    )


def gen_import_org_manifest_data():
    """Random data for Organization Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    random_data = (
        {'users': [{
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric')
        } for i in range(len(org_ids))]},
    )
    if not affected_by_bz('1260722'):
        random_data = random_data + (
            {'users': [{
                u'key': 'organization_id',
                u'key_id': type(u'')(i + 1),
                u'organization_id': org_ids[i],
                u'organization': gen_string('utf8')
            } for i in range(len(org_ids))]},
        )
    return random_data


def gen_import_user_data():
    """Random data for User Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    return (
        {'users': [{
            u'key': u'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric'),
            u'username': gen_string('alphanumeric')
        } for i in range(len(org_ids))]},
        {'users': [{
            u'key': u'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('utf8'),
            u'username': gen_string('utf8')
        } for i in range(len(org_ids))]},
    )


def gen_import_hostcol_data():
    """Random data for Organization Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    random_data = {'users': [], 'system-groups': []}
    for i in range(len(org_ids)):
        random_data['users'].append({
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric'),
        })
        random_data['system-groups'].append({
            u'key': u'org_id',
            u'key_id': type(u'')(i + 1),
            u'org_id': org_ids[i],
            u'name': gen_string('alphanumeric'),
        })
    return (random_data,)


def gen_import_repo_data():
    """Random data for Repository Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    random_data = {'users': [], 'repositories': []}
    for i in range(len(org_ids)):
        random_data['users'].append({
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric'),
        })
        random_data['repositories'].append({
            u'key': 'org_id',
            u'key_id': type(u'')(i + 1),
            u'org_id': org_ids[i],
        })
    return (random_data,)


def gen_import_cv_data():
    """Random data for Content View Import tests"""
    return ({
        u'users': [{
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization': gen_string('alphanumeric')}
            for i in range(3)
        ],
        u'custom-channels': [{
            u'key': u'org_id',
            u'key_id': type(u'')(i + 1),
            u'channel_name': gen_string('alphanumeric'),
            u'channel_label': gen_string('alphanumeric')}
            for i in range(3)
        ]},
    )


def gen_import_rh_repo_data():
    """Random data for RH Repos Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    # wipe all channel names and labels excepting channel id 106
    return (
        {
            u'users': [{
                u'key': u'organization_id',
                u'key_id': type(u'')(i + 1),
                u'organization_id': org_ids[i],
                u'organization': gen_string('alphanumeric'),
            } for i in range(len(org_ids))],
            u'channels': [{
                u'key': u'channel_id',
                u'key_id': type(u'')(i),
                u'channel_label': u'',
                u'channel_name': gen_string('alphanumeric'),
            } for i in set(range(101, 113)) - {106}] + [
                {
                    u'key': u'org_id',
                    u'key_id': type(u'')(i + 1),
                    u'org_id': org_ids[i],
                } for i in range(len(org_ids))
            ],
        },
    )


def gen_import_chost_data():
    """Random data for Content Host Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    return (
        {
            u'users': [{
                u'key': u'organization_id',
                u'key_id': type(u'')(i + 1),
                u'organization': gen_string('alphanumeric'),
            } for i in range(len(org_ids))],
            u'custom-channels': [{
                u'key': u'channel_id',
                u'key_id': type(u'')(i + 1),
                u'channel_name': gen_string('alphanumeric'),
                u'channel_label': gen_string('alphanumeric')}
                # generate random names and labels for channels 106-112
                # according channel numbering in our sample file
                for i in range(106, 113)
            ],
            u'system-profiles': [{
                u'key': u'server_id',
                u'key_id': type(u'')(1000010000 + i),
                u'base_channel_id': u'110',
                u'child_channel_id': u'None;111'}
                # generate random data for sys profiles 1000010000[8-10]
                for i in set(range(8, 11))
            ],
        },
    )


def gen_import_snippet_data():
    """Random data for Repository Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    random_data = {'users': [], 'kickstart-scripts': []}
    for i in range(len(org_ids)):
        random_data['users'].append({
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric'),
        })
        random_data['kickstart-scripts'].append({
            u'key': 'org_id',
            u'key_id': type(u'')(i + 1),
            u'org_id': org_ids[i],
            u'script_name': gen_string('utf8'),
            u'kickstart_label': gen_string('utf8'),
            u'script_type': sample([u'pre', u'post'], 1).pop(),
            u'chroot': sample([u'Y', u'N'], 1).pop(),
        })
    return (random_data,)


def gen_import_config_files_data():
    """Random data for Config File Import tests"""
    org_ids = [type(u'')(org_id) for org_id in sample(range(1, 1000), 3)]
    random_data = {'users': [], 'config-files-latest': []}
    for i in range(len(org_ids)):
        random_data['users'].append({
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization_id': org_ids[i],
            u'organization': gen_string('alphanumeric'),
        })
        random_data['config-files-latest'].append({
            u'key': 'org_id',
            u'key_id': type(u'')(i + 1),
            u'org_id': org_ids[i],
        })
    return (random_data,)


def gen_import_ak_data():
    """Random data for AK Import tests"""
    return ({
        u'users': [{
            u'key': 'organization_id',
            u'key_id': type(u'')(i + 1),
            u'organization': gen_string('alphanumeric'),
        } for i in range(3)],
        u'custom-channels': [{
            u'key': u'org_id',
            u'key_id': type(u'')(i + 1),
            u'channel_name': gen_string('alphanumeric'),
            u'channel_label': gen_string('alphanumeric'),
        } for i in range(3)],
        u'system-groups': [{
            u'key': u'org_id',
            u'key_id': type(u'')(i + 1),
            u'name': gen_string('alphanumeric'),
        } for i in range(3)],
        u'activation-keys': [{
            u'key': u'org_id',
            u'key_id': type(u'')(i + 1),
            u'token': type(u'')(i + 1) + '-' + gen_string('utf8'),
            u'base_channel_id': u'110',
            u'child_channel_id': u'None;111',
        } for i in range(3)],
    },)


@run_in_one_thread
class TestImport(CLITestCase):
    """Import CLI tests.

    All default tests pass no options to the imprt object
    In such case methods download a default data set from URL
    specified in robottelo.properties.

    """
    @classmethod
    @skip_if_not_set('transition')
    def setUpClass(cls):
        super(TestImport, cls).setUpClass()
        # prepare the default dataset
        cls.default_dataset = prepare_import_data()

    @classmethod
    def tearDownClass(cls):
        ssh.command(u'rm -r {0}'.format(cls.default_dataset[0]))
        super(TestImport, cls).tearDownClass()

    @tier1
    def test_positive_import_orgs_default(self):
        """Import all organizations from the default data set
        (predefined source).

        @id: e7d91832-72bb-4d15-9a75-b3bc0d40b857

        @expectedresults: 3 Organizations are created

        """
        for test_data in gen_import_org_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                Import.organization({'csv-file': files['users']})
                # now to check whether the orgs from csv appeared in satellite
                for org in Import.csv_to_dataset([files['users']]):
                    Org.info({'name': org['organization']})
                clean_transdata()

    @tier3
    def test_positive_import_orgs_manifests(self):
        """Import all organizations from the default data set
        (predefined source) and upload manifests for each of them

        @id: 4e64ecb7-68ac-40ed-91b8-a2ac1b426b20

        @expectedresults: 3 Organizations are created with 3 manifests uploaded


        @CaseLevel: System
        """
        for test_data in gen_import_org_manifest_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                Import.organization_with_tr_data_manifests({
                    'csv-file': files['users'],
                })
                # now to check whether the orgs from csv appeared in satellite
                orgs = set(org['name'] for org in Org.list())
                imp_orgs = set(
                    org['organization'] for
                    org in Import.csv_to_dataset([files['users']])
                )
                self.assertTrue(imp_orgs.issubset(orgs))
                for org in imp_orgs:
                    manifest_history = Subscription.manifest_history({
                        'organization': org,
                    })[3]
                    self.assertIn('SUCCESS', manifest_history)
                clean_transdata()

    @tier1
    def test_negative_reimport_orgs_default(self):
        """Try to Import all organizations from the predefined source
        and try to import them again

        @id: 990e5efc-7f72-45c9-a402-76633adcd49f

        @expectedresults: 2nd Import will result in No Action Taken

        """
        for test_data in gen_import_org_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                Import.organization({'csv-file': files['users']})
                orgs_before = Org.list()
                Import.organization({'csv-file': files['users']})
                self.assertEqual(orgs_before, Org.list())
                clean_transdata()

    @tier1
    def test_positive_import_orgs_recovery(self):
        """Try to Import organizations with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @id: e85563e8-284c-420c-9b62-30a847039e36

        @expectedresults: 2nd Import will result in No Action Taken, 3rd one
        will rename the new organizations, and the 4th one will map them

        """
        for test_data in gen_import_org_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # initial import
                Import.organization({'csv-file': files['users']})
                # clear the .transition_data to clear the transition mapping
                ssh.command('rm -rf "${HOME}"/.transition_data')

                # use the 'none' strategy
                orgs_before = Org.list()
                Import.organization({
                    'csv-file': files['users'], 'recover': 'none'
                })
                self.assertEqual(orgs_before, Org.list())
                # use the default (rename) strategy
                imp_rename = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                self.assertEqual(
                    len(imp_rename[1]), len(test_data['users'])
                )
                for record in imp_rename[1]:
                    Org.info({'id': record['sat6']})
                Import.organization({
                    'csv-file': files['users'], 'delete': True
                })
                # use the 'map' strategy
                imp_map = Import.organization_with_tr_data({
                    'csv-file': files['users'], 'recover': 'map',
                })
                for record in imp_map[1]:
                    Org.info({'id': record['sat6']})
                Import.organization({
                    'csv-file': files['users'], 'delete': True
                })
                clean_transdata()

    @tier1
    def test_positive_merge_orgs(self):
        """Try to Import all organizations and their users from CSV
        to a mapped organization.

        @id: f456d8ea-2388-4944-a194-8860154c2529

        @expectedresults: 3 Organizations Mapped and their Users created in a
        single Organization

        """
        for test_data in gen_import_user_data():
            with self.subTest(test_data):
                # create a new Organization and prepare CSV files
                new_org = make_org()
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))
                files = update_csv_values(files, test_data, tmp_dir)
                Import.organization({
                    'csv-file': files['users'],
                    'into-org-id': new_org['id'],
                    'verbose': True,
                })
                Import.user({
                    'csv-file': files['users'], 'new-passwords': pwdfile
                })
                # list users by org-id and check whether
                # users from csv are in listing
                users = User.list({u'organization-id': new_org['id']})
                logins = set(user['login'] for user in users)
                imp_users = set(
                    user['username']
                    for user in Import.csv_to_dataset([files['users']])
                )
                self.assertTrue(all((user in logins for user in imp_users)))
                clean_transdata()

    @tier1
    def test_positive_import_users_default(self):
        """Import all 3 users from the default data set (predefined
        source).

        @id: 4306e315-85dc-4324-9ecc-911f97d461ae

        @expectedresults: 3 Users created

        """
        for test_data in gen_import_user_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))
                Import.organization({'csv-file': files['users']})
                Import.user({
                    'csv-file': files['users'], 'new-passwords': pwdfile,
                })
                # list the users and check whether
                # users from csv are in the listing
                logins = set(user['login'] for user in User.list())
                imp_users = set(
                    user['username']
                    for user in Import.csv_to_dataset([files['users']])
                )
                self.assertTrue(imp_users.issubset(logins))
                clean_transdata()

    @tier1
    def test_negative_reimport_users_default(self):
        """Try to Import all users from the
        predefined source and try to import them again

        @id: 7142fcf0-1766-4bf6-bb82-26dbf9fb18ec

        @expectedresults: 2nd Import will result in No Action Taken

        """
        for test_data in gen_import_user_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                pwdfile = os.path.join(tmp_dir, gen_string('alpha', 6))
                # Import the organizations first
                Import.organization({'csv-file': files['users']})
                Import.user({
                    'csv-file': files['users'], 'new-passwords': pwdfile,
                })
                ssh.command(u'rm -rf {0}'.format(pwdfile))
                users_before = set(user['login'] for user in User.list())
                Import.user({
                    'csv-file': files['users'], 'new-passwords': pwdfile,
                })
                users_after = set(user['login'] for user in User.list())
                self.assertTrue(users_after.issubset(users_before))
                clean_transdata()

    @tier1
    def test_positive_import_users_merge(self):
        """Try to Merge users with the same name using 'merge-users'
        option.

        @id: 466a9bbd-f804-4d22-993d-37a8c6b9dade

        @expectedresults: Users imported in 2nd import are being mapped to the
        existing ones with the same name

        """
        for test_data in gen_import_user_data():
            with self.subTest(test_data):
                # prepare the data
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                pwdfiles = [
                    os.path.join(tmp_dir, gen_string('alpha', 6))
                    for _ in range(2)
                ]
                # initial import
                Import.organization({'csv-file': files['users']})
                Import.user({
                    'csv-file': files['users'],
                    'new-passwords': pwdfiles[0],
                })
                # clear the .transition_data to clear the transition mapping
                ssh.command('rm -rf "${HOME}"/.transition_data/users*')
                # import users using merge-users option
                import_merge = Import.user_with_tr_data({
                    'csv-file': files['users'],
                    'new-passwords': pwdfiles[1],
                    'merge-users': True,
                })
                for record in import_merge[1]:
                    self.assertNotEqual(User.info({'id': record['sat6']}), '')
                clean_transdata()

    @tier1
    def test_positive_import_users_recovery(self):
        """Try to Import users with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @id: 6c235a7a-d957-4144-a0f3-0f048851da0f

        @expectedresults: 2nd Import will rename new users, 3rd one will result
        in No Action Taken and 4th import will map them

        """
        for test_data in gen_import_user_data():
            with self.subTest(test_data):
                # prepare the data
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                pwdfiles = [
                    os.path.join(tmp_dir, gen_string('alpha', 6))
                    for _ in range(4)
                ]
                # initial import
                Import.organization({'csv-file': files['users']})
                Import.user({
                    'csv-file': files['users'],
                    'new-passwords': pwdfiles[0],
                })
                # clear the .transition_data to clear the transition mapping
                ssh.command('rm -rf "${HOME}"/.transition_data/users*')

                # use the default (rename) strategy
                import_rename = Import.user_with_tr_data({
                    'csv-file': files['users'],
                    'new-passwords': pwdfiles[1],
                })
                for record in import_rename[1]:
                    User.info({'id': record['sat6']})
                Import.user({'csv-file': files['users'], 'delete': True})

                # use the 'none' strategy
                users_before = set(user['login'] for user in User.list())
                Import.user({
                    'csv-file': files['users'],
                    'new-passwords': pwdfiles[2],
                    'recover': 'none',
                })
                users_after = set(user['login'] for user in User.list())
                self.assertEqual(users_before, users_after)

                # use the 'map' strategy
                import_map = Import.user_with_tr_data({
                    'csv-file': files['users'],
                    'recover': 'map',
                    'new-passwords': pwdfiles[3],
                })
                for record in import_map[1]:
                    User.info({'id': record['sat6']})

                # do the cleanup
                ssh.command(u'rm -rf {0}'.format(' '.join(pwdfiles)))
                clean_transdata()

    @tier1
    def test_positive_import_host_collections_default(self):
        """Import all System Groups from the default data set
        (predefined source) as the Host Collections.

        @id: c0d19696-49fb-4dd2-b66d-6fc05042a668

        @expectedresults: 3 Host Collections created

        """
        for test_data in gen_import_hostcol_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                Import.host_collection_with_tr_data({
                    'csv-file': files['system-groups'],
                })
                # now check whether all HCs from csv are imported
                imp_orgs = get_sat6_id(
                    Import.csv_to_dataset([files['users']]),
                    import_org[1]
                )
                for imp_org in imp_orgs:
                    self.assertNotEqual(
                        HostCollection.list(
                            {'organization-id': imp_org['sat6']}
                        ),
                        []
                    )
                clean_transdata()

    @tier1
    def test_negative_reimport_host_collections_default(self):
        """Try to re-import all System Groups from the default data set
        (predefined source) as the Host Collections.

        @id: cb3e4799-2d3d-4e5f-8a3a-7f2d1f7ea4cc

        @expectedresults: 3 Host Collections created, no action taken on 2nd
        Import

        """
        for test_data in gen_import_hostcol_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                Import.host_collection({'csv-file': files['system-groups']})
                hcollections_before = [
                    HostCollection.list({'organization-id': tr['sat6']})
                    for tr in import_org[1]
                ]
                self.assertNotEqual(hcollections_before, [])
                Import.host_collection({'csv-file': files['system-groups']})
                hcollections_after = [
                    HostCollection.list({'organization-id': tr['sat6']})
                    for tr in import_org[1]
                ]
                self.assertEqual(hcollections_before, hcollections_after)
                clean_transdata()

    @tier1
    def test_positive_import_host_collections_recovery(self):
        """Try to Import Collections with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @id: e0520f6b-64c3-4263-8064-9ec5ba7eb2f5

        @expectedresults: 2nd Import will rename the new collections, 3nd
        import will result in No Action Taken and the 4th one will map them

        """
        for test_data in gen_import_hostcol_data():
            with self.subTest(test_data):
                # prepare the data
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # initial import
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users']
                })
                Import.host_collection_with_tr_data({
                    'csv-file': files['system-groups'],
                })
                # clear the .transition_data to clear the transition mapping
                ssh.command(
                    'rm -rf "${HOME}"/.transition_data/host_collections*'
                )
                # use the default (rename) strategy
                import_hc_rename = Import.host_collection_with_tr_data({
                    'csv-file': files['system-groups'],
                    'verbose': True,
                })
                for record in import_hc_rename[1]:
                    HostCollection.info({'id': record['sat6']})
                Import.host_collection({
                    'csv-file': files['system-groups'],
                    'delete': True,
                })
                # use the 'none' strategy
                hc_before = [
                    HostCollection.list({'organization-id': tr['sat6']})
                    for tr in import_org[1]
                ]
                Import.host_collection({
                    'csv-file': files['system-groups'], 'recover': 'none',
                })
                hc_after = [
                    HostCollection.list({'organization-id': tr['sat6']})
                    for tr in import_org[1]
                ]
                self.assertEqual(hc_before, hc_after)

                # use the 'map' strategy
                import_hc_map = Import.host_collection_with_tr_data({
                    'csv-file': files['system-groups'],
                    'recover': 'map',
                    'verbose': True,
                })
                for record in import_hc_map[1]:
                    HostCollection.info({'id': record['sat6']})
                clean_transdata()

    @tier1
    def test_positive_import_repo_default(self):
        """Import and enable all Repositories from the default data set
        (predefined source)

        @id: ae506d6c-a24b-4d27-85a0-9a3791684e6f

        @expectedresults: 3 Repositories imported and enabled

        """
        for test_data in gen_import_repo_data():
            with self.subTest(test_data):
                # randomize the values for orgs and repos
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                # now proceed with importing the repositories
                Import.repository_with_tr_data({
                    'csv-file': files['repositories'],
                    'synchronize': True,
                    'wait': True,
                })
                # get the sat6 mapping of the imported organizations
                imp_orgs = get_sat6_id(
                    Import.csv_to_dataset([files['users']]),
                    import_org[1]
                )
                # now to check whether all repos from csv appeared in satellite
                for imp_org in imp_orgs:
                    self.assertNotEqual(
                        Repository.list({'organization-id': imp_org['sat6']}),
                        [],
                    )
                clean_transdata()

    @tier1
    def test_negative_reimport_repo(self):
        """Import and enable all Repositories from the default data set
        (predefined source), then try to Import Repositories from the same CSV
        again.

        @id: 75d5cd18-fe73-4a2c-8036-4a60dab7a729

        @expectedresults: 3 Repositories imported and enabled, second run
        should trigger no action.
        """
        for test_data in gen_import_repo_data():
            with self.subTest(test_data):
                # randomize the values for orgs and repos
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                # now proceed with importing the repositories
                Import.repository_with_tr_data({
                    'csv-file': files['repositories'],
                    'synchronize': True,
                    'wait': True,
                })
                # get the sat6 mapping of the imported organizations
                imp_orgs = get_sat6_id(
                    Import.csv_to_dataset([files['users']]),
                    import_org[1]
                )
                repos_before = [
                    Repository.list({'organization-id': imp_org['sat6']})
                    for imp_org in imp_orgs
                ]
                # Reimport the same repos and check for changes in sat6
                Import.repository({
                    'csv-file': files['repositories'],
                    'synchronize': True,
                    'wait': True,
                })
                self.assertEqual(
                    repos_before,
                    [
                        Repository.list({'organization-id': imp_org['sat6']})
                        for imp_org in imp_orgs
                    ]
                )
                clean_transdata()

    @tier1
    def test_positive_import_repo_recovery(self):
        """Try to Import Repos with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @id: 6ab9d08f-74e6-488d-932c-1ef0fca319d9

        @expectedresults: 2nd Import will rename the new repos, 3rd import will
        map them and the 4th one will result in No Action Taken

        """
        for test_data in gen_import_repo_data():
            with self.subTest(test_data):
                # prepare the data
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                Import.repository_with_tr_data({
                    'csv-file': files['repositories'],
                })
                # clear the .transition_data to clear the transition mapping
                ssh.command('rm -rf "${HOME}"/.transition_data/repositories*')
                ssh.command('rm -rf "${HOME}"/.transition_data/products*')

                # use the default (rename) strategy
                import_repo_rename = Import.repository_with_tr_data({
                    'csv-file': files['repositories'], 'verbose': True,
                })
                for record in import_repo_rename[1][1]:
                    Repository.info({'id': record['sat6']})
                Import.repository({
                    'csv-file': files['repositories'], 'delete': True,
                })

                # use the 'none' strategy
                repos_before = [
                    Repository.list({'organization-id': tr['sat6']})
                    for tr in import_org[1]
                ]
                Import.repository({
                    'csv-file': files['repositories'],
                    'recover': 'none',
                })
                self.assertEqual(
                    repos_before,
                    [Repository.list({'organization-id': tr['sat6']})
                        for tr in import_org[1]],
                )

                # use the 'map' strategy
                import_repo_map = Import.repository_with_tr_data({
                    'csv-file': files['repositories'],
                    'recover': 'map',
                    'verbose': True,
                })
                for record in import_repo_map[1][1]:
                    Repository.info({'id': record['sat6']})
                clean_transdata()

    @tier1
    def test_positive_import_cv_default(self):
        """Import and enable all Content Views from the default data set
        (predefined source)

        @id: 6c42e82f-4939-41bb-9445-cf9ea4a5d3ab

        @expectedresults: 3 Content Views imported and enabled

        """
        for test_data in gen_import_cv_data():
            with self.subTest(test_data):
                # randomize the values for orgs and repos
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                Import.repository_with_tr_data({
                    'csv-file': files['repositories'],
                    'synchronize': True,
                    'wait': True,
                })
                # now proceed with Content View import
                Import.content_view_with_tr_data({
                    'csv-file': files['custom-channels'],
                    'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
                })

                # get the sat6 mapping of the imported organizations
                imp_orgs = get_sat6_id(
                    Import.csv_to_dataset([files['users']]),
                    import_org[1]
                )
                # now check whether all CVs from csv are imported
                for imp_org in imp_orgs:
                    self.assertNotEqual(
                        ContentView.list({'organization-id': imp_org['sat6']}),
                        []
                    )
                clean_transdata()

    @tier1
    def test_negative_reimport_cv(self):
        """Import and enable all Content Views from the default data set
        (predefined source), then try to Import them from the same CSV
        again.

        @id: ad600c5b-057e-45b5-be67-ab6a338f9fef

        @expectedresults: 3 Content Views imported and enabled, 2nd run should
        trigger no action.

        """
        for test_data in gen_import_cv_data():
            with self.subTest(test_data):
                # randomize the values for orgs and repos
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                Import.repository_with_tr_data({
                    'csv-file': files['repositories'],
                    'synchronize': True,
                    'wait': True,
                })
                Import.content_view_with_tr_data({
                    'csv-file': files['custom-channels'],
                    'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
                })
                # WONTFIX if affected_by_bz('1263650'):
                wait_for_publish()
                # get the sat6 mapping of the imported organizations
                imp_orgs = get_sat6_id(
                    Import.csv_to_dataset([files['users']]),
                    import_org[1]
                )
                cvs_before = [
                    ContentView.list({'organization-id': imp_org['sat6']})
                    for imp_org in imp_orgs
                ]
                # Reimport the same content views and check for changes in sat6
                Import.content_view({
                    'csv-file': files['custom-channels'],
                    'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
                })
                self.assertEqual(
                    cvs_before,
                    [
                        ContentView.list({'organization-id': imp_org['sat6']})
                        for imp_org in imp_orgs
                    ]
                )
                clean_transdata()

    @tier1
    def test_positive_import_cv_recovery(self):
        """Try to Import Content Views with the same name to invoke
        usage of a recovery strategy (rename, map, none)

        @id: 29bd0728-ae3c-4866-b9db-6b033ec36b2f

        @expectedresults: 2nd Import will rename the new Content Views, 3rd
        import will map them and the 4th one will result in No Action Taken

        """
        for test_data in gen_import_cv_data():
            with self.subTest(test_data):
                # prepare the data
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                Import.repository_with_tr_data({
                    'csv-file': files['repositories'],
                })
                Import.content_view_with_tr_data({
                    'csv-file': files['custom-channels'],
                    'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
                })
                # clear the .transition_data to clear the transition mapping
                ssh.command('rm -rf "${HOME}"/.transition_data/repositories*')
                ssh.command('rm -rf "${HOME}"/.transition_data/products*')
                ssh.command('rm -rf "${HOME}"/.transition_data/content_views*')

                # use the default (rename) strategy
                import_cv_rename = Import.content_view_with_tr_data({
                    'csv-file': files['custom-channels'],
                    'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
                    'verbose': True,
                })
                for record in import_cv_rename[1]:
                    ContentView.info({'id': record['sat6']})
                Import.content_view({
                    'csv-file': files['custom-channels'],
                    'delete': True,
                })

                # use the 'none' strategy
                cvs_before = [
                    ContentView.list({'organization-id': tr['sat6']})
                    for tr in import_org[1]
                ]
                Import.content_view({
                    'csv-file': files['custom-channels'],
                    'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
                    'recover': 'none',
                })
                cvs_after = [
                    ContentView.list({'organization-id': tr['sat6']})
                    for tr in import_org[1]
                ]
                self.assertEqual(cvs_before, cvs_after)

                # use the 'map' strategy
                import_cvs_map = Import.content_view_with_tr_data({
                    'csv-file': files['custom-channels'],
                    'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
                    'recover': 'map',
                    'verbose': True,
                })
                for record in import_cvs_map[1]:
                    ContentView.info({'id': record['sat6']})
                clean_transdata()

    @skip_if_bug_open('bugzilla', 1325880)
    @tier1
    def test_positive_translate_macros(self):
        """Check whether all supported Sat5 macros are being properly
        converted to the Puppet facts.
        According to RH Transition Guide (Chapter 3.7.8, Table 3.1)

        @id: 1e6d2979-1187-4f54-a7f7-84349afc1db4

        @expectedresults: Generated .erb file contains correctly formatted
        puppet facts

        """
        # This bug was originally created to verify BZ 1160847
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
            u'contents': u'{0}\n'.format(csv_contents),
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
        if affected_by_bz(1226981):
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
        Import.config_file({
            u'csv-file': file_name,
            u'generate-only': True,
        })
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
        clean_transdata()

    @tier3
    def test_positive_import_enable_rh_repos(self):
        """Import and enable all red hat repositories from predefined
        dataset

        @id: 6b5c8955-979b-4852-b401-b2c534631dce

        @expectedresults: All Repositories imported and synchronized


        @CaseLevel: System
        """
        for test_data in gen_import_rh_repo_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(dict(files), test_data, tmp_dir)
                rh_repos = [
                    repo for repo in Import.csv_to_dataset([files['channels']])
                    if (
                        repo['channel_name'].startswith('Red Hat') or
                        repo['channel_name'].startswith('RHN')
                    )
                ]
                # import the prerequisities (organizations with manifests)
                import_org = Import.organization_with_tr_data_manifests({
                    'csv-file': files['users'],
                })
                Import.repository_enable_with_tr_data({
                    'csv-file': files['channels'],
                    'synchronize': True,
                    'wait': True,
                })
                # verify rh repos appended in every imported org
                for record in product(rh_repos, import_org[1]):
                    self.assertNotEqual(
                        Repository.list({
                            u'organization-id': record[1]['sat6'],
                            u'name':  Import.repos[record[0]['channel_label']]
                        }),
                        []
                    )
                    self.assertNotEqual(
                        ContentView.info({
                            u'organization-id': record[1]['sat6'],
                            u'name': record[0]['channel_name']
                        }),
                        []
                    )
                clean_transdata()

    @tier3
    def test_negative_reimport_enable_rh_repos(self):
        """Repetitive Import and enable of all red hat repositories from
        the predefined dataset

        @id: ca345863-8e94-463e-bc06-b217ecb1189f

        @expectedresults: All Repositories imported and synchronized only once


        @CaseLevel: System
        """
        for test_data in gen_import_rh_repo_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities (organizations with manifests)
                import_org = Import.organization_with_tr_data_manifests({
                    'csv-file': files['users'],
                })
                Import.repository_enable({
                    'csv-file': files['channels'],
                    'synchronize': True,
                    'wait': True,
                })
                # verify rh repos appended in every imported org
                repos_before, cvs_before = verify_rh_repos(
                    import_org[1], files['channels']
                )
                self.assertFalse([] in repos_before)
                self.assertFalse([] in cvs_before)
                Import.repository_enable({
                    'csv-file': files['channels'],
                    'synchronize': True,
                    'wait': True,
                })
                # compare after and before to make sure
                # nothing has changed after 2nd import
                self.assertEqual(
                    (repos_before, cvs_before),
                    verify_rh_repos(
                        import_org[1], files['channels']
                    )
                )
                clean_transdata()

    @skip_if_bug_open('bugzilla', 1238247)
    @tier1
    def test_positive_import_chosts_default(self):
        """Import all content hosts from
        the predefined dataset

        @id: 90662be7-335f-43a4-816c-b6bb906614fd

        @expectedresults: Profiles for all Content Hosts created

        """
        for test_data in gen_import_chost_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisites and content hosts
                imports = import_content_hosts(files, tmp_dir)
                # get the sat6 mapping of the imported organizations
                imp_orgs = get_sat6_id(
                    Import.csv_to_dataset([files['users']]),
                    imports['organizations'][1]
                )
                # now to check whether all cont. hosts appeared in satellite
                for imp_org in imp_orgs:
                    self.assertNotEqual(
                        ContentHost.list({'organization-id': imp_org['sat6']}),
                        []
                    )
                clean_transdata()

    @skip_if_bug_open('bugzilla', 1238247)
    @tier1
    def test_negative_reimport_chosts(self):
        """Repetitive Import of all content hosts from
        the predefined dataset

        @id: b98ef26e-e938-40c2-805d-6292b12b64d5

        @expectedresults: Profiles for all Content Hosts created only once

        """
        for test_data in gen_import_chost_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisites and content hosts
                imports = import_content_hosts(files, tmp_dir)
                # get the sat6 mapping of the imported organizations
                imp_orgs = get_sat6_id(
                    Import.csv_to_dataset([files['users']]),
                    imports['organizations'][1]
                )
                chosts_before = [
                    ContentHost.list({'organization-id': imp_org['sat6']})
                    for imp_org in imp_orgs
                ]
                Import.content_host_with_tr_data({
                    u'csv-file': files['system-profiles'],
                    u'export-directory': tmp_dir,
                    u'verbose': True
                })
                self.assertEqual(
                    [
                        ContentHost.list({'organization-id': imp_org['sat6']})
                        for imp_org in imp_orgs
                    ],
                    chosts_before
                )
                clean_transdata()

    @skip_if_bug_open('bugzilla', 1238247)
    @skip_if_bug_open('bugzilla', 1267224)
    @tier1
    def test_negative_import_chosts_recovery(self):
        """Try to invoke usage of a recovery strategy

        @id: 29d59eab-2f30-4812-82ba-ca4c49439da5

        @expectedresults: No such option exists, error is shown

        """
        for test_data in gen_import_chost_data():
            with self.subTest(test_data):
                # prepare the data
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                import_content_hosts(files, tmp_dir)
                # clear the .transition_data to clear the transition mapping
                ssh.command(
                    'rm -rf "${{HOME}}"/.transition_data/{{system*,hosts*}} '
                    '{0}/SOURCES {0}/SPECS'
                    .format(tmp_dir)
                )
                # use the rename strategy
                with self.assertRaises(CLIReturnCodeError):
                    Import.content_host_with_tr_data({
                        u'csv-file': files['system-profiles'],
                        u'export-directory': tmp_dir,
                        u'recover': u'rename',
                    })
                clean_transdata()

    @tier1
    def test_positive_import_snippets_default(self):
        """Import template snippets from the default data set
        (predefined source)

        @id: fcced407-4e94-49ae-ab5a-8e868aee6625

        @expectedresults: All Snippets imported

        """
        for test_data in gen_import_snippet_data():
            with self.subTest(test_data):
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                # randomize the values for orgs and snippets
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                Import.organization_with_tr_data({'csv-file': files['users']})
                # list and save templates before import
                before = Template.list()
                # now proceed with importing the template snippets
                import_snippet = Import.template_snippet_with_tr_data({
                    'csv-file': files['kickstart-scripts'],
                    'verbose': True,
                })
                # list and save templates after import
                after = Template.list()
                # difference between before and after import
                diff = [d for d in after if d not in before]
                diff_ids = [d[u'id'] for d in diff]
                mapping = import_snippet[1][0]
                # check that snippets have been properly imported
                for row in mapping:
                    template = Template.info({u'id': row[u'sat6']})
                    self.assertTrue(template[u'id'] in diff_ids)
                    self.assertTrue(template[u'type'] == u'snippet')
                clean_transdata()

    @skip_if_bug_open('bugzilla', 1325880)
    @tier1
    def test_positive_import_config_files_default(self):
        """Import all Config Files from the default data set
        (predefined source)

        @id: 760393d2-b4c5-48ec-96ff-8947dd3bca62

        @expectedresults: All Config Files are imported

        """
        for test_data in gen_import_config_files_data():
            with self.subTest(test_data):
                # randomize the values for orgs and repos
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                Import.organization_with_tr_data(
                    {'csv-file': files['users']}
                )
                # now proceed with Config Files import
                import_cf = Import.config_file_with_tr_data({
                    'csv-file': files['config-files-latest'],
                    'verbose': True,
                })
                configs = Import.csv_to_dataset([files['config-files-latest']])
                imp_configs = get_sat6_id(
                    configs,
                    import_cf[1][1],
                    'channel_id',
                    'channel_id'
                )
                for rec in imp_configs:
                    self.assertEqual(
                        rec['channel'],
                        Repository.info({'id': rec['sat6']})['name']
                    )
                clean_transdata()

    @skip_if_bug_open('bugzilla', 1325880)
    @tier1
    def test_negative_reimport_config_files(self):
        """Repetitive Import of all Config Files from the default
        data set (predefined source)

        @id: 8b3d2956-c842-4a91-bf3e-6dcda174bd5f

        @expectedresults: All Config Files are imported only once

        """
        for test_data in gen_import_config_files_data():
            with self.subTest(test_data):
                # randomize the values for orgs and repos
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                Import.organization_with_tr_data(
                    {'csv-file': files['users']}
                )
                # initial import
                import_cf = Import.config_file_with_tr_data({
                    'csv-file': files['config-files-latest'],
                    'verbose': True,
                })
                configs = Import.csv_to_dataset([files['config-files-latest']])
                imp_configs = get_sat6_id(
                    configs,
                    import_cf[1][1],
                    'channel_id',
                    'channel_id'
                )
                cf_before = [
                    Repository.info({'id': rec['sat6']})
                    for rec in imp_configs
                ]
                # sequential import
                import_cf = Import.config_file_with_tr_data({
                    'csv-file': files['config-files-latest'],
                    'verbose': True,
                })
                configs = Import.csv_to_dataset([files['config-files-latest']])
                imp_configs = get_sat6_id(
                    configs,
                    import_cf[1][1],
                    'channel_id',
                    'channel_id'
                )
                cf_after = [
                    Repository.info({'id': rec['sat6']})
                    for rec in imp_configs
                ]
                self.assertEqual(cf_before, cf_after)
                clean_transdata()

    @skip_if_bug_open('bugzilla', 1325124)
    @tier1
    def test_positive_import_ak_default(self):
        """Import AKs from the default data set
        (predefined source)

        @id: 86b35ce4-c51d-4391-98c9-9dd0ff50963a

        @expectedresults: 3 AKs imported

        """
        for test_data in gen_import_ak_data():
            with self.subTest(test_data):
                # randomize the values for orgs and repos
                tmp_dir = self.default_dataset[0]
                files = dict(self.default_dataset[1])
                files = update_csv_values(files, test_data, tmp_dir)
                # import the prerequisities
                import_org = Import.organization_with_tr_data({
                    'csv-file': files['users'],
                })
                map_orgs = import_org[1]
                Import.host_collection_with_tr_data({
                    'csv-file': files['system-groups'],
                    'verbose': True,
                })
                Import.repository_with_tr_data({
                    'csv-file': files['repositories'],
                    'verbose': True,
                    'synchronize': True,
                    'wait': True,
                })
                Import.content_view_with_tr_data({
                    'csv-file': files['custom-channels'],
                    'dir': os.path.join(tmp_dir, 'exports/CHANNELS'),
                    'verbose': True,
                })
                # list and save AKs before import
                aks_before = [
                    ak for row in map_orgs
                    for ak in ActivationKey.list(
                        {'organization-id': row[u'sat6']})
                ]
                # now proceed with AK import
                import_ak = Import.activation_key_with_tr_data({
                    'csv-file': files['activation-keys'],
                    'verbose': True,
                })
                map_aks = import_ak[1]
                # list and save AKs after import
                aks_after = [
                    ak for row in map_orgs
                    for ak in ActivationKey.list(
                        {'organization-id': row[u'sat6']})
                ]
                # difference between before and after import
                aks_diff = [d for d in aks_after if d not in aks_before]
                diff_ids = [d[u'id'] for d in aks_diff]
                # now check whether all AKs from csv are imported
                for row in map_aks:
                    ak = ActivationKey.info({u'id': row[u'sat6']})
                    self.assertTrue(ak[u'id'] in diff_ids)
                for row in map_orgs:
                    self.assertNotEqual(
                        ActivationKey.list({'organization-id': row['sat6']}),
                        []
                    )
                clean_transdata()
