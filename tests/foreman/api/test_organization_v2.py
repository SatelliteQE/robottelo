"""Unit tests for the ``organizations`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/organizations.html

"""
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo import entities, factory, orm
from unittest import TestCase
import ddt
import httplib
import sys
# (too many public methods) pylint: disable=R0904


@ddt.ddt
class OrganizationTestCase(TestCase):
    """Tests for the ``organizations`` path."""
    @skip_if_bug_open('bugzilla', 1116043)
    def test_create_text_plain(self):
        """@Test Create an organization using a 'text/plain' content-type.

        @Assert: HTTP 415 is returned.

        @Feature: Organization

        """
        path = entities.Organization().path()
        attrs = entities.Organization().build()
        response = client.post(
            path,
            attrs,
            auth=get_server_credentials(),
            headers={'content-type': 'text/plain'},
            verify=False,
        )
        status_code = httplib.UNSUPPORTED_MEDIA_TYPE
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )

    def test_positive_create_1(self):
        """@Test: Create an organization and provide a name.

        @Assert: The organization has the provided attributes and an
        auto-generated label.

        @Feature: Organization

        """
        attrs = entities.Organization().create()
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
        name_label = entities.Organization.label.get_value()
        attrs = entities.Organization(
            name=name_label,
            label=name_label,
        ).create()
        self.assertEqual(attrs['name'], name_label)
        self.assertEqual(attrs['label'], name_label)

    def test_positive_create_3(self):
        """@Test: Create an organization and provide a name and label.

        @Assert: The organization has the provided attributes.

        @Feature: Organization

        """
        name = entities.Organization.name.get_value()
        label = entities.Organization.label.get_value()
        attrs = entities.Organization(name=name, label=label).create()
        self.assertEqual(attrs['name'], name)
        self.assertEqual(attrs['label'], label)

    @ddt.data(
        # two-tuples of data
        (orm.StringField(str_type=('alpha',)).get_value(),
         orm.StringField(str_type=('alpha',)).get_value()),
        (orm.StringField(str_type=('alphanumeric',)).get_value(),
         orm.StringField(str_type=('alphanumeric',)).get_value()),
        (orm.StringField(str_type=('cjk',)).get_value(),
         orm.StringField(str_type=('cjk',)).get_value()),
        (orm.StringField(str_type=('latin1',)).get_value(),
         orm.StringField(str_type=('latin1',)).get_value()),
        (orm.StringField(str_type=('numeric',)).get_value(),
         orm.StringField(str_type=('numeric',)).get_value()),
        (orm.StringField(str_type=('utf8',)).get_value(),
         orm.StringField(str_type=('utf8',)).get_value()),
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
        ).create()
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
        name = entities.Organization.name.get_value()
        label = entities.Organization.label.get_value()
        description = entities.Organization.description.get_value()
        attrs = entities.Organization(
            name=name,
            label=label,
            description=description,
        ).create()
        self.assertEqual(attrs['name'], name)
        self.assertEqual(attrs['label'], label)
        self.assertEqual(attrs['description'], description)

    @ddt.data(
        orm.StringField(len=256).get_value(),  # longer than 255
        '',
        ' ',
    )
    def test_negative_create_name(self, name):
        """@Test: Create an org with an incorrect name.

        @Assert: The organization cannot be created.

        @Feature: Organization

        """
        with self.assertRaises(factory.FactoryError):
            entities.Organization(name=name).create()

    def test_negative_create_duplicate(self):
        """@Test: Create two organizations with identical names.

        @Assert: The second organization cannot be created.

        @Feature: Organization

        """
        name = entities.Organization.name.get_value()
        entities.Organization(name=name).create()
        with self.assertRaises(factory.FactoryError):
            entities.Organization(name=name).create()

    def test_positive_search(self):
        """@Test: Create an organization, then search for it by name.

        @Assert: Searching returns at least one result.

        @Feature: Organization

        """
        name = entities.Organization().create()['name']
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
class OrganizationUpdateTestCase(TestCase):
    """Tests for the ``organizations`` path."""
    @classmethod
    def setUpClass(cls):
        """Create an organization."""
        cls.organization = entities.Organization(
            id=entities.Organization().create()['id']
        ).read()

    @ddt.data(
        {'description': orm.StringField(str_type=('alpha',)).get_value()},
        {'description': orm.StringField(str_type=('alphanumeric',)).get_value()},  # flake8:noqa pylint:disable=C0301
        {'description': orm.StringField(str_type=('cjk',)).get_value()},
        {'description': orm.StringField(str_type=('latin1',)).get_value()},
        {'description': orm.StringField(str_type=('numeric',)).get_value()},
        {'description': orm.StringField(str_type=('utf8',)).get_value()},
        {'name': orm.StringField(str_type=('alpha',)).get_value()},
        {'name': orm.StringField(str_type=('alphanumeric',)).get_value()},
        {'name': orm.StringField(str_type=('cjk',)).get_value()},
        {'name': orm.StringField(str_type=('latin1',)).get_value()},
        {'name': orm.StringField(str_type=('numeric',)).get_value()},
        {'name': orm.StringField(str_type=('utf8',)).get_value()},
        {  # can we update two attrs at once?
            'description': entities.Organization.description.get_value(),
            'name': entities.Organization.name.get_value(),
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

    @ddt.data(
        {'name': orm.StringField(len=256).get_value()},
        {'label': orm.StringField().get_value()},  # Immutable. See BZ 1089996.
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
