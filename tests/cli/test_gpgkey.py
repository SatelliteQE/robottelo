# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for GPG Key CLI
"""

from ddt import data, ddt
from robottelo.cli.factory import make_gpg_key, make_org
from robottelo.cli.gpgkey import GPGKey
from robottelo.cli.org import Org
from robottelo.common import ssh
from robottelo.common.constants import NOT_IMPLEMENTED, VALID_GPG_KEY_FILE
from robottelo.common.decorators import redminebug
from robottelo.common.helpers import generate_name, generate_string
from tempfile import mkstemp
from tests.cli.basecli import BaseCLI


VALID_GPG_KEY_FILE_PATH = 'tests/data/%s' % VALID_GPG_KEY_FILE

POSITIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 10).encode("utf-8")},
    {'name': generate_string("utf8", 10).encode("utf-8")},
    {'name': generate_string("alpha", 10)},
    {'name': generate_string("alphanumeric", 10)},
    {'name': generate_string("numeric", 10)},
    {'name': generate_string("html", 10)},
)

NEGATIVE_CREATE_DATA = (
    {'name': ' '},
    {'name': generate_string('alpha', 300).encode('utf-8')},
    {'name': generate_string('numeric', 300)},
    {'name': generate_string('alphanumeric', 300)},
    {'name': generate_string('utf8', 300).encode('utf-8')},
    {'name': generate_string('latin1', 300).encode('utf-8')},
    {'name': generate_string('html', 300)},
)


@ddt
@redminebug('4262')
@redminebug('4263')
@redminebug('4271')
@redminebug('4272')
@redminebug('4480')
@redminebug('4486')
class TestGPGKey(BaseCLI):
    """Tests for GPG Keys via Hammer CLI"""

    search_key = 'name'

    def create_org(self):
        """Creates and asserts the creation of an organization"""
        label = generate_name(6)
        org = make_org({'label': label})
        result = Org().exists(('label', org['label']))
        self.assertTrue(result.return_code == 0,
                        "Failed to find the created organization")
        org.update(result.stdout)

        return org

    def create_gpg_key_file(self):
        """
        Creates a fake GPG Key file and returns its path or None if an error
        happens.
        """

        (file_handle, key_filename) = mkstemp(text=True)
        with open(key_filename, "w") as gpg_key_file:
            gpg_key_file.write(generate_name(minimum=20, maximum=50))
            return key_filename

        return None

    # Positive Create

    @data(*POSITIVE_CREATE_DATA)
    def test_positive_create_1(self, data):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file import
        using the default created organization
        @assert: gpg key is created
        """

        result = Org().list()
        self.assertGreater(len(result.stdout), 0, 'No organization found')
        org = result.stdout[0]

        # Setup data to pass to the factory
        data = data.copy()
        data['key'] = VALID_GPG_KEY_FILE_PATH
        data['organization-id'] = org['label']
        new_obj = make_gpg_key(data)

        # Can we find the new object?
        result = GPGKey().exists(
            org['label'],
            (self.search_key, new_obj[self.search_key])
        )

        self.assertTrue(result.return_code == 0, "Failed to create object")
        self.assertTrue(
            len(result.stderr) == 0, "There should not be an exception here")
        self.assertEqual(
            new_obj[self.search_key], result.stdout[self.search_key])

    @data(*POSITIVE_CREATE_DATA)
    def test_positive_create_2(self, data):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file import
        using the a new organization
        @assert: gpg key is created
        """

        org = self.create_org()

        # Setup data to pass to the factory
        data = data.copy()
        data['key'] = VALID_GPG_KEY_FILE_PATH
        data['organization-id'] = org['label']
        new_obj = make_gpg_key(data)

        # Can we find the new object?
        result = GPGKey().exists(
            org['label'],
            (self.search_key, new_obj[self.search_key])
        )

        self.assertTrue(result.return_code == 0, "Failed to create object")
        self.assertTrue(
            len(result.stderr) == 0, "There should not be an exception here")
        self.assertEqual(
            new_obj[self.search_key], result.stdout[self.search_key])

    # Negative Create

    @data(*POSITIVE_CREATE_DATA)
    def test_negative_create_1(self, data):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file import
        then try to create new one with same name
        @assert: gpg key is not created
        """

        org = self.create_org()

        # Setup data to pass to the factory
        data = data.copy()
        data['organization-id'] = org['label']
        new_obj = make_gpg_key(data)

        # Can we find the new object?
        result = GPGKey().exists(
            org['label'],
            (self.search_key, new_obj[self.search_key])
        )

        self.assertTrue(result.return_code == 0, "Failed to create object")
        self.assertTrue(
            len(result.stderr) == 0, "There should not be an exception here")
        self.assertEqual(
            new_obj[self.search_key], result.stdout[self.search_key])

        # Setup a new key file
        data['key'] = '/tmp/%s' % generate_name()
        gpg_key = self.create_gpg_key_file()
        self.assertIsNotNone(gpg_key, 'GPG Key file must be created')
        ssh.upload_file(local_file=gpg_key, remote_file=data['key'])

        # Try to create a gpg key with the same name
        new_obj = GPGKey().create(data)
        self.assertNotEqual(
            new_obj.return_code, 0, "Object should not be created")
        self.assertGreater(
            len(new_obj.stderr), 0, "Should have raised an exception")

    @data(*POSITIVE_CREATE_DATA)
    def test_negative_create_2(self, data):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and no gpg key
        @assert: gpg key is not created
        """

        org = self.create_org()

        # Setup data to pass to create
        data = data.copy()
        data['organization-id'] = org['label']

        # Try to create a new object passing @data to factory method
        new_obj = GPGKey().create(data)
        self.assertNotEqual(
            new_obj.return_code, 0, "Object should not be created")
        self.assertGreater(
            len(new_obj.stderr), 0, "Should have raised an exception")

    @data(*NEGATIVE_CREATE_DATA)
    def test_negative_create_3(self, data):
        """
        @feature: GPG Keys
        @test: Create gpg key with invalid name and valid gpg key via
        file import
        @assert: gpg key is not created
        """

        org = self.create_org()

        # Setup data to pass to create
        data = data.copy()
        data['key'] = '/tmp/%s' % generate_name()
        data['organization-id'] = org['label']

        ssh.upload_file(
            local_file=VALID_GPG_KEY_FILE_PATH, remote_file=data['key'])

        # Try to create a new object passing @data to factory method
        new_obj = GPGKey().create(data)
        self.assertNotEqual(
            new_obj.return_code, 0, "Object should not be created")
        self.assertGreater(
            len(new_obj.stderr), 0, "Should have raised an exception")

    # Positive Delete

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_positive_delete_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then delete it
        @assert: gpg key is deleted
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
    def test_positive_delete_2(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then delete it
        @assert: gpg key is deleted
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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

    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_positive_update_1(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then update its name
        @assert: gpg key is updated
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
    def test_positive_update_2(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file
        @assert: gpg key is updated
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
    def test_positive_update_3(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its name
        @assert: gpg key is updated
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
    def test_positive_update_4(self):
        """
        @feature: GPG Keys
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its gpg key text
        @assert: gpg key is updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

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
        gpg key is associated with product and one of the repositories
        @assert: gpg key is associated with the repository
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
