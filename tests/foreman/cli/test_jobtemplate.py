# -*- encoding: utf-8 -*-
"""Test class for Remote Execution Management UI

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.defaults import Defaults
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_job_template
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.job_template import JobTemplate
from robottelo.datafactory import invalid_values_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase

TEMPLATE_FILE = u'template_file.txt'
TEMPLATE_FILE_EMPTY = u'template_file_empty.txt'


class JobTemplateTestCase(CLITestCase):
    """Implements job template tests in CLI."""

    @classmethod
    def setUpClass(cls):
        """Create an organization to be reused in tests."""
        super(JobTemplateTestCase, cls).setUpClass()
        cls.organization = make_org()
        ssh.command('''echo '<%= input("command") %>' > {0}'''.format(TEMPLATE_FILE))
        ssh.command('touch {0}'.format(TEMPLATE_FILE_EMPTY))

    @tier1
    def test_positive_create_job_template(self):
        """Create a simple Job Template

        :id: a5a67b10-61b0-4362-b671-9d9f095c452c

        :expectedresults: The job template was successfully created

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha', 7)
        make_job_template(
            {
                u'organizations': self.organization['name'],
                u'name': template_name,
                u'file': TEMPLATE_FILE,
            }
        )
        self.assertIsNotNone(JobTemplate.info({u'name': template_name}))

    @tier1
    def test_negative_create_job_template_with_invalid_name(self):
        """Create Job Template with invalid name

        :id: eb51afd4-e7b3-42c3-81c3-6e18ef3d7efe

        :expectedresults: Job Template with invalid name cannot be created and
            error is raised

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaisesRegex(
                    CLIFactoryError, u'Could not create the job template:'
                ):
                    make_job_template(
                        {
                            u'organizations': self.organization['name'],
                            u'name': name,
                            u'file': TEMPLATE_FILE,
                        }
                    )

    @tier1
    def test_negative_create_job_template_with_same_name(self):
        """Create Job Template with duplicate name

        :id: 66100c82-97f5-4300-a0c9-8cf041f7789f

        :expectedresults: The name duplication is caught and error is raised

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha', 7)
        make_job_template(
            {
                u'organizations': self.organization['name'],
                u'name': template_name,
                u'file': TEMPLATE_FILE,
            }
        )
        with self.assertRaisesRegex(CLIFactoryError, u'Could not create the job template:'):
            make_job_template(
                {
                    u'organizations': self.organization['name'],
                    u'name': template_name,
                    u'file': TEMPLATE_FILE,
                }
            )

    @tier1
    def test_negative_create_empty_job_template(self):
        """Create Job Template with empty template file

        :id: 749be863-94ae-4008-a242-c23f353ca404

        :expectedresults: The empty file is detected and error is raised

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha', 7)
        with self.assertRaisesRegex(CLIFactoryError, u'Could not create the job template:'):
            make_job_template(
                {
                    u'organizations': self.organization['name'],
                    u'name': template_name,
                    u'file': TEMPLATE_FILE_EMPTY,
                }
            )

    @tier1
    @upgrade
    def test_positive_delete_job_template(self):
        """Delete a job template

        :id: 33104c04-20e9-47aa-99da-4bf3414ea31a

        :expectedresults: The Job Template has been deleted

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha', 7)
        make_job_template(
            {
                u'organizations': self.organization['name'],
                u'name': template_name,
                u'file': TEMPLATE_FILE,
            }
        )
        JobTemplate.delete({u'name': template_name})
        with self.assertRaises(CLIReturnCodeError):
            JobTemplate.info({u'name': template_name})

    @run_in_one_thread
    @tier2
    def test_positive_list_job_template_with_saved_org_and_loc(self):
        """List available job templates with saved default organization and
        location in config

        :id: 4fd05dd7-53e3-41ba-ba90-6181a7190ad8

        :expectedresults: The Job Template can be listed without errors

        :BZ: 1368173
        """
        template_name = gen_string('alpha')
        location = make_location()
        make_job_template(
            {
                u'organizations': self.organization['name'],
                u'name': template_name,
                u'file': TEMPLATE_FILE,
            }
        )
        templates = JobTemplate.list({'organization-id': self.organization['id']})
        self.assertGreaterEqual(len(templates), 1)
        Defaults.add({u'param-name': 'organization_id', u'param-value': self.organization['id']})
        Defaults.add({u'param-name': 'location_id', u'param-value': location['id']})
        try:
            templates = JobTemplate.list()
            self.assertGreaterEqual(len(templates), 1)
        finally:
            Defaults.delete({u'param-name': 'organization_id'})
            Defaults.delete({u'param-name': 'location_id'})

    @tier2
    def test_positive_view_dump(self):
        """Export contents of a job template

        :id: 25fcfcaa-fc4c-425e-919e-330e36195c4a

        :expectedresults: Verify no errors are thrown

        """
        template_name = gen_string('alpha', 7)
        make_job_template(
            {
                u'organizations': self.organization['name'],
                u'name': template_name,
                u'file': TEMPLATE_FILE,
            }
        )
        dumped_content = JobTemplate.dump({u'name': template_name})
        self.assertGreater(len(dumped_content), 0)
