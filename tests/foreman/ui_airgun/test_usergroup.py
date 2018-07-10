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
    fixture,
    parametrize,
    run_in_one_thread,
    skip_if_not_set,
    tier2,
    tier3,
    upgrade,
)


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
