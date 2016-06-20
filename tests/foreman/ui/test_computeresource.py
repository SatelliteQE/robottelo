# -*- encoding: utf-8 -*-
"""Test for Compute Resource UI

@Requirement: Computeresource

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
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
            LIBVIRT_RESOURCE_URL % settings.compute_resources.libvirt_hostname
        )

    @run_only_on('sat')
    @tier1
    def test_positive_create_libvirt_with_name(self):
        """Create a new libvirt Compute Resource using different value
        types as a name

        @id: 71307d6d-04be-431f-b8fc-81ea883b4f19

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

        @id: 0ef00468-d6e6-449b-be3e-de95ba03a73b

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

        @id: 95e8cf49-8cb5-4c3b-9b21-8d33c51c9ac6

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

        @id: 26726673-a467-47d5-b24a-4535b98b3e50

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

        @id: 4d9be6b5-f9d4-402e-ad13-843335d83879

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

        @id: 508d34bd-491c-461d-b568-7063c68e971d

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

        @id: a1c3fd14-62e9-4e80-8ef7-bfa36420ce9b

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

        @id: 2790e1c2-ecdc-4257-9912-49b50891aa1f

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

        @id: 860b0036-24ab-49de-8d99-75243444df06

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
