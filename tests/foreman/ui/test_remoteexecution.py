"""Test class for Remote Execution Management UI

@Requirement: Remoteexecution

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from datetime import datetime, timedelta
from nailgun import entities
from robottelo.constants import OS_TEMPLATE_DATA_FILE, DISTRO_RHEL7
from robottelo.datafactory import (
    gen_string,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import stubbed, tier1, tier2, tier3
from robottelo.helpers import add_remote_execution_ssh_key, get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_job_template, set_context
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine

OS_TEMPLATE_DATA_FILE = get_data_file(OS_TEMPLATE_DATA_FILE)


class JobsTemplateTestCase(UITestCase):
    """Test class for jobs template feature"""

    @classmethod
    def setUpClass(cls):
        """Create an organization and host which can be re-used in tests."""
        super(JobsTemplateTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.host = entities.Host(organization=cls.organization).create()
        entities.OperatingSystem(
            id=cls.host.operatingsystem.id, family='Redhat').update(['family'])

    @tier1
    def test_positive_create_simple_job_template(self):
        """Create a simple Job Template

        @id: 7cb1e5b0-5420-47c5-bb43-e2c58bed7a9d

        @Steps:

        1. Navigate to Hosts -> Job Templates
        2. Enter a valid name
        3. Populate the template code
        4. Navigate to the job tab
        5. Enter a job name
        6. Click submit

        @Assert: The job template was successfully created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_job_template(
                        session,
                        name=name,
                        template_type='input',
                        template_content=gen_string('alphanumeric', 500),
                    )
                    self.assertIsNotNone(self.jobtemplate.search(name))

    @tier1
    def test_positive_template_upload(self):
        """Use a template file to populate the job template

        @id: 976cf310-b2af-41bd-845a-f08baa2e8490

        @Setup: Create or use a pre-made job template file

        @Steps:

        1. Create a new job template.
        2. Enter a valid name
        3. Click the upload button to upload a template from the file
        4. Select the file with the desired template

        @Assert: Verify the template correctly imported the file's contents
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_job_template(
                        session,
                        name=name,
                        template_type='file',
                        template_content=OS_TEMPLATE_DATA_FILE,
                    )
                    self.assertIsNotNone(self.jobtemplate.search(name))

    @tier1
    def test_positive_create_job_template_input(self):
        """Create a Job Template using input

        @id: dbaf5aa9-101d-47dc-bdf8-d5b4d1a52396

        @Steps:

        1. Navigate to Hosts -> Job Templates
        2. Enter a name
        3. Navigate to the job tab
        4. Enter a job name
        5. Click the +Add Input button
        6. Add an appropriate name
        7. Choose an input type
        8. Populate the template code and reference the newly created input
        9. Click submit

        @Assert: The job template was successfully saved with new input added
        """
        name = gen_string('alpha')
        var_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.assertIsNotNone(self.jobtemplate.search(name))
            self.jobtemplate.add_input(name, var_name)
            self.jobtemplate.update(
                name,
                template_type='input',
                template_content='<%= input("{0}") %>'.format(var_name)
            )

    @tier1
    def test_negative_create_job_template(self):
        """Create Job Template with invalid name

        @id: 79342781-1369-4d1f-a512-ca1a809d98fb

        @Steps:

        1. Navigate to Hosts -> Job Templates
        2. Enter an invalid name
        3. Click submit

        @Assert: Job Template with invalid name cannot be created and error is
        raised
        """
        with Session(self.browser) as session:
            for name in invalid_values_list('ui'):
                with self.subTest(name):
                    make_job_template(
                        session,
                        name=name,
                        template_type='input',
                        template_content=gen_string('alphanumeric', 20),
                    )
                    self.assertIsNotNone(self.jobtemplate.wait_until_element(
                        common_locators['name_haserror']))

    @tier1
    def test_negative_create_job_template_with_same_name(self):
        """Create Job Template with duplicate name

        @id: 2c193758-dc34-4701-863c-f2823851223a

        @Steps:

        1. Create a new job template.
        2. Enter a name that has already been used
        3. Click submit

        @Assert: The name duplication is caught and error is raised
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.assertIsNotNone(self.jobtemplate.search(name))
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.assertIsNotNone(self.jobtemplate.wait_until_element(
                common_locators['name_haserror']))

    @tier1
    def test_positive_delete_job_template(self):
        """Delete a job template

        @id: b25e4fb9-ad75-407d-b15f-76df381c4f9c

        @Setup: Create a valid job template.

        @Steps:

        1. Click the dropdown next to the Job Template's Run button
        2. Select Delete from the list
        3. Confirm the deletion

        @Assert: The Job Template has been deleted
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.jobtemplate.delete(name)

    @tier1
    def test_positive_clone_job_template(self):
        """Clone a Job Template

        @id: a1ec5d1d-907f-4d18-93d3-adb1134d9cca

        @Setup: Create a valid job template.

        @Steps:

        1. Navigate to Hosts -> Job Templates
        2. Click the clone button next to a job template
        3. Change the name
        4. Click submit

        @Assert: Verify all job template contents were successfully copied
        """
        name = gen_string('alpha')
        clone_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.assertIsNotNone(self.jobtemplate.search(name))
            self.jobtemplate.clone(name, clone_name)
            self.assertIsNotNone(self.jobtemplate.search(clone_name))

    @tier1
    def test_positive_view_diff(self):
        """View diff within template editor

        @id: 4b8fff93-4862-4119-bb97-aadc50fc817d

        @Setup: Create a valid job template.

        @Steps:

        1. Open the job template created during setup
        2. Modify the template's code
        3. Click the Diff button

        @Assert: Verify that the new changes are displayed in the window
        """
        name = gen_string('alpha')
        old_template = gen_string('alpha')
        new_template = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=old_template,
            )
            self.jobtemplate.click(self.jobtemplate.search(name))
            self.jobtemplate.assign_value(
                locators['job.template_input'], new_template)
            self.jobtemplate.click(common_locators['ace.diff'])
            template_text = self.jobtemplate.wait_until_element(
                locators['job.template_input']).text
            self.assertIn('-' + old_template, template_text)
            self.assertIn('+' + new_template, template_text)

    @tier1
    def test_positive_preview_verify(self):
        """Use preview within the job template editor to verify template

        @id: 4b4939f3-c056-4716-8071-e8fa00233e3e

        @Steps:

        1. Create a new job template.
        2. Add input controls under jobs
        3. Reference those input controls in the template text
        4. Select "preview" within the template viewer

        @Assert: Verify no errors are thrown
        """
        name = gen_string('alpha')
        var_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alpha'),
                org=self.organization.name,
            )
            self.jobtemplate.add_input(name, var_name)
            self.jobtemplate.update(
                name,
                template_type='input',
                template_content='<%= input("{0}") %>'.format(var_name)
            )
            self.jobtemplate.click(self.jobtemplate.search(name))
            self.jobtemplate.click(common_locators['ace.preview'])
            self.assertEqual(
                u'$USER_INPUT[{0}]'.format(var_name),
                self.jobtemplate.wait_until_element(
                    locators['job.template_input']).text
            )

    @tier1
    def test_negative_preview_verify(self):
        """Use a template file to populate the job template

        @id: 8c0d132c-b500-44b5-a549-d32c7636a712

        @Steps:

        1. Create a new job template
        2. Add input controls under jobs
        3. Incorrectly reference those input controls in the template text
        4. And/or reference non-existent input controls in the template text
        5. Select "preview" within the template viewer

        @Assert: Verify appropriate errors are thrown
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alpha'),
                org=self.organization.name,
            )
            self.jobtemplate.add_input(name, gen_string('alpha'))
            self.jobtemplate.update(
                name,
                template_type='input',
                template_content='<%= input("{0}") %>'.format(
                    gen_string('alphanumeric'))
            )
            self.jobtemplate.click(self.jobtemplate.search(name))
            self.jobtemplate.click(common_locators['ace.preview'])
            self.assertIsNotNone(self.jobtemplate.wait_until_element(
                common_locators['alert.error']))


class RemoteExecutionTestCase(UITestCase):
    """Test class for remote execution feature"""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(RemoteExecutionTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @tier2
    def test_positive_run_default_job_template(self):
        """Run a job template against a single host

        @id: 7f0cdd1a-c87c-4324-ae9c-dbc30abad217

        @Setup: Use pre-defined job template.

        @Steps:

        1. Navigate to an individual host and click Run Job
        2. Select the job and appropriate template
        3. Run the job

        @Assert: Verify the job was successfully ran against the host

        @CaseLevel: Integration
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(self.organization.label, lce='Library')
            add_remote_execution_ssh_key(client.ip_addr)
            with Session(self.browser) as session:
                set_context(session, org=self.organization.name)
                self.hosts.click(self.hosts.search(client.hostname))
                status = self.job.run(
                    job_category='Commands',
                    job_template='Run Command - SSH Default',
                    options_list=[{'name': 'command', 'value': 'ls'}]
                )
                self.assertTrue(status)

    @tier3
    def test_positive_run_custom_job_template(self):
        """Run a job template against a single host

        @id: 89b75feb-afff-44f2-a2bd-2ffe74b63ec7

        @Setup: Create a working job template.

        @Steps:

        1. Navigate to an individual host and click Run Job
        2. Select the job and appropriate template
        3. Run the job

        @Assert: Verify the job was successfully ran against the host

        @CaseLevel: System
        """
        jobs_template_name = gen_string('alpha')
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(self.organization.label, lce='Library')
            add_remote_execution_ssh_key(client.ip_addr)
            with Session(self.browser) as session:
                set_context(session, org=self.organization.name)
                make_job_template(
                    session,
                    name=jobs_template_name,
                    template_type='input',
                    template_content='<%= input("command") %>',
                    provider_type='SSH',
                )
                self.assertIsNotNone(
                    self.jobtemplate.search(jobs_template_name))
                self.jobtemplate.add_input(
                    jobs_template_name, 'command', required=True)
                self.hosts.click(self.hosts.search(client.hostname))
                status = self.job.run(
                    job_category='Miscellaneous',
                    job_template=jobs_template_name,
                    options_list=[{'name': 'command', 'value': 'ls'}]
                )
                self.assertTrue(status)

    @tier3
    def test_positive_run_job_template_multiple_hosts(self):
        """Run a job template against multiple hosts

        @id: 7f1981cb-afcc-49b7-a565-7fef9aa8ddde

        @Setup: Create a working job template.

        @Steps:

        1. Navigate to the hosts page and select at least two hosts
        2. Click the "Select Action"
        3. Select the job and appropriate template
        4. Run the job

        @Assert: Verify the job was successfully ran against the hosts

        @CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            with VirtualMachine(distro=DISTRO_RHEL7) as client2:
                for vm in client, client2:
                    vm.install_katello_ca()
                    vm.register_contenthost(
                        self.organization.label, lce='Library')
                    add_remote_execution_ssh_key(vm.ip_addr)
                with Session(self.browser) as session:
                    set_context(session, org=self.organization.name)
                    self.hosts.navigate_to_entity()
                    self.hosts.update_host_bulkactions(
                        [client.hostname, client2.hostname],
                        action='Run Job',
                        parameters_list=[{'command': 'ls'}],
                    )
                    strategy, value = locators['job_invocation.status']
                    self.job.wait_until_element(
                        (strategy, value % 'succeeded'), 240)

    @tier3
    def test_positive_run_scheduled_job_template(self):
        """Schedule a job to be ran against a host

        @id: 35c8b68e-1ac5-4c33-ad62-a939b87f76fb

        @Setup: Use pre-defined job template.

        @Steps:

        1. Navigate to an individual host and click Run Job
        2. Select the job and appropriate template
        3. Select "Schedule Future Job"
        4. Enter a desired time for the job to run
        5. Click submit

        @Assert:

        1. Verify the job was not immediately ran
        2. Verify the job was successfully ran after the designated time

        @CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(self.organization.label, lce='Library')
            add_remote_execution_ssh_key(client.ip_addr)
            with Session(self.browser) as session:
                set_context(session, org=self.organization.name)
                self.hosts.click(self.hosts.search(client.hostname))
                plan_time = (datetime.now() + timedelta(seconds=90)).strftime(
                    "%Y-%m-%d %H:%M")
                status = self.job.run(
                    job_category='Commands',
                    job_template='Run Command - SSH Default',
                    options_list=[{'name': 'command', 'value': 'ls'}],
                    schedule='future',
                    schedule_options=[
                        {'name': 'start_at', 'value': plan_time}],
                    result='queued'
                )
                self.assertTrue(status)
                strategy, value = locators['job_invocation.status']
                self.job.wait_until_element_is_not_visible(
                    (strategy, value % 'queued'), 95)
                self.job.wait_until_element(
                    (strategy, value % 'succeeded'), 30)

    @stubbed()
    @tier3
    def test_positive_run_job_against_provisioned_rhel6_host(self):
        """Run a job against a single provisioned RHEL 6 host

        @id: 7cc94029-69a0-43e0-8ce5-fdf802d0addc

        @Setup:

        1. Provision a RHEL 6 host.
        2. Create a working job template.

        @Steps:

        1. Navigate to the provisioned host and click Run Job
        2. Select the created job and appropriate template
        3. Click submit

        @Assert: Verify the job was successfully ran on the provisioned host

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_run_job_against_provisioned_rhel7_host(self):
        """Run a job against a single provisioned RHEL 7 host

        @id: e911edfb-abcf-4ea2-940d-44f3e4de1954

        @Setup:

        1. Provision a RHEL 7 host.
        2. Create a working job template.

        @Steps:

        1. Navigate to the provisioned host and click Run Job
        2. Select the created job and appropriate template
        3. Click submit

        @Assert: Verify the job was successfully ran on the provisioned host

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_run_job_against_multiple_provisioned_hosts(self):
        """Run a job against multiple provisioned hosts

        @id: 7637f724-924f-478d-88d8-25f500335236

        @Setup:

        1. Provision at least two hosts (RHEL6/7 preferred).
        2. Create a working job template.

        @Steps:

        1. Navigate to the hosts page and select all provisioned hosts
        2. Click Select Action -> Run Job
        3. Select the created job and appropriate template
        4. Click submit

        @Assert: Verify the job was successfully ran on the provisioned hosts

        @caseautomation: notautomated

        @CaseLevel: System
        """
