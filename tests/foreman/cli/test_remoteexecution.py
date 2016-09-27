# -*- encoding: utf-8 -*-
"""Test class for Remote Execution Management UI

@Requirement: Remoteexecution

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from datetime import datetime, timedelta
from fauxfactory import gen_string
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_job_invocation,
    make_job_template,
    make_org
)
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.job_template import JobTemplate
from robottelo.constants import DISTRO_RHEL7, REPOS
from robottelo.datafactory import invalid_values_list
from robottelo.decorators import tier1, tier2, tier3
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine
from time import sleep

TEMPLATE_FILE = u'template_file.txt'
TEMPLATE_FILE_EMPTY = u'template_file_empty.txt'


class JobTemplateTestCase(CLITestCase):
    """Implements job template tests in CLI."""

    @classmethod
    def setUpClass(cls):
        """Create an organization to be reused in tests."""
        super(JobTemplateTestCase, cls).setUpClass()
        cls.organization = make_org()
        ssh.command(
            '''echo '<%= input("command") %>' > {0}'''.format(TEMPLATE_FILE)
        )
        ssh.command('touch {0}'.format(TEMPLATE_FILE_EMPTY))

    @tier1
    def test_positive_create_job_template(self):
        """Create a simple Job Template

        @id: a5a67b10-61b0-4362-b671-9d9f095c452c

        @Assert: The job template was successfully created
        """
        template_name = gen_string('alpha', 7)
        make_job_template({
            u'organizations': self.organization['name'],
            u'name': template_name,
            u'file': TEMPLATE_FILE
        })
        self.assertIsNotNone(
            JobTemplate.info({u'name': template_name})
        )

    @tier1
    def test_negative_create_job_template_with_invalid_name(self):
        """Create Job Template with invalid name

        @id: eb51afd4-e7b3-42c3-81c3-6e18ef3d7efe

        @Assert: Job Template with invalid name cannot be created and error is
        raised
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaisesRegex(
                    CLIFactoryError,
                    u'Could not create the job template:'
                ):
                    for name in invalid_values_list():
                        make_job_template({
                            u'organizations': self.organization['name'],
                            u'name': name,
                            u'file': TEMPLATE_FILE
                        })

    @tier1
    def test_negative_create_job_template_with_same_name(self):
        """Create Job Template with duplicate name

        @id: 66100c82-97f5-4300-a0c9-8cf041f7789f

        @Assert: The name duplication is caught and error is raised
        """
        template_name = gen_string('alpha', 7)
        make_job_template({
            u'organizations': self.organization['name'],
            u'name': template_name,
            u'file': TEMPLATE_FILE
        })
        with self.assertRaisesRegex(
            CLIFactoryError,
            u'Could not create the job template:'
        ):
            make_job_template({
                u'organizations': self.organization['name'],
                u'name': template_name,
                u'file': TEMPLATE_FILE
            })

    @tier1
    def test_negative_create_empty_job_template(self):
        """Create Job Template with empty template file

        @id: 749be863-94ae-4008-a242-c23f353ca404

        @Assert: The empty file is detected and error is raised
        """
        template_name = gen_string('alpha', 7)
        with self.assertRaisesRegex(
            CLIFactoryError,
            u'Could not create the job template:'
        ):
            make_job_template({
                u'organizations': self.organization['name'],
                u'name': template_name,
                u'file': TEMPLATE_FILE_EMPTY
            })

    @tier1
    def test_positive_delete_job_template(self):
        """Delete a job template

        @id: 33104c04-20e9-47aa-99da-4bf3414ea31a

        @Assert: The Job Template has been deleted
        """
        template_name = gen_string('alpha', 7)
        make_job_template({
            u'organizations': self.organization['name'],
            u'name': template_name,
            u'file': TEMPLATE_FILE
        })
        JobTemplate.delete({u'name': template_name})
        with self.assertRaises(CLIReturnCodeError):
            JobTemplate.info({u'name': template_name})

    @tier1
    def test_positive_view_dump(self):
        """Export contents of a job template

        @id: 25fcfcaa-fc4c-425e-919e-330e36195c4a

        @Assert: Verify no errors are thrown
        """
        template_name = gen_string('alpha', 7)
        make_job_template({
            u'organizations': self.organization['name'],
            u'name': template_name,
            u'file': TEMPLATE_FILE
        })
        dumped_content = JobTemplate.dump({u'name': template_name})
        self.assertGreater(len(dumped_content), 0)


class RemoteExecutionTestCase(CLITestCase):
    """Implements job execution tests in CLI."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(RemoteExecutionTestCase, cls).setUpClass()
        cls.organization = make_org()
        ssh.command(
            '''echo 'getenforce' > {0}'''.format(TEMPLATE_FILE)
        )
        cls.client = VirtualMachine(distro=DISTRO_RHEL7)
        cls.client.create()
        cls.client.install_katello_ca()
        cls.client.register_contenthost(
            cls.organization['label'],
            lce='Library'
        )
        cls.client.enable_repo(REPOS['rhst7']['id'])
        cls.client.install_katello_agent()
        add_remote_execution_ssh_key(cls.client.hostname)

    @classmethod
    def tearDownClass(cls):
        """Remove the VM used for testing remote execution"""
        cls.client.destroy()
        super(RemoteExecutionTestCase, cls).tearDownClass()

    @tier2
    def test_positive_run_default_job_template(self):
        """Run default job template against a single host

        @id: f4470ed4-f971-4a3c-a2f1-150d45755e48

        @Assert: Verify the job was successfully ran against the host
        """
        invocation_command = make_job_invocation({
            'job-template': 'Run Command - SSH Default',
            'inputs': 'command="ls"',
            'search-query': "name ~ {0}".format(self.client.hostname),
        })
        self.assertEqual(invocation_command['success'], u'1')

    @tier2
    def test_positive_run_custom_job_template(self):
        """Run custom job template against a single host

        @id: 71928f36-61b4-46e6-842c-a051cfd9a68e

        @Assert: Verify the job was successfully ran against the host
        """
        template_name = gen_string('alpha', 7)
        make_job_template({
            u'organizations': self.organization[u'name'],
            u'name': template_name,
            u'file': TEMPLATE_FILE
        })
        invocation_command = make_job_invocation({
            'job-template': template_name,
            'search-query': "name ~ {0}".format(self.client.hostname),
        })
        self.assertEqual(invocation_command[u'success'], u'1')

    @tier3
    def test_positive_run_scheduled_job_template(self):
        """Schedule a job to be ran against a host

        @id: 1953517b-6908-40aa-858b-747629d2f374

        @Assert: Verify the job was successfully ran after the designated time
        """
        system_current_time = ssh.command('date +"%b %d %Y %I:%M%p"').stdout[0]
        current_time_object = datetime.strptime(
            system_current_time, '%b %d %Y %I:%M%p')
        plan_time = (current_time_object + timedelta(seconds=30)).strftime(
            "%Y-%m-%d %H:%M")
        invocation_command = make_job_invocation({
            'job-template': 'Run Command - SSH Default',
            'inputs': 'command="ls"',
            'start-at': plan_time,
            'search-query': "name ~ {0}".format(self.client.hostname),
        })
        for _ in range(5):
            try:
                invocation_info = JobInvocation.info({
                    'id': invocation_command[u'id']})
                self.assertEqual(invocation_info[u'success'], u'1')
            except AssertionError:
                sleep(30)
