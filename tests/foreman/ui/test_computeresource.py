# -*- encoding: utf-8 -*-
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import (
    FOREMAN_PROVIDERS,
    LIBVIRT_RESOURCE_URL,
)
from robottelo.decorators import data, run_only_on
from robottelo.helpers import (
    get_external_docker_url,
    invalid_names_list,
    valid_data_list,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_resource
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class ComputeResource(UITestCase):
    """Implements Compute Resource tests in UI"""

    current_libvirt_url = LIBVIRT_RESOURCE_URL % settings.server.hostname

    @data(*valid_data_list())
    def test_create_libvirt_resource_different_names(self, name):
        """@Test: Create a new libvirt Compute Resource using different value
        types as a name

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created successfully

        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['libvirt'],
                parameter_list=[['URL', self.current_libvirt_url, 'field']],
            )
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)

    @data(*valid_data_list())
    def test_create_libvirt_resource_description(self, description):
        """@Test: Create libvirt Compute Resource with description.

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created successfully

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
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

    @data('VNC', 'SPICE')
    def test_create_libvirt_resource_display_type(self, display_type):
        """@Test: Create libvirt Compute Resource with different display types.

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created successfully

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
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

    @data(True, False)
    def test_create_libvirt_resource_console_pass(self, console_password):
        """@Test: Create libvirt Compute Resource with checked/unchecked
        console password checkbox

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is created successfully

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
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

    @data(' ', *invalid_names_list())
    def test_create_libvirt_resource_different_names_negative(self, name):
        """@Test: Create a new libvirt Compute Resource with incorrect values
        only

        @Feature: Compute Resource - Create

        @Assert: A libvirt Compute Resource is not created

        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['libvirt'],
                parameter_list=[['URL', self.current_libvirt_url, 'field']],
            )
            self.assertIsNotNone(self.compute_resource.wait_until_element(
                common_locators["name_haserror"]
            ))

    @data(*invalid_names_list())
    def test_create_libvirt_resource_description_negative(self, description):
        """@Test: Create libvirt Compute Resource with incorrect description.

        @Feature: Compute Resource - Create with long description.

        @Assert: A libvirt Compute Resource is not created

        """
        with Session(self.browser) as session:
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

    @data(*valid_data_list())
    def test_update_libvirt_resource_different_name(self, newname):
        """@Test: Update a libvirt Compute Resource name

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
            )
            search = self.compute_resource.search(name)
            self.assertIsNotNone(search)
            self.compute_resource.update(name=name, newname=newname)
            search = self.compute_resource.search(newname)
            self.assertIsNotNone(search)

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

    @data(*valid_data_list())
    def test_remove_resource(self, name):
        """@Test: Delete a Compute Resource

        @Feature: Compute Resource - Delete

        @Assert: The Compute Resource is deleted

        """
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['libvirt'],
                parameter_list=[['URL', self.current_libvirt_url, 'field']],
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            self.compute_resource.delete(name)

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
                parameter_list=[['URL', get_external_docker_url(), 'field']],
            )
            self.assertIsNotNone(self.compute_profile.select_resource(
                '1-Small', name, 'Docker'))
