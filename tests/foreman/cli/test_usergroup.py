"""Test class for User Group CLI

:Requirement: Usergroup

:CaseAutomation: Automated

:CaseComponent: UsersRoles

:Team: Endeavour

:CaseImportance: High

"""

import random

import pytest

from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import valid_usernames_list


@pytest.fixture
def function_user_group(target_sat):
    """Create new usergroup per each test"""
    return target_sat.cli_factory.usergroup()


@pytest.mark.tier1
def test_positive_CRUD(module_target_sat):
    """Create new user group with valid elements that attached group.
       List the user group, update and delete it.

    :id: bacef0e3-31dd-4991-93f7-f54fbe64d0f0

    :expectedresults: User group is created, listed, updated and
         deleted successfully.

    :CaseImportance: Critical
    """
    user = module_target_sat.cli_factory.user()
    ug_name = random.choice(valid_usernames_list())
    role_name = random.choice(valid_usernames_list())
    role = module_target_sat.cli_factory.make_role({'name': role_name})
    sub_user_group = module_target_sat.cli_factory.usergroup()

    # Create
    user_group = module_target_sat.cli_factory.usergroup(
        {
            'user-ids': user['id'],
            'name': ug_name,
            'role-ids': role['id'],
            'user-group-ids': sub_user_group['id'],
        }
    )

    assert user_group['name'] == ug_name
    assert user_group['users'][0] == user['login']
    assert len(user_group['roles']) == 1
    assert user_group['roles'][0] == role_name
    assert user_group['user-groups'][0]['usergroup'] == sub_user_group['name']

    # List
    result_list = module_target_sat.cli.UserGroup.list(
        {'search': 'name={}'.format(user_group['name'])}
    )
    assert len(result_list) > 0
    assert module_target_sat.cli.UserGroup.exists(search=('name', user_group['name']))

    # Update
    new_name = random.choice(valid_usernames_list())
    module_target_sat.cli.UserGroup.update({'id': user_group['id'], 'new-name': new_name})
    user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
    assert user_group['name'] == new_name

    # Delete
    module_target_sat.cli.UserGroup.delete({'name': user_group['name']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.UserGroup.info({'name': user_group['name']})


@pytest.mark.tier1
def test_positive_create_with_multiple_elements(module_target_sat):
    """Create new user group using multiple users, roles and user
       groups attached to that group.

    :id: 3b0a3c3c-aab2-4e8a-b043-7462621c7333

    :expectedresults: User group is created successfully and contains all
        expected elements.

    :CaseImportance: Critical
    """
    count = 2
    users = [module_target_sat.cli_factory.user()['login'] for _ in range(count)]
    roles = [module_target_sat.cli_factory.make_role()['name'] for _ in range(count)]
    sub_user_groups = [module_target_sat.cli_factory.usergroup()['name'] for _ in range(count)]
    user_group = module_target_sat.cli_factory.usergroup(
        {'users': users, 'roles': roles, 'user-groups': sub_user_groups}
    )
    assert sorted(users) == sorted(user_group['users'])
    assert sorted(roles) == sorted(user_group['roles'])
    assert sorted(sub_user_groups) == sorted(ug['usergroup'] for ug in user_group['user-groups'])


@pytest.mark.tier2
def test_positive_add_and_remove_elements(module_target_sat):
    """Create new user group. Add and remove several element from the group.

    :id: a4ce8724-d3c8-4c00-9421-aaa40394134d

    :BZ: 1395229

    :expectedresults: Elements are added to user group and then removed
                      successfully.
    """
    role = module_target_sat.cli_factory.make_role()
    user_group = module_target_sat.cli_factory.usergroup()
    user = module_target_sat.cli_factory.user()
    sub_user_group = module_target_sat.cli_factory.usergroup()

    # Add elements by id
    module_target_sat.cli.UserGroup.add_role({'id': user_group['id'], 'role-id': role['id']})
    module_target_sat.cli.UserGroup.add_user({'id': user_group['id'], 'user-id': user['id']})
    module_target_sat.cli.UserGroup.add_user_group(
        {'id': user_group['id'], 'user-group-id': sub_user_group['id']}
    )

    user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
    assert len(user_group['roles']) == 1
    assert user_group['roles'][0] == role['name']
    assert len(user_group['users']) == 1
    assert user_group['users'][0] == user['login']
    assert len(user_group['user-groups']) == 1
    assert user_group['user-groups'][0]['usergroup'] == sub_user_group['name']

    # Remove elements by name
    module_target_sat.cli.UserGroup.remove_role({'id': user_group['id'], 'role': role['name']})
    module_target_sat.cli.UserGroup.remove_user({'id': user_group['id'], 'user': user['login']})
    module_target_sat.cli.UserGroup.remove_user_group(
        {'id': user_group['id'], 'user-group': sub_user_group['name']}
    )

    user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
    assert len(user_group['roles']) == 0
    assert len(user_group['users']) == 0
    assert len(user_group['user-groups']) == 0


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_remove_user_assigned_to_usergroup(module_target_sat):
    """Create new user and assign it to user group. Then remove that user.

    :id: 2a2623ce-4723-4402-aae7-8675473fd8bd

    :expectedresults: User should delete successfully.

    :customerscenario: true

    :BZ: 1667704
    """
    user = module_target_sat.cli_factory.user()
    user_group = module_target_sat.cli_factory.usergroup()
    module_target_sat.cli.UserGroup.add_user({'id': user_group['id'], 'user-id': user['id']})
    module_target_sat.cli.User.delete({'id': user['id']})
    user_group = module_target_sat.cli.UserGroup.info({'id': user_group['id']})
    assert user['login'] not in user_group['users']


@pytest.mark.tier2
@pytest.mark.parametrize("ldap_auth_source", ["AD"], indirect=True)
def test_positive_automate_bz1426957(ldap_auth_source, function_user_group, target_sat):
    """Verify role is properly reflected on AD user.

    :id: 1c1209a6-5bb8-489c-a151-bb2fce4dbbfc

    :parametrized: yes

    :expectedresults: Roles from usergroup is applied on AD user successfully.

    :customerscenario: true

    :BZ: 1426957, 1667704
    """
    ext_user_group = target_sat.cli_factory.usergroup_external(
        {
            'auth-source-id': ldap_auth_source[1].id,
            'user-group-id': function_user_group['id'],
            'name': 'foobargroup',
        }
    )
    assert ext_user_group['auth-source'] == ldap_auth_source[1].name
    role = target_sat.cli_factory.make_role()
    target_sat.cli.UserGroup.add_role({'id': function_user_group['id'], 'role-id': role['id']})
    target_sat.cli.Task.with_user(
        username=ldap_auth_source[0]['ldap_user_name'],
        password=ldap_auth_source[0]['ldap_user_passwd'],
    ).list()
    target_sat.cli.UserGroupExternal.refresh(
        {'user-group-id': function_user_group['id'], 'name': 'foobargroup'}
    )
    assert (
        role['name']
        in target_sat.cli.User.info({'login': ldap_auth_source[0]['ldap_user_name']})['user-groups']
    )
    target_sat.cli.User.delete({'login': ldap_auth_source[0]['ldap_user_name']})
    target_sat.cli.LDAPAuthSource.delete({'id': ldap_auth_source[1].id})


@pytest.mark.tier2
@pytest.mark.parametrize("ldap_auth_source", ["AD"], indirect=True)
def test_negative_automate_bz1437578(ldap_auth_source, function_user_group, module_target_sat):
    """Verify error message on usergroup create with 'Domain Users' on AD user.

    :id: d4caf33e-b9eb-4281-9e04-fbe1d5b035dc

    :parametrized: yes

    :expectedresults: Error message as Domain Users is a special group in AD.

    :BZ: 1437578
    """
    with pytest.raises(CLIReturnCodeError):
        result = module_target_sat.cli.UserGroupExternal.create(
            {
                'auth-source-id': ldap_auth_source[1].id,
                'user-group-id': function_user_group['id'],
                'name': 'Domain Users',
            }
        )
    assert (
        result == 'Could not create external user group: '
        'Name is not found in the authentication source'
        'Name Domain Users is a special group in AD.'
        ' Unfortunately, we cannot obtain membership information'
        ' from a LDAP search and therefore sync it.'
    )
