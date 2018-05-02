"""Test class for User UI

:Requirement: User

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random
from nailgun import entities

from robottelo.constants import DEFAULT_ORG, ROLES
from robottelo.datafactory import gen_string
from robottelo.decorators import tier2


@tier2
def test_positive_create_with_multiple_roles(session):
    """Create User with multiple roles

    :id: d3cc4434-25ca-4465-8878-42495390c17b

    :expectedresults: User is created successfully and has proper roles
        assigned

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    role1 = gen_string('alpha')
    role2 = gen_string('alpha')
    password = gen_string('alpha')
    for role in [role1, role2]:
        entities.Role(name=role).create()
    with session:
        session.user.create({
            'user.login': name,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
            'roles.resources.assigned': [role1, role2],
        })
        assert session.user.search(name) == name
        user_values = session.user.read(name)
        assert (
            set(user_values['roles']['resources']['assigned']) ==
            set([role1, role2])
        )


@tier2
def test_positive_create_with_all_roles(session):
    """Create User and assign all available roles to it

    :id: 814593ca-1566-45ea-9eff-e880183b1ee3

    :expectedresults: User is created successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    password = gen_string('alpha')
    with session:
        session.user.create({
            'user.login': name,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
            'roles.resources.assigned': ROLES,
        })
        assert session.user.search(name) == name
        user_values = session.user.read(name)
        assert (
            set(user_values['roles']['resources']['assigned']) == set(ROLES))


@tier2
def test_positive_create_with_multiple_orgs(session):
    """Create User associated to multiple Orgs

    :id: d74c0284-3995-4a4a-8746-00858282bf5d

    :expectedresults: User is created successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    org_name1 = gen_string('alpha')
    org_name2 = gen_string('alpha')
    password = gen_string('alpha')
    for org_name in [org_name1, org_name2]:
        entities.Organization(name=org_name).create()
    with session:
        session.organization.select(org_name=DEFAULT_ORG)
        session.user.create({
            'user.login': name,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
            'organizations.resources.assigned': [org_name1, org_name2],
        })
        assert session.user.search(name) == name
        user_values = session.user.read(name)
        assert (
            set(user_values['organizations']['resources']['assigned']) ==
            set([DEFAULT_ORG, org_name1, org_name2])
        )


@tier2
def test_positive_update_with_multiple_roles(session):
    """Update User with multiple roles

    :id: 127fb368-09fd-4f10-8319-566a1bcb5cd2

    :expectedresults: User is updated successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    role_names = [
        entities.Role().create().name
        for _ in range(3)
    ]
    password = gen_string('alpha')
    with session:
        session.user.create({
            'user.login': name,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
        })
        session.user.update(
            name,
            {'roles.resources.assigned': role_names},
        )
        assert session.user.search(name) == name
        user_values = session.user.read(name)
        assert (
            set(user_values['roles']['resources']['assigned']) ==
            set(role_names)
        )


@tier2
def test_positive_update_with_all_roles(session):
    """Update User with all roles

    :id: cd7a9cfb-a700-45f2-a11d-bba6be3c810d

    :expectedresults: User is updated successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    password = gen_string('alpha')
    with session:
        session.user.create({
            'user.login': name,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
        })
        session.user.update(
            name,
            {'roles.resources.assigned': ROLES},
        )
        assert session.user.search(name) == name
        user_values = session.user.read(name)
        assert (
            set(user_values['roles']['resources']['assigned']) == set(ROLES))


@tier2
def test_positive_update_orgs(session):
    """Assign a User to multiple Orgs

    :id: a207188d-1ad1-4ff1-9906-bae1d91104fd

    :expectedresults: User is updated

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    password = gen_string('alpha')
    org_names = [
        entities.Organization().create().name
        for _ in range(3)
    ]
    with session:
        session.organization.select(org_name=random.choice(org_names))
        session.user.create({
            'user.login': name,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
        })
        session.user.update(
            name,
            {'organizations.resources.assigned': org_names},
        )
        assert session.user.search(name) == name
        user_values = session.user.read(name)
        assert (
            set(user_values['organizations']['resources']['assigned']) ==
            set(org_names)
        )
