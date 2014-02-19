# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import unittest
from robottelo.common.helpers import generate_name
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


class Host(BaseUI):

    @unittest.skip("Test needs to create other required stuff")
    def test_create_host(self):
        """
        @Feature: Host - Positive create
        @Test: Create a new Host
        @Assert: Host is created
        """
        # TODO need to create environment architecture domain etc
        name = generate_name(8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_hosts()
        self.hosts.create(name, "some.domain.redhat.com",
                          "lab2-subnet (10.10.10.0/24)", host_group=None,
                          resource="KVM_201199 (Libvirt)", env="test",
                          ip_addr=None, mac=None, os="rhel 6.5", arch="x86_64",
                          media="redhat_64", ptable="Kickstart default",
                          custom_ptable=None, root_pwd="redhat", cpus="1",
                          memory="768 MB")
        self.navigator.go_to_hosts()
        #confirm the Host appears in the UI
        search = self.hosts.search(name)
        self.assertIsNotNone(search)

    @unittest.skip("Test needs to create other required stuff")
    def test_create_delete(self):
        """
        @Feature: Host - Positive Delete
        @Test: Delete a Host
        @Assert: Host is deleted
        """
        # TODO need to create environment architecture domain etc
        name = generate_name(8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_hosts()
        self.hosts.create(name, "some.domain.redhat.com",
                          "lab2-subnet (10.10.10.0/24)", host_group=None,
                          resource="KVM_201199 (Libvirt)", env="test",
                          ip_addr=None, mac=None, os="rhel 6.5", arch="x86_64",
                          media="redhat_64", ptable="Kickstart default",
                          custom_ptable=None, root_pwd="redhat", cpus="1",
                          memory="768 MB")
        self.navigator.go_to_hosts()
        #confirm the Host appears in the UI
        self.hosts.delete(name, really=True)
        self.assertTrue(
            self.user.wait_until_element(common_locators["notif.success"]))
