"""Test for compute resource UI

:Requirement: Computeresource

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import (
    AWS_EC2_FLAVOR_T2_MICRO,
    COMPUTE_PROFILE_LARGE,
    EC2_REGION_CA_CENTRAL_1,
    FOREMAN_PROVIDERS,
)
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_resource
from robottelo.ui.session import Session


class Ec2ComputeResourceTestCase(UITestCase):
    """Implements EC2 compute resource tests in UI"""

    @classmethod
    @skip_if_not_set('ec2')
    def setUpClass(cls):
        super(Ec2ComputeResourceTestCase, cls).setUpClass()
        cls.aws_access_key = settings.ec2.access_key
        cls.aws_secret_key = settings.ec2.secret_key
        cls.aws_region = settings.ec2.region
        cls.aws_image = settings.ec2.image
        cls.aws_availability_zone = settings.ec2.availability_zone
        cls.aws_subnet = settings.ec2.subnet
        cls.aws_security_groups = settings.ec2.security_groups
        cls.aws_managed_ip = settings.ec2.managed_ip

    @run_only_on('sat')
    @tier1
    def test_positive_create_ec2_with_name(self):
        """Create a new ec2 compute resource with valid name

        :id: 4c74d04a-a276-4d6a-b080-77b2b64942ef

        :setup: ec2 hostname and credentials.

        :steps:
            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Provide a valid name to ec2 compute resource.
            4. Test the connection using Load Regions and submit.

        :expectedresults: An ec2 compute resource is created
            successfully.

        :Caseautomation: Automated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['Access Key', self.aws_access_key, 'field'],
            ['Secret Key', self.aws_secret_key, 'field'],
            ['Region', self.aws_region, 'special select']
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['ec2'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_ec2_with_description(self):
        """Create ec2 compute resource with description.

        :id: bca54de0-ac53-432c-85af-6f5b842cd10b

        :setup: ec2 hostname and credentials.

        :steps:
            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Provide a valid description to ec2 compute resource.
            4. Test the connection using Load Regions and submit.

        :expectedresults: An ec2 compute resource is created successfully

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @run_only_on('sat')
    def test_positive_create_ec2_with_custom_region(self):
        """Create a new ec2 compute resource with custom region

        :id: aeb0c52e-34dd-4574-af34-a6d8721724a7

        :customerscenario: true

        :setup: ec2 hostname and credentials.

        :steps:
            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Provide a valid name to ec2 compute resource.
            4. Test the connection using Load Regions.
            5. Provide a valid custom region

        :expectedresults: An ec2 compute resource is created
            successfully.

        :BZ: 1456942

        :Caseautomation: Automated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['Access Key', self.aws_access_key, 'field'],
            ['Secret Key', self.aws_secret_key, 'field'],
            ['Region', EC2_REGION_CA_CENTRAL_1, 'special select']
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['ec2'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_ec2_with_invalid_name(self):
        """Create a new ec2 compute resource with invalid names.

        :id: 36e48e72-e6fa-4b1a-add8-90810902e976

        :setup: ec2 hostname and credentials.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Provide a invalid name to ec2 compute resource.
            4. Test the connection using Load Regions and submit.

        :expectedresults: An ec2 compute resource is not created

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_ec2_name(self):
        """Update An ec2 compute resource name

        :id: bfc43b84-518b-4ec9-a2ac-e77a1e7cdcb0

        :setup: ec2 hostname and credentials.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Provide a valid name to ec2 compute resource.
            4. Test the connection using Load Regions and submit.
            5. Update the name of the created CR with valid string.

        :expectedresults: The ec2 compute resource is updated

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_ec2_organization(self):
        """Update An ec2 compute resource organization

        :id: ee286e04-0012-4573-86aa-8930efe89ec6

        :setup: ec2 hostname and credentials.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Provide a valid name to ec2 compute resource.
            4. Test the connection using Load Regions and submit.
            5. Create a new organization.
            6. Add the CR to new organization.

        :expectedresults: The ec2 compute resource is updated

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1451626)
    @tier1
    def test_positive_delete_ec2(self):
        """Delete An ec2 compute resource

        :id: fd1ba240-d47f-42c8-a1d1-146ab5fd2641

        :setup: ec2 hostname and credentials.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Provide a valid name to ec2 compute resource.
            4. Test the connection using Load Regions and submit.
            5. Delete the created compute resource.

        :expectedresults: The compute resource is deleted

        :BZ: 1451626

        :Caseautomation: Automated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['Access Key', self.aws_access_key, 'field'],
            ['Secret Key', self.aws_secret_key, 'field'],
            ['Region', self.aws_region, 'special select']
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['ec2'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            self.compute_resource.delete(name, dropdown_present=True)
            self.assertIsNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_image_ec2_with_name(self):
        """Add images to the ec2 compute resource with valid name.

        :id: f70c9520-e8cb-46fb-99b6-045877c70170

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

        :Caseautomation: notautomated
         """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_add_image_ec2_with_invalid_name(self):
        """Add images to the ec2 compute resource with invalid name.

        :id: e6cba3ec-83f8-484d-b4ef-862f20faa37f

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

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @tier2
    def test_positive_access_ec2_with_default_profile(self):
        """Associate default (3-Large) compute profile to ec2 compute
        resource

        :id: 11577087-8c0c-4e87-aed0-4d1b147fd274

        :setup: ec2 hostname, credentials, and flavor.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Select the created ec2 CR.
            4. Click Compute Profile tab.
            5. Select (3-Large) and submit.

        :expectedresults: The compute resource created and opened successfully

        :Caseautomation: Automated
        """
        parameter_list = [
            ['Access Key', self.aws_access_key, 'field'],
            ['Secret Key', self.aws_secret_key, 'field'],
            ['Region', self.aws_region, 'special select']
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['ec2'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(
                self.compute_resource.select_profile(
                    name,
                    COMPUTE_PROFILE_LARGE
                )
            )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_access_ec2_with_custom_profile(self):
        """Associate custom (3-Large) compute profile to ec2 compute resource

        :id: 88cb2f19-4f6e-4533-859b-59c7d99c206f

        :setup: ec2 hostname and credentials, custom flavor.

        :steps:

            1. Create a compute resource of type ec2.
            2. Provide a valid Access Key and Secret Key.
            3. Select the created ec2 CR.
            4. Click Compute Profile tab.
            5. Edit (3-Large) with valid configurations and submit.

        :expectedresults: The compute resource created and opened successfully

        :Caseautomation: Automated
        """
        parameter_list = [
            ['Access Key', self.aws_access_key, 'field'],
            ['Secret Key', self.aws_secret_key, 'field'],
            ['Region', self.aws_region, 'special select']
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['ec2'],
                parameter_list=parameter_list
            )
            self.compute_resource.set_profile_values(
                name, COMPUTE_PROFILE_LARGE,
                flavor=AWS_EC2_FLAVOR_T2_MICRO,
                availability_zone=self.aws_availability_zone,
                subnet=self.aws_subnet,
                security_groups=self.aws_security_groups,
                managed_ip=self.aws_managed_ip,
            )

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_retrieve_ec2_vm_list(self):
        """List the virtual machines from ec2 compute resource.

        :id: a8f09878-4aec-484c-a9d6-710ffe2cc8df

        :setup: ec2 hostname and credentials.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.

        :expectedresults: The Virtual machines should be displayed

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_ec2_host_with_image(self):
        """Provision a host on ec2 compute resource with image based

        :id: 5b68bfb8-6c15-4629-b25a-8928afdc7ca9

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
            6. Select ec2 compute resource from "Deploy on" drop down.
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

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_ec2_with_compute_profile(self):
        """ Provision a host on ec2 compute resource with compute profile
        default (3-Large)

        :id: 01c8b5de-2b37-4cb2-989c-fae5a9446944

        :setup: ec2 hostname, credentials and provisioning setup.

        :steps:
            1. Go to "Hosts --> New host".
            2. Fill in the required details.(eg name,loc, org).
            3. Select ec2 compute resource from "Deploy on" drop down.
            4. Interfaces Tab: Deselect subnet option
            5. Virtual Machine Tab: Select Flavor, Availability zone, Subnet,
               Security groups, Managed IP if we are not using HG.
            6. Parameters Tab: Ensure the sshkey parameter and it's value
               (public key) is added depending upon whether we are using HG
               or not.
            7. Select the "Compute profile" from the drop down.
            8. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned successfully

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_ec2_with_custom_compute_settings(self):
        """ Provision a host on ec2 compute resource with
         custom flavour.

        :id: 441ba03a-98e7-4475-a0d5-56bad23e645b

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

        :Caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_ec2_with_host_group(self):
        """ Provision a host on ec2 compute resource with
        the help of hostgroup.

        :id: a8f4f26b-e075-411d-b4b2-d0ba1e7f09d4

        :setup: ec2 hostname, credentials, provisioning setup and
                hostgroup for ec2.

        :steps:
            1. Go to "Hosts --> New host".
            2. Assign the host group to the host.
            3. Select the Deploy on as ec2 compute resource.
            4. Interfaces Tab: Deselect subnet option
            5. Virtual Machine Tab: Select Flavor, Availability zone, Subnet,
               Security groups, Managed IP if we are not using HG.
            6. Parameters Tab: Ensure the sshkey parameter and it's value
               (public key) is added depending upon whether we are using HG
               or not.
            7. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :Caseautomation: notautomated
        """
