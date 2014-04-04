# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Users CLI
"""

from ddt import data
from ddt import ddt
from tests.foreman.cli.basecli import BaseCLI
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.cli.factory import make_user
from robottelo.common.helpers import generate_string
from robottelo.common.decorators import bzbug, redminebug
from robottelo.cli.user import User as UserObj
import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest


@ddt
class User(BaseCLI):
    """
    Implements Users tests in CLI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name
    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size
    """

    def __assert_exists(self, args):
        """
        Checks if the object that passed as args parameter really exists
        in `hammer user list --search args['login']` and has values of:
        Login,Name,Email
        """
        result = UserObj().list({'search': 'login=\"%s\"' % args['login']})
        self.assertTrue(result.return_code == 0,
                        "User search - exit code %d" %
                        result.return_code)
        self.assertTrue(result.stdout[0]['name'] ==
                        args['firstname'] + " " + args['lastname'],
                        "User search - check our value 'Name'")
        self.assertTrue(result.stdout[0]['email'] == args['mail'],
                        "User search - check our value 'Email'")

    # Issues

    @bzbug('1079649')
    def test_bugzilla_1079649_1(self):
        """
        @Test: Delete a user by it's name
        @Feature: User
        @Steps:
        1. Create User
        2. Delete the User
        @Assert: User is deleted
        @BZ: 1079649
        """

        user = make_user()
        self.__assert_exists(user)
        result = UserObj().delete({'login': user['login']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # make sure user was removed
        result = UserObj().info({'login': user['login']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    @bzbug('1079649')
    def test_bugzilla_1079649_2(self):
        """
        @Test: Delete a user by it's ID
        @Feature: User
        @Steps:
        1. Create User
        2. Delete the User
        @Assert: User is deleted
        @BZ: 1079649
        """

        user = make_user()
        self.__assert_exists(user)
        result = UserObj().delete({'id': user['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # make sure user was removed
        result = UserObj().info({'login': user['login']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    # CRUD

    @data({'login': generate_string("latin1", 10)},
          {'login': generate_string("utf8", 10)},
          {'login': generate_string("alpha", 10)},
          {'login': generate_string("alphanumeric", 10)},
          {'login': generate_string("numeric", 10)},
          {'login': generate_string("alphanumeric", 100)})
    def test_positive_create_user_1(self, data):
        """
        @Test: Create User for all variations of Username
        @Feature: User - Positive Create
        @Steps:
        1. Create User for all valid Username variation in [1] using
        valid First Name, Surname, Email Address, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    @data({'firstname': generate_string("latin1", 10)},
          {'firstname': generate_string("utf8", 10)},
          {'firstname': generate_string("alpha", 10)},
          {'firstname': generate_string("alphanumeric", 10)},
          {'firstname': generate_string("numeric", 10)},
          {'firstname': generate_string("alphanumeric", 50)})
    def test_positive_create_user_2(self, data):
        """
        @Test: Create User for all variations of First Name
        @Feature: User - Positive Create
        @Steps:
        1. Create User for all valid First Name variation in [1] using
        valid Username, Surname, Email Address, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    @data({'lastname': generate_string("latin1", 10)},
          {'lastname': generate_string("utf8", 10)},
          {'lastname': generate_string("alpha", 10)},
          {'lastname': generate_string("alphanumeric", 10)},
          {'lastname': generate_string("numeric", 10)},
          {'lastname': generate_string("alphanumeric", 50)})
    def test_positive_create_user_3(self, data):
        """
        @Test: Create User for all variations of Surname
        @Feature: User - Positive Create
        @Steps:
        1. Create User for all valid Surname variation in [1] using
        valid Username, First Name, Email Address, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    @data({'mail': generate_string("latin1", 10) +
           "@somemail.com"},
          {'mail': generate_string("utf8", 10) +
           "@somemail.com"},
          {'mail': generate_string("alpha", 10) + "@somemail.com"},
          {'mail': generate_string("alphanumeric", 10) + "@somemail.com"},
          {'mail': generate_string("numeric", 10) + "@somemail.com"},
          {'mail': generate_string("alphanumeric", 50) +
           "@somem.com"})  # max 60 chars
    def test_positive_create_user_4(self, data):
        """
        @Test: Create User for all variations of Email Address
        @Feature: User - Positive Create
        @Steps:
        1. Create User for all valid Email Address variation in [1] using
        valid Username, First Name, Surname, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    @data({'password': generate_string("latin1", 10)},
          {'password': generate_string("utf8", 10)},
          {'password': generate_string("alpha", 10)},
          {'password': generate_string("alphanumeric", 10)},
          {'password': generate_string("numeric", 10)},
          {'password': generate_string("alphanumeric", 3000)})
    def test_positive_create_user_5(self, data):
        """
        @Test: Create User for all variations of Password
        @Feature: User - Positive Create
        @Steps:
        1. Create User for all valid Password variation in [1] using valid
        Username, First Name, Surname, Email Address, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    def test_positive_create_user_6(self):
        """
        @Test: Create an Admin user
        @Feature: User - Positive Create
        @Assert: Admin User is created
        """
        args = make_user({'admin': '1'})
        self.__assert_exists(args)

    @unittest.skip(NOT_IMPLEMENTED)
    @redminebug('2922')
    def test_positive_create_user_9(self):
        """
        @Test: Create User with one role
        @Feature: User - Positive Create
        @Steps:
        1. Create User with one role assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @redminebug('2922')
    def test_positive_create_user_10(self):
        """
        @Test: Create User with multiple roles
        @Feature: User - Positive Create
        @Steps:
        1. Create User with multiple roles assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @redminebug('2922')
    def test_positive_create_user_11(self):
        """
        @Test: Create User and assign all available roles to it
        @Feature: User - Positive Create
        @Steps:
        1. Create User with all available roles assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_12(self):
        """
        @Test: Create User with one owned host
        @Feature: User - Positive Create
        @Steps:
        1. Create User with one owned host assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_13(self):
        """
        @Test: Create User with mutiple owned hosts
        @Feature: User - Positive Create
        @Steps:
        1. Create User with multiple owned hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_14(self):
        """
        @Test: Create User with all owned hosts
        @Feature: User - Positive Create
        @Steps:
        1. Create User with all owned hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_15(self):
        """
        @Test: Create User with one Domain host
        @Feature: User - Positive Create
        @Steps:
        1. Create User with one Domain host assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_16(self):
        """
        @Test: Create User with mutiple Domain hosts
        @Feature: User - Positive Create
        @Steps:
        1. Create User with multiple Domain hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_17(self):
        """
        @Test: Create User with all Domain hosts
        @Feature: User - Positive Create
        @Steps:
        1. Create User with all Domain hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_18(self):
        """
        @Test: Create User with one Compute Resource
        @Feature: User - Positive Create
        @Steps:
        1. Create User associated with one Compute Resource
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_19(self):
        """
        @Test: Create User with mutiple Compute Resources
        @Feature: User - Positive Create
        @Steps:
        1. Create User associated with multiple Compute Resources
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_20(self):
        """
        @Test: Create User with all Compute Resources
        @Feature: User - Positive Create
        @Steps:
        1. Create User associated with all Compute Resources
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_21(self):
        """
        @Test: Create User with one Host group
        @Feature: User - Positive Create
        @Steps:
        1. Create User associated with one Host group
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_22(self):
        """
        @Test: Create User with multiple Host groups
        @Feature: User - Positive Create
        @Steps:
        1. Create User associated with multiple Host groups
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_23(self):
        """
        @Test: Create User with all Host groups
        @Feature: User - Positive Create
        @Steps:
        1. Create User associated with all available Host groups
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_24(self):
        """
        @Test: Create User associated to one Org
        @Feature: User - Positive Create
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_25(self):
        """
        @Test: Create User associated to multiple Orgs
        @Feature: User - Positive Create
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_26(self):
        """
        @Test: Create User associated to all available Orgs
        @Feature: User - Positive Create
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_27(self):
        """
        @Test: Create User with a new Fact filter
        @Feature: User - Positive Create
        @Steps:
        1. Create User associating it to a new Fact filter
        @Assert: User is created
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_user_28(self):
        """
        @Test: Create User in supported ldap modes
        @Feature: User - Positive Create
        @Steps:
        1. Create User in all supported ldap modes - (Active Driectory,
        IPA, Posix)
        @Assert: User is created without specifying the password
        @Status: Manual
        """
        pass

    @data({'login': ''},
          {'login': "space %s" % generate_string("alpha", 10)},
          {'login': generate_string("alpha", 101)},
          {'login': generate_string("html", 10)})
    def test_negative_create_user_1(self, opts):
        """
        @Test: Create User with invalid Username
        @Feature: User - Negative Create
        @Steps:
        1. Create User for all invalid Usernames in [2]
        using valid First Name, Surname, Email Address, Language, authorized by
        @Assert: User is not created. Appropriate error shown.
        """
        options = {
            'login': opts['login'],
            'mail': "root@localhost",
            'password': generate_string("alpha", 10),
            'auth-source-id': 1
        }
        self.logger.debug(str(options))
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @data({'firstname': generate_string("alpha", 51)},
          {'firstname': generate_string("html", 10)})
    def test_negative_create_user_2(self, opts):
        """
        @Test: Create User with invalid Firstname
        @Feature: User - Negative Create
        @Steps:
        1. Create User for all invalid Firstname in [2]
        using valid Username, Surname, Email Address, Language, authorized by
        @Assert: User is not created. Appropriate error shown.
        """
        options = {
            'login': generate_string("alpha", 10),
            'firstname': opts['firstname'],
            'mail': "root@localhost",
            'password': generate_string("alpha", 10),
            'auth-source-id': 1
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @data({'lastname': generate_string("alpha", 51)},
          {'lastname': generate_string("html", 10)})
    def test_negative_create_user_3(self, opts):
        """
        @Test: Create User with invalid Surname
        @Feature: User - Negative Create
        @Steps:
        1. Create User for all invalid Surname in [2]
        using valid Username, First Name Email Address, Language, authorized by
        @Assert: User is not created. Appropriate error shown.
        """
        options = {
            'login': generate_string("alpha", 10),
            'lastname': opts['lastname'],
            'mail': "root@localhost",
            'password': generate_string("alpha", 10),
            'auth-source-id': 1
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @bzbug('1070730')
    @data('foreman@',
          '@foreman',
          '@',
          'Abc.example.com',
          'A@b@c@example.com',
          'email@brazil.b',
          '%s@example.com' % generate_string("alpha", 49),  # total length 61
          '',
          '%s@example.com' % generate_string("html", 10),
          's p a c e s@example.com',
          'dot..dot@example.com')
    def test_negative_create_user_4(self, email):
        """
        @Test: Create User with invalid Email Address
        @Feature: User - Negative Create
        @Steps:
        1. Create User for all invalid Email Address in [2]
        using valid Username, First Name, Surname, Language, authorized by
        @Assert: User is not created. Appropriate error shown.
        """
        options = {
            'login': generate_string("alpha", 10),
            'firstname': generate_string("alpha", 10),
            'lastname': generate_string("alpha", 10),
            'mail': email,
            'password': generate_string("alpha", 10),
            'auth-source-id': 1
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    def test_negative_create_user_5(self):
        """
        @Test: Create User with blank Authorized by
        @Feature: User - Negative Create
        @Steps:
        1. Create User with blank Authorized by
        using valid Username, First Name, Surname, Email Address, Language
        @Assert: User is not created. Appropriate error shown.
        """
        options = {
            'login': generate_string("alpha", 10),
            'mail': "root@localhost",
            'auth-source-id': ''
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    def test_negative_create_user_6(self):
        """
        @Test: Create User with blank Authorized by but values in
        @Feature: User - Negative Create
        Password and verify
        @Steps:
        1. Create User with blank Authorized by but having matching values in
        Password and verify fields and using valid Username, First Name,
        Surname, Email Address, Language
        @Assert: User is not created. Appropriate error shown.
        """
        options = {
            'login': generate_string("alpha", 10),
            'mail': "root@localhost",
            'password': generate_string("alpha", 10),
            'auth-source-id': ''
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @data({'firstname': generate_string("latin1", 10)},
          {'firstname': generate_string("utf8", 10)},
          {'firstname': generate_string("alpha", 10)},
          {'firstname': generate_string("alphanumeric", 10)},
          {'firstname': generate_string("numeric", 10)},)
    def test_positive_update_user_1(self, test_data):
        """
        @Test: Update Username in User
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Update User name for all variations in [1]
        @Assert: User is updated
        """

        new_obj = make_user()
        # Can we find the new object?
        result = UserObj().info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])

        # Update the user name
        result = UserObj().update({'id': new_obj['id'],
                                   'firstname': test_data['firstname']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            len(result.stderr), 0, "There should not be an error here")

        # Fetch the user again
        result = UserObj().info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        user_name = result.stdout['name'].split(' ')
        self.assertEqual(
            user_name[0],
            test_data['firstname'],
            "User first name was not updated"
        )

    @data({'lastname': generate_string("latin1", 10)},
          {'lastname': generate_string("utf8", 10)},
          {'lastname': generate_string("alpha", 10)},
          {'lastname': generate_string("alphanumeric", 10)},
          {'lastname': generate_string("numeric", 10)},)
    def test_positive_update_user_3(self, test_data):
        """
        @Test: Update Surname in User
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Update Surname for all variations in [1]
        @Assert: User is updated
        """

        new_obj = make_user()
        # Can we find the new object?
        result = UserObj().info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])

        # Update the last name
        result = UserObj().update({'id': new_obj['id'],
                                   'lastname': test_data['lastname']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            len(result.stderr), 0, "There should not be an error here")

        # Fetch the user again
        result = UserObj().info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        user_last_name = result.stdout['name'].split(' ')
        new_obj_user_last_name = new_obj['name'].split(' ')
        self.assertNotEqual(user_last_name[1], new_obj_user_last_name[1])
        self.assertEqual(
            user_last_name[1],
            test_data['lastname'],
            "User last name was not updated"
        )

    @data({'mail': generate_string("latin1", 10)},
          {'mail': generate_string("utf8", 10)},
          {'mail': generate_string("alpha", 10)},
          {'mail': generate_string("alphanumeric", 10)},
          {'mail': generate_string("numeric", 10)},)
    def test_positive_update_user_4(self, test_data):
        """
        @Test: Update Email Address in User
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Update Email Address for all variations in [1]
        @Assert: User is updated
        """

        new_obj = make_user()
        # Can we find the new object?
        result = UserObj().info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])
        self.assertEqual(result.stdout['email'], new_obj['email'])

        # Update the mail
        email = test_data['mail'] + "@example.com"
        result = UserObj().update({'id': new_obj['id'],
                                   'mail': email})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            len(result.stderr), 0, "There should not be an error here")

        # Fetch the user again
        result = UserObj().info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertNotEqual(result.stdout['email'], new_obj['email'])
        self.assertEqual(
            result.stdout['email'],
            email,
            "User Email was not updated"
        )

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_6(self):
        """
        @Test: Update Password/Verify fields in User
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Update Password/Verify fields
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_9(self):
        """
        @Test: Update User with one role
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign one role to the user
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_10(self):
        """
        @Test: Update User with multiple roles
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign multiple roles to the user
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_11(self):
        """
        @Test: Update User with all roles
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign all available roles to the user
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_12(self):
        """
        @Test: Update User with one owned host
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign one host to the user
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_13(self):
        """
        @Test: Update User with multiple owned hosts
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign multiple owned hosts to the user
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_14(self):
        """
        @Test: Update User with all owned hosts
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign all available owned hosts to the user
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_15(self):
        """
        @Test: Update User with one Domain host
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign one Domain host to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_16(self):
        """
        @Test: Update User with multiple Domain hosts
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign multiple Domain hosts to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_17(self):
        """
        @Test: Update User with all Domain hosts
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign all Domain hosts to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_18(self):
        """
        @Test: Update User with one Compute Resource
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign one Compute Resource to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_19(self):
        """
        @Test: Update User with multiple Compute Resources
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign multiple Compute Resources to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_20(self):
        """
        @Test: Update User with all Compute Resources
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign all Compute Resources to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_21(self):
        """
        @Test: Update User with one Host group
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign one Host group to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_22(self):
        """
        @Test: Update User with multiple Host groups
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign multiple Host groups to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_23(self):
        """
        @Test: Update User with all Host groups
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign all available Host groups to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_24(self):
        """
        @Test: Assign a User to an Org
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign an Org to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_25(self):
        """
        @Test: Assign a User to multiple Orgs
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign multiple Orgs to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_26(self):
        """
        @Test: Assign a User to all available Orgs
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Assign all available Orgs to the User
        @Assert: User is updated
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_update_user_28(self):
        """
        @Test: Update User with a new Fact filter
        @Feature: User - Positive Update
        @Steps:
        1. Create User
        2. Create and assign a new Fact filter to the User
        @Assert: User is update
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @bzbug('1061701')
    def test_negative_update_user_1(self):
        """
        @Test: Update invalid Username in an User
        @Feature: User - Negative Update
        @Steps:
        1. Create User
        2. Update Username for all variations in [2]
        @Assert: User is not updated.  Appropriate error shown.
        @Status: Manual
        """
        pass

    @data({'firstname': generate_string("alpha", 51)},
          {'firstname': generate_string("html", 10)})
    def test_negative_update_user_2(self, opts):
        """
        @Test: Update invalid Firstname in an User
        @Feature: User - Negative Update
        @Steps:
        1. Create User
        2. Update Firstname for all variations in [2]
        @Assert: User is not updated.  Appropriate error shown.
        """
        new_user = make_user()
        result = UserObj().update({'login': new_user['login'],
                                   'firstname': opts['firstname']})
        self.assertTrue(result.stderr)
        self.assertNotEqual(result.return_code, 0)
        # check name have not changed
        updated_user = UserObj().exists(('login', new_user['login']))
        self.assertEqual(updated_user.stdout['name'], "%s %s" %
                                                      (new_user['firstname'],
                                                       new_user['lastname']))

    @data({'lastname': generate_string("alpha", 51)},
          {'lastname': generate_string("html", 10)})
    def test_negative_update_user_3(self, opts):
        """
        @Test: Update invalid Surname in an User
        @Feature: User - Negative Update
        @Steps:
        1. Create User
        2. Update Surname for all variations in [2]
        @Assert: User is not updated.  Appropriate error shown.
        """
        new_user = make_user()
        result = UserObj().update({'login': new_user['login'],
                                   'lastname': opts['lastname']})
        self.assertTrue(result.stderr)
        self.assertNotEqual(result.return_code, 0)
        # check name have not changed
        updated_user = UserObj().exists(('login', new_user['login']))
        self.assertEqual(updated_user.stdout['name'], "%s %s" %
                                                      (new_user['firstname'],
                                                       new_user['lastname']))

    @bzbug('1070730')
    @data('foreman@',
          '@foreman',
          '@',
          'Abc.example.com',
          'A@b@c@example.com',
          'email@brazil.b',
          '%s@example.com' % generate_string("alpha", 49),  # total length 61
          '',
          '%s@example.com' % generate_string("html", 10),
          's p a c e s@example.com',
          'dot..dot@example.com')
    def test_negative_update_user_4(self, mail):
        """
        @Test: Update invalid Email Address in an User
        @Feature: User - Negative Update
        @Steps:
        1. Create User
        2. Update Email Address for all variations in [2]
        @Assert: User is not updated.  Appropriate error shown.
        """
        new_user = make_user()
        result = UserObj().update({'login': new_user['login'], 'mail': mail})
        self.assertTrue(result.stderr)
        self.assertNotEqual(result.return_code, 0)
        # check name have not changed
        updated_user = UserObj().exists(('login', new_user['login']))
        self.assertEqual(updated_user.stdout['email'], new_user['mail'])

    @bzbug('1079649')
    @data({'login': generate_string("latin1", 10)},
          {'login': generate_string("utf8", 10)},
          {'login': generate_string("alpha", 10)},
          {'login': generate_string("alphanumeric", 10)},
          {'login': generate_string("numeric", 10)},
          {'login': generate_string("alphanumeric", 10)})
    def test_positive_delete_user_1(self, login):
        """
        @Test: Delete a user
        @Feature: User - Positive Delete
        @Steps:
        1. Create User
        2. Delete the User
        @Assert: User is deleted
        @BZ: 1079649
        """
        user = make_user({'login': login})
        self.__assert_exists(user)
        result = UserObj().delete({'login': user['login']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # make sure user was removed
        result = UserObj().info({'login': user['login']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    @bzbug('1079649')
    @data({'login': generate_string("latin1", 10)},
          {'login': generate_string("utf8", 10)},
          {'login': generate_string("alpha", 10)},
          {'login': generate_string("alphanumeric", 10)},
          {'login': generate_string("numeric", 10)},
          {'login': generate_string("alphanumeric", 10)})
    def test_positive_delete_user_2(self, login):
        """
        @Test: Delete an admin user
        @Feature: User - Positive Delete
        @Steps:
        1. Create an admin user
        2. Delete the User
        @Assert: User is deleted
        """
        user = make_user({'admin': 'true', 'login': login})
        self.__assert_exists(user)
        result = UserObj().delete({'login': user['login']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # make sure user was removed
        result = UserObj().info({'login': user['login']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    @data(make_user({'admin': 'true'}),
          {'login': 'admin', 'password': 'changeme'})
    def test_negative_delete_user_1(self, opts):
        """
        @Test: Attempt to delete internal admin user
        @Feature: User - Negative Delete
        @Steps:
        1. Attempt to delete the last admin user
        @Assert: User is not deleted
        """
        user = UserObj()
        user.katello_user = opts['login']
        user.katello_passwd = opts['password']
        result = user.delete({'login': 'admin'})
        self.assertTrue(result.stderr)
        self.assertNotEqual(result.return_code, 0)
        result = UserObj().exists(('login', 'admin'))
        self.assertTrue(result.stdout)

    @unittest.skip(NOT_IMPLEMENTED)
    def test_list_user_1(self):
        """
        @Test: List User for all variations of Username
        @Feature: User - list
        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_list_user_2(self):
        """
        @Test: List User for all variations of Firstname
        @Feature: User - list
        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_list_user_3(self):
        """
        @Test: List User for all variations of Surname
        @Feature: User - list
        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_list_user_4(self):
        """
        @Test: List User for all variations of Email Address
        @Feature: User - list
        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_list_user_5(self):
        """
        @Test: List User for all variations of Language
        @Feature: User - list
        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_search_user_1(self):
        """
        @Test: Search User for all variations of Username
        @Feature: User - search
        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_search_user_2(self):
        """
        @Test: Search User for all variations of Firstname
        @Feature: User - search
        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_search_user_3(self):
        """
        @Test: Search User for all variations of Surname
        @Feature: User - search
        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_search_user_4(self):
        """
        @Test: Search User for all variations of Email Address
        @Feature: User - search
        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_search_user_5(self):
        """
        @Test: Search User for all variations of Language
        @Feature: User - search
        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_info_user_1(self):
        """
        @Test: Get User info for all variations of Username
        @Feature: User - info
        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_info_user_2(self):
        """
        @Test: Search User for all variations of Firstname
        @Feature: User - search
        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_info_user_3(self):
        """
        @Test: Search User for all variations of Surname
        @Feature: User - search
        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_info_user_4(self):
        """
        @Test: Search User for all variations of Email Address
        @Feature: User - search
        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_info_user_5(self):
        """
        @Test: Search User for all variations of Language
        @Feature: User - search
        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_end_to_end_user_1(self):
        """
        @Test: Create User and perform different operations
        @Feature: User - End to End
        @Steps:
        1. Create User
        2. Login with the new user
        3. Upload Subscriptions
        4. Provision Systems
        5. Add/Remove Users
        6. Add/Remove Orgs
        7. Delete the User
        @Assert: All actions passed
        @Status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_end_to_end_user_2(self):
        """
        @Test: Create User with no Org assigned and attempt different
        @Feature: User - End to End
        operations
        @Steps:
        1. Create User.  Do not assign any Org
        2. Login with the new user
        3. Attempt to Upload Subscriptions
        4. Attempt to Provision Systems
        5. Attempt to Add/Remove Users
        6. Attempt to Add/Remove Orgs
        @Assert: All actions failed since the User is not assigned to any Org
        @Status: Manual
        """
        pass
