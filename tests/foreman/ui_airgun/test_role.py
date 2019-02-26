"""Test class for Roles UI

:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

from airgun.session import Session
from nailgun import entities
from navmazing import NavigationTriesExceeded
from pytest import raises

from robottelo.constants import PERMISSIONS_UI, ROLES
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for role component

    :id: 3284016a-e2df-4a0e-aa24-c95ab132eec1

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :BZ: 1353788

    :CaseImportance: High
    """
    role_name = gen_string('alpha')
    role_description = gen_string('alpha')
    resource_type = 'Architecture'
    permissions = ['view_architectures', 'edit_architectures']
    cloned_role_name = gen_string('alpha')
    new_role_name = gen_string('alpha')
    new_role_description = gen_string('alpha')
    new_org = entities.Organization().create()
    new_loc = entities.Location(organization=[new_org]).create()
    with session:
        session.role.create({
            'name': role_name,
            'description': role_description,
            'organizations.assigned': [module_org.name],
            'locations.assigned': [module_loc.name]
        })
        values = session.role.read(role_name)
        assert values['name'] == role_name
        assert values['description'] == role_description
        assert values['organizations']['assigned'] == [module_org.name]
        assert values['locations']['assigned'] == [module_loc.name]
        session.filter.create(role_name, {
            'resource_type': resource_type,
            'permission.assigned': permissions
        })
        assigned_permissions = session.filter.read_permissions(role_name)
        assert set(assigned_permissions[resource_type]) == set(permissions)
        # clone the role
        session.role.clone(role_name, {'name': cloned_role_name})
        assert session.role.search(cloned_role_name)[0]['Name'] == cloned_role_name
        assigned_permissions = session.filter.read_permissions(cloned_role_name)
        assert list(assigned_permissions.keys()) == [resource_type]
        assert set(assigned_permissions[resource_type]) == set(permissions)
        # update the role
        session.role.update(role_name, {
            'name': new_role_name,
            'description': new_role_description,
            'organizations.assigned': [new_org.name],
            'locations.assigned': [new_loc.name]
        })
        assert not session.role.search(role_name)
        values = session.role.read(new_role_name)
        assert values['name'] == new_role_name
        assert values['description'] == new_role_description
        assert set(values['organizations']['assigned']) == {module_org.name, new_org.name}
        assert set(values['locations']['assigned']) == {module_loc.name, new_loc.name}
        # delete the role
        session.role.delete(new_role_name)
        assert not session.role.search(new_role_name)
        # delete the cloned role
        session.role.delete(cloned_role_name)
        assert not session.role.search(cloned_role_name)


@tier2
def test_positive_assign_cloned_role(session):
    """Clone role and assign it to user

    :id: cbb17f37-9039-4875-981b-1f427b095ed1

    :customerscenario: true

    :expectedresults: User is created successfully

    :BZ: 1353788

    :CaseImportance: Critical
    """
    role_name = random.choice(ROLES)
    cloned_role_name = gen_string('alpha')
    user_name = gen_string('alpha')
    user_password = gen_string('alpha')
    with session:
        session.role.clone(role_name, {'name': cloned_role_name})
        assert session.role.search(cloned_role_name)[0]['Name'] == cloned_role_name
        session.user.create({
            'user.login': user_name,
            'user.auth': 'INTERNAL',
            'user.password': user_password,
            'user.confirm': user_password,
            'roles.resources.assigned': [cloned_role_name],
        })
        assert session.user.search(user_name)[0]['Username'] == user_name
        user = session.user.read(user_name)
        assert user['roles']['resources']['assigned'] == [cloned_role_name]


@tier2
@upgrade
def test_positive_delete_cloned_builtin(session):
    """Delete cloned builtin role

    :id: 7f0a595b-2b27-4dca-b15a-02cd2519b2f7

    :customerscenario: true

    :expectedresults: Role is deleted

    :BZ: 1353788, 1426672

    :CaseImportance: Critical
    """
    role_name = random.choice(ROLES)
    cloned_role_name = gen_string('alpha')
    with session:
        session.role.clone(role_name, {'name': cloned_role_name})
        assert session.role.search(cloned_role_name)[0]['Name'] == cloned_role_name
        session.role.delete(cloned_role_name)
        assert not session.role.search(cloned_role_name)


@tier2
def test_positive_create_filter_without_override(
        session, module_org, module_loc, test_name):
    """Create filter in role w/o overriding it

    :id: a7f76f6e-6c13-4b34-b38c-19501b65786f

    :steps:

        1. Create a role with taxonomies (location and organization)
            assigned
        2. Create filter in role without overriding it
        3. Create user and assign new role to it
        4. Re-login into application using new user with a role

    :expectedresults:

        1. Filter w/o override is created in role
        2. The taxonomies of role are inherited to filter
        3. User can access application sections specified in a filter
    """
    role_name = gen_string('alpha')
    username = gen_string('alpha')
    password = gen_string('alpha')
    subnet = entities.Subnet()
    subnet.create_missing()
    subnet_name = subnet.name
    with session:
        session.role.create({
            'name': role_name,
            'organizations.assigned': [module_org.name],
            'locations.assigned': [module_loc.name]
        })
        assert session.role.search(role_name)[0]['Name'] == role_name
        session.filter.create(
            role_name,
            {
                'resource_type': 'Subnet',
                'permission.assigned': ['view_subnets', 'create_subnets'],
            }
        )
        filter_values = session.filter.read(role_name, 'Subnet')
        assert filter_values['override'] is False
        session.filter.create(
            role_name,
            {
                'resource_type': 'Organization',
                'permission.assigned': [
                    'assign_organizations', 'view_organizations'],
            }
        )
        session.filter.create(
            role_name,
            {
                'resource_type': 'Location',
                'permission.assigned': ['assign_locations', 'view_locations'],
            }
        )
        session.user.create({
            'user.login': username,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
            'user.mail': 'test@eample.com',
            'roles.resources.assigned': [role_name],
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],

        })
    with Session(test_name, user=username, password=password) as session:
        session.subnet.create({
            'subnet.name': subnet_name,
            'subnet.protocol': 'IPv4',
            'subnet.network_address': subnet.network,
            'subnet.network_mask': subnet.mask,
            'subnet.boot_mode': 'Static',
        })
        assert session.subnet.search(subnet_name)[0]['Name'] == subnet_name
        with raises(NavigationTriesExceeded):
            session.architecture.create({'name': gen_string('alpha')})


@tier2
@upgrade
def test_positive_create_non_overridable_filter(
        session, module_org, module_loc, test_name):
    """Create non overridden filter in role

    :id: 5ee281cf-28fa-439d-888d-b1f9aacc6d57

    :steps:

        1. Create a filter in a role to which taxonomies (location and
            organization) cannot be associated.  e.g Architecture filter
        2. Create an user with taxonomies different than role and assign
            role to it
        3. Login as new user and attempt to access the resources

    :expectedresults:

        1. Filter is created without taxonomies
        2. User can access resources, permissions specified in a filter
        3. User have access in all taxonomies available to user
    """
    role_name = gen_string('alpha')
    username = gen_string('alpha')
    password = gen_string('alpha')
    new_name = gen_string('alpha')
    user_org = entities.Organization().create()
    user_loc = entities.Location().create()
    arch = entities.Architecture().create()
    with session:
        session.role.create({
            'name': role_name,
            'organizations.assigned': [module_org.name],
            'locations.assigned': [module_loc.name]
        })
        assert session.role.search(role_name)[0]['Name'] == role_name
        session.filter.create(
            role_name,
            {
                'resource_type': 'Architecture',
                'permission.assigned': [
                    'view_architectures', 'edit_architectures'],
            }
        )
        session.user.create({
            'user.login': username,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
            'user.mail': 'test@eample.com',
            'roles.resources.assigned': [role_name],
            'organizations.resources.assigned': [user_org.name],
            'locations.resources.assigned': [user_loc.name],

        })
    with Session(test_name, user=username, password=password) as session:
        session.architecture.update(arch.name, {'name': new_name})
        assert session.architecture.search(new_name)[0]['Name'] == new_name
        with raises(NavigationTriesExceeded):
            session.organization.create({
                'name': gen_string('alpha'),
                'label': gen_string('alpha'),
            })


@tier2
@upgrade
def test_positive_create_overridable_filter(
        session, module_org, module_loc, test_name):
    """Create overridden filter in role

    :id: 325e7e3e-60fc-4182-9585-0449d9660e8d

    :steps:

        1. Create a role with some taxonomies (organizations and locations)
        2. Create a filter in role to which taxonomies can be associated
            e.g Subnet filter
        3. Override a filter with some taxonomies which doesnt match the
            taxonomies of role
        4. Create user with taxonomies including filter taxonomies and
            assign role to it
        5. Login with user and attempt to access the resources

    :expectedresults:

        1. Filter is created with taxonomies
        2. User can access resources, permissions specified in filter
        3. User have access only in taxonomies specified in filter
    """
    role_name = gen_string('alpha')
    username = gen_string('alpha')
    password = gen_string('alpha')
    role_org = entities.Organization().create()
    role_loc = entities.Location().create()
    subnet = entities.Subnet()
    subnet.create_missing()
    subnet_name = subnet.name
    new_subnet_name = gen_string('alpha')
    with session:
        session.role.create({
            'name': role_name,
            'organizations.assigned': [role_org.name, module_org.name],
            'locations.assigned': [role_loc.name, module_loc.name]

        })
        assert session.role.search(role_name)[0]['Name'] == role_name
        session.filter.create(
            role_name,
            {
                'resource_type': 'Subnet',
                'permission.assigned': ['view_subnets', 'create_subnets'],
                'override': True,
                'taxonomies_tabs.locations.resources.assigned': [
                    module_loc.name],
                'taxonomies_tabs.organizations.resources.assigned': [
                    module_org.name]
            }
        )
        session.filter.create(
            role_name,
            {
                'resource_type': 'Organization',
                'permission.assigned': [
                    'assign_organizations', 'view_organizations'],
            }
        )
        session.filter.create(
            role_name,
            {
                'resource_type': 'Location',
                'permission.assigned': ['assign_locations', 'view_locations'],
            }
        )
        session.user.create({
            'user.login': username,
            'user.auth': 'INTERNAL',
            'user.password': password,
            'user.confirm': password,
            'user.mail': 'test@eample.com',
            'roles.resources.assigned': [role_name],
            'organizations.resources.assigned': [
                role_org.name, module_org.name],
            'locations.resources.assigned': [role_loc.name, module_loc.name],

        })
    with Session(test_name, user=username, password=password) as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_loc.name)
        session.subnet.create({
            'subnet.name': subnet_name,
            'subnet.protocol': 'IPv4',
            'subnet.network_address': subnet.network,
            'subnet.network_mask': subnet.mask,
            'subnet.boot_mode': 'Static',
        })
        assert session.subnet.search(subnet_name)[0]['Name'] == subnet_name
        session.organization.select(org_name=role_org.name)
        session.location.select(loc_name=role_loc.name)
        with raises(AssertionError) as context:
            session.subnet.create({
                'subnet.name': new_subnet_name,
                'subnet.protocol': 'IPv4',
                'subnet.network_address': subnet.network,
                'subnet.network_mask': subnet.mask,
                'subnet.boot_mode': 'Static',
            })
        assert "You don't have permission create_subnets with attributes" \
               " that you have specified or you don't have access to" \
               " specified locations or organizations" in str(context.value)


@tier2
def test_positive_create_with_21_filters(session):
    """Make sure it's possible to create more than 20 filters inside single role

    :BZ: 1277444

    :id: 6c36d382-9790-4d34-affa-e993764cef9a

    :customerscenario: true

    :expectedresults: more than 20 filters are displayed

    :CaseImportance: Medium
    """
    filters_number = 21
    role_name = gen_string('alphanumeric')
    permissions = (
        (resource, permission)
        for resource, resource_permissions in PERMISSIONS_UI.items()
        for permission in resource_permissions
    )
    with session:
        session.role.create({'name': role_name})
        assert session.role.search(role_name)[0]['Name'] == role_name
        used_filters = set()
        for _ in range(filters_number):
            resource_type, permission = next(permissions)
            used_filters.add((resource_type, permission))
            session.filter.create(role_name, {
                'resource_type': resource_type,
                'permission.assigned': [permission]
            })
        assigned_permissions = session.filter.read_permissions(role_name)
        assigned_filters = {
            (resource_type, permission)
            for resource_type, resource_permissions in assigned_permissions.items()
            for permission in resource_permissions
        }
        assert len(assigned_filters) == filters_number
        assert assigned_filters == used_filters


@tier2
def test_positive_create_with_sc_parameter_permission(session):
    """Create role filter with few permissions for smart class parameters.

    :id: c9e466e5-d6ce-4596-bd32-c2a7817da34a

    :customerscenario: true

    :expectedresults: Corresponding role filter has necessary permissions

    :BZ: 1360191

    :CaseImportance: High
    """
    role_name = gen_string('alpha')
    resource_type = 'Smart class parameter'
    permissions = ['view_external_parameters', 'edit_external_parameters']
    with session:
        session.role.create({'name': role_name})
        assert session.role.search(role_name)[0]['Name'] == role_name
        session.filter.create(role_name, {
            'resource_type': resource_type,
            'permission.assigned': permissions
        })
        values = session.filter.search(role_name, 'PuppetclassLookupKey')
        assert values
        assert values[0]['Resource'] == resource_type
        assigned_permissions = values[0]['Permissions'].split(', ')
        assert set(assigned_permissions) == set(permissions)


@tier2
def test_positive_create_with_smart_variable_permission(session):
    """Create role filter with few permissions for smart variables.

    :id: 9e5775f3-5f79-4212-bcb4-29d91032df4e

    :customerscenario: true

    :expectedresults: Corresponding role filter has necessary permissions

    :BZ: 1360191

    :CaseImportance: High
    """
    role_name = gen_string('alpha')
    resource_type = 'Smart variable'
    permissions = ['view_external_variables', 'edit_external_variables']
    with session:
        session.role.create({'name': role_name})
        assert session.role.search(role_name)[0]['Name'] == role_name
        session.filter.create(role_name, {
            'resource_type': resource_type,
            'permission.assigned': permissions
        })
        values = session.filter.search(role_name, 'VariableLookupKey')
        assert values
        assert values[0]['Resource'] == resource_type
        assigned_permissions = values[0]['Permissions'].split(', ')
        assert set(assigned_permissions) == set(permissions)


@tier2
def test_positive_create_filter_admin_user_with_locs(test_name):
    """Attempt to create a role filter by admin user, who has 6+ locations assigned.

    :id: 688ecb7d-1d49-494c-97cc-0d5e715f3bb1

    :customerscenario: true

    :expectedresults: filter was successfully created.

    :BZ: 1315580

    :CaseImportance: Critical
    """
    role_name = gen_string('alpha')
    resource_type = 'Architecture'
    permissions = ['view_architectures', 'edit_architectures']
    org = entities.Organization().create()
    locations = [
        entities.Location(organization=[org]).create() for _ in range(6)]
    password = gen_string('alphanumeric')
    user = entities.User(
        admin=True,
        organization=[org],
        location=locations,
        default_organization=org,
        default_location=locations[0],
        password=password,
    ).create()
    with Session(test_name, user=user.login, password=password) as session:
        session.role.create({'name': role_name})
        assert session.role.search(role_name)[0]['Name'] == role_name
        session.filter.create(role_name, {
            'resource_type': resource_type,
            'permission.assigned': permissions
        })
        assigned_permissions = session.filter.read_permissions(role_name)
        assert set(assigned_permissions[resource_type]) == set(permissions)


@tier2
def test_positive_create_filter_admin_user_with_orgs(test_name):
    """Attempt to create a role filter by admin user, who has 10 organizations assigned.

    :id: 04208e17-34b5-46b1-84dd-b8a973521d30

    :customerscenario: true

    :expectedresults: filter was successfully created.

    :BZ: 1389795

    :CaseImportance: Critical
    """
    role_name = gen_string('alpha')
    resource_type = 'Architecture'
    permissions = ['view_architectures', 'edit_architectures']
    password = gen_string('alphanumeric')
    organizations = [
        entities.Organization().create()
        for _ in range(10)
    ]
    loc = entities.Location(organization=[organizations[0]]).create()
    user = entities.User(
        admin=True,
        organization=organizations,
        location=[loc],
        default_organization=organizations[0],
        default_location=loc,
        password=password,
    ).create()
    with Session(test_name, user=user.login, password=password) as session:
        session.role.create({'name': role_name})
        assert session.role.search(role_name)[0]['Name'] == role_name
        session.filter.create(role_name, {
            'resource_type': resource_type,
            'permission.assigned': permissions
        })
        assigned_permissions = session.filter.read_permissions(role_name)
        assert set(assigned_permissions[resource_type]) == set(permissions)
