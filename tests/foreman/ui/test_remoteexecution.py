"""Test class for Remote Execution Management UI

@Requirement: Remoteexecution

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from robottelo.decorators import stubbed, tier1, tier2, tier3
from robottelo.test import UITestCase


class RemoteExecutionTestCase(UITestCase):
    """Test class for remote execution feature"""

    @stubbed()
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

        @caseautomation: notautomated
        """

    @stubbed()
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

        @Assert: The job template was successfully created

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_create_job_template_with_same_name(self):
        """Create Job Template with duplicate name

        @id: 2c193758-dc34-4701-863c-f2823851223a

        @Steps:

        1. Create a new job template.
        2. Enter a name that has already been used
        3. Click submit

        @Assert: The name duplication was caught, stopping creation

        @caseautomation: notautomated
        """

    @stubbed()
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

        @caseautomation: notautomated
        """

    @stubbed()
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

        @caseautomation: notautomated
        """

    @stubbed()
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

        @caseautomation: notautomated
        """

    @stubbed()
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

        @caseautomation: notautomated
        """

    @stubbed()
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

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_preview_verify(self):
        """Use a template file to populate the job template

        @id: 8c0d132c-b500-44b5-a549-d32c7636a712

        @Steps:

        1. Create a new job template
        2. Add input controls under jobs
        3. Incorrectly reference those input controls in the template text
        4. And/or reference non-existant input controls in the template text
        5. Select "preview" within the template viewer

        @Assert: Verify appropriate errors are thrown

        @caseautomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_run_job_template(self):
        """Run a job template against a single host

        @id: 7f0cdd1a-c87c-4324-ae9c-dbc30abad217

        @Setup: Create a working job template.

        @Steps:

        1. Navigate to an individual host and click Run Job
        2. Select the job and appropriate template
        3. Run the job

        @Assert: Verify the job was succesfully ran against the host

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_run_job_template_multiple_hosts(self):
        """Run a job template against multiple hosts

        @id: 7f1981cb-afcc-49b7-a565-7fef9aa8ddde

        @Setup: Create a working job template.

        @Steps:

        1. Navigate to the hosts page and select at least two hosts
        2. Click the "Select Action"
        3. Select the job and appropriate template
        4. Run the job

        @Assert: Verify the job was succesfully ran against the hosts

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_run_scheduled_job_template(self):
        """Schedule a job to be ran against a host

        @id: 35c8b68e-1ac5-4c33-ad62-a939b87f76fb

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

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

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

        @Assert: Verify the job was succesfully ran on the provisioned host

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

        @Assert: Verify the job was succesfully ran on the provisioned host

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
