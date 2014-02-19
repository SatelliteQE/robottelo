# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.common import conf
from robottelo.common.helpers import generate_name
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


class ComputeResource(BaseUI):
    def create_org(self, org_name=None):
        """Creates Org"""
        org_name = org_name or generate_name(8, 8)
        self.navigator.go_to_org()  # go to org page
        self.org.create(org_name)

    def test_create_resource(self):
        """
        @Feature: Compute Resource - Create
        @Test: Create a new libvirt Compute Resource
        @Assert: A libvirt Compute Resource is created
        """
        name = generate_name(8)
        org_name = generate_name(8, 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(name, [org_name], provider_type="Libvirt",
                                     url=url)
        self.navigator.go_to_compute_resources()
        search = self.compute_resource.search(name)
        self.assertIsNotNone(search)

    def test_update_resource(self):
        """
        @Feature: Compute Resource - Update
        @Test: Update a libvirt Compute Resource
        @Assert: The libvirt Compute Resource is updated
        """
        name = generate_name(8)
        newname = generate_name(8)
        org_name = generate_name(8, 8)
        new_org = generate_name(8, 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.create_org(new_org)
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(name, [org_name],
                                     provider_type="Libvirt", url=url)
        self.navigator.go_to_compute_resources()
        self.compute_resource.update(name, newname, [org_name], [new_org],
                                     libvirt_set_passwd=False)
        self.navigator.go_to_compute_resources()
        search = self.compute_resource.search(newname)
        self.assertIsNotNone(search)

    def test_remove_resource(self):
        """
        @Feature: Compute Resource - Delete
        @Test: Delete a Compute Resource
        @Assert: The Compute Resource is deleted
        """
        name = generate_name(8)
        org_name = generate_name(8, 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(name, [org_name], provider_type="Libvirt",
                                     url=url)
        self.navigator.go_to_compute_resources()
        self.compute_resource.delete(name, really=True)
        notif = self.user.wait_until_element(common_locators["notif.success"])
        self.assertTrue(notif)
