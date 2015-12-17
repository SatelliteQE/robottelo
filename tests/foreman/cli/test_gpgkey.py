# -*- encoding: utf-8 -*-
"""Test class for GPG Key CLI"""

from fauxfactory import (
    gen_alphanumeric,
    gen_choice,
    gen_integer,
    gen_string,
)
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_gpg_key,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.gpgkey import GPGKey
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.constants import VALID_GPG_KEY_FILE
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.helpers import get_data_file
from robottelo.test import CLITestCase
from tempfile import mkstemp

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
        # pylint: disable=unexpected-keyword-arg
        cls.org = make_org(cached=True)

    # Bug verification

    @run_only_on('sat')
    @tier1
    def test_verify_redmine_4272(self):
        """@Test: gpg info should display key content

        @Feature: GPG Keys

        @Assert: gpg info should display key content
        """
        # Setup a new key file
        content = gen_alphanumeric()
        gpg_key = create_gpg_key_file(content=content)
        self.assertIsNotNone(gpg_key, 'GPG Key file must be created')
        gpg_key = make_gpg_key({
            'key': gpg_key,
            'name': gen_string('alpha'),
            'organization-id': self.org['id'],
        })
        self.assertEqual(gpg_key['content'], content)

    @run_only_on('sat')
    @tier1
    def test_positive_get_info_by_name(self):
        """@Test: Create single gpg key and get its info by name

        @Feature: GPG Keys

        @Assert: specific information for GPG key matches the creation name
        """
        name = gen_string('utf8')
        gpg_key = make_gpg_key({
            u'key': VALID_GPG_KEY_FILE_PATH,
            u'name': name,
            u'organization-id': self.org['id'],
        })
        gpg_key = GPGKey.info({
            u'name': gpg_key['name'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(gpg_key['name'], name)

    # Positive Create

    @skip_if_bug_open('bugzilla', 1172009)
    @run_only_on('sat')
    @tier1
    def test_positive_create_with_default_org(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import using the default created organization

        @feature: GPG Keys

        @assert: gpg key is created

        @BZ: 1172009
        """
        result = Org.list()
        self.assertGreater(len(result), 0, 'No organization found')
        org = result[0]
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = make_gpg_key({
                    'key': VALID_GPG_KEY_FILE_PATH,
                    'name': name,
                    'organization-id': org['id'],
                })
                # Can we find the new object?
                result = GPGKey.exists(
                    {'organization-id': org['id']},
                    (self.search_key, gpg_key[self.search_key])
                )
                self.assertEqual(
                    gpg_key[self.search_key],
                    result[self.search_key]
                )

    @skip_if_bug_open('bugzilla', 1172009)
    @run_only_on('sat')
    @tier1
    def test_positive_create_with_custom_org(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import using a new organization

        @feature: GPG Keys

        @assert: gpg key is created

        @BZ: 1172009
        """
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = make_gpg_key({
                    'key': VALID_GPG_KEY_FILE_PATH,
                    'name': name,
                    'organization-id': self.org['id'],
                })
                # Can we find the new object?
                result = GPGKey.exists(
                    {'organization-id': self.org['id']},
                    (self.search_key, gpg_key[self.search_key])
                )
                self.assertEqual(
                    gpg_key[self.search_key],
                    result[self.search_key]
                )

    # Negative Create

    @skip_if_bug_open('bugzilla', 1172009)
    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then try to create new one with same name

        @feature: GPG Keys

        @assert: gpg key is not created

        @BZ: 1172009
        """
        name = gen_string('alphanumeric')
        gpg_key = make_gpg_key({
            'name': name,
            'organization-id': self.org['id'],
        })
        # Can we find the new object?
        result = GPGKey.exists(
            {'organization-id': self.org['id']},
            (self.search_key, gpg_key[self.search_key])
        )
        self.assertEqual(gpg_key[self.search_key], result[self.search_key])
        # Try to create a gpg key with the same name
        with self.assertRaises(CLIFactoryError):
            make_gpg_key({
                'name': name,
                'organization-id': self.org['id'],
            })

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_no_gpg_key(self):
        """@test: Create gpg key with valid name and no gpg key

        @feature: GPG Keys

        @assert: gpg key is not created
        """
        for name in valid_data_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    GPGKey.create({
                        'name': name,
                        'organization-id': self.org['id'],
                    })

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """@test: Create gpg key with invalid name and valid gpg key via
        file import

        @feature: GPG Keys

        @assert: gpg key is not created
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    # factory will provide a valid key
                    make_gpg_key({
                        'name': name,
                        'organization-id': self.org['id'],
                    })

    # Positive Delete
    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then delete it

        @feature: GPG Keys

        @assert: gpg key is deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = make_gpg_key({
                    'name': name,
                    'organization-id': self.org['id'],
                })
                result = GPGKey.exists(
                    {'organization-id': self.org['id']},
                    (self.search_key, gpg_key[self.search_key])
                )
                self.assertEqual(
                    gpg_key[self.search_key],
                    result[self.search_key]
                )
                GPGKey.delete({
                    'name': name,
                    'organization-id': self.org['id'],
                })
                result = GPGKey.exists(
                    {'organization-id': self.org['id']},
                    (self.search_key, gpg_key[self.search_key])
                )
                self.assertEqual(len(result), 0)

    # Positive Update

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then update its name

        @feature: GPG Keys

        @assert: gpg key is updated
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        for new_name in valid_data_list():
            with self.subTest(new_name):
                GPGKey.update({
                    'name': gpg_key['name'],
                    'new-name': new_name,
                    'organization-id': self.org['id'],
                })
                gpg_key = GPGKey.info({
                    'name': new_name,
                    'organization-id': self.org['id'],
                })

    @run_only_on('sat')
    @tier1
    def test_positive_update_key(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file

        @feature: GPG Keys

        @assert: gpg key is updated
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        content = gen_alphanumeric(gen_integer(20, 50))
        self.assertNotEqual(gpg_key['content'], content)
        local_key = create_gpg_key_file(content)
        self.assertIsNotNone(local_key, 'GPG Key file must be created')
        key = '/tmp/%s' % gen_alphanumeric()
        ssh.upload_file(local_file=local_key, remote_file=key)
        GPGKey.update({
            'key': key,
            'name': gpg_key['name'],
            'organization-id': self.org['id'],
        })
        gpg_key = GPGKey.info({
            'name': gpg_key['name'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(gpg_key['content'], content)

    # Negative Update
    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then fail to update its name

        @feature: GPG Keys

        @assert: gpg key is not updated
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    GPGKey.update({
                        'name': gpg_key['name'],
                        'new-name': new_name,
                        'organization-id': self.org['id'],
                    })

    # Product association
    @run_only_on('sat')
    @tier2
    def test_positive_add_empty_product(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product

        @feature: GPG Keys

        @assert: gpg key is associated with product
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        product = make_product({
            'gpg-key-id': gpg_key['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_add_product_with_repo(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repository
        """
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        Product.update({
            'gpg-key': gpg_key['name'],
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(product['gpg']['gpg-key-id'], gpg_key['id'])
        self.assertEqual(repo['gpg-key']['id'], gpg_key['id'])

    @run_only_on('sat')
    @tier2
    def test_positive_add_product_with_repos(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repositories
        """
        product = make_product({'organization-id': self.org['id']})
        repos = [
            make_repository({'product-id': product['id']})
            for _ in range(gen_integer(2, 5))
        ]
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        Product.update({
            'gpg-key': gpg_key['name'],
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key-id'], gpg_key['id'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(repo['gpg-key']['id'], gpg_key['id'])

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_add_product_using_repo_discovery(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method

        @feature: GPG Keys

        @assert: gpg key is associated with product but not the repositories

        @status: manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_add_repo_from_product_with_repo(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository

        @feature: GPG Keys

        @assert: gpg key is associated with the repository but not with
        the product
        """
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        Repository.update({
            'gpg-key-id': gpg_key['id'],
            'id': repo['id'],
            'organization-id': self.org['id'],
        })
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['gpg-key']['id'], gpg_key['id'])
        self.assertNotEqual(product['gpg'].get('gpg-key-id'), gpg_key['id'])

    @run_only_on('sat')
    @tier2
    def test_positive_add_repo_from_product_with_repos(self):
        """@test: Create gpg key via file import and associate with custom repo

        GPGKey should contain valid name and valid key and should be associated
        to one repository from custom product. Make sure custom product should
        have more than one repository.

        @feature: GPG Keys

        @assert: gpg key is associated with the repository
        """
        product = make_product({'organization-id': self.org['id']})
        repos = [
            make_repository({'product-id': product['id']})
            for _ in range(gen_integer(2, 5))
        ]
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        Repository.update({
            'gpg-key': gpg_key['name'],
            'id': repos[0]['id'],
            'organization-id': self.org['id'],
        })
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertNotEqual(product['gpg'].get('gpg-key-id'), gpg_key['id'])
        # First repo should have a valid gpg key assigned
        repo = Repository.info({'id': repos.pop(0)['id']})
        self.assertEqual(repo['gpg-key']['id'], gpg_key['id'])
        # The rest of repos should not
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(repo['gpg-key'].get('id'), gpg_key['id'])

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_add_repos_using_repo_discovery(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method

        @feature: GPG Keys

        @assert: gpg key is associated with product and all the repositories

        @status: manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_empty_product(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product then
        update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product before/after update
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a product
        Product.update({
            'gpg-key': gpg_key['name'],
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update({
            'name': gpg_key['name'],
            'new-name': new_name,
            'organization-id': self.org['id'],
        })
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({
            'id': gpg_key['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the product
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key'], new_name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_product_with_repo(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product before/after update as well
        as with the repository
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Create a repository and assign it to the product
        repo = make_repository({'product-id': product['id']})
        # Associate gpg key with a product
        Product.update({
            'gpg-key': gpg_key['name'],
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update({
            'name': gpg_key['name'],
            'new-name': new_name,
            'organization-id': self.org['id'],
        })
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({
            'id': gpg_key['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the product
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key'], new_name)
        # Verify changes are reflected in the repository
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['gpg-key'].get('id'), gpg_key['id'])

    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_product_with_repos(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product before/after update as well
        as with the repositories
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Create repositories and assign them to the product
        repos = [
            make_repository({'product-id': product['id']})
            for _ in range(gen_integer(2, 5))
        ]
        # Associate gpg key with a product
        Product.update({
            'gpg-key': gpg_key['name'],
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update({
            'name': gpg_key['name'],
            'new-name': new_name,
            'organization-id': self.org['id'],
        })
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({
            'id': gpg_key['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the product
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key'], new_name)
        # Verify changes are reflected in the repositories
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(repo['gpg-key'].get('name'), new_name)

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_product_using_repo_discovery(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product before/after update but
        not the repositories

        @status: manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_repo_from_product_with_repo(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with the repository before/after update,
        but not with the product
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Create repository, assign product and gpg-key
        repo = make_repository({
            'gpg-key-id': gpg_key['id'],
            'product-id': product['id'],
        })
        # Verify gpg key was associated
        self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update({
            'name': gpg_key['name'],
            'new-name': new_name,
            'organization-id': self.org['id'],
        })
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({
            'id': gpg_key['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the repositories
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['gpg-key'].get('name'), new_name)
        # Verify gpg key wasn't added to the product
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertNotEqual(product['gpg']['gpg-key'], new_name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_repo_from_product_with_repos(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with a single repository before/after
        update and not associated with product or other repositories
        """
        # Create a product and a gpg key
        product = make_product({'organization-id': self.org['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Create repositories and assign them to the product
        repos = [
            make_repository({'product-id': product['id']})
            for _ in range(gen_integer(2, 5))
        ]
        # Associate gpg key with a single repository
        Repository.update({
            'gpg-key': gpg_key['name'],
            'id': repos[0]['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated
        repos[0] = Repository.info({'id': repos[0]['id']})
        self.assertEqual(repos[0]['gpg-key']['name'], gpg_key['name'])
        # Update the gpg key
        new_name = gen_choice(valid_data_list())
        GPGKey.update({
            'name': gpg_key['name'],
            'new-name': new_name,
            'organization-id': self.org['id'],
        })
        # Verify changes are reflected in the gpg key
        gpg_key = GPGKey.info({
            'id': gpg_key['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(gpg_key['name'], new_name)
        # Verify changes are reflected in the associated repository
        repos[0] = Repository.info({'id': repos[0]['id']})
        self.assertEqual(repos[0]['gpg-key'].get('name'), new_name)
        # Verify changes are not reflected in the product
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertNotEqual(product['gpg']['gpg-key'], new_name)
        # Verify changes are not reflected in the rest of repositories
        for repo in repos[1:]:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(repo['gpg-key'].get('name'), new_name)

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_repos_using_repo_discovery(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product and all repositories
        before/after update

        @status: manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_empty_product(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product
        then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product during creation but removed
        from product after deletion
        """
        # Create a product and a gpg key
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        product = make_product({
            'gpg-key-id': gpg_key['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({
            'name': gpg_key['name'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({
                'id': gpg_key['id'],
                'organization-id': self.org['id'],
            })
        # Verify gpg key was disassociated from the product
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_product_with_repo(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product but and its repository
        during creation but removed from product and repository after deletion
        """
        # Create product, repository and gpg key
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a product
        Product.update({
            'gpg-key': gpg_key['name'],
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated both with product and its repository
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({
            'name': gpg_key['name'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({
                'id': gpg_key['id'],
                'organization-id': self.org['id'],
            })
        # Verify gpg key was disassociated from the product and its repository
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])
        self.assertNotEqual(repo['gpg-key'].get('name'), gpg_key['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_product_with_repos(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product and its repositories
        during creation but removed from the product and the repositories after
        deletion
        """
        # Create product, repositories and gpg key
        product = make_product({'organization-id': self.org['id']})
        repos = [
            make_repository({'product-id': product['id']})
            for _ in range(gen_integer(2, 5))
        ]
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a product
        Product.update({
            'gpg-key': gpg_key['name'],
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated with product and its repositories
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key'], gpg_key['name'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({
            'name': gpg_key['name'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({
                'id': gpg_key['id'],
                'organization-id': self.org['id'],
            })
        # Verify gpg key was disassociated from the product and its
        # repositories
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(repo['gpg-key'].get('name'), gpg_key['name'])

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_product_using_repo_discovery(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion

        @status: manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_repo_from_product_with_repo(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with the single repository but not the
        product during creation and was removed from repository after deletion
        """
        # Create product, repository and gpg key
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a repository
        Repository.update({
            'gpg-key': gpg_key['name'],
            'id': repo['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated with the repository but not with the
        # product
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])
        self.assertEqual(repo['gpg-key'].get('name'), gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({
            'name': gpg_key['name'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({
                'id': gpg_key['id'],
                'organization-id': self.org['id'],
            })
        # Verify gpg key was disassociated from the repository
        repo = Repository.info({'id': repo['id']})
        self.assertNotEqual(repo['gpg-key'].get('name'), gpg_key['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_repo_from_product_with_repos(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with a single repository but not the
        product during creation and removed from repository after deletion
        """
        # Create product, repositories and gpg key
        product = make_product({'organization-id': self.org['id']})
        repos = []
        for _ in range(gen_integer(2, 5)):
            repos.append(make_repository({'product-id': product['id']}))
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        # Associate gpg key with a repository
        Repository.update({
            'gpg-key': gpg_key['name'],
            'id': repos[0]['id'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was associated with the repository
        repos[0] = Repository.info({'id': repos[0]['id']})
        self.assertEqual(repos[0]['gpg-key']['name'], gpg_key['name'])
        # Delete the gpg key
        GPGKey.delete({
            'name': gpg_key['name'],
            'organization-id': self.org['id'],
        })
        # Verify gpg key was actually deleted
        with self.assertRaises(CLIReturnCodeError):
            GPGKey.info({
                'id': gpg_key['id'],
                'organization-id': self.org['id'],
            })
        # Verify gpg key is not associated with any repository or the product
        # itself
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertNotEqual(product['gpg']['gpg-key'], gpg_key['name'])
        for repo in repos:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(repo['gpg-key'].get('name'), gpg_key['name'])

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_repos_using_repo_discovery(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with product and all repositories
        during creation but removed from product and all repositories after
        deletion

        @status: manual
        """

    # Content

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_consume_content_using_repo(self):
        """@test: Hosts can install packages using gpg key associated with
        single custom repository

        @feature: GPG Keys

        @assert: host can install package from custom repository

        @status: manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_consume_content_using_repos(self):
        """@test: Hosts can install packages using gpg key associated with
        multiple custom repositories

        @feature: GPG Keys

        @assert: host can install package from custom repositories

        @status: manual
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_consume_content_using_repos_and_different_keys(self):
        """@test: Hosts can install packages using different gpg keys
        associated with multiple custom repositories

        @feature: GPG Keys

        @assert: host can install package from custom repositories

        @status: manual
        """

    # Miscelaneous

    @run_only_on('sat')
    @tier1
    def test_positive_list(self):
        """@test: Create gpg key and list it

        @feature: GPG Keys

        @assert: gpg key is displayed/listed
        """
        gpg_key = make_gpg_key({
            'key': VALID_GPG_KEY_FILE_PATH,
            'organization-id': self.org['id'],
        })
        gpg_keys_list = GPGKey.list({'organization-id': self.org['id']})
        self.assertIn(gpg_key['id'], [gpg['id'] for gpg in gpg_keys_list])

    @run_only_on('sat')
    @tier1
    def test_positive_search(self):
        """@test: Create gpg key and search/find it

        @feature: GPG Keys

        @assert: gpg key can be found
        """
        for name in valid_data_list():
            with self.subTest(name):
                gpg_key = make_gpg_key({
                    'key': VALID_GPG_KEY_FILE_PATH,
                    'name': name,
                    'organization-id': self.org['id'],
                })
                # Can we find the new object?
                result = GPGKey.exists(
                    {'organization-id': self.org['id']},
                    search=('name', gpg_key['name'])
                )
                self.assertEqual(gpg_key['name'], result['name'])
