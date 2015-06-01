# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI"""
import csv
import os
import tempfile
from ddt import ddt
from fauxfactory import gen_string
from robottelo.common import ssh
from robottelo.common.helpers import prepare_import_data
from robottelo.common.decorators import (
    bz_bug_is_open,
    skip_if_bug_open,
)
from robottelo.test import CLITestCase
from robottelo.cli.import_ import Import
from robottelo.cli.factory import make_org
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
        pwdfile = os.path.join(tmpdir, gen_string('alpha', 6))

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
        data = [
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
            u'{0}={1}'.format(i['name'], i['macro']) for i in data
        )
        csv_header = [
            u'org_id', u'channel_id', u'channel', u'channel_type', u'path',
            u'file_type', u'file_id', u'revision', u'is_binary', u'contents',
            u'delim_start', u'delim_end', u'username', u'groupname',
            u'filemode', u'symbolic_link', u'selinux_ctx'
        ]
        csv_row = [
            u'1', u'3', u'config-1', u'normal',
            u'/etc/sysconfig/rhn/systemid', u'file', u'8', u'1', u'N',
            csv_contents + u'\n',
            u'{|', u'|}', u'root', u'root', u'600', u'', u''
        ]

        file_name = tempfile.mkstemp()[1]
        with open(file_name, 'wb') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(csv_header)
            csv_writer.writerow(csv_row)

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
            [fact['name'] + '=' + fact['fact'] for fact in data],
        )
        # cleanup the remote part
        ssh.command(u'rm -rf $HOME/.transition_data ~/puppet_work_dir')
        ssh.command(u'rm -rf $HOME/{0}'.format(os.path.basename(file_name)))
