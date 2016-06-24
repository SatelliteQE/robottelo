from robottelo.test import UITestCase
from robottelo.common import conf
from robottelo.ui.session import Session
from robottelo.common.constants import FOREMAN_PROVIDERS
from robottelo.ui.factory import make_resource
from ddt import data, ddt
import time


@ddt
class ComputeResourceTestCase(UITestCase):

    default_org = 'Default Organization'
    default_loc = 'Default Location'

    vmware_name = conf.properties['vmware.name']
    vmware_vcenter = conf.properties['vmware.vcenter']
    vmware_username = conf.properties['vmware.username']
    vmware_password = conf.properties['vmware.password']
    vmware_datacenter = conf.properties['vmware.datacenter']
    vmware_vm_name = conf.properties['vmware.vm_name']
    vmware_url_name = 'vcenterserver'
    vmware_dc_locator = 'datacenter_vsphere'
    vmware_img_name = conf.properties['vmware.img_name']
    vmware_img_os = conf.properties['vmware.img_os']
    vmware_img_arch = conf.properties['vmware.img_arch']
    vmware_img_uname = conf.properties['vmware.img_username']
    vmware_img_passw = conf.properties['vmware.img_password']
    vmware_img = conf.properties['vmware.img_image']

    @data(
        {'name': vmware_name,
         'provider': FOREMAN_PROVIDERS['vmware'],
         'url': vmware_vcenter,
         'username': vmware_username,
         'password': vmware_password,
         'datacenter': vmware_datacenter,
         'url_name': vmware_url_name,
         'dc_locator': vmware_dc_locator}
    )
    def test_create_compute_resource(self, data):
        """ @Test: Create a compute resource.
        @Assert: A compute resource is created
        @Feature: Compute Resource
        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=data['name'],
                provider_type=data['provider'],
                parameter_list=[
                    [data['url_name'], data['url'], 'field'],
                    ['Username', data['username'], 'field'],
                    ['Password', data['password'], 'field'],
                    [data['dc_locator'], data['datacenter'], 'special select']
                ],
                orgs=[self.default_org],
                org_select=False,
                locations=[self.default_loc],
                loc_select=True
            )
            # nasty hack
            time.sleep(5)
            search = self.compute_resource.search(data['name'])
            self.assertIsNotNone(search)
            self.compute_resource.delete(data['name'])
            search = self.compute_resource.search(data['name'])
            self.assertIsNone(search)

    @data(
        {'name': vmware_name,
         'new_name': '%s-updated' % vmware_name,
         'provider': FOREMAN_PROVIDERS['vmware'],
         'url': vmware_vcenter,
         'username': vmware_username,
         'password': vmware_password,
         'datacenter': vmware_datacenter,
         'url_name': vmware_url_name,
         'dc_locator': vmware_dc_locator}
    )
    def test_edit_compute_resource(self, data):
        """ @Test: Edit a compute resource.
        @Assert: A compute resource with new name exists
        @Feature: Compute Resource
        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=data['name'],
                provider_type=data['provider'],
                parameter_list=[
                    [data['url_name'], data['url'], 'field'],
                    ['Username', data['username'], 'field'],
                    ['Password', data['password'], 'field'],
                    [data['dc_locator'], data['datacenter'], 'special select']
                ],
                orgs=[self.default_org],
                org_select=False,
                locations=[self.default_loc],
                loc_select=True
            )
            # nasty hack
            time.sleep(5)
            search = self.compute_resource.search(data['name'])
            self.assertIsNotNone(search)

            self.compute_resource.update(name=data['name'],
                                         newname=data['new_name'])
            search = self.compute_resource.search(data['new_name'])
            self.assertIsNotNone(search)

            self.compute_resource.delete(data['new_name'])
            search = self.compute_resource.search(data['new_name'])
            self.assertIsNone(search)

    @data(
        {'name': vmware_name,
         'provider': FOREMAN_PROVIDERS['vmware'],
         'url': vmware_vcenter,
         'username': vmware_username,
         'password': vmware_password,
         'datacenter': vmware_datacenter,
         'url_name': vmware_url_name,
         'dc_locator': vmware_dc_locator}
    )
    def test_retrieve_vm_list(self, data):
        """ @Test: Retrieve list of VMs.
        @Feature: Compute Resource
        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=data['name'],
                provider_type=data['provider'],
                parameter_list=[
                    [data['url_name'], data['url'], 'field'],
                    ['Username', data['username'], 'field'],
                    ['Password', data['password'], 'field'],
                    [data['dc_locator'], data['datacenter'], 'special select']
                ],
                orgs=[self.default_org],
                org_select=False,
                locations=[self.default_loc],
                loc_select=True
            )
            # nasty hack
            time.sleep(5)
            search = self.compute_resource.search(data['name'])
            self.assertIsNotNone(search)

            print "%s:" % data['name']
            for item in self.compute_resource.list_vms(data['name']):
                if item.text:
                    print "VM: %s" % item.text

            self.compute_resource.delete(data['name'])
            search = self.compute_resource.search(data['name'])
            self.assertIsNone(search)

    @data(
        {'name': vmware_name,
         'provider': FOREMAN_PROVIDERS['vmware'],
         'url': vmware_vcenter,
         'username': vmware_username,
         'password': vmware_password,
         'datacenter': vmware_datacenter,
         'url_name': vmware_url_name,
         'dc_locator': vmware_dc_locator}
    )
    def test_retrieve_template_list(self, data):
        """ @Test: Retrieve list of templates..
        @Feature: Compute Resource
        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=data['name'],
                provider_type=data['provider'],
                parameter_list=[
                    [data['url_name'], data['url'], 'field'],
                    ['Username', data['username'], 'field'],
                    ['Password', data['password'], 'field'],
                    [data['dc_locator'], data['datacenter'], 'special select']
                ],
                orgs=[self.default_org],
                org_select=False,
                locations=[self.default_loc],
                loc_select=True
            )
            # nasty hack
            time.sleep(5)
            search = self.compute_resource.search(data['name'])
            self.assertIsNotNone(search)

            print "%s:" % data['name']
            for item in self.compute_resource.list_images(data['name']):
                print "Image: %s" % item.text

            self.compute_resource.delete(data['name'])
            search = self.compute_resource.search(data['name'])
            self.assertIsNone(search)

    @data(
        {'name': vmware_name,
         'vm_name': vmware_vm_name,
         'provider': FOREMAN_PROVIDERS['vmware'],
         'url': vmware_vcenter,
         'username': vmware_username,
         'password': vmware_password,
         'datacenter': vmware_datacenter,
         'url_name': vmware_url_name,
         'dc_locator': vmware_dc_locator}
    )
    def test_vm_start_stop(self, data):
        """ @Test: Start & Stop a VM.
        @Feature: Compute Resource
        note: assuming the VM is powered down when starting this test
        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=data['name'],
                provider_type=data['provider'],
                parameter_list=[
                    [data['url_name'], data['url'], 'field'],
                    ['Username', data['username'], 'field'],
                    ['Password', data['password'], 'field'],
                    [data['dc_locator'], data['datacenter'], 'special select']
                ],
                orgs=[self.default_org],
                org_select=False,
                locations=[self.default_loc],
                loc_select=True
            )
            # nasty hack
            time.sleep(5)
            search = self.compute_resource.search(data['name'])
            self.assertIsNotNone(search)

            self.compute_resource.vm_action_start(data['name'],
                                                  data['vm_name'])
            self.compute_resource.vm_action_stop(data['name'],
                                                 data['vm_name'],
                                                 True)

            self.compute_resource.delete(data['name'])
            search = self.compute_resource.search(data['name'])
            self.assertIsNone(search)

    @data(
        {'name': vmware_name,
         'vm_name': vmware_vm_name,
         'provider': FOREMAN_PROVIDERS['vmware'],
         'url': vmware_vcenter,
         'username': vmware_username,
         'password': vmware_password,
         'datacenter': vmware_datacenter,
         'url_name': vmware_url_name,
         'dc_locator': vmware_dc_locator}
    )
    def test_delete_vm(self, data):
        """ @Test: Deletes a VM.
        @Feature: Compute Resource
        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=data['name'],
                provider_type=data['provider'],
                parameter_list=[
                    [data['url_name'], data['url'], 'field'],
                    ['Username', data['username'], 'field'],
                    ['Password', data['password'], 'field'],
                    [data['dc_locator'], data['datacenter'], 'special select']
                ],
                orgs=[self.default_org],
                org_select=False,
                locations=[self.default_loc],
                loc_select=True
            )
            # nasty hack
            time.sleep(5)
            search = self.compute_resource.search(data['name'])
            self.assertIsNotNone(search)

            self.compute_resource.vm_delete(data['name'], data['vm_name'],
                                            True)

            self.compute_resource.delete(data['name'])
            search = self.compute_resource.search(data['name'])
            self.assertIsNone(search)

    @data(
        {'name': vmware_name,
         'vm_name': vmware_vm_name,
         'provider': FOREMAN_PROVIDERS['vmware'],
         'url': vmware_vcenter,
         'username': vmware_username,
         'password': vmware_password,
         'datacenter': vmware_datacenter,
         'url_name': vmware_url_name,
         'dc_locator': vmware_dc_locator,
         'img_name': vmware_img_name,
         'img_os': vmware_img_os,
         'img_arch': vmware_img_arch,
         'img_uname': vmware_img_uname,
         'img_passw': vmware_img_passw,
         'img_img': vmware_img}
    )
    def test_add_image(self, data):
        """ @Test: Adds an image to compute resource.
        @Assert: Image added is on the first page
        @Feature: Compute Resource
        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=data['name'],
                provider_type=data['provider'],
                parameter_list=[
                    [data['url_name'], data['url'], 'field'],
                    ['Username', data['username'], 'field'],
                    ['Password', data['password'], 'field'],
                    [data['dc_locator'], data['datacenter'], 'special select']
                ],
                orgs=[self.default_org],
                org_select=False,
                locations=[self.default_loc],
                loc_select=True
            )
            # nasty hack
            time.sleep(5)
            search = self.compute_resource.search(data['name'])
            self.assertIsNotNone(search)

            parameter_list = [
                ['Name', data['img_name'], 'field'],
                ['Operatingsystem', data['img_os'], 'select'],
                ['Architecture', data['img_arch'], 'select'],
                ['Username', data['img_uname'], 'field'],
                ['Password', data['img_passw'], 'field'],
                ['Image', data['img_img'], 'field']
            ]
            self.compute_resource.add_image(data['name'], parameter_list)
            time.sleep(5)
            for item in self.compute_resource.list_images(data['name']):
                if item.text == data['img_name']:
                    search = True
            self.assertIsNotNone(search)

            self.compute_resource.delete(data['name'])
            search = self.compute_resource.search(data['name'])
            self.assertIsNone(search)
