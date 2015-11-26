# -*- encoding: utf-8 -*-
"""Test class for Users CLI

When testing email validation [1] and [2] should be taken into consideration.

[1] http://tools.ietf.org/html/rfc3696#section-3
[2] https://github.com/theforeman/foreman/pull/1776

"""

from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_location, make_org, make_role, make_user
from robottelo.cli.user import User as UserObj
from robottelo.datafactory import (
    invalid_emails_list,
    valid_emails_list,
    valid_usernames_list,
)
from robottelo.decorators import stubbed, skip_if_bug_open, tier1, tier2
from robottelo.test import CLITestCase


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
        result = UserObj.list({
            u'search': u'login="{0}"'.format(user['login']),
        })
        self.assertEqual(result[0]['name'], user['name'])
        self.assertEqual(result[0]['email'], user['email'])

    # Issues
    @tier1
    def test_bugzilla_1079649_1(self):
        """@Test: Delete a user by it's name

        @Feature: User

        @Steps:
        1. Create User
        2. Delete the User

        @Assert: User is deleted
        """
        user = make_user()
        self.__assert_exists(user)
        UserObj.delete({'login': user['login']})
        # make sure user was removed
        with self.assertRaises(CLIReturnCodeError):
            UserObj.info({'login': user['login']})

    @tier1
    def test_bugzilla_1079649_2(self):
        """@Test: Delete a user by it's ID

        @Feature: User

        @Steps:
        1. Create User
        2. Delete the User

        @Assert: User is deleted

        @BZ: 1079649
        """
        user = make_user()
        self.__assert_exists(user)
        UserObj.delete({'id': user['id']})
        # make sure user was removed
        with self.assertRaises(CLIReturnCodeError):
            UserObj.info({'login': user['login']})

    # CRUD
    @tier1
    def test_positive_create_user_1(self):
        """@Test: Create User for all variations of Username

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Username variation in [1] using
        valid First Name, Surname, Email Address, Language, authorized by

        @Assert: User is created
        """
        include_list = [gen_string("alphanumeric", 100)]
        for login in valid_usernames_list() + include_list:
            with self.subTest(login):
                user = make_user({'login': login})
                self.__assert_exists(user)

    @tier1
    def test_positive_create_user_2(self):
        """@Test: Create User for all variations of First Name

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid First Name variation in [1] using
        valid Username, Surname, Email Address, Language, authorized by

        @Assert: User is created
        """
        include_list = [gen_string("alphanumeric", 50)]
        for firstname in valid_usernames_list() + include_list:
            with self.subTest(firstname):
                user = make_user({'firstname': firstname})
                self.__assert_exists(user)

    @tier1
    def test_positive_create_user_3(self):
        """@Test: Create User for all variations of Surname

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Surname variation in [1] using
        valid Username, First Name, Email Address, Language, authorized by

        @Assert: User is created
        """
        include_list = [gen_string("alphanumeric", 50)]
        for lastname in valid_usernames_list() + include_list:
            with self.subTest(lastname):
                user = make_user({'lastname': lastname})
                self.__assert_exists(user)

    @tier1
    def test_positive_create_user_4(self):
        """@Test: Create User for all variations of Email Address

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Email Address variation in [1] using
        valid Username, First Name, Surname, Language, authorized by

        @Assert: User is created
        """
        for email in valid_emails_list():
            with self.subTest(email):
                # The email must be escaped because some characters to not fail
                # the parsing of the generated shell command
                escaped_email = email.replace('"', r'\"').replace('`', r'\`')
                user = make_user({'mail': escaped_email})
                self.assertEqual(user['email'], email)

    @tier1
    def test_positive_create_user_5(self):
        """@Test: Create User for all variations of Password

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Password variation in [1] using valid
        Username, First Name, Surname, Email Address, Language, authorized by

        @Assert: User is created
        """
        include_list = [gen_string("alphanumeric", 3000)]
        for password in valid_usernames_list() + include_list:
            with self.subTest(password):
                user = make_user({'password': password})
                self.__assert_exists(user)

    @tier1
    def test_positive_create_user_6(self):
        """@Test: Create an Admin user

        @Feature: User - Positive Create

        @Assert: Admin User is created
        """
        user = make_user({'admin': '1'})
        self.__assert_exists(user)

    @tier1
    def test_create_user_default_loc(self):
        """@Test: Check if user with default location can be created

        @Feature: User - Positive create

        @Assert: User is created and has new default location assigned
        """
        location = make_location()
        user = make_user({
            'default-location-id': location['id'],
            'location-ids': location['id'],
        })
        self.assertIn(location['name'], user['locations'])
        self.assertEqual(location['name'], user['default-location'])

    @tier1
    def test_create_user_defaut_org(self):
        """@Test: Check if user with default organization can be created

        @Feature: User - Positive create

        @Assert: User is created and has new default organization assigned
        """
        org = make_org()
        user = make_user({
            'default-organization-id': org['id'],
            'organization-ids': org['id'],
        })
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

    @stubbed()
    def test_positive_create_user_10(self):
        """@Test: Create User with multiple roles

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple roles assigned to it

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_11(self):
        """@Test: Create User and assign all available roles to it

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all available roles assigned to it

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_12(self):
        """@Test: Create User with one owned host

        @Feature: User - Positive Create

        @Steps:
        1. Create User with one owned host assigned to it

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_13(self):
        """@Test: Create User with mutiple owned hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple owned hosts assigned to it

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_14(self):
        """@Test: Create User with all owned hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all owned hosts assigned to it

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_15(self):
        """@Test: Create User with one Domain host

        @Feature: User - Positive Create

        @Steps:
        1. Create User with one Domain host assigned to it

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_16(self):
        """@Test: Create User with mutiple Domain hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple Domain hosts assigned to it

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_17(self):
        """@Test: Create User with all Domain hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all Domain hosts assigned to it

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_18(self):
        """@Test: Create User with one Compute Resource

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with one Compute Resource

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_19(self):
        """@Test: Create User with mutiple Compute Resources

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with multiple Compute Resources

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_20(self):
        """@Test: Create User with all Compute Resources

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with all Compute Resources

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_21(self):
        """@Test: Create User with one Host group

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with one Host group

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_22(self):
        """@Test: Create User with multiple Host groups

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with multiple Host groups

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_23(self):
        """@Test: Create User with all Host groups

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with all available Host groups

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_24(self):
        """@Test: Create User associated to one Org

        @Feature: User - Positive Create

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_25(self):
        """@Test: Create User associated to multiple Orgs

        @Feature: User - Positive Create

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_26(self):
        """@Test: Create User associated to all available Orgs

        @Feature: User - Positive Create

        @Assert: User is created

        @Status: Manual
        """

    @stubbed()
    def test_positive_create_user_27(self):
        """@Test: Create User with a new Fact filter

        @Feature: User - Positive Create

        @Steps:
        1. Create User associating it to a new Fact filter

        @Assert: User is created

        @Status: Manual
        """

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

    @tier1
    def test_negative_create_user_1(self):
        """@Test: Create User with invalid Username

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Usernames in [2]
        using valid First Name, Surname, Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.
        """
        for invalid_name in ('',
                             'space {0}'.format(gen_string('alpha')),
                             gen_string('alpha', 101),
                             gen_string('html')):
            with self.subTest(invalid_name):
                options = {
                    'auth-source-id': 1,
                    'login': invalid_name,
                    'mail': 'root@localhost',
                    'password': gen_string('alpha'),
                }
                self.logger.debug(str(options))
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.create(options)

    @tier1
    def test_negative_create_user_2(self):
        """@Test: Create User with invalid Firstname

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Firstname in [2]
        using valid Username, Surname, Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.
        """
        for invalid_firstname in (gen_string("alpha", 51),
                                  gen_string("html")):
            with self.subTest(invalid_firstname):
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.create({
                        'auth-source-id': 1,
                        'login': gen_string('alpha'),
                        'firstname': invalid_firstname,
                        'mail': 'root@localhost',
                        'password': gen_string('alpha'),
                    })

    @tier1
    def test_negative_create_user_3(self):
        """@Test: Create User with invalid lastname

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid lastname in [2]
        using valid Username, First Name Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.
        """
        for invalid_lastname in (gen_string("alpha", 51),
                                 gen_string("html")):
            with self.subTest(invalid_lastname):
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.create({
                        'auth-source-id': 1,
                        'login': gen_string('alpha'),
                        'lastname': invalid_lastname,
                        'mail': 'root@localhost',
                        'password': gen_string('alpha'),
                    })

    @tier1
    def test_negative_create_user_4(self):
        """@Test: Create User with invalid Email Address

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Email Address in [2]
        using valid Username, First Name, Surname, Language, authorized by

        @Assert: User is not created. Appropriate error shown.
        """
        for email in invalid_emails_list():
            with self.subTest(email):
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.create({
                        'auth-source-id': 1,
                        'firstname': gen_string('alpha'),
                        'lastname': gen_string('alpha'),
                        'login': gen_string('alpha'),
                        'mail': email,
                        'password': gen_string('alpha'),
                    })

    @skip_if_bug_open('bugzilla', 1204686)
    @tier1
    def test_bugzilla_1204686(self):
        """@Test: Create User with Empty Email Address

        @Feature: User - Negative Create

        @Steps:
        1. Create User with empty Email Address in [2]
        using valid Username, First Name, Surname, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        @BZ: 1204686
        """
        with self.assertRaises(CLIReturnCodeError):
            UserObj.create({
                'auth-source-id': 1,
                'firstname': gen_string('alpha'),
                'lastname': gen_string('alpha'),
                'login': gen_string('alpha'),
                'mail': '',
                'password': gen_string('alpha'),
            })

    @tier1
    def test_negative_create_user_5(self):
        """@Test: Create User with blank Authorized by

        @Feature: User - Negative Create

        @Steps:
        1. Create User with blank Authorized by
        using valid Username, First Name, Surname, Email Address, Language

        @Assert: User is not created. Appropriate error shown.
        """
        with self.assertRaises(CLIReturnCodeError):
            UserObj.create({
                'auth-source-id': '',
                'login': gen_string('alpha'),
                'mail': 'root@localhost',
            })

    @tier1
    def test_negative_create_user_6(self):
        """@Test: Create User with blank Authorized by but values in

        @Feature: User - Negative Create Password and verify

        @Steps:
        1. Create User with blank Authorized by but having matching values in
        Password and verify fields and using valid Username, First Name,
        Surname, Email Address, Language

        @Assert: User is not created. Appropriate error shown.
        """
        with self.assertRaises(CLIReturnCodeError):
            UserObj.create({
                'auth-source-id': '',
                'login': gen_string('alpha'),
                'mail': 'root@localhost',
                'password': gen_string('alpha'),
            })

    @tier1
    def test_positive_update_user_1(self):
        """@Test: Update firstname in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update first name for all variations in [1]

        @Assert: User is updated
        """
        user = make_user()
        for new_firstname in valid_usernames_list():
            with self.subTest(new_firstname):
                UserObj.update({
                    'firstname': new_firstname,
                    'id': user['id'],
                })
                result = UserObj.info({'id': user['id']})
                user_name = result['name'].split(' ')
                self.assertEqual(user_name[0], new_firstname)

    @tier1
    def test_positive_update_user_2(self):
        """@Test: Update Login in User

        @Feature: User

        @Steps:
        1. Create User
        2. Update User login for all variations in [1]

        @Assert: User login is updated
        """
        user = make_user()
        include_list = [gen_string("alphanumeric", 100)]
        for new_login in valid_usernames_list() + include_list:
            with self.subTest(new_login):
                UserObj.update({
                    'id': user['id'],
                    'login': new_login,
                })
                user = UserObj.info({'id': user['id']})
                self.assertEqual(user['login'], new_login)

    @tier1
    def test_positive_update_user_3(self):
        """@Test: Update Lastname in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Lastname for all variations in [1]

        @Assert: User is updated
        """
        user = make_user()
        for new_lastname in valid_usernames_list():
            with self.subTest(new_lastname):
                UserObj.update({
                    'id': user['id'],
                    'lastname': new_lastname,
                })
                user = UserObj.info({'id': user['id']})
                last_name_after = user['name'].split(' ')
                self.assertEqual(last_name_after[1], new_lastname)

    @tier1
    def test_positive_update_user_4(self):
        """@Test: Update Email Address in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Email Address for all variations in [1]

        @Assert: User is updated
        """
        user = make_user()
        for data in (gen_string("alpha"),
                     gen_string("alphanumeric"),
                     gen_string("numeric"),
                     '{0}+{1}'.format(gen_alphanumeric(), gen_alphanumeric()),
                     '{0}.{1}'.format(gen_alphanumeric(), gen_alphanumeric()),
                     r"!#$%&*+-/=?^`{|}~"):
            with self.subTest(data):
                email = '{0}@example.com'.format(data)
                UserObj.update({
                    'id': user['id'],
                    # escape ` to avoid bash syntax error
                    'mail': email.replace('`', r'\`'),
                })
                result = UserObj.info({'id': user['id']})
                self.assertEqual(result['email'], email)

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

    @tier1
    def test_negative_update_user_2(self):
        """@Test: Update invalid Firstname in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Firstname for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.
        """
        new_user = make_user()
        for invalid_firstname in (gen_string("alpha", 51),
                                  gen_string("html")):
            with self.subTest(invalid_firstname):
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.update({
                        'firstname': invalid_firstname,
                        'login': new_user['login'],
                    })
                    updated_user = UserObj.exists(
                        search=('login', new_user['login']))
                    self.assertEqual(updated_user['name'], new_user['name'])

    @tier1
    def test_negative_update_user_3(self):
        """@Test: Update invalid lastname in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Surname for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.
        """
        new_user = make_user()
        for invalid_lastname in (gen_string("alpha", 51),
                                 gen_string("html")):
            with self.subTest(invalid_lastname):
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.update({
                        'lastname': invalid_lastname,
                        'login': new_user['login'],
                    })
                    updated_user = UserObj.exists(
                        search=('login', new_user['login']))
                    self.assertEqual(updated_user['name'], new_user['name'])

    @tier1
    def test_negative_update_user_4(self):
        """@Test: Update invalid Email Address in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Email Address for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.
        """
        new_user = make_user()
        for email in invalid_emails_list():
            with self.subTest(email):
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.update({
                        'login': new_user['login'],
                        'mail': email,
                    })
                    updated_user = UserObj.exists(
                        search=('login', new_user['login']))
                    self.assertEqual(updated_user['email'], new_user['email'])

    @tier1
    def test_positive_delete_user_1(self):
        """@Test: Delete a user

        @Feature: User - Positive Delete

        @Steps:
        1. Create User
        2. Delete the User

        @Assert: User is deleted
        """
        for login in valid_usernames_list():
            with self.subTest(login):
                user = make_user({"login": login})
                self.__assert_exists(user)
                UserObj.delete({'login': user['login']})
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.info({'login': user['login']})

    @tier1
    def test_positive_delete_user_2(self):
        """@Test: Delete an admin user

        @Feature: User - Positive Delete

        @Steps:
        1. Create an admin user
        2. Delete the User

        @Assert: User is deleted
        """
        for login in valid_usernames_list():
            with self.subTest(login):
                user = make_user({"login": login, "admin": 'true'})
                self.__assert_exists(user)
                UserObj.delete({'login': user['login']})
                with self.assertRaises(CLIReturnCodeError):
                    UserObj.info({'login': user['login']})

    @tier1
    def test_negative_delete_user_1(self):
        """@Test: Attempt to delete internal admin user

        @Feature: User - Negative Delete

        @Steps:
        1. Attempt to delete the last admin user

        @Assert: User is not deleted
        """
        for opts in ({'admin': 'true'},
                     {'login': 'admin', 'password': 'changeme'}):
            with self.subTest(opts):
                login = opts.get('login')
                if login is None:
                    login = make_user(opts)['login']
                user = UserObj
                user.katello_user = login
                user.katello_passwd = opts.get('password', gen_alphanumeric())
                with self.assertRaises(CLIReturnCodeError):
                    user.delete({'login': 'admin'})
                    result = UserObj.exists(search=('login', 'admin'))
                    self.assertTrue(result)

    @tier1
    def test_list_user_1(self):
        """@Test: List User for all variations of Username

        @Feature: User - list

        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed
        """
        include_list = [gen_string("alphanumeric", 100)]
        for login in valid_usernames_list() + include_list:
            with self.subTest(login):
                user = make_user({'login': login})
                self.__assert_exists(user)
                result = UserObj.list({
                    u'search': u'login = {0}'.format(login),
                })
                self.assertEqual(len(result), 1)
                # make sure user is in list result
                self.assertEqual({
                    'email': user['email'],
                    'id': user['id'],
                    'login': user['login'],
                    'name': user['name'],
                }, result[0])

    @tier1
    def test_list_user_2(self):
        """@Test: List User for all variations of Firstname

        @Feature: User - list

        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed
        """
        include_list = [gen_string("alphanumeric", 50)]
        for firstname in valid_usernames_list() + include_list:
            with self.subTest(firstname):
                user = make_user({'firstname': firstname})
                self.__assert_exists(user)
                result = UserObj.list({
                    u'search': u'firstname = {0}'.format(firstname),
                })
                # make sure user is in list result
                self.assertIn({
                    'email': user['email'],
                    'id': user['id'],
                    'login': user['login'],
                    'name': user['name'],
                }, result)

    @tier1
    def test_list_user_3(self):
        """@Test: List User for all variations of Surname

        @Feature: User - list

        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed
        """
        include_list = [gen_string("alphanumeric", 50)]
        for lastname in valid_usernames_list() + include_list:
            with self.subTest(lastname):
                user = make_user({'lastname': lastname})
                self.__assert_exists(user)
                result = UserObj.list({
                    u'search': u'lastname = {0}'.format(lastname),
                })
                # make sure user is in list result
                self.assertIn({
                    'email': user['email'],
                    'id': user['id'],
                    'login': user['login'],
                    'name': user['name'],
                }, result)

    @tier1
    def test_list_user_4(self):
        """@Test: List User for all variations of Email Address

        @Feature: User - list

        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. List User

        @Assert: User is listed
        """
        for mail in (gen_string("alpha") + "@somemail.com",
                     gen_string("alphanumeric", 10) + "@somemail.com",
                     gen_string("numeric") + "@somemail.com",
                     gen_string("alphanumeric", 50) + "@somem.com"):
            with self.subTest(mail):
                user = make_user({'mail': mail})
                self.__assert_exists(user)
                result = UserObj.list({
                    u'search': u'mail = {0}'.format(mail),
                })
                # make sure user is in list result
                self.assertIn({
                    'email': user['email'],
                    'id': user['id'],
                    'login': user['login'],
                    'name': user['name'],
                }, result)

    @skip_if_bug_open('bugzilla', 1204667)
    @tier1
    def test_bugzilla_1204667(self):
        """@Test: List User for utf-8,latin variations of Email Address

        @Feature: User - list

        @Steps:
        1. Create User with above Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. List User

        @Assert: User is listed

        @BZ: 1204667
        """
        for mail in (gen_string("latin1") + "@somemail.com",
                     gen_string("utf8") + "@somemail.com"):
            with self.subTest(mail):
                user = make_user({'mail': mail})
                self.__assert_exists(user)
                result = UserObj.list({
                    u'search': u'mail = {0}'.format(mail),
                })
                # make sure user is in list result
                self.assertIn({
                    'email': user['email'],
                    'id': user['id'],
                    'login': user['login'],
                    'name': user['name'],
                }, result)

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

    @tier1
    def test_automation_bz_1110337(self):
        """@Test: Automation of BZ 1110337

        @Feature: User - info, list BZ

        @Assert: No undefined method exception
        """
        users = [make_user() for _ in range(4)]
        # non-existing user info
        with self.assertRaises(CLIReturnCodeError) as exe:
            UserObj.info({'id': 0})
        self.assertNotRegexpMatches(exe.exception.stderr, 'undefined method')
        # list users
        result = UserObj.list()
        for user in users:
            self.assertNotEqual(str(result).find(user['login']), -1)

    @skip_if_bug_open('bugzilla', 1138553)
    @tier2
    def test_user_add_role_1(self):
        """@Test: Add role to User for all variations of role names

        @Feature: User - Add role

        @Steps:
        1. Create role and add it to the user

        @Assert: Role is added to user

        @BZ: 1138553
        """
        user = make_user()
        include_list = [gen_string("alphanumeric", 100)]
        for role_name in valid_usernames_list() + include_list:
            with self.subTest(role_name):
                make_role({'name': role_name})
                self.__assert_exists(user)
                UserObj.add_role({
                    'login': user['login'],
                    'role': role_name,
                })
                user = UserObj.info({'id': user['id']})
                self.assertIn(role_name, user['roles'])

    @skip_if_bug_open('bugzilla', 1138553)
    @tier2
    def test_user_remove_role_1(self):
        """@Test: Remove role to User for all variations of role names

        @Feature: User - Remove role

        @Steps:
        1. Create role and add it to the user . Try to remove the role

        @Assert: Role is removed

        @BZ: 1138553
        """
        user = make_user()
        include_list = [gen_string("alphanumeric", 100)]
        for role_name in valid_usernames_list() + include_list:
            with self.subTest(role_name):
                make_role({'name': role_name})
                self.__assert_exists(user)
                UserObj.add_role({
                    'login': user['login'],
                    'role': role_name,
                })
                user = UserObj.info({'id': user['id']})
                self.assertIn(role_name, user['roles'])
                UserObj.remove_role({
                    'login': user['login'],
                    'role': role_name,
                })
                user = UserObj.info({'id': user['id']})
                self.assertNotIn(role_name, user['roles'])
