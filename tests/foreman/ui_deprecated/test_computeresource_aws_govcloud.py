"""Test for compute resource UI

:Requirement: Provision to AWS GovCloud

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import (
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier2,
    tier3,
    upgrade,
)
from robottelo.test import UITestCase


class Ec2ComputeResourceTestCase(UITestCase):
    """Implements AWS Govcloud ec2 compute resource tests in UI"""

    @classmethod
    @skip_if_not_set('ec2')
    def setUpClass(cls):
        super(Ec2ComputeResourceTestCase, cls).setUpClass()

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_ec2_organization(self):
        """Update An AWS Govcloud ec2 compute resource organization

        :id: 47d2e286-c447-4435-9657-1af7cc2dee3f

        :setup: ec2 hostname and credentials.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Provide a valid name to AWS Govcloud ec2 compute resource.
            4. Test the connection using Load Regions and submit.
            5. Create a new organization.
            6. Add the CR to new organization.

        :expectedresults: The AWS Govcloud ec2 compute resource is updated

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_image_ec2_with_name(self):
        """Add images to the AWS Govcloud ec2 compute resource with valid name.

        :id: b873eb04-f511-44ba-80b2-ea6aae389a7e

        :setup: ec2 hostname, credentials and images in ec2.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Select the created ec2 CR and click images tab.
            4. Select "New image" , provide it valid name and information.
            5. The user for the image should be "ec2-user".
            6. Select the desired Amazon Machine Image (ami) to create image
               and submit.

        :expectedresults: The image is added to the CR successfully

        :CaseAutomation: notautomated
         """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_add_image_ec2_with_invalid_name(self):
        """Add images to the AWS Govcloud ec2 compute resource with invalid name.

        :id: c7cc2732-ef2a-43c2-86e8-405ebb4004df

        :setup: ec2 hostname, credentials and images in ec2.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Select the created ec2 CR and click images tab.
            4. Select "New image" , provide it invalid name.
            5. The user for the image should be "ec2-user".
            6. Select the desired Amazon Machine Image (ami) to create the
               image from and submit.

        :expectedresults: The image should not be added to the CR

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_access_ec2_with_default_profile(self):
        """Associate default (3-Large) compute profile to ec2 compute
        resource

        :id: 3a747815-dcd2-4b67-94aa-a402c41f83c3

        :setup: ec2 hostname, credentials, and flavor.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Select the created ec2 CR.
            4. Click Compute Profile tab.
            5. Select (3-Large) and submit.

        :expectedresults: The compute resource created and opened successfully

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_access_ec2_with_custom_profile(self):
        """Associate custom (3-Large) compute profile to AWS Govcloud ec2
        compute resource

        :id: 003902e1-cfec-4133-b413-cd33ee87e5f4

        :setup: ec2 hostname and credentials, custom flavor.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Select the created ec2 CR.
            4. Click Compute Profile tab.
            5. Edit (3-Large) with valid configurations and submit.

        :expectedresults: The compute resource created and opened successfully

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_retrieve_ec2_vm_list(self):
        """List the virtual machines from AWS Govcloud ec2 compute resource.

        :id: e0c6d180-c001-4615-bd51-55720417be2d

        :setup: ec2 hostname and credentials.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.

        :expectedresults: The Virtual machines should be displayed

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_ec2_host_with_image(self):
        """Provision a host on AWS Govcloud ec2 compute resource with image
        based

        :id: 331c844e-e416-4ab4-8fa9-2adccca440c1

        :setup:
                1. Ec2 hostname and credentials.
                2. Addition of custom provisioning template
                   to add ssh-key parameter. (Refer step 3)
                3. Clone the Satellite Kickstart Default Finish, add new
                   ssh-key parameter support in the template and save the
                   template using custom name.
                4. Update the OS to use the provisioning template
                5. Ec2 ami image added to compute resource.

        :steps:
            1. Populate images into satellite from ec2 ami images.
            2. Associate Activation key and CV to the host.
            3. Edit the required Operating system to use the custom
               provisioning template.
            4. Go to "Hosts --> New host".
            5. Fill in the required details.(eg name,loc, org)(hostgroup)
            6. Select AWS Govcloud ec2 compute resource from "Deploy on" drop
               down.
            7. Interfaces Tab: Deselect subnet option.
            8. Virtual Machine Tab: Select Flavor, Availability zone, Subnet,
               Security groups, Managed IP if we are not using HG.
            9. Parameters Tab: Ensure the sshkey parameter and it's value
               (public key) is added depending upon whether we are using HG
               or not.
            10. Associate appropriate feature capsules.
            11. Go to "operating system tab".
            12. Select the appropriate image .
            13. Associate the activation key and submit.

        :expectedresults: The host should be provisioned successfully

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_ec2_with_compute_profile(self):
        """ Provision a host on AWS Govcloud ec2 compute resource with compute
        profile default (3-Large)

        :id: a3b3c139-e0db-4e93-a68a-94ab7e9c69ea

        :setup: ec2 hostname, credentials and provisioning setup.

        :steps:
            1. Go to "Hosts --> New host".
            2. Fill in the required details.(eg name,loc, org).
            3. Select AWS Govcloud ec2 compute resource from "Deploy on" drop
               down.
            4. Interfaces Tab: Deselect subnet option
            5. Virtual Machine Tab: Select Flavor, Availability zone, Subnet,
               Security groups, Managed IP if we are not using HG.
            6. Parameters Tab: Ensure the sshkey parameter and it's value
               (public key) is added depending upon whether we are using HG
               or not.
            7. Select the "Compute profile" from the drop down.
            8. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned successfully

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_ec2_with_custom_compute_settings(self):
        """ Provision a host on AWS Govcloud ec2 compute resource with
         custom flavour.

        :id: 28013848-ab4a-4e42-bef0-b2296698f54b

        :setup: ec2 hostname, credentials and provisioning setup.

        :steps:
            1. Go to "Hosts --> New host".
            2. Fill in the required details.(eg name,loc, org).
            3. Select ec2 custom compute resource from "Deploy on" drop
               down.
            4. Interfaces Tab: Deselect subnet option
            5. Virtual Machine Tab: Select Flavor, Availability zone, Subnet,
               Security groups, Managed IP if we are not using HG.
            6. Parameters Tab: Ensure the sshkey parameter and it's value
               (public key) is added depending upon whether we are using HG
               or not.
            7. Select the custom compute profile and flavor.
            8. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned with custom settings

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_ec2_with_host_group(self):
        """ Provision a host on AWS Govcloud ec2 compute resource with
        the help of hostgroup.

        :id: 802cc2c7-ef6f-4772-b464-c1e48f1caec4

        :setup: ec2 hostname, credentials, provisioning setup and
                hostgroup for ec2.

        :steps:
            1. Go to "Hosts --> New host".
            2. Assign the host group to the host.
            3. Select the Deploy on as AWS Govcloud ec2 compute resource.
            4. Interfaces Tab: Deselect subnet option
            5. Virtual Machine Tab: Select Flavor, Availability zone, Subnet,
               Security groups, Managed IP if we are not using HG.
            6. Parameters Tab: Ensure the sshkey parameter and it's value
               (public key) is added depending upon whether we are using HG
               or not.
            7. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :CaseAutomation: notautomated
        """
