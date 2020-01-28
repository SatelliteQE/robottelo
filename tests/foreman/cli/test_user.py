# -*- encoding: utf-8 -*-
"""Test class for Users CLI

When testing email validation [1] and [2] should be taken into consideration.

[1] http://tools.ietf.org/html/rfc3696#section-3
[2] https://github.com/theforeman/foreman/pull/1776


:Requirement: User

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import datetime
import pytest
import random

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_location, make_org, make_role, make_user
from robottelo.cli.org import Org
from robottelo.cli.role import Role
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import DEFAULT_ROLE
from robottelo.datafactory import (
    invalid_emails_list,
    invalid_names_list,
    valid_data_list,
    valid_emails_list,
    valid_usernames_list,
)
from robottelo.decorators import stubbed, tier1, tier2, tier3, upgrade
from robottelo.test import CLITestCase


class UserTestCase(CLITestCase):
    """Implements Users tests in CLI"""

    # CRUD

    @tier1
    def test_positive_create_with_name(self):
        """Create User for all variations of Username

        :id: 2d430243-8512-46ee-8d21-7ccf0c7af807

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        include_list = [gen_string("alphanumeric", 100)]
        for login in valid_usernames_list() + include_list:
            with self.subTest(login):
                user = make_user({'login': login})
                self.assertEqual(user['login'], login)

    @tier1
    def test_positive_create_with_firstname(self):
        """Create User for all variations of First Name

        :id: b5f07890-020c-4ea0-a519-75d325127b2b

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        include_list = [gen_string("alphanumeric", 50)]
        for firstname in valid_usernames_list() + include_list:
            with self.subTest(firstname):
                user = make_user({'firstname': firstname})
                self.assertIn(firstname, user['name'])

    @tier1
    def test_positive_create_with_surname(self):
        """Create User for all variations of Surname

        :id: 1b3d7014-6575-4cfd-b6d7-8ff2bfef587e

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        include_list = [gen_string("alphanumeric", 50)]
        for lastname in valid_usernames_list() + include_list:
            with self.subTest(lastname):
                user = make_user({'lastname': lastname})
                self.assertIn(lastname, user['name'])

    @tier1
    def test_positive_create_with_email(self):
        """Create User for all variations of Email Address

        :id: 2c3ba244-3bd7-4455-8289-03dc7a28a4a6

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        for email in valid_emails_list():
            with self.subTest(email):
                # The email must be escaped because some characters to not fail
                # the parsing of the generated shell command
                escaped_email = email.replace('"', r'\"').replace('`', r'\`')
                user = make_user({'mail': escaped_email})
                self.assertEqual(user['email'], email)

    @tier1
    def test_positive_create_with_description(self):
        """Create User for all variations of Description

        :id: 6d2f8d13-4033-4741-9bdd-37e76abff59f

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        for description in valid_data_list():
            with self.subTest(description):
                user = make_user({'description': description})
                self.assertEqual(description, user['description'])

    @tier1
    def test_positive_create_with_password(self):
        """Create User for all variations of Password

        :id: cffb7317-0a17-4fff-bd2b-66d295cd40ad

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        include_list = [gen_string("alphanumeric", 3000)]
        for password in valid_usernames_list() + include_list:
            with self.subTest(password):
                user = make_user({'password': password})
                self.assertTrue(user)

    @tier1
    @upgrade
    def test_positive_create_admin(self):
        """Create an Admin user

        :id: 0d0384ad-d85a-492e-8630-7f48912a4fd5

        :expectedresults: Admin User is created

        :CaseImportance: Critical
        """
        user = make_user({'admin': '1'})
        self.assertEqual(user['admin'], 'yes')

    @tier1
    def test_positive_create_with_default_loc(self):
        """Check if user with default location can be created

        :id: efe7256d-8c8f-444c-8d59-43500e1319c3

        :expectedresults: User is created and has new default location assigned

        :CaseImportance: Critical
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
        """Check if user with default organization can be created

        :id: cc692b6f-2519-429b-8ecb-c4bb51ed3544

        :expectedresults: User is created and has new default organization
            assigned

        :CaseImportance: Critical
        """
        org = make_org()
        user = make_user({
            'default-organization-id': org['id'],
            'organization-ids': org['id'],
        })
        self.assertIn(org['name'], user['organizations'])
        self.assertEqual(org['name'], user['default-organization'])

    @tier1
    def test_positive_create_with_org(self):
        """Create User associated to one Organization

        :id: 336bc067-9edd-481a-ae7a-0ff1270b2e41

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        org = make_org()
        user = make_user({'organization-ids': org['id']})
        self.assertEqual(org['name'], user['organizations'][0])

    @tier2
    def test_positive_create_with_orgs(self):
        """Create User associated to multiple Organizations

        :id: f537296c-a8a8-45ef-8996-c1d32b8f64de

        :expectedresults: User is created

        :CaseLevel: Integration
        """
        orgs_amount = random.randint(3, 5)
        orgs = [make_org() for _ in range(orgs_amount)]
        user = make_user({'organization-ids': [org['id'] for org in orgs]})
        self.assertEqual(len(user['organizations']), orgs_amount)
        for org in orgs:
            self.assertIn(org['name'], user['organizations'])

    @stubbed()
    @tier2
    @upgrade
    def test_positive_create_in_ldap_modes(self):
        """Create User in supported ldap modes

        :id: ef107cea-c0e1-4d67-88e5-45cd30122d29

        :Steps: Create User in all supported ldap modes - (Active Driectory,
            IPA, Posix)

        :expectedresults: User is created without specifying the password

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @tier1
    def test_negative_create_with_invalid_username(self):
        """Create User with invalid Username

        :id: 8bb53001-6377-49fe-a85c-f92204a5dea4

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        invalid_names = (
            '', 'space {0}'.format(gen_string('alpha')),
            gen_string('alpha', 101),
            gen_string('html')
        )
        for invalid_name in invalid_names:
            with self.subTest(invalid_name):
                options = {
                    'auth-source-id': 1,
                    'login': invalid_name,
                    'mail': 'root@localhost',
                    'password': gen_string('alpha'),
                }
                self.logger.debug(str(options))
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not create the user:'
                ):
                    User.create(options)

    @tier1
    def test_negative_create_with_invalid_firstname(self):
        """Create User with invalid First Name

        :id: 08b7be40-40f5-4423-91a6-03bb2bfb714c

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        invalid_first_names = (gen_string("alpha", 51), gen_string("html"))
        for invalid_first_name in invalid_first_names:
            with self.subTest(invalid_first_name):
                options = {
                    'auth-source-id': 1,
                    'login': gen_string('alpha'),
                    'firstname': invalid_first_name,
                    'mail': 'root@localhost',
                    'password': gen_string('alpha'),
                }
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not create the user'
                ):
                    User.create(options)

    @tier1
    def test_negative_create_with_invalid_lastname(self):
        """Create User with invalid lastname

        :id: f73d2374-6bdf-4d25-945e-46a34fe692e7

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        invalid_lastnames = (gen_string("alpha", 51), gen_string("html"))
        for invalid_lastname in invalid_lastnames:
            with self.subTest(invalid_lastname):
                options = {
                    'auth-source-id': 1,
                    'login': gen_string('alpha'),
                    'lastname': invalid_lastname,
                    'mail': 'root@localhost',
                    'password': gen_string('alpha'),
                }
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not create the user'
                ):
                    User.create(options)

    @tier1
    def test_negative_create_with_invalid_email(self):
        """Create User with invalid Email Address

        :id: e21be14c-e985-4f27-b189-1cfe454e03d2

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        for email in invalid_emails_list():
            with self.subTest(email):
                options = {
                    'auth-source-id': 1,
                    'firstname': gen_string('alpha'),
                    'lastname': gen_string('alpha'),
                    'login': gen_string('alpha'),
                    'mail': email,
                    'password': gen_string('alpha'),
                }
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not create the user'
                ):
                    User.create(options)

    @tier1
    def test_negative_create_with_blank_authorized_by(self):
        """Create User with blank Authorized by

        :id: 1f60fbf8-a5f0-432e-9b4e-60bc0224294a

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with self.assertRaisesRegex(
            CLIReturnCodeError,
            u'Could not create the user:'
        ):
            User.create({
                'auth-source-id': '',
                'login': gen_string('alpha'),
                'mail': 'root@localhost',
            })

    @tier1
    def test_negative_create_with_blank_authorized_by_full(self):
        """Create User with blank Authorized by but having matching
        values in Password and verify fields and using valid Username, First
        Name, Surname, Email Address, Language

        :id: 4b142a12-8354-437e-89cc-c0505bda2027

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with self.assertRaisesRegex(
            CLIReturnCodeError,
            u'Could not create the user:'
        ):
            User.create({
                'auth-source-id': '',
                'login': gen_string('alpha'),
                'mail': 'root@localhost',
                'password': gen_string('alpha'),
            })

    @tier1
    def test_positive_update_to_non_admin(self):
        """Convert an user from an admin user to non-admin user

        :id: 6a291547-d60d-4dc6-aeb6-d7ad969993a8

        :expectedresults: User is updated

        :CaseImportance: Critical
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
    @upgrade
    def test_positive_delete_by_name(self):
        """Create an user and then delete it using its name

        :id: 37cf4313-012f-4215-b537-030ee61c1c3c

        :expectedresults: User is deleted

        :CaseImportance: Critical
        """
        for login in valid_usernames_list():
            with self.subTest(login), self.assertRaises(CLIReturnCodeError):
                user = make_user({'login': login})
                self.assertEqual(user['login'], login)
                User.delete({'login': user['login']})

                User.info({'login': user['login']})

    @tier1
    def test_positive_delete_by_id(self):
        """Create an user and then delete it using its id

        :id: 7e97e177-b676-49b3-86ee-644f6f6ff30c

        :expectedresults: User is deleted

        :CaseImportance: Critical
        """
        user = make_user()
        User.exists(search=('login', user['login']))
        User.delete({'id': user['id']})
        with self.assertRaises(CLIReturnCodeError):
            User.info({'login': user['login']})

    @tier1
    def test_positive_delete_admin(self):
        """Delete an admin user

        :id: 9752706c-fdbd-4a36-af6f-27824d22ea03

        :expectedresults: User is deleted

        :CaseImportance: Critical
        """
        for login in valid_usernames_list():
            with self.subTest(login), self.assertRaises(CLIReturnCodeError):
                user = make_user({"login": login, "admin": 'true'})
                self.assertEqual(user['admin'], 'yes')
                User.delete({'login': user['login']})
                User.info({'login': user['login']})

    @tier1
    def test_negative_delete_internal_admin(self):
        """Attempt to delete internal admin user

        :id: 4fc92958-9e75-4bd2-bcbe-32f906e432f5

        :expectedresults: User is not deleted

        :CaseImportance: Critical
        """
        with self.assertRaisesRegex(
            CLIReturnCodeError,
            u'Could not delete the user:'
        ):
            User.delete({'login': self.foreman_user})
        self.assertTrue(User.info({'login': self.foreman_user}))

    @tier1
    def test_positive_list_username(self):
        """List User for all variations of Username

        :id: 3beef11a-c1d0-4b8f-a9f9-1eb557b36579

        :expectedresults: User is listed

        :CaseImportance: Critical
        """
        for login in valid_usernames_list():
            with self.subTest(login):
                user = make_user({'login': login})
                result = User.list({
                    u'search': u'login = {0}'.format(login),
                })
                self.assertEqual(len(result), 1)
                # make sure user is in list result
                self.assertEqual(
                    {user['id'], user['login']},
                    {result[0]['id'], result[0]['login']}
                )

    @tier1
    def test_positive_list_firstname(self):
        """List User for all variations of First Name

        :id: 7786d834-f899-4277-b7ed-5d66605fb746

        :expectedresults: User is listed

        :CaseImportance: Critical
        """
        for firstname in valid_usernames_list():
            with self.subTest(firstname):
                user = make_user({'firstname': firstname})
                result = User.list({
                    u'search': u'firstname = {0}'.format(firstname),
                })
                # make sure user is in list result
                self.assertEqual(
                    {user['id'], user['login'], user['name']},
                    {result[0]['id'], result[0]['login'], result[0]['name']}
                )

    @tier1
    def test_positive_list_surname(self):
        """List User for all variations of Surname

        :id: 1fcc6b76-28d8-4253-86b0-dae09703abe1

        :expectedresults: User is listed

        :CaseImportance: Critical
        """
        for lastname in valid_usernames_list():
            with self.subTest(lastname):
                user = make_user({'lastname': lastname})
                result = User.list({
                    u'search': u'lastname = {0}'.format(lastname),
                })
                # make sure user is in list result
                self.assertEqual(
                    {user['id'], user['login'], user['name']},
                    {result[0]['id'], result[0]['login'], result[0]['name']}
                )

    @tier1
    def test_positive_list_email(self):
        """List User for all variations of Email Address

        :id: 252f5583-6c34-43ae-9966-636fa0a2bb10

        :expectedresults: User is listed

        :CaseImportance: Critical
        """
        valid_emails = (
            gen_string("alpha") + "@somemail.com",
            gen_string("alphanumeric", 10) + "@somemail.com",
            gen_string("numeric") + "@somemail.com",
            gen_string("alphanumeric", 50) + "@somem.com"
        )
        for mail in valid_emails:
            with self.subTest(mail):
                user = make_user({'mail': mail})
                result = User.list({
                    u'search': u'mail = {0}'.format(mail),
                })
                # make sure user is in list result
                self.assertEqual(
                    {user['email'], user['id'], user['login']},
                    {result[0]['email'], result[0]['id'], result[0]['login']}
                )

    @tier1
    def test_positive_create_with_email_utf8_latin(self):
        """List User for utf-8,latin variations of Email Address

        :id: 3d865df5-2e28-44fb-add8-c79a18db2f95

        :expectedresults: User is listed

        :BZ: 1204667

        :CaseImportance: Critical
        """
        valid_mails = (
            gen_string("latin1") + "@somemail.com",
            gen_string("utf8") + "@somemail.com"
        )
        for mail in valid_mails:
            with self.subTest(mail):
                user = make_user({'mail': mail})
                result = User.list({
                    u'search': u'mail = {0}'.format(mail),
                })
                # make sure user is in list result
                self.assertEqual(
                    {user['email'], user['id'], user['login']},
                    {result[0]['email'], result[0]['id'], result[0]['login']}
                )

    @stubbed()
    @tier3
    @upgrade
    def test_positive_end_to_end(self):
        """Create User and perform different operations

        :id: fc723d97-fc36-4468-8b1e-3c07d28f4d10

        :Steps:
            1. Create User
            2. Login with the new user
            3. Upload Subscriptions
            4. Provision Systems
            5. Add/Remove Users
            6. Add/Remove Orgs
            7. Delete the User

        :expectedresults: All actions passed

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_end_to_end_without_org(self):
        """Create User with no Org assigned and attempt different operations

        :id: a5ed8e77-942f-4b48-b184-b72b38cdb4f9

        :Steps:
            1. Create User.  Do not assign any Org
            2. Login with the new user
            3. Attempt to Upload Subscriptions
            4. Attempt to Provision Systems
            5. Attempt to Add/Remove Users
            6. Attempt to Add/Remove Orgs

        :expectedresults: All actions failed since the User is not assigned to
            any Org

        :CaseAutomation: notautomated

        :CaseLevel: System
        """


class UserWithCleanUpTestCase(CLITestCase):
    """Implements Users tests in CLI which user can be cleaned up after tests,
    thus reducing number of users on system
    """

    @classmethod
    def setUpClass(cls):
        """
        Initializes class attribute ``dct_roles`` with several random roles
        saved on sat. roles is a dict so keys are role's id respective value is
        the role itself
        """

        super(UserWithCleanUpTestCase, cls).setUpClass()
        settings.configure()
        include_list = [gen_string("alphanumeric", 100)]

        def roles_helper():
            """Generator funcion which creates several Roles to be used on
            tests
            """
            for role_name in valid_usernames_list() + include_list:
                yield make_role({'name': role_name})

        cls.stubbed_roles = {role['id']: role for role in roles_helper()}
        # Get all user roles except default one due to BZ 1518654
        cls.all_user_roles = {role['id']: role for role in Role.list()
                              if role['name'] != DEFAULT_ROLE}

    @classmethod
    def tearDownClass(cls):
        """Remove all roles created during tests"""
        super(UserWithCleanUpTestCase, cls).tearDownClass()
        for role_id in cls.stubbed_roles:
            Role.delete({'id': role_id})

    def setUp(self):
        """Setting up user to be used on tests"""
        super(UserWithCleanUpTestCase, self).setUp()
        self.user = make_user()

    def tearDown(self):
        """Cleaning up user used on tests"""
        super(UserWithCleanUpTestCase, self).tearDown()
        User.delete({'id': self.user['id']})

    def assert_user_roles(self, roles_dct):
        """
        Check if roles present on roles_dct are added to user
        :param roles_dct: dictionary if roles
        """
        user = self.user
        expected_role_names = set(user['roles'])
        for role_id, role in roles_dct.items():
            User.add_role({'login': user['login'], 'role-id': role_id})
            expected_role_names.add(role['name'])
        self.assertItemsEqual(
            expected_role_names,
            User.info({'id': user['id']})['roles']
        )

    @tier1
    def test_positive_update_firstname(self):
        """Update firstname value for existing User

        :id: c51baf5e-206d-4e95-a713-795574080bd9

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        user = self.user
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
        """Update username value for existing User

        :id: 72734d5a-bfba-4db8-9c8f-cc6190c74b69

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        user = self.user
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
        """Update Last Name value for existing User

        :id: 03479f69-7606-46b3-9dc1-664d30f40ae1

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        user = self.user
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
        """Update Email Address value for existing User

        :id: 75067bf3-e43e-4c6a-b3fd-63e564eda7db

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        user = self.user
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
    def test_positive_update_description(self):
        """Update Description value for existing User

        :id: 8ead3d27-884a-4ac3-94e8-476f406c557b

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        user = self.user
        for new_description in valid_data_list():
            with self.subTest(new_description):
                User.update({
                    'id': user['id'],
                    'description': new_description,
                })
                user = User.info({'id': user['id']})
                self.assertEqual(user['description'], new_description)

    @tier1
    @upgrade
    def test_positive_update_password(self):
        """Update Password/Verify fields for existing User

        :id: 065197ab-1352-4da8-9df6-b6ff332e6847

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        user = self.user
        for password in valid_usernames_list():
            with self.subTest(password):
                User.update({
                    'id': user['id'],
                    'password': password,
                })
                user = User.info({'id': user['id']})
                self.assertTrue(user)

    @tier1
    def test_positive_update_to_admin(self):
        """Convert usual user to an admin user

        :id: 3c5cdeb0-c529-472e-a291-269b703bf9d1

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        user = self.user
        self.assertEqual(user['admin'], 'no')
        User.update({
            'id': user['id'],
            'admin': '1',
        })
        user = User.info({'id': user['id']})
        self.assertEqual(user['admin'], 'yes')

    @tier1
    def test_positive_update_org(self):
        """Assign a User to an Org

        :id: 7d16ea11-b1e9-4f3b-b3c5-a4b8569947da

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        user = self.user
        org = make_org()
        User.update({
            'id': user['id'],
            'organization-ids': org['id'],
        })
        user = User.info({'id': user['id']})
        self.assertEqual(org['name'], user['organizations'][0])

    @tier2
    def test_positive_update_orgs(self):
        """Assign a User to multiple Orgs

        :id: 2303ea38-eb08-4f68-ac73-48968e06aec0

        :expectedresults: User is updated

        :CaseLevel: Integration
        """
        user = self.user
        orgs_amount = random.randint(3, 5)
        orgs = [make_org() for _ in range(orgs_amount)]
        User.update({
            'id': user['id'],
            'organization-ids': [org['id'] for org in orgs],
        })
        user = User.info({'id': user['id']})
        self.assertItemsEqual(
            user['organizations'],
            [org['name'] for org in orgs]
        )

    @tier1
    def test_negative_update_username(self):
        """Try to update User using invalid Username

        :id: 208bb597-1b33-44c8-9b15-b7bfcbb739fd

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        user = self.user
        for new_user_name in invalid_names_list():
            with self.subTest(new_user_name):
                options = {'id': user['id'], 'login': new_user_name}
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not update the user:'
                ):
                    User.update(options)

    @tier1
    def test_negative_update_firstname(self):
        """Try to update User using invalid First Name

        :id: fb425e86-6e09-4535-b1dc-aef1e02ea712

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        user = self.user
        for invalid_firstname in invalid_names_list():
            with self.subTest(invalid_firstname):
                options = {
                    'firstname': invalid_firstname, 'login': user['login'],
                }
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not update the user:'
                ):
                    User.update(options)
                updated_user = User.info({'id': user['id']})
                self.assertEqual(updated_user['name'], user['name'])

    @tier1
    def test_negative_update_surname(self):
        """Try to update User using invalid Last Name

        :id: 92ca237a-daa8-43bd-927b-a0bdc8250658

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        user = self.user
        for invalid_lastname in (gen_string('alpha', 51), gen_string('html')):
            with self.subTest(invalid_lastname):
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not update the user:'
                ):
                    User.update({
                        'lastname': invalid_lastname,
                        'login': user['login']
                    })

    @tier1
    def test_negative_update_email(self):
        """Try to update User using invalid Email Address

        :id: 4a2876cc-2580-4ae9-8ce7-d7390bfebd4b

        :expectedresults: User is not updated.  Appropriate error shown.

        :CaseImportance: Critical
        """
        user = self.user
        for email in invalid_emails_list():
            with self.subTest(email):
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not update the user:'
                ):
                    User.update({
                        'login': user['login'],
                        'mail': email
                    })

    @tier2
    def test_positive_add_role(self):
        """Add role to User for all variations of role names

        :id: 4df495b8-ed02-480e-a935-ffc0b6746e08

        :expectedresults: Role is added to user

        :BZ: 1138553

        :CaseLevel: Integration
        """
        user = self.user
        for role_id, role in self.stubbed_roles.items():
            with self.subTest(role['name']):
                User.add_role({
                    'login': user['login'],
                    'role-id': role_id,
                })
                user = User.info({'id': user['id']})
                self.assertIn(role['name'], user['roles'])

    @tier2
    @upgrade
    def test_positive_add_roles(self):
        """Add multiple roles to User

        For now add-role user sub command does not allow multiple role ids
        (https://github.com/SatelliteQE/robottelo/issues/3729)
        So if if it gets fixed this test can be updated:
        (http://projects.theforeman.org/issues/16206)

        :id: d769ac61-f158-4e4e-a176-1c87de8b00f6

        :expectedresults: Roles are added to user

        :CaseLevel: Integration
        """
        user = self.user
        original_role_names = set(user['roles'])
        expected_role_names = set(original_role_names)

        for role_id, role in self.stubbed_roles.items():
            User.add_role({'login': user['login'], 'role-id': role_id})
            expected_role_names.add(role['name'])

        self.assertItemsEqual(
            expected_role_names,
            User.info({'id': user['id']})['roles']
        )

    @tier2
    @upgrade
    def test_positive_remove_role(self):
        """Remove role from User for all variations of role names

        :id: 51b15516-da42-4149-8032-87baa93f9e56

        :expectedresults: Role is removed

        :BZ: 1138553

        :CaseLevel: Integration
        """
        user = self.user
        for role_id, role in self.stubbed_roles.items():
            role_name = role['name']
            with self.subTest(role_name):
                user_credentials = {'login': user['login'], 'role': role_name}
                User.add_role(user_credentials)
                user = User.info({'id': user['id']})
                self.assertIn(role_name, user['roles'])
                User.remove_role(user_credentials)
                user = User.info({'id': user['id']})
                self.assertNotIn(role_name, user['roles'])

    @pytest.mark.skip_if_open("BZ:1763816")
    @tier2
    def test_positive_last_login_for_new_user(self):
        """Create new user with admin role and check last login updated for that user

        :id: 967282d3-92d0-42ce-9ef3-e542d2883408

        :expectedresults: last login should be updated for user after login using hammer

        :BZ: 1763816

        :CaseLevel: Integration
        """
        login = gen_string('alpha')
        password = gen_string('alpha')
        org_name = gen_string('alpha')

        make_user({'login': login, 'password': password})
        User.add_role({'login': login, 'role': 'System admin'})
        result_before_login = User.list({
            u'search': u'login = {0}'.format(login),
        })

        # this is because satellite uses the UTC timezone
        before_login_time = datetime.datetime.utcnow()
        assert result_before_login[0]['login'] == login
        assert result_before_login[0]['last-login'] == ""

        Org.with_user(username=login, password=password).create({'name': org_name})
        result_after_login = User.list({
            u'search': u'login = {0}'.format(login),
        })

        # checking user last login should not be empty
        assert result_after_login[0]['last-login'] != ""
        after_login_time = datetime.datetime.strptime(result_after_login[0]['last-login'],
                                                      "%Y/%m/%d %H:%M:%S")
        assert after_login_time > before_login_time

    @stubbed()
    @tier2
    def test_positive_add_all_default_roles(self):
        """Create User and assign all available default roles to it

        :id: 7faa3254-36ad-4496-9c0e-7b0454e4bc26

        :expectedresults: All default roles are added to user

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @tier1
    def test_positive_update_role(self):
        """Update User with one role

        :id: 9b23f242-6a55-4267-bd70-b4a5619f7990

        :expectedresults: User is updated

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """
        for role_id, role in self.stubbed_roles.items():
            self.assert_user_roles({role_id: role})
            break  # test for only one role

    @tier2
    def test_positive_update_roles(self):
        """Update User with multiple roles

        :id: a41663a7-eb77-4083-9ca3-a1c1df1c87eb

        :expectedresults: User is updated

        :CaseLevel: Integration
        """
        self.assert_user_roles(self.stubbed_roles)


class SshKeyInUserTestCase(CLITestCase):
    """Implements the SSH Key in User Tests
    :CaseAutomation: notautomated
    """

    @stubbed()
    @tier1
    def test_positive_create_ssh_key(self):
        """SSH Key can be added to new User

        :id: 57304fca-8e0d-454a-be31-34423345c8b2

        :expectedresults: SSH key should be added to new user

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_add_ssh_key_from_file(self):
        """SSH Key can be added to User from ssh pub file

        :id: 8b43dbf3-7ead-4d00-97ce-cec24f29ce44

        :expectedresults: SSH key should be added to user from ssh pub file

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_create_ssh_key_super_admin(self):
        """SSH Key can be added to Super Admin user

        :id: b865d0ae-6317-475c-a6da-600615b71eeb

        :expectedresults: SSH Key should be added to Super Admin user

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_create_ssh_key(self):
        """Invalid ssh key can not be added in User Template

        :id: 05012e9b-f5cf-4cd6-ba4d-269be7b03f9b

        :steps:

            1. Create new user with all the details
            2. Attempt to add invalid string as SSH Key to above user
                e.g blabla

        :expectedresults:

            1. Invalid SSH key should not be added in user
            2. Satellite returns 'Fingerprint could not be generated' error

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_create_invalid_length_ssh_key(self):
        """Attempt to add SSH key that has invalid length

        :id: 1a101ba8-1456-423f-955a-8bf4e3b2147d

        :steps:

            1. Create new user with all the details
            2. Attempt to add invalid length of SSH Key to above user

        :expectedresults: Satellite should raise 'Length could not be
            calculated' error

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_create_multiple_ssh_key_types(self):
        """Multiple types of ssh keys can be added to user

        :id: 7afc4ad6-d3f0-4155-9de0-b24c417ca54a

        :steps:

            1. Create user with all the details
            2. Add multiple types of supported ssh keys, type includes
                rsa, dsa, ed25519, ecdsa

        :expectedresults: Multiple types of supported ssh keys can be added to
            user
        """

    @stubbed()
    @tier1
    def test_positive_delete_ssh_key(self):
        """Satellite Admin can delete ssh key from user

        :id: 75ebdba2-0f6c-4862-8546-22a37fc71062

        :steps:

            1. Create new user with all the details
            2. Add SSH Key to above user
            3. Delete the ssh-key from user

        :expectedresults: SSH key should be deleted from admin user

        :CaseImportance: Critical
        """

    @stubbed()
    @tier2
    def test_positive_list_users_ssh_key(self):
        """Satellite lists users ssh keys

        :id: 3fb375ef-c07e-4363-874c-94440858bbc2

        :steps:

            1. Create user with all the details
            2. Add SSH key in above user
            3. List all the ssh keys of above user

        :expectedresults: Satellite should list all the SSH keys of user

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_positive_info_users_ssh_key(self):
        """Satellite returns info of user ssh key

        :id: 0992fce7-0e79-4b7b-b8b7-d9b2818cc073

        :steps:

            1. Create user with all the details
            2. Add SSH key in above user
            3. Info the above ssh key in user

        :expectedresults: Satellite should return information of SSH keys of
            user

        :CaseImportance: Critical
        """
