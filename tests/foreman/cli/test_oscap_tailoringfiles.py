# -*- encoding: utf-8 -*-
"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import os

from fauxfactory import gen_string

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_tailoringfile, CLIFactoryError
from robottelo.cli.scap_tailoring_files import TailoringFiles
from robottelo.config import settings
from robottelo.constants import SNIPPET_DATA_FILE
from robottelo.datafactory import (
    valid_data_list,
    invalid_names_list,
)
from robottelo.decorators import (
    stubbed,
    tier1,
    tier2,
    tier4,
    upgrade
)
from robottelo.helpers import get_data_file
from robottelo.test import CLITestCase


class TailoringFilesTestCase(CLITestCase):
    """Implements Tailoring Files tests in CLI."""

    @classmethod
    def setUpClass(cls):
        super(TailoringFilesTestCase, cls).setUpClass()
        _, cls.file_name = os.path.split(settings.oscap.tailoring_path)
        ssh.upload_file(
            local_file=settings.oscap.tailoring_path,
            remote_file="/tmp/{0}".format(cls.file_name)
        )

    @tier1
    def test_positive_create(self):
        """Create new Tailoring Files using different values types as name

        :id: e1bb4de2-1b64-4904-bc7c-f0befa9dbd6f

        :steps:

            1. Create valid tailoring file with valid parameter

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                tailoring_file = make_tailoringfile({
                    'name': name,
                    'scap-file': '/tmp/{0}'.format(self.file_name)})
                self.assertEqual(tailoring_file['name'], name)

    @tier1
    def test_positive_create_with_space(self):
        """Create tailoring files with space in name

        :id: c98ef4e7-41c5-4a8b-8a0b-8d53100b75a8

        :steps:

            1. Create valid tailoring file with space in name

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric') + ' ' + gen_string('alphanumeric')
        tailoring_file = make_tailoringfile({
            'name': name,
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        self.assertEqual(tailoring_file['name'], name)

    @tier1
    def test_positive_get_info_of_tailoring_file(self):
        """Get information of tailoring file

        :id: bc201194-e8c8-4385-a577-09f3455f5a4d

        :setup: tailoring file

        :steps:

            1. Create tailoring file with valid parameters
            2. Execute "tailoring-file" command with "info" as sub-command
               with valid parameter

        :expectedresults: Tailoring file information should be displayed

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        make_tailoringfile({
            'name': name,
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        result = TailoringFiles.info({'name': name})
        self.assertEqual(result['name'], name)

    @tier1
    def test_positive_list_tailoring_file(self):
        """List all created tailoring files

        :id: 2ea63c4b-eebe-468d-8153-807e86d1b6a2

        :setup: tailoring file

        :steps:

            1. Create different tailoring file with different valid name
            2. Execute "tailoring-file" command with "list" as sub-command

        :expectedresults: Tailoring files list should be displayed

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        make_tailoringfile({
            'name': name,
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        result = TailoringFiles.list()
        self.assertIn(
             name, [tailoringfile['name'] for tailoringfile in result])

    @tier1
    def test_negative_create_with_invalid_file(self):
        """Create Tailoring files with invalid file

        :id: 86f5ce13-856c-4e58-997f-fa21093edd04

        :steps:

            1. Attempt to create tailoring file with invalid file

        :expectedresults: Tailoring file will not be added to satellite

        :CaseImportance: Critical
        """
        ssh.upload_file(
            local_file=get_data_file(SNIPPET_DATA_FILE),
            remote_file='/tmp/{0}'.format(SNIPPET_DATA_FILE)
        )
        name = gen_string('alphanumeric')
        with self.assertRaises(CLIFactoryError):
            make_tailoringfile({
                'name': name,
                'scap-file': '/tmp/{0}'.format(SNIPPET_DATA_FILE)
            })

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Tailoring files with invalid name

        :id: 973eee82-9735-49bb-b534-0de619aa0279

        :steps:

            1. Attempt to create tailoring file with invalid name parameter

        :expectedresults: Tailoring file will not be added to satellite

        :CaseImportance: Critical
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_tailoringfile({
                        'name': name,
                        'scap-file': '/tmp/{0}'.format(self.file_name)})

    @stubbed()
    @tier2
    def test_negative_associate_tailoring_file_with_different_scap(self):
        """ Associate a tailoring file with different scap content

        :id: f36be738-eaa1-4f6b-aa6c-9924be5f1e96

        :steps:

            1. Execute "scap-content" command with "create" as sub-command
            2. Upload a Mutually exclusive tailoring file
            3. Associate the scap content with tailoring file

        :CaseAutomation: notautomated

        :expectedresults: Association should give some warning

        :CaseImportance: Critical
        """

    @tier2
    def test_positive_download_tailoring_file(self):

        """ Download the tailoring file from satellite

        :id: 75d8c810-19a7-4285-bc3a-a1fb1a0e9088

        :steps:

            1.Create valid tailoring file with valid name
            2.Execute "tailoring-file" command with "download" as sub-command

        :expectedresults: The tailoring file should be downloaded

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        file_path = '/tmp/{0}.xml'.format(name)
        tailoring_file = make_tailoringfile({
            'name': name,
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        self.assertEqual(tailoring_file['name'], name)
        result = TailoringFiles.download_tailoring_file({
            'name': name,
            'path': '/tmp/'
        })
        self.assertIn(file_path, result[0])
        result = ssh.command('find {0}'.format(file_path))
        self.assertEqual(result.return_code, 0)
        self.assertIn(file_path, result.stdout)

    @tier1
    @upgrade
    def test_positive_delete_tailoring_file(self):
        """ Delete tailoring file

        :id: 8bab5478-1ef1-484f-aafd-98e5cba7b1e7

        :steps:

            1. Create valid tailoring file with valid parameter
            2. Execute "tailoring-file" command with "delete" as sub-command

        :expectedresults: Tailoring file should be deleted

        :CaseImportance: Critical
        """
        tailoring_file = make_tailoringfile({
            'scap-file': '/tmp/{0}'.format(self.file_name)})
        TailoringFiles.delete({'id': tailoring_file['id']})
        with self.assertRaises(CLIReturnCodeError):
            TailoringFiles.info({'id': tailoring_file['id']})

    @stubbed()
    @tier4
    @upgrade
    def test_positive_oscap_run_with_tailoring_file_and_capsule(self):
        """ End-to-End Oscap run with tailoring files and default capsule

        :id: 91fd3ccd-6177-4efd-8842-73fd14f53a85

        :steps:

            1. Execute "scap-content" command with "create" as sub-command
            2. Execute "tailoring-file" command with "create" as sub-command
            3. Execute "policy" command with "create" as sub-command
            4. Associate scap content with it’s tailoring file
            5. Associate the policy with a hostgroup
            6. Provision a host using the hostgroup
            7. Puppet should configure and fetch the scap content
               and tailoring file

        :CaseAutomation: notautomated

        :expectedresults: ARF report should be sent to satellite reflecting
                         the changes done via tailoring files

        :CaseImportance: Critical
        """

    @stubbed()
    @tier4
    @upgrade
    def test_positive_oscap_run_with_tailoring_file_and_external_capsule(self):
        """ End-to-End Oscap run with tailoring files and external capsule

        :id: 39d2e690-8410-4cc7-b873-bb5f658148cc

        :steps:

            1. Execute "scap-content" command with "create" as sub-command
            2. Execute "tailoring-file" command with "create" as sub-command
            3. Execute "policy" command with "create" as sub-command
            4. Associate scap content with it’s tailoring file
            5. Associate the policy with a hostgroup
            6. Provision a host using the hostgroup
            7. Puppet should configure and fetch the scap content
               and tailoring file from external capsule

        :CaseAutomation: notautomated

        :expectedresults: ARF report should be sent to satellite
                         reflecting the changes done via tailoring files

        :CaseImportance: Critical
        """

    @stubbed()
    @tier4
    @upgrade
    def test_positive_fetch_tailoring_file_information_from_arfreports(self):
        """ Fetch Tailoring file Information from Arf-reports

        :id: d8fa1a05-db99-47a9-b1f5-12712a0b1378

        :steps:

            1. Execute "scap-content" command with "create" as sub-command
            2. Execute "tailoring-file" command with "create" as sub-command
            3. Execute "policy" command with "create" as sub-command
            4. Associate scap content with it’s tailoring file
            5. Associate the policy with a hostgroup
            6. Provision a host using the hostgroup
            7. Puppet should configure and fetch the scap content
               and send arf-report to satellite

        :CaseAutomation: notautomated

        :expectedresults: ARF report should have information
                          about the tailoring file used, if any

        :CaseImportance: Critical
        """
