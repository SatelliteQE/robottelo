"""Unit tests for the ``gpgkeys`` paths.

:Requirement: Gpgkey

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: GPGKeys

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
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

        :id: ff5e047c-404b-4379-8d28-3ad8cb39b6a9

        :Steps:

            1. Create an organization.
            2. Create a GPG key belonging to the organization.
            3. Search for GPG keys in the organization.

        :expectedresults: Only one GPG key is in the search results: the
            created GPG key.

        :CaseImportance: Critical
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

        :id: 741d969b-28ef-481f-bcf7-ed4cd920b030

        :expectedresults: A GPG key is created with the given name.

        :CaseImportance: Critical
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

        :id: cfa6690e-fed7-49cf-94f9-fd2deed941c0

        :expectedresults: A GPG key is created with the expected content.

        :CaseImportance: Critical
        """
        gpg_key = entities.GPGKey(
            organization=self.org, content=self.key_content).create()
        self.assertEqual(self.key_content, gpg_key.content)

    @tier1
    @run_only_on('sat')
    def test_negative_create_name(self):
        """Attempt to create GPG key with invalid names only.

        :id: 904a3ed0-7d50-495e-a700-b4f1ae913599

        :expectedresults: A GPG key is not created and error is raised.

        :CaseImportance: Critical
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

        :id: 78299f13-5977-4409-9bc7-844e54349926

        :expectedresults: A GPG key is not created and error is raised.

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        entities.GPGKey(organization=self.org, name=name).create()
        with self.assertRaises(HTTPError):
            entities.GPGKey(organization=self.org, name=name).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_content(self):
        """Attempt to create GPG key with empty content.

        :id: fc79c840-6bcb-4d97-9145-c0008d5b028d

        :expectedresults: A GPG key is not created and error is raised.

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.GPGKey(content='').create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update GPG key name to another valid name.

        :id: 9868025d-5346-42c9-b850-916ce37a9541

        :expectedresults: The GPG key name can be updated.

        :CaseImportance: Critical
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

        :id: 62fdaf55-c931-4be6-9857-68cc816046ad

        :expectedresults: The GPG key content text can be updated.

        :CaseImportance: Critical
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

        :id: 1a43f610-8969-4f08-967f-fb6af0fca31b

        :expectedresults: GPG key is not updated

        :CaseImportance: Critical
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

        :id: e294e3b2-1125-4ad9-969a-eb3f1966419e

        :expectedresults: GPG key is not updated

        :CaseImportance: Critical
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

        :id: fee30ef8-370a-4fdd-9e45-e7ab95dade8b

        :expectedresults: GPG key is not updated

        :CaseImportance: Critical
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

        :id: b06d211f-2827-40f7-b627-8b1fbaee2eb4

        :expectedresults: The GPG key deleted successfully.

        :CaseImportance: Critical
        """
        gpg_key = entities.GPGKey(organization=self.org).create()
        gpg_key.delete()
        with self.assertRaises(HTTPError):
            gpg_key.read()
