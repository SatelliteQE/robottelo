"""Test class for UserGroup UI

:Requirement: Usergroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Assignee: sganar

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from fauxfactory import gen_utf8
from nailgun import entities


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_with_user(session, module_org, module_loc):
    """Delete a Usergroup that contains a user

    :id: 2bda3db5-f54f-412f-831f-8e005631f271

    :expectedresults: Usergroup is deleted but added user is not

    :CaseLevel: Integration
    """
    user_name = gen_string('alpha')
    group_name = gen_utf8(smp=False)
    # Create a new user
    entities.User(
        login=user_name,
        password=gen_string('alpha'),
        organization=[module_org],
        location=[module_loc],
    ).create()
    with session:
        session.usergroup.create(
            {'usergroup.name': group_name, 'usergroup.users': {'assigned': [user_name]}}
        )
        session.usergroup.delete(group_name)
        assert not session.usergroup.search(group_name)
        assert session.user.search(user_name) is not None


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for usergroup component

    :id: c1c7c383-b118-4caf-a5ef-4e75fdbbacdc

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    user = entities.User(
        password=gen_string('alpha'), organization=[module_org], location=[module_loc]
    ).create()
    user_group = entities.UserGroup().create()
    with session:
        # Create new user group with assigned entities
        session.usergroup.create(
            {
                'usergroup.name': name,
                'usergroup.users': {'assigned': [user.login]},
                'usergroup.usergroups': {'assigned': [user_group.name]},
                'roles.admin': True,
                'roles.resources': {'assigned': ['Viewer']},
            }
        )
        assert session.usergroup.search(name)[0]['Name'] == name
        usergroup_values = session.usergroup.read(name)
        assert usergroup_values['usergroup']['name'] == name
        assert usergroup_values['usergroup']['usergroups']['assigned'][0] == user_group.name
        assert usergroup_values['usergroup']['users']['assigned'][0] == user.login
        assert usergroup_values['roles']['admin'] is True
        assert usergroup_values['roles']['resources']['assigned'][0] == 'Viewer'
        # Update user group with new name
        session.usergroup.update(name, {'usergroup.name': new_name})
        assert session.usergroup.search(new_name)[0]['Name'] == new_name
        # Delete user group
        session.usergroup.delete(new_name)
        assert not session.usergroup.search(new_name)
