"""Test class for Roles UI

:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from airgun.session import Session
from nailgun import entities
from navmazing import NavigationTriesExceeded
from pytest import raises

from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


def test_positive_update_filter(session):
    resource_name = 'Architecture'
    permission_name = 'edit_architectures'
    role = entities.Role().create()
    permission = entities.Permission(resource_type=resource_name).search()
    entities.Filter(permission=permission, role=role.id).create()
    with session:
        filter_values = session.filter.read(role.name, resource_name)
        assert permission_name in filter_values['permission']['assigned']
        session.filter.update(
            role.name,
            resource_name,
            {'permission.unassigned': ['edit_architectures']}
        )
        filter_values = session.filter.read(role.name, resource_name)
        assert permission_name in filter_values['permission']['unassigned']


def test_positive_delete_filter(session):
    resource_name = 'Architecture'
    role = entities.Role().create()
    permission = entities.Permission(resource_type=resource_name).search()
    entities.Filter(permission=permission, role=role.id).create()
    with session:
        assert session.filter.search(
            role.name, resource_name)[0]['Resource'] == resource_name
        session.filter.delete(role.name, resource_name)
        assert not session.filter.search(role.name, resource_name)


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
            'name': subnet_name,
            'protocol': 'IPv4',
            'network_address': subnet.network,
            'network_mask': subnet.mask,
            'boot_mode': 'Static',
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
            'name': subnet_name,
            'protocol': 'IPv4',
            'network_address': subnet.network,
            'network_mask': subnet.mask,
            'boot_mode': 'Static',
        })
        assert session.subnet.search(subnet_name)[0]['Name'] == subnet_name
        session.organization.select(org_name=role_org.name)
        session.location.select(loc_name=role_loc.name)
        with raises(AssertionError) as context:
            session.subnet.create({
                'name': new_subnet_name,
                'protocol': 'IPv4',
                'network_address': subnet.network,
                'network_mask': subnet.mask,
                'boot_mode': 'Static',
            })
        assert "You don't have permission create_subnets with attributes" \
               " that you have specified or you don't have access to" \
               " specified locations or organizations" in str(context.value)
