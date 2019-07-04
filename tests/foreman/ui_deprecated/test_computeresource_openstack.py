"""Test for compute resource UI

:Requirement: Computeresource Openstack

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


class OpenstackComputeResourceTestCase(UITestCase):
    """Implements compute resource tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_openstack_with_name(self):
        """Create a new openstack compute resource with valid name

        :id: 17f8e903-c2db-4580-8162-0706da6c6368

        :setup: openstack hostname and credentials.

        :steps:
            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Provide a valid name to openstack compute resource.
            4. Test the connection using Load Tenants and submit.

        :expectedresults: An openstack compute resource is created
            successfully.

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_openstack_with_description(self):
        """Create openstack compute resource with description.

        :id: 8373b79a-bffc-409b-95fe-0bb170536c5b

        :setup: openstack hostname and credentials.

        :steps:
            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Provide a valid description to openstack compute resource.
            4. Test the connection using Load Tenants and submit.

        :expectedresults: An openstack compute resource is created successfully

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_openstack_with_invalid_name(self):
        """Create a new openstack compute resource with invalid names.

        :id: aa0cf21d-40a2-4478-9ab5-8e18db7fb8c0

        :setup: openstack hostname and credentials.

        :steps:

            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Provide a invalid name to openstack compute resource.
            4. Test the connection using Load Tenants and submit.

        :expectedresults: An openstack compute resource is not created

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_openstack_name(self):
        """Update An openstack compute resource name

        :id: 27b475dc-bec8-4b25-a67a-0bdba4d086c9

        :setup: openstack hostname and credentials.

        :steps:

            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Provide a valid name to openstack compute resource.
            4. Test the connection using Load Tenants and submit.
            5. Update the name of the created CR with valid string.

        :expectedresults: The openstack compute resource is updated

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_openstack_organization(self):
        """Update An openstack compute resource organization

        :id: 571119e2-cac2-4d05-8e70-c258242bda98

        :setup: openstack hostname and credentials.

        :steps:

            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Provide a valid name to openstack compute resource.
            4. Test the connection using Load Tenants and submit.
            5. Create a new organization.
            6. Add the CR to new organization.

        :expectedresults: The openstack compute resource is updated

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_openstack(self):
        """Delete An openstack compute resource

        :id: 9336c44a-81d3-4132-96b7-013aad45ba67

        :setup: openstack hostname and credentials.

        :steps:

            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Provide a valid name to openstack compute resource.
            4. Test the connection using Load Tenants and submit.
            5. Delete the created compute resource.

        :expectedresults: The compute resource is deleted

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_image_openstack_with_name(self):
        """Add images to the openstack compute resource with valid name.

        :id: bbd49aa3-97d6-4d8f-8caa-1e2660afa6ee

        :setup: openstack hostname, credentials and images in openstack.

        :steps:

            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Select the created openstack CR and click images tab.
            4. Select "New image" , provide it valid name and information.
            5. Select the desired template to create image and submit.

        :expectedresults: The image is added to the CR successfully

        :Caseautomation: notautomated
         """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_add_image_openstack_with_invalid_name(self):
        """Add images to the openstack compute resource with invalid name.

        :id: e2e5989b-b033-4691-b91c-adba1c88af28

        :setup: openstack hostname, credentials and images in openstack.

        :steps:

            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Select the created openstack CR and click images tab.
            4. Select "New image" , provide it invalid name.
            5. Select the desired template to create the image from and submit.

        :expectedresults: The image should not be added to the CR

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_access_openstack_with_default_profile(self):
        """Associate default (3-Large) compute profile to openstack compute
        resource

        :id: 5706bf0a-b052-47eb-8129-559d8fd3238b

        :setup: openstack hostname, credentials, and flavor.

        :steps:

            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Select the created openstack CR.
            4. Click Compute Profile tab.
            5. Select (3-Large) and submit.

        :expectedresults: The compute resource created and opened successfully

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_access_openstack_with_custom_profile(self):
        """Associate custom (3-Large) compute profile to openstack compute resource

        :id: 253e9639-128d-4b3e-a3b7-f5287c58550e

        :setup: openstack hostname and credentials, custom flavor.

        :steps:

            1. Create a compute resource of type openstack.
            2. Provide a valid hostname, username and password.
            3. Select the created openstack CR.
            4. Click Compute Profile tab.
            5. Edit (3-Large) with valid configurations and submit.

        :expectedresults: The compute resource created and opened successfully

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_retrieve_openstack_vm_list(self):
        """List the virtual machines from openstack compute resource.

        :id: c04cdd6b-5ecc-4103-8410-57b73240aeb5

        :setup: openstack hostname and credentials.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.

        :expectedresults: The Virtual machines should be displayed

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_openstack_host_with_image(self):
        """ Provision a host on openstack compute resource with image based

        :id: b3dff8c1-e613-4914-82c1-e2ee36108a19

        :setup: openstack hostname and credentials.
            1. The addition of foreman-proxy-dns-reverse subnets.
            2. The addition of foreman-proxy-dns-zone domain.
            3. Addition of custom provisioning template
            to add ssh-key parameter.

        :steps:
            1. Populate images into satellite from openstack images.
            2. Associate Activation key and CV to the host.
            3. Edit the required Operating system to use the custom
               provisioning template.
            4. Go to "Hosts --> New host".
            5. Fill in the required details.(eg name,loc, org)(hostgroup)
            6. Select openstack compute resource from "Deploy on" drop down.
            7. Associate appropriate feature capsules.
            8. Go to "operating system tab".
            9. Select the appropriate image .
            10. Associate the activation key and submit.

        :expectedresults: The host should be provisioned successfully

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_openstack_with_compute_profile(self):
        """ Provision a host on openstack compute resource with compute profile
        default (3-Large)

        :id: b1e1ad3e-9ad2-45c6-b8dd-4f39ce7729ca

        :setup: openstack hostname ,credentials and provisioning setup.

        :steps:
            1. Go to "Hosts --> New host".
            2. Fill in the required details.(eg name,loc, org).
            3. Select openstack compute resource from "Deploy on" drop down.
            4. Select the "Compute profile" from the drop down.
            5. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned successfully

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_openstack_with_custom_compute_settings(self):
        """ Provision a host on openstack compute resource with
         custom flavour and disk.

        :id: 52c53d90-8eaa-47dd-8c44-6c03293cf64c

        :setup: openstack hostname ,credentials and provisioning setup.

        :steps:
            1. Go to "Hosts --> New host".
            2. Fill in the required details.(eg name,loc, org).
            3. Select openstack custom compute resource from "Deploy on" drop
               down.
            4. Select the custom compute profile" with custom disk size and
               flavor.
            5. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned with custom settings

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_openstack_with_host_group(self):
        """ Provision a host on openstack compute resource with
        the help of hostgroup.

        :id: a3fecc66-0162-4b92-8341-14d255adc118

        :setup: openstack hostname ,credentials, provisioning setup and
            hostgroup for openstack.

        :steps:
            1. Go to "Hosts --> New host".
            2. Assign the host group to the host.
            3. Select the Deploy on as openstack compute resource.
            4. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :Caseautomation: notautomated
        """
