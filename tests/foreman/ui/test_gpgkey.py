# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for GPG Key UI
"""

import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.constants import (NOT_IMPLEMENTED, VALID_GPG_KEY_FILE,
                                        VALID_GPG_KEY_BETA_FILE)
from robottelo.common.decorators import data, skip_if_bz_bug_open
from robottelo.common.helpers import (generate_string, get_data_file,
                                      read_data_file, valid_names_list,
                                      invalid_names_list, valid_data_list,
                                      generate_strings_list)
from robottelo.ui.factory import make_org
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session
from tests.foreman.ui.baseui import BaseUI

REPO_URL = "http://inecas.fedorapeople.org/fakerepos/zoo2/"
REPO2_URL = "http://inecas.fedorapeople.org/fakerepos/zoo3/"


@ddt
class GPGKey(BaseUI):
    """Implements tests for GPG Keys via UI"""

    org_name = None

    def setUp(self):
        super(GPGKey, self).setUp()

        # Make sure to use the Class' org_name instance
        if GPGKey.org_name is None:
            GPGKey.org_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=GPGKey.org_name)

    # Positive Create

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_names_list())
    def test_positive_create_1(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file import
        @assert: gpg key is created
        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_names_list())
    def test_positive_create_2(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string
        @assert: gpg key is created
        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))

    # Negative Create

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_data_list())
    def test_negative_create_1(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file import
        then try to create new one with same name
        @assert: gpg key is not created
        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.error"]))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_data_list())
    def test_negative_create_2(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string import then try to create new one with same name
        @assert: gpg key is not created
        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.create(name, key_content=key_content)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.error"]))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_data_list())
    def test_negative_create_3(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and no gpg key
        @assert: gpg key is not created
        """

        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        with self.assertRaises(Exception):
            self.gpgkey.create(name)
        self.assertIsNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*invalid_names_list())
    def test_negative_create_4(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with invalid name and valid gpg key via
        file import
        @assert: gpg key is not created
        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.error"]))
        self.assertIsNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*invalid_names_list())
    def test_negative_create_5(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with invalid name and valid gpg key text via
        cut and paste/string
        @assert: gpg key is not created
        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.error"]))
        self.assertIsNone(self.gpgkey.search(name))

    # Positive Delete

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_names_list())
    def test_positive_delete_1(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then delete it
        @assert: gpg key is deleted
        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_names_list())
    def test_positive_delete_2(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then delete it
        @assert: gpg key is deleted
        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))

    # Positive Update

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then update its name
        @assert: gpg key is updated
        """

        name = generate_string("alpha", 6)
        new_name = generate_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.update(name, new_name)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.success"]))

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_2(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file
        @assert: gpg key is updated
        """

        name = generate_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.update(name, new_key=new_key_path)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.success"]))

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_3(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its name
        @assert: gpg key is updated
        """

        name = generate_string("alpha", 6)
        new_name = generate_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.update(name, new_name)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.success"]))

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_4(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its gpg key text
        @assert: gpg key is updated
        """

        name = generate_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.update(name, new_key=new_key_path)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.success"]))

    # Negative Update

    @attr('ui', 'gpgkey', 'implemented')
    @data(*invalid_names_list())
    def test_negative_update_1(self, new_name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then fail to update its name
        @assert: gpg key is not updated
        """

        name = generate_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.update(name, new_name)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.error"]))
        self.assertIsNone(self.gpgkey.search(new_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*invalid_names_list())
    def test_negative_update_2(self, new_name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then fail to update its name
        @assert: gpg key is not updated
        """

        name = generate_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.update(name, new_name)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.error"]))
        self.assertIsNone(self.gpgkey.search(new_name))

    # Product association

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_1(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product
        @assert: gpg key is associated with product
        """

        prd_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.navigator.go_to_gpg_keys()
        self.assertEqual(prd_name,
                         self.gpgkey.assert_product_repo(name, product=True))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_2(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        @assert: gpg key is associated with product
                as well as with the repository
        """

        prd_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_3(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository
        @assert: gpg key is associated with product
                as well as with the repositories
        """

        prd_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name, url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @skip_if_bz_bug_open('1085035')
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_4(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method
        @assert: gpg key is associated with product as well as
        with the repositories
        @BZ: 1085035
        """

        prd_name = generate_string("alpha", 8)
        url = "http://omaciel.fedorapeople.org/"
        discovered_urls = ["fakerepo01/"]
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.repository.discover_repo(url, discovered_urls,
                                      product=prd_name, new_product=True,
                                      gpg_key=name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_5(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository
        @assert: gpg key is associated with repository but not with product
        """

        prd_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_6(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository
        @assert: gpg key is associated with the selected
        repository but not with product
        """

        prd_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name, url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @skip_if_bz_bug_open('1085924')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_7(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method
        @assert: gpg key is associated with product and all the repositories
        @status: manual
        @BZ: 1085924
        """

        pass

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_8(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product then
        update the key
        @assert: gpg key is associated with product before/after update
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.navigator.go_to_gpg_keys()
        self.assertEqual(prd_name, self.gpgkey.assert_product_repo
                         (name, product=True))
        self.gpgkey.update(name, new_name)
        self.assertEqual(prd_name, self.gpgkey.assert_product_repo
                         (new_name, product=True))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_9(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then update the key
        @assert: gpg key is associated with product
        and repository before/after update
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_10(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then update the key
        @assert: gpg key is associated with product as well as
        with repositories before/after update
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name, url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @skip_if_bz_bug_open('1085035')
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_11(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then update the key
        @assert: gpg key is associated with product as well as repository
        before/after update
        @BZ: 1085035
        """

        new_name = generate_string("alpha", 8)
        prd_name = generate_string("alpha", 8)
        url = "http://omaciel.fedorapeople.org/"
        discovered_urls = ["fakerepo01/"]
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.repository.discover_repo(url, discovered_urls,
                                      product=prd_name, new_product=True,
                                      gpg_key=name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_12(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then update the key
        @assert: gpg key is associated with the repository
        before/after update but not with product
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_13(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then update the key
        @assert: gpg key is associated with single repository
        before/after update but not with product
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name, url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @skip_if_bz_bug_open('1085924')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_14(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method then update the key
        @assert: gpg key is associated with product and all repositories
        before/after update
        @status: manual
        @BZ: 1085924
        """

        pass

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_15(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product
        then delete it
        @assert: gpg key is associated with product during creation but removed
        from product after deletion
        """

        prd_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product(name, prd_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_16(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then delete it
        @assert: gpg key is associated with product as well as with
        the repository during creation but removed from product
        after deletion
        """

        prd_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product(name, prd_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_17(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then delete it
        @assert: gpg key is associated with product as well as with
        the repositories during creation but removed from product
        after deletion
        """

        prd_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name, url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product(name, prd_name))

    @skip_if_bz_bug_open('1085035')
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_18(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then delete it
        @assert: gpg key is associated with product as well as with
        the repositories during creation but removed from
        product after deletion
        @BZ: 1085035
        """

        prd_name = generate_string("alpha", 8)
        url = "http://omaciel.fedorapeople.org/"
        discovered_urls = ["fakerepo01/"]
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.repository.discover_repo(url, discovered_urls,
                                      product=prd_name, new_product=True,
                                      gpg_key=name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product(name, prd_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_19(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then delete the key
        @assert: gpg key is associated with single repository but
        not with product during creation, and removed from
        repository after deletion
        """

        prd_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product
                          (name, prd_name, repo_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_20(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then delete the key
        @assert: gpg key is associated with single repository but not
        with product during creation but removed from
        repository after deletion
        """

        prd_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, upload_key=True, key_path=key_path)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name, url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product
                          (name, prd_name, repo_name1))

    @skip_if_bz_bug_open('1085924')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_21(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method then delete the key
        @assert: gpg key is associated with product and all repositories
        during creation but removed from product and all repositories after
        deletion
        @status: manual
        @BZ: 1085924
        """

        pass

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_22(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos)
        custom product
        @assert: gpg key is associated with product
        """

        prd_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_23(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository
        @assert: gpg key is associated with product as well as
        with the repository
        """

        prd_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_24(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository
        @assert: gpg key is associated with product as well as with
        the repositories
        """

        prd_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name,
                               url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @skip_if_bz_bug_open('1085035')
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_25(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via text via
        cut and paste/string then associate it with custom product using
        Repo discovery method
        @assert: gpg key is associated with product as well as with
        the repositories
        @BZ: 1085035
        """

        prd_name = generate_string("alpha", 8)
        url = "http://omaciel.fedorapeople.org/"
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.repository.discover_repo(url, discovered_urls,
                                      product=prd_name, new_product=True,
                                      gpg_key=name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_26(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository
        @assert: gpg key is associated with the repository but not with
        the product
        """

        prd_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_27(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository
        @assert: gpg key is associated with one of the repositories but
        not with the product
        """

        prd_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name,
                               url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))

    @skip_if_bz_bug_open('1085924')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_28(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repos from custom product
        using Repo discovery method
        @assert: gpg key is associated with product and all the repositories
        @status: manual
        @BZ: 1085924
        """

        pass

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_29(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos)
        custom product then update the key
        @assert: gpg key is associated with product before/after update
        """

        new_name = generate_string("alpha", 8)
        prd_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.gpgkey.update(name, new_name)
        self.assertEqual(prd_name, self.gpgkey.assert_product_repo
                         (new_name, product=True))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_30(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository then update the key
        @assert: gpg key is associated with product as well as with
        reposiotry before/after update
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_31(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository then update the key
        @assert: gpg key is associated with product as well as with
        reposiories before/after update
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name,
                               url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @skip_if_bz_bug_open('1085035')
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_32(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product using
        Repo discovery method then update the key
        @assert: gpg key is associated with product as well as with
        repository before/after update
        @BZ: 1085035
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        url = "http://omaciel.fedorapeople.org/"
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.repository.discover_repo(url, discovered_urls,
                                      product=prd_name, new_product=True,
                                      gpg_key=name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_33(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository then update the key
        @assert: gpg key is associated with repository
        before/after update but not with product.
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_34(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository then update the key
        @assert: gpg key is associated with single repository
        before/after update but not with product
        """

        prd_name = generate_string("alpha", 8)
        new_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name,
                               url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.update(name, new_name)
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (new_name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (new_name, product=False))

    @skip_if_bz_bug_open('1085924')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_35(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repos from custom product
        using Repo discovery method then update the key
        @assert: gpg key is associated with product and all repositories
        before/after update
        @status: manual
        @BZ: 1085924
        """

        pass

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_36(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos) custom
        product then delete it
        @assert: gpg key is associated with product during creation but
        removed from product after deletion
        """

        prd_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product(name, prd_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_37(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository then delete it
        @assert: gpg key is associated with product as well as with the
        repository during creation but removed from product after deletion
        """

        prd_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product(name, prd_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_38(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository then delete it
        @assert: gpg key is associated with product as well as with
        repositories during creation but removed from product after deletion
        """

        prd_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name, gpg_key=name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name,
                               url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product(name, prd_name))

    @skip_if_bz_bug_open('1085035')
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_39(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product using
        Repo discovery method then delete it
        @assert: gpg key is associated with product as well as with
        the repositories during creation but removed from product
        after deletion
        @BZ: 1085035
        """

        prd_name = generate_string("alpha", 8)
        url = "http://omaciel.fedorapeople.org/"
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.repository.discover_repo(url, discovered_urls,
                                      product=prd_name, new_product=True,
                                      gpg_key=name)
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product(name, prd_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_40(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository then delete the key
        @assert: gpg key is associated with single repository
        during creation but removed from repository after deletion
        """

        prd_name = generate_string("alpha", 8)
        repo_name = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product
                          (name, prd_name, repo_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_41(self, name):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository then delete the key
        @assert: gpg key is associated with single repository
        during creation but removed from repository after deletion
        """

        prd_name = generate_string("alpha", 8)
        repo_name1 = generate_string("alpha", 8)
        repo_name2 = generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name1, product=prd_name,
                               gpg_key=name, url=REPO_URL)
        self.assertIsNotNone(self.repository.search(repo_name1))
        self.repository.create(repo_name2, product=prd_name,
                               url=REPO2_URL)
        self.assertIsNotNone(self.repository.search(repo_name2))
        self.navigator.go_to_gpg_keys()
        self.assertIsNone(self.gpgkey.assert_product_repo
                          (name, product=True))
        self.assertIsNotNone(self.gpgkey.assert_product_repo
                             (name, product=False))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))
        self.assertIsNone(self.gpgkey.assert_key_from_product
                          (name, prd_name, repo_name1))

    @skip_if_bz_bug_open('1085924')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_42(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repos from custom product
        using Repo discovery method then delete the key
        @assert: gpg key is associated with product and all repositories
        during creation but removed from product and all repositories
        after deletion
        @status: manual
        @BZ: 1085924
        """

        pass

    # Content

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_consume_content_1(self):
        """
        @feature: GPG Keys
        @test: Hosts can install packages using gpg key associated with
        single custom repository
        @assert: host can install package from custom repository
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_consume_content_2(self):
        """
        @feature: GPG Keys
        @test: Hosts can install packages using gpg key associated with
        multiple custom repositories
        @assert: host can install package from custom repositories
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_consume_content_3(self):
        """
        @feature: GPG Keys
        @test: Hosts can install packages using different gpg keys associated
        with multiple custom repositories
        @assert: host can install package from custom repositories
        @status: manual
        """

        pass

    # Miscelaneous

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_list_key_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key and list it
        @assert: gpg key is displayed/listed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_search_key_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key and search/find it
        @assert: gpg key can be found
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_info_key_1(self):
        """
        @feature: GPG Keys
        @test: Create single gpg key and get its info
        @assert: specific information for gpg key matches the creation values
        @status: manual
        """

        pass
