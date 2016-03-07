"""Unit tests for the ``gpgkeys`` paths."""
from fauxfactory import gen_string
from nailgun import entities
from requests import HTTPError
from robottelo.constants import VALID_GPG_KEY_BETA_FILE, VALID_GPG_KEY_FILE
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import run_only_on, tier1
from robottelo.helpers import read_data_file
from robottelo.test import APITestCase


class GPGKeyTestCase(APITestCase):
    """Tests for ``katello/api/v2/gpg_keys``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(GPGKeyTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.key_content = read_data_file(VALID_GPG_KEY_FILE)

    @tier1
    @run_only_on('sat')
    def test_positive_search_in_org(self):
        """Search for a GPG key and specify just ``organization_id``.

        @Feature: GPGKey

        @Steps:

        1. Create an organization.
        1. Create a GPG key belonging to the organization.
        2. Search for GPG keys in the organization.

        @Assert: Only one GPG key is in the search results: the created GPG
        key.
        """
        org = entities.Organization().create()
        gpg_key = entities.GPGKey(organization=org).create()
        gpg_keys = gpg_key.search({'organization'})
        self.assertEqual(len(gpg_keys), 1)
        self.assertEqual(gpg_key.id, gpg_keys[0].id)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create a GPG key with valid name.

        @Assert: A GPG key is created with the given name.

        @Feature: GPGKey
        """
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = entities.GPGKey(
                    organization=self.org, name=name).create()
                self.assertEqual(name, gpg_key.name)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_content(self):
        """Create a GPG key with valid name and valid gpg key text.

        @Assert: A GPG key is created with the expected content.

        @Feature: GPGKey
        """
        gpg_key = entities.GPGKey(
            organization=self.org, content=self.key_content).create()
        self.assertEqual(self.key_content, gpg_key.content)

    @tier1
    @run_only_on('sat')
    def test_negative_create_name(self):
        """Attempt to create GPG key with invalid names only.

        @Assert: A GPG key is not created and error is raised.

        @Feature: GPGKey
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.GPGKey(name=name).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_same_name(self):
        """Attempt to create a GPG key providing a name of already existent
        entity

        @Assert: A GPG key is not created and error is raised.

        @Feature: GPGKey
        """
        name = gen_string('alphanumeric')
        entities.GPGKey(organization=self.org, name=name).create()
        with self.assertRaises(HTTPError):
            entities.GPGKey(organization=self.org, name=name).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_content(self):
        """Attempt to create GPG key with empty content.

        @Assert: A GPG key is not created and error is raised.

        @Feature: GPGKey
        """
        with self.assertRaises(HTTPError):
            entities.GPGKey(content='').create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update GPG key name to another valid name.

        @Assert: The GPG key name can be updated.

        @Feature: GPGKey
        """
        gpg_key = entities.GPGKey(organization=self.org).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                gpg_key.name = new_name
                gpg_key = gpg_key.update(['name'])
                self.assertEqual(new_name, gpg_key.name)

    @tier1
    @run_only_on('sat')
    def test_positive_update_content(self):
        """Update GPG key content text to another valid one.

        @Assert: The GPG key content text can be updated.

        @Feature: GPGKey
        """
        gpg_key = entities.GPGKey(
            organization=self.org,
            content=read_data_file(VALID_GPG_KEY_BETA_FILE),
        ).create()
        gpg_key.content = self.key_content
        gpg_key = gpg_key.update(['content'])
        self.assertEqual(self.key_content, gpg_key.content)

    @tier1
    @run_only_on('sat')
    def test_negative_update_name(self):
        """Attempt to update GPG key name to invalid one

        @Assert: GPG key is not updated

        @Feature: GPGKey
        """
        gpg_key = entities.GPGKey(organization=self.org).create()
        for new_name in invalid_values_list():
            gpg_key.name = new_name
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    gpg_key.update(['name'])

    @tier1
    @run_only_on('sat')
    def test_negative_update_same_name(self):
        """Attempt to update GPG key name to the name of existing GPG key
        entity

        @Assert: GPG key is not updated

        @Feature: GPGKey
        """
        name = gen_string('alpha')
        entities.GPGKey(organization=self.org, name=name).create()
        new_gpg_key = entities.GPGKey(organization=self.org).create()
        new_gpg_key.name = name
        with self.assertRaises(HTTPError):
            new_gpg_key.update(['name'])

    @tier1
    @run_only_on('sat')
    def test_negative_update_content(self):
        """Attempt to update GPG key content to invalid one

        @Assert: GPG key is not updated

        @Feature: GPGKey
        """
        gpg_key = entities.GPGKey(
            organization=self.org, content=self.key_content).create()
        gpg_key.content = ''
        with self.assertRaises(HTTPError):
            gpg_key.update(['content'])
        self.assertEqual(self.key_content, gpg_key.read().content)

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create a GPG key with different names and then delete it.

        @Assert: The GPG key deleted successfully.

        @Feature: GPGKey
        """
        gpg_key = entities.GPGKey(organization=self.org).create()
        gpg_key.delete()
        with self.assertRaises(HTTPError):
            gpg_key.read()
