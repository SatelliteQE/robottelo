"""Test class for Remote Execution Management UI"""
from robottelo.decorators import stubbed, tier1, tier2, tier3
from robottelo.test import UITestCase


class RemoteExecutionTestCase(UITestCase):
    """Test class for remote execution feature"""

    @stubbed()
    @tier1
    def test_positive_create_simple_job_template(self):
        """Create a simple Job Template

        @Feature: Remote Execution

        @Steps:

        1. Navigate to Hosts -> Job Templates
        2. Enter a valid name
        3. Populate the template code
        4. Navigate to the job tab
        5. Enter a job name
        6. Click submit

        @Assert: The job template was successfully created

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_create_job_template_input(self):
        """Create a Job Template using input

        @Feature: Remote Execution

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

        @Assert: The job template was successfully created

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_create_job_template_with_same_name(self):
        """Create Job Template with duplicate name

        @Feature: Remote Execution

        @Steps:

        1. Create a new job template.
        2. Enter a name that has already been used
        3. Click submit

        @Assert: The name duplication was caught, stopping creation

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_delete_job_template(self):
        """Delete a job template

        @Feature: Remote Execution

        @Setup: Create a valid job template.

        @Steps:

        1. Click the dropdown next to the Job Template's Run button
        2. Select Delete from the list
        3. Confirm the deletion

        @Assert: The Job Template has been deleted

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_clone_job_template(self):
        """Clone a Job Template

        @Feature: Remote Execution

        @Setup: Create a valid job template.

        @Steps:

        1. Navigate to Hosts -> Job Templates
        2. Click the clone button next to a job template
        3. Change the name
        4. Click submit

        @Assert: Verify all job template contents were successfully copied

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_view_diff(self):
        """View diff within template editor

        @Feature: Remote Execution

        @Setup: Create a valid job template.

        @Steps:

        1. Open the job template created during setup
        2. Modify the template's code
        3. Click the Diff button

        @Assert: Verify that the new changes are displayed in the window

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_template_upload(self):
        """Use a template file to populate the job template

        @Feature: Remote Execution

        @Setup: Create or use a pre-made job template file

        @Steps:

        1. Create a new job template.
        2. Enter a valid name
        3. Click the upload button to upload a template from the file
        4. Select the file with the desired template

        @Assert: Verify the template correctly imported the file's contents

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_preview_verify(self):
        """Use preview within the job template editor to verify template

        @Feature: Remote Execution

        @Steps:

        1. Create a new job template.
        2. Add input controls under jobs
        3. Reference those input controls in the template text
        4. Select "preview" within the template viewer

        @Assert: Verify no errors are thrown

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_preview_verify(self):
        """Use a template file to populate the job template

        @Feature: Remote Execution

        @Steps:

        1. Create a new job template
        2. Add input controls under jobs
        3. Incorrectly reference those input controls in the template text
        4. And/or reference non-existant input controls in the template text
        5. Select "preview" within the template viewer

        @Assert: Verify appropriate errors are thrown

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_run_job_template(self):
        """Run a job template against a single host

        @Feature: Remote Execution

        @Setup: Create a working job template.

        @Steps:

        1. Navigate to an individual host and click Run Job
        2. Select the job and appropriate template
        3. Run the job

        @Assert: Verify the job was succesfully ran against the host

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_run_job_template_multiple_hosts(self):
        """Run a job template against multiple hosts

        @Feature: Remote Execution

        @Setup: Create a working job template.

        @Steps:

        1. Navigate to the hosts page and select at least two hosts
        2. Click the "Select Action"
        3. Select the job and appropriate template
        4. Run the job

        @Assert: Verify the job was succesfully ran against the hosts

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_run_scheduled_job_template(self):
        """Schedule a job to be ran against a host

        @Feature: Remote Execution

        @Setup: Create a working job template.

        @Steps:

        1. Navigate to an individual host and click Run Job
        2. Select the job and appropriate template
        3. Select "Schedule Future Job"
        4. Enter a desired time for the job to run
        5. Click submit

        @Assert:

        1. Verify the job was not immediately ran
        2. Verify the job was succesfully ran after the designated time

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_run_job_against_provisioned_rhel6_host(self):
        """Run a job against a single provisioned RHEL 6 host

        @Feature: Remote Execution

        @Setup:

        1. Provision a RHEL 6 host.
        2. Create a working job template.

        @Steps:

        1. Navigate to the provisioned host and click Run Job
        2. Select the created job and appropriate template
        3. Click submit

        @Assert: Verify the job was succesfully ran on the provisioned host

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_run_job_against_provisioned_rhel7_host(self):
        """Run a job against a single provisioned RHEL 7 host

        @Feature: Remote Execution

        @Setup:

        1. Provision a RHEL 7 host.
        2. Create a working job template.

        @Steps:

        1. Navigate to the provisioned host and click Run Job
        2. Select the created job and appropriate template
        3. Click submit

        @Assert: Verify the job was succesfully ran on the provisioned host

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_run_job_against_multiple_provisioned_hosts(self):
        """Run a job against multiple provisioned hosts

        @Feature: Remote Execution

        @Setup:

        1. Provision at least two hosts (RHEL6/7 preferred).
        2. Create a working job template.

        @Steps:

        1. Navigate to the hosts page and select all provisioned hosts
        2. Click Select Action -> Run Job
        2. Select the created job and appropriate template
        3. Click submit

        @Assert: Verify the job was succesfully ran on the provisioned hosts

        @Status: Manual
        """
