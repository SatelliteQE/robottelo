"""Test for compute resource UI

:Requirement: Computeresource

:CaseComponent: UI

:CaseLevel: Acceptance

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import (
    COMPUTE_PROFILE_LARGE,
    FOREMAN_PROVIDERS,
    VMWARE_CONSTANTS
)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.base import UINoSuchElementError
from robottelo.ui.computeresource import get_compute_resource_profile
from robottelo.ui.factory import make_hostgroup, make_resource
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


class VmwareComputeResourceTestCase(UITestCase):
    """Implement vmware compute resource tests in UI"""

    @classmethod
    @skip_if_not_set('vmware')
    def setUpClass(cls):
        super(VmwareComputeResourceTestCase, cls).setUpClass()
        cls.vmware_url = settings.vmware.vcenter
        cls.vmware_password = settings.vmware.password
        cls.vmware_username = settings.vmware.username
        cls.vmware_datacenter = settings.vmware.datacenter
        cls.vmware_img_name = settings.vmware.image_name
        cls.vmware_img_arch = settings.vmware.image_arch
        cls.vmware_img_os = settings.vmware.image_os
        cls.vmware_img_user = settings.vmware.image_username
        cls.vmware_img_pass = settings.vmware.image_password
        cls.vmware_vm_name = settings.vmware.vm_name
        cls.current_interface = (
            VMWARE_CONSTANTS.get(
                'network_interfaces') % settings.vlan_networking.bridge
        )

    @run_only_on('sat')
    @tier1
    def test_positive_create_vmware_with_name(self):
        """Create a new vmware compute resource using valid name.

        :id: 944ed0da-49d4-4c14-8884-9184d2aef126

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide a valid hostname, username and password.
            3. Provide a valid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.

        :expectedresults: A vmware compute resource is created successfully.

        :Caseautomation: Automated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_vmware_with_description(self):
        """Create vmware compute resource with valid description.

        :id: bdd879be-3467-41ca-9a67-d98f185ba892

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide a valid hostname, username and password.
            3. Provide a valid description to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.

        :expectedresults: A vmware compute resource is created successfully

        :Caseautomation: Automated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            for description in valid_data_list():
                with self.subTest(description):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_vmware_with_invalid_name(self):
        """Create a new vmware compute resource with invalid names.

        :id: 19c206dc-5efc-4a7d-b04d-2aa04a22448c

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Provide invalid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.

        :expectedresults: A vmware compute resource is not created

        :Caseautomation: Automated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        with Session(self) as session:
            for name in invalid_names_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(
                        self.compute_resource.wait_until_element(
                            common_locators["name_haserror"]
                        )
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_update_vmware_name(self):
        """Update a vmware compute resource name

        :id: e2bf2fcb-4611-445e-bc36-a54b3fd2d559

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Provide valid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.
            5. Update the name of the created CR with valid string.

        :expectedresults: The vmware compute resource is updated

        :Caseautomation: Automated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        newname = gen_string('alpha')
        name = gen_string('alpha')
        with Session(self) as session:
            with self.subTest(newname):
                make_resource(
                    session,
                    name=name,
                    provider_type=FOREMAN_PROVIDERS['vmware'],
                    parameter_list=parameter_list
                )
                self.assertIsNotNone(self.compute_resource.search(name))
                self.compute_resource.update(name=name, newname=newname)
                self.assertIsNotNone(self.compute_resource.search(newname))

    @run_only_on('sat')
    @tier2
    def test_positive_update_vmware_organization(self):
        """Update a vmware compute resource organization

        :id: b7ffc933-9ffb-4bcd-ab23-33fde67f27e4

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Provide valid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.
            5. Create a new organization.
            6. Add the CR to new organization.

        :expectedresults: The vmware compute resource is updated

        :Caseautomation: Automated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list,
                orgs=[entities.Organization().create().name],
                org_select=True
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            self.compute_resource.update(
                name=name,
                orgs=[entities.Organization().create().name],
                org_select=True
            )

    @run_only_on('sat')
    @tier1
    def test_positive_delete_vmware(self):
        """Delete a vmware compute resource

        :id: b38f2c9b-f4e3-41e3-8ee1-3b342025860c

        :setup: vmware hostname and credentials.

        :steps:
            1. Create compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Provide valid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.
            5. Delete the created compute resource.

        :expectedresults: The compute resource is deleted

        :Caseautomation: Automated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            with self.subTest(name):
                make_resource(
                    session,
                    name=name,
                    provider_type=FOREMAN_PROVIDERS['vmware'],
                    parameter_list=parameter_list
                )
                self.assertIsNotNone(self.compute_resource.search(name))
                self.compute_resource.delete(name, dropdown_present=True)

    @run_only_on('sat')
    @tier2
    def test_positive_add_image_vmware_with_name(self):
        """Add images to the vmware compute resource

        :id: 4b749529-b98d-4a3e-a2d1-b9738c96c283

        :setup:
            1. Valid vmware hostname, credentials.
            2. Add images as templates in vmware.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR and click images tab.
            4. Select "New image", provide valid name and information.
            5. Select the desired template to create image and submit.

        :expectedresults: The image is added to the CR successfully

        :Caseautomation: Automated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            self.compute_resource.check_image_os(self.vmware_img_os)
            for img_name in valid_data_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                parameter_list_img = [
                    ['Name', img_name],
                    ['Operatingsystem', self.vmware_img_os],
                    ['Architecture', self.vmware_img_arch],
                    ['Username', self.vmware_img_user],
                    ['Password', self.vmware_img_pass],
                    ['uuid', self.vmware_img_name],
                ]
                self.compute_resource.add_image(name, parameter_list_img)
                self.assertIsNotNone(self.compute_resource.search(name))
                imgs = self.compute_resource.list_images(name)
                self.assertIn(img_name, imgs)

    @run_only_on('sat')
    @tier2
    def test_negative_add_image_vmware_with_invalid_name(self):
        """Add images to the vmware compute resource

        :id: 436324bf-7dcf-4197-b1ca-198492bf0356

        :setup:

            1. Valid vmware hostname, credentials.
            2. Add images as templates in vmware.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR and click images tab.
            4. Select "New image" , provide invalid name and valid information.
            5. Select the desired template to create the image from and submit.

        :expectedresults: The image should not be added to the CR

        :Caseautomation: Automated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            self.compute_resource.check_image_os(self.vmware_img_os)
            for img_name in invalid_names_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                parameter_list_img = [
                    ['Name', img_name],
                    ['Operatingsystem', self.vmware_img_os],
                    ['Architecture', self.vmware_img_arch],
                    ['Username', self.vmware_img_user],
                    ['Password', self.vmware_img_pass],
                    ['uuid', self.vmware_img_name],
                ]
                self.compute_resource.add_image(name, parameter_list_img)
                self.assertIsNotNone(
                    self.compute_resource.wait_until_element(
                        common_locators["name_haserror"]
                    ))

    @run_only_on('sat')
    @tier2
    def test_positive_access_vmware_with_default_profile(self):
        """Associate default (3-Large) compute profile

        :id: ceb2ef14-fa96-4951-9198-768ffcc4d01f

        :setup: vmware hostname and credentials.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR.
            4. Click Compute Profile tab.
            5. Select (3-Large) and submit.

        :expectedresults: The Compute Resource created and opened successfully

        :Caseautomation: Automated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_profile.select_resource(
                '3-Large', name, 'VMware'))

    @run_only_on('sat')
    @tier2
    def test_positive_access_vmware_with_custom_profile(self):
        """Associate custom default (3-Large) compute profile

        :id: 751ef765-5091-4322-a0d9-0c9c73009cc4

        :setup: vmware hostname and credentials.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR.
            4. Click Compute Profile tab.
            5. Edit (3-Large) with valid configurations and submit.

        :expectedresults: The Compute Resource created and opened successfully

        :Caseautomation: Automated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            self.compute_resource.set_profile_values(
                name, COMPUTE_PROFILE_LARGE,
                cpus=2,
                corespersocket=2,
                memory=1024,
                cluster=VMWARE_CONSTANTS.get('cluster'),
                folder=VMWARE_CONSTANTS.get('folder'),
                guest_os=VMWARE_CONSTANTS.get('guest_os'),
                scsicontroller=VMWARE_CONSTANTS.get('scsicontroller'),
                virtualhw_version=VMWARE_CONSTANTS.get('virtualhw_version'),
                memory_hotadd=True,
                cpu_hotadd=True,
                cdrom_drive=False,
                annotation_notes=gen_string('alpha'),
                pool=VMWARE_CONSTANTS.get('pool'),
                network_interfaces=[
                    dict(
                        name=VMWARE_CONSTANTS.get('network_interface_name'),
                        network=self.current_interface
                    ),
                    dict(
                        name=VMWARE_CONSTANTS.get('network_interface_name'),
                        network=self.current_interface
                    ),
                ],
                storage=[
                    dict(
                        datastore=VMWARE_CONSTANTS.get('datastore'),
                        size='10',
                        thin_provision=True,
                        eager_zero=True,
                    ),
                    dict(
                        datastore=VMWARE_CONSTANTS.get('datastore'),
                        size='10',
                        thin_provision=False,
                        eager_zero=False,
                    )
                ]
                )
            self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @tier2
    def test_positive_select_vmware_custom_profile_guest_os_rhel7(self):
        """Select custom default (3-Large) compute profile guest OS RHEL7.

        :id: 24f7bb5f-2aaf-48cb-9a56-d2d0713dfe3d

        :customerscenario: true

        :setup: vmware hostname and credentials.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR.
            4. Click Compute Profile tab.
            5. Select 3-Large profile
            6. Set Guest OS field to RHEL7 OS.

        :expectedresults: Guest OS RHEL7 is selected successfully.

        :BZ: 1315277

        :Caseautomation: Automated

        :CaseLevel: Integration
        """
        rc_name = gen_string('alpha')
        guest_os_name = 'Red Hat Enterprise Linux 7 (64-bit)'
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        with Session(self) as session:
            make_resource(
                session,
                name=rc_name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            resource_type, _ = session.compute_resource.select_profile(
                rc_name, COMPUTE_PROFILE_LARGE)
            resource_profile_form = get_compute_resource_profile(
                session.compute_resource, resource_type)
            with self.assertNotRaises(UINoSuchElementError):
                resource_profile_form.set_value('guest_os', guest_os_name)

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_apply_vmware_with_custom_profile_to_host(self):
        """Associate custom default (3-Large) compute profile with hostgroup
        and then inherit it to the host

        :id: c16c6d42-3950-46a7-bfe6-5e19bcfa29d0

        :customerscenario: true

        :setup: vmware hostname and credentials.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR.
            4. Click Compute Profile tab.
            5. Edit (3-Large) with valid configurations and submit.
            6. Create new host group with custom profile
            7. Open new host page and put host group name into corresponding
               field
            8. Check that compute profile is inherited and then switch to
               Virtual Machine tab

        :expectedresults: All fields values for Virtual Machine tab are
            inherited from custom profile and have non default values

        :Caseautomation: Automated

        :BZ: 1249744

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        hg_name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                orgs=[org.name],
                org_select=True,
                parameter_list=parameter_list
            )
            self.compute_resource.set_profile_values(
                name, COMPUTE_PROFILE_LARGE,
                cpus=3,
                corespersocket=4,
                memory=2048,
                cluster=VMWARE_CONSTANTS.get('cluster'),
                folder=VMWARE_CONSTANTS.get('folder'),
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            make_hostgroup(
                session,
                name=hg_name,
                organizations=[org.name],
                parameters_list=[
                    ['Host Group', 'Compute Profile', COMPUTE_PROFILE_LARGE],
                ],
            )
            self.hosts.navigate_to_entity()
            self.hosts.click(locators['host.new'])
            self.hosts.assign_value(locators['host.organization'], org.name)
            # Selecting host group and then compute resource. It is not
            # possible to do it in opposite order as mentioned in initial BZ,
            # because selecting host group will always reset most fields values
            self.hosts.assign_value(locators['host.host_group'], hg_name)
            self.hosts.click(locators['host.deploy_on'])
            self.hosts.assign_value(
                common_locators['select_list_search_box'], name)
            self.hosts.click(
                common_locators['entity_select_list'] %
                '{} (VMware)'.format(name)
            )
            # Check that compute profile is inherited automatically from host
            # group
            self.assertEqual(
                self.hosts.get_element_value(
                    locators['host.fetch_compute_profile']),
                COMPUTE_PROFILE_LARGE
            )
            # Open Virtual Machine tab
            self.hosts.click(tab_locators['host.tab_virtual_machine'])
            # Check that all values are inherited from custom profile
            for locator, value in [
                ['host.cpus', '3'],
                ['host.cores', '4'],
                ['host.memory', '2048'],
                ['host.fetch_cluster', VMWARE_CONSTANTS.get('cluster')],
                ['host.fetch_folder', VMWARE_CONSTANTS.get('folder')],

            ]:
                self.assertEqual(
                    self.hosts.get_element_value(locators[locator]), value)

    @run_only_on('sat')
    @tier2
    def test_positive_retrieve_vmware_vm_list(self):
        """List the virtual machine list from vmware compute resource

        :id: 21ade57a-0caa-4144-9c46-c8e22f33414e

        :setup: vmware hostname and credentials.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.

        :expectedresults: The Virtual machines should be displayed

        :Caseautomation: Automated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            vms = self.compute_resource.list_vms(name)
            self.assertIn(self.vmware_vm_name, vms)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_vmware_with_image(self):
        """ Provision a host on vmware compute resource with image based

        :id: 2cbddac9-c5fa-4f6e-a098-d3e47a3aeb3c

        :setup: vmware hostname and credentials.

            1. Configured subnet for provisioning of the host.
            2. Configured domains for the host.
            3. Population of images into satellite from vmware templates.
            4. Activation key and CV for the host.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill the required details.(eg name,loc, org).
            3. Select vmware compute resource from "Deploy on" drop down.
            4. Associate appropriate feature capsules.
            5. Go to "operating system tab".
            6. Edit Provisioning Method to image based.
            7. Select the appropriate image .
            8. Associate the activation key and submit.

        :expectedresults: The host should be provisioned successfully

        :Caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_vmware_with_compute_profile(self):
        """ Provision a host on vmware compute resource with compute profile
        default (3-Large)

        :id: cfe68708-f062-425e-bed7-a46e04007b11

        :setup:

            1. Vaild vmware hostname ,credentials.
            2. Configure provisioning setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill the required details.(eg name,loc, org).
            3. Select vmware compute resource from "Deploy on" drop down.
            4. Select the "Compute profile" from the drop down.
            5. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned successfully

        :Caseautomation: notautomated

        :CaseLevel: System
        """

    @upgrade
    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_vmware_with_custom_compute_settings(self):
        """ Provision a host on vmware compute resource with
        custom disk, cpu count and memory

        :id: d82c2b81-3a24-4d6e-82eb-c35709861a44

        :setup:

            1. Vaild vmware hostname ,credentials.
            2. Configure provisioning setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill the required details.(eg name,loc, org).
            3. Select vmware custom compute resource from "Deploy on" drop
               down.
            4. Select the custom compute profile" with custom disk size, cpu
               count and memory.
            5. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned with custom settings

        :Caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_vmware_with_host_group(self):
        """ Provision a host on vmware compute resource with
        the help of hostgroup.

        :id: d4e442ad-77f1-4d5e-9d1b-9a60d69b034f

        :setup:

            1. Vaild vmware hostname ,credentials.
            2. Configure provisioning setup.
            3. Configure host group setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Assign the host group to the host.
            3. Select the Deploy on as vmware Compute Resource.
            4. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :Caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier2
    def test_positive_power_on_off_vmware_vms(self):
        """Power on and off the vmware virtual machine

        :id: 846318e9-8b95-46ea-b7bc-26689064f80c

        :setup:

            1. Valid vmware hostname, credentials.
            2. Virtual machine in vmware.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.
            3. Click "Power on" button associated with the vm.
            4. Go to "Virtual Machines" tab.
            5. Click "Power off" button associated with the vm.

        :expectedresults: The Virtual machine is switched on and switched off

        :Caseautomation: Automated

        :Caselevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        cr_name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=cr_name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            if self.compute_resource.power_on_status(
                    cr_name, self.vmware_vm_name) == 'on':
                self.compute_resource.set_power_status(
                    cr_name, self.vmware_vm_name, False)
            self.assertEqual(self.compute_resource.set_power_status(
                cr_name, self.vmware_vm_name, True), u'On')
            self.assertEqual(self.compute_resource.set_power_status(
                cr_name, self.vmware_vm_name, False), u'Off')
