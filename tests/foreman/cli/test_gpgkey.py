# -*- encoding: utf-8 -*-
"""Test class for GPG Key CLI

:Requirement: Gpgkey

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: GPGKeys

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from tempfile import mkstemp

from fauxfactory import gen_alphanumeric
from fauxfactory import gen_choice
from fauxfactory import gen_integer
from fauxfactory import gen_string

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_gpg_key
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.gpgkey import GPGKey
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import VALID_GPG_KEY_FILE
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.helpers import get_data_file
from robottelo.test import CLITestCase

VALID_GPG_KEY_FILE_PATH = get_data_file(VALID_GPG_KEY_FILE)


def create_gpg_key_file(content=None):
    """Creates a fake GPG Key file and returns its path or None if an error
    happens.
    """

    (_, key_filename) = mkstemp(text=True)
    if not content:
        content = gen_alphanumeric(gen_integer(20, 50))
    with open(key_filename, "w") as gpg_key_file:
        gpg_key_file.write(content)
        return key_filename

    return None


class TestGPGKey(CLITestCase):
    """Tests for GPG Keys via Hammer CLI"""

    search_key = 'name'

    @classmethod
    def setUpClass(cls):
        """Create a shared organization for all tests to avoid generating
        hundreds of organizations
        """
        super(TestGPGKey, cls).setUpClass()
        cls.org = make_org(cached=True)

    # Bug verification

    @tier1
    def test_verify_redmine_4272(self):
        """gpg info should display key content

        :id: 2c6176ca-34dd-4d52-930d-6e79da6b0c15

        :expectedresults: gpg info should display key content

        :CaseImportance: Critical
        """
        # Setup a new key file
        content = gen_alphanumeric()
        gpg_key = create_gpg_key_file(content=content)
        self.assertIsNotNone(gpg_key, 'GPG Key file must be created')
        gpg_key = make_gpg_key(
            {'key': gpg_key, 'name': gen_string('alpha'), 'organization-id': self.org['id']}
        )
        self.assertEqual(gpg_key['content'], content)

    @tier1
    def test_positive_get_info_by_name(self):
        """Create single gpg key and get its info by name

        :id: be418cf8-8a90-46db-9e8c-8ff349c98401

        :expectedresults: specific information for GPG key matches the creation
            name

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        gpg_key = make_gpg_key(
            {'key': VALID_GPG_KEY_FILE_PATH, 'name': name, 'organization-id': self.org['id']}
        )
        gpg_key = GPGKey.info({'name': gpg_key['name'], 'organization-id': self.org['id']})
        self.assertEqual(gpg_key['name'], name)

    # Positive Create

    @tier1
    def test_positive_create_with_default_org(self):
        """Create gpg key with valid name and valid gpg key via file
        import using the default created organization

        :id: c64d4959-e53e-44c0-82da-dc4dd4c89733

        :expectedresults: gpg key is created

        :CaseImportance: Critical
        """
        org = Org.info({'name': DEFAULT_ORG})
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = make_gpg_key(
                    {'key': VALID_GPG_KEY_FILE_PATH, 'name': name, 'organization-id': org['id']}
                )
                # Can we find the new object?
                result = GPGKey.exists(
                    {'organization-id': org['id']}, (self.search_key, gpg_key[self.search_key])
                )
                self.assertEqual(gpg_key[self.search_key], result[self.search_key])

    @tier1
    def test_positive_create_with_custom_org(self):
        """Create gpg key with valid name and valid gpg key via file
        import using a new organization

        :id: f1bcf748-0890-4b54-8f30-2df4924c80b3

        :expectedresults: gpg key is created

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = make_gpg_key(
                    {
                        'key': VALID_GPG_KEY_FILE_PATH,
                        'name': name,
                        'organization-id': self.org['id'],
                    }
                )
                # Can we find the new object?
                result = GPGKey.exists(
                    {'organization-id': self.org['id']},
                    (self.search_key, gpg_key[self.search_key]),
                )
                self.assertEqual(gpg_key[self.search_key], result[self.search_key])

    # Negative Create

    @tier1
    def test_negative_create_with_same_name(self):
        """Create gpg key with valid name and valid gpg key via file
        import then try to create new one with same name

        :id: 3f1423da-bcc1-4320-8b9b-260784eb123c

        :expectedresults: gpg key is not created

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        gpg_key = make_gpg_key({'name': name, 'organization-id': self.org['id']})
        # Can we find the new object?
        result = GPGKey.exists(
            {'organization-id': self.org['id']}, (self.search_key, gpg_key[self.search_key])
        )
        self.assertEqual(gpg_key[self.search_key], result[self.search_key])
        # Try to create a gpg key with the same name
        with self.assertRaises(CLIFactoryError):
            make_gpg_key({'name': name, 'organization-id': self.org['id']})

    @tier1
    def test_negative_create_with_no_gpg_key(self):
        """Create gpg key with valid name and no gpg key

        :id: 9440a1a0-eb0d-445e-88d3-3139c2b1d17a

        :expectedresults: gpg key is not created

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    GPGKey.create({'name': name, 'organization-id': self.org['id']})

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create gpg key with invalid name and valid gpg key via
        file import

        :id: 93160f88-b653-42a9-b44f-9b2ba56f38d9

        :expectedresults: gpg key is not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    # factory will provide a valid key
                    make_gpg_key({'name': name, 'organization-id': self.org['id']})

    # Positive Delete
    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create gpg key with valid name and valid gpg key via file
        import then delete it

        :id: 5bf72e5c-767a-4321-8781-a5cea9474421

        :expectedresults: gpg key is deleted

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = make_gpg_key({'name': name, 'organization-id': self.org['id']})
                result = GPGKey.exists(
                    {'organization-id': self.org['id']},
                    (self.search_key, gpg_key[self.search_key]),
                )
                self.assertEqual(gpg_key[self.search_key], result[self.search_key])
                GPGKey.delete({'name': name, 'organization-id': self.org['id']})
                result = GPGKey.exists(
                    {'organization-id': self.org['id']},
                    (self.search_key, gpg_key[self.search_key]),
                )
                self.assertEqual(len(result), 0)

    # Positive Update

    @tier1
    def test_positive_update_name(self):
        """Create gpg key with valid name and valid gpg key via file
        import then update its name

        :id: e18d7cd8-2757-4134-9ed9-7eb68f2872e2

        :expectedresults: gpg key is updated

        :CaseImportance: Critical
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        for new_name in valid_data_list():
            with self.subTest(new_name):
                GPGKey.update(
                    {
                        'name': gpg_key['name'],
                        'new-name': new_name,
                        'organization-id': self.org['id'],
                    }
                )
                gpg_key = GPGKey.info({'name': new_name, 'organization-id': self.org['id']})

    @tier1
    def test_positive_update_key(self):
        """Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file

        :id: 58a8ed14-adfc-4046-af63-59a7008ff4d7

        :expectedresults: gpg key is updated

        :CaseImportance: Critical
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        content = gen_alphanumeric(gen_integer(20, 50))
        self.assertNotEqual(gpg_key['content'], content)
        local_key = create_gpg_key_file(content)
        self.assertIsNotNone(local_key, 'GPG Key file must be created')
        key = '/tmp/%s' % gen_alphanumeric()
        ssh.upload_file(local_file=local_key, remote_file=key)
        GPGKey.update({'key': key, 'name': gpg_key['name'], 'organization-id': self.org['id']})
        gpg_key = GPGKey.info({'name': gpg_key['name'], 'organization-id': self.org['id']})
        self.assertEqual(gpg_key['content'], content)

    # Negative Update
    @tier1
    def test_negative_update_name(self):
        """Create gpg key with valid name and valid gpg key via file
        import then fail to update its name

        :id: 938d2925-c82c-43b6-8dfc-29c42eca7424

        :expectedresults: gpg key is not updated

        :CaseImportance: Critical
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    GPGKey.update(
                        {
                            'name': gpg_key['name'],
                            'new-name': new_name,
                            'organization-id': self.org['id'],
                        }
                    )

    # Product association
    @tier2
    def test_positive_add_empty_product(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product

        :id: b7477c2f-586c-4593-96c0-1fbc532ce8bf

        :expectedresults: gpg key is associated with product

        :CaseLevel: Integration
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        product = make_product({'gpg-key-id': gpg_key['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])

    @tier2
    def test_positive_add_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository

        :id: 5529a852-9ef6-48f8-b2bc-2bbf463657dd

        :expectedresults: gpg key is associated with product as well as with
            the repository

        :CaseLevel: Integration
        """
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        Product.update(
            {'gpg-key': gpg_key['name'], 'id': product['id'], 'organization-id': self.org['id']}
        )
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(product['gpg']['gpg-key-id'], gpg_key['id'])
        self.assertEqual(repo['gpg-key']['id'], gpg_key['id'])

    @tier2
    def test_positive_add_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository

        :id: b05c5223-44d5-4a48-9d99-18ca351c84a5

        :expectedresults: gpg key is associated with product as well as with
            the repositories

        :CaseLevel: Integration
        """
        product = make_product({'organization-id': self.org['id']})
        repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        Product.update(
            {'gpg-key': gpg_key['name'], 'id': product['id'], 'organization-id': self.org['id']}
        )
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['gpg']['gpg-key-id'], gpg_key['id'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(repo['gpg-key']['id'], gpg_key['id'])

    @stubbed()
    @tier2
    def test_positive_add_product_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method

        :id: fb12db0f-583f-49f4-9d8f-d19f2d5550ee

        :expectedresults: gpg key is associated with product but not the
            repositories

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @tier2
    def test_positive_add_repo_from_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository

        :id: 1427f145-9faf-41ef-ae42-dc91d61ce1f6

        :expectedresults: gpg key is associated with the repository but not
            with the product

        :CaseLevel: Integration
        """
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        Repository.update(
            {'gpg-key-id': gpg_key['id'], 'id': repo['id'], 'organization-id': self.org['id']}
        )
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['gpg-key']['id'], gpg_key['id'])
        self.assertNotEqual(product['gpg'].get('gpg-key-id'), gpg_key['id'])

    @tier2
    def test_positive_add_repo_from_product_with_repos(self):
        """Create gpg key via file import and associate with custom repo

        GPGKey should contain valid name and valid key and should be associated
        to one repository from custom product. Make sure custom product should
        have more than one repository.

        :id: 9796f6f0-e688-4f14-89ec-447feb4e4911

        :expectedresults: gpg key is associated with the repository

        :CaseLevel: Integration
        """
        product = make_product({'organization-id': self.org['id']})
        repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        Repository.update(
            {'gpg-key': gpg_key['name'], 'id': repos[0]['id'], 'organization-id': self.org['id']}
        )
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertNotEqual(product['gpg'].get('gpg-key-id'), gpg_key['id'])
        # First repo should have a valid gpg key assigned
        repo = Repository.info({'id': repos.pop(0)['id']})
        self.assertEqual(repo['gpg-key']['id'], gpg_key['id'])
        # The rest of repos should not
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(repo['gpg-key'].get('id'), gpg_key['id'])

    @stubbed()
    @tier2
    def test_positive_add_repos_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method

        :id: 1e91871c-0298-4cd0-b63b-f02d02622259

        :expectedresults: gpg key is associated with product and all the
            repositories

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @tier2
    def test_positive_update_key_for_empty_product(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product then
        update the key

        :id: c0c84c45-21fc-4940-9d52-00babb807ec7

        :expectedresults: gpg key is associated with product before/after
            update

        :CaseLevel: Integration
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a product
        Product.update(
            {'gpg-key': gpg_key['name'], 'id': product['id'], 'organization-id': self.org['id']}
        )
        # Verify gpg key was associated
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update(
            {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': self.org['id']}
        )
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the product
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['gpg']['gpg-key'], new_name)

    @tier2
    def test_positive_update_key_for_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then update the key

        :id: 3fb550a7-507e-4988-beb6-35bdfc2e99a8

        :expectedresults: gpg key is associated with product before/after
            update as well as with the repository

        :CaseLevel: Integration
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Create a repository and assign it to the product
        repo = make_repository({'product-id': product['id']})
        # Associate gpg key with a product
        Product.update(
            {'gpg-key': gpg_key['name'], 'id': product['id'], 'organization-id': self.org['id']}
        )
        # Verify gpg key was associated
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update(
            {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': self.org['id']}
        )
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the product
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['gpg']['gpg-key'], new_name)
        # Verify changes are reflected in the repository
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['gpg-key'].get('id'), gpg_key['id'])

    @tier2
    def test_positive_update_key_for_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then update the key

        :id: a95eb51b-4b6b-4c04-bb4d-cbe600431850

        :expectedresults: gpg key is associated with product before/after
            update as well as with the repositories

        :CaseLevel: Integration
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Create repositories and assign them to the product
        repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
        # Associate gpg key with a product
        Product.update(
            {'gpg-key': gpg_key['name'], 'id': product['id'], 'organization-id': self.org['id']}
        )
        # Verify gpg key was associated
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update(
            {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': self.org['id']}
        )
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the product
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['gpg']['gpg-key'], new_name)
        # Verify changes are reflected in the repositories
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(repo['gpg-key'].get('name'), new_name)

    @stubbed()
    @tier2
    def test_positive_update_key_for_product_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then update the key

        :id: 8092bd11-75f3-4657-9309-d327498e7d52

        :expectedresults: gpg key is associated with product before/after
            update but not the repositories

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @tier2
    def test_positive_update_key_for_repo_from_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then update the key

        :id: 549e2e1e-fd10-4487-a3a5-fdee9b8cfc48

        :expectedresults: gpg key is associated with the repository
            before/after update, but not with the product

        :CaseLevel: Integration
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Create repository, assign product and gpg-key
        repo = make_repository({'gpg-key-id': gpg_key['id'], 'product-id': product['id']})
        # Verify gpg key was associated
        self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update(
            {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': self.org['id']}
        )
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the repositories
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['gpg-key'].get('name'), new_name)
        # Verify gpg key wasn't added to the product
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], new_name)

    @tier2
    def test_positive_update_key_for_repo_from_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then update the key

        :id: 773a9141-9f04-40ba-b3df-4b6d80db25a6

        :expectedresults: gpg key is associated with a single repository
            before/after update and not associated with product or other
            repositories

        :CaseLevel: Integration
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Create repositories and assign them to the product
        repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
        # Associate gpg key with a single repository
        Repository.update(
            {'gpg-key': gpg_key['name'], 'id': repos[0]['id'], 'organization-id': self.org['id']}
        )
        # Verify gpg key was associated
        repos[0] = Repository.info({'id': repos[0]['id']})
        self.assertEqual(repos[0]['gpg-key']['name'], gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update(
            {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': self.org['id']}
        )
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the associated repository
        repos[0] = Repository.info({'id': repos[0]['id']})
        self.assertEqual(repos[0]['gpg-key'].get('name'), new_name)
        # Verify changes are not reflected in the product
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], new_name)
        # Verify changes are not reflected in the rest of repositories
        for repo in repos[1:]:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(repo['gpg-key'].get('name'), new_name)

    @stubbed()
    @tier2
    def test_positive_update_key_for_repos_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method then update the key

        :id: 21dfd9b0-3de9-4876-aeea-c856adb5ed98

        :expectedresults: gpg key is associated with product and all
            repositories before/after update

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @tier2
    def test_positive_delete_key_for_empty_product(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product
        then delete it

        :id: da76cada-5ccf-47e1-8c12-24f30c41c8b6

        :expectedresults: gpg key is associated with product during creation
            but removed from product after deletion

        :CaseLevel: Integration
        """
        # Create a product and a gpg key
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        product = make_product({'gpg-key-id': gpg_key['id'], 'organization-id': self.org['id']})
        # Verify gpg key was associated
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({'name': gpg_key['name'], 'organization-id': self.org['id']})
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        # Verify gpg key was disassociated from the product
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])

    @tier2
    @upgrade
    def test_positive_delete_key_for_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then delete it

        :id: a5d4ea02-f015-4026-b4dc-7365eaf00049

        :expectedresults: gpg key is associated with product but and its
            repository during creation but removed from product and repository
            after deletion

        :CaseLevel: Integration
        """
        # Create product, repository and gpg key
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a product
        Product.update(
            {'gpg-key': gpg_key['name'], 'id': product['id'], 'organization-id': self.org['id']}
        )
        # Verify gpg key was associated both with product and its repository
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({'name': gpg_key['name'], 'organization-id': self.org['id']})
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        # Verify gpg key was disassociated from the product and its repository
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])
        self.assertNotEqual(repo['gpg-key'].get('name'), gpg_key['name'])

    @tier2
    def test_positive_delete_key_for_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then delete it

        :id: f92d4643-1892-4f95-ae6b-fcea8e726946

        :expectedresults: gpg key is associated with product and its
            repositories during creation but removed from the product and the
            repositories after deletion

        :CaseLevel: Integration
        """
        # Create product, repositories and gpg key
        product = make_product({'organization-id': self.org['id']})
        repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a product
        Product.update(
            {'gpg-key': gpg_key['name'], 'id': product['id'], 'organization-id': self.org['id']}
        )
        # Verify gpg key was associated with product and its repositories
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({'name': gpg_key['name'], 'organization-id': self.org['id']})
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        # Verify gpg key was disassociated from the product and its
        # repositories
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(repo['gpg-key'].get('name'), gpg_key['name'])

    @stubbed()
    @tier2
    def test_positive_delete_key_for_product_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then delete it

        :id: f8492db8-12f3-4d32-833a-f177734e2253

        :expectedresults: gpg key is associated with product but not the
            repositories during creation but removed from product after
            deletion

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @tier2
    def test_positive_delete_key_for_repo_from_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then delete the key

        :id: 3658e04d-fc63-499f-a22d-b512941cc96b

        :expectedresults: gpg key is associated with the single repository but
            not the product during creation and was removed from repository
            after deletion

        :CaseLevel: Integration
        """
        # Create product, repository and gpg key
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a repository
        Repository.update(
            {'gpg-key': gpg_key['name'], 'id': repo['id'], 'organization-id': self.org['id']}
        )
        # Verify gpg key was associated with the repository but not with the
        # product
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])
        self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({'name': gpg_key['name'], 'organization-id': self.org['id']})
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        # Verify gpg key was disassociated from the repository
        repo = Repository.info({'id': repo['id']})
        self.assertNotEqual(repo['gpg-key'].get('name'), gpg_key['name'])

    @tier2
    def test_positive_delete_key_for_repo_from_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then delete the key

        :id: e7ed4ed9-ecfe-4954-b806-cdd0668e8822

        :expectedresults: gpg key is associated with a single repository but
            not the product during creation and removed from repository after
            deletion

        :CaseLevel: Integration
        """
        # Create product, repositories and gpg key
        product = make_product({'organization-id': self.org['id']})
        repos = []
        for _ in range(gen_integer(2, 5)):
            repos.append(make_repository({'product-id': product['id']}))
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a repository
        Repository.update(
            {'gpg-key': gpg_key['name'], 'id': repos[0]['id'], 'organization-id': self.org['id']}
        )
        # Verify gpg key was associated with the repository
        repos[0] = Repository.info({'id': repos[0]['id']})
        self.assertEqual(repos[0]['gpg-key']['name'], gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({'name': gpg_key['name'], 'organization-id': self.org['id']})
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({'id': gpg_key['id'], 'organization-id': self.org['id']})
        # Verify gpg key is not associated with any repository or the product
        # itself
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(repo['gpg-key'].get('name'), gpg_key['name'])

    @stubbed()
    @tier2
    def test_positive_delete_key_for_repos_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method then delete the key

        :id: 8ae226c6-f27c-4fb5-94f2-89792cccda0b

        :expectedresults: gpg key is associated with product and all
            repositories during creation but removed from product and all
            repositories after deletion

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    # Content

    @stubbed()
    @tier2
    def test_positive_consume_content_using_repo(self):
        """Hosts can install packages using gpg key associated with
        single custom repository

        :id: 39357649-4c60-4c82-9114-a43dfef81e5b

        :expectedresults: host can install package from custom repository

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_consume_content_using_repos(self):
        """Hosts can install packages using gpg key associated with
        multiple custom repositories

        :id: fedd6fa2-e28b-468b-8e15-802b52970bb9

        :expectedresults: host can install package from custom repositories

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_consume_content_using_repos_and_different_keys(self):
        """Hosts can install packages using different gpg keys
        associated with multiple custom repositories

        :id: ac908aee-0928-4f81-a98b-b60d46b10c90

        :expectedresults: host can install package from custom repositories

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    # Miscelaneous

    @tier1
    def test_positive_list(self):
        """Create gpg key and list it

        :id: 5da535b3-1728-4edf-bd33-3822c4427ef3

        :expectedresults: gpg key is displayed/listed

        :CaseImportance: Critical
        """
        gpg_key = make_gpg_key({'key': VALID_GPG_KEY_FILE_PATH, 'organization-id': self.org['id']})
        gpg_keys_list = GPGKey.list({'organization-id': self.org['id']})
        self.assertIn(gpg_key['id'], [gpg['id'] for gpg in gpg_keys_list])

    @tier1
    def test_positive_search(self):
        """Create gpg key and search/find it

        :id: 9ef15add-b067-4134-b930-aaeda18bddfa

        :expectedresults: gpg key can be found

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = make_gpg_key(
                    {
                        'key': VALID_GPG_KEY_FILE_PATH,
                        'name': name,
                        'organization-id': self.org['id'],
                    }
                )
                # Can we find the new object?
                result = GPGKey.exists(
                    {'organization-id': self.org['id']}, search=('name', gpg_key['name'])
                )
                self.assertEqual(gpg_key['name'], result['name'])
