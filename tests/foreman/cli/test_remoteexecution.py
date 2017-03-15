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
from robottelo.cleanup import vm_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    make_content_view,
    make_job_invocation,
    make_job_template,
    make_lifecycle_environment,
    make_org,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.job_template import JobTemplate
from robottelo.config import settings
from robottelo.constants import (
    DISTRO_RHEL7,
    PRDS,
    REPOS,
    REPOSET
)
from robottelo.datafactory import invalid_values_list
from robottelo.decorators import (
    skip_if_not_set,
    tier1,
    tier2,
    tier3
)
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
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key
        """
        super(RemoteExecutionTestCase, cls).setUpClass()
        cls.org = make_org()
        ssh.command(
            '''echo 'getenforce' > {0}'''.format(TEMPLATE_FILE)
        )
        cls.env = make_lifecycle_environment({
            u'organization-id': cls.org['id'],
        })
        cls.content_view = make_content_view({
            u'organization-id': cls.org['id'],
        })
        cls.activation_key = make_activation_key({
            u'lifecycle-environment-id': cls.env['id'],
            u'organization-id': cls.org['id'],
        })
        if settings.cdn:
            # Add subscription to Satellite Tools repo to activation key
            setup_org_for_a_rh_repo({
                u'product': PRDS['rhel'],
                u'repository-set': REPOSET['rhst7'],
                u'repository': REPOS['rhst7']['name'],
                u'organization-id': cls.org['id'],
                u'content-view-id': cls.content_view['id'],
                u'lifecycle-environment-id': cls.env['id'],
                u'activationkey-id': cls.activation_key['id'],
            })
        else:
            # Create custom internal Tools repo, add to activation key
            setup_org_for_a_custom_repo({
                u'url': settings.sattools_repo,
                u'organization-id': cls.org['id'],
                u'content-view-id': cls.content_view['id'],
                u'lifecycle-environment-id': cls.env['id'],
                u'activationkey-id': cls.activation_key['id'],
            })

    def setUp(self):
        """Create VM, subscribe it to satellite-tools repo, install katello-ca
        and katello-agent packages, add remote execution key
        """
        super(RemoteExecutionTestCase, self).setUp()
        # Create VM and register content host
        self.client = VirtualMachine(distro=DISTRO_RHEL7)
        self.addCleanup(vm_cleanup, self.client)
        self.client.create()
        self.client.install_katello_ca()
        # Register content host, install katello-agent
        self.client.register_contenthost(
            self.org['label'],
            self.activation_key['name'],
        )
        if settings.cdn:
            self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_agent()
        add_remote_execution_ssh_key(self.client.ip_addr)

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
        JobInvocation.get_output({
             'id': invocation_command[u'id'],
             'host': self.client.hostname
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
            u'organizations': self.org['name'],
            u'name': template_name,
            u'file': TEMPLATE_FILE
        })
        invocation_command = make_job_invocation({
            'job-template': template_name,
            'search-query': "name ~ {0}".format(self.client.hostname),
        })
        JobInvocation.get_output({
             'id': invocation_command[u'id'],
             'host': self.client.hostname
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
        # Wait unitl the job runs
        pending_state = u'1'
        while pending_state != u'0':
            invocation_info = JobInvocation.info({
                'id': invocation_command[u'id']})
            pending_state = invocation_info[u'pending']
            sleep(30)
        # Check the job status
        JobInvocation.get_output({
             'id': invocation_command[u'id'],
             'host': self.client.hostname
        })
        invocation_info = JobInvocation.info({
            'id': invocation_command[u'id']})
        self.assertEqual(invocation_info[u'success'], u'1')
