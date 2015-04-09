# -*- encoding: utf-8 -*-
from ddt import ddt
from fauxfactory import gen_string
from robottelo.common import conf
from robottelo.common.constants import FOREMAN_PROVIDERS
from robottelo.common.decorators import run_only_on
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_resource
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session
from robottelo import entities


@run_only_on('sat')
@ddt
class ComputeResource(UITestCase):
    """Implements Compute Resource tests in UI"""

    @data(*generate_strings_list(len1=8))
    def test_create_resource_1(self, name):
        """@Test: Create a new libvirt Compute Resource

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created

        """
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name,
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    @data(
        gen_string('alphanumeric', 255),
        gen_string('alpha', 255),
        gen_string('numeric', 255),
        gen_string('latin1', 255),
        gen_string('utf8', 255)
    )
    def test_create_resource_2(self, name):
        """@Test: Create a new libvirt Compute Resource with 255 char name

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created

        """
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name,
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    @data(
        gen_string('alphanumeric', 255),
        gen_string('alpha', 255),
        gen_string('numeric', 255),
        gen_string('latin1', 255),
        gen_string('utf8', 255)
    )
    def test_create_resource_3(self, description):
        """@Test: Create libvirt Compute Resource with 255 char description.

        @Feature: Compute Resource - Create with long description.

        @Assert: A libvirt Compute Resource is not created with 255 char
        description.

        """
        name = gen_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name,
                          description=description,
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    @data(*generate_strings_list(len1=256))
    def test_create_resource_negative_1(self, name):
        """@Test: Create a new libvirt Compute Resource with 256 char name

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is not created

        """
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name,
                          provider_type=provider_type, url=url)
            self.assertIsNotNone(self.compute_resource.wait_until_element(
                common_locators["name_haserror"]
            ))

    @data(*generate_strings_list(len1=256))
    def test_create_resource_negative_2(self, description):
        """@Test: Create libvirt Compute Resource with 256 char description.

        @Feature: Compute Resource - Create with long description.

        @Assert: A libvirt Compute Resource is not created with 256 char
        description.

        """
        name = gen_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name,
                          description=description,
                          provider_type=provider_type, url=url)
            error_element = session.nav.wait_until_element(
                common_locators["haserror"])
            self.assertIsNotNone(error_element)

    @data("", "  ")
    def test_create_resource_negative_3(self, name):
        """@Test: Create a new libvirt Compute Resource with whitespace

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is not created

        """
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name,
                          provider_type=provider_type, url=url)
            error_element = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error_element)

    @data({'name': gen_string('alpha'),
           'newname': gen_string('alpha')},
          {'name': gen_string('numeric'),
           'newname': gen_string('numeric')},
          {'name': gen_string('alphanumeric'),
           'newname': gen_string('alphanumeric')},
          {'name': gen_string('utf8'),
           'newname': gen_string('utf8')},
          {'name': gen_string('latin1'),
           'newname': gen_string('latin1')},
          {'name': gen_string('html'),
           'newname': gen_string('html')})
    def test_update_resource(self, testdata):
        """@Test: Update a libvirt Compute Resource's Organization

        @Feature: Compute Resource - Update

        @Assert: The libvirt Compute Resource is updated

        """
        name = testdata['name']
        newname = testdata['newname']
        org_name1 = entities.Organization(
            name=gen_string("alpha", 8)
        ).create_json()['name']
        org_name2 = entities.Organization(
            name=gen_string("alpha", 8)
        ).create_json()['name']
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name, orgs=[org_name1],
                          provider_type=provider_type, url=url,
                          org_select=True)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)
            self.compute_resource.update(name, newname,
                                         [org_name1], [org_name2],
                                         libvirt_set_passwd=False)
            search = self.compute_resource.search(newname)
            self.assertIsNotNone(search)

    @data(*generate_strings_list(len1=8))
    def test_remove_resource(self, name):
        """@Test: Delete a Compute Resource

        @Feature: Compute Resource - Delete

        @Assert: The Compute Resource is deleted

        """
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=name,
                          provider_type=provider_type, url=url)
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)
            self.compute_resource.delete(name, really=True)
            self.assertIsNone(self.compute_resource.search(name))
