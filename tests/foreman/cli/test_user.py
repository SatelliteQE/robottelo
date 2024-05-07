"""Test class for Users CLI

When testing email validation [1] and [2] should be taken into consideration.

[1] http://tools.ietf.org/html/rfc3696#section-3
[2] https://github.com/theforeman/foreman/pull/1776


:Requirement: User

:CaseAutomation: Automated

:CaseComponent: UsersRoles

:Team: Endeavour

:CaseImportance: High

"""

import datetime
import random
from time import sleep

from fauxfactory import gen_alphanumeric, gen_string
from nailgun import entities
import pytest

from robottelo.config import settings
from robottelo.constants import LOCALES
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils import gen_ssh_keypairs
from robottelo.utils.datafactory import (
    parametrized,
    valid_data_list,
    valid_emails_list,
    valid_usernames_list,
)


class TestUser:
    """Implements Users tests in CLI"""

    @pytest.fixture(scope='module')
    def module_roles(self, module_target_sat):
        """
        Initializes class attribute ``dct_roles`` with several random roles
        saved on sat. roles is a dict so keys are role's id respective value is
        the role itself
        """
        include_list = [gen_string("alphanumeric", 100)]

        def roles_helper():
            """Generator funcion which creates several Roles to be used on
            tests
            """
            for role_name in valid_usernames_list() + include_list:
                yield module_target_sat.cli_factory.make_role({'name': role_name})

        # return stubbed roles
        return {role['id']: role for role in roles_helper()}

    @pytest.mark.parametrize('email', **parametrized(valid_emails_list()))
    @pytest.mark.tier2
    def test_positive_CRUD(self, email, module_target_sat):
        """Create User with various parameters, updating and deleting

        :id: 2d430243-8512-46ee-8d21-7ccf0c7af807

        :expectedresults: User is created with parameters, parameters
                          are updated, user is deleted

        :BZ: 1204667

        :parametrized: yes

        :CaseImportance: Critical
        """
        # create with params
        mail = email
        user_params = {
            'login': random.choice(valid_usernames_list()),
            'firstname': random.choice(valid_usernames_list()),
            'lastname': random.choice(valid_usernames_list()),
            'mail': mail.replace('"', r'\"').replace('`', r'\`'),
            'description': random.choice(list(valid_data_list().values())),
        }
        user = module_target_sat.cli_factory.user(user_params)
        user['firstname'], user['lastname'] = user['name'].split()
        user_params.pop('mail')
        user_params['email'] = mail
        for key in user_params:
            assert user_params[key] == user[key], f'values for key "{key}" do not match'

        # list by firstname and lastname
        result = module_target_sat.cli.User.list(
            {'search': 'firstname = {}'.format(user_params['firstname'])}
        )
        # make sure user is in list result
        assert {user['id'], user['login'], user['name']} == {
            result[0]['id'],
            result[0]['login'],
            result[0]['name'],
        }
        result = module_target_sat.cli.User.list(
            {'search': 'lastname = {}'.format(user_params['lastname'])}
        )
        # make sure user is in list result
        assert {user['id'], user['login'], user['name']} == {
            result[0]['id'],
            result[0]['login'],
            result[0]['name'],
        }
        # update params
        new_mail = random.choice(valid_emails_list())
        user_params = {
            'firstname': random.choice(valid_usernames_list()),
            'lastname': random.choice(valid_usernames_list()),
            'mail': new_mail.replace('"', r'\"').replace('`', r'\`'),
            'description': random.choice(list(valid_data_list().values())),
        }
        user_params.update({'id': user['id']})
        module_target_sat.cli.User.update(user_params)
        user = module_target_sat.cli.User.info({'login': user['login']})
        user['firstname'], user['lastname'] = user['name'].split()
        user_params.pop('mail')
        user_params['email'] = new_mail
        for key in user_params:
            assert user_params[key] == user[key], f'values for key "{key}" do not match'
        # delete
        module_target_sat.cli.User.delete({'login': user['login']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.User.info({'login': user['login']})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_CRUD_admin(self, target_sat):
        """Create an Admin user

        :id: 0d0384ad-d85a-492e-8630-7f48912a4fd5

        :expectedresults: Admin User is created, updated, deleted

        :CaseImportance: Critical
        """
        user = target_sat.cli_factory.user({'admin': '1'})
        assert user['admin'] == 'yes'
        # update to non admin by id
        target_sat.cli.User.update({'id': user['id'], 'admin': '0'})
        user = target_sat.cli.User.info({'id': user['id']})
        assert user['admin'] == 'no'
        # update back to admin by name
        target_sat.cli.User.update({'login': user['login'], 'admin': '1'})
        user = target_sat.cli.User.info({'login': user['login']})
        assert user['admin'] == 'yes'
        # delete user
        target_sat.cli.User.delete({'login': user['login']})
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.User.info({'id': user['id']})

    @pytest.mark.tier1
    def test_positive_create_with_default_loc(self, target_sat):
        """Check if user with default location can be created

        :id: efe7256d-8c8f-444c-8d59-43500e1319c3

        :expectedresults: User is created and has new default location assigned

        :CaseImportance: Critical
        """
        location = target_sat.cli_factory.make_location()
        user = target_sat.cli_factory.user(
            {'default-location-id': location['id'], 'location-ids': location['id']}
        )
        assert location['name'] in user['locations']
        assert location['name'] == user['default-location']

    @pytest.mark.tier1
    def test_positive_create_with_defaut_org(self, module_target_sat):
        """Check if user with default organization can be created

        :id: cc692b6f-2519-429b-8ecb-c4bb51ed3544

        :expectedresults: User is created and has new default organization
            assigned

        :CaseImportance: Critical
        """
        org = module_target_sat.cli_factory.make_org()
        user = module_target_sat.cli_factory.user(
            {'default-organization-id': org['id'], 'organization-ids': org['id']}
        )
        assert org['name'] in user['organizations']
        assert org['name'] == user['default-organization']

    @pytest.mark.tier2
    def test_positive_create_with_orgs_and_update(self, module_target_sat):
        """Create User associated to multiple Organizations, update them

        :id: f537296c-a8a8-45ef-8996-c1d32b8f64de

        :expectedresults: User is created with orgs, orgs are updated

        """
        orgs_amount = 2
        orgs = [module_target_sat.cli_factory.make_org() for _ in range(orgs_amount)]
        user = module_target_sat.cli_factory.user({'organization-ids': [org['id'] for org in orgs]})
        assert len(user['organizations']) == orgs_amount
        for org in orgs:
            assert org['name'] in user['organizations']
        orgs = [module_target_sat.cli_factory.make_org() for _ in range(orgs_amount)]
        module_target_sat.cli.User.update(
            {'id': user['id'], 'organization-ids': [org['id'] for org in orgs]}
        )
        user = module_target_sat.cli.User.info({'id': user['id']})
        for org in orgs:
            assert org['name'] in user['organizations']

    @pytest.mark.tier1
    def test_negative_delete_internal_admin(self, module_target_sat):
        """Attempt to delete internal admin user

        :id: 4fc92958-9e75-4bd2-bcbe-32f906e432f5

        :expectedresults: User is not deleted

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.User.delete({'login': settings.server.admin_username})
        assert module_target_sat.cli.User.info({'login': settings.server.admin_username})

    @pytest.mark.tier2
    def test_positive_last_login_for_new_user(self, module_target_sat):
        """Create new user with admin role and check last login updated for that user

        :id: 967282d3-92d0-42ce-9ef3-e542d2883408

        :customerscenario: true

        :expectedresults: last login should be updated for user after login using hammer

        :BZ: 1763816

        """
        login = gen_string('alpha')
        password = gen_string('alpha')
        org_name = gen_string('alpha')

        module_target_sat.cli_factory.user({'login': login, 'password': password})
        module_target_sat.cli.User.add_role({'login': login, 'role': 'System admin'})
        result_before_login = module_target_sat.cli.User.list({'search': f'login = {login}'})

        # this is because satellite uses the UTC timezone
        before_login_time = datetime.datetime.utcnow()
        assert result_before_login[0]['login'] == login
        assert result_before_login[0]['last-login'] == ""

        module_target_sat.cli.Org.with_user(username=login, password=password).create(
            {'name': org_name}
        )
        result_after_login = module_target_sat.cli.User.list({'search': f'login = {login}'})

        # checking user last login should not be empty
        assert result_after_login[0]['last-login'] != ""
        after_login_time = datetime.datetime.strptime(
            result_after_login[0]['last-login'], "%Y/%m/%d %H:%M:%S"
        )
        assert after_login_time > before_login_time

    @pytest.mark.tier1
    def test_positive_update_all_locales(self, module_target_sat):
        """Update Language in My Account

        :id: f0993495-5117-461d-a116-44867b820139

        :steps: Update current User with all different Language options

        :expectedresults: Current User is updated

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        user = module_target_sat.cli_factory.user()
        for locale in LOCALES:
            module_target_sat.cli.User.update({'id': user['id'], 'locale': locale})
            assert locale == module_target_sat.cli.User.info({'id': user['id']})['locale']

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_add_and_delete_roles(self, module_roles, module_target_sat):
        """Add multiple roles to User, then delete them

        For now add-role user sub command does not allow multiple role ids
        (https://github.com/SatelliteQE/robottelo/issues/3729)
        So if if it gets fixed this test can be updated:
        (http://projects.theforeman.org/issues/16206)

        :BZ: 1138553

        :id: d769ac61-f158-4e4e-a176-1c87de8b00f6

        :expectedresults: Roles are added to user and deleted successfully

        """
        user = module_target_sat.cli_factory.user()
        original_role_names = set(user['roles'])
        expected_role_names = set(original_role_names)

        for role_id, role in module_roles.items():
            module_target_sat.cli.User.add_role({'login': user['login'], 'role-id': role_id})
            expected_role_names.add(role['name'])

        user_roles = module_target_sat.cli.User.info({'id': user['id']})['roles']
        assert len(expected_role_names) == len(user_roles)
        for role in expected_role_names:
            assert role in user_roles

        roles_to_remove = expected_role_names - original_role_names
        for role_name in roles_to_remove:
            user_credentials = {'login': user['login'], 'role': role_name}
            module_target_sat.cli.User.remove_role(user_credentials)
            user = module_target_sat.cli.User.info({'id': user['id']})
            assert role_name not in user['roles']

        user_roles = module_target_sat.cli.User.info({'id': user['id']})['roles']
        assert len(original_role_names) == len(user_roles)
        for role in original_role_names:
            assert role in user_roles


class TestSshKeyInUser:
    """Implements the SSH Key in User Tests"""

    ssh_key = gen_ssh_keypairs()[1]

    @pytest.fixture(scope='module')
    def module_user(self):
        """Create an user"""
        return entities.User().create()

    @pytest.mark.tier1
    def test_positive_CRD_ssh_key(self, module_user, module_target_sat):
        """SSH Key can be added to a User, listed and deletd

        :id: 57304fca-8e0d-454a-be31-34423345c8b2

        :expectedresults: SSH key should be added to new user,
                          listed and deleted

        :CaseImportance: Critical
        """
        ssh_name = gen_string('alpha')
        module_target_sat.cli.User.ssh_keys_add(
            {'user': module_user.login, 'key': self.ssh_key, 'name': ssh_name}
        )
        result = module_target_sat.cli.User.ssh_keys_list({'user-id': module_user.id})
        assert ssh_name in [i['name'] for i in result]
        result = module_target_sat.cli.User.ssh_keys_info(
            {'user-id': module_user.id, 'name': ssh_name}
        )
        assert self.ssh_key in result[0]['public-key']
        result = module_target_sat.cli.User.ssh_keys_delete(
            {'user-id': module_user.id, 'name': ssh_name}
        )
        result = module_target_sat.cli.User.ssh_keys_list({'user-id': module_user.id})
        assert ssh_name not in [i['name'] for i in result]

    @pytest.mark.tier1
    def test_positive_create_ssh_key_super_admin_from_file(self, target_sat):
        """SSH Key can be added to Super Admin user from file

        :id: b865d0ae-6317-475c-a6da-600615b71eeb

        :expectedresults: SSH Key should be added to Super Admin user
                          from ssh pub file

        :CaseImportance: Critical
        """
        ssh_name = gen_string('alpha')
        result = target_sat.execute(f"echo '{self.ssh_key}' > test_key.pub")
        assert result.status == 0, 'key file not created'
        target_sat.cli.User.ssh_keys_add(
            {'user': 'admin', 'key-file': 'test_key.pub', 'name': ssh_name}
        )
        result = target_sat.cli.User.ssh_keys_list({'user': 'admin'})
        assert ssh_name in [i['name'] for i in result]
        result = target_sat.cli.User.ssh_keys_info({'user': 'admin', 'name': ssh_name})
        assert self.ssh_key == result[0]['public-key']


class TestPersonalAccessToken:
    """Implement personal access token for the users"""

    @pytest.mark.tier2
    def test_personal_access_token_admin_user(self, target_sat):
        """Personal access token for admin user

        :id: f2d3813f-e477-4b6b-8507-246b08fcb3b4

        :steps:
            1. Create an admin user and add personal access token
            2. Use any api endpoint with the token
            3. Revoke the token and check for the result.

        :expectedresults:
            1. Should show output of the api endpoint
            2. When revoked, authentication error

        :CaseImportance: High
        """
        user = target_sat.cli_factory.user({'admin': '1'})
        token_name = gen_alphanumeric()
        result = target_sat.cli.User.access_token(
            action="create", options={'name': token_name, 'user-id': user['id']}
        )
        token_value = result[0]['message'].split(':')[-1]
        curl_command = f'curl -k -u {user["login"]}:{token_value} {target_sat.url}/api/v2/users'
        command_output = target_sat.execute(curl_command)
        assert user['login'] in command_output.stdout
        assert user['email'] in command_output.stdout
        target_sat.cli.User.access_token(
            action="revoke", options={'name': token_name, 'user-id': user['id']}
        )
        command_output = target_sat.execute(curl_command)
        assert f'Unable to authenticate user {user["login"]}' in command_output.stdout

    @pytest.mark.tier2
    def test_positive_personal_access_token_user_with_role(self, target_sat):
        """Personal access token for user with a role

        :id: b9fe7ddd-d1e4-4d76-9966-d223b02768ec

        :steps:
            1. Create a new user. Assign a role to it and create personal
               access token
            2. Use an api endpoint to that specific role and other roles.
            3. Revoke the access token

        :expectedresults:
            1. When used with the correct role and end point, corresponding
               output should be displayed.
            2. When an incorrect end point is used, missing
               permission should be displayed.

        :CaseImportance: High
        """
        user = target_sat.cli_factory.user()
        target_sat.cli.User.add_role({'login': user['login'], 'role': 'Viewer'})
        token_name = gen_alphanumeric()
        result = target_sat.cli.User.access_token(
            action="create", options={'name': token_name, 'user-id': user['id']}
        )
        token_value = result[0]['message'].split(':')[-1]
        command_output = target_sat.execute(
            f'curl -k -u {user["login"]}:{token_value} {target_sat.url}/api/v2/users'
        )
        assert user['login'] in command_output.stdout
        assert user['email'] in command_output.stdout
        command_output = target_sat.execute(
            f'curl -k -u {user["login"]}:{token_value} {target_sat.url}/api/dashboard'
        )
        assert 'Access denied' in command_output.stdout

    @pytest.mark.tier2
    def test_expired_personal_access_token(self, target_sat):
        """Personal access token expired for the user.

        :id: cb07b096-aba4-4a95-9a15-5413f32b597b

        :steps:
            1. Set the expired time to +x seconds from the current time.
            2. Wait +x seconds
            3. Try using the token with any end point.

        :expectedresults: Authentication error

        :CaseImportance: Medium
        """
        user = target_sat.cli_factory.user()
        target_sat.cli.User.add_role({'login': user['login'], 'role': 'Viewer'})
        token_name = gen_alphanumeric()
        datetime_now = datetime.datetime.utcnow()
        datetime_expire = datetime_now + datetime.timedelta(seconds=20)
        datetime_expire = datetime_expire.strftime("%Y-%m-%d %H:%M:%S")
        result = target_sat.cli.User.access_token(
            action="create",
            options={'name': token_name, 'user-id': user['id'], 'expires-at': datetime_expire},
        )
        token_value = result[0]['message'].split(':')[-1]
        command_output = target_sat.execute(
            f'curl -k -u {user["login"]}:{token_value} {target_sat.url}/api/v2/users'
        )
        assert user['login'] in command_output.stdout
        assert user['email'] in command_output.stdout
        sleep(20)
        command_output = target_sat.execute(
            f'curl -k -u {user["login"]}:{token_value} {target_sat.url}/api/v2/hosts'
        )
        assert f'Unable to authenticate user {user["login"]}' in command_output.stdout

    @pytest.mark.tier2
    def test_custom_personal_access_token_role(self, target_sat):
        """Personal access token for non admin user with custom role

        :id: dcbd22df-2641-4d3e-a1ad-76f36642e31b

        :steps:
            1. Create role with PAT and View Users
            2. Create non admin user and assign the role
            3. Create PAT for the user and test with the end point
            4. Revoke the token and then test for end point.

        :expectedresults: Non admin user is able to view only the assigned entity

        :CaseImportance: High

        :BZ: 1974685, 1996048
        """
        role = target_sat.cli_factory.make_role()
        permissions = [
            permission['name']
            for permission in target_sat.cli.Filter.available_permissions(
                {'search': 'resource_type=PersonalAccessToken'}
            )
        ]
        permissions = ','.join(permissions)
        target_sat.cli_factory.make_filter({'role-id': role['id'], 'permissions': permissions})
        target_sat.cli_factory.make_filter({'role-id': role['id'], 'permissions': 'view_users'})
        user = target_sat.cli_factory.user()
        target_sat.cli.User.add_role({'login': user['login'], 'role': role['name']})
        token_name = gen_alphanumeric()
        result = target_sat.cli.User.access_token(
            action="create", options={'name': token_name, 'user-id': user['id']}
        )
        token_value = result[0]['message'].split(':')[-1]
        command_output = target_sat.execute(
            f'curl -k -u {user["login"]}:{token_value} {target_sat.url}/api/v2/users'
        )
        assert user['login'] in command_output.stdout
        assert user['email'] in command_output.stdout
        target_sat.cli.User.access_token(
            action="revoke", options={'name': token_name, 'user-id': user['id']}
        )
        command_output = target_sat.execute(
            f'curl -k -u {user["login"]}:{token_value} {target_sat.url}/api/v2/users'
        )
        assert f'Unable to authenticate user {user["login"]}' in command_output.stdout

    @pytest.mark.tier2
    def test_negative_personal_access_token_invalid_date(self, target_sat):
        """Personal access token with invalid expire date.

        :id: 8c7c91c5-f6d9-4709-857c-6a875db41b88

        :steps:
            1. Set the expired time to a nonsensical datetime
            2. Set the expired time to a past datetime

        :expectedresults: token is not created with invalid or past expire time

        :CaseImportance: Medium

        :BZ: 2231814
        """
        user = target_sat.cli_factory.user()
        target_sat.cli.User.add_role({'login': user['login'], 'role': 'Viewer'})
        token_name = gen_alphanumeric()
        # check for invalid datetime
        invalid_datetimes = ['00-14-00 09:30:55', '2028-08-22 28:30:55', '0000-00-22 15:90:55']
        for datetime_expire in invalid_datetimes:
            with pytest.raises(CLIReturnCodeError):
                target_sat.cli.User.access_token(
                    action='create',
                    options={
                        'name': token_name,
                        'user-id': user['id'],
                        'expires-at': datetime_expire,
                    },
                )
        # check for past datetime
        datetime_now = datetime.datetime.utcnow()
        datetime_expire = datetime_now - datetime.timedelta(seconds=20)
        datetime_expire = datetime_expire.strftime("%Y-%m-%d %H:%M:%S")
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.User.access_token(
                action='create',
                options={'name': token_name, 'user-id': user['id'], 'expires-at': datetime_expire},
            )
