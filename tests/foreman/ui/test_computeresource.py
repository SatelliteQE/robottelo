# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common import conf
from robottelo.common.constants import FOREMAN_PROVIDERS
from robottelo.common.decorators import skip_if_bz_bug_open
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string, generate_strings_list
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

    @attr('ui', 'resource', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_create_resource_1(self, name):
        """
        @Test: Create a new libvirt Compute Resource
        @Feature: Compute Resource - Create
        @Assert: A libvirt Compute Resource is created
        """
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name],
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    @skip_if_bz_bug_open("1120271")
    @attr('ui', 'resource', 'implemented')
    @data(*generate_strings_list(len1=255))
    def test_create_resource_2(self, name):
        """
        @Test: Create a new libvirt Compute Resource with 255 char name
        @Feature: Compute Resource - Create
        @Assert: A libvirt Compute Resource is created
        """
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name],
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    @attr('ui', 'resource', 'implemented')
    @data(*generate_strings_list(len1=255))
    def test_create_resource_3(self, desc):
        """
        @Test: Create a new libvirt Compute Resource with 255 char desc.
        @Feature: Compute Resource - Create with long desc.
        @Assert: A libvirt Compute Resource is not created with 256 char desc.
        """
        name = generate_string("alpha", 8)
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name], desc=desc,
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    @skip_if_bz_bug_open("1120271")
    @attr('ui', 'resource', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_create_resource_negative_1(self, name):
        """
        @Test: Create a new libvirt Compute Resource with 256 char name
        @Feature: Compute Resource - Create
        @Assert: A libvirt Compute Resource is not created
        """
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name],
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    @skip_if_bz_bug_open("1120271")
    @attr('ui', 'resource', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_create_resource_negative_2(self, desc):
        """
        @Test: Create a new libvirt Compute Resource with 256 char desc.
        @Feature: Compute Resource - Create with long desc.
        @Assert: A libvirt Compute Resource is not created with 256 char desc.
        """
        name = generate_string("alpha", 8)
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name], desc=desc,
                          provider_type=provider_type, url=url)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_create_resource_negative_3(self):
        """
        @Test: Create a new libvirt Compute Resource with whitespace
        @Feature: Compute Resource - Create
        @Assert: A libvirt Compute Resource is not created
        """
        name = "   "
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name],
                          provider_type=provider_type, url=url)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_create_resource_negative_4(self):
        """
        @Test: Create a new libvirt Compute Resource with name blank
        @Feature: Compute Resource - Create
        @Assert: A libvirt Compute Resource is not created
        """
        name = ""
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name],
                          provider_type=provider_type, url=url)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @attr('ui', 'resource', 'implemented')
    @data({'name': generate_string('alpha', 10),
           'newname': generate_string('alpha', 10)},
          {'name': generate_string('numeric', 10),
           'newname': generate_string('numeric', 10)},
          {'name': generate_string('alphanumeric', 10),
           'newname': generate_string('alphanumeric', 10)},
          {'name': generate_string('utf8', 10),
           'newname': generate_string('utf8', 10)},
          {'name': generate_string('latin1', 10),
           'newname': generate_string('latin1', 10)},
          {'name': generate_string('html', 10),
           'newname': generate_string('html', 10)})
    def test_update_resource(self, testdata):
        """
        @Test: Update a libvirt Compute Resource's Organization
        @Feature: Compute Resource - Update
        @Assert: The libvirt Compute Resource is updated
        """
        name = testdata['name']
        newname = testdata['newname']
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
            make_org(session, org_name=new_org)
            self.compute_resource.update(name, newname, [org_name], [new_org],
                                         libvirt_set_passwd=False)
            search = self.compute_resource.search(newname)
            self.assertIsNotNone(search)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_remove_resource(self, name):
        """
        @Test: Delete a Compute Resource
        @Feature: Compute Resource - Delete
        @Assert: The Compute Resource is deleted
        """
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
