"""Test class for Repository UI"""

from ddt import ddt
from fauxfactory import gen_string
from nose.plugins.attrib import attr
from robottelo import entities
from robottelo.common.constants import (
    DOCKER_REGISTRY_HUB,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    REPO_DISCOVERY_URL,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import generate_strings_list, read_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_repository
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@ddt
class Repos(UITestCase):
    """Implements Repos tests in UI"""

    org_name = None
    org_id = None
    loc_name = None
    loc_id = None

    def setUp(self):
        super(Repos, self).setUp()
        # Make sure to use the Class' org_name instance
        if Repos.org_name is None and Repos.loc_name is None:
            org_name = gen_string("alpha", 10)
            loc_name = gen_string("alpha", 10)
            org_attrs = entities.Organization(name=org_name).create()
            loc_attrs = entities.Location(name=loc_name).create()
            Repos.org_name = org_attrs['name']
            Repos.org_id = org_attrs['id']
            Repos.loc_name = loc_attrs['name']
            Repos.loc_id = loc_attrs['id']

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_create_repo_1(self, repo_name):
        """@Test: Create repository with minimal input parameters

        @Feature: Content Repos - Positive Create

        @Assert: Repos is created

        """

        # Creates new product
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id,
        ).create()['name']
        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_create_repo_2(self, repo_name):
        """@Test: Create repository in two different orgs with same name

        @Assert: Repos is created

        @Feature: Content Repos - Positive Create

        """

        org_2_name = gen_string("alpha", 10)
        # Creates new product_1
        product_1_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id,
        ).create()['name']

        # Create new product_2 under new organization_2
        org_2_id = entities.Organization(name=org_2_name).create()['id']
        product_2_name = entities.Product(
            organization=org_2_id,
            location=self.loc_id,
        ).create()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_1_name,
                            url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))
            make_repository(session, org=org_2_name, loc=self.loc_name,
                            name=repo_name, product=product_2_name,
                            url=FAKE_1_YUM_REPO, force_context=True)
            self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented', 'docker')
    def test_create_repo_3(self):
        """@Test: Create a Docker-based repository

        @Feature: Content Repos - Positive Create

        @Assert: Docker-based repo is created.

        """

        # Creates new product
        repo_name = u'wordpress'
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id,
        ).create()['name']
        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            repo_type=u'docker', url=DOCKER_REGISTRY_HUB)
            self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented', 'docker')
    def test_create_repo_4(self):
        """@Test: Create and sync a Docker-based repository

        @Feature: Content Repos - Positive Create

        @Assert: Docker-based repo is created and synchronized.

        """

        # Creates new product
        repo_name = u'wordpress'
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id,
        ).create()['name']
        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            repo_type=u'docker', url=DOCKER_REGISTRY_HUB)
            self.assertIsNotNone(self.repository.search(repo_name))
            # Synchronize it
            self.navigator.go_to_sync_status()
            synced = self.sync.sync_custom_repos(product_name, [repo_name])
            self.assertIsNotNone(synced)

    @run_only_on('sat')
    @data("", "   ")
    def test_negative_create_1(self, repo_name):
        """@Test: Create repository with blank and whitespace in name

        @Feature: Content Repos - Negative Create zero length

        @Assert: Repos is not created

        """

        # Creates new product
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            invalid = self.products.wait_until_element(
                common_locators["common_invalid"])
            self.assertIsNotNone(invalid)

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_2(self, repo_name):
        """@Test: Create repository with same name

        @Feature: Content Repos - Negative Create with same name

        @Assert: Repos is not created

        """

        # Creates new product
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            invalid = self.products.wait_until_element(
                common_locators["common_invalid"])
            self.assertTrue(invalid)

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_3(self, repo_name):
        """@Test: Create content repository with 256 characters in name

        @Feature: Content Repos - Negative Create

        @Assert: Repos is not created

        """

        # Creates new product
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            error = self.repository.wait_until_element(
                common_locators["common_haserror"])
            self.assertTrue(error)

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_1(self, repo_name):
        """@Test: Update content repository with new URL

        @Feature: Content Repo - Positive Update

        @Assert: Repo is updated with new url

        """

        locator = locators["repo.fetch_url"]
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.search(repo_name).click()
            self.repository.wait_for_ajax()
            url_text = self.repository.wait_until_element(locator).text
            self.assertEqual(url_text, FAKE_1_YUM_REPO)
            self.navigator.go_to_products()
            self.products.search(product_name).click()
            self.repository.update(repo_name, new_url=FAKE_2_YUM_REPO)
            url_text = self.repository.wait_until_element(locator).text
            self.assertEqual(url_text, FAKE_2_YUM_REPO)

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_2(self, repo_name):
        """@Test: Update content repository with new gpg-key

        @Feature: Content Repo - Positive Update

        @Assert: Repo is updated with new gpg key

        """

        key_1_content = read_data_file(VALID_GPG_KEY_FILE)
        key_2_content = read_data_file(VALID_GPG_KEY_BETA_FILE)
        locator = locators["repo.fetch_gpgkey"]
        # Create two new GPGKey's
        gpgkey_1_name = entities.GPGKey(
            content=key_1_content,
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']
        gpgkey_2_name = entities.GPGKey(
            content=key_2_content,
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']

        # Creates new product
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO, gpg_key=gpgkey_1_name)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.search(repo_name).click()
            self.repository.wait_for_ajax()
            gpgkey_1_text = self.repository.wait_until_element(locator).text
            self.assertEqual(gpgkey_1_text, gpgkey_1_name)
            self.navigator.go_to_products()
            self.products.search(product_name).click()
            self.repository.update(repo_name, new_gpg_key=gpgkey_2_name)
            gpgkey_2_text = self.repository.wait_until_element(locator).text
            self.assertEqual(gpgkey_2_text, gpgkey_2_name)

    @run_only_on('sat')
    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_remove_repo(self, repo_name):
        """@Test: Create content repository and remove it

        @Feature: Content Repos - Positive Delete

        @Assert: Repos is Deleted

        """

        # Creates new product
        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, loc=self.loc_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.delete(repo_name)
            self.assertIsNone(self.repository.search(repo_name))

    @run_only_on('sat')
    def test_discover_repo_1(self):
        """@Test: Create repository via repo-discovery under existing product

        @Feature: Content Repos - Discover repo via http URL

        @Assert: Repos is discovered and created

        """

        discovered_urls = "fakerepo01/"

        product_name = entities.Product(
            organization=self.org_id,
            location=self.loc_id
        ).create()['name']

        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_products()
            self.repository.discover_repo(url_to_discover=REPO_DISCOVERY_URL,
                                          discovered_urls=[discovered_urls],
                                          product=product_name)

    @run_only_on('sat')
    def test_discover_repo_2(self):
        """@Test: Create repository via repo discovery under new product

        @Feature: Content Repos - Discover repo via http URL

        @Assert: Repos is discovered and created

        """

        product_name = gen_string("alpha", 8)
        discovered_urls = "fakerepo01/"
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_select_loc(self.loc_name)
            session.nav.go_to_products()
            self.repository.discover_repo(url_to_discover=REPO_DISCOVERY_URL,
                                          discovered_urls=[discovered_urls],
                                          product=product_name,
                                          new_product=True)
            self.assertIsNotNone(self.products.search(product_name))
