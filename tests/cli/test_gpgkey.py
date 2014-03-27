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

import unittest

VALID_GPG_KEY_FILE_PATH = 'tests/data/%s' % VALID_GPG_KEY_FILE


def positive_create_data():
    """Random data for positive creation"""

    return (
        {'name': generate_string("latin1", 10)},
        {'name': generate_string("utf8", 10)},
        {'name': generate_string("alpha", 10)},
        {'name': generate_string("alphanumeric", 10)},
        {'name': generate_string("numeric", 20)},
        {'name': generate_string("html", 10)},
    )


def negative_create_data():
    """Random data for negative creation"""

    return (
        {'name': ' '},
        {'name': generate_string('alpha', 300)},
        {'name': generate_string('numeric', 300)},
        {'name': generate_string('alphanumeric', 300)},
        {'name': generate_string('utf8', 300)},
        {'name': generate_string('latin1', 300)},
        {'name': generate_string('html', 300)},
    )


@ddt
class TestGPGKey(BaseCLI):
    """Tests for GPG Keys via Hammer CLI"""

    search_key = 'name'

    @classmethod
    def setUpClass(cls):
        """
        Create a shared organization for all tests to avoid generating hundreds
        of organizations
        """
        BaseCLI.setUpClass()
        cls.org = cls.create_org()

    @classmethod
    def create_org(cls):
        """Creates and returns an organization"""
        label = generate_name(6)
        org = make_org({'label': label})
        result = Org.exists(('id', org['id']))

        org.update(result.stdout)

        return org

    def create_gpg_key_file(self, content=None):
        """
        Creates a fake GPG Key file and returns its path or None if an error
        happens.
        """

        (file_handle, key_filename) = mkstemp(text=True)
        if not content:
            content = generate_name(minimum=20, maximum=50)
        with open(key_filename, "w") as gpg_key_file:
            gpg_key_file.write(content)
            return key_filename

        return None

    # Bug verification

    @redminebug('4271')
    def test_redmine_4271(self):
        """
        @Test: cvs output for gpg subcommand doesn\'t work
        @Feature: GPG Keys
        @Assert: cvs output for gpg info works
        @BZ: Redmine#4271
        """

        # GPG Key data
        data = {'name': generate_string("alpha", 10)}
        data['organization-id'] = self.org['label']

        # Setup a new key file
        data['key'] = VALID_GPG_KEY_FILE_PATH
        try:
            new_obj = make_gpg_key(data)
        except Exception, e:
            self.fail(e)

        # Can we find the new object?
        result = GPGKey().info(
            {'id': new_obj['id']}
        )

        self.assertEqual(result.return_code, 0,
                         "Failed to get object information")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        self.assertEqual(
            new_obj[self.search_key], result.stdout[self.search_key])

    @redminebug('4272')
    def test_redmine_4272(self):
        """
        @Test: gpg info should display key content
        @Feature: GPG Keys
        @Assert: gpg info should display key content
        @BZ: Redmine#4272
        """

        # GPG Key data
        data = {'name': generate_string("alpha", 10)}
        data['organization-id'] = self.org['label']

        # Setup a new key file
        content = generate_name()
        gpg_key = self.create_gpg_key_file(content=content)
        self.assertIsNotNone(gpg_key, 'GPG Key file must be created')
        data['key'] = gpg_key
        try:
            new_obj = make_gpg_key(data)
        except Exception, e:
            self.fail(e)

        # Can we find the new object?
        result = GPGKey().info(
            {'id': new_obj['id']}
        )

        self.assertEqual(result.return_code, 0,
                         "Failed to get object information")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        self.assertEqual(
            result.stdout['content'], content)

    @redminebug('4480')
    def test_redmine_4480(self):
        """
        @Test: Hammer fails to get a gpg info by name
        @Feature: GPG Keys
        @Assert: can get gpg key info by name
        @BZ: Redmine#4480
        """

        # GPG Key data
        data = {'name': generate_string("alpha", 10)}
        data['organization-id'] = self.org['label']

        # Setup a new key file
        data['key'] = VALID_GPG_KEY_FILE_PATH
        try:
            new_obj = make_gpg_key(data)
        except Exception, e:
            self.fail(e)

        # Can we find the new object?
        result = GPGKey().info(
            {'name': new_obj['name']}
        )

        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        self.assertEqual(
            new_obj[self.search_key], result.stdout[self.search_key])

    # Positive Create

    @data(*positive_create_data())
    def test_positive_create_1(self, data):
        """
        @test: Create gpg key with valid name and valid gpg key via file import
        using the default created organization
        @feature: GPG Keys
        @assert: gpg key is created
        """

        result = Org.list()
        self.assertGreater(len(result.stdout), 0, 'No organization found')
        org = result.stdout[0]

        # Setup data to pass to the factory
        data = data.copy()
        data['key'] = VALID_GPG_KEY_FILE_PATH
        data['organization-id'] = org['label']

        try:
            new_obj = make_gpg_key(data)
        except Exception, e:
            self.fail(e)

        # Can we find the new object?
        result = GPGKey().exists(
            org['label'],
            (self.search_key, new_obj[self.search_key])
        )

        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        self.assertEqual(
            new_obj[self.search_key], result.stdout[self.search_key])

    @data(*positive_create_data())
    def test_positive_create_2(self, data):
        """
        @test: Create gpg key with valid name and valid gpg key via file import
        using the a new organization
        @feature: GPG Keys
        @assert: gpg key is created
        """

        # Setup data to pass to the factory
        data = data.copy()
        data['key'] = VALID_GPG_KEY_FILE_PATH
        data['organization-id'] = self.org['label']
        try:
            new_obj = make_gpg_key(data)
        except Exception, e:
            self.fail(e)

        # Can we find the new object?
        result = GPGKey().exists(
            self.org['label'],
            (self.search_key, new_obj[self.search_key])
        )

        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        self.assertEqual(
            new_obj[self.search_key], result.stdout[self.search_key])

    # Negative Create

    @data(*positive_create_data())
    def test_negative_create_1(self, data):
        """
        @test: Create gpg key with valid name and valid gpg key via file import
        then try to create new one with same name
        @feature: GPG Keys
        @assert: gpg key is not created
        """

        # Setup data to pass to the factory
        data = data.copy()
        data['organization-id'] = self.org['label']
        try:
            new_obj = make_gpg_key(data)
        except Exception, e:
            self.fail(e)

        # Can we find the new object?
        result = GPGKey().exists(
            self.org['label'],
            (self.search_key, new_obj[self.search_key])
        )

        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
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

    @data(*positive_create_data())
    def test_negative_create_2(self, data):
        """
        @test: Create gpg key with valid name and no gpg key
        @feature: GPG Keys
        @assert: gpg key is not created
        """

        # Setup data to pass to create
        data = data.copy()
        data['organization-id'] = self.org['label']

        # Try to create a new object passing @data to factory method
        new_obj = GPGKey().create(data)
        self.assertNotEqual(
            new_obj.return_code, 0, "Object should not be created")
        self.assertGreater(
            len(new_obj.stderr), 0, "Should have raised an exception")

    @data(*negative_create_data())
    def test_negative_create_3(self, data):
        """
        @test: Create gpg key with invalid name and valid gpg key via
        file import
        @feature: GPG Keys
        @assert: gpg key is not created
        """

        # Setup data to pass to create
        data = data.copy()
        data['key'] = '/tmp/%s' % generate_name()
        data['organization-id'] = self.org['label']

        ssh.upload_file(
            local_file=VALID_GPG_KEY_FILE_PATH, remote_file=data['key'])

        # Try to create a new object passing @data to factory method
        new_obj = GPGKey().create(data)
        self.assertNotEqual(
            new_obj.return_code, 0, "Object should not be created")
        self.assertGreater(
            len(new_obj.stderr), 0, "Should have raised an exception")

    # Positive Delete

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
    """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_delete_1(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then delete it
        @feature: GPG Keys
        @assert: gpg key is deleted
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key text is valid text from a valid gpg key file
    """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_delete_2(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then delete it
        @feature: GPG Keys
        @assert: gpg key is deleted
        @status: manual
        """

        pass

    # Negative Delete

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        delete using a negative gpg key ID
        delete using a random string as the gpg key ID
    """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_negative_delete_1(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then fail to delete it
        @feature: GPG Keys
        @assert: gpg key is not deleted
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key text is valid text from a valid gpg key file
        delete using a negative gpg key ID
        delete using a random string as the gpg key ID
    """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_negative_delete_2(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then fail to delete it
        @feature: GPG Keys
        @assert: gpg key is not deleted
        @status: manual
        """

        pass

    # Positive Update

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
    """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_1(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then update its name
        @feature: GPG Keys
        @assert: gpg key is updated
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_2(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file
        @feature: GPG Keys
        @assert: gpg key is updated
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key text is valid text from a valid gpg key file
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_3(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its name
        @feature: GPG Keys
        @assert: gpg key is updated
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key text is valid text from a valid gpg key file
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_4(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its gpg key text
        @feature: GPG Keys
        @assert: gpg key is updated
        @status: manual
        """

        pass

    # Negative Update

    """DATADRIVENGOESHERE
        update name is blank
        update name is alpha 300 characters long
        update name is numeric 300 characters long
        update name is alphanumeric 300 characters long
        update name is utf-8 300 characters long
        update name is latin1 300 characters long
        update name is html 300 characters long
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_negative_update_1(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then fail to update its name
        @feature: GPG Keys
        @assert: gpg key is not updated
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        update name is blank
        update name is alpha 300 characters long
        update name is numeric 300 characters long
        update name is alphanumeric 300 characters long
        update name is utf-8 300 characters long
        update name is latin1 300 characters long
        update name is html 300 characters long
        gpg key text is valid text from a valid gpg key file
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_negative_update_2(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then fail to update its name
        @feature: GPG Keys
        @assert: gpg key is not updated
        @status: manual
        """

        pass

    # Product association

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_1(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product
        @feature: GPG Keys
        @assert: gpg key is associated with product
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_2(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repository
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_3(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_4(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_5(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository
        @feature: GPG Keys
        @assert: gpg key is associated with product and the repository
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
        """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_6(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository
        gpg key is associated with product and one of the repositories
        @feature: GPG Keys
        @assert: gpg key is associated with the repository
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_7(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method
        @feature: GPG Keys
        @assert: gpg key is associated with product and all the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_8(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product then
        update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product before/after update
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_9(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product before/after update but
        not the repository
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_10(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product before/after update but
        not the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_11(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product before/after update but
        not the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_12(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and repository
        before/after update
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_13(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and single repository
        before/after update
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_14(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and all repositories
        before/after update
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_15(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with empty (no repos) custom product
        then delete it
        @feature: GPG Keys
        @assert: gpg key is associated with product during creation but removed
        from product after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_16(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has one repository
        then delete it
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repository
        during creation but removed from product after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_17(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product that has more than one
        repository then delete it
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_18(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it with custom product using Repo discovery
        method then delete it
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_19(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        one repository then delete the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and single repository
        during creation but removed from product and repository after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_20(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repository from custom product that has
        more than one repository then delete the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and single repository
        during creation but removed from product and repository after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_21(self):
        """
        @test: Create gpg key with valid name and valid gpg key via file
        import then associate it to repos from custom product using Repo
        discovery method then delete the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and all repositories
        during creation but removed from product and all repositories after
        deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_22(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos)
        custom product
        @feature: GPG Keys
        @assert: gpg key is associated with product
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_23(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repository
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_24(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_25(self):
        """
        @test: Create gpg key with valid name and valid gpg key via text via
        cut and paste/string then associate it with custom product using
        Repo discovery method
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_26(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository
        @feature: GPG Keys
        @assert: gpg key is associated with product and the repository
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_27(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository
        @feature: GPG Keys
        @assert: gpg key is associated with product and one of the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_28(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repos from custom product
        using Repo discovery method
        @feature: GPG Keys
        @assert: gpg key is associated with product and all the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_29(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos)
        custom product then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product before/after update
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_30(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product before/after update
        but not the repository
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_31(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product before/after update
        but not the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_32(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product using
        Repo discovery method then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product before/after update
        but not the repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_33(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and repository
        before/after update
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_34(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and single repository
        before/after update
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_35(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repos from custom product
        using Repo discovery method then update the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and all repositories
        before/after update
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_36(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with empty (no repos) custom
        product then delete it
        @feature: GPG Keys
        @assert: gpg key is associated with product during creation but
        removed from product after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_37(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        one repository then delete it
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repository
        during creation but removed from product after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_38(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product that has
        more than one repository then delete it
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_39(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it with custom product using
        Repo discovery method then delete it
        @feature: GPG Keys
        @assert: gpg key is associated with product but not the repositories
        during creation but removed from product after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_40(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has one repository then delete the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and single repository
        during creation but removed from product and repository after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_41(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repository from custom
        product that has more than one repository then delete the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and single repository
        during creation but removed from product and repository after deletion
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_key_associate_42(self):
        """
        @test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then associate it to repos from custom product
        using Repo discovery method then delete the key
        @feature: GPG Keys
        @assert: gpg key is associated with product and all repositories
        during creation but removed from product and all repositories
        after deletion
        @status: manual
        """

        pass

    # Content

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_consume_content_1(self):
        """
        @test: Hosts can install packages using gpg key associated with
        single custom repository
        @feature: GPG Keys
        @assert: host can install package from custom repository
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_consume_content_2(self):
        """
        @test: Hosts can install packages using gpg key associated with
        multiple custom repositories
        @feature: GPG Keys
        @assert: host can install package from custom repositories
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_consume_content_3(self):
        """
        @test: Hosts can install packages using different gpg keys associated
        with multiple custom repositories
        @feature: GPG Keys
        @assert: host can install package from custom repositories
        @status: manual
        """

        pass

    # Miscelaneous

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_list_key_1(self):
        """
        @test: Create gpg key and list it
        @feature: GPG Keys
        @assert: gpg key is displayed/listed
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_search_key_1(self):
        """
        @test: Create gpg key and search/find it
        @feature: GPG Keys
        @assert: gpg key can be found
        @status: manual
        """

        pass

    """DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
"""
    @unittest.skip(NOT_IMPLEMENTED)
    def test_info_key_1(self):
        """
        @test: Create single gpg key and get its info
        @feature: GPG Keys
        @assert: specific information for gpg key matches the creation values
        @status: manual
        """

        pass
