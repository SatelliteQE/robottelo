# -*- encoding: utf-8 -*-
"""Unit tests for the ``compute_resource`` paths.

A full API reference for compute resources can be found here:
http://www.katello.org/docs/api/apidoc/compute_resources.html

"""
from fauxfactory import gen_string
from nailgun import entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.constants import LIBVIRT_RESOURCE_URL
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import tier1, tier2
from robottelo.test import APITestCase


class ComputeResourceTestCase(APITestCase):
    """Tests for ``katello/api/v2/compute_resources``."""

    @classmethod
    def setUpClass(cls):
        """Set up organization and location for tests."""
        super(ComputeResourceTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()
        cls.current_libvirt_url = (
            LIBVIRT_RESOURCE_URL % settings.compute_resources.libvirt_hostname
        )

    @tier1
    def test_positive_create_with_name(self):
        """Create compute resources with different names

        @Feature: Compute Resource

        @Assert: Compute resources are created with expected names
        """
        for name in valid_data_list():
            with self.subTest(name):
                compresource = entities.LibvirtComputeResource(
                    location=[self.loc],
                    name=name,
                    organization=[self.org],
                    url=self.current_libvirt_url,
                ).create()
                self.assertEqual(compresource.name, name)

    @tier1
    def test_positive_create_with_description(self):
        """Create compute resources with different descriptions

        @Feature: Compute Resource

        @Assert: Compute resources are created with expected descriptions
        """
        for description in valid_data_list():
            with self.subTest(description):
                compresource = entities.LibvirtComputeResource(
                    description=description,
                    location=[self.loc],
                    organization=[self.org],
                    url=self.current_libvirt_url,
                ).create()
                self.assertEqual(compresource.description, description)

    @tier1
    def test_positive_create_libvirt_with_display_type(self):
        """Create a libvirt compute resources with different values of
        'display_type' parameter

        @Feature: Compute Resource

        @Assert: Compute resources are created with expected display_type value
        """
        for display_type in ('spice', 'vnc'):
            with self.subTest(display_type):
                compresource = entities.LibvirtComputeResource(
                    display_type=display_type,
                    location=[self.loc],
                    organization=[self.org],
                    url=self.current_libvirt_url,
                ).create()
                self.assertEqual(compresource.display_type, display_type)

    @tier1
    def test_positive_create_with_provider(self):
        """Create compute resources with different providers. Testing only
        Libvirt and Docker as other providers require valid credentials

        @Feature: Compute Resource

        @Assert: Compute resources are created with expected providers
        """
        for entity in (entities.DockerComputeResource(),
                       entities.LibvirtComputeResource()):
            with self.subTest(entity):
                entity.location = [self.loc]
                entity.organization = [self.org]
                result = entity.create()
                self.assertEqual(result.provider, entity.provider)

    @tier2
    def test_positive_create_with_locs(self):
        """Create a compute resource with multiple locations

        @Feature: Compute Resource

        @Assert: A compute resource is created with expected multiple locations
        assigned
        """
        locs = [
            entities.Location(organization=[self.org]).create()
            for _ in range(randint(3, 5))
        ]
        compresource = entities.LibvirtComputeResource(
            location=locs,
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        self.assertEqual(
            set(loc.name for loc in locs),
            set(loc.read().name for loc in compresource.location)
        )

    @tier2
    def test_positive_create_with_orgs(self):
        """Create a compute resource with multiple organizations

        @Feature: Compute Resource

        @Assert: A compute resource is created with expected multiple
        organizations assigned
        """
        orgs = [
            entities.Organization().create()
            for _ in range(randint(3, 5))
        ]
        compresource = entities.LibvirtComputeResource(
            organization=orgs,
            url=self.current_libvirt_url,
        ).create()
        self.assertEqual(
            set(org.name for org in orgs),
            set(org.read().name for org in compresource.organization)
        )

    @tier1
    def test_positive_update_name(self):
        """Update a compute resource with different names

        @Feature: Compute Resource

        @Assert: Compute resource is updated with expected names
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                compresource.name = new_name
                compresource = compresource.update(['name'])
                self.assertEqual(compresource.name, new_name)

    @tier1
    def test_positive_update_description(self):
        """Update a compute resource with different descriptions

        @Feature: Compute Resource

        @Assert: Compute resource is updated with expected descriptions
        """
        compresource = entities.LibvirtComputeResource(
            description=gen_string('alpha'),
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        for new_description in valid_data_list():
            with self.subTest(new_description):
                compresource.description = new_description
                compresource = compresource.update(['description'])
                self.assertEqual(compresource.description, new_description)

    @tier1
    def test_positive_update_libvirt_display_type(self):
        """Update a libvirt compute resource with different values of
        'display_type' parameter

        @Feature: Compute Resource

        @Assert: Compute resource is updated with expected display_type value
        """
        compresource = entities.LibvirtComputeResource(
            display_type='VNC',
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        for display_type in ('spice', 'vnc'):
            with self.subTest(display_type):
                compresource.display_type = display_type
                compresource = compresource.update(['display_type'])
                self.assertEqual(compresource.display_type, display_type)

    @tier1
    def test_positive_update_url(self):
        """Update a compute resource's url field

        @Feature: Compute Resource

        @Assert: Compute resource is updated with expected url
        """
        new_url = 'qemu+tcp://localhost:16509/system'

        compresource = entities.LibvirtComputeResource(
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        compresource.url = new_url
        compresource = compresource.update(['url'])
        self.assertEqual(compresource.url, new_url)

    @tier2
    def test_positive_update_loc(self):
        """Update a compute resource's location

        @Feature: Compute Resource

        @Assert: Compute resource is updated with expected location
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        new_loc = entities.Location(organization=[self.org]).create()
        compresource.location = [new_loc]
        compresource = compresource.update(['location'])
        self.assertEqual(len(compresource.location), 1)
        self.assertEqual(compresource.location[0].id, new_loc.id)

    @tier2
    def test_positive_update_locs(self):
        """Update a compute resource with new multiple locations

        @Feature: Compute Resource

        @Assert: Compute resource is updated with expected locations
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        new_locs = [
            entities.Location(organization=[self.org]).create()
            for _ in range(randint(3, 5))
        ]
        compresource.location = new_locs
        compresource = compresource.update(['location'])
        self.assertEqual(
            set(location.id for location in compresource.location),
            set(location.id for location in new_locs),
        )

    @tier2
    def test_positive_update_org(self):
        """Update a compute resource's organization

        @Feature: Compute Resource

        @Assert: Compute resource is updated with expected organization
        """
        compresource = entities.LibvirtComputeResource(
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        new_org = entities.Organization().create()
        compresource.organization = [new_org]
        compresource = compresource.update(['organization'])
        self.assertEqual(len(compresource.organization), 1)
        self.assertEqual(compresource.organization[0].id, new_org.id)

    @tier2
    def test_positive_update_orgs(self):
        """Update a compute resource with new multiple organizations

        @Feature: Compute Resource

        @Assert: Compute resource is updated with expected organizations
        """
        compresource = entities.LibvirtComputeResource(
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        new_orgs = [
            entities.Organization().create()
            for _ in range(randint(3, 5))
        ]
        compresource.organization = new_orgs
        compresource = compresource.update(['organization'])
        self.assertEqual(
            set(organization.id for organization in compresource.organization),
            set(organization.id for organization in new_orgs),
        )

    @tier1
    def test_positive_delete(self):
        """Delete a compute resource

        @Feature: Compute Resource

        @Assert: Compute resources is successfully deleted
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        compresource.delete()
        with self.assertRaises(HTTPError):
            compresource.read()

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Attempt to create compute resources with invalid names

        @Feature: Compute Resource

        @Assert: Compute resources are not created
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.LibvirtComputeResource(
                        location=[self.loc],
                        name=name,
                        organization=[self.org],
                        url=self.current_libvirt_url,
                    ).create()

    @tier1
    def test_negative_create_with_same_name(self):
        """Attempt to create a compute resource with already existing name

        @Feature: Compute Resource

        @Assert: Compute resources is not created
        """
        name = gen_string('alphanumeric')
        entities.LibvirtComputeResource(
            location=[self.loc],
            name=name,
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        with self.assertRaises(HTTPError):
            entities.LibvirtComputeResource(
                location=[self.loc],
                name=name,
                organization=[self.org],
                url=self.current_libvirt_url,
            ).create()

    @tier1
    def test_negative_create_with_url(self):
        """Attempt to create compute resources with invalid url

        @Feature: Compute Resource

        @Assert: Compute resources are not created
        """
        for url in ('', gen_string('alpha')):
            with self.subTest(url):
                with self.assertRaises(HTTPError):
                    entities.LibvirtComputeResource(
                        location=[self.loc],
                        organization=[self.org],
                        url=url,
                    ).create()

    @tier1
    def test_negative_update_invalid_name(self):
        """Attempt to update compute resource with invalid names

        @Feature: Compute Resource

        @Assert: Compute resource is not updated
        """
        name = gen_string('alphanumeric')
        compresource = entities.LibvirtComputeResource(
            location=[self.loc],
            name=name,
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    compresource.name = new_name
                    compresource.update(['name'])
                self.assertEqual(compresource.read().name, name)

    @tier1
    def test_negative_update_same_name(self):
        """Attempt to update a compute resource with already existing name

        @Feature: Compute Resource

        @Assert: Compute resources is not updated
        """
        name = gen_string('alphanumeric')
        entities.LibvirtComputeResource(
            location=[self.loc],
            name=name,
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        new_compresource = entities.LibvirtComputeResource(
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        with self.assertRaises(HTTPError):
            new_compresource.name = name
            new_compresource.update(['name'])
        self.assertNotEqual(new_compresource.read().name, name)

    @tier1
    def test_negative_update_url(self):
        """Attempt to update a compute resource with invalid url

        @Feature: Compute Resource

        @Assert: Compute resources is not updated
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc],
            organization=[self.org],
            url=self.current_libvirt_url,
        ).create()
        for url in ('', gen_string('alpha')):
            with self.subTest(url):
                with self.assertRaises(HTTPError):
                    compresource.url = url
                    compresource.update(['url'])
            self.assertNotEqual(compresource.read().url, url)
