"""Test for Compute Resource UI

:Requirement: Computeresource

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    COMPUTE_PROFILE_LARGE,
    FOREMAN_PROVIDERS

)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.api.utils import configure_provisioning
from robottelo.helpers import ProvisioningCheckError
from robottelo.test import UITestCase
from robottelo.ui.factory import make_resource, make_host
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


class RhevComputeResourceTestCase(UITestCase):
    """Implements Compute Resource tests in UI"""

    @classmethod
    @skip_if_not_set('rhev')
    def setUpClass(cls):
        super(RhevComputeResourceTestCase, cls).setUpClass()
        cls.rhev_url = settings.rhev.hostname
        cls.rhev_password = settings.rhev.password
        cls.rhev_username = settings.rhev.username
        cls.rhev_datacenter = settings.rhev.datacenter
        cls.rhev_img_name = settings.rhev.image_name
        cls.rhev_img_arch = settings.rhev.image_arch
        cls.rhev_img_os = settings.rhev.image_os
        cls.rhev_img_user = settings.rhev.image_username
        cls.rhev_img_pass = settings.rhev.image_password
        cls.rhev_vm_name = settings.rhev.vm_name
        cls.rhev_storage_domain = settings.rhev.storage_domain

    @run_only_on('sat')
    @tier1
    def test_positive_create_rhev_with_name(self):
        """Create a new rhev Compute Resource using different value
        types as a name

        :id: be735d8c-5644-4a42-9a08-2f9c6181a8c6

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Provide a valid name to rhev Compute Resource.
            4. Test the connection using Load Datacenter and submit.

        :CaseAutomation: Automated

        :expectedresults: A rhev CR is created successfully with proper
            connection.

        :CaseImportance: Critical
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['rhev'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1467664)
    @tier1
    def test_positive_create_rhev_with_same_name(self):
        """Create a new rhev Compute Resource with existing name correction

        :id: b9499d65-ef70-48b7-854a-f4cf740fbf9c

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Provide a valid name to rhev Compute Resource.
            4. Test the connection using Load Datacenter and submit.
            5. Create again a compute resource with same name.
            6. After error of name already taken,
               update with different name
            7. Click submit

        :CaseAutomation: Automated

        :expectedresults: A rhev CR is created successfully with proper
            connection.

        :CaseImportance: Critical

        :BZ: 1467664
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list
            )
            self.compute_resource.assign_value(
                locators['resource.name'],
                new_name
            )
            self.compute_resource.click(common_locators['submit'])
            self.assertIsNone(
                self.compute_resource.wait_until_element(
                    common_locators["alert.error"],
                    timeout=2,
                )
            )

    @run_only_on('sat')
    @tier1
    def test_positive_create_rhev_with_description(self):
        """Create rhev Compute Resource with description.

        :id: bd5e3066-395c-486e-bce8-b0a9bdd4e236

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Provide it with some valid description to rhev Compute Resource.
            4. Test the connection using Load Datacenter and submit.

        :CaseAutomation: Automated

        :expectedresults: A rhev Compute Resource is created successfully

        :CaseImportance: Critical
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            for description in valid_data_list():
                with self.subTest(description):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['rhev'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_rhev_with_invalid_name(self):
        """Create a new rhev Compute Resource with incorrect values
        only

        :id: 5598b123-b6ad-4bdf-b192-2b1ccc2f41eb

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Provide a invalid name to rhev Compute Resource.
            4. Test the connection using Load Datacenter and submit.

        :CaseAutomation: Automated

        :expectedresults: A rhev Compute Resource is not created

        :CaseImportance: Critical
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        with Session(self) as session:
            for name in invalid_names_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['rhev'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(
                        self.compute_resource.wait_until_element(
                            common_locators["name_haserror"]
                        )
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_update_rhev_name(self):
        """Update a rhev Compute Resource name

        :id: 62d0c495-c87e-42dd-91aa-9b9b728f7dda

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Provide a valid name to rhev Compute Resource.
            4. Test the connection using Load Datacenter and submit.
            5. Update the name of the created CR with valid string.

        :CaseAutomation: Automated

        :expectedresults: The rhev Compute Resource is updated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        newname = gen_string('alpha')
        name = gen_string('alpha')
        with Session(self) as session:
            with self.subTest(newname):
                make_resource(
                    session,
                    name=name,
                    provider_type=FOREMAN_PROVIDERS['rhev'],
                    parameter_list=parameter_list
                )
                self.assertIsNotNone(self.compute_resource.search(name))
                self.compute_resource.update(name=name, newname=newname)
                self.assertIsNotNone(self.compute_resource.search(newname))

    @run_only_on('sat')
    @tier2
    def test_positive_update_rhev_organization(self):
        """Update a rhev Compute Resource organization

        :id: f6656c8e-70a3-40e5-8dda-2154f2eeb042

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Provide a valid name to rhev Compute Resource.
            4. Test the connection using Load Datacenter and submit.
            5. Create a new organization.
            6. Add the new CR to organization that is created.

        :CaseAutomation: Automated

        :expectedresults: The rhev Compute Resource is updated
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
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
    def test_positive_delete_rhev(self):
        """Delete a rhev Compute Resource

        :id: 4a8b18f0-a2af-491a-bcf7-64d59a0fbc01

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Provide a valid name to rhev Compute Resource.
            4. Test the connection using Load Datacenter and submit.
            5. Delete the created compute resource.

        :CaseAutomation: Automated

        :expectedresults: The Compute Resource is deleted

        :CaseImportance: Critical
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            with self.subTest(name):
                make_resource(
                    session,
                    name=name,
                    provider_type=FOREMAN_PROVIDERS['rhev'],
                    parameter_list=parameter_list
                )
                self.assertIsNotNone(self.compute_resource.search(name))
                self.compute_resource.delete(name, dropdown_present=True)

    @run_only_on('sat')
    @tier2
    def test_positive_add_image_rhev_with_name(self):
        """Add images to the rhev compute resource

        :id: 6c7f4169-2e78-44d6-87af-434146093bcc

        :setup: rhev hostname, credentials and images as templates in rhev.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Select the created rhev CR and click images tab.
            4. Select "New image" , provide it valid name and information.
            5. Select the desired template to create image and submit.

        :CaseAutomation: Automated

        :expectedresults: The image is added to the CR successfully
         """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        with Session(self) as session:
            self.compute_resource.check_image_os(self.rhev_img_os)
            for img_name in valid_data_list():
                with self.subTest(img_name):
                    # Note: create a new compute resource for each sub test
                    # as using the same uuid image
                    cr_name = gen_string('alpha')
                    make_resource(
                        session,
                        name=cr_name,
                        provider_type=FOREMAN_PROVIDERS['rhev'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(self.compute_resource.search(cr_name))
                    parameter_list_img = [
                        ['Name', img_name],
                        ['Operatingsystem', self.rhev_img_os],
                        ['Architecture', self.rhev_img_arch],
                        ['Username', self.rhev_img_user],
                        ['Password', self.rhev_img_pass],
                        ['uuid', self.rhev_img_name],
                    ]
                    self.compute_resource.add_image(
                        cr_name, parameter_list_img)
                    self.assertIn(
                        img_name,
                        self.compute_resource.list_images(cr_name)
                    )

    @run_only_on('sat')
    @tier2
    def test_negative_add_image_rhev_with_invalid_name(self):
        """Add images to the rhev compute resource

        :id: 0054b389-1e2f-44d9-a306-0410fc0b9d99

        :setup: rhev hostname, credentials and images as templates in rhev.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Select the created rhev CR and click images tab.
            4. Select "New image", provide it invalid name and valid
               information.
            5. Select the desired template to create the image from and submit.

        :CaseAutomation: Automated

        :expectedresults: The image should not be added to the CR
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        with Session(self) as session:
            self.compute_resource.check_image_os(self.rhev_img_os)
            for img_name in invalid_names_list():
                with self.subTest(img_name):
                    # Note: create a new compute resource for each sub test as
                    # using the same uuid image.
                    # the images should not be created, but we need to have the
                    # sub tests isolated, and use the same scenario as positive
                    # test
                    cr_name = gen_string('alpha')
                    make_resource(
                        session,
                        name=cr_name,
                        provider_type=FOREMAN_PROVIDERS['rhev'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(self.compute_resource.search(cr_name))
                    parameter_list_img = [
                        ['Name', img_name],
                        ['Operatingsystem', self.rhev_img_os],
                        ['Architecture', self.rhev_img_arch],
                        ['Username', self.rhev_img_user],
                        ['Password', self.rhev_img_pass],
                        ['uuid', self.rhev_img_name],
                    ]
                    self.compute_resource.add_image(
                        cr_name, parameter_list_img)
                    self.assertIsNotNone(
                        self.compute_resource.wait_until_element(
                            common_locators["name_haserror"])
                    )
                    self.assertNotIn(
                        img_name,
                        self.compute_resource.list_images(cr_name)
                    )

    @run_only_on('sat')
    @tier2
    def test_positive_access_rhev_with_default_profile(self):
        """Associate default (3-Large) compute profile to rhev compute resource

        :id: 7049227e-f384-4aa1-8a01-228c3e7292a6

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Select the created rhev CR.
            4. Click Compute Profile tab.
            5. Select (3-Large) and submit.

        :CaseAutomation: Automated

        :expectedresults: The Compute Resource created and opened successfully
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_profile.select_resource(
                '3-Large', name, 'RHEV'))

    @run_only_on('sat')
    @tier2
    def test_positive_access_rhev_with_custom_profile(self):
        """Associate custom default (3-Large) compute profile to rhev compute resource

        :id: e7698154-62ff-492b-8e56-c5dc70f0c9df

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Select the created rhev CR.
            4. Click Compute Profile tab.
            5. Edit (3-Large) with valid configurations and submit.

        :expectedresults: The Compute Resource created and associated compute
            profile has provided values

        :BZ: 1286033

        :Caseautomation: Automated
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list
            )
            self.compute_resource.set_profile_values(
                name, COMPUTE_PROFILE_LARGE,
                cluster=self.rhev_datacenter,
                cores=2,
                memory=1024,
                network_interfaces=[
                    dict(
                        name='nic1',
                        network=settings.vlan_networking.bridge
                    ),
                    dict(
                        name='nic2',
                        network=settings.vlan_networking.bridge
                    ),
                ],
                storage=[
                    dict(
                        size='10',
                        storage_domain=self.rhev_storage_domain,
                        bootable=True,
                        preallocate_disk=True
                    ),
                    dict(
                        size='20',
                        storage_domain=self.rhev_storage_domain,
                        bootable=False,
                        preallocate_disk=False
                    )
                ]
            )
            values = self.compute_resource.get_profile_values(
                name,
                COMPUTE_PROFILE_LARGE,
                [
                    'cluster',
                    'cores',
                    'memory',
                    'size',
                    'storage_domain',
                    'bootable',
                    'preallocate_disk'
                ]
            )
            self.assertEqual(values['cluster'], self.rhev_datacenter)
            self.assertEqual(values['cores'], '2')
            self.assertEqual(values['memory'], '1 GB')
            self.assertEqual(values['size'], '10')
            self.assertEqual(
                values['storage_domain'], self.rhev_storage_domain)
            self.assertEqual(values['bootable'], True)
            self.assertEqual(values['preallocate_disk'], True)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1452534)
    @tier2
    def test_positive_access_rhev_with_custom_profile_with_template(self):
        """Associate custom default (3-Large) compute profile to rhev compute
         resource, with template

        :id: bb9794cc-6335-4621-92fd-fdc815f23263

        :setup: rhev hostname and credentials.

        :steps:

            1. Create a compute resource of type rhev.
            2. Provide it with the valid hostname, username and password.
            3. Select the created rhev CR.
            4. Click Compute Profile tab.
            5. Edit (3-Large) with valid configuration and template and submit.

        :expectedresults: The Compute Resource created and opened successfully

        :BZ: 1452534
        :Caseautomation: Automated
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list
            )
            self.compute_resource.set_profile_values(
                name, COMPUTE_PROFILE_LARGE,
                cluster=self.rhev_datacenter,
                template=self.rhev_img_name,
                cores=2,
                memory=1024
            )

    @run_only_on('sat')
    @tier2
    def test_positive_retrieve_rhev_vm_list(self):
        """Retrieve the Virtual machine list from rhev compute resource

        :id: f8cef7fb-e14c-4d12-9862-0e448a59ca50

        :setup: rhev hostname and credentials.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.

        :CaseAutomation: Automated

        :expectedresults: The Virtual machines should be displayed
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            vms = self.compute_resource.list_vms(name)
            self.assertTrue(self.rhev_vm_name in vms)

    @run_only_on('sat')
    @tier2
    def test_positive_rhev_vm_power_on_off(self):
        """The virtual machine in rhev cr should be powered on and off.

        :id: fb42e739-c35b-4c6f-a727-b99a4d695191

        :expectedresults: The virtual machine is switched on and switched off

        :CaseAutomation: Automated
        """
        parameter_list = [
            ['URL', self.rhev_url, 'field'],
            ['Username', self.rhev_username, 'field'],
            ['Password', self.rhev_password, 'field'],
            ['Datacenter', self.rhev_datacenter, 'special select'],
        ]
        cr_name = gen_string('alpha')
        with Session(self) as session:
            make_resource(
                session,
                name=cr_name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list
            )
            if self.compute_resource.power_on_status(
                    cr_name, self.rhev_vm_name) == 'on':
                self.compute_resource.set_power_status(
                    cr_name, self.rhev_vm_name, False)
            self.assertEqual(self.compute_resource.set_power_status(
                cr_name, self.rhev_vm_name, True), u'On')
            self.assertEqual(self.compute_resource.set_power_status(
                cr_name, self.rhev_vm_name, False), u'Off')


class RhevComputeResourceHostTestCase(UITestCase):
    """Implements Compute Resource tests in UI"""

    @classmethod
    @skip_if_not_set('rhev')
    def setUpClass(cls):
        super(RhevComputeResourceHostTestCase, cls).setUpClass()
        cls.rhev_url = settings.rhev.hostname
        cls.rhev_password = settings.rhev.password
        cls.rhev_username = settings.rhev.username
        cls.rhev_datacenter = settings.rhev.datacenter
        cls.rhev_img_name = settings.rhev.image_name
        cls.rhev_img_arch = settings.rhev.image_arch
        cls.rhev_img_os = settings.rhev.image_os
        cls.rhev_img_user = settings.rhev.image_username
        cls.rhev_img_pass = settings.rhev.image_password
        cls.rhev_vm_name = settings.rhev.vm_name
        cls.rhev_storage_domain = settings.rhev.storage_domain

        cls.org = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = cls.org.name
        cls.loc = entities.Location(
            name=gen_string('alpha'),
            organization=[cls.org],
        ).create()
        cls.loc_name = cls.loc.name
        cls.config_env = configure_provisioning(compute=True,
                                                org=cls.org,
                                                loc=cls.loc
                                                )

    def tearDown(self):
        """Delete the host to free the resources"""
        super(RhevComputeResourceHostTestCase, self).tearDown()
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            hosts = entities.Host().search(
                query={u'search': u'organization={0}'.format(self.org_name)})
            for host in hosts:
                host.delete()

    @skip_if_bug_open('bugzilla', 1467925)
    @skip_if_bug_open('bugzilla', 1467828)
    @skip_if_bug_open('bugzilla', 1466645)
    @run_only_on('sat')
    @tier3
    def test_positive_provision_rhev_with_image(self):
        """ Provision a host on rhev compute resource with image based

        :id: 80abd6b1-31cd-4f3e-949c-f1ca608d0bbb

        :setup: rhev hostname and credentials.

            1. Configured subnet for provisioning of the host.
            2. Configured domains for the host.
            3. Population of images into satellite from rhev templates.
            4. Activation key and CV for the host.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill in the required details.(eg name,loc, org).
            3. Select rhev compute resource from "Deploy on" drop down.
            4. Associate appropriate feature capsules.
            5. Go to "operating system tab".
            6. Edit Provisioning Method to image based.
            7. Select the appropriate image .
            8. Associate the activation key and submit.

        :expectedresults: The host should be provisioned successfully

        :CaseAutomation: Automated
        """
        hostname = gen_string('alpha', 9)
        cr_name = gen_string('alpha', 9)
        img_name = gen_string('alpha', 5)
        root_pwd = gen_string('alpha', 15)
        with Session(self) as session:
            parameter_list = [
                ['URL', self.rhev_url, 'field'],
                ['Username', self.rhev_username, 'field'],
                ['Password', self.rhev_password, 'field'],
                ['Datacenter', self.rhev_datacenter, 'special select'],
            ]
            make_resource(
                session,
                name=cr_name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list,
                orgs=[self.org_name], org_select=True,
                locations=[self.loc_name], loc_select=True
            )
            parameter_list_img = [
                ['Name', img_name],
                ['Operatingsystem', self.rhev_img_os],
                ['Architecture', self.rhev_img_arch],
                ['Username', self.rhev_img_user],
                ['Password', self.rhev_img_pass],
                ['uuid', self.rhev_img_name],
            ]
            self.compute_resource.add_image(cr_name, parameter_list_img)
            imgs = self.compute_resource.list_images(cr_name)
            self.assertTrue(img_name in imgs)
            self.compute_resource.set_profile_values(
                cr_name, COMPUTE_PROFILE_LARGE,
                cluster=self.rhev_datacenter,
                cores=2,
                memory=1024,
                image=self.rhev_img_name,
                network_interfaces=[
                    dict(
                        name='nic1',
                        network=settings.vlan_networking.bridge
                    ),
                ],
                storage=[
                    dict(
                        size='10',
                        storage_domain=self.rhev_storage_domain,
                        bootable=True,
                        preallocate_disk=False
                    ),
                ]
            )
            make_host(
                session,
                name=hostname,
                org=ANY_CONTEXT['org'],
                loc=self.loc_name,
                parameters_list=[
                    ['Host', 'Organization', self.org_name],
                    ['Host', 'Location', self.loc_name],
                    ['Host', 'Host group', self.config_env['host_group']],
                    ['Host', 'Deploy on', cr_name],
                    ['Host', 'Compute profile', COMPUTE_PROFILE_LARGE],
                    ['Host', 'Puppet Environment',
                        self.config_env['environment']],
                    ['Operating System', 'Operating System', self.rhev_img_os],
                    ['Operating System', 'Partition table',
                        self.config_env['ptable']],
                    ['Operating System', 'PXE loader', 'PXELinux BIOS'],
                    ['Operating System', 'Root password', root_pwd],
                ],
                provisioning_method='network'
            )
            self.assertIsNotNone(self.hosts.search(
                u'{0}.{1}'.format(hostname.lower(),
                                  self.config_env['domain']
                                  )))
            host_ip = entities.Host().search(query={
                'search': 'name={0}.{1} and organization="{3}"'.format(
                    hostname.lower(),
                    self.config_env['domain'],
                    self.org_name)
                    })[0].read().ip
            with self.assertNotRaises(ProvisioningCheckError):
                self.compute_resource.host_provisioning_check(host_ip)

    @skip_if_bug_open('bugzilla', 1467925)
    @skip_if_bug_open('bugzilla', 1467828)
    @run_only_on('sat')
    @tier3
    def test_positive_provision_rhev_with_compute_profile(self):
        """ Provision a host on rhev compute resource with compute profile
        default (3-Large)

        :id: fe4a05ef-d548-4c28-80d0-d17851fb4b03

        :setup: rhev hostname ,credentials and provisioning setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill in the required details.(eg name,loc, org).
            3. Select rhev compute resource from "Deploy on" drop down.
            4. Select the "Compute profile" from the drop down.
            5. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned successfully

        :CaseAutomation: Automated
        """
        hostname = gen_string('alpha', 9)
        cr_name = gen_string('alpha', 9)
        root_pwd = gen_string('alpha', 15)
        with Session(self) as session:
            parameter_list = [
                ['URL', self.rhev_url, 'field'],
                ['Username', self.rhev_username, 'field'],
                ['Password', self.rhev_password, 'field'],
                ['Datacenter', self.rhev_datacenter, 'special select'],
            ]
            make_resource(
                session,
                name=cr_name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list,
                orgs=[self.org_name], org_select=True,
                locations=[self.loc_name], loc_select=True
            )
            self.compute_resource.set_profile_values(
                cr_name, COMPUTE_PROFILE_LARGE,
                cluster=self.rhev_datacenter,
                cores=2,
                memory=1024,
                network_interfaces=[
                    dict(
                        name='nic1',
                        network=settings.vlan_networking.bridge
                    ),
                ],
                storage=[
                    dict(
                        size='10',
                        storage_domain=self.rhev_storage_domain,
                        bootable=True,
                        preallocate_disk=False
                    ),
                ]
            )
            make_host(
                session,
                name=hostname,
                org=ANY_CONTEXT['org'],
                loc=self.loc_name,
                parameters_list=[
                    ['Host', 'Organization', self.org_name],
                    ['Host', 'Location', self.loc_name],
                    ['Host', 'Host group', self.config_env['host_group']],
                    ['Host', 'Deploy on', cr_name],
                    ['Host', 'Compute profile', COMPUTE_PROFILE_LARGE],
                    ['Host', 'Puppet Environment',
                        self.config_env['environment']],
                    ['Operating System', 'Operating System', self.rhev_img_os],
                    ['Operating System', 'Partition table',
                        self.config_env['ptable']],
                    ['Operating System', 'PXE loader', 'PXELinux BIOS'],
                    ['Operating System', 'Root password', root_pwd],
                ],
                provisioning_method='network'
            )
            self.assertIsNotNone(self.hosts.search(
                u'{0}.{1}'.format(hostname.lower(),
                                  self.config_env['domain']
                                  )))
            host_ip = entities.Host().search(query={
                'search': 'name={0}.{1} and organization="{3}"'.format(
                    hostname.lower(),
                    self.config_env['domain'],
                    self.org_name)
                    })[0].read().ip
            with self.assertNotRaises(ProvisioningCheckError):
                self.compute_resource.host_provisioning_check(host_ip)

    @upgrade
    @skip_if_bug_open('bugzilla', 1467925)
    @skip_if_bug_open('bugzilla', 1467828)
    @run_only_on('sat')
    @tier3
    def test_positive_provision_rhev_with_custom_compute_settings(self):
        """ Provision a host on rhev compute resource with
         custom disk, cpu count and memory

        :id: a972c095-7567-4bb0-86cb-9bd835fed7b7

        :setup: rhev hostname ,credentials and provisioning setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill in the required details.(eg name,loc, org).
            3. Select rhev custom compute resource from "Deploy on" drop down.
            4. Select the custom compute profile" with custom disk size, cpu
               count and memory.
            5. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned with custom settings

        :CaseAutomation: Automated
        """
        hostname = gen_string('alpha', 9)
        cr_name = gen_string('alpha', 9)
        root_pwd = gen_string('alpha', 15)
        with Session(self) as session:
            parameter_list = [
                ['URL', self.rhev_url, 'field'],
                ['Username', self.rhev_username, 'field'],
                ['Password', self.rhev_password, 'field'],
                ['Datacenter', self.rhev_datacenter, 'special select'],
            ]
            make_resource(
                session,
                name=cr_name,
                provider_type=FOREMAN_PROVIDERS['rhev'],
                parameter_list=parameter_list,
                orgs=[self.org_name], org_select=True,
                locations=[self.loc_name], loc_select=True
            )
            self.compute_resource.set_profile_values(
                cr_name, COMPUTE_PROFILE_LARGE,
                cluster=self.rhev_datacenter,
                cores=2,
                memory=2024,
                network_interfaces=[
                    dict(
                        name='nic1',
                        network=settings.vlan_networking.bridge
                    ),
                    dict(
                        name='nic2',
                        network=settings.vlan_networking.bridge
                    ),
                ],
                storage=[
                    dict(
                        size='10',
                        storage_domain=self.rhev_storage_domain,
                        bootable=False,
                        preallocate_disk=True
                    ),
                    dict(
                        size='20',
                        storage_domain=self.rhev_storage_domain,
                        bootable=False,
                        preallocate_disk=False
                    )
                ]
            )
            make_host(
                session,
                name=hostname,
                org=ANY_CONTEXT['org'],
                loc=self.loc_name,
                parameters_list=[
                    ['Host', 'Organization', self.org_name],
                    ['Host', 'Location', self.loc_name],
                    ['Host', 'Host group', self.config_env['host_group']],
                    ['Host', 'Deploy on', cr_name],
                    ['Host', 'Compute profile', COMPUTE_PROFILE_LARGE],
                    ['Host', 'Puppet Environment',
                        self.config_env['environment']],
                    ['Operating System', 'Operating System', self.rhev_img_os],
                    ['Operating System', 'Partition table',
                        self.config_env['ptable']],
                    ['Operating System', 'PXE loader', 'PXELinux BIOS'],
                    ['Operating System', 'Root password', root_pwd],
                ],
                provisioning_method='network'
            )
            self.assertIsNotNone(self.hosts.search(
                u'{0}.{1}'.format(hostname.lower(),
                                  self.config_env['domain']
                                  )))
            host_ip = entities.Host().search(query={
                'search': 'name={0}.{1} and organization="{3}"'.format(
                    hostname.lower(),
                    self.config_env['domain'],
                    self.org_name)
                    })[0].read().ip
            with self.assertNotRaises(ProvisioningCheckError):
                self.compute_resource.host_provisioning_check(host_ip)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_rhev_with_host_group(self):
        """ Provision a host on rhev compute resource with
        the help of hostgroup.

        :id: e02fae7d-ac39-4068-ba82-ec0cf110aae8

        :setup: rhev hostname ,credentials provisioning setup and hostgroup

        :steps:

            1. Go to "Hosts --> New host".
            2. Assign the host group to the host.
            3. Select the Deploy on as rhev Compute Resource.
            4. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :Caseautomation: notautomated
        """
