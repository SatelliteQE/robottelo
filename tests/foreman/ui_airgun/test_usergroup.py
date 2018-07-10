# -*- encoding: utf-8 -*-
"""Test class for UserGroup UI

:Requirement: Usergroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string, gen_utf8
from nailgun import entities

from robottelo.datafactory import generate_strings_list
from robottelo.decorators import (
    parametrize,
    tier1,
    tier2,
    upgrade,
)


@tier1
@parametrize("group_name", generate_strings_list())
def test_positive_create_with_name(session, group_name):
    """Create new Usergroup using different names

    :id: 43e70c8d-455e-4da8-9c69-ab80dae2a0bc

    :expectedresults: Usergroup is created successfully

    :CaseImportance: Critical
    """
    with session:
        session.usergroup.create({
            'usergroup.name': group_name,
        })
        assert session.usergroup.search(group_name) is not None


@tier1
@parametrize("new_group_name", generate_strings_list())
def test_positive_update_name(session, new_group_name):
    """Update usergroup with new name

    :id: 2f49ab7c-2f11-48c0-99c2-448fc86b5ad2

    :expectedresults: Usergroup is updated

    :CaseImportance: Critical
    """
    group_name = gen_string('alpha')
    with session:
        session.usergroup.create({
            'usergroup.name': group_name,
        })
        session.usergroup.update(group_name, {
            'usergroup.name': new_group_name,
        })
        assert session.usergroup.search(new_group_name) is not None


@tier1
@parametrize("group_name", generate_strings_list())
def test_positive_delete_empty(session, group_name):
    """Delete an empty Usergroup

    :id: ca82f84b-bc5a-4f7d-b70d-9ee3e1b0fffa

    :expectedresults: Usergroup is deleted

    :CaseImportance: Critical
    """
    with session:
        session.usergroup.create({
            'usergroup.name': group_name,
        })
        session.usergroup.delete(group_name)
        assert session.usergroup.search(group_name) == []


@tier2
@upgrade
def test_positive_delete_with_user(session, module_org):
    """Delete an Usergroup that contains a user

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
    ).create()

    with session:
        session.usergroup.create({
            'usergroup.name': group_name,
            'usergroup.users': {'assigned': [user_name]},
        })
        session.usergroup.delete(group_name)
        assert session.user.search(user_name) is not None
