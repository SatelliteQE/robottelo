# -*- encoding: utf-8 -*-
"""Test class for Users CLI

When testing email validation [1] and [2] should be taken into consideration.

[1] http://tools.ietf.org/html/rfc3696#section-3
[2] https://github.com/theforeman/foreman/pull/1776

"""

from ddt import ddt
from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cli.factory import (
    CLIFactoryError,
    make_location,
    make_org,
    make_role,
    make_user,
)
from robottelo.cli.user import User as UserObj
from robottelo.decorators import data, stubbed, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class User(CLITestCase):
    """Implements Users tests in CLI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name

    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size

    """

    def __assert_exists(self, user):
        """Checks if the object that passed as user parameter really exists
        in `hammer user list --search user['login']` and has values of:
        Login,Name,Email

        """
        result = UserObj().list({
            u'search': u'login="{0}"'.format(user['login']),
        })
        self.assertEqual(
            result.return_code, 0,
            'User search - exit code {0}'.format(result.return_code)
        )
        self.assertEqual(result.stdout[0]['name'], user['name'])
        self.assertEqual(result.stdout[0]['email'], user['email'])

    # Issues
    def test_bugzilla_1079649_1(self):
        """@Test: Delete a user by it's name

        @Feature: User

        @Steps:
        1. Create User
        2. Delete the User

        @Assert: User is deleted

        """

        try:
            user = make_user()
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj().delete({'login': user['login']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # make sure user was removed
        result = UserObj().info({'login': user['login']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    def test_bugzilla_1079649_2(self):
        """@Test: Delete a user by it's ID

        @Feature: User

        @Steps:
        1. Create User
        2. Delete the User

        @Assert: User is deleted

        @BZ: 1079649

        """

        try:
            user = make_user()
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj().delete({'id': user['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # make sure user was removed
        result = UserObj().info({'login': user['login']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    # CRUD

    @data(
        {'login': gen_string("latin1")},
        {'login': gen_string("utf8")},
        {'login': gen_string("alpha")},
        {'login': gen_string("alphanumeric")},
        {'login': gen_string("numeric")},
        {'login': gen_string("alphanumeric", 100)}
    )
    def test_positive_create_user_1(self, data):
        """@Test: Create User for all variations of Username

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Username variation in [1] using
        valid First Name, Surname, Email Address, Language, authorized by

        @Assert: User is created

        """
        try:
            args = make_user(data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(args)

    @data(
        {'firstname': gen_string("latin1")},
        {'firstname': gen_string("utf8")},
        {'firstname': gen_string("alpha")},
        {'firstname': gen_string("alphanumeric")},
        {'firstname': gen_string("numeric")},
        {'firstname': gen_string("alphanumeric", 50)}
    )
    def test_positive_create_user_2(self, data):
        """@Test: Create User for all variations of First Name

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid First Name variation in [1] using
        valid Username, Surname, Email Address, Language, authorized by

        @Assert: User is created

        """
        try:
            args = make_user(data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(args)

    @data(
        {'lastname': gen_string("latin1")},
        {'lastname': gen_string("utf8")},
        {'lastname': gen_string("alpha")},
        {'lastname': gen_string("alphanumeric")},
        {'lastname': gen_string("numeric")},
        {'lastname': gen_string("alphanumeric", 50)}
    )
    def test_positive_create_user_3(self, data):
        """@Test: Create User for all variations of Surname

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Surname variation in [1] using
        valid Username, First Name, Email Address, Language, authorized by

        @Assert: User is created

        """
        try:
            args = make_user(data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(args)

    @data(
        u'{0}@example.com'.format(gen_string('alpha')),
        u'{0}@example.com'.format(gen_string('alphanumeric')),
        u'{0}@example.com'.format(gen_string('numeric')),
        u'{0}@example.com'.format(gen_string('alphanumeric', 48)),
        u'{0}+{1}@example.com'.format(gen_alphanumeric(), gen_alphanumeric()),
        u'{0}.{1}@example.com'.format(gen_alphanumeric(), gen_alphanumeric()),
        u'"():;"@example.com',
        r'!#$%&*+-/=?^`{|}~@example.com',
    )
    def test_positive_create_user_4(self, email):
        """@Test: Create User for all variations of Email Address

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Email Address variation in [1] using
        valid Username, First Name, Surname, Language, authorized by

        @Assert: User is created

        """
        # The email must be escaped because some characters to not fail the
        # parsing of the generated shell command
        escaped_email = email.replace('"', r'\"').replace('`', r'\`')
        try:
            user = make_user({'mail': escaped_email})
        except CLIFactoryError as err:
            self.fail(err)
        self.assertEqual(user['email'], email)

    @data({'password': gen_string("latin1")},
          {'password': gen_string("utf8")},
          {'password': gen_string("alpha")},
          {'password': gen_string("alphanumeric")},
          {'password': gen_string("numeric")},
          {'password': gen_string("alphanumeric", 3000)})
    def test_positive_create_user_5(self, data):
        """@Test: Create User for all variations of Password

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Password variation in [1] using valid
        Username, First Name, Surname, Email Address, Language, authorized by

        @Assert: User is created

        """
        try:
            args = make_user(data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(args)

    def test_positive_create_user_6(self):
        """@Test: Create an Admin user

        @Feature: User - Positive Create

        @Assert: Admin User is created

        """
        try:
            args = make_user({'admin': '1'})
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(args)

    @skip_if_bug_open('bugzilla', 1213426)
    def test_create_user_with_default_location(self):
        """@Test: Check if user with default location can be created

        @Feature: User - Positive create

        @Assert: User is created and has new default location assigned

        @BZ: 1213426

        """
        try:
            location = make_location()
            user = make_user({
                'location-ids': location['id'],
                'default-location-id': location['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)
        self.assertIn(location['name'], user['locations'])
        self.assertEqual(location['name'], user['default-location'])

    @skip_if_bug_open('bugzilla', 1213426)
    def test_create_user_with_defaut_org(self):
        """@Test: Check if user with default organization can be created

        @Feature: User - Positive create

        @Assert: User is created and has new default organization assigned

        @BZ: 1213426

        """
        try:
            org = make_org()
            user = make_user({
                'organization-ids': org['id'],
                'default-organization-id': org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)
        self.assertIn(org['name'], user['organizations'])
        self.assertEqual(org['name'], user['default-organization'])

    @stubbed()
    def test_positive_create_user_9(self):
        """@Test: Create User with one role

        @Feature: User - Positive Create

        @Steps:
        1. Create User with one role assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_10(self):
        """@Test: Create User with multiple roles

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple roles assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_11(self):
        """@Test: Create User and assign all available roles to it

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all available roles assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_12(self):
        """@Test: Create User with one owned host

        @Feature: User - Positive Create

        @Steps:
        1. Create User with one owned host assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_13(self):
        """@Test: Create User with mutiple owned hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple owned hosts assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_14(self):
        """@Test: Create User with all owned hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all owned hosts assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_15(self):
        """@Test: Create User with one Domain host

        @Feature: User - Positive Create

        @Steps:
        1. Create User with one Domain host assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_16(self):
        """@Test: Create User with mutiple Domain hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple Domain hosts assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_17(self):
        """@Test: Create User with all Domain hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all Domain hosts assigned to it

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_18(self):
        """@Test: Create User with one Compute Resource

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with one Compute Resource

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_19(self):
        """@Test: Create User with mutiple Compute Resources

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with multiple Compute Resources

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_20(self):
        """@Test: Create User with all Compute Resources

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with all Compute Resources

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_21(self):
        """@Test: Create User with one Host group

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with one Host group

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_22(self):
        """@Test: Create User with multiple Host groups

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with multiple Host groups

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_23(self):
        """@Test: Create User with all Host groups

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with all available Host groups

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_24(self):
        """@Test: Create User associated to one Org

        @Feature: User - Positive Create

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_25(self):
        """@Test: Create User associated to multiple Orgs

        @Feature: User - Positive Create

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_26(self):
        """@Test: Create User associated to all available Orgs

        @Feature: User - Positive Create

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_27(self):
        """@Test: Create User with a new Fact filter

        @Feature: User - Positive Create

        @Steps:
        1. Create User associating it to a new Fact filter

        @Assert: User is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_user_28(self):
        """@Test: Create User in supported ldap modes

        @Feature: User - Positive Create

        @Steps:
        1. Create User in all supported ldap modes - (Active Driectory,
        IPA, Posix)

        @Assert: User is created without specifying the password

        @Status: Manual

        """
        pass

    @data({'login': ''},
          {'login': 'space {0}'.format(gen_string('alpha'))},
          {'login': gen_string('alpha', 101)},
          {'login': gen_string('html')})
    def test_negative_create_user_1(self, opts):
        """@Test: Create User with invalid Username

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Usernames in [2]
        using valid First Name, Surname, Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        """
        options = {
            'login': opts['login'],
            'mail': "root@localhost",
            'password': gen_string("alpha"),
            'auth-source-id': 1
        }
        self.logger.debug(str(options))
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @data({'firstname': gen_string("alpha", 51)},
          {'firstname': gen_string("html")})
    def test_negative_create_user_2(self, opts):
        """@Test: Create User with invalid Firstname

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Firstname in [2]
        using valid Username, Surname, Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        """
        options = {
            'login': gen_string("alpha"),
            'firstname': opts['firstname'],
            'mail': "root@localhost",
            'password': gen_string("alpha"),
            'auth-source-id': 1
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @data({'lastname': gen_string("alpha", 51)},
          {'lastname': gen_string("html")})
    def test_negative_create_user_3(self, opts):
        """@Test: Create User with invalid Surname

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Surname in [2]
        using valid Username, First Name Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        """
        options = {
            'login': gen_string("alpha"),
            'lastname': opts['lastname'],
            'mail': "root@localhost",
            'password': gen_string("alpha"),
            'auth-source-id': 1
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @data(
        'foreman@',
        '@foreman',
        '@',
        'Abc.example.com',
        'A@b@c@example.com',
        'email@example..c',
        '{0}@example.com'.format(gen_string('alpha', 49)),  # total length 61
        '{0}@example.com'.format(gen_string('html')),
        's p a c e s@example.com',
        'dot..dot@example.com'
    )
    def test_negative_create_user_4(self, email):
        """@Test: Create User with invalid Email Address

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Email Address in [2]
        using valid Username, First Name, Surname, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        """
        options = {
            'login': gen_string("alpha"),
            'firstname': gen_string("alpha"),
            'lastname': gen_string("alpha"),
            'mail': email,
            'password': gen_string("alpha"),
            'auth-source-id': 1
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @skip_if_bug_open('bugzilla', 1204686)
    def test_bugzilla_1204686(self):
        """@Test: Create User with Empty Email Address

        @Feature: User - Negative Create

        @Steps:
        1. Create User with empty Email Address in [2]
        using valid Username, First Name, Surname, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        @BZ: 1204686

        """
        options = {
            'login': gen_string("alpha"),
            'firstname': gen_string("alpha"),
            'lastname': gen_string("alpha"),
            'mail': '',
            'password': gen_string("alpha"),
            'auth-source-id': 1
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertGreaterThan(len(result.stderr), 0)
        self.assertIn('Email address is invalid', result.stdout)

    def test_negative_create_user_5(self):
        """@Test: Create User with blank Authorized by

        @Feature: User - Negative Create

        @Steps:
        1. Create User with blank Authorized by
        using valid Username, First Name, Surname, Email Address, Language

        @Assert: User is not created. Appropriate error shown.

        """
        options = {
            'login': gen_string("alpha"),
            'mail': "root@localhost",
            'auth-source-id': ''
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    def test_negative_create_user_6(self):
        """@Test: Create User with blank Authorized by but values in

        @Feature: User - Negative Create Password and verify

        @Steps:
        1. Create User with blank Authorized by but having matching values in
        Password and verify fields and using valid Username, First Name,
        Surname, Email Address, Language

        @Assert: User is not created. Appropriate error shown.

        """
        options = {
            'login': gen_string("alpha"),
            'mail': "root@localhost",
            'password': gen_string("alpha"),
            'auth-source-id': ''
        }
        result = UserObj().create(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertTrue(result.stderr)

    @data(
        {'firstname': gen_string("latin1")},
        {'firstname': gen_string("utf8")},
        {'firstname': gen_string("alpha")},
        {'firstname': gen_string("alphanumeric")},
        {'firstname': gen_string("numeric")},
    )
    def test_positive_update_user_1(self, test_data):
        """@Test: Update Username in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update User name for all variations in [1]

        @Assert: User is updated

        """
        try:
            new_obj = make_user()
        except CLIFactoryError as err:
            self.fail(err)

        # Update the user name
        result = UserObj().update({
            'id': new_obj['id'],
            'firstname': test_data['firstname'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

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

    @data(
        {'login': gen_string("latin1")},
        {'login': gen_string("utf8")},
        {'login': gen_string("alpha")},
        {'login': gen_string("alphanumeric")},
        {'login': gen_string("numeric")},
        {'login': gen_string("alphanumeric", 100)}
    )
    def test_positive_update_user_2(self, test_data):
        """@Test: Update Login in User

        @Feature: User

        @Steps:
        1. Create User
        2. Update User login for all variations in [1]

        @Assert: User login is updated

        """
        try:
            new_obj = make_user()
        except CLIFactoryError as err:
            self.fail(err)

        # Update the user login
        result = UserObj().update({
            'id': new_obj['id'],
            'login': test_data['login'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch the user again
        result = UserObj().info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['login'],
            test_data['login'],
            "User login was not updated"
        )

    @data(
        {'lastname': gen_string("latin1")},
        {'lastname': gen_string("utf8")},
        {'lastname': gen_string("alpha")},
        {'lastname': gen_string("alphanumeric")},
        {'lastname': gen_string("numeric")},
    )
    def test_positive_update_user_3(self, test_data):
        """@Test: Update Surname in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Surname for all variations in [1]

        @Assert: User is updated

        """
        try:
            new_obj = make_user()
        except CLIFactoryError as err:
            self.fail(err)

        # Update the last name
        result = UserObj().update({
            'id': new_obj['id'],
            'lastname': test_data['lastname'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

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

    @data(
        gen_string("alpha"),
        gen_string("alphanumeric"),
        gen_string("numeric"),
        '{0}+{1}'.format(gen_alphanumeric(), gen_alphanumeric()),
        '{0}.{1}'.format(gen_alphanumeric(), gen_alphanumeric()),
        r"!#$%&*+-/=?^`{|}~",
    )
    def test_positive_update_user_4(self, test_data):
        """@Test: Update Email Address in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Email Address for all variations in [1]

        @Assert: User is updated

        """
        try:
            new_obj = make_user()
        except CLIFactoryError as err:
            self.fail(err)

        # Update the mail
        email = '{0}@example.com'.format(test_data)
        result = UserObj().update({
            'id': new_obj['id'],
            # escape ` to avoid bash syntax error
            'mail': email.replace('`', r'\`'),
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

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

    @stubbed()
    def test_positive_update_user_5(self):
        """@Test: Update Language in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update User with all different Language options

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_6(self):
        """@Test: Update Password/Verify fields in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Password/Verify fields

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_7(self):
        """@Test: Convert an user from an admin user to non-admin user

        @Feature: User - Positive Update

        @Steps:
        1. Create User with Administrator rights
        2. Update the User to remove Administrator rights

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_8(self):
        """@Test: Convert a user to an admin user

        @Feature: User - Positive Update

        @Steps:
        1. Create a regular (non-admin) user
        2. Update the User to add Administrator rights

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_9(self):
        """@Test: Update User with one role

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one role to the user

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_10(self):
        """@Test: Update User with multiple roles

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple roles to the user

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_11(self):
        """@Test: Update User with all roles

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all available roles to the user

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_12(self):
        """@Test: Update User with one owned host

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one host to the user

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_13(self):
        """@Test: Update User with multiple owned hosts

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple owned hosts to the user

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_14(self):
        """@Test: Update User with all owned hosts

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all available owned hosts to the user

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_15(self):
        """@Test: Update User with one Domain host

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one Domain host to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_16(self):
        """@Test: Update User with multiple Domain hosts

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple Domain hosts to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_17(self):
        """@Test: Update User with all Domain hosts

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all Domain hosts to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_18(self):
        """@Test: Update User with one Compute Resource

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one Compute Resource to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_19(self):
        """@Test: Update User with multiple Compute Resources

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple Compute Resources to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_20(self):
        """@Test: Update User with all Compute Resources

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all Compute Resources to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_21(self):
        """@Test: Update User with one Host group

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one Host group to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_22(self):
        """@Test: Update User with multiple Host groups

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple Host groups to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_23(self):
        """@Test: Update User with all Host groups

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all available Host groups to the User
        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_24(self):
        """@Test: Assign a User to an Org

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign an Org to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_25(self):
        """@Test: Assign a User to multiple Orgs

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple Orgs to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_26(self):
        """@Test: Assign a User to all available Orgs

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all available Orgs to the User

        @Assert: User is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_user_28(self):
        """@Test: Update User with a new Fact filter

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Create and assign a new Fact filter to the User

        @Assert: User is update

        @Status: Manual

        """
        pass

    @stubbed()
    def test_negative_update_user_1(self):
        """@Test: Update invalid Username in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Username for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.

        @Status: Manual

        """
        pass

    @data({'firstname': gen_string("alpha", 51)},
          {'firstname': gen_string("html")})
    def test_negative_update_user_2(self, opts):
        """@Test: Update invalid Firstname in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Firstname for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.

        """
        try:
            new_user = make_user()
        except CLIFactoryError as err:
            self.fail(err)
        result = UserObj().update({'login': new_user['login'],
                                   'firstname': opts['firstname']})
        self.assertTrue(result.stderr)
        self.assertNotEqual(result.return_code, 0)
        # check name have not changed
        updated_user = UserObj().exists(
            search=('login', new_user['login']))
        self.assertEqual(updated_user.stdout['name'], new_user['name'])

    @data({'lastname': gen_string("alpha", 51)},
          {'lastname': gen_string("html")})
    def test_negative_update_user_3(self, opts):
        """@Test: Update invalid Surname in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Surname for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.

        """
        try:
            new_user = make_user()
        except CLIFactoryError as err:
            self.fail(err)
        result = UserObj().update({'login': new_user['login'],
                                   'lastname': opts['lastname']})
        self.assertTrue(result.stderr)
        self.assertNotEqual(result.return_code, 0)
        # check name have not changed
        updated_user = UserObj().exists(
            search=('login', new_user['login']))
        self.assertEqual(updated_user.stdout['name'], new_user['name'])

    @data(
        'foreman@',
        '@foreman',
        '@',
        'Abc.example.com',
        'A@b@c@example.com',
        '{0}@example.com'.format(gen_string(
            'alpha', 49)),  # total length 61
        '',
        '{0}@example.com'.format(gen_string('html')),
        's p a c e s@example.com',
        'dot..dot@example.com'
    )
    def test_negative_update_user_4(self, mail):
        """@Test: Update invalid Email Address in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Email Address for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.

        """
        try:
            new_user = make_user()
        except CLIFactoryError as err:
            self.fail(err)
        result = UserObj().update({'login': new_user['login'], 'mail': mail})
        self.assertTrue(result.stderr)
        self.assertNotEqual(result.return_code, 0)
        # check name have not changed
        updated_user = UserObj().exists(
            search=('login', new_user['login']))
        self.assertEqual(updated_user.stdout['email'], new_user['email'])

    @data(
        {'login': gen_string("latin1")},
        {'login': gen_string("utf8")},
        {'login': gen_string("alpha")},
        {'login': gen_string("alphanumeric")},
        {'login': gen_string("numeric")},
        {'login': gen_string("alphanumeric")}
    )
    def test_positive_delete_user_1(self, test_data):
        """@Test: Delete a user

        @Feature: User - Positive Delete

        @Steps:
        1. Create User
        2. Delete the User

        @Assert: User is deleted

        """
        try:
            user = make_user(test_data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj().delete({'login': user['login']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # make sure user was removed
        result = UserObj().info({'login': user['login']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    @data(
        {'login': gen_string("latin1")},
        {'login': gen_string("utf8")},
        {'login': gen_string("alpha")},
        {'login': gen_string("alphanumeric")},
        {'login': gen_string("numeric")},
        {'login': gen_string("alphanumeric")}
    )
    def test_positive_delete_user_2(self, test_data):
        """@Test: Delete an admin user

        @Feature: User - Positive Delete

        @Steps:
        1. Create an admin user
        2. Delete the User

        @Assert: User is deleted

        """
        test_data.update({'admin': 'true'})
        try:
            user = make_user(test_data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj().delete({'login': user['login']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # make sure user was removed
        result = UserObj().info({'login': user['login']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    @data({'admin': 'true'},
          {'login': 'admin', 'password': 'changeme'})
    def test_negative_delete_user_1(self, opts):
        """@Test: Attempt to delete internal admin user

        @Feature: User - Negative Delete

        @Steps:
        1. Attempt to delete the last admin user

        @Assert: User is not deleted

        """
        login = opts.get('login')
        if login is None:
            try:
                login = make_user(opts)['login']
            except CLIFactoryError as err:
                self.fail(err)

        user = UserObj()
        user.katello_user = login
        user.katello_passwd = opts.get('password', gen_alphanumeric())
        result = user.delete({'login': 'admin'})
        self.assertTrue(result.stderr)
        self.assertNotEqual(result.return_code, 0)
        result = UserObj().exists(search=('login', 'admin'))
        self.assertTrue(result.stdout)

    @data(
        {'login': gen_string("alpha")},
        {'login': gen_string("alphanumeric")},
        {'login': gen_string("numeric")},
        {'login': gen_string("latin1")},
        {'login': gen_string("utf8")},
        {'login': gen_string("alphanumeric", 100)}
    )
    def test_list_user_1(self, test_data):
        """@Test: List User for all variations of Username

        @Feature: User - list

        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed

        """
        try:
            user = make_user(test_data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj.list({
            u'search': u'login = {0}'.format(test_data['login']),
        })
        self.assertEqual(len(result.stdout), 1)
        self.assertEqual(len(result.stderr), 0)
        # make sure user is in list result
        self.assertEqual({
            'name': user['name'],
            'login': user['login'],
            'id': user['id'],
            'email': user['email']}, result.stdout[0])

    @data(
        {'firstname': gen_string("latin1")},
        {'firstname': gen_string("utf8")},
        {'firstname': gen_string("alpha")},
        {'firstname': gen_string("alphanumeric")},
        {'firstname': gen_string("numeric")},
        {'firstname': gen_string("alphanumeric", 50)}
    )
    def test_list_user_2(self, test_data):
        """@Test: List User for all variations of Firstname

        @Feature: User - list

        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed

        """
        try:
            user = make_user(test_data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj.list({
            u'search': u'firstname = {0}'.format(test_data['firstname']),
        })
        self.assertEqual(len(result.stderr), 0)
        # make sure user is in list result
        self.assertTrue({
            'name': user['name'],
            'login': user['login'],
            'id': user['id'],
            'email': user['email']} in result.stdout)

    @data(
        {'lastname': gen_string("latin1")},
        {'lastname': gen_string("utf8")},
        {'lastname': gen_string("alpha")},
        {'lastname': gen_string("alphanumeric")},
        {'lastname': gen_string("numeric")},
        {'lastname': gen_string("alphanumeric", 50)}
    )
    def test_list_user_3(self, test_data):
        """@Test: List User for all variations of Surname

        @Feature: User - list

        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed

        """
        try:
            user = make_user(test_data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj.list({
            u'search': u'lastname = {0}'.format(test_data['lastname']),
        })
        self.assertEqual(len(result.stderr), 0)
        # make sure user is in list result
        self.assertTrue({
            'name': user['name'],
            'login': user['login'],
            'id': user['id'],
            'email': user['email']} in result.stdout)

    @data(
        {'mail': gen_string("alpha") + "@somemail.com"},
        {'mail': gen_string(
            "alphanumeric", 10) + "@somemail.com"},
        {'mail': gen_string("numeric") + "@somemail.com"},
        {'mail': gen_string(
            "alphanumeric", 50) + "@somem.com"}
    )
    def test_list_user_4(self, test_data):
        """@Test: List User for all variations of Email Address

        @Feature: User - list

        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. List User

        @Assert: User is listed

        """
        try:
            user = make_user(test_data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj.list({
            u'search': u'mail = {0}'.format(test_data['mail']),
        })
        self.assertEqual(len(result.stderr), 0)
        # make sure user is in list result
        self.assertTrue({
            'name': user['name'],
            'login': user['login'],
            'id': user['id'],
            'email': user['email']} in result.stdout)

    @skip_if_bug_open('bugzilla', 1204667)
    @data(
        {'mail': gen_string("latin1") + "@somemail.com"},
        {'mail': gen_string("utf8") + "@somemail.com"}
    )
    def test_bugzilla_1204667(self, test_data):
        """@Test: List User for utf-8,latin variations of Email Address

        @Feature: User - list

        @Steps:
        1. Create User with above Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. List User

        @Assert: User is listed

        @BZ: 1204667

        """
        try:
            user = make_user(test_data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj.list({
            u'search': u'mail = {0}'.format(test_data['mail']),
        })
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.return_code, 0)
        # make sure user is in list result
        self.assertTrue({
            'name': user['name'],
            'login': user['login'],
            'id': user['id'],
            'email': user['email']} in result.stdout)

    @stubbed()
    def test_search_user_1(self):
        """@Test: Search User for all variations of Username

        @Feature: User - search

        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """
        pass

    @stubbed()
    def test_search_user_2(self):
        """@Test: Search User for all variations of Firstname

        @Feature: User - search

        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """
        pass

    @stubbed()
    def test_search_user_3(self):
        """@Test: Search User for all variations of Surname

        @Feature: User - search

        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """
        pass

    @stubbed()
    def test_search_user_4(self):
        """@Test: Search User for all variations of Email Address

        @Feature: User - search

        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """
        pass

    @stubbed()
    def test_search_user_5(self):
        """@Test: Search User for all variations of Language

        @Feature: User - search

        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """
        pass

    @stubbed()
    def test_info_user_1(self):
        """@Test: Get User info for all variations of Username

        @Feature: User - info

        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """
        pass

    @stubbed()
    def test_info_user_2(self):
        """@Test: Search User for all variations of Firstname

        @Feature: User - search

        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """
        pass

    @stubbed()
    def test_info_user_3(self):
        """@Test: Search User for all variations of Surname

        @Feature: User - search

        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """
        pass

    @stubbed()
    def test_info_user_4(self):
        """@Test: Search User for all variations of Email Address

        @Feature: User - search

        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """
        pass

    @stubbed()
    def test_info_user_5(self):
        """@Test: Search User for all variations of Language

        @Feature: User - search

        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """
        pass

    @stubbed()
    def test_end_to_end_user_1(self):
        """@Test: Create User and perform different operations

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

    @stubbed()
    def test_end_to_end_user_2(self):
        """@Test: Create User with no Org assigned and attempt different

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

    def test_automation_bz_1110337(self):
        """@Test: Automation of BZ 1110337

        @Feature: User - info, list BZ

        @Assert: No undefined method exception

        """
        try:
            users = [make_user() for _ in range(4)]
        except CLIFactoryError as err:
            self.fail(err)

        # non-existing user info
        result = UserObj.info({'id': 0})
        self.assertNotEqual(result.return_code, 0)
        self.assertNotRegexpMatches(result.stderr, 'undefined method')

        # list users
        result = UserObj.list()
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        for user in users:
            self.assertNotEqual(str(result.stdout).find(user['login']), -1)

    @data(
        {'name': gen_string("latin1")},
        {'name': gen_string("utf8")},
        {'name': gen_string("alpha")},
        {'name': gen_string("alphanumeric")},
        {'name': gen_string("numeric")},
        {'name': gen_string("alphanumeric", 100)},
    )
    def test_user_add_role_1(self, data):
        """@Test: Add role to User for all variations of role names

        @Feature: User - Add role

        @Steps:
        1. Create role and add it to the user

        @Assert: Role is added to user

        """
        try:
            user = make_user()
            role = make_role(data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj.add_role({
            'login': user['login'],
            'role': role['name']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an error here")
        result = UserObj.info({'id': user['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an error here")
        self.assertIn(role['name'], result.stdout['roles'])

    @data(
        {'name': gen_string("latin1")},
        {'name': gen_string("utf8")},
        {'name': gen_string("alpha")},
        {'name': gen_string("alphanumeric")},
        {'name': gen_string("numeric")},
        {'name': gen_string("alphanumeric", 100)},
    )
    def test_user_remove_role_1(self, data):
        """@Test: Remove role to User for all variations of role names

        @Feature: User - Remove role

        @Steps:
        1. Create role and add it to the user . Try to remove the role

        @Assert: Role is removed

        """
        try:
            user = make_user()
            role = make_role(data)
        except CLIFactoryError as err:
            self.fail(err)
        self.__assert_exists(user)
        result = UserObj.add_role({
            'login': user['login'],
            'role': role['name']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an error here")
        result = UserObj.info({'id': user['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an error here")
        self.assertIn(role['name'], result.stdout['roles'])
        result = UserObj.remove_role({
            'login': user['login'],
            'role': role['name']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an error here")
        result = UserObj.info({'id': user['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an error here")
        self.assertNotIn(role['name'], result.stdout['roles'])
