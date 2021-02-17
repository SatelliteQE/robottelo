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
import random

import paramiko
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.org import Org
from robottelo.cli.role import Role
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_emails_list
from robottelo.datafactory import valid_usernames_list
from robottelo.ssh import get_connection
from robottelo.test import CLITestCase


class UserTestCase(CLITestCase):
    """Implements Users tests in CLI"""

    @classmethod
    def setUpClass(cls):
        """
        Initializes class attribute ``dct_roles`` with several random roles
        saved on sat. roles is a dict so keys are role's id respective value is
        the role itself
        """

        super().setUpClass()
        settings.configure()
        include_list = [gen_string("alphanumeric", 100)]

        def roles_helper():
            """Generator funcion which creates several Roles to be used on
            tests
            """
            for role_name in valid_usernames_list() + include_list:
                yield make_role({'name': role_name})

        cls.stubbed_roles = {role['id']: role for role in roles_helper()}

    @classmethod
    def tearDownClass(cls):
        """Remove all roles created during tests"""
        super().tearDownClass()
        for role_id in cls.stubbed_roles:
            Role.delete({'id': role_id})

    @pytest.mark.tier2
    def test_positive_CRUD(self):
        """Create User with various parameters, updating and deleting

        :id: 2d430243-8512-46ee-8d21-7ccf0c7af807

        :expectedresults: User is created with parameters, parameters
                          are updated, user is deleted

        :CaseImportance: Critical
        """
        # create with params
        mail = random.choice(valid_emails_list())
        user_params = {
            'login': random.choice(valid_usernames_list()),
            'firstname': random.choice(valid_usernames_list()),
            'lastname': random.choice(valid_usernames_list()),
            'mail': mail.replace('"', r'\"').replace('`', r'\`'),
            'description': random.choice(list(valid_data_list().values())),
        }
        user = make_user(user_params)
        user['firstname'], user['lastname'] = user['name'].split()
        user_params.pop('mail')
        user_params['email'] = mail
        for key in user_params:
            with self.subTest(key):
                self.assertEqual(
                    user_params[key], user[key], f'values for key "{key}" do not match'
                )

        # list by firstname and lastname
        result = User.list({'search': 'firstname = {}'.format(user_params['firstname'])})
        # make sure user is in list result
        self.assertEqual(
            {user['id'], user['login'], user['name']},
            {result[0]['id'], result[0]['login'], result[0]['name']},
        )
        result = User.list({'search': 'lastname = {}'.format(user_params['lastname'])})
        # make sure user is in list result
        self.assertEqual(
            {user['id'], user['login'], user['name']},
            {result[0]['id'], result[0]['login'], result[0]['name']},
        )

        # update params
        new_mail = random.choice(valid_emails_list())
        user_params = {
            'firstname': random.choice(valid_usernames_list()),
            'lastname': random.choice(valid_usernames_list()),
            'mail': new_mail.replace('"', r'\"').replace('`', r'\`'),
            'description': random.choice(list(valid_data_list().values())),
        }
        user_params.update({'id': user['id']})
        User.update(user_params)
        user = User.info({'login': user['login']})
        user['firstname'], user['lastname'] = user['name'].split()
        user_params.pop('mail')
        user_params['email'] = new_mail
        for key in user_params:
            with self.subTest(key):
                self.assertEqual(
                    user_params[key], user[key], f'values for key "{key}" do not match'
                )

        # delete
        User.delete({'login': user['login']})
        with self.assertRaises(CLIReturnCodeError):
            User.info({'login': user['login']})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.build_sanity
    def test_positive_CRUD_admin(self):
        """Create an Admin user

        :id: 0d0384ad-d85a-492e-8630-7f48912a4fd5

        :expectedresults: Admin User is created, updated, deleted

        :CaseImportance: Critical
        """
        user = make_user({'admin': '1'})
        self.assertEqual(user['admin'], 'yes')
        # update to non admin by id
        User.update({'id': user['id'], 'admin': '0'})
        user = User.info({'id': user['id']})
        self.assertEqual(user['admin'], 'no')
        # update back to admin by name
        User.update({'login': user['login'], 'admin': '1'})
        user = User.info({'login': user['login']})
        self.assertEqual(user['admin'], 'yes')
        # delete user
        User.delete({'login': user['login']})
        with self.assertRaises(CLIReturnCodeError):
            User.info({'id': user['id']})

    @pytest.mark.tier1
    def test_positive_create_with_default_loc(self):
        """Check if user with default location can be created

        :id: efe7256d-8c8f-444c-8d59-43500e1319c3

        :expectedresults: User is created and has new default location assigned

        :CaseImportance: Critical
        """
        location = make_location()
        user = make_user({'default-location-id': location['id'], 'location-ids': location['id']})
        self.assertIn(location['name'], user['locations'])
        self.assertEqual(location['name'], user['default-location'])

    @pytest.mark.tier1
    def test_positive_create_with_defaut_org(self):
        """Check if user with default organization can be created

        :id: cc692b6f-2519-429b-8ecb-c4bb51ed3544

        :expectedresults: User is created and has new default organization
            assigned

        :CaseImportance: Critical
        """
        org = make_org()
        user = make_user({'default-organization-id': org['id'], 'organization-ids': org['id']})
        self.assertIn(org['name'], user['organizations'])
        self.assertEqual(org['name'], user['default-organization'])

    @pytest.mark.tier2
    def test_positive_create_with_orgs_and_update(self):
        """Create User associated to multiple Organizations, update them

        :id: f537296c-a8a8-45ef-8996-c1d32b8f64de

        :expectedresults: User is created with orgs, orgs are updated

        :CaseLevel: Integration
        """
        orgs_amount = 2
        orgs = [make_org() for _ in range(orgs_amount)]
        user = make_user({'organization-ids': [org['id'] for org in orgs]})
        self.assertEqual(len(user['organizations']), orgs_amount)
        for org in orgs:
            self.assertIn(org['name'], user['organizations'])
        orgs = [make_org() for _ in range(orgs_amount)]
        User.update({'id': user['id'], 'organization-ids': [org['id'] for org in orgs]})
        user = User.info({'id': user['id']})
        self.assertItemsEqual(user['organizations'], [org['name'] for org in orgs])

    @pytest.mark.tier1
    def test_negative_delete_internal_admin(self):
        """Attempt to delete internal admin user

        :id: 4fc92958-9e75-4bd2-bcbe-32f906e432f5

        :expectedresults: User is not deleted

        :CaseImportance: Critical
        """
        with self.assertRaisesRegex(CLIReturnCodeError, 'Could not delete the user:'):
            User.delete({'login': self.foreman_user})
        self.assertTrue(User.info({'login': self.foreman_user}))

    @pytest.mark.tier2
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
        result_before_login = User.list({'search': f'login = {login}'})

        # this is because satellite uses the UTC timezone
        before_login_time = datetime.datetime.utcnow()
        assert result_before_login[0]['login'] == login
        assert result_before_login[0]['last-login'] == ""

        Org.with_user(username=login, password=password).create({'name': org_name})
        result_after_login = User.list({'search': f'login = {login}'})

        # checking user last login should not be empty
        assert result_after_login[0]['last-login'] != ""
        after_login_time = datetime.datetime.strptime(
            result_after_login[0]['last-login'], "%Y/%m/%d %H:%M:%S"
        )
        assert after_login_time > before_login_time

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_add_and_delete_roles(self):
        """Add multiple roles to User, then delete them

        For now add-role user sub command does not allow multiple role ids
        (https://github.com/SatelliteQE/robottelo/issues/3729)
        So if if it gets fixed this test can be updated:
        (http://projects.theforeman.org/issues/16206)

        :BZ: 1138553

        :id: d769ac61-f158-4e4e-a176-1c87de8b00f6

        :expectedresults: Roles are added to user and deleted successfully

        :CaseLevel: Integration
        """
        user = make_user()
        original_role_names = set(user['roles'])
        expected_role_names = set(original_role_names)

        for role_id, role in self.stubbed_roles.items():
            User.add_role({'login': user['login'], 'role-id': role_id})
            expected_role_names.add(role['name'])

        self.assertItemsEqual(expected_role_names, User.info({'id': user['id']})['roles'])

        roles_to_remove = expected_role_names - original_role_names
        for role_name in roles_to_remove:
            user_credentials = {'login': user['login'], 'role': role_name}
            User.remove_role(user_credentials)
            user = User.info({'id': user['id']})
            self.assertNotIn(role_name, user['roles'])

        self.assertItemsEqual(original_role_names, User.info({'id': user['id']})['roles'])


class SshKeyInUserTestCase(CLITestCase):
    """Implements the SSH Key in User Tests"""

    def gen_ssh_rsakey(self):
        """Generates RSA type ssh key using ssh module

        :return: string type well formatted RSA key
        """
        return 'ssh-rsa {}'.format(paramiko.RSAKey.generate(2048).get_base64())

    @classmethod
    def setUpClass(cls):
        """Create an user and import different keys from data json file"""
        super().setUpClass()
        cls.user = entities.User().create()

    @pytest.mark.tier1
    def test_positive_CRD_ssh_key(self):
        """SSH Key can be added to a User, listed and deletd

        :id: 57304fca-8e0d-454a-be31-34423345c8b2

        :expectedresults: SSH key should be added to new user,
                          listed and deleted

        :CaseImportance: Critical
        """
        ssh_name = gen_string('alpha')
        ssh_key = self.gen_ssh_rsakey()
        User.ssh_keys_add({'user': self.user.login, 'key': ssh_key, 'name': ssh_name})
        result = User.ssh_keys_list({'user-id': self.user.id})
        self.assertIn(ssh_name, [i['name'] for i in result])
        result = User.ssh_keys_info({'user-id': self.user.id, 'name': ssh_name})
        self.assertEqual(ssh_key, result[0]['public-key'])
        result = User.ssh_keys_delete({'user-id': self.user.id, 'name': ssh_name})
        result = User.ssh_keys_list({'user-id': self.user.id})
        self.assertNotIn(ssh_name, [i['name'] for i in result])

    @pytest.mark.tier1
    def test_positive_create_ssh_key_super_admin_from_file(self):
        """SSH Key can be added to Super Admin user from file

        :id: b865d0ae-6317-475c-a6da-600615b71eeb

        :expectedresults: SSH Key should be added to Super Admin user
                          from ssh pub file

        :CaseImportance: Critical
        """
        ssh_name = gen_string('alpha')
        ssh_key = self.gen_ssh_rsakey()
        with get_connection() as connection:
            result = connection.run(f'''echo '{ssh_key}' > test_key.pub''')
        self.assertEqual(result.return_code, 0, 'key file not created')
        User.ssh_keys_add({'user': 'admin', 'key-file': 'test_key.pub', 'name': ssh_name})
        result = User.ssh_keys_list({'user': 'admin'})
        self.assertIn(ssh_name, [i['name'] for i in result])
        result = User.ssh_keys_info({'user': 'admin', 'name': ssh_name})
        self.assertEqual(ssh_key, result[0]['public-key'])
