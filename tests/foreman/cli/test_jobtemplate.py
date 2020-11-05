"""Test class for Remote Execution Management UI

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
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
from robottelo.test import CLITestCase

TEMPLATE_FILE = 'template_file.txt'
TEMPLATE_FILE_EMPTY = 'template_file_empty.txt'


class JobTemplateTestCase(CLITestCase):
    """Implements job template tests in CLI."""

    @classmethod
    def setUpClass(cls):
        """Create an organization to be reused in tests."""
        super().setUpClass()
        cls.organization = make_org()
        ssh.command(f'''echo '<%= input("command") %>' > {TEMPLATE_FILE}''')
        ssh.command(f'touch {TEMPLATE_FILE_EMPTY}')

    @pytest.mark.tier1
    def test_positive_create_job_template(self):
        """Create a simple Job Template

        :id: a5a67b10-61b0-4362-b671-9d9f095c452c

        :expectedresults: The job template was successfully created

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha', 7)
        make_job_template(
            {
                'organizations': self.organization['name'],
                'name': template_name,
                'file': TEMPLATE_FILE,
            }
        )
        self.assertIsNotNone(JobTemplate.info({'name': template_name}))

    @pytest.mark.tier1
    def test_negative_create_job_template_with_invalid_name(self):
        """Create Job Template with invalid name

        :id: eb51afd4-e7b3-42c3-81c3-6e18ef3d7efe

        :expectedresults: Job Template with invalid name cannot be created and
            error is raised

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaisesRegex(CLIFactoryError, 'Could not create the job template:'):
                    make_job_template(
                        {
                            'organizations': self.organization['name'],
                            'name': name,
                            'file': TEMPLATE_FILE,
                        }
                    )

    @pytest.mark.tier1
    def test_negative_create_job_template_with_same_name(self):
        """Create Job Template with duplicate name

        :id: 66100c82-97f5-4300-a0c9-8cf041f7789f

        :expectedresults: The name duplication is caught and error is raised

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha', 7)
        make_job_template(
            {
                'organizations': self.organization['name'],
                'name': template_name,
                'file': TEMPLATE_FILE,
            }
        )
        with self.assertRaisesRegex(CLIFactoryError, 'Could not create the job template:'):
            make_job_template(
                {
                    'organizations': self.organization['name'],
                    'name': template_name,
                    'file': TEMPLATE_FILE,
                }
            )

    @pytest.mark.tier1
    def test_negative_create_empty_job_template(self):
        """Create Job Template with empty template file

        :id: 749be863-94ae-4008-a242-c23f353ca404

        :expectedresults: The empty file is detected and error is raised

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha', 7)
        with self.assertRaisesRegex(CLIFactoryError, 'Could not create the job template:'):
            make_job_template(
                {
                    'organizations': self.organization['name'],
                    'name': template_name,
                    'file': TEMPLATE_FILE_EMPTY,
                }
            )

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_delete_job_template(self):
        """Delete a job template

        :id: 33104c04-20e9-47aa-99da-4bf3414ea31a

        :expectedresults: The Job Template has been deleted

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha', 7)
        make_job_template(
            {
                'organizations': self.organization['name'],
                'name': template_name,
                'file': TEMPLATE_FILE,
            }
        )
        JobTemplate.delete({'name': template_name})
        with self.assertRaises(CLIReturnCodeError):
            JobTemplate.info({'name': template_name})

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier2
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
                'organizations': self.organization['name'],
                'name': template_name,
                'file': TEMPLATE_FILE,
            }
        )
        templates = JobTemplate.list({'organization-id': self.organization['id']})
        self.assertGreaterEqual(len(templates), 1)
        Defaults.add({'param-name': 'organization_id', 'param-value': self.organization['id']})
        Defaults.add({'param-name': 'location_id', 'param-value': location['id']})
        try:
            templates = JobTemplate.list()
            self.assertGreaterEqual(len(templates), 1)
        finally:
            Defaults.delete({'param-name': 'organization_id'})
            Defaults.delete({'param-name': 'location_id'})

    @pytest.mark.tier2
    def test_positive_view_dump(self):
        """Export contents of a job template

        :id: 25fcfcaa-fc4c-425e-919e-330e36195c4a

        :expectedresults: Verify no errors are thrown

        """
        template_name = gen_string('alpha', 7)
        make_job_template(
            {
                'organizations': self.organization['name'],
                'name': template_name,
                'file': TEMPLATE_FILE,
            }
        )
        dumped_content = JobTemplate.dump({'name': template_name})
        self.assertGreater(len(dumped_content), 0)
