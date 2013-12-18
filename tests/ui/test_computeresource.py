#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import unittest
from tests.ui.baseui import BaseUI
from robottelo.ui.locators import locators
from robottelo.common.helpers import generate_name


class ComputeResource(BaseUI):

    @unittest.skip("Test needs to create other required stuff")
    def test_create_resource(self):
        "Test to create a new libvirt Compute Resource"
        name = generate_name(8)
        url = "qemu+tcp://xxx.yyy.com:16509/system"  # conf file needed
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(name, provider_type="Libvirt", url=url)
        self.assertIsNotNone(self.compute_resource.search(name))

    def test_remove_resource(self):
        "Test to delete a Compute Resource "
        name = generate_name(8)
        url = "qemu+tcp://xxx.yyy.com:16509/system"  # conf file needed
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(name, provider_type="Libvirt", url=url)
        self.assertIsNotNone(self.compute_resource.search(name))
        self.compute_resource.delete(name, really=True)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))  # @IgnorePep8
