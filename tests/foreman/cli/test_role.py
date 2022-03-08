"""Test for Roles CLI

:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Assignee: sganar

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re
from math import ceil
from random import choice

import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIDataBaseError
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_filter
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.filter import Filter
from robottelo.cli.role import Role
from robottelo.cli.settings import Settings
from robottelo.cli.user import User
from robottelo.constants import PERMISSIONS
from robottelo.constants import ROLES
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import parametrized


class TestRole:
    """Test class for Roles CLI"""

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'name, new_name',
        **parametrized(
            list(zip(generate_strings_list(length=10), generate_strings_list(length=10)))
        ),
    )
    def test_positive_crud_with_name(self, name, new_name):
        """Create new role with provided name, update name and delete role by ID

        :id: f77b8e84-e964-4007-b12b-142949134d8b

        :parametrized: yes

        :expectedresults: Role is created and has correct name, its name is updated
            and then deleted by ID

        :BZ: 1138553

        :CaseImportance: Critical
        """
        role = make_role({'name': name})
        assert role['name'] == name
        Role.update({'id': role['id'], 'new-name': new_name})
        role = Role.info({'id': role['id']})
        assert role['name'] == new_name
        Role.delete({'id': role['id']})
        with pytest.raises(CLIReturnCodeError):
            Role.info({'id': role['id']})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.build_sanity
    def test_positive_create_with_permission(self):
        """Create new role with a set of permission

        :id: 7cb2b2e2-ad4d-41e9-b6b2-c0366eb09b9a

        :expectedresults: Role is created and has correct set of permissions

        :CaseImportance: Critical
        """
        role = make_role()
        # Pick permissions by its resource type
        permissions = [
            permission['name']
            for permission in Filter.available_permissions({"search": "resource_type=Organization"})
        ]
        # Assign filter to created role
        make_filter({'role-id': role['id'], 'permissions': permissions})
        assert set(Role.filters({'id': role['id']})[0]['permissions']) == set(permissions)

    @pytest.mark.tier1
    def test_positive_list_filters_by_id(self):
        """Create new role with a filter and list it by role id

        :id: 6979ad8d-629b-481e-9d3a-8f3b3bca53f9

        :expectedresults: Filter is listed for specified role

        :CaseImportance: Critical
        """
        role = make_role()
        # Pick permissions by its resource type
        permissions = [
            permission['name']
            for permission in Filter.available_permissions({"search": "resource_type=Organization"})
        ]
        # Assign filter to created role
        filter_ = make_filter({'role-id': role['id'], 'permissions': permissions})
        assert role['name'] == filter_['role']
        assert Role.filters({'id': role['id']})[0]['id'] == filter_['id']

    @pytest.mark.tier1
    def test_positive_list_filters_by_name(self):
        """Create new role with a filter and list it by role name

        :id: bbcb3982-f484-4dde-a3ea-7145fd28ab1f

        :expectedresults: Filter is listed for specified role

        :CaseImportance: Critical
        """
        role = make_role()
        # Pick permissions by its resource type
        permissions = [
            permission['name']
            for permission in Filter.available_permissions({"search": "resource_type=Organization"})
        ]
        # Assign filter to created role
        filter_ = make_filter({'role': role['name'], 'permissions': permissions})
        assert role['name'] == filter_['role']
        assert Role.filters({'name': role['name']})[0]['id'] == filter_['id']

    @pytest.mark.tier1
    def test_negative_list_filters_without_parameters(self):
        """Try to list filter without specifying role id or name

        :id: 56cafbe0-d1cb-413e-8eac-0e01a3590fd2

        :expectedresults: Proper error message is shown instead of SQL error

        :CaseImportance: Critical

        :BZ: 1296782
        """
        with pytest.raises(CLIReturnCodeError) as err:
            try:
                Role.filters()
            except CLIDataBaseError as err:
                pytest.fail(err)
        assert re.search('At least one of options .* is required', err.value.msg)

    @pytest.fixture()
    def make_role_with_permissions(self):
        """Create new role with a filter"""
        role = make_role()
        res_types = iter(PERMISSIONS.keys())
        permissions = []
        # Collect more than 20 different permissions
        while len(permissions) <= 20:
            permissions += [
                permission['name']
                for permission in Filter.available_permissions(
                    {"search": f"resource_type={next(res_types)}"}
                )
            ]
        # Create a filter for each permission
        for perm in permissions:
            make_filter({'role': role['name'], 'permissions': perm})
        return {
            'role': role,
            'permissions': permissions,
        }

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize('per_page', [1, 5, 20])
    def test_positive_list_filters_with_pagination(self, make_role_with_permissions, per_page):
        """Make sure filters list can be displayed with different items per
        page value

        :id: b9c7c6c1-70c2-4d7f-8d36-fa8613acc865

        :BZ: 1428516

        :expectedresults: `per-page` correctly sets amount of items displayed
            per page, different `per-page` values divide a list into correct
            number of pages

        :CaseImportance: Critical

        :parametrized: yes
        """
        # Verify the first page contains exactly the same items count
        # as `per-page` value
        filters = Role.filters(
            {'name': make_role_with_permissions['role']['name'], 'per-page': per_page}
        )
        assert len(filters) == per_page
        # Verify pagination and total amount of pages by checking the
        # items count on the last page
        last_page = ceil(len(make_role_with_permissions['permissions']) / per_page)
        filters = Role.filters(
            {
                'name': make_role_with_permissions['role']['name'],
                'page': last_page,
                'per-page': per_page,
            }
        )
        assert len(filters) == (
            len(make_role_with_permissions['permissions']) % per_page or per_page
        )

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_delete_cloned_builtin(self):
        """Clone a builtin role and attempt to delete it

        :id: 1fd9c636-596a-4cb2-b100-de19238042cc

        :BZ: 1426672

        :expectedresults: role was successfully deleted

        :CaseImportance: Critical

        """
        role_list = Role.list({'search': f'name=\\"{choice(ROLES)}\\"'})
        assert len(role_list) == 1
        cloned_role = Role.clone({'id': role_list[0]['id'], 'new-name': gen_string('alphanumeric')})
        Role.delete({'id': cloned_role['id']})
        with pytest.raises(CLIReturnCodeError):
            Role.info({'id': cloned_role['id']})


class TestSystemAdmin:
    """Test class for System Admin role end to end CLI"""

    @pytest.fixture(scope='class', autouse=True)
    def tearDown(self):
        """Will reset the changed value of settings"""
        yield
        Settings.set({'name': "outofsync_interval", 'value': "30"})

    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_system_admin_role_end_to_end(self):
        """Test System admin role with a end to end workflow

        :id: da6b3549-d1cf-44fc-869f-08d15d407fa2

        :steps:

            1. Create a System admin role user1
            2. Login with the user1 and change global settings
                "Out of sync interval" to 31
            3. Create user2 with system admin role
            4. Login with user2 to create a Organization
            5. Clone a Org-admin role
            6. Edit the Architecture Filter and search name  =  x86_64
            7. Create a User with Cloned Org admin
            8. Login with user.

        :expectedresults:

            1. User should be assigned with System Admin role.
            2. User with sys admin role should be able to update settings
            3. User with sys admin role should be able to create users and
                assign Organizations to them.
            4. System Admin role should be able to create Organization admins
            5. User with sys admin role should be able to edit filters on roles

        :CaseLevel: System
        """
        org = make_org()
        location = make_location()
        common_pass = gen_string('alpha')
        role = Role.info({'name': 'System admin'})
        system_admin_1 = make_user(
            {
                'password': common_pass,
                'organization-ids': org['id'],
                'location-ids': location['id'],
            }
        )
        User.add_role({'id': system_admin_1['id'], 'role-id': role['id']})
        Settings.with_user(username=system_admin_1['login'], password=common_pass).set(
            {'name': "outofsync_interval", 'value': "32"}
        )
        sync_time = Settings.list({'search': 'name=outofsync_interval'})[0]
        # Asserts if the setting was updated successfully
        assert '32' == sync_time['value']

        # Create another System Admin user using the first one
        system_admin = User.with_user(
            username=system_admin_1['login'], password=common_pass
        ).create(
            {
                'auth-source-id': 1,
                'firstname': gen_string('alpha'),
                'lastname': gen_string('alpha'),
                'login': gen_string('alpha'),
                'mail': '{}@example.com'.format(gen_string('alpha')),
                'password': common_pass,
                'organizations': org['name'],
                'role-ids': role['id'],
                'locations': location['name'],
            }
        )
        # Create the Org Admin user
        org_role = Role.with_user(username=system_admin['login'], password=common_pass).clone(
            {
                'name': 'Organization admin',
                'new-name': gen_string('alpha'),
                'organization-ids': org['id'],
                'location-ids': location['id'],
            }
        )
        org_admin = User.with_user(username=system_admin['login'], password=common_pass).create(
            {
                'auth-source-id': 1,
                'firstname': gen_string('alpha'),
                'lastname': gen_string('alpha'),
                'login': gen_string('alpha'),
                'mail': '{}@example.com'.format(gen_string('alpha')),
                'password': common_pass,
                'organizations': org['name'],
                'role-ids': org_role['id'],
                'location-ids': location['id'],
            }
        )
        # Assert if the cloning was successful
        assert org_role['id'] is not None
        org_role_filters = Role.filters({'id': org_role['id']})
        search_filter = None
        for arch_filter in org_role_filters:
            if arch_filter['resource-type'] == 'Architecture':
                search_filter = arch_filter
                break
        Filter.with_user(username=system_admin['login'], password=common_pass).update(
            {'role-id': org_role['id'], 'id': arch_filter['id'], 'search': 'name=x86_64'}
        )
        # Asserts if the filter is updated
        assert 'name=x86_64' in Filter.info({'id': search_filter['id']}).values()
        org_admin = User.with_user(username=system_admin['login'], password=common_pass).info(
            {'id': org_admin['id']}
        )
        # Asserts Created Org Admin
        assert org_role['name'] in org_admin['roles']
        assert org['name'] in org_admin['organizations']
