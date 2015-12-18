# -*- encoding: utf-8 -*-
"""Test class for Users CLI

When testing email validation [1] and [2] should be taken into consideration.

[1] http://tools.ietf.org/html/rfc3696#section-3
[2] https://github.com/theforeman/foreman/pull/1776

"""
import random
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_location, make_org, make_role, make_user
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.datafactory import (
    invalid_emails_list,
    invalid_names_list,
    valid_emails_list,
    valid_usernames_list,
)
from robottelo.decorators import stubbed, skip_if_bug_open, tier1, tier2, tier3
from robottelo.test import CLITestCase


class UserTestCase(CLITestCase):
    """Implements Users tests in CLI"""

    # CRUD

    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create User for all variations of Username

        @Feature: User - Positive Create

        @Assert: User is created
        """
        include_list = [gen_string("alphanumeric", 100)]
        for login in valid_usernames_list() + include_list:
            with self.subTest(login):
                user = make_user({'login': login})
                self.assertEqual(user['login'], login)

    @tier1
    def test_positive_create_with_firstname(self):
        """@Test: Create User for all variations of First Name

        @Feature: User - Positive Create

        @Assert: User is created
        """
        include_list = [gen_string("alphanumeric", 50)]
        for firstname in valid_usernames_list() + include_list:
            with self.subTest(firstname):
                user = make_user({'firstname': firstname})
                self.assertIn(firstname, user['name'])

    @tier1
    def test_positive_create_with_surname(self):
        """@Test: Create User for all variations of Surname

        @Feature: User - Positive Create

        @Assert: User is created
        """
        include_list = [gen_string("alphanumeric", 50)]
        for lastname in valid_usernames_list() + include_list:
            with self.subTest(lastname):
                user = make_user({'lastname': lastname})
                self.assertIn(lastname, user['name'])

    @tier1
    def test_positive_create_user_with_email(self):
        """@Test: Create User for all variations of Email Address

        @Feature: User - Positive Create

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
    def test_positive_create_with_password(self):
        """@Test: Create User for all variations of Password

        @Feature: User - Positive Create

        @Assert: User is created
        """
        include_list = [gen_string("alphanumeric", 3000)]
        for password in valid_usernames_list() + include_list:
            with self.subTest(password):
                user = make_user({'password': password})
                self.assertTrue(user)

    @tier1
    def test_positive_create_admin(self):
        """@Test: Create an Admin user

        @Feature: User - Positive Create

        @Assert: Admin User is created
        """
        user = make_user({'admin': '1'})
        self.assertEqual(user['admin'], 'yes')

    @tier1
    def test_positive_create_with_default_loc(self):
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
    def test_positive_create_with_defaut_org(self):
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

    @skip_if_bug_open('bugzilla', 1138553)
    @tier2
    def test_positive_add_role(self):
        """@Test: Add role to User for all variations of role names

        @Feature: User - Add role

        @Assert: Role is added to user

        @BZ: 1138553
        """
        user = make_user()
        include_list = [gen_string("alphanumeric", 100)]
        for role_name in valid_usernames_list() + include_list:
            with self.subTest(role_name):
                make_role({'name': role_name})
                User.add_role({
                    'login': user['login'],
                    'role': role_name,
                })
                user = User.info({'id': user['id']})
                self.assertIn(role_name, user['roles'])

    @skip_if_bug_open('bugzilla', 1138553)
    @tier2
    def test_positive_remove_role(self):
        """@Test: Remove role from User for all variations of role names

        @Feature: User - Remove role

        @Assert: Role is removed

        @BZ: 1138553
        """
        user = make_user()
        include_list = [gen_string("alphanumeric", 100)]
        for role_name in valid_usernames_list() + include_list:
            with self.subTest(role_name):
                make_role({'name': role_name})
                User.add_role({
                    'login': user['login'],
                    'role': role_name,
                })
                user = User.info({'id': user['id']})
                self.assertIn(role_name, user['roles'])
                User.remove_role({
                    'login': user['login'],
                    'role': role_name,
                })
                user = User.info({'id': user['id']})
                self.assertNotIn(role_name, user['roles'])

    @stubbed()
    @tier2
    def test_positive_add_roles(self):
        """@Test: Add multiple roles to User

        @Feature: User - Add role

        @Assert: Roles are added to user

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_add_all_default_roles(self):
        """@Test: Create User and assign all available default roles to it

        @Feature: User - Add role

        @Assert: All default roles are added to user

        @Status: Manual
        """

    @tier1
    def test_positive_create_with_org(self):
        """@Test: Create User associated to one Organization

        @Feature: User - Positive Create

        @Assert: User is created
        """
        org = make_org()
        user = make_user({'organization-ids': org['id']})
        self.assertEqual(org['name'], user['organizations'][0])

    @tier2
    def test_positive_create_with_orgs(self):
        """@Test: Create User associated to multiple Organizations

        @Feature: User - Positive Create

        @Assert: User is created
        """
        orgs_amount = random.randint(3, 5)
        orgs = [make_org() for _ in range(orgs_amount)]
        user = make_user({'organization-ids': [org['id'] for org in orgs]})
        self.assertEqual(len(user['organizations']), orgs_amount)
        for org in orgs:
            self.assertIn(org['name'], user['organizations'])

    @stubbed()
    @tier2
    def test_positive_create_in_ldap_modes(self):
        """@Test: Create User in supported ldap modes

        @Feature: User - Positive Create

        @Steps:
        1. Create User in all supported ldap modes - (Active Driectory,
        IPA, Posix)

        @Assert: User is created without specifying the password

        @Status: Manual
        """

    @tier1
    def test_negative_create_with_invalid_username(self):
        """@Test: Create User with invalid Username

        @Feature: User - Negative Create

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
                    User.create(options)

    @tier1
    def test_negative_create_with_invalid_firstname(self):
        """@Test: Create User with invalid First Name

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        for invalid_firstname in (gen_string("alpha", 51),
                                  gen_string("html")):
            with self.subTest(invalid_firstname):
                with self.assertRaises(CLIReturnCodeError):
                    User.create({
                        'auth-source-id': 1,
                        'login': gen_string('alpha'),
                        'firstname': invalid_firstname,
                        'mail': 'root@localhost',
                        'password': gen_string('alpha'),
                    })

    @tier1
    def test_negative_create_with_invalid_lastname(self):
        """@Test: Create User with invalid lastname

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        for invalid_lastname in (gen_string("alpha", 51),
                                 gen_string("html")):
            with self.subTest(invalid_lastname):
                with self.assertRaises(CLIReturnCodeError):
                    User.create({
                        'auth-source-id': 1,
                        'login': gen_string('alpha'),
                        'lastname': invalid_lastname,
                        'mail': 'root@localhost',
                        'password': gen_string('alpha'),
                    })

    @tier1
    def test_negative_create_with_invalid_email(self):
        """@Test: Create User with invalid Email Address

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        for email in invalid_emails_list():
            with self.subTest(email):
                with self.assertRaises(CLIReturnCodeError):
                    User.create({
                        'auth-source-id': 1,
                        'firstname': gen_string('alpha'),
                        'lastname': gen_string('alpha'),
                        'login': gen_string('alpha'),
                        'mail': email,
                        'password': gen_string('alpha'),
                    })

    @skip_if_bug_open('bugzilla', 1204686)
    @tier1
    def test_verify_bugzilla_1204686(self):
        """@Test: Create User with empty Email Address

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.

        @BZ: 1204686
        """
        with self.assertRaises(CLIReturnCodeError):
            User.create({
                'auth-source-id': 1,
                'firstname': gen_string('alpha'),
                'lastname': gen_string('alpha'),
                'login': gen_string('alpha'),
                'mail': '',
                'password': gen_string('alpha'),
            })

    @tier1
    def test_negative_create_with_blank_authorized_by(self):
        """@Test: Create User with blank Authorized by

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        with self.assertRaises(CLIReturnCodeError):
            User.create({
                'auth-source-id': '',
                'login': gen_string('alpha'),
                'mail': 'root@localhost',
            })

    @tier1
    def test_negative_create_with_blank_authorized_by_full(self):
        """@Test: Create User with blank Authorized by but having matching values in
        Password and verify fields and using valid Username, First Name,
        Surname, Email Address, Language

        @Feature: User - Negative Create Password and verify

        @Assert: User is not created. Appropriate error shown.
        """
        with self.assertRaises(CLIReturnCodeError):
            User.create({
                'auth-source-id': '',
                'login': gen_string('alpha'),
                'mail': 'root@localhost',
                'password': gen_string('alpha'),
            })

    @tier1
    def test_positive_update_firstname(self):
        """@Test: Update firstname value for existing User

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user()
        for new_firstname in valid_usernames_list():
            with self.subTest(new_firstname):
                User.update({
                    'firstname': new_firstname,
                    'id': user['id'],
                })
                result = User.info({'id': user['id']})
                user_name = result['name'].split(' ')
                self.assertEqual(user_name[0], new_firstname)

    @tier1
    def test_positive_update_username(self):
        """@Test: Update username value for existing User

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user()
        include_list = [gen_string("alphanumeric", 100)]
        for new_login in valid_usernames_list() + include_list:
            with self.subTest(new_login):
                User.update({
                    'id': user['id'],
                    'login': new_login,
                })
                user = User.info({'id': user['id']})
                self.assertEqual(user['login'], new_login)

    @tier1
    def test_positive_update_lastname(self):
        """@Test: Update Last Name value for existing User

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user()
        for new_lastname in valid_usernames_list():
            with self.subTest(new_lastname):
                User.update({
                    'id': user['id'],
                    'lastname': new_lastname,
                })
                user = User.info({'id': user['id']})
                last_name_after = user['name'].split(' ')
                self.assertEqual(last_name_after[1], new_lastname)

    @tier1
    def test_positive_update_email(self):
        """@Test: Update Email Address value for existing User

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user()
        for email in valid_emails_list():
            with self.subTest(email):
                User.update({
                    'id': user['id'],
                    # escape to avoid bash syntax error
                    'mail': email.replace('"', r'\"').replace('`', r'\`'),
                })
                result = User.info({'id': user['id']})
                self.assertEqual(result['email'], email)

    @tier1
    def test_positive_update_password(self):
        """@Test: Update Password/Verify fields for existing User

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user()
        for password in valid_usernames_list():
            with self.subTest(password):
                User.update({
                    'id': user['id'],
                    'password': password,
                })
                user = User.info({'id': user['id']})
                self.assertTrue(user)

    @tier1
    def test_positive_update_to_non_admin(self):
        """@Test: Convert an user from an admin user to non-admin user

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user({'admin': '1'})
        self.assertEqual(user['admin'], 'yes')
        User.update({
            'id': user['id'],
            'admin': '0',
        })
        user = User.info({'id': user['id']})
        self.assertEqual(user['admin'], 'no')

    @tier1
    def test_positive_update_to_admin(self):
        """@Test: Convert usual user to an admin user

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user()
        self.assertEqual(user['admin'], 'no')
        User.update({
            'id': user['id'],
            'admin': '1',
        })
        user = User.info({'id': user['id']})
        self.assertEqual(user['admin'], 'yes')

    @stubbed()
    @tier1
    def test_positive_update_role(self):
        """@Test: Update User with one role

        @Feature: User - Positive Update

        @Assert: User is updated

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_update_roles(self):
        """@Test: Update User with multiple roles

        @Feature: User - Positive Update

        @Assert: User is updated

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_update_all_roles(self):
        """@Test: Update User with all roles

        @Feature: User - Positive Update

        @Assert: User is updated

        @Status: Manual
        """

    @tier1
    def test_positive_update_org(self):
        """@Test: Assign a User to an Org

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user()
        org = make_org()
        User.update({
            'id': user['id'],
            'organization-ids': org['id'],
        })
        user = User.info({'id': user['id']})
        self.assertEqual(org['name'], user['organizations'][0])

    @tier2
    def test_positive_update_orgs(self):
        """@Test: Assign a User to multiple Orgs

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        user = make_user()
        orgs_amount = random.randint(3, 5)
        orgs = [make_org() for _ in range(orgs_amount)]
        User.update({
            'id': user['id'],
            'organization-ids': [org['id'] for org in orgs],
        })
        user = User.info({'id': user['id']})
        self.assertEqual(len(user['organizations']), orgs_amount)
        for org in orgs:
            self.assertIn(org['name'], user['organizations'])

    @tier1
    def test_negative_update_username(self):
        """@Test: Try to update User using invalid Username

        @Feature: User - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        user = make_user()
        for new_user_name in invalid_names_list():
            with self.subTest(new_user_name):
                with self.assertRaises(CLIReturnCodeError):
                    User.update({
                        'id': user['id'],
                        'login': new_user_name,
                    })

    @tier1
    def test_negative_update_firstname(self):
        """@Test: Try to update User using invalid First Name

        @Feature: User - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        user = make_user()
        for invalid_firstname in invalid_names_list():
            with self.subTest(invalid_firstname):
                with self.assertRaises(CLIReturnCodeError):
                    User.update({
                        'firstname': invalid_firstname,
                        'login': user['login'],
                    })
                    updated_user = User.info({'id': user['id']})
                    self.assertEqual(updated_user['name'], user['name'])

    @tier1
    def test_negative_update_surname(self):
        """@Test: Try to update User using invalid Last Name

        @Feature: User - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        user = make_user()
        for invalid_lastname in (gen_string('alpha', 51),
                                 gen_string('html')):
            with self.subTest(invalid_lastname):
                with self.assertRaises(CLIReturnCodeError):
                    User.update({
                        'lastname': invalid_lastname,
                        'login': user['login'],
                    })

    @tier1
    def test_negative_update_email(self):
        """@Test: Try to update User using invalid Email Address

        @Feature: User - Negative Update

        @Assert: User is not updated.  Appropriate error shown.
        """
        user = make_user()
        for email in invalid_emails_list():
            with self.subTest(email):
                with self.assertRaises(CLIReturnCodeError):
                    User.update({
                        'login': user['login'],
                        'mail': email,
                    })

    @tier1
    def test_positive_delete_by_name(self):
        """@Test: Create an user and then delete it using its name

        @Feature: User - Positive Delete

        @Assert: User is deleted
        """
        for login in valid_usernames_list():
            with self.subTest(login):
                user = make_user({'login': login})
                self.assertEqual(user['login'], login)
                User.delete({'login': user['login']})
                with self.assertRaises(CLIReturnCodeError):
                    User.info({'login': user['login']})

    @tier1
    def test_positive_delete_by_id(self):
        """@Test: Create an user and then delete it using its id

        @Feature: User - Positive Delete

        @Assert: User is deleted
        """
        user = make_user()
        User.exists(search=('login', user['login']))
        User.delete({'id': user['id']})
        with self.assertRaises(CLIReturnCodeError):
            User.info({'login': user['login']})

    @tier1
    def test_positive_delete_admin(self):
        """@Test: Delete an admin user

        @Feature: User - Positive Delete

        @Assert: User is deleted
        """
        for login in valid_usernames_list():
            with self.subTest(login):
                user = make_user({"login": login, "admin": 'true'})
                self.assertEqual(user['admin'], 'yes')
                User.delete({'login': user['login']})
                with self.assertRaises(CLIReturnCodeError):
                    User.info({'login': user['login']})

    @tier1
    def test_negative_delete_internal(self):
        """@Test: Attempt to delete internal admin user

        @Feature: User - Negative Delete

        @Assert: User is not deleted
        """
        login = settings.server.admin_username
        with self.assertRaises(CLIReturnCodeError):
            User.delete({'login': login})
        self.assertTrue(User.info({'login': login}))

    @tier1
    def test_positive_list_username(self):
        """@Test: List User for all variations of Username

        @Feature: User - list

        @Assert: User is listed
        """
        for login in valid_usernames_list():
            with self.subTest(login):
                user = make_user({'login': login})
                result = User.list({
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
    def test_positive_list_firstname(self):
        """@Test: List User for all variations of First Name

        @Feature: User - list

        @Assert: User is listed
        """
        for firstname in valid_usernames_list():
            with self.subTest(firstname):
                user = make_user({'firstname': firstname})
                result = User.list({
                    u'search': u'firstname = {0}'.format(firstname),
                })
                # make sure user is in list result
                self.assertEqual({
                    'email': user['email'],
                    'id': user['id'],
                    'login': user['login'],
                    'name': user['name'],
                }, result[0])

    @tier1
    def test_positive_list_surname(self):
        """@Test: List User for all variations of Surname

        @Feature: User - list

        @Assert: User is listed
        """
        for lastname in valid_usernames_list():
            with self.subTest(lastname):
                user = make_user({'lastname': lastname})
                result = User.list({
                    u'search': u'lastname = {0}'.format(lastname),
                })
                # make sure user is in list result
                self.assertEqual({
                    'email': user['email'],
                    'id': user['id'],
                    'login': user['login'],
                    'name': user['name'],
                }, result[0])

    @tier1
    def test_positive_list_email(self):
        """@Test: List User for all variations of Email Address

        @Feature: User - list

        @Assert: User is listed
        """
        for mail in (gen_string("alpha") + "@somemail.com",
                     gen_string("alphanumeric", 10) + "@somemail.com",
                     gen_string("numeric") + "@somemail.com",
                     gen_string("alphanumeric", 50) + "@somem.com"):
            with self.subTest(mail):
                user = make_user({'mail': mail})
                result = User.list({
                    u'search': u'mail = {0}'.format(mail),
                })
                # make sure user is in list result
                self.assertEqual({
                    'email': user['email'],
                    'id': user['id'],
                    'login': user['login'],
                    'name': user['name'],
                }, result[0])

    @skip_if_bug_open('bugzilla', 1204667)
    @tier1
    def test_verify_bugzilla_1204667(self):
        """@Test: List User for utf-8,latin variations of Email Address

        @Feature: User - list

        @Assert: User is listed

        @BZ: 1204667
        """
        for mail in (gen_string("latin1") + "@somemail.com",
                     gen_string("utf8") + "@somemail.com"):
            with self.subTest(mail):
                user = make_user({'mail': mail})
                result = User.list({
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
    @tier3
    def test_positive_end_to_end(self):
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
    @tier3
    def test_positvie_end_to_end_without_org(self):
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
