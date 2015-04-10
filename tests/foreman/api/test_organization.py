"""Unit tests for the ``organizations`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here:
http://theforeman.org/api/apidoc/v2/organizations.html

"""
import ddt
import httplib
import sys
from fauxfactory import gen_string
from nailgun import client
from requests.exceptions import HTTPError
from robottelo import entities
from robottelo.common.helpers import get_server_credentials
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


@ddt.ddt
class OrganizationTestCase(APITestCase):
    """Tests for the ``organizations`` path."""

    def test_create_text_plain(self):
        """@Test Create an organization using a 'text/plain' content-type.

        @Assert: HTTP 415 is returned.

        @Feature: Organization

        """
        organization = entities.Organization()
        organization.create_missing()
        response = client.post(
            organization.path(),
            organization.create_payload(),
            auth=get_server_credentials(),
            headers={'content-type': 'text/plain'},
            verify=False,
        )
        self.assertEqual(httplib.UNSUPPORTED_MEDIA_TYPE, response.status_code)

    def test_positive_create_1(self):
        """@Test: Create an organization and provide a name.

        @Assert: The organization has the provided attributes and an
        auto-generated label.

        @Feature: Organization

        """
        attrs = entities.Organization().create_json()
        self.assertTrue('label' in attrs.keys())
        if sys.version_info[0] is 2:
            self.assertIsInstance(attrs['label'], unicode)
        else:
            self.assertIsInstance(attrs['label'], str)

    def test_positive_create_2(self):
        """@Test: Create an org and provide a name and identical label.

        @Assert: The organization has the provided attributes.

        @Feature: Organzation

        """
        # A label has a more restrictive allowable charset than a name.
        name_label = entities.Organization.label.gen_value()
        attrs = entities.Organization(
            name=name_label,
            label=name_label,
        ).create_json()
        self.assertEqual(attrs['name'], name_label)
        self.assertEqual(attrs['label'], name_label)

    def test_positive_create_3(self):
        """@Test: Create an organization and provide a name and label.

        @Assert: The organization has the provided attributes.

        @Feature: Organization

        """
        name = entities.Organization.name.gen_value()
        label = entities.Organization.label.gen_value()
        attrs = entities.Organization(name=name, label=label).create_json()
        self.assertEqual(attrs['name'], name)
        self.assertEqual(attrs['label'], label)

    @ddt.data(
        # two-tuples of data
        (gen_string(str_type='alpha'),
         gen_string(str_type='alpha')),
        (gen_string(str_type='alphanumeric'),
         gen_string(str_type='alphanumeric')),
        (gen_string(str_type='cjk'),
         gen_string(str_type='cjk')),
        (gen_string(str_type='latin1'),
         gen_string(str_type='latin1')),
        (gen_string(str_type='numeric'),
         gen_string(str_type='numeric')),
        (gen_string(str_type='utf8'),
         gen_string(str_type='utf8')),
    )
    @ddt.unpack
    def test_positive_create_4(self, name, description):
        """@Test: Create an organization and provide a name and description.

        @Assert: The organization has the provided attributes and an
        auto-generated label.

        @Feature: Organization

        """
        attrs = entities.Organization(
            name=name,
            description=description,
        ).create_json()
        self.assertEqual(name, attrs['name'])
        self.assertEqual(description, attrs['description'])

        # Was a label auto-generated?
        self.assertTrue('label' in attrs.keys())
        if sys.version_info[0] is 2:
            self.assertIsInstance(attrs['label'], unicode)
        else:
            self.assertIsInstance(attrs['label'], str)
        self.assertGreater(len(attrs['label']), 0)

    def test_positive_create_5(self):
        """@Test: Create an org and provide a name, label and description.

        @Assert: The organization has the provided name, label and description.

        @Feature: Organization

        """
        name = entities.Organization.name.gen_value()
        label = entities.Organization.label.gen_value()
        description = entities.Organization.description.gen_value()
        attrs = entities.Organization(
            name=name,
            label=label,
            description=description,
        ).create_json()
        self.assertEqual(attrs['name'], name)
        self.assertEqual(attrs['label'], label)
        self.assertEqual(attrs['description'], description)

    @ddt.data(
        gen_string('utf8', length=256),  # longer than 255
        '',
        ' ',
    )
    def test_negative_create_name(self, name):
        """@Test: Create an org with an incorrect name.

        @Assert: The organization cannot be created.

        @Feature: Organization

        """
        with self.assertRaises(HTTPError):
            entities.Organization(name=name).create_json()

    def test_negative_create_duplicate(self):
        """@Test: Create two organizations with identical names.

        @Assert: The second organization cannot be created.

        @Feature: Organization

        """
        name = entities.Organization.name.gen_value()
        entities.Organization(name=name).create_json()
        with self.assertRaises(HTTPError):
            entities.Organization(name=name).create_json()

    def test_positive_search(self):
        """@Test: Create an organization, then search for it by name.

        @Assert: Searching returns at least one result.

        @Feature: Organization

        """
        name = entities.Organization().create_json()['name']
        response = client.get(
            entities.Organization().path(),
            auth=get_server_credentials(),
            data={u'name': name},
            verify=False,
        )
        response.raise_for_status()
        results = response.json()['results']
        self.assertGreaterEqual(len(results), 1)


@ddt.ddt
class OrganizationUpdateTestCase(APITestCase):
    """Tests for the ``organizations`` path."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create an organization."""
        cls.organization = entities.Organization(
            id=entities.Organization().create_json()['id']
        ).read()

    @ddt.data(
        {'description': gen_string(str_type='alpha')},
        {'description': gen_string(str_type='alphanumeric')},
        {'description': gen_string(str_type='cjk')},
        {'description': gen_string(str_type='latin1')},
        {'description': gen_string(str_type='numeric')},
        {'description': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='alpha')},
        {'name': gen_string(str_type='alphanumeric')},
        {'name': gen_string(str_type='cjk')},
        {'name': gen_string(str_type='latin1')},
        {'name': gen_string(str_type='numeric')},
        {'name': gen_string(str_type='utf8')},
        {  # can we update two attrs at once?
            'description': entities.Organization.description.gen_value(),
            'name': entities.Organization.name.gen_value(),
        },
    )
    def test_positive_update(self, attrs):
        """@Test: Update an organization's attributes with valid values.

        @Assert: The organization's attributes are updated.

        @Feature: Organization

        """
        client.put(
            self.organization.path(),
            attrs,
            verify=False,
            auth=get_server_credentials(),
        ).raise_for_status()

        # Read the organization and validate its attributes.
        new_attrs = self.organization.read_json()
        for name, value in attrs.items():
            self.assertIn(name, new_attrs.keys())
            self.assertEqual(new_attrs[name], value)

    def test_associate_user_with_organization(self):
        """@Test: Update an organization, associate user with it.

        @Assert: User is associated with organization.

        @Feature: Organization

        """
        user_id = entities.User().create_json()['id']
        client.put(
            self.organization.path(),
            {'organization': {'user_ids': [user_id]}},
            verify=False,
            auth=get_server_credentials(),
        ).raise_for_status()
        new_attrs = self.organization.read_json()
        self.assertEqual(1, len(new_attrs['users']))
        self.assertEqual(user_id, new_attrs['users'][0]['id'])

    def test_associate_subnet_with_organization(self):
        """@Test: Update an organization, associate subnet with it.

        @Assert: Subnet is associated with organization.

        @Feature: Organization

        """
        subnet_id = entities.Subnet().create_json()['id']
        client.put(
            self.organization.path(),
            {'organization': {'subnet_ids': [subnet_id]}},
            verify=False,
            auth=get_server_credentials(),
        ).raise_for_status()
        new_attrs = self.organization.read_json()
        self.assertEqual(1, len(new_attrs['subnets']))
        self.assertEqual(subnet_id, new_attrs['subnets'][0]['id'])

    @ddt.data(
        {'name': gen_string(str_type='utf8', length=256)},
        {'label': gen_string(str_type='utf8')},  # Immutable. See BZ 1089996.
    )
    def test_negative_update(self, attrs):
        """@Test: Update an organization's attributes with invalid values.

        @Assert: The organization's attributes are not updated.

        @Feature: Organization

        """
        response = client.put(
            self.organization.path(),
            attrs,
            verify=False,
            auth=get_server_credentials(),
        )
        with self.assertRaises(HTTPError):
            response.raise_for_status()
