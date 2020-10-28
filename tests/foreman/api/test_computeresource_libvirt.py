# -*- encoding: utf-8 -*-
"""Unit tests for the ``compute_resource`` paths.

A full API reference for compute resources can be found here:
http://www.katello.org/docs/api/apidoc/compute_resources.html


:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import LIBVIRT_RESOURCE_URL
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.test import APITestCase


class ComputeResourceTestCase(APITestCase):
    """Tests for ``katello/api/v2/compute_resources``."""

    @classmethod
    @skip_if_not_set('compute_resources')
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

        :id: 1e545c56-2f53-44c1-a17e-38c83f8fe0c1

        :expectedresults: Compute resources are created with expected names

        :CaseImportance: Critical

        :CaseLevel: Component
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

        :id: 1fa5b35d-ee47-452b-bb5f-4a4ca321f992

        :expectedresults: Compute resources are created with expected
            descriptions

        :CaseImportance: Critical

        :CaseLevel: Component
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

    @tier2
    def test_positive_create_libvirt_with_display_type(self):
        """Create a libvirt compute resources with different values of
        'display_type' parameter

        :id: 76380f31-e217-4ff1-ac6b-20f41e59f133

        :expectedresults: Compute resources are created with expected
            display_type value

        :CaseImportance: High

        :CaseLevel: Component
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

        :id: f61c66c9-15f8-4b00-9e53-7ebfb09397cc

        :expectedresults: Compute resources are created with expected providers

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        entity = entities.LibvirtComputeResource()
        entity.location = [self.loc]
        entity.organization = [self.org]
        result = entity.create()
        self.assertEqual(result.provider, entity.provider)

    @tier2
    def test_positive_create_with_locs(self):
        """Create a compute resource with multiple locations

        :id: c6c6c6f7-50ca-4f38-8126-eb95359d7cbb

        :expectedresults: A compute resource is created with expected multiple
            locations assigned

        :CaseImportance: High

        :CaseLevel: Integration
        """
        locs = [entities.Location(organization=[self.org]).create() for _ in range(randint(3, 5))]
        compresource = entities.LibvirtComputeResource(
            location=locs, organization=[self.org], url=self.current_libvirt_url
        ).create()
        self.assertEqual(
            set(loc.name for loc in locs), set(loc.read().name for loc in compresource.location)
        )

    @tier2
    def test_positive_create_with_orgs(self):
        """Create a compute resource with multiple organizations

        :id: 2f6e5019-6353-477e-a81f-2a551afc7556

        :expectedresults: A compute resource is created with expected multiple
            organizations assigned

        :CaseImportance: High

        :CaseLevel: Integration
        """
        orgs = [entities.Organization().create() for _ in range(randint(3, 5))]
        compresource = entities.LibvirtComputeResource(
            organization=orgs, url=self.current_libvirt_url
        ).create()
        self.assertEqual(
            set(org.name for org in orgs),
            set(org.read().name for org in compresource.organization),
        )

    @tier1
    def test_positive_update_name(self):
        """Update a compute resource with different names

        :id: 60f08418-b1a2-445e-9cd6-dbc92a33b57a

        :expectedresults: Compute resource is updated with expected names

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc], organization=[self.org], url=self.current_libvirt_url
        ).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                compresource.name = new_name
                compresource = compresource.update(['name'])
                self.assertEqual(compresource.name, new_name)

    @tier2
    def test_positive_update_description(self):
        """Update a compute resource with different descriptions

        :id: aac5dc53-8709-441b-b360-28b8efd3f63f

        :expectedresults: Compute resource is updated with expected
            descriptions

        :CaseImportance: High

        :CaseLevel: Component
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

    @tier2
    def test_positive_update_libvirt_display_type(self):
        """Update a libvirt compute resource with different values of
        'display_type' parameter

        :id: 0cbf08ac-acc4-476a-b389-271cea2b6cda

        :expectedresults: Compute resource is updated with expected
            display_type value

        :CaseImportance: High

        :CaseLevel: Component
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

    @tier2
    def test_positive_update_url(self):
        """Update a compute resource's url field

        :id: 259aa060-ed9e-4ed5-91e1-7fb0a3592879

        :expectedresults: Compute resource is updated with expected url

        :CaseImportance: High

        :CaseLevel: Component
        """
        new_url = 'qemu+tcp://localhost:16509/system'

        compresource = entities.LibvirtComputeResource(
            location=[self.loc], organization=[self.org], url=self.current_libvirt_url
        ).create()
        compresource.url = new_url
        compresource = compresource.update(['url'])
        self.assertEqual(compresource.url, new_url)

    @tier2
    def test_positive_update_loc(self):
        """Update a compute resource's location

        :id: 57e96c7c-da9e-4400-af80-c374cd6b3d4a

        :expectedresults: Compute resource is updated with expected location

        :CaseImportance: High

        :CaseLevel: Integration
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc], organization=[self.org], url=self.current_libvirt_url
        ).create()
        new_loc = entities.Location(organization=[self.org]).create()
        compresource.location = [new_loc]
        compresource = compresource.update(['location'])
        self.assertEqual(len(compresource.location), 1)
        self.assertEqual(compresource.location[0].id, new_loc.id)

    @tier2
    def test_positive_update_locs(self):
        """Update a compute resource with new multiple locations

        :id: cda9f501-2879-4cb0-a017-51ee795232f1

        :expectedresults: Compute resource is updated with expected locations

        :CaseImportance: High

        :CaseLevel: Integration
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc], organization=[self.org], url=self.current_libvirt_url
        ).create()
        new_locs = [
            entities.Location(organization=[self.org]).create() for _ in range(randint(3, 5))
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

        :id: 430b64a2-7f64-4344-a73b-1b47d8dfa6cb

        :expectedresults: Compute resource is updated with expected
            organization

        :CaseImportance: High

        :CaseLevel: Integration
        """
        compresource = entities.LibvirtComputeResource(
            organization=[self.org], url=self.current_libvirt_url
        ).create()
        new_org = entities.Organization().create()
        compresource.organization = [new_org]
        compresource = compresource.update(['organization'])
        self.assertEqual(len(compresource.organization), 1)
        self.assertEqual(compresource.organization[0].id, new_org.id)

    @tier2
    def test_positive_update_orgs(self):
        """Update a compute resource with new multiple organizations

        :id: 2c759ad5-d115-46d9-8365-712c0bb39a1d

        :expectedresults: Compute resource is updated with expected
            organizations

        :CaseImportance: High

        :CaseLevel: Integration
        """
        compresource = entities.LibvirtComputeResource(
            organization=[self.org], url=self.current_libvirt_url
        ).create()
        new_orgs = [entities.Organization().create() for _ in range(randint(3, 5))]
        compresource.organization = new_orgs
        compresource = compresource.update(['organization'])
        self.assertEqual(
            set(organization.id for organization in compresource.organization),
            set(organization.id for organization in new_orgs),
        )

    @tier1
    def test_positive_delete(self):
        """Delete a compute resource

        :id: 0117a4f1-e2c2-44aa-8919-453166aeebbc

        :expectedresults: Compute resources is successfully deleted

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc], organization=[self.org], url=self.current_libvirt_url
        ).create()
        compresource.delete()
        with self.assertRaises(HTTPError):
            compresource.read()

    @tier2
    def test_negative_create_with_invalid_name(self):
        """Attempt to create compute resources with invalid names

        :id: f73bf838-3ffd-46d3-869c-81b334b47b13

        :expectedresults: Compute resources are not created

        :CaseImportance: High

        :CaseLevel: Component
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

    @tier2
    def test_negative_create_with_same_name(self):
        """Attempt to create a compute resource with already existing name

        :id: 9376e25c-2aa8-4d99-83aa-2eec160c030e

        :expectedresults: Compute resources is not created

        :CaseImportance: High

        :CaseLevel: Component
        """
        name = gen_string('alphanumeric')
        entities.LibvirtComputeResource(
            location=[self.loc], name=name, organization=[self.org], url=self.current_libvirt_url
        ).create()
        with self.assertRaises(HTTPError):
            entities.LibvirtComputeResource(
                location=[self.loc],
                name=name,
                organization=[self.org],
                url=self.current_libvirt_url,
            ).create()

    @tier2
    def test_negative_create_with_url(self):
        """Attempt to create compute resources with invalid url

        :id: 37e9bf39-382e-4f02-af54-d3a17e285c2a

        :expectedresults: Compute resources are not created

        :CaseImportance: High

        :CaseLevel: Component
        """
        for url in ('', gen_string('alpha')):
            with self.subTest(url):
                with self.assertRaises(HTTPError):
                    entities.LibvirtComputeResource(
                        location=[self.loc], organization=[self.org], url=url
                    ).create()

    @tier2
    def test_negative_update_invalid_name(self):
        """Attempt to update compute resource with invalid names

        :id: a6554c1f-e52f-4614-9fc3-2127ced31470

        :expectedresults: Compute resource is not updated

        :CaseImportance: High

        :CaseLevel: Component
        """
        name = gen_string('alphanumeric')
        compresource = entities.LibvirtComputeResource(
            location=[self.loc], name=name, organization=[self.org], url=self.current_libvirt_url
        ).create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    compresource.name = new_name
                    compresource.update(['name'])
                self.assertEqual(compresource.read().name, name)

    @tier2
    def test_negative_update_same_name(self):
        """Attempt to update a compute resource with already existing name

        :id: 4d7c5eb0-b8cb-414f-aa10-fe464a164ab4

        :expectedresults: Compute resources is not updated

        :CaseImportance: High

        :CaseLevel: Component
        """
        name = gen_string('alphanumeric')
        entities.LibvirtComputeResource(
            location=[self.loc], name=name, organization=[self.org], url=self.current_libvirt_url
        ).create()
        new_compresource = entities.LibvirtComputeResource(
            location=[self.loc], organization=[self.org], url=self.current_libvirt_url
        ).create()
        with self.assertRaises(HTTPError):
            new_compresource.name = name
            new_compresource.update(['name'])
        self.assertNotEqual(new_compresource.read().name, name)

    @tier2
    def test_negative_update_url(self):
        """Attempt to update a compute resource with invalid url

        :id: b5256090-2ceb-4976-b54e-60d60419fe50

        :expectedresults: Compute resources is not updated

        :CaseImportance: High

        :CaseLevel: Component
        """
        compresource = entities.LibvirtComputeResource(
            location=[self.loc], organization=[self.org], url=self.current_libvirt_url
        ).create()
        for url in ('', gen_string('alpha')):
            with self.subTest(url):
                with self.assertRaises(HTTPError):
                    compresource.url = url
                    compresource.update(['url'])
            self.assertNotEqual(compresource.read().url, url)
