# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Users CLI
"""

from ddt import data
from ddt import ddt
from tests.cli.basecli import BaseCLI
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.cli.factory import make_user
from robottelo.common.helpers import generate_string
from robottelo.common.decorators import redminebug
from robottelo.cli.user import User as UserObj


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

    @data({'login': generate_string("latin1", 10).encode("utf-8")},
          {'login': generate_string("utf8", 10).encode("utf-8")},
          {'login': generate_string("alpha", 10)},
          {'login': generate_string("alphanumeric", 10)},
          {'login': generate_string("numeric", 10)},
          {'login': generate_string("alphanumeric", 100)})
    def test_positive_create_user_1(self, data):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Username
        @Steps:
        1. Create User for all valid Username variation in [1] using
        valid First Name, Surname, Email Address, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    @data({'firstname': generate_string("latin1", 10).encode("utf-8")},
          {'firstname': generate_string("utf8", 10).encode("utf-8")},
          {'firstname': generate_string("alpha", 10)},
          {'firstname': generate_string("alphanumeric", 10)},
          {'firstname': generate_string("numeric", 10)},
          {'firstname': generate_string("alphanumeric", 50)})
    def test_positive_create_user_2(self, data):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of First Name
        @Steps:
        1. Create User for all valid First Name variation in [1] using
        valid Username, Surname, Email Address, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    @data({'lastname': generate_string("latin1", 10).encode("utf-8")},
          {'lastname': generate_string("utf8", 10).encode("utf-8")},
          {'lastname': generate_string("alpha", 10)},
          {'lastname': generate_string("alphanumeric", 10)},
          {'lastname': generate_string("numeric", 10)},
          {'lastname': generate_string("alphanumeric", 50)})
    def test_positive_create_user_3(self, data):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Surname
        @Steps:
        1. Create User for all valid Surname variation in [1] using
        valid Username, First Name, Email Address, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    @data({'mail': generate_string("latin1", 10).encode("utf-8") +
           "@somemail.com"},
          {'mail': generate_string("utf8", 10).encode("utf-8") +
           "@somemail.com"},
          {'mail': generate_string("alpha", 10) + "@somemail.com"},
          {'mail': generate_string("alphanumeric", 10) + "@somemail.com"},
          {'mail': generate_string("numeric", 10) + "@somemail.com"},
          {'mail': generate_string("alphanumeric", 50) +
           "@somem.com"})  # max 60 chars
    def test_positive_create_user_4(self, data):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Email Address
        @Steps:
        1. Create User for all valid Email Address variation in [1] using
        valid Username, First Name, Surname, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    @data({'password': generate_string("latin1", 10).encode("utf-8")},
          {'password': generate_string("utf8", 10).encode("utf-8")},
          {'password': generate_string("alpha", 10)},
          {'password': generate_string("alphanumeric", 10)},
          {'password': generate_string("numeric", 10)},
          {'password': generate_string("alphanumeric", 3000)})
    def test_positive_create_user_5(self, data):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Password
        @Steps:
        1. Create User for all valid Password variation in [1] using valid
        Username, First Name, Surname, Email Address, Language, authorized by
        @Assert: User is created
        """
        args = make_user(data)
        self.__assert_exists(args)

    def test_positive_create_user_6(self):
        """
        @Feature: User - Positive Create
        @Test: Create an Admin user
        @Assert: Admin User is created
        """
        args = make_user({'admin': '1'})
        self.__assert_exists(args)

    @redminebug('2922')
    def test_positive_create_user_9(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one role
        @Steps:
        1. Create User with one role assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @redminebug('2922')
    def test_positive_create_user_10(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with multiple roles
        @Steps:
        1. Create User with multiple roles assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @redminebug('2922')
    def test_positive_create_user_11(self):
        """
        @Feature: User - Positive Create
        @Test: Create User and assign all available roles to it
        @Steps:
        1. Create User with all available roles assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_12(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one owned host
        @Steps:
        1. Create User with one owned host assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_13(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with mutiple owned hosts
        @Steps:
        1. Create User with multiple owned hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_14(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with all owned hosts
        @Steps:
        1. Create User with all owned hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_15(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one Domain host
        @Steps:
        1. Create User with one Domain host assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_16(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with mutiple Domain hosts
        @Steps:
        1. Create User with multiple Domain hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_17(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with all Domain hosts
        @Steps:
        1. Create User with all Domain hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_18(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one Compute Resource
        @Steps:
        1. Create User associated with one Compute Resource
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_19(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with mutiple Compute Resources
        @Steps:
        1. Create User associated with multiple Compute Resources
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_20(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with all Compute Resources
        @Steps:
        1. Create User associated with all Compute Resources
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_21(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one Host group
        @Steps:
        1. Create User associated with one Host group
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_22(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with multiple Host groups
        @Steps:
        1. Create User associated with multiple Host groups
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_23(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with all Host groups
        @Steps:
        1. Create User associated with all available Host groups
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_24(self):
        """
        @Feature: User - Positive Create
        @Test: Create User associated to one Org
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_25(self):
        """
        @Feature: User - Positive Create
        @Test: Create User associated to multiple Orgs
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_26(self):
        """
        @Feature: User - Positive Create
        @Test: Create User associated to all available Orgs
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_27(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with a new Fact filter
        @Steps:
        1. Create User associating it to a new Fact filter
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_28(self):
        """
        @Feature: User - Positive Create
        @Test: Create User in supported ldap modes
        @Steps:
        1. Create User in all supported ldap modes - (Active Driectory,
        IPA, Posix)
        @Assert: User is created without specifying the password
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_user_1(self):
        """
        @Feature: User - Positive Create
        @Test: [UI ONLY] Attempt to enter all User creation details and Cancel
        @Steps:
        1. Enter all valid Username, First Name, Surname, Email Address,
        Language, authorized by.
        2. Click Cancel
        @Assert: User is not created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_user_2(self):
        """
        @Feature: User - Negative Create
        @Test: Create User with invalid Username
        @Steps:
        1. Create User for all invalid Usernames in [2]
        using valid First Name, Surname, Email Address, Language, authorized by
        @Assert: User is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_user_3(self):
        """
        @Feature: User - Negative Create
        @Test: Create User with invalid Firstname
        @Steps:
        1. Create User for all invalid Firstname in [2]
        using valid Username, Surname, Email Address, Language, authorized by
        @Assert: User is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_user_4(self):
        """
        @Feature: User - Negative Create
        @Test: Create User with invalid Surname
        @Steps:
        1. Create User for all invalid Surname in [2]
        using valid Username, First Name Email Address, Language, authorized by
        @Assert: User is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_user_5(self):
        """
        @Feature: User - Negative Create
        @Test: Create User with invalid Email Address
        @Steps:
        1. Create User for all invalid Email Address in [2]
        using valid Username, First Name, Surname, Language, authorized by
        @Assert: User is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_user_6(self):
        """
        @Feature: User - Negative Create
        @Test: Create User with blank Authorized by
        @Steps:
        1. Create User with blank Authorized by
        using valid Username, First Name, Surname, Email Address, Language
        @Assert: User is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_user_7(self):
        """
        @Feature: User - Negative Create
        @Test: Create User with blank Authorized by but values in
        Password and verify
        @Steps:
        1. Create User with blank Authorized by but having matching values in
        Password and verify fields and using valid Username, First Name,
        Surname, Email Address, Language
        @Assert: User is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_user_8(self):
        """
        @Feature: User - Negative Create
        @Test: Create User with non-matching values in Password and verify
        @Steps:
        1. Create User with non-matching values in Password and verify
        using valid Username, First Name, Surname, Email Address, Language,
        authorized by - INTERNAL
        @Assert: User is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_1(self):
        """
        @Feature: User - Positive Update
        @Test: Update Username in User
        @Steps:
        1. Create User
        2. Update User name for all variations in [1]
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_2(self):
        """
        @Feature: User - Positive Update
        @Test: Update Firstname in User
        @Steps:
        1. Create User
        2. Update Firstname name for all variations in [1]
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_3(self):
        """
        @Feature: User - Positive Update
        @Test: Update Surname in User
        @Steps:
        1. Create User
        2. Update Surname for all variations in [1]
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_4(self):
        """
        @Feature: User - Positive Update
        @Test: Update Email Address in User
        @Steps:
        1. Create User
        2. Update Email Address for all variations in [1]
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_5(self):
        """
        @Feature: User - Positive Update
        @Test: Update Language in User
        @Steps:
        1. Create User
        2. Update User with all different Language options
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_6(self):
        """
        @Feature: User - Positive Update
        @Test: Update Password/Verify fields in User
        @Steps:
        1. Create User
        2. Update Password/Verify fields
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_7(self):
        """
        @Feature: User - Positive Update
        @Test: Convert an user from an admin user to non-admin user
        @Steps:
        1. Create User with Administrator rights
        2. Update the User to remove Administrator rights
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_8(self):
        """
        @Feature: User - Positive Update
        @Test: Convert a user to an admin user
        @Steps:
        1. Create a regular (non-admin) user
        2. Update the User to add Administrator rights
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_9(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with one role
        @Steps:
        1. Create User
        2. Assign one role to the user
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_10(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with multiple roles
        @Steps:
        1. Create User
        2. Assign multiple roles to the user
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_11(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with all roles
        @Steps:
        1. Create User
        2. Assign all available roles to the user
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_12(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with one owned host
        @Steps:
        1. Create User
        2. Assign one host to the user
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_13(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with multiple owned hosts
        @Steps:
        1. Create User
        2. Assign multiple owned hosts to the user
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_14(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with all owned hosts
        @Steps:
        1. Create User
        2. Assign all available owned hosts to the user
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_15(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with one Domain host
        @Steps:
        1. Create User
        2. Assign one Domain host to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_16(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with multiple Domain hosts
        @Steps:
        1. Create User
        2. Assign multiple Domain hosts to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_17(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with all Domain hosts
        @Steps:
        1. Create User
        2. Assign all Domain hosts to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_18(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with one Compute Resource
        @Steps:
        1. Create User
        2. Assign one Compute Resource to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_19(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with multiple Compute Resources
        @Steps:
        1. Create User
        2. Assign multiple Compute Resources to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_20(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with all Compute Resources
        @Steps:
        1. Create User
        2. Assign all Compute Resources to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_21(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with one Host group
        @Steps:
        1. Create User
        2. Assign one Host group to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_22(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with multiple Host groups
        @Steps:
        1. Create User
        2. Assign multiple Host groups to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_23(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with all Host groups
        @Steps:
        1. Create User
        2. Assign all available Host groups to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_24(self):
        """
        @Feature: User - Positive Update
        @Test: Assign a User to an Org
        @Steps:
        1. Create User
        2. Assign an Org to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_25(self):
        """
        @Feature: User - Positive Update
        @Test: Assign a User to multiple Orgs
        @Steps:
        1. Create User
        2. Assign multiple Orgs to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_26(self):
        """
        @Feature: User - Positive Update
        @Test: Assign a User to all available Orgs
        @Steps:
        1. Create User
        2. Assign all available Orgs to the User
        @Assert: User is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_user_28(self):
        """
        @Feature: User - Positive Update
        @Test: Update User with a new Fact filter
        @Steps:
        1. Create User
        2. Create and assign a new Fact filter to the User
        @Assert: User is update
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update_user_1(self):
        """
        @Feature: User - Negative Update
        @Test: Update invalid Username in an User
        @Steps:
        1. Create User
        2. Update Username for all variations in [2]
        @Assert: User is not updated.  Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update_user_2(self):
        """
        @Feature: User - Negative Update
        @Test: Update invalid Firstname in an User
        @Steps:
        1. Create User
        2. Update Firstname for all variations in [2]
        @Assert: User is not updated.  Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update_user_3(self):
        """
        @Feature: User - Negative Update
        @Test: Update invalid Surname in an User
        @Steps:
        1. Create User
        2. Update Surname for all variations in [2]
        @Assert: User is not updated.  Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update_user_4(self):
        """
        @Feature: User - Negative Update
        @Test: Update invalid Email Address in an User
        @Steps:
        1. Create User
        2. Update Email Address for all variations in [2]
        @Assert: User is not updated.  Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update_user_5(self):
        """
        @Feature: User - Negative Update
        @Test: Update different values in Password and verify fields in an User
        @Steps:
        1. Create User
        2. Update the password by entering different values in Password and
        verify fields
        @Assert: User is not updated.  Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update_user_6(self):
        """
        @Feature: User - Negative Update
        @Test: [UI ONLY] Attempt to update User info and Cancel
        @Steps:
        1. Update Current user with valid Firstname, Surname, Email Address,
        Language, Password/Verify fields
        2. Click Cancel
        @Assert: User is not updated.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_delete_user_1(self):
        """
        @Feature: User - Positive Delete
        @Test: Delete a user
        @Steps:
        1. Create User
        2. Delete the User
        @Assert: User is deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_delete_user_2(self):
        """
        @Feature: User - Positive Delete
        @Test: Delete an admin user
        @Steps:
        1. Create an admin user
        2. Delete the User
        @Assert: User is deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_delete_user_1(self):
        """
        @Feature: User - Negative Delete
        @Test: [UI ONLY] Attempt to delete an User and cancel
        @Steps:
        1. Create a User
        2. ATtempt to delete the user and click Cancel on the confirmation
        @Assert: User is not deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_delete_user_2(self):
        """
        @Feature: User - Negative Delete
        @Test: Attempt to delete the last remaining admin user
        @Steps:
        1. Create multiple Users and admin users
        2. Delete the users except the last admin user
        3. Attempt to delete the last admin user
        @Assert: User is not deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_list_user_1(self):
        """
        @Feature: User - list
        @Test: List User for all variations of Username
        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_list_user_2(self):
        """
        @Feature: User - list
        @Test: List User for all variations of Firstname
        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_list_user_3(self):
        """
        @Feature: User - list
        @Test: List User for all variations of Surname
        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_list_user_4(self):
        """
        @Feature: User - list
        @Test: List User for all variations of Email Address
        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_list_user_5(self):
        """
        @Feature: User - list
        @Test: List User for all variations of Language
        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. List User
        @Assert: User is listed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_search_user_1(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Username
        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_search_user_2(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Firstname
        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_search_user_3(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Surname
        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_search_user_4(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Email Address
        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_search_user_5(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Language
        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. Search/Find User
        @Assert: User is found
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_info_user_1(self):
        """
        @Feature: User - info
        @Test: Get User info for all variations of Username
        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_info_user_2(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Firstname
        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_info_user_3(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Surname
        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_info_user_4(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Email Address
        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_info_user_5(self):
        """
        @Feature: User - search
        @Test: Search User for all variations of Language
        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. Get info of the User
        @Assert: User info is displayed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_end_to_end_user_1(self):
        """
        @Feature: User - End to End
        @Test: Create User and perform different operations
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
        self.fail(NOT_IMPLEMENTED)

    def test_end_to_end_user_2(self):
        """
        @Feature: User - End to End
        @Test: Create User with no Org assigned and attempt different
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
        self.fail(NOT_IMPLEMENTED)
