# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Repository UI"""

import time

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import (
    CHECKSUM_TYPE,
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    REPO_DISCOVERY_URL,
    REPO_TYPE,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.decorators import run_only_on
from robottelo.helpers import (
    generate_strings_list,
    invalid_values_list,
    read_data_file,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_repository
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


def valid_repo_names_docker_sync():
    """Returns a list of valid repo names for docker sync test"""
    return [
        gen_string('alpha', 8).lower(),
        gen_string('numeric', 8),
        gen_string('alphanumeric', 8).lower(),
        gen_string('html', 8),
        gen_string('utf8', 8),
    ]


class Repos(UITestCase):
    """Implements Repos tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(Repos, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.loc = entities.Location().create()

    def setup_navigate_syncnow(self, session, prd_name, repo_name):
        """Helps with Navigation for syncing via the repos page."""
        strategy1, value1 = locators['repo.select']
        strategy2, value2 = locators['repo.select_checkbox']
        session.nav.go_to_select_org(self.organization.name)
        session.nav.go_to_products()
        session.nav.click((strategy1, value1 % prd_name))
        session.nav.click((strategy2, value2 % repo_name))
        session.nav.click(locators['repo.sync_now'])

    def prd_sync_is_ok(self, repo_name):
        """Asserts whether the sync Result is successful."""
        strategy1, value1 = locators['repo.select_event']
        self.repository.click(tab_locators['prd.tab_tasks'])
        self.repository.click((strategy1, value1 % repo_name))
        timeout = time.time() + 60 * 10
        spinner = self.repository.wait_until_element(
            locators['repo.result_spinner'], 20)
        # Waits until result spinner is visible on the UI or times out
        # after 10mins
        while spinner:
            if time.time() > timeout:
                break
            spinner = self.repository.wait_until_element(
                locators['repo.result_spinner'], 3)
        result = self.repository.wait_until_element(
            locators['repo.result_event']).text
        return result == 'success'

    @run_only_on('sat')
    def test_create_repo_basic(self):
        """@Test: Create repository with minimal input parameters

        @Feature: Content Repos - Positive Create

        @Assert: Repos is created

        """
        prod = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    make_repository(
                        session,
                        org=self.organization.name,
                        name=repo_name,
                        product=prod.name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    def test_create_repo_in_different_orgs(self):
        """@Test: Create repository in two different orgs with same name

        @Assert: Repos is created

        @Feature: Content Repos - Positive Create

        """
        # Creates new product_1
        product_1 = entities.Product(organization=self.organization).create()
        # Create new product_2 under new organization_2
        org_2 = entities.Organization(name=gen_string('alpha')).create()
        product_2 = entities.Product(organization=org_2).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    make_repository(
                        session,
                        org=self.organization.name,
                        name=repo_name,
                        product=product_1.name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    make_repository(
                        session,
                        org=org_2.name,
                        name=repo_name,
                        product=product_2.name,
                        url=FAKE_1_YUM_REPO,
                        force_context=True,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    def test_create_repo_with_checksum(self):
        """@Test: Create repository with checksum type as sha256.

        @Feature: Content Repos - Positive Create

        @Assert: Repos is created with checksum type as sha256.

        """
        checksum = CHECKSUM_TYPE[u'sha256']
        # Creates new product
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    make_repository(
                        session,
                        org=self.organization.name,
                        name=repo_name,
                        product=product.name,
                        url=FAKE_1_YUM_REPO,
                        repo_checksum=checksum,
                    )
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'checksum', checksum))

    @run_only_on('sat')
    def test_negative_create_with_blank(self):
        """@Test: Create repository with invalid name

        @Feature: Content Repos - Negative Create

        @Assert: Repos is not created

        """
        # Creates new product
        product = entities.Product(organization=self.organization).create()
        for repo_name in invalid_values_list(interface='ui'):
            with self.subTest(repo_name):
                with Session(self.browser) as session:
                    make_repository(
                        session,
                        org=self.organization.name,
                        name=repo_name,
                        product=product.name,
                        url=FAKE_1_YUM_REPO,
                    )
                    invalid = self.products.wait_until_element(
                        common_locators['common_invalid'])
                    self.assertIsNotNone(invalid)

    @run_only_on('sat')
    def test_negative_create_with_same_names(self):
        """@Test: Create repository with same name

        @Feature: Content Repos - Negative Create with same name

        @Assert: Repos is not created

        """
        repo_name = gen_string('alphanumeric')
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            make_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=product.name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            make_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=product.name,
                url=FAKE_1_YUM_REPO,
            )
            invalid = self.products.wait_until_element(
                common_locators['common_invalid'])
            self.assertTrue(invalid)

    @run_only_on('sat')
    def test_positive_update_URL(self):
        """@Test: Update content repository with new URL

        @Feature: Content Repo - Positive Update

        @Assert: Repo is updated with new url

        """
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    make_repository(
                        session,
                        org=self.organization.name,
                        name=repo_name,
                        product=product.name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'url', FAKE_1_YUM_REPO))
                    self.navigator.go_to_products()
                    self.products.search(product.name).click()
                    self.repository.update(repo_name, new_url=FAKE_2_YUM_REPO)
                    self.navigator.go_to_products()
                    self.products.search(product.name).click()
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'url', FAKE_2_YUM_REPO))

    @run_only_on('sat')
    def test_positive_update_GPG(self):
        """@Test: Update content repository with new gpg-key

        @Feature: Content Repo - Positive Update

        @Assert: Repo is updated with new gpg key

        """
        repo_name = gen_string('alphanumeric')
        key_1_content = read_data_file(VALID_GPG_KEY_FILE)
        key_2_content = read_data_file(VALID_GPG_KEY_BETA_FILE)
        # Create two new GPGKey's
        gpgkey_1 = entities.GPGKey(
            content=key_1_content,
            organization=self.organization,
        ).create()
        gpgkey_2 = entities.GPGKey(
            content=key_2_content,
            organization=self.organization,
        ).create()
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            make_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=product.name,
                url=FAKE_1_YUM_REPO,
                gpg_key=gpgkey_1.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'gpgkey', gpgkey_1.name))
            self.navigator.go_to_products()
            self.products.search(product.name).click()
            self.repository.update(repo_name, new_gpg_key=gpgkey_2.name)
            self.navigator.go_to_products()
            self.products.search(product.name).click()
            self.assertTrue(self.repository.validate_field(
                repo_name, 'gpgkey', gpgkey_2.name))

    @run_only_on('sat')
    def test_positive_update_checksum_type(self):
        """@Test: Update content repository with new checksum type

        @Feature: Content Repo - Positive Update of checksum type.

        @Assert: Repo is updated with new checksum type.

        """
        repo_name = gen_string('alphanumeric')
        checksum_default = CHECKSUM_TYPE['default']
        checksum_update = CHECKSUM_TYPE['sha1']
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            make_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=product.name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'checksum', checksum_default))
            self.navigator.go_to_products()
            self.products.search(product.name).click()
            self.repository.update(
                repo_name, new_repo_checksum=checksum_update)
            self.navigator.go_to_products()
            self.products.search(product.name).click()
            self.assertTrue(self.repository.validate_field(
                repo_name, 'checksum', checksum_update))

    @run_only_on('sat')
    def test_remove_repo(self):
        """@Test: Create content repository and remove it

        @Feature: Content Repos - Positive Delete

        @Assert: Repos is Deleted

        """
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    make_repository(
                        session,
                        org=self.organization.name,
                        name=repo_name,
                        product=product.name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.repository.delete(repo_name)
                    self.assertIsNone(self.repository.search(repo_name))

    @run_only_on('sat')
    def test_discover_repo_via_existing_product(self):
        """@Test: Create repository via repo-discovery under existing product

        @Feature: Content Repos - Discover repo via http URL

        @Assert: Repos is discovered and created

        """
        discovered_urls = 'fakerepo01/'
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_products()
            self.repository.discover_repo(
                url_to_discover=REPO_DISCOVERY_URL,
                discovered_urls=[discovered_urls],
                product=product.name,
            )

    @run_only_on('sat')
    def test_discover_repo_via_new_product(self):
        """@Test: Create repository via repo discovery under new product

        @Feature: Content Repos - Discover repo via http URL

        @Assert: Repos is discovered and created

        """
        product_name = gen_string('alpha', 8)
        discovered_urls = 'fakerepo01/'
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_select_loc(self.loc.name)
            session.nav.go_to_products()
            self.repository.discover_repo(
                url_to_discover=REPO_DISCOVERY_URL,
                discovered_urls=[discovered_urls],
                product=product_name,
                new_product=True,
            )
            self.assertIsNotNone(self.products.search(product_name))

    @run_only_on('sat')
    def test_syncnow_custom_repos_yum(self):
        """@Test: Create Custom yum repos and sync it via the repos page.

        @Feature: Custom yum Repos - Sync via repos page

        @Assert: Whether Sync is successful

        """
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    # Creates new repository using api
                    entities.Repository(
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                        product=product,
                    ).create()
                    self.setup_navigate_syncnow(
                        session,
                        product.name,
                        repo_name,
                    )
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    def test_syncnow_custom_repos_puppet(self):
        """@Test: Create Custom puppet repos and sync it via the repos page.

        @Feature: Custom puppet Repos - Sync via repos page

        @Assert: Whether Sync is successful

        """
        # Creates new product
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    # Creates new puppet repository
                    entities.Repository(
                        name=repo_name,
                        url=FAKE_0_PUPPET_REPO,
                        product=product,
                        content_type=REPO_TYPE['puppet'],
                    ).create()
                    self.setup_navigate_syncnow(
                        session,
                        product.name,
                        repo_name,
                    )
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    def test_syncnow_custom_repos_docker(self):
        """@Test: Create Custom docker repos and sync it via the repos page.

        @Feature: Custom docker Repos - Sync via repos page

        @Assert: Whether Sync is successful

        """
        # Creates new product
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in valid_repo_names_docker_sync():
                with self.subTest(repo_name):
                            # Creates new puppet repository
                    entities.Repository(
                        name=repo_name,
                        url=DOCKER_REGISTRY_HUB,
                        product=product,
                        content_type=REPO_TYPE['docker'],
                    ).create()
                    self.setup_navigate_syncnow(
                        session, product.name, repo_name,)
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))
