"""Test class for User UI

:Requirement: User

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Assignee: dsynk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from airgun.session import Session
from fauxfactory import gen_email
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import create_role_permissions
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import PERMISSIONS
from robottelo.constants import ROLES


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_loc():
    return entities.Location().create()


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, test_name, module_org, module_loc):
    """Perform end to end testing for user component

    :id: 2794fdd0-cfe3-4f1a-aa5f-25b2d211ae12

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    ak_name = gen_string('alpha')
    firstname = gen_string('alpha')
    lastname = gen_string('alpha')
    password = gen_string('alpha')
    email = gen_email()
    description = gen_string('alphanumeric')
    language = 'English (United States)'
    timezone = '(GMT+00:00) UTC'
    role = entities.Role().create().name
    with session:
        # Create new user and validate its values
        session.user.create(
            {
                'user.login': name,
                'user.firstname': firstname,
                'user.lastname': lastname,
                'user.mail': email,
                'user.description': description,
                'user.language': language,
                'user.timezone': timezone,
                'user.auth': 'INTERNAL',
                'user.password': password,
                'user.confirm': password,
                'locations.resources.assigned': [module_loc.name],
                'organizations.resources.assigned': [module_org.name],
                'roles.admin': True,
                'roles.resources.assigned': [role],
            }
        )
        assert session.user.search(name)[0]['Username'] == name
        user_values = session.user.read(name)
        assert user_values['user']['login'] == name
        assert user_values['user']['firstname'] == firstname
        assert user_values['user']['lastname'] == lastname
        assert user_values['user']['mail'] == email
        assert user_values['user']['description'] == description
        assert user_values['user']['language'] == language
        assert user_values['user']['timezone'] == timezone
        assert user_values['user']['auth'] == 'INTERNAL'
        assert user_values['locations']['resources']['assigned'] == [module_loc.name]
        assert user_values['organizations']['resources']['assigned'] == [module_org.name]
        assert user_values['roles']['admin'] is True
        assert user_values['roles']['resources']['assigned'] == [role]
        # Update user with new name
        session.user.update(name, {'user.login': new_name})
        assert session.user.search(new_name)[0]['Username'] == new_name
        assert not session.user.search(name)
        # Login into application using new user
    with Session(test_name, new_name, password) as newsession:
        newsession.organization.select(module_org.name)
        newsession.location.select(module_loc.name)
        newsession.activationkey.create({'name': ak_name})
        assert newsession.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = newsession.activationkey.read(ak_name, 'current_user')['current_user']
        assert current_user == f'{firstname} {lastname}'
        # Delete user
        session.user.delete(new_name)
        assert not session.user.search(new_name)


@pytest.mark.tier2
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
        session.user.create(
            {
                'user.login': name,
                'user.auth': 'INTERNAL',
                'user.password': password,
                'user.confirm': password,
                'roles.resources.assigned': [role1, role2],
            }
        )
        assert session.user.search(name)[0]['Username'] == name
        user = session.user.read(name)
        assert set(user['roles']['resources']['assigned']) == {role1, role2}


@pytest.mark.tier2
def test_positive_create_with_all_roles(session):
    """Create User and assign all available roles to it

    :id: 814593ca-1566-45ea-9eff-e880183b1ee3

    :expectedresults: User is created successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    password = gen_string('alpha')
    with session:
        session.user.create(
            {
                'user.login': name,
                'user.auth': 'INTERNAL',
                'user.password': password,
                'user.confirm': password,
                'roles.resources.assigned': ROLES,
            }
        )
        assert session.user.search(name)[0]['Username'] == name
        user = session.user.read(name)
        assert set(user['roles']['resources']['assigned']) == set(ROLES)


@pytest.mark.tier2
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
        session.user.create(
            {
                'user.login': name,
                'user.auth': 'INTERNAL',
                'user.password': password,
                'user.confirm': password,
                'organizations.resources.assigned': [org_name1, org_name2],
            }
        )
        assert session.user.search(name)[0]['Username'] == name
        user = session.user.read(name)
        assert set(user['organizations']['resources']['assigned']) == {
            DEFAULT_ORG,
            org_name1,
            org_name2,
        }


@pytest.mark.tier2
def test_positive_update_with_multiple_roles(session):
    """Update User with multiple roles

    :id: 127fb368-09fd-4f10-8319-566a1bcb5cd2

    :expectedresults: User is updated successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    role_names = [entities.Role().create().name for _ in range(3)]
    password = gen_string('alpha')
    with session:
        session.user.create(
            {
                'user.login': name,
                'user.auth': 'INTERNAL',
                'user.password': password,
                'user.confirm': password,
            }
        )
        session.user.update(name, {'roles.resources.assigned': role_names})
        assert session.user.search(name)[0]['Username'] == name
        user = session.user.read(name)
        assert set(user['roles']['resources']['assigned']) == set(role_names)


@pytest.mark.tier2
def test_positive_update_with_all_roles(session):
    """Update User with all roles

    :id: cd7a9cfb-a700-45f2-a11d-bba6be3c810d

    :expectedresults: User is updated successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    password = gen_string('alpha')
    with session:
        session.user.create(
            {
                'user.login': name,
                'user.auth': 'INTERNAL',
                'user.password': password,
                'user.confirm': password,
            }
        )
        session.user.update(name, {'roles.resources.assigned': ROLES})
        assert session.user.search(name)[0]['Username'] == name
        user = session.user.read(name)
        assert set(user['roles']['resources']['assigned']) == set(ROLES)


@pytest.mark.tier2
def test_positive_update_orgs(session):
    """Assign a User to multiple Orgs

    :id: a207188d-1ad1-4ff1-9906-bae1d91104fd

    :expectedresults: User is updated

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    password = gen_string('alpha')
    org_names = [entities.Organization().create().name for _ in range(3)]
    with session:
        session.organization.select(org_name=random.choice(org_names))
        session.user.create(
            {
                'user.login': name,
                'user.auth': 'INTERNAL',
                'user.password': password,
                'user.confirm': password,
            }
        )
        session.user.update(name, {'organizations.resources.assigned': org_names})
        assert session.user.search(name)[0]['Username'] == name
        user = session.user.read(name)
        assert set(user['organizations']['resources']['assigned']) == set(org_names)


@pytest.mark.tier2
def test_positive_create_product_with_limited_user_permission(
    session, test_name, module_org, module_loc
):
    """A user with all permissions in Product and Repositories should be able to
    create a new product

    :id: 534a16f9-2d66-4fa1-aa5b-560f00eb4f67

    :expectedresults: User successfully creates new product

    :CaseLevel: Component

    :CaseImportance: High

    :BZ: 1771937
    """
    username = gen_string('alpha')
    password = gen_string('alpha')
    product_name = gen_string('alpha')
    product_label = gen_string('alpha')
    product_description = gen_string('alpha')
    role = entities.Role().create()
    # Calling Products and Repositoy to get all the permissions in it
    create_role_permissions(role, {'Katello::Product': PERMISSIONS['Katello::Product']})
    entities.User(
        default_organization=module_org,
        organization=[module_org],
        firstname='sample',
        lastname='test',
        role=[role],
        login=username,
        password=password,
        mail='test@test.com',
    ).create()
    with Session(test_name, username, password) as newsession:
        newsession.product.create(
            {'name': product_name, 'label': product_label, 'description': product_description}
        )
        assert newsession.product.search(product_name)[0]['Name'] == product_name


@pytest.mark.tier2
@pytest.mark.stubbed
def test_personal_access_token_admin():
    """Personal access token for admin

    :id: 32162724-4a23-49f6-8644-28b6f44a3e18

    :steps:
        1. Edit ‘admin’ user to add personal access token
        2. Use any api endpoint with the token
        3. Revoke the token and check for the result.

    :expectedresults:
        1. Should show output of the api endpoint
        2. When revoked, authentication error

    :CaseLevel: System

    :CaseImportance: High
    """


@pytest.mark.tier2
@pytest.mark.stubbed
def test_positive_personal_access_token_user_with_role():
    """Personal access token for user with a role

    :id: 7e392265-feed-47d4-bad4-15dad9171f12

    :steps:
        1. Create a new user. Assign a role to it and create personal
           access token
        2. Use an api endpoint to that specific role and other roles.
        3. Revoke the access token

    :expectedresults:
        1. When used with the correct role and end point, corresponding
           output should be displayed.
        2. When an incorrect role and end point is used, missing
           permission should be displayed.

    :CaseLevel: System

    :CaseImportance: High
    """


@pytest.mark.tier2
@pytest.mark.stubbed
def test_expired_personal_access_token():
    """Personal access token expired for the user.

    :id: 8e46907f-cf56-4e77-8496-8d8935b333d8

    :steps:
        1. Set the expired time to 1 minute from the current time.
        2. Wait 1 minute
        3. Try using the token with any end point.

    :expectedresults: Authentication error

    :CaseLevel: System

    :CaseImportance: Medium
    """
