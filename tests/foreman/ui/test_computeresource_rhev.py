"""Test for Compute Resource UI

@Requirement: Computeresource

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import run_only_on, tier1, tier2, tier3, stubbed
from robottelo.test import UITestCase


class RhevComputeResourceTestCase(UITestCase):
    """Implements Compute Resource tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_rhev_with_name(self):
        """Create a new rhev Compute Resource using different value
        types as a name

        @id: be735d8c-5644-4a42-9a08-2f9c6181a8c6

        @setup: rhev hostname and credentials.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Provide a valid name to rhev Compute Resource.
        4. Test the connection using Load Datacenter and submit.

        @Assert: A rhev CR is created successfully with proper connection.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_rhev_with_description(self):
        """Create rhev Compute Resource with description.

        @id: bd5e3066-395c-486e-bce8-b0a9bdd4e236

        @setup: rhev hostname and credentials.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Provide it with some valid description to rhev Compute Resource.
        4. Test the connection using Load Datacenter and submit.

        @Assert: A rhev Compute Resource is created successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_rhev_with_invalid_name(self):
        """Create a new rhev Compute Resource with incorrect values
        only

        @id: 5598b123-b6ad-4bdf-b192-2b1ccc2f41eb

        @setup: rhev hostname and credentials.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Provide a invalid name to rhev Compute Resource.
        4. Test the connection using Load Datacenter and submit.

        @Assert: A rhev Compute Resource is not created

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_rhev_name(self):
        """Update a rhev Compute Resource name

        @id: 62d0c495-c87e-42dd-91aa-9b9b728f7dda

        @setup: rhev hostname and credentials.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Provide a valid name to rhev Compute Resource.
        4. Test the connection using Load Datacenter and submit.
        5. Update the name of the created CR with valid string.

        @Assert: The rhev Compute Resource is updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_rhev_organization(self):
        """Update a rhev Compute Resource organization

        @id: f6656c8e-70a3-40e5-8dda-2154f2eeb042

        @setup: rhev hostname and credentials.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Provide a valid name to rhev Compute Resource.
        4. Test the connection using Load Datacenter and submit.
        5. Create a new organization.
        6. Add the new CR to organization that is created.

        @Assert: The rhev Compute Resource is updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_rhev(self):
        """Delete a rhev Compute Resource

        @id: 4a8b18f0-a2af-491a-bcf7-64d59a0fbc01

        @setup: rhev hostname and credentials.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Provide a valid name to rhev Compute Resource.
        4. Test the connection using Load Datacenter and submit.
        5. Delete the created compute resource.

        @Assert: The Compute Resource is deleted

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_image_rhev_with_name(self):
        """Add images to the rhev compute resource

        @id: 6c7f4169-2e78-44d6-87af-434146093bcc

        @setup: rhev hostname, credentials and images as templates in rhev.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Select the created rhev CR and click images tab.
        4. Select "New image" , provide it valid name and information.
        5. Select the desired template to create image and submit.

        @Assert: The image is added to the CR successfully

        @Caseautomation: notautomated
         """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_add_image_rhev_with_invalid_name(self):
        """Add images to the rhev compute resource

        @id: 0054b389-1e2f-44d9-a306-0410fc0b9d99

        @setup: rhev hostname, credentials and images as templates in rhev.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Select the created rhev CR and click images tab.
        4. Select "New image" , provide it invalid name and valid information.
        5. Select the desired template to create the image from and submit.

        @Assert: The image should not be added to the CR

        @Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_access_rhev_with_default_profile(self):
        """Associate default (3-Large) compute profile to rhev compute resource

        @id: 7049227e-f384-4aa1-8a01-228c3e7292a6

        @setup: rhev hostname and credentials.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Select the created rhev CR.
        4. Click Compute Profile tab.
        5. Select (3-Large) and submit.

        @Assert: The Compute Resource created and opened successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_access_rhev_with_custom_profile(self):
        """Associate custom default (3-Large) compute profile to rhev compute resource

        @id: e7698154-62ff-492b-8e56-c5dc70f0c9df

        @setup: rhev hostname and credentials.

        @steps:
        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Select the created rhev CR.
        4. Click Compute Profile tab.
        5. Edit (3-Large) with valid configurations and submit.

        @Assert: The Compute Resource created and opened successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_retrieve_rhev_vm_list(self):
        """Retrieve the Virtual machine list from rhev compute resource

        @id: f8cef7fb-e14c-4d12-9862-0e448a59ca50

        @setup: rhev hostname and credentials.

        @steps:
        1. Select the created compute resource.
        2. Go to "Virtual Machines" tab.

        @Assert: The Virtual machines should be displayed

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_rhev_with_image(self):
        """ Provision a host on rhev compute resource with image based

        @id: 80abd6b1-31cd-4f3e-949c-f1ca608d0bbb

        @setup: rhev hostname and credentials.
        1. Configured subnet for provisioning of the host.
        2. Configured domains for the host.
        3. Population of images into satellite from rhev templates.
        4. Activation key and CV for the host.

        @steps:
        1. Go to "Hosts --> New host".
        2. Fill in the required details.(eg name,loc, org).
        3. Select rhev compute resource from "Deploy on" drop down.
        4. Associate appropriate feature capsules.
        5. Go to "operating system tab".
        6. Edit Provisioning Method to image based.
        7. Select the appropriate image .
        8. Associate the activation key and submit.

        @Assert: The host should be provisioned successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_rhev_with_compute_profile(self):
        """ Provision a host on rhev compute resource with compute profile
        default (3-Large)

        @id: fe4a05ef-d548-4c28-80d0-d17851fb4b03

        @setup: rhev hostname ,credentials and provisioning setup.

        @steps:
        1. Go to "Hosts --> New host"
        2. Fill in the required details.(eg name,loc, org).
        3. Select rhev compute resource from "Deploy on" drop down.
        4. Select the "Compute profile" from the drop down.
        5. Provision the host using the compute profile.

        @Assert: The host should be provisioned successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_rhev_with_custom_compute_settings(self):
        """ Provision a host on rhev compute resource with
         custom disk, cpu count and memory.

        @id: a972c095-7567-4bb0-86cb-9bd835fed7b7

        @setup: rhev hostname ,credentials and provisioning setup.

        @steps:
        1. Go to "Hosts --> New host"
        2. Fill in the required details.(eg name,loc, org).
        3. Select rhev custom compute resource from "Deploy on" drop down.
        4. Select the custom compute profile" with custom disk size, cpu count
        and memory.
        5. Provision the host using the compute profile.

        @Assert: The host should be provisioned with custom settings

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_rhev_with_host_group(self):
        """ Provision a host on rhev compute resource with
        the help of hostgroup.

        @id: e02fae7d-ac39-4068-ba82-ec0cf110aae8

        @setup: rhev hostname ,credentials provisioning setup and hostgroup

        @steps:
        1. Go to "Hosts --> New host"
        2. Assign the host group to the host
        3. Select the Deploy on as rhev Compute Resource
        4. Provision the host

        @Assert: The host should be provisioned with host group

        @caseautomation: notautomated
        """
