# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for GPG Key UI"""

import sys

if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from ddt import ddt
from fauxfactory import FauxFactory
from nose.plugins.attrib import attr
from robottelo import entities, orm
from robottelo.common.constants import (
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    NOT_IMPLEMENTED,
    REPO_DISCOVERY_URL,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import (
    get_data_file, read_data_file, valid_names_list, invalid_names_list,
    generate_strings_list)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_gpgkey
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class GPGKey(UITestCase):
    """Implements tests for GPG Keys via UI"""

    org_name = None
    org_id = None

    def setUp(self):
        super(GPGKey, self).setUp()

        # Make sure to use the Class' org_name instance
        if GPGKey.org_name is None:
            org_name = orm.StringField(str_type=('alphanumeric',),
                                       len=(5, 80)).get_value()
            org_attrs = entities.Organization(name=org_name).create()
            GPGKey.org_name = org_attrs['name']
            GPGKey.org_id = org_attrs['id']

    # Positive Create

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        via file import

        @feature: GPG Keys

        @assert: gpg key is created

        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string

        @feature: GPG Keys

        @assert: gpg key is created

        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))

    # Negative Create

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key via
        file import then try to create new one with same name

        @feature: GPG Keys

        @assert: gpg key is not created

        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.wait_until_element
                                 (common_locators["alert.error"]))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string import then try to create new one with same name

        @feature: GPG Keys

        @assert: gpg key is not created

        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_3(self, name):
        """@test: Create gpg key with valid name and no gpg key

        @feature: GPG Keys

        @assert: gpg key is not created

        """

        with Session(self.browser) as session:
            with self.assertRaises(Exception):
                make_gpgkey(session, org=GPGKey.org_name,
                            name=name)
            self.assertIsNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*invalid_names_list())
    def test_negative_create_4(self, name):
        """@test: Create gpg key with invalid name and valid gpg key via
        file import

        @feature: GPG Keys

        @assert: gpg key is not created

        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))
            self.assertIsNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    def test_negative_create_5(self):
        """@test: Create gpg key with blank name and valid gpg key via
        file import

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        name = " "
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["haserror"]))
            self.assertIsNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*invalid_names_list())
    def test_negative_create_6(self, name):
        """@test: Create gpg key with invalid name and valid gpg key text via
        cut and paste/string

        @feature: GPG Keys

        @assert: gpg key is not created

        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))
            self.assertIsNone(self.gpgkey.search(name))

    # Positive Delete

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_names_list())
    def test_positive_delete_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then delete it

        @feature: GPG Keys

        @assert: gpg key is deleted

        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*valid_names_list())
    def test_positive_delete_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then delete it

        @feature: GPG Keys

        @assert: gpg key is deleted

        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))

    # Positive Update

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_1(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then update its name

        @feature: GPG Keys

        @assert: gpg key is updated

        """

        name = FauxFactory.generate_string("alpha", 6)
        new_name = FauxFactory.generate_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.success"]))

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_2(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file

        @feature: GPG Keys

        @assert: gpg key is updated

        """

        name = FauxFactory.generate_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_key=new_key_path)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.success"]))

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_3(self):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its name

        @feature: GPG Keys

        @assert: gpg key is updated

        """

        name = FauxFactory.generate_string("alpha", 6)
        new_name = FauxFactory.generate_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.success"]))

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_4(self):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its gpg key text

        @feature: GPG Keys

        @assert: gpg key is updated

        """

        name = FauxFactory.generate_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_key=new_key_path)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.success"]))

    # Negative Update

    @attr('ui', 'gpgkey', 'implemented')
    @data(*invalid_names_list())
    def test_negative_update_1(self, new_name):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then fail to update its name

        @feature: GPG Keys

        @assert: gpg key is not updated

        """

        name = FauxFactory.generate_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))
            self.assertIsNone(self.gpgkey.search(new_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*invalid_names_list())
    def test_negative_update_2(self, new_name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then fail to update its name

        @feature: GPG Keys

        @assert: gpg key is not updated

        """

        name = FauxFactory.generate_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))
            self.assertIsNone(self.gpgkey.search(new_name))

    # Product association

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with empty (no repos) custom product

        @feature: GPG Keys

        @assert: gpg key is associated with product

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has one repository

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as
        with the repository

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        repository_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_3(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has more than one repository

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repositories

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        repository_1_name = FauxFactory.generate_string("alpha", 8)
        repository_2_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id']
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id']
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @skip_if_bug_open('bugzilla', 1085035)
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_4(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product using Repo discovery method

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repositories

        @BZ: 1085035

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        url = REPO_DISCOVERY_URL
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=GPGKey.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            session.nav.go_to_products()
            self.repository.discover_repo(url, discovered_urls,
                                          product=product_name,
                                          new_product=True,
                                          gpg_key=name)
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_5(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository

        @feature: GPG Keys

        @assert: gpg key is associated with the repository but not with
        the product

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        repository_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create()
        # Creates new repository with GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_6(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository

        @feature: GPG Keys

        @assert: gpg key is associated with one of the repositories but
        not with the product

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        repository_1_name = FauxFactory.generate_string("alpha", 8)
        repository_2_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create()
        # Creates new repository with GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is not associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @skip_if_bug_open('bugzilla', 1085924)
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
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repos from custom product using Repo discovery method

        @feature: GPG Keys

        @assert: gpg key is associated with product and all the repositories

        @status: manual

        @BZ: 1085924

        """

        pass

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_8(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it with empty (no repos) custom product then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product before/after update

        """
        name = FauxFactory.generate_string("alpha", 8)
        new_name = FauxFactory.generate_string("alpha", 8)
        product_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Update the Key name
            self.gpgkey.update(name, new_name)
            # Again assert that GPGKey is associated with product
            self.assertEqual(product_name, self.gpgkey.assert_product_repo
                             (new_name, product=True))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_9(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has one repository
        then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        reposiotry before/after update

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        new_name = FauxFactory.generate_string("alpha", 8)
        repository_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that before update GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that before update GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=True))
            # Assert that after update GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_10(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has more than one
        repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        reposiories before/after update

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        new_name = FauxFactory.generate_string("alpha", 8)
        repository_1_name = FauxFactory.generate_string("alpha", 8)
        repository_2_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that before update GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that before update GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=True))
            # Assert that after update GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @skip_if_bug_open('bugzilla', 1085035)
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_11(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product using Repo discovery
        method then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        repository before/after update

        @BZ: 1085035

        """

        prd_name = FauxFactory.generate_string("alpha", 8)
        new_name = FauxFactory.generate_string("alpha", 8)
        url = REPO_DISCOVERY_URL
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_products()
            # Perform repo discovery
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
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository
        then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with repository
        before/after update but not with product.

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        new_name = FauxFactory.generate_string("alpha", 8)
        repository_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create()
        # Creates new repository with GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (new_name, product=True))
            # Assert that after update GPGKey is still associated
            # with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_13(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with single repository
        before/after update but not with product

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        new_name = FauxFactory.generate_string("alpha", 8)
        repository_1_name = FauxFactory.generate_string("alpha", 8)
        repository_2_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create()
        # Creates new repository_1 with GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (new_name, product=True))
            # Assert that after update GPGKey is not associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @skip_if_bug_open('bugzilla', 1085924)
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
        """@test: Create gpg key with valid name and valid gpg key
        then associate it to repos from custom product
        using Repo discovery method then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product and all repositories
        before/after update

        @status: manual

        @BZ: 1085924

        """

        pass

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_15(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with empty (no repos) custom
        product then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product during creation but
        removed from product after deletion

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_16(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it with custom product that has one repository then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with the
        repository during creation but removed from product after deletion

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        repository_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_17(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has
        more than one repository then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        repositories during creation but removed from product after deletion

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        repository_1_name = FauxFactory.generate_string("alpha", 8)
        repository_2_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name))

    @skip_if_bug_open('bugzilla', 1085035)
    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_18(self, name):
        """@test: Create gpg key with valid name and valid gpg then associate
        it with custom product using Repo discovery method then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repositories during creation but removed from product
        after deletion

        @BZ: 1085035

        """

        prd_name = FauxFactory.generate_string("alpha", 8)
        url = REPO_DISCOVERY_URL
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_products()
            # Perform repo discovery
            self.repository.discover_repo(url, discovered_urls,
                                          product=prd_name, new_product=True,
                                          gpg_key=name)
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, prd_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_19(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository
        then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with single repository
        during creation but removed from repository after deletion

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        repository_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create()
        # Creates new repository with GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name, repository_name))

    @attr('ui', 'gpgkey', 'implemented')
    @data(*generate_strings_list())
    def test_key_associate_20(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with single repository but not
        with product during creation but removed from
        repository after deletion

        """

        product_name = FauxFactory.generate_string("alpha", 8)
        repository_1_name = FauxFactory.generate_string("alpha", 8)
        repository_2_name = FauxFactory.generate_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        # Creates New GPGKey
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create()
        # Creates new product without GPGKey association
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create()
        # Creates new repository_1 with GPGKey association
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create()
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
            # notice that we're not making this repo point to the GPG key
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(GPGKey.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert key shouldn't be associated with product or repository
            # after deletion
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name, repository_1_name))

    @skip_if_bug_open('bugzilla', 1085924)
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
        """  @test: Create gpg key with valid name and valid gpg key then
        associate it to repos from custom product using Repo discovery method
        then delete the key

        @feature: GPG Keys

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
        """@test: Hosts can install packages using gpg key associated with
        single custom repository

        @feature: GPG Keys

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
        """@test: Hosts can install packages using gpg key associated with
        multiple custom repositories

        @feature: GPG Keys

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
        """@test: Hosts can install packages using different gpg keys
        associated with multiple custom repositories

        @feature: GPG Keys

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
        """@test: Create gpg key and list it

        @feature: GPG Keys

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
        """@test: Create gpg key and search/find it

        @feature: GPG Keys

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
        """@test: Create single gpg key and get its info

        @feature: GPG Keys

        @assert: specific information for gpg key matches the creation values

        @status: manual

        """

        pass
