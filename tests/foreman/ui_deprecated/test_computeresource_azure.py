"""Test for compute resource UI

:Requirement: Computeresource Azure

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
    tier3,
    upgrade,
)
from robottelo.test import UITestCase


class AzureComputeResourceTestCase(UITestCase):
    """Implements compute resource tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_azure_with_name(self):
        """Create a new azure compute resource with valid name.

        :id: 477194a8-ac7e-4ab0-a59c-a45c0c2e9520

        :setup:

            1. Management certificates, two certificates are needed.
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.

        :steps:

            1. Create a compute resource of type azure.
            2. Provide a valid subscription ID and a path to the ".pem"
               certificate.
            3. Provide a valid name to azure compute resource.
            4. Test the connection using "Test Connection" and submit.

        :expectedresults: An azure compute resource is created successfully.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_azure_with_description(self):
        """Create azure compute resource with description.

        :id: 40f62a58-3f8c-4c9d-b8df-582ed6bb4367

        :setup:

            1. Management certificates, two certificates are needed.
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.

        :steps:

            1. Create a compute resource of type azure.
            2. Provide a valid subscription ID and a path to the ".pem"
               certificate.
            3. Provide a valid description to azure compute resource.
            4. Test the connection using "Test Connection" and submit.

        :expectedresults: An azure compute resource is created successfully

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_azure_with_invalid_name(self):
        """Create a new azure compute resource with invalid names.

        :id: 350edd6f-16fb-410e-a118-d9a3f496da3c

        :setup:

            1. Management certificates, two certificates are needed.
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.

        :steps:

            1. Create a compute resource of type azure.
            2. Provide a valid subscription ID and a path to the ".pem"
               certificate.
            3. Provide a invalid name to azure compute resource.
            4. Test the connection using "Test Connection" and submit.

        :expectedresults: An azure compute resource is not created

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_azure_name(self):
        """Update An azure compute resource name.

        :id: 9bfcb0a8-9806-41de-8faf-3b7a40f05823

        :setup:

            1. Management certificates, two certificates are needed.
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.

        :steps:

            1. Create a compute resource of type azure.
            2. Provide a valid subscription ID and a path to the ".pem"
               certificate.
            3. Provide a valid name to azure compute resource.
            4. Test the connection using "Test Connection" and submit.
            5. Update the name of the created CR with valid string.

        :expectedresults: The azure compute resource is updated

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_azure_organization(self):
        """Update An azure compute resource organization.

        :id: 724546cf-185a-4d91-92f2-9ef078ab38cf

        :setup:

            1. Management certificates, two certificates are needed.
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.

        :steps:

            1. Create a compute resource of type azure.
            2. Provide a valid subscription ID and a path to the ".pem"
               certificate.
            3. Provide a valid name to azure compute resource.
            4. Test the connection using "Test Connection" and submit.
            5. Create a new organization.
            6. Add the CR to new organization.

        :expectedresults: The azure compute resource is updated

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    @upgrade
    def test_positive_delete_azure(self):
        """Delete An azure compute resource.

        :id: c9223ef6-00a7-4463-9f67-4f8cee3475c6

        :setup:

            1. Management certificates, two certificates are needed.
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.

        :steps:

            1. Create a compute resource of type azure.
            2. Provide a valid subscription ID and a path to the ".pem"
               certificate.
            3. Provide a valid name to azure compute resource.
            4. Test the connection using "Test Connection" and submit.
            5. Delete the created compute resource.

        :expectedresults: The compute resource is deleted

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_image_azure_with_name(self):
        """Add images to the azure compute resource with valid name.

        :id: 6cd42f2f-44cb-4e10-b5f9-bcc617b63cab

        :setup:

            1. Management certificates, two certificates are needed
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.
            5. Make sure Images available in azure region.

        :steps:

            1. Create a compute resource of type azure.
            2. Provide a valid subscription ID and a path to the ".pem"
               certificate.
            3. Select the created azure CR and click images tab.
            4. Select "New image" , provide it valid name and information.
            5. Select the desired template to create image and submit.

        :expectedresults: The image is added to the CR successfully

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_add_image_azure_with_invalid_name(self):
        """Add images to the azure compute resource with invalid name.

        :id: 3cef6a33-e614-4571-a1ee-cf9b62dac764

        :setup:

            1. Management certificates, two certificates are needed
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.
            5. Make sure Images available in azure region.

        :steps:

            1. Create a compute resource of type azure.
            2. Provide a valid subscription ID and a path to the ".pem"
               certificate.
            3. Select the created azure CR and click images tab.
            4. Select "New image" , provide it invalid name.
            5. Select the desired template to create the image from and submit.

        :expectedresults: The image should not be added to the CR

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_retrieve_azure_vm_list(self):
        """List the virtual machines from azure compute resource.

        :id: 9e0b29f9-6873-4b10-931a-e2a54720f076

        :setup:

            1. Management certificates, two certificates are needed
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.

        :expectedresults: The Virtual machines should be displayed

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_azure_with_host_group(self):
        """ Provision a host on azure compute resource with
        the help of hostgroup.

        :id: d3c2d0e3-8a3a-4f3c-9b7f-ce21c32a7347

        :setup:

            1. Management certificates, two certificates are needed
            2. ".cer" file, which is uploaded to Azure.
            3. ".pem" file, which is stored locally.
            4. Subscription ID from azure.

        :steps:

            1. Go to "Hosts --> New host".
            2. Assign the host group to the host.
            3. Select the Deploy on as azure compute resource.
            4. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :CaseAutomation: notautomated
        """
