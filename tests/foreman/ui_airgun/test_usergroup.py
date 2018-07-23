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

from robottelo.decorators import (
    tier2,
    upgrade,
)


def test_positive_create_with_name(session):
    """Create new Usergroup using different names

    :expectedresults: Usergroup is created successfully

    :CaseImportance: Critical
    """
    group_name = gen_utf8(smp=False)
    with session:
        session.usergroup.create({
            'usergroup.name': group_name,
        })
        assert session.usergroup.search(group_name) is not None


def test_positive_update_name(session):
    """Update usergroup with new name

    :expectedresults: Usergroup is updated

    :CaseImportance: Critical
    """
    group_name = gen_string('alpha')
    new_group_name = gen_utf8(smp=False)
    with session:
        session.usergroup.create({
            'usergroup.name': group_name,
        })
        session.usergroup.update(group_name, {
            'usergroup.name': new_group_name,
        })
        assert session.usergroup.search(new_group_name) is not None
        assert not session.usergroup.search(group_name)


def test_positive_delete_empty(session):
    """Delete an empty Usergroup

    :expectedresults: Usergroup is deleted

    :CaseImportance: Critical
    """
    group_name = gen_utf8(smp=False)
    with session:
        session.usergroup.create({
            'usergroup.name': group_name,
        })
        session.usergroup.delete(group_name)
        assert not session.usergroup.search(group_name)


@tier2
@upgrade
def test_positive_delete_with_user(session, module_org):
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
    ).create()

    with session:
        session.usergroup.create({
            'usergroup.name': group_name,
            'usergroup.users': {'assigned': [user_name]},
        })
        session.usergroup.delete(group_name)
        assert not session.usergroup.search(group_name)
        assert session.user.search(user_name) is not None
