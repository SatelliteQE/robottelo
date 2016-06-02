# -*- encoding: utf-8 -*-
"""Test for Compute Resource UI"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, LIBVIRT_RESOURCE_URL
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_resource
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class ComputeResourceTestCase(UITestCase):
    """Implements Compute Resource tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(ComputeResourceTestCase, cls).setUpClass()
        cls.current_libvirt_url = (
            LIBVIRT_RESOURCE_URL % settings.server.hostname
        )

    @run_only_on('sat')
    @tier1
    def test_positive_create_libvirt_with_name(self):
        """Create a new libvirt Compute Resource using different value
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
    @tier1
    def test_positive_create_libvirt_with_description(self):
        """Create libvirt Compute Resource with description.

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
    @tier1
    def test_positive_create_libvirt_with_display_type(self):
        """Create libvirt Compute Resource with different display types.

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
    @tier1
    def test_positive_create_libvirt_with_console_password(self):
        """Create libvirt Compute Resource with checked/unchecked
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
    @tier1
    def test_negative_create_libvirt_with_invalid_name(self):
        """Create a new libvirt Compute Resource with incorrect values
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
    @tier1
    def test_positive_update_libvirt_name(self):
        """Update a libvirt Compute Resource name

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
    @tier1
    def test_positive_update_libvirt_organization(self):
        """Update a libvirt Compute Resource organization

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
    @tier1
    def test_positive_delete(self):
        """Delete a Compute Resource

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
    @tier1
    def test_positive_access_libvirt_via_profile(self):
        """Try to access libvirt compute resource via compute profile
        (1-Small) screen

        @Feature: Compute Resource

        @Assert: The Compute Resource created and opened successfully
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['libvirt'],
                parameter_list=[[
                    'URL', self.current_libvirt_url, 'field'
                ]],
            )
            self.assertIsNotNone(self.compute_profile.select_resource(
                '1-Small', name, 'Libvirt'))
