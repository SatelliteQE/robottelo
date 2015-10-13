# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test for Compute Resource UI"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, LIBVIRT_RESOURCE_URL
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.factory import make_resource
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class ComputeResource(UITestCase):
    """Implements Compute Resource tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(ComputeResource, cls).setUpClass()
        cls.current_libvirt_url = (
            LIBVIRT_RESOURCE_URL % settings.server.hostname
        )

    @run_only_on('sat')
    def test_create_libvirt_resource_different_names(self):
        """@Test: Create a new libvirt Compute Resource using different value
        types as a name

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created successfully

        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['libvirt'],
                        parameter_list=[
                            ['URL', self.current_libvirt_url, 'field']
                        ],
                    )
                    search = self.compute_resource.search(name)
                    self.assertIsNotNone(search)

    @run_only_on('sat')
    def test_create_libvirt_resource_description(self):
        """@Test: Create libvirt Compute Resource with description.

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created successfully

        """
        with Session(self.browser) as session:
            for description in valid_data_list():
                with self.subTest(description):
                    name = gen_string('alpha')
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['libvirt'],
                        parameter_list=[
                            ['URL', self.current_libvirt_url, 'field'],
                            ['Description', description, 'field']
                        ],
                    )
                    search = self.compute_resource.search(name)
                    self.assertIsNotNone(search)

    @run_only_on('sat')
    def test_create_libvirt_resource_display_type(self):
        """@Test: Create libvirt Compute Resource with different display types.

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created successfully

        """
        with Session(self.browser) as session:
            for display_type in 'VNC', 'SPICE':
                with self.subTest(display_type):
                    name = gen_string('alpha')
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['libvirt'],
                        parameter_list=[
                            ['URL', self.current_libvirt_url, 'field'],
                            ['Display Type', display_type, 'select']
                        ],
                    )
                    search = self.compute_resource.search(name)
                    self.assertIsNotNone(search)

    @run_only_on('sat')
    def test_create_libvirt_resource_console_pass(self):
        """@Test: Create libvirt Compute Resource with checked/unchecked
        console password checkbox

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created successfully

        """
        with Session(self.browser) as session:
            for console_password in True, False:
                with self.subTest(console_password):
                    name = gen_string('alpha')
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['libvirt'],
                        parameter_list=[
                            ['URL', self.current_libvirt_url, 'field'],
                            ['Console Passwords', console_password, 'checkbox']
                        ],
                    )
                    search = self.compute_resource.search(name)
                    self.assertIsNotNone(search)

    @run_only_on('sat')
    def test_create_libvirt_resource_different_names_negative(self):
        """@Test: Create a new libvirt Compute Resource with incorrect values
        only

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is not created

        """
        include_list = [' ']
        with Session(self.browser) as session:
            for name in invalid_names_list() + include_list:
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['libvirt'],
                        parameter_list=[
                            ['URL', self.current_libvirt_url, 'field']
                        ],
                    )
                    self.assertIsNotNone(
                        self.compute_resource.wait_until_element(
                            common_locators["name_haserror"]
                        )
                    )

    @run_only_on('sat')
    def test_create_libvirt_resource_description_negative(self):
        """@Test: Create libvirt Compute Resource with incorrect description.

        @Feature: Compute Resource - Create with long description.

        @Assert: A libvirt Compute Resource is not created

        """
        with Session(self.browser) as session:
            for description in invalid_names_list():
                with self.subTest(description):
                    make_resource(
                        session,
                        name=gen_string('alpha'),
                        provider_type=FOREMAN_PROVIDERS['libvirt'],
                        parameter_list=[
                            ['URL', self.current_libvirt_url, 'field'],
                            ['Description', description, 'field']
                        ],
                    )
                    error_element = session.nav.wait_until_element(
                        common_locators["haserror"])
                    self.assertIsNotNone(error_element)

    @run_only_on('sat')
    def test_update_libvirt_resource_different_name(self):
        """@Test: Update a libvirt Compute Resource name

        @Feature: Compute Resource - Update

        @Assert: The libvirt Compute Resource is updated

        """
        with Session(self.browser) as session:
            for newname in valid_data_list():
                with self.subTest(newname):
                    name = gen_string('alpha')
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['libvirt'],
                        parameter_list=[
                            ['URL', self.current_libvirt_url, 'field']
                        ],
                    )
                    search = self.compute_resource.search(name)
                    self.assertIsNotNone(search)
                    self.compute_resource.update(name=name, newname=newname)
                    search = self.compute_resource.search(newname)
                    self.assertIsNotNone(search)

    @run_only_on('sat')
    def test_update_libvirt_resource_organization(self):
        """@Test: Update a libvirt Compute Resource organization

        @Feature: Compute Resource - Update

        @Assert: The libvirt Compute Resource is updated

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['libvirt'],
                parameter_list=[
                    ['URL', self.current_libvirt_url, 'field']],
                orgs=[entities.Organization().create().name],
                org_select=True
            )
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)
            self.compute_resource.update(
                name=name,
                orgs=[entities.Organization().create().name],
                org_select=True
            )

    @run_only_on('sat')
    def test_remove_resource(self):
        """@Test: Delete a Compute Resource

        @Feature: Compute Resource - Delete

        @Assert: The Compute Resource is deleted

        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['libvirt'],
                        parameter_list=[
                            ['URL', self.current_libvirt_url, 'field']
                        ],
                    )
                    self.assertIsNotNone(self.compute_resource.search(name))
                    self.compute_resource.delete(name)

    @run_only_on('sat')
    def test_access_docker_resource_via_compute_profile(self):
        """@Test: Try to access docker compute resource via compute profile
        (1-Small) screen

        @Feature: Compute Resource

        @Assert: The Compute Resource created and opened successfully

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['docker'],
                parameter_list=[[
                    'URL', settings.docker.external_url, 'field'
                ]],
            )
            self.assertIsNotNone(
                self.compute_profile.select_resource('1-Small', name, 'Docker')
            )
