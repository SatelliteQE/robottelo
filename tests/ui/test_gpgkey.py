# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for GPG Key UI
"""

from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.common.constants import (NOT_IMPLEMENTED, VALID_GPG_KEY_FILE,
                                        VALID_GPG_KEY_BETA_FILE)
from robottelo.common.helpers import (generate_name, get_data_file,
                                      read_data_file, valid_names_list)
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


@ddt
class GPGKey(BaseUI):
    """IMplements tests for GPG Keys via UI"""

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
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))

        #Negative Create

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
    """)
    def test_negative_create_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file import
        then try to create new one with same name
        @assert: gpg key is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key text is valid text from a valid gpg key file
    """)
    def test_negative_create_2(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string import then try to create new one with same name
        @assert: gpg key is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is always empty/not provided
""")
    def test_negative_create_3(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and no gpg key
        @assert: gpg key is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is blank
        name is alpha 300 characters long
        name is numeric 300 characters long
        name is alphanumeric 300 characters long
        name is utf-8 300 characters long
        name is latin1 300 characters long
        name is html 300 characters long
        gpg key file is valid always
        submitted name = already existing key name?
""")
    def test_negative_create_4(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with invalid name and valid gpg key via
        file import
        @assert: gpg key is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is blank
        name is alpha 300 characters long
        name is numeric 300 characters long
        name is alphanumeric 300 characters long
        name is utf-8 300 characters long
        name is latin1 300 characters long
        name is html 300 characters long
        gpg key text is valid text from gpg key file always
""")
    def test_negative_create_5(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with invalid name and valid gpg key text via
        cut and paste/string
        @assert: gpg key is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.delete(name, True)
        self.assertIsNone(self.gpgkey.search(name))

    # Negative Delete

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        delete using a negative gpg key ID
        delete using a random string as the gpg key ID
""")
    def test_negative_delete_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then fail to delete it
        @assert: gpg key is not deleted
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key text is valid text from a valid gpg key file
        delete using a negative gpg key ID
        delete using a random string as the gpg key ID
""")
    def test_negative_delete_2(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then fail to delete it
        @assert: gpg key is not deleted
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Positive Update

    @attr('ui', 'gpgkey', 'implemented')
    def test_positive_update_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then update its name
        @assert: gpg key is updated
        """

        name = generate_name(6)
        new_name = generate_name(6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
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

        name = generate_name(6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
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

        name = generate_name(6)
        new_name = generate_name(6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
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

        name = generate_name(6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_gpg_keys()
        self.gpgkey.create(name, key_content=key_content)
        self.assertIsNotNone(self.gpgkey.search(name))
        self.gpgkey.update(name, new_key=new_key_path)
        self.assertTrue(self.gpgkey.wait_until_element
                        (common_locators["alert.success"]))

    # Negative Update

    @data("""DATADRIVENGOESHERE
        update name is blank
        update name is alpha 300 characters long
        update name is numeric 300 characters long
        update name is alphanumeric 300 characters long
        update name is utf-8 300 characters long
        update name is latin1 300 characters long
        update name is html 300 characters long
        gpg key file is valid always
""")
    def test_negative_update_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then fail to update its name
        @assert: gpg key is not updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update name is blank
        update name is alpha 300 characters long
        update name is numeric 300 characters long
        update name is alphanumeric 300 characters long
        update name is utf-8 300 characters long
        update name is latin1 300 characters long
        update name is html 300 characters long
        gpg key text is valid text from a valid gpg key file
""")
    def test_negative_update_2(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then fail to update its name
        @assert: gpg key is not updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Product association

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """)
    def test_key_associate_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product
        @assert: gpg key is associated with product
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """)
    def test_key_associate_2(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        @assert: gpg key is associated with product but not the repository
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """)
    def test_key_associate_3(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository
        @assert: gpg key is associated with product but not the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """)
    def test_key_associate_4(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method
        @assert: gpg key is associated with product but not the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """)
    def test_key_associate_5(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository
        @assert: gpg key is associated with product and the repository
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """)
    def test_key_associate_6(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository
        @assert: gpg key is associated with product and one of the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_8(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product then
        update the key
        @assert: gpg key is associated with product before/after update
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_9(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then update the key
        @assert: gpg key is associated with product before/after update but
        not the repository
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_10(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then update the key
        @assert: gpg key is associated with product before/after update but
        not the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_11(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then update the key
        @assert: gpg key is associated with product before/after update but
        not the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_12(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then update the key
        @assert: gpg key is associated with product and repository
        before/after update
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_13(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then update the key
        @assert: gpg key is associated with product and single repository
        before/after update
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_15(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product
        then delete it
        @assert: gpg key is associated with product during creation but removed
        from product after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_16(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then delete it
        @assert: gpg key is associated with product but not the repository
        during creation but removed from product after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_17(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then delete it
        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_18(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then delete it
        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_19(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then delete the key
        @assert: gpg key is associated with product and single repository
        during creation but removed from product and repository after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_20(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then delete the key
        @assert: gpg key is associated with product and single repository
        during creation but removed from product and repository after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_22(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos)
        custom product
        @assert: gpg key is associated with product
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_23(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository
        @assert: gpg key is associated with product but not the repository
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_24(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository
        @assert: gpg key is associated with product but not the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_25(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via text via
        cut and paste/string then associate it with custom product using
        Repo discovery method
        @assert: gpg key is associated with product but not the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_26(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository
        @assert: gpg key is associated with product and the repository
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_27(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository
        @assert: gpg key is associated with product and one of the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_29(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos)
        custom product then update the key
        @assert: gpg key is associated with product before/after update
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_30(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository then update the key
        @assert: gpg key is associated with product before/after update
        but not the repository
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_31(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository then update the key
        @assert: gpg key is associated with product before/after update
        but not the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_32(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product using
        Repo discovery method then update the key
        @assert: gpg key is associated with product before/after update
        but not the repositories
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_33(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository then update the key
        @assert: gpg key is associated with product and repository
        before/after update
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_34(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository then update the key
        @assert: gpg key is associated with product and single repository
        before/after update
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_36(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos) custom
        product then delete it
        @assert: gpg key is associated with product during creation but
        removed from product after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_37(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository then delete it
        @assert: gpg key is associated with product but not the repository
        during creation but removed from product after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_38(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository then delete it
        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_39(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product using
        Repo discovery method then delete it
        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_40(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository then delete the key
        @assert: gpg key is associated with product and single repository
        during creation but removed from product and repository after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_41(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository then delete the key
        @assert: gpg key is associated with product and single repository
        during creation but removed from product and repository after deletion
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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
        """

        self.fail(NOT_IMPLEMENTED)

    # Content

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

        self.fail(NOT_IMPLEMENTED)

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

        self.fail(NOT_IMPLEMENTED)

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

        self.fail(NOT_IMPLEMENTED)

    #Miscelaneous

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

        self.fail(NOT_IMPLEMENTED)

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

        self.fail(NOT_IMPLEMENTED)

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

        self.fail(NOT_IMPLEMENTED)
