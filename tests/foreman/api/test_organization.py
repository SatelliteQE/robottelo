"""Unit tests for the ``organizations`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here:
http://theforeman.org/api/apidoc/v2/organizations.html

"""
import httplib

from fauxfactory import gen_alphanumeric, gen_string
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.decorators import skip_if_bug_open
from robottelo.helpers import (
    get_nailgun_config,
    get_server_credentials,
    invalid_values_list,
    valid_data_list,
)
from robottelo.test import APITestCase


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
        org = entities.Organization().create()
        self.assertTrue(hasattr(org, 'label'))
        self.assertIsInstance(org.label, type(u''))

    def test_positive_create_2(self):
        """@Test: Create an org and provide a name and identical label.

        @Assert: The organization has the provided attributes.

        @Feature: Organzation

        """
        # A label has a more restrictive allowable charset than a name, so we
        # use it for populating both name and label.
        org = entities.Organization()
        name_label = org.get_fields()['label'].gen_value()
        org.name = org.label = name_label
        org = org.create()
        self.assertEqual(name_label, org.name)
        self.assertEqual(name_label, org.label)

    def test_positive_create_3(self):
        """@Test: Create an organization and provide a name and label.

        @Assert: The organization has the provided attributes.

        @Feature: Organization

        """
        org = entities.Organization()
        org.name = name = org.get_fields()['name'].gen_value()
        org.label = label = org.get_fields()['label'].gen_value()
        org = org.create()
        self.assertEqual(name, org.name)
        self.assertEqual(label, org.label)

    def test_positive_create_4(self):
        """@Test: Create an organization and provide a name and description.

        @Assert: The organization has the provided attributes and an
        auto-generated label.

        @Feature: Organization

        """
        for name in valid_data_list():
            with self.subTest(name):
                org = entities.Organization(
                    name=name,
                    description=name,
                ).create()
                self.assertEqual(org.name, name)
                self.assertEqual(org.description, name)

                # Was a label auto-generated?
                self.assertTrue(hasattr(org, 'label'))
                self.assertIsInstance(org.label, type(u''))
                self.assertGreater(len(org.label), 0)

    def test_positive_create_5(self):
        """@Test: Create an org and provide a name, label and description.

        @Assert: The organization has the provided name, label and description.

        @Feature: Organization

        """
        org = entities.Organization()
        org.name = name = org.get_fields()['name'].gen_value()
        org.label = label = org.get_fields()['label'].gen_value()
        org.description = desc = org.get_fields()['description'].gen_value()
        org = org.create()
        self.assertEqual(org.name, name)
        self.assertEqual(org.label, label)
        self.assertEqual(org.description, desc)

    def test_negative_create_name(self):
        """@Test: Create an org with an incorrect name.

        @Assert: The organization cannot be created.

        @Feature: Organization

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Organization(name=name).create()

    def test_negative_create_duplicate(self):
        """@Test: Create two organizations with identical names.

        @Assert: The second organization cannot be created.

        @Feature: Organization

        """
        name = entities.Organization().create().name
        with self.assertRaises(HTTPError):
            entities.Organization(name=name).create()

    def test_positive_search(self):
        """@Test: Create an organization, then search for it by name.

        @Assert: Searching returns at least one result.

        @Feature: Organization

        """
        org = entities.Organization().create()
        orgs = entities.Organization().search(
            query={u'search': u'name="{0}"'.format(org.name)}
        )
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0].id, org.id)
        self.assertEqual(orgs[0].name, org.name)


class OrganizationUpdateTestCase(APITestCase):
    """Tests for the ``organizations`` path."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create an organization."""
        cls.organization = entities.Organization().create()

    def test_update_name(self):
        """@Test: Update an organization's name with valid values.

        @Assert: The organization's name is updated.

        @Feature: Organization

        """
        for name in valid_data_list():
            with self.subTest(name):
                setattr(self.organization, 'name', name)
                self.organization = self.organization.update(['name'])
                self.assertEqual(self.organization.name, name)

    def test_update_desc(self):
        """@Test: Update an organization's description with valid values.

        @Assert: The organization's description is updated.

        @Feature: Organization

        """
        for desc in valid_data_list():
            with self.subTest(desc):
                setattr(self.organization, 'description', desc)
                self.organization = self.organization.update(['description'])
                self.assertEqual(self.organization.description, desc)

    def test_update_name_desc(self):
        """@Test: Update an organization with new name and description.

        @Assert: The organization's name and description are updated.

        @Feature: Organization

        """
        name = gen_string('alpha')
        desc = gen_string('alpha')
        self.organization.name = name
        self.organization.description = desc
        self.organization = self.organization.update(['name', 'description'])
        self.assertEqual(self.organization.name, name)
        self.assertEqual(self.organization.description, desc)

    def test_associate_with_user(self):
        """@Test: Update an organization, associate user with it.

        @Assert: User is associated with organization.

        @Feature: Organization

        """
        user = entities.User().create()
        self.organization.user = [user]
        self.organization = self.organization.update(['user'])
        self.assertEqual(len(self.organization.user), 1)
        self.assertEqual(self.organization.user[0].id, user.id)

    def test_associate_with_subnet(self):
        """@Test: Update an organization, associate subnet with it.

        @Assert: Subnet is associated with organization.

        @Feature: Organization

        """
        subnet = entities.Subnet().create()
        self.organization.subnet = [subnet]
        self.organization = self.organization.update(['subnet'])
        self.assertEqual(len(self.organization.subnet), 1)
        self.assertEqual(self.organization.subnet[0].id, subnet.id)

    @skip_if_bug_open('bugzilla', 1230865)
    def test_associate_with_media(self):
        """@Test: Update an organization and associate it with a media.

        @Assert: An organization is associated with a media.

        @Feature: Organziation

        """
        media = entities.Media().create()
        self.organization.media = [media]
        self.organization = self.organization.update(['media'])
        self.assertEqual(len(self.organization.media), 1)
        self.assertEqual(self.organization.media[0].id, media.id)

    def test_negative_update(self):
        """@Test: Update an organization's attributes with invalid values.

        @Assert: The organization's attributes are not updated.

        @Feature: Organization

        """
        dataset = (
            {'name': gen_string(str_type='utf8', length=256)},
            # Immutable. See BZ 1089996.
            {'label': gen_string(str_type='utf8')},
        )
        for attrs in dataset:
            with self.subTest(attrs):
                with self.assertRaises(HTTPError):
                    entities.Organization(
                        id=self.organization.id,
                        **attrs
                    ).update(attrs.keys())

    @skip_if_bug_open('bugzilla', 1103157)
    def test_bugzilla_1103157(self):
        """@Test: Create organization and add two compute resources one by one
        using different transactions and different users to see that they
        actually added, but not overwrite each other

        @Feature: Organization - Update

        @Steps:

        1. Use the admin user to create an organization and two compute
           resources. Make one compute resource point at / belong to the
           organization.
        2. Create a user and give them the ability to update compute resources
           and organizations. Have this user make the second compute resource
           point at / belong to the organization.
        3. Use the admin user to read information about the organization.
           Verify that both compute resources are pointing at / belong to the
           organization.

        @Assert: Organization contains both compute resources

        """
        # setUpClass() creates an organization w/admin user. Here, we use admin
        # to make two compute resources and make first belong to organization.
        compute_resources = [
            entities.LibvirtComputeResource(
                name=gen_string('alpha'),
                url='qemu://host.example.com/system'
            ).create()
            for _ in range(2)
        ]
        self.organization.compute_resource = compute_resources[:1]  # list
        self.organization = self.organization.update(['compute_resource'])
        self.assertEqual(len(self.organization.compute_resource), 1)

        # Create a new user and give them minimal permissions.
        login = gen_alphanumeric()
        password = gen_alphanumeric()
        user = entities.User(login=login, password=password).create()
        role = entities.Role().create()
        for perm in ['edit_compute_resources', 'edit_organizations']:
            permissions = [
                entities.Permission(id=permission['id'])
                for permission
                in entities.Permission(name=perm).search()
            ]
            entities.Filter(permission=permissions, role=role).create()
        user.role = [role]
        user = user.update(['role'])

        # Make new user assign second compute resource to org.
        cfg = get_nailgun_config()
        cfg.auth = (login, password)
        entities.Organization(
            cfg,
            id=self.organization.id,
            compute_resource=compute_resources[1:],  # slice returns list
        ).update(['compute_resource'])

        # Use admin to verify both compute resources belong to organization.
        self.assertEqual(len(self.organization.read().compute_resource), 2)
