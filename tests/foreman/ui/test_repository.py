"""
Test class for Repository UI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.constants import (VALID_GPG_KEY_FILE,
                                        VALID_GPG_KEY_BETA_FILE)
from robottelo.common.decorators import data
from robottelo.common.helpers import (generate_string, skip_if_bz_bug_open,
                                      generate_strings_list, get_data_file)
from robottelo.ui.factory import make_org
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.session import Session
from tests.foreman.ui.baseui import BaseUI


@ddt
class Repos(BaseUI):
    """
    Implements Repos tests in UI
    """

    org_name = None

    def setUp(self):
        super(Repos, self).setUp()
        # Make sure to use the Class' org_name instance
        if Repos.org_name is None:
            Repos.org_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Repos.org_name)

    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_create_repo(self, repo_name):
        """
        @Feature: Content Repos - Positive Create
        @Test: Create Content Repos with minimal input parameters
        @Assert: Repos is created
        """

        prd_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))

    def test_negative_create_1(self):
        """
        @Feature: Content Repos - Negative Create zero length
        @Test: Create Content Repos without input parameter
        @Assert: Repos is not created
        """

        locator = common_locators["common_invalid"]
        repo_name = ""
        prd_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        invalid = self.products.wait_until_element(locator)
        self.assertTrue(invalid)

    def test_negative_create_2(self):
        """
        @Feature: Content Repos - Negative Create with whitespace
        @Test: Create Content Repos with whitespace input parameter
        @Assert: Repos is not created
        """

        locator = common_locators["common_invalid"]
        repo_name = "   "
        prd_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        invalid = self.products.wait_until_element(locator)
        self.assertTrue(invalid)

    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_3(self, repo_name):
        """
        @Feature: Content Repos - Negative Create with same name
        @Test: Create Content Repos with same name input parameter
        @Assert: Repos is not created
        @BZ: 1081059
        """
        skip_if_bz_bug_open("1081059")

        locator = common_locators["common_invalid"]
        prd_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_products()
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        invalid = self.products.wait_until_element(locator)
        self.assertTrue(invalid)

    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_4(self, repo_name):
        """
        @Feature: Content Repos - Negative Create with same name
        @Test: Create Content Repos with long name input parameter
        @Assert: Repos is not created
        """

        locator = common_locators["common_haserror"]
        prd_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        error = self.repository.wait_until_element(locator)
        self.assertTrue(error)

    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_1(self, repo_name):
        """
        @Feature: Content Repo - Positive Update
        @Test: Update Content Repo with repository url
        @Assert: Repo is updated with new url
        """

        prd_name = generate_string("alpha", 8)
        locator = locators["repo.fetch_url"]
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        new_repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo2/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.repository.search(repo_name).click()
        url_text = self.repository.wait_until_element(locator).text
        self.assertEqual(url_text, repo_url)
        self.navigator.go_to_products()
        self.products.search(prd_name).click()
        self.repository.update(repo_name, new_url=new_repo_url)
        url_text = self.repository.wait_until_element(locator).text
        self.assertEqual(url_text, new_repo_url)

    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_2(self, repo_name):
        """
        @Feature: Content Repo - Positive Update
        @Test: Update Content Repo with gpg key
        @Assert: Repo is updated with new gpg key
        """

        key_path1 = get_data_file(VALID_GPG_KEY_FILE)
        key_path2 = get_data_file(VALID_GPG_KEY_BETA_FILE)
        prd_name = generate_string("alpha", 8)
        gpgkey_name1 = generate_string("alpha", 8)
        gpgkey_name2 = generate_string("alpha", 8)
        locator = locators["repo.fetch_gpgkey"]
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(gpgkey_name1, upload_key=True, key_path=key_path1)
        self.assertIsNotNone(self.gpgkey.search(gpgkey_name1))
        self.gpgkey.create(gpgkey_name2, upload_key=True, key_path=key_path2)
        self.assertIsNotNone(self.gpgkey.search(gpgkey_name2))
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url,
                               gpg_key=gpgkey_name1)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.repository.search(repo_name).click()
        gpgkey_text1 = self.repository.wait_until_element(locator).text
        self.assertEqual(gpgkey_text1, gpgkey_name1)
        self.navigator.go_to_products()
        self.products.search(prd_name).click()
        self.repository.update(repo_name, new_gpg_key=gpgkey_name2)
        gpgkey_text2 = self.repository.wait_until_element(locator).text
        self.assertEqual(gpgkey_text2, gpgkey_name2)

    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_remove_repo(self, repo_name):
        """
        @Feature: Content Repos - Positive Delete
        @Test: Create Content Repos with minimal input parameters
        @Assert: Repos is Deleted
        """

        prd_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.repository.delete(repo_name)
        self.assertIsNone(self.repository.search(repo_name))

    def test_discover_repo_1(self):
        """
        @Feature: Content Repos - Discover repo via http URL
        @Test: Create Content Repos via repo discovery under existing
        product
        @Assert: Repos is discovered and created
        """

        prd_name = generate_string("alpha", 8)
        url = "http://omaciel.fedorapeople.org/"
        discovered_urls = ["fakerepo01/"]
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.discover_repo(url, discovered_urls, product=prd_name)

    def test_discover_repo_2(self):
        """
        @Feature: Content Repos - Discover repo via http URL
        @Test: Create Content Repos via repo discovery under new
        product
        @Assert: Repos is discovered and created
        """

        prd_name = generate_string("alpha", 8)
        url = "http://omaciel.fedorapeople.org/"
        discovered_urls = ["fakerepo01/"]
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.repository.discover_repo(url, discovered_urls,
                                      product=prd_name, new_product=True)
        self.assertIsNotNone(self.products.search(prd_name))
