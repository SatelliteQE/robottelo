#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import unittest
from robottelo.common import conf
from robottelo.common.helpers import generate_name
from robottelo.ui.locators import locators
from tests.ui.baseui import BaseUI


class ComputeResource(BaseUI):

    # would require some libvirt configuration on foreman host.
    @unittest.skip("Test needs to create other required stuff")
    def test_create_resource(self):
        "Test to create a new libvirt Compute Resource"
        name = generate_name(8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(name, provider_type="Libvirt", url=url)
        self.navigator.go_to_compute_resources()
        self.assertIsNotNone(self.compute_resource.search(name))

    @unittest.skip("Test needs to create other required stuff")
    def test_remove_resource(self):
        "Test to delete a Compute Resource "
        name = generate_name(8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(name, provider_type="Libvirt", url=url)
        self.navigator.go_to_compute_resources()
        self.compute_resource.delete(name, really=True)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))  # @IgnorePep8
