# -*- encoding: utf-8 -*-
"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier2,
    tier4,
    upgrade
)
from robottelo.test import UITestCase


class TailoringFilesTestCase(UITestCase):
    """Implements Tailoring Files tests in UI."""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create(self):
        """Create new Tailoring Files using different values types as name

        :id: d6ae6b33-5af3-4b55-8ad4-6fa8e67e40f5

        :setup: Oscap enabled on capsule and scap tailoring file

        :steps:

            1. Navigate to Tailoring files menu
            2. Upload a valid tailoring file
            3. Give it a valid name

        :CaseAutomation: notautomated

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_with_space(self):
        """Create tailoring files with space in name

        :id: 4b6a608b-b032-4d03-b67a-a9dce194e1ce

        :setup: tailoring file

        :steps:

            1. Navigate to Tailoring files menu
            2. Upload a valid tailoring file
            3. Give it a name with space

        :CaseAutomation: notautomated

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_with_valid_file(self):
        """Create Tailoring files with valid file

        :id: add6ac04-20f7-4446-a66a-297a6a16f4ff

        :setup: tailoring file

        :steps:

            1. Navigate to Tailoring files menu
            2. With valid name ,upload a valid tailoring file

        :CaseAutomation: notautomated

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_creat_with_invalid_file(self):
        """Create Tailoring files with invalid file

        :id: 310200e6-b5d9-460e-866a-a7864c134d76

        :setup: invalid tailoring file

        :steps:

            1. Navigate to Tailoring files menu
            2. With valid name ,upload  invalid tailoring file

        :CaseAutomation: notautomated

        :expectedresults: Tailoring file will not be added to satellite

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_associate_tailoring_file_with_scap(self):
        """ Associate a Tailoring file with it’s scap content

        :id: 33e7b8ca-2e5f-4886-91b7-1a8763059d14

        :setup: scap content and tailoring file

        :steps:

            1. Create a valid scap content
            2. Upload a vaild tailoring file
            3. Associate scap content with it’s tailoring file

        :CaseAutomation: notautomated

        :expectedresults: Association should be successful

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_associate_tailoring_file_with_different_scap(self):
        """ Associate a tailoring file with different scap content

        :id: 5b166dd4-5e9c-4c35-b2fb-fd35d75d51f5

        :setup: scap content and tailoring file

        :steps:

            1. Create a valid scap content
            2. Upload a Mutually exclusive tailoring file
            3. Associate the scap content with tailoring file

        :CaseAutomation: notautomated

        :expectedresults: Association should give some warning

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_download_tailoring_file(self):
        """ Download the tailoring file from satellite

        :id: 906ab1f8-c02c-4197-9c98-01e8b9f2f075

        :setup: tailoring file

        :steps:

            1. Upload a tailoring file
            2. Download the uploaded tailoring file

        :CaseAutomation: notautomated

        :expectedresults: The tailoring file should be downloaded

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_download_tailoring_file(self):
        """ Download the tailoring file from satellite

        :id: 001a75c1-1579-4169-80a5-1a39e8afdd63

        :setup: tailoring file

        :steps:

            1. Upload a tailoring file
            2. Shut down OSCAP proxy
            3. Download the uploaded tailoring file

        :CaseAutomation: notautomated

        :expectedresults: Get meaningful message about what went wrong

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_delete_tailoring_file(self):
        """ Delete tailoring file

        :id: 359bade3-fff1-4aac-b4de-491190407507

        :setup: tailoring file

        :steps:

            1. Upload a tailoring file
            2. Delete the created tailoring file

        :CaseAutomation: notautomated

        :expectedresults: Tailoring file should be deleted

        :CaseImportance: Critical
        """

    @upgrade
    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_oscap_run_with_tailoring_file_and_capsule(self):
        """ End-to-End Oscap run with tailoring files and default capsule

        :id: 346946ad-4f62-400e-9390-81817006048c

        :setup: scap content, scap policy, tailoring file, host group

        :steps:

            1. Create a valid scap content
            2. Upload a valid tailoring file
            3. Create a scap policy
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

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_oscap_run_with_tailoring_file_and_external_capsule(self):
        """ End-to-End Oscap run with tailoring files and external capsule

        :id: 5e6e87b1-5f7d-4bbb-9603-eb3a34521d31

        :setup: scap content, scap policy, tailoring file, host group

        :steps:
            1. Create a valid scap content
            2. Upload a valid tailoring file
            3. Create a scap policy
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

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_fetch_tailoring_file_information_from_arfreports(self):
        """ Fetch Tailoring file Information from Arf-reports

        :id: 7412cf34-8271-4c8b-b369-304529e8ee28

        :setup: scap content, scap policy, tailoring file, host group

        :steps:

            1. Create a valid scap content
            2. Upload a valid tailoring file
            3. Create a scap policy
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

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_tailoring_file_options_with_no_capsule_support(self):
        """ Tailoring Files Options with no capsule support(Eg. 6.2 cap)

        :id: ecfd2f5f-a8b1-4491-a081-33ac013f5e9f

        :CaseAutomation: notautomated

        :expectedresults:  Display a message about no supported capsule

        :CaseImportance: Critical
        """
