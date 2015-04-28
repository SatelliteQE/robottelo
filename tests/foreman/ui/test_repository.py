"""Test class for Repository UI"""

import time
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from robottelo.common.constants import (
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
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import generate_strings_list, read_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_repository
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@ddt
class Repos(UITestCase):
    """Implements Repos tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        org_attrs = entities.Organization().create_json()
        loc_attrs = entities.Location().create_json()
        cls.org_name = org_attrs['name']
        cls.org_id = org_attrs['id']
        cls.loc_name = loc_attrs['name']
        cls.loc_id = loc_attrs['id']

        super(Repos, cls).setUpClass()

    def setup_navigate_syncnow(self, session, prd_name, repo_name):
        """Helps with Navigation for syncing via the repos page."""
        strategy1, value1 = locators["repo.select"]
        strategy2, value2 = locators["repo.select_checkbox"]
        session.nav.go_to_select_org(self.org_name)
        session.nav.go_to_products()
        session.nav.wait_until_element(
            (strategy1, value1 % prd_name)).click()
        session.nav.wait_until_element(
            (strategy2, value2 % repo_name)).click()
        session.nav.wait_for_ajax()
        session.nav.wait_until_element(locators["repo.sync_now"]).click()
        session.nav.wait_for_ajax()

    def prd_sync_is_ok(self, repo_name):
        """Asserts whether the sync Result is successful."""
        strategy1, value1 = locators["repo.select_event"]
        self.repository.wait_until_element(
            tab_locators["prd.tab_tasks"]).click()
        self.repository.wait_for_ajax()
        self.repository.wait_until_element(
            (strategy1, value1 % repo_name)).click()
        self.repository.wait_for_ajax()
        timeout = time.time() + 60 * 10
        spinner = self.repository.wait_until_element(
            locators["repo.result_spinner"], 20)
        # Waits until result spinner is visible on the UI or times out
        # after 10mins
        while spinner:
            if time.time() > timeout:
                break
            spinner = self.repository.wait_until_element(
                locators["repo.result_spinner"], 3)
        result = self.repository.wait_until_element(
            locators["repo.result_event"]).text
        return result == 'success'

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_create_repo_1(self, repo_name):
        """@Test: Create repository with minimal input parameters

        @Feature: Content Repos - Positive Create

        @Assert: Repos is created

        """
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']
        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, name=repo_name,
                            product=product_name, url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
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
        ).create_json()['name']

        # Create new product_2 under new organization_2
        org_2_id = entities.Organization(name=org_2_name).create_json()['id']
        product_2_name = entities.Product(
            organization=org_2_id,
        ).create_json()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name, name=repo_name,
                            product=product_1_name, url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))
            make_repository(session, org=org_2_name, name=repo_name,
                            product=product_2_name,
                            url=FAKE_1_YUM_REPO, force_context=True)
            self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    def test_create_repo_3(self):
        """@Test: Create a Docker-based repository

        @Feature: Content Repos - Positive Create

        @Assert: Docker-based repo is created.

        """
        upstream_name = u'busybox'
        repo_name = gen_string("alpha", 8)
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']
        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
                            name=repo_name, product=product_name,
                            repo_type=REPO_TYPE['docker'],
                            url=DOCKER_REGISTRY_HUB,
                            upstream_repo_name=upstream_name)
            self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1167837)
    def test_create_repo_4(self):
        """@Test: Create and sync a Docker-based repository

        @Feature: Content Repos - Positive Create

        @Assert: Docker-based repo is created and synchronized.

        """
        # Creates new product
        upstream_name = u'busybox'
        repo_name = gen_string("alpha", 8)
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']
        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
                            name=repo_name, product=product_name,
                            repo_type=REPO_TYPE['docker'],
                            url=DOCKER_REGISTRY_HUB,
                            upstream_repo_name=upstream_name)
            self.assertIsNotNone(self.repository.search(repo_name))
            # Synchronize it
            self.navigator.go_to_sync_status()
            synced = self.sync.sync_custom_repos(product_name, [repo_name])
            self.assertTrue(synced)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_create_repo_5(self, repo_name):
        """@Test: Create repository with checksum type as sha256.

        @Feature: Content Repos - Positive Create

        @Assert: Repos is created with checksum type as sha256.

        """
        locator = locators['repo.fetch_checksum']
        checksum = CHECKSUM_TYPE[u'sha256']
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']
        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO, repo_checksum=checksum)
            self.repository.search(repo_name).click()
            self.repository.wait_for_ajax()
            checksum_text = session.nav.wait_until_element(locator).text
            self.assertEqual(checksum_text, checksum)

    @run_only_on('sat')
    @data("", "   ")
    def test_negative_create_1(self, repo_name):
        """@Test: Create repository with blank and whitespace in name

        @Feature: Content Repos - Negative Create zero length

        @Assert: Repos is not created

        """
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            invalid = self.products.wait_until_element(
                common_locators["common_invalid"])
            self.assertIsNotNone(invalid)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_negative_create_2(self, repo_name):
        """@Test: Create repository with same name

        @Feature: Content Repos - Negative Create with same name

        @Assert: Repos is not created

        """
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id,
        ).create_json()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))
            make_repository(session, org=self.org_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            invalid = self.products.wait_until_element(
                common_locators["common_invalid"])
            self.assertTrue(invalid)

    @run_only_on('sat')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_3(self, repo_name):
        """@Test: Create content repository with 256 characters in name

        @Feature: Content Repos - Negative Create

        @Assert: Repos is not created

        """
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            error = self.repository.wait_until_element(
                common_locators["common_haserror"])
            self.assertTrue(error)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_positive_update_1(self, repo_name):
        """@Test: Update content repository with new URL

        @Feature: Content Repo - Positive Update

        @Assert: Repo is updated with new url

        """
        locator = locators["repo.fetch_url"]
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
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
            organization=self.org_id
        ).create_json()['name']
        gpgkey_2_name = entities.GPGKey(
            content=key_2_content,
            organization=self.org_id
        ).create_json()['name']

        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
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
    @data(*generate_strings_list())
    def test_positive_update_3(self, repo_name):
        """@Test: Update content repository with new checksum type

        @Feature: Content Repo - Positive Update of checksum type.

        @Assert: Repo is updated with new checksum type.

        """
        locator = locators["repo.fetch_checksum"]
        checksum_default = CHECKSUM_TYPE['default']
        checksum_update = CHECKSUM_TYPE['sha1']
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
                            name=repo_name, product=product_name,
                            url=FAKE_1_YUM_REPO)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.search(repo_name).click()
            self.repository.wait_for_ajax()
            checksum_text = self.repository.wait_until_element(locator).text
            self.assertEqual(checksum_text, checksum_default)
            self.navigator.go_to_products()
            self.products.search(product_name).click()
            self.repository.update(repo_name,
                                   new_repo_checksum=checksum_update)
            checksum_text = self.repository.wait_until_element(locator).text
            self.assertEqual(checksum_text, checksum_update)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_remove_repo(self, repo_name):
        """@Test: Create content repository and remove it

        @Feature: Content Repos - Positive Delete

        @Assert: Repos is Deleted

        """
        # Creates new product
        product_name = entities.Product(
            organization=self.org_id
        ).create_json()['name']

        with Session(self.browser) as session:
            make_repository(session, org=self.org_name,
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
            organization=self.org_id
        ).create_json()['name']

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

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_syncnow_custom_repos_1(self, repository_name):
        """@Test: Create Custom yum repos and sync it via the repos page.

        @Feature: Custom yum Repos - Sync via repos page

        @Assert: Whether Sync is successful

        """
        # Creates new product
        product_attrs = entities.Product(
            organization=self.org_id
        ).create_json()
        # Creates new repository
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id']
        ).create_json()
        with Session(self.browser) as session:
            self.setup_navigate_syncnow(session,
                                        product_attrs['name'],
                                        repository_name)
            # prd_sync_is_ok returns boolean values and not objects
            self.assertTrue(self.prd_sync_is_ok(repository_name))

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_syncnow_custom_repos_2(self, repository_name):
        """@Test: Create Custom puppet repos and sync it via the repos page.

        @Feature: Custom puppet Repos - Sync via repos page

        @Assert: Whether Sync is successful

        """
        # Creates new product
        product_attrs = entities.Product(
            organization=self.org_id
        ).create_json()
        # Creates new puppet repository
        entities.Repository(
            name=repository_name,
            url=FAKE_0_PUPPET_REPO,
            product=product_attrs['id'],
            content_type=REPO_TYPE['puppet'],
        ).create_json()
        with Session(self.browser) as session:
            self.setup_navigate_syncnow(session,
                                        product_attrs['name'],
                                        repository_name)
            # prd_sync_is_ok returns boolean values and not objects
            self.assertTrue(self.prd_sync_is_ok(repository_name))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1167837)
    @data(gen_string('alpha', 8).lower(),
          gen_string('numeric', 8),
          gen_string('alphanumeric', 8).lower(),
          gen_string('html', 8),
          gen_string('utf8', 8))
    def test_syncnow_custom_repos_3(self, repository_name):
        """@Test: Create Custom docker repos and sync it via the repos page.

        @Feature: Custom docker Repos - Sync via repos page

        @Assert: Whether Sync is successful

        """
        # Creates new product
        product_attrs = entities.Product(
            organization=self.org_id
        ).create_json()
        # Creates new puppet repository
        entities.Repository(
            name=repository_name,
            url=DOCKER_REGISTRY_HUB,
            product=product_attrs['id'],
            content_type=REPO_TYPE['docker'],
            docker_upstream_name=u'busybox',
        ).create_json()
        with Session(self.browser) as session:
            self.setup_navigate_syncnow(session,
                                        product_attrs['name'],
                                        repository_name)
            # prd_sync_is_ok returns boolean values and not objects
            self.assertTrue(self.prd_sync_is_ok(repository_name))
