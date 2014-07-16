# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common import conf
from robottelo.common.constants import FOREMAN_PROVIDERS
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc,
                                  make_resource)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class ComputeResource(UITestCase):
    """
    Implements Compute Resource tests in UI
    """

    org_name = None
    loc_name = None

    def setUp(self):
        super(ComputeResource, self).setUp()
        # Make sure to use the Class' org_name instance
        if (ComputeResource.org_name is None and
            ComputeResource.loc_name is None):
            ComputeResource.org_name = generate_string("alpha", 8)
            ComputeResource.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=ComputeResource.org_name)
                make_loc(session, name=ComputeResource.loc_name)

    def test_create_resource(self):
        """
        @Test: Create a new libvirt Compute Resource
        @Feature: Compute Resource - Create
        @Assert: A libvirt Compute Resource is created
        """
        name = generate_string("alpha", 8)
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name],
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    def test_update_resource(self):
        """
        @Test: Update a libvirt Compute Resource
        @Feature: Compute Resource - Update
        @Assert: The libvirt Compute Resource is updated
        """
        name = generate_string("alpha", 8)
        newname = generate_string("alpha", 8)
        org_name = generate_string("alpha", 8)
        new_org = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name],
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)
            self.compute_resource.update(name, newname, [org_name], [new_org],
                                         libvirt_set_passwd=False)
            search = self.compute_resource.search(newname)
            self.assertIsNotNone(search)

    def test_remove_resource(self):
        """
        @Test: Delete a Compute Resource
        @Feature: Compute Resource - Delete
        @Assert: The Compute Resource is deleted
        """
        name = generate_string("alpha", 8)
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name],
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)
            self.compute_resource.delete(name, really=True)
            notif = session.nav.wait_until_element(
                common_locators["notif.success"])
            self.assertTrue(notif)
