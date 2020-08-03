"""Unit tests for the ``roles`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/roles.html


:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from nailgun.config import ServerConfig
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.datafactory import gen_string
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.test import APITestCase
from robottelo.utils.issue_handlers import is_open


class RoleTestCase(APITestCase):
    """Tests for ``api/v2/roles``."""

    @tier1
    def test_positive_create(self):
        """Create a role with name ``name_generator()``.

        :id: 488a0970-f844-4286-b1eb-dd93005b4580

        :expectedresults: An entity can be created without receiving any
            errors, the entity can be fetched, and the fetched entity has the
            specified name.

        :CaseImportance: Critical
        """
        for name in generate_strings_list():
            with self.subTest(name):
                self.assertEqual(entities.Role(name=name).create().name, name)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete a role with name ``name_generator()``.

        :id: 6e1d9f9c-3cbb-460b-8ef8-4a156e6552a0

        :expectedresults: The role cannot be fetched after it is deleted.

        :CaseImportance: Critical
        """
        for name in generate_strings_list():
            with self.subTest(name):
                role = entities.Role(name=name).create()
                self.assertEqual(role.name, name)
                role.delete()
                with self.assertRaises(HTTPError):
                    role.read()

    @tier1
    def test_positive_update(self):
        """Update a role with and give a name of ``name_generator()``.

        :id: 30cb4b42-24cd-48a0-a3c5-7ca44c060e2e

        :expectedresults: The role is updated with the given name.

        :CaseImportance: Critical
        """
        for name in generate_strings_list():
            with self.subTest(name):
                role = entities.Role().create()
                role.name = name
                self.assertEqual(role.update(['name']).name, name)


class CannedRoleTestCases(APITestCase):
    """Implements Canned Roles tests from API"""

    def create_org_admin_role(self, name=None, orgs=None, locs=None):
        """Helper function to create org admin role for particular
        organizations and locations by cloning 'Organization admin' role.

        :param str name: The name of cloned Org Admin role
        :param list orgs: The list of organizations for which the org admin is
            being created
        :param list locs: The list of locations for which the org admin is
            being created
        :return dict: This function returns dict representation of cloned role
            data returned from 'clone' function
        """
        name = gen_string('alpha') if not name else name
        default_org_admin = entities.Role().search(query={'search': 'name="Organization admin"'})
        org_admin = entities.Role(id=default_org_admin[0].id).clone(
            data={
                'role': {'name': name, 'organization_ids': orgs or [], 'location_ids': locs or []}
            }
        )
        return entities.Role(id=org_admin['id']).read()

    def create_org_admin_user(self, role_taxos, user_taxos, same_taxos):
        """Helper function to create an Org Admin user by assigning org admin
        role and assign taxonomies to Role and User

        The taxonomies for role and user will be assigned based on parameters

        :param bool role_taxos: Whether or not to assign taxonomies to Role
            If True, self.role_orgs and self.role_locs will be assigned else []
        :param bool user_taxos: Whether or not to assign taxonomies to User
            If True and if same_taxos True => self.role_orgs, self.role_locs
            will be assigned
            elseif True and if same_taxos False => self.filter_orgs,
            self.filter_locs will be assigned
            else []
        :param same_taxos: Whether or not taxonomies of role and user should
            be same. Check user_taxos param description
        :return User: Returns the ```nailgun.entities.User``` object with
            passwd attr
        """
        # Create Org Admin Role
        orgs = [self.role_org.id] if role_taxos else []
        locs = [self.role_loc.id] if role_taxos else []
        org_admin = self.create_org_admin_role(orgs=orgs, locs=locs)
        # Create Org Admin User
        orgs = ([self.role_org.id] if same_taxos else [self.filter_org.id]) if user_taxos else []
        locs = ([self.role_loc.id] if same_taxos else [self.filter_loc.id]) if user_taxos else []
        user_login = gen_string('alpha')
        user_passwd = gen_string('alphanumeric')
        user = entities.User(
            login=user_login,
            password=user_passwd,
            organization=orgs,
            location=locs,
            role=[org_admin.id],
        ).create()
        user.passwd = user_passwd
        return user

    def create_simple_user(self, filter_taxos=None, role=None):
        """Creates simple user and assigns taxonomies

        :param bool filter_taxos: Whether to assign filter taxonomies created
            in setupclass method.
            If true, self.filter_orgs and filter_locs else self.role_orgs
            and role_locs
        :param nailgun.entities.Role role: Nailgun Role entity assign to user
        :return User: Returns the ```nailgun.entities.User``` object with
            passwd attr
        """
        user_passwd = gen_string('alphanumeric')
        user = entities.User(
            login=gen_string('alpha'),
            password=user_passwd,
            organization=([self.filter_org.id] if filter_taxos else [self.role_org.id]),
            location=([self.filter_loc.id] if filter_taxos else [self.role_loc.id]),
            role=role or [],
        ).create()
        user.passwd = user_passwd
        return user

    def create_domain(self, orgs, locs):
        """Creates domain in given orgs and locs

        :param list orgs: List of Organization ids
        :param list locs: List of Location ids
        :return Domain: Returns the ```nailgun.entities.Domain``` object
        """
        return entities.Domain(name=gen_string('alpha'), organization=orgs, location=locs).create()

    def user_config(self, user):
        """Returns The ```nailgun.confin.ServerConfig``` for given user

        :param user: The nailgun.entities.User object of an user with passwd
            parameter
        """
        return ServerConfig(auth=(user.login, user.passwd), url=self.sat_url, verify=False)

    @classmethod
    def setUpClass(cls):
        """Creates two orgs and locations that will be used by all the
        underlying tests
        """
        super(CannedRoleTestCases, cls).setUpClass()
        cls.sat_url = 'https://{}'.format(settings.server.hostname)
        # These two will be used as role taxonomies
        cls.role_org = entities.Organization().create()
        cls.role_loc = entities.Location().create()
        # These two will be used as filter taxonomies
        cls.filter_org = entities.Organization().create()
        cls.filter_loc = entities.Location().create()

    @tier1
    def test_positive_create_role_with_taxonomies(self):
        """create role with taxonomies

        :id: fa449217-889c-429b-89b5-0b6c018ffd9e

        :steps: Create new role with taxonomies

        :expectedresults: New role is created with taxonomies

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(
            name=role_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(role.name, role_name)
        self.assertEqual(self.role_org.id, role.organization[0].id)
        self.assertEqual(self.role_loc.id, role.location[0].id)

    @tier1
    def test_positive_create_role_without_taxonomies(self):
        """Create role without taxonomies

        :id: fe65a691-1b04-4bfe-a24b-adb48feb31d1

        :steps: Create new role without any taxonomies

        :expectedresults: New role is created without taxonomies

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(name=role_name, organization=[], location=[]).create()
        self.assertEqual(role.name, role_name)
        self.assertFalse(role.organization)
        self.assertFalse(role.location)

    @tier1
    def test_positive_create_filter_without_override(self):
        """Create filter in role w/o overriding it

        :id: 1aadb7ea-ff76-4171-850f-188ba6f87021

        :steps:

            1. Create a role with taxonomies assigned
            2. Create filter in role without overriding it

        :expectedresults:

            1. Filter w/o override is created in role
            2. The taxonomies of role are inherited to filter
            3. Override check is not marked by default in filters table

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(
            name=role_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(role.name, role_name)
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        filtr = entities.Filter(permission=dom_perm, role=role.id).create()
        self.assertEqual(role.id, filtr.role.id)
        self.assertEqual(self.role_org.id, filtr.organization[0].id)
        self.assertEqual(self.role_loc.id, filtr.location[0].id)
        self.assertFalse(filtr.override)

    @tier1
    def test_positive_create_non_overridable_filter(self):
        """Create non overridable filter in role

        :id: f891e2e1-76f8-4edf-8c96-b41d05483298

        :steps: Create a filter to which taxonomies cannot be associated.
            e.g Architecture filter

        :expectedresults:

            1. Filter is created without taxonomies
            2. Override check is set to false

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(name=role_name).create()
        self.assertEqual(role.name, role_name)
        arch_perm = entities.Permission().search(query={'search': 'resource_type="Architecture"'})
        filtr = entities.Filter(permission=arch_perm, role=role.id).create()
        self.assertEqual(role.id, filtr.role.id)
        self.assertFalse(filtr.override)

    @tier1
    def test_negative_override_non_overridable_filter(self):
        """Override non overridable filter

        :id: 7793be96-e8eb-451b-a986-51a46a1ab4f9

        :steps: Attempt to override a filter to which taxonomies cannot be
            associated.  e.g Architecture filter

        :expectedresults: Filter is not overrided as taxonomies cannot be
            applied to that filter

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(name=role_name).create()
        self.assertEqual(role.name, role_name)
        arch_perm = entities.Permission().search(query={'search': 'resource_type="Architecture"'})
        with self.assertRaises(HTTPError):
            entities.Filter(
                permission=arch_perm,
                role=[role.id],
                override=True,
                organization=[self.filter_org],
                location=[self.filter_loc],
            ).create()

    @tier1
    @upgrade
    def test_positive_create_overridable_filter(self):
        """Create overridable filter in role

        :id: c7ea9377-9b9e-495e-accd-3576166d504e

        :steps:

            1. Create a filter to which taxonomies can be associated.
                e.g Domain filter
            2. Override a filter with some taxonomies

        :expectedresults:

            1. Filter is created with taxonomies
            2. Override check is set to true
            3. Filter doesnt inherits taxonomies from role

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(
            name=role_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(role.name, role_name)
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        filtr = entities.Filter(
            permission=dom_perm,
            role=role.id,
            override=True,
            organization=[self.filter_org],
            location=[self.filter_loc],
        ).create()
        self.assertEqual(role.id, filtr.role.id)
        self.assertEqual(self.filter_org.id, filtr.organization[0].id)
        self.assertEqual(self.filter_loc.id, filtr.location[0].id)
        self.assertTrue(filtr.override)
        self.assertNotEqual(self.role_org.id, filtr.organization[0].id)
        self.assertNotEqual(self.role_loc.id, filtr.location[0].id)

    @tier1
    def test_positive_update_role_taxonomies(self):
        """Update role taxonomies which applies to its non-overrided filters

        :id: 902dcb32-2126-4ff4-b733-3e86749ccd1e

        :steps: Update existing role with different taxonomies

        :expectedresults: The taxonomies are applied only to non-overrided role
            filters

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(
            name=role_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(role.name, role_name)
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        filtr = entities.Filter(permission=dom_perm, role=role.id).create()
        self.assertEqual(role.id, filtr.role.id)
        role.organization = [self.filter_org]
        role.location = [self.filter_loc]
        role = role.update(['organization', 'location'])
        # Updated Role
        role = entities.Role(id=role.id).read()
        self.assertEqual(self.filter_org.id, role.organization[0].id)
        self.assertEqual(self.filter_loc.id, role.location[0].id)
        # Updated Filter
        filtr = entities.Filter(id=filtr.id).read()
        self.assertEqual(self.filter_org.id, filtr.organization[0].id)
        self.assertEqual(self.filter_loc.id, filtr.location[0].id)

    @tier1
    def test_negative_update_role_taxonomies(self):
        """Update role taxonomies which doesnt applies to its overrided filters

        :id: 9f3bf95a-f71a-4063-b51c-12610bc655f2

        :steps:

            1. Update existing role with different taxonomies

        :expectedresults: The overridden role filters are not updated

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(
            name=role_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(role.name, role_name)
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        filtr = entities.Filter(
            permission=dom_perm,
            role=role.id,
            override=True,
            organization=[self.filter_org],
            location=[self.filter_loc],
        ).create()
        self.assertEqual(role.id, filtr.role.id)
        # Creating new Taxonomies
        org_new = entities.Organization().create()
        loc_new = entities.Location().create()
        # Updating Taxonomies
        role.organization = [org_new]
        role.location = [loc_new]
        role = role.update(['organization', 'location'])
        # Updated Role
        role = entities.Role(id=role.id).read()
        self.assertEqual(org_new.id, role.organization[0].id)
        self.assertEqual(loc_new.id, role.location[0].id)
        # Updated Filter
        filtr = entities.Filter(id=filtr.id).read()
        self.assertNotEqual(org_new.id, filtr.organization[0].id)
        self.assertNotEqual(loc_new.id, filtr.location[0].id)

    @tier1
    def test_positive_disable_filter_override(self):
        """Unsetting override flag resets filter taxonomies

        :id: eaa7b921-7c12-45c5-989b-d82aa2b6e3a6

        :steps:

            1. Create role with organization A and Location A
            2. Create an overridden filter in role with organization B
                and Location B
            3. Set above filter override flag to False in role
            4. Get above role filters

        :expectedresults: The taxonomies of filters resets/synced to role
            taxonomies

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(
            name=role_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(role.name, role_name)
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        filtr = entities.Filter(
            permission=dom_perm,
            role=role.id,
            override=True,
            organization=[self.filter_org],
            location=[self.filter_loc],
        ).create()
        self.assertEqual(role.id, filtr.role.id)
        # Un-overriding
        filtr.override = False
        filtr = filtr.update(['override'])
        self.assertFalse(filtr.override)
        self.assertNotEqual(self.filter_org.id, filtr.organization[0].id)
        self.assertNotEqual(self.filter_loc.id, filtr.location[0].id)

    @tier1
    def test_positive_create_org_admin_from_clone(self):
        """Create Org Admin role which has access to most of the resources
        within organization

        :id: bf33b70a-25a9-4eb1-982f-03448d008ec8

        :steps: Create Org Admin role by cloning 'Organization admin' role
            which has most resources permissions

        :expectedresults: Org Admin role should be created successfully

        :CaseImportance: Critical

        :BZ: 1637436
        """
        default_org_admin = entities.Role().search(query={'search': 'name="Organization admin"'})
        org_admin = self.create_org_admin_role()
        default_filters = entities.Role(id=default_org_admin[0].id).read().filters
        orgadmin_filters = entities.Role(id=org_admin.id).read().filters
        self.assertEqual(len(default_filters), len(orgadmin_filters))

    @tier1
    def test_positive_create_cloned_role_with_taxonomies(self):
        """Taxonomies can be assigned to cloned role

        :id: 31079015-5ede-439a-a062-e20d1ffd66df

        :steps:

            1. Create Org Admin role by cloning 'Organization admin' role
            2. Set new taxonomies (locations and organizations) to cloned role

        :expectedresults:

            1. While cloning, role allows to set taxonomies
            2. New taxonomies should be applied to cloned role successfully

        :CaseImportance: Critical
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        org_admin = entities.Role(id=org_admin.id).read()
        self.assertEqual(self.role_org.id, org_admin.organization[0].id)
        self.assertEqual(self.role_loc.id, org_admin.location[0].id)

    @tier3
    def test_negative_access_entities_from_org_admin(self):
        """User can not access resources in taxonomies assigned to role if
        its own taxonomies are not same as its role

        :id: 225bed99-e768-461f-9972-4b9a4ffe3152

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to user
            4. Login with user and attempt to access resources

        :expectedresults: User should not be able to access any resources and
            permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """
        user = self.create_org_admin_user(role_taxos=True, user_taxos=True, same_taxos=False)
        domain = self.create_domain(orgs=[self.role_org.id], locs=[self.role_loc.id])
        sc = self.user_config(user)
        # Getting the domain from user
        with self.assertRaises(HTTPError):
            entities.Domain(sc, id=domain.id).read()

    @tier3
    def test_negative_access_entities_from_user(self):
        """User can not access resources within its own taxonomies if assigned
        role does not have permissions for user taxonomies

        :id: 5d663705-7b9e-4c42-82fa-db2f53715c91

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to user
            4. Login with user and attempt to access resources

        :expectedresults: User should not be able to access any resources and
            permissions in its own taxonomies

        :CaseLevel: System
        """
        user = self.create_org_admin_user(role_taxos=True, user_taxos=True, same_taxos=False)
        domain = self.create_domain(orgs=[self.filter_org.id], locs=[self.filter_loc.id])
        sc = self.user_config(user)
        # Getting the domain from user
        with self.assertRaises(HTTPError):
            entities.Domain(sc, id=domain.id).read()

    @tier2
    def test_positive_override_cloned_role_filter(self):
        """Cloned role filter overrides

        :id: 8a32ed5f-b93f-4f31-aff4-16602fbe7fab

        :steps:

            1. Create a role with overridden filter
            2. Clone above role
            3. Attempt to override the filter in cloned role

        :expectedresults: Filter in cloned role should be overridden

        :CaseLevel: Integration
        """
        role_name = gen_string('alpha')
        role = entities.Role(name=role_name).create()
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        entities.Filter(permission=dom_perm, role=role.id).create()
        cloned_role_name = gen_string('alpha')
        cloned_role = entities.Role(id=role.id).clone(data={'name': cloned_role_name})
        self.assertEqual(cloned_role_name, cloned_role['name'])
        filter_cloned_id = entities.Role(id=cloned_role['id']).read().filters[0].id
        filter_cloned = entities.Filter(id=filter_cloned_id).read()
        filter_cloned.override = True
        filter_cloned.organization = [self.role_org]
        filter_cloned.location = [self.role_loc]
        filter_cloned.update(['override', 'organization', 'location'])
        # Updated Filter
        filter_cloned = entities.Filter(id=filter_cloned_id).read()
        self.assertTrue(filter_cloned.override)
        self.assertEqual(self.role_org.id, filter_cloned.organization[0].id)
        self.assertEqual(self.role_loc.id, filter_cloned.location[0].id)

    @tier2
    def test_positive_emptiness_of_filter_taxonomies_on_role_clone(self):
        """Taxonomies of filters in cloned role are set to None for filters that
        are overridden in parent role

        :id: 4bfc44db-9089-4ce8-9fd8-8eab1a7cbd33

        :steps:

            1. Create a role with an overridden filter
            2. Overridden filter should have taxonomies assigned
            3. Clone above role
            4. GET cloned role filters

        :expectedresults:

            1. Taxonomies of the 'parent roles overridden filter' are set to
                None in cloned role
            2. Override flag is set to True in cloned role filter

        :CaseLevel: Integration
        """
        role = entities.Role(
            name=gen_string('alpha'), organization=[self.role_org], location=[self.role_loc]
        ).create()
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        entities.Filter(
            permission=dom_perm,
            role=role.id,
            override=True,
            organization=[self.filter_org],
            location=[self.filter_loc],
        ).create()
        cloned_role = entities.Role(id=role.id).clone(data={'name': gen_string('alpha')})
        cloned_role_filter = entities.Role(id=cloned_role['id']).read().filters[0]
        filter_cloned = entities.Filter(id=cloned_role_filter.id).read()
        self.assertFalse(filter_cloned.organization)
        self.assertFalse(filter_cloned.location)
        self.assertTrue(filter_cloned.override)

    @tier2
    def test_positive_clone_role_having_overridden_filter_with_taxonomies(self):  # noqa
        """When taxonomies assigned to cloned role, Unlimited and Override flag
        sets on filter for filter that is overridden in parent role

        :id: 233a4489-d327-4fa0-8a8a-b3a0905b9c12

        :steps:

            1. Create a role with organization A and Location A
            2. Create overridden role filter in organization B
                and Location B
            3. Clone above role and assign Organization A and Location A
                while cloning
            4. GET cloned role filter

        :expectedresults: Unlimited and Override flags should be set to True on
            filter for filter that is overridden in parent role

        :CaseLevel: Integration
        """
        role = entities.Role(
            name=gen_string('alpha'), organization=[self.role_org], location=[self.role_loc]
        ).create()
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        entities.Filter(
            permission=dom_perm,
            role=role.id,
            override=True,
            organization=[self.filter_org],
            location=[self.filter_loc],
        ).create()
        cloned_role = entities.Role(id=role.id).clone(
            data={
                'name': gen_string('alpha'),
                'organization_ids': [self.role_org.id],
                'location_ids': [self.role_loc.id],
            }
        )
        cloned_role_filter = entities.Role(id=cloned_role['id']).read().filters[0]
        cloned_filter = entities.Filter(id=cloned_role_filter.id).read()
        self.assertTrue(cloned_filter.unlimited)
        self.assertTrue(cloned_filter.override)

    @tier2
    def test_positive_clone_role_having_non_overridden_filter_with_taxonomies(self):  # noqa
        """When taxonomies assigned to cloned role, Neither unlimited nor
        override sets on filter for filter that is not overridden in parent
        role

        :id: abc8d419-0c1a-4043-b739-833714663127

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter without overriding
            3. Clone above role and assign Organization A and Location A
                while cloning
            4. GET cloned role filter

        :expectedresults: Both unlimited and override flag should be set to
            False on filter for filter that is not overridden in parent role

        :CaseLevel: Integration
        """
        role = entities.Role(
            name=gen_string('alpha'), organization=[self.role_org], location=[self.role_loc]
        ).create()
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        entities.Filter(permission=dom_perm, role=role.id).create()
        cloned_role = entities.Role(id=role.id).clone(
            data={
                'name': gen_string('alpha'),
                'organization_ids': [self.role_org.id],
                'location_ids': [self.role_loc.id],
            }
        )
        cloned_role_filter = entities.Role(id=cloned_role['id']).read().filters[0]
        cloned_filter = entities.Filter(id=cloned_role_filter.id).read()
        self.assertFalse(cloned_filter.unlimited)
        self.assertFalse(cloned_filter.override)

    @tier2
    def test_positive_clone_role_having_unlimited_filter_with_taxonomies(self):
        """When taxonomies assigned to cloned role, Neither unlimited nor
        override sets on filter for filter that is unlimited in parent role

        :id: 7cb99401-9af2-40b8-9300-0a6333f8aaa0

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter with unlimited check
            3. Clone above role and assign Organization A and Location A
                while cloning
            4. GET cloned role filter

        :expectedresults: Both unlimited and override flags should be set to
            False on filter for filter that is unlimited in parent role

        :CaseLevel: Integration
        """
        role = entities.Role(
            name=gen_string('alpha'), organization=[self.role_org], location=[self.role_loc]
        ).create()
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        entities.Filter(permission=dom_perm, role=role.id, unlimited=True).create()
        cloned_role = entities.Role(id=role.id).clone(
            data={
                'name': gen_string('alpha'),
                'organization_ids': [self.role_org.id],
                'location_ids': [self.role_loc.id],
            }
        )
        cloned_role_filter = entities.Role(id=cloned_role['id']).read().filters[0]
        cloned_filter = entities.Filter(id=cloned_role_filter.id).read()
        self.assertFalse(cloned_filter.unlimited)
        self.assertFalse(cloned_filter.override)

    @tier2
    def test_positive_clone_role_having_overridden_filter_without_taxonomies(self):  # noqa
        """When taxonomies not assigned to cloned role, Unlimited and override
        flags sets on filter for filter that is overridden in parent role

        :id: 1af58f93-46f8-411a-8468-43abc34ef966

        :steps:

            1. Create a role with organization A and Location A
            2. Create overridden role filter in organization B
                and Location B
            3. Clone above role without assigning taxonomies
            4. GET cloned role filter

        :expectedresults: Both unlimited and Override flags should be set to
            True on filter for filter that is overridden in parent role

        :CaseLevel: Integration
        """
        role = entities.Role(
            name=gen_string('alpha'), organization=[self.role_org], location=[self.role_loc]
        ).create()
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        entities.Filter(
            permission=dom_perm,
            role=role.id,
            override=True,
            organization=[self.filter_org],
            location=[self.filter_loc],
        ).create()
        cloned_role = entities.Role(id=role.id).clone(data={'name': gen_string('alpha')})
        cloned_role_filter = entities.Role(id=cloned_role['id']).read().filters[0]
        cloned_filter = entities.Filter(id=cloned_role_filter.id).read()
        self.assertTrue(cloned_filter.unlimited)
        self.assertTrue(cloned_filter.override)

    @tier2
    def test_positive_clone_role_without_taxonomies_non_overided_filter(self):
        """When taxonomies not assigned to cloned role, only unlimited but not
        override flag sets on filter for filter that is overridden in parent
        role

        :id: 85eea70a-482a-487c-affa-dec3891a1388

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter without overriding
            3. Clone above role without assigning taxonomies
            4. GET cloned role filter

        :expectedresults:

            1. Unlimited flag should be set to True
            2. Override flag should be set to False

        :CaseLevel: Integration

        :BZ: 1488908
        """
        role = entities.Role(
            name=gen_string('alpha'), organization=[self.role_org], location=[self.role_loc]
        ).create()
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        entities.Filter(permission=dom_perm, role=role.id).create()
        cloned_role = entities.Role(id=role.id).clone(
            data={
                'role': {'name': gen_string('alpha'), 'location_ids': [], 'organization_ids': []}
            }
        )
        cloned_role_filter = entities.Role(id=cloned_role['id']).read().filters[0]
        cloned_filter = entities.Filter(id=cloned_role_filter.id).read()
        self.assertTrue(cloned_filter.unlimited)
        self.assertFalse(cloned_filter.override)

    @tier2
    def test_positive_clone_role_without_taxonomies_unlimited_filter(self):
        """When taxonomies not assigned to cloned role, Unlimited and override
        flags sets on filter for filter that is unlimited in parent role

        :id: 8ffc7b34-1a25-4663-b3c8-0bbf5fcb61aa

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter with unlimited check
            3. Clone above role without assigning taxonomies
            4. GET cloned role filter

        :expectedresults:

            1. Unlimited flag should be set to True
            2. Override flag should be set to False

        :CaseLevel: Integration

        :BZ: 1488908
        """
        role = entities.Role(
            name=gen_string('alpha'), organization=[self.role_org], location=[self.role_loc]
        ).create()
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        entities.Filter(permission=dom_perm, role=role.id, unlimited=True).create()
        cloned_role = entities.Role(id=role.id).clone(
            data={
                'role': {'name': gen_string('alpha'), 'location_ids': [], 'organization_ids': []}
            }
        )
        cloned_role_filter = entities.Role(id=cloned_role['id']).read().filters[0]
        cloned_filter = entities.Filter(id=cloned_role_filter.id).read()
        self.assertTrue(cloned_filter.unlimited)
        self.assertFalse(cloned_filter.override)

    @tier2
    def test_positive_force_unlimited(self):
        """Unlimited flag forced sets to filter when no taxonomies are set to role
        and filter

        :id: b94d35f3-be63-4b05-b42e-a77a1c48a4f3

        :steps:

            1. Create a role with organization A and Location A
            2. Create a role filter without override and unlimited check
            3. Remove taxonomies assigned earlier to role and ensure
                no taxonomies are assigned to role
            4. GET Role filter

        :expectedresults: Unlimited flag should be forcefully set on filter
            when no taxonomies are set to role and filter

        :CaseLevel: Integration
        """
        role_name = gen_string('alpha')
        role = entities.Role(
            name=role_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(role_name, role.name)
        dom_perm = entities.Permission().search(query={'search': 'resource_type="Domain"'})
        filtr = entities.Filter(permission=dom_perm, role=role.id).create()
        self.assertEqual(role.id, filtr.role.id)
        self.assertFalse(filtr.override)
        self.assertFalse(filtr.unlimited)
        role.organization = []
        role.location = []
        role = role.update(['organization', 'location'])
        self.assertEqual(role.organization, [])
        self.assertEqual(role.location, [])
        # Get updated filter
        filtr = entities.Filter(id=filtr.id).read()
        self.assertTrue(filtr.unlimited)

    @tier3
    @upgrade
    def test_positive_user_group_users_access_as_org_admin(self):
        """Users in usergroup can have access to the resources in taxonomies if
        the taxonomies of Org Admin role is same

        :id: e7f25d82-3b69-4b8e-b5fc-714d33f91505

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create two users without assigning roles while creating them
            4. Assign Organization A and Location A to both users
            5. Create an user group with above two users
            6. Assign Org Admin role to User Group

        :expectedresults: Both the user should have access to the resources of
            organization A and Location A

        :CaseLevel: System
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        userone_login = gen_string('alpha')
        userone_pass = gen_string('alphanumeric')
        user_one = entities.User(
            login=userone_login,
            password=userone_pass,
            organization=[self.role_org.id],
            location=[self.role_loc.id],
        ).create()
        self.assertEqual(userone_login, user_one.login)
        usertwo_login = gen_string('alpha')
        usertwo_pass = gen_string('alphanumeric')
        user_two = entities.User(
            login=usertwo_login,
            password=usertwo_pass,
            organization=[self.role_org.id],
            location=[self.role_loc.id],
        ).create()
        self.assertEqual(usertwo_login, user_two.login)
        ug_name = gen_string('alpha')
        user_group = entities.UserGroup(
            name=ug_name, role=[org_admin.id], user=[user_one.id, user_two.id]
        ).create()
        self.assertEqual(user_group.name, ug_name)
        # Creating Subnets and Domains to verify if user really can access them
        subnet = entities.Subnet(
            name=gen_string('alpha'), organization=[self.role_org.id], location=[self.role_loc.id]
        ).create()
        domain = entities.Domain(
            name=gen_string('alpha'), organization=[self.role_org.id], location=[self.role_loc.id]
        ).create()
        for login, password in ((userone_login, userone_pass), (usertwo_login, usertwo_pass)):
            with self.subTest(login):
                sc = ServerConfig(auth=(login, password), url=self.sat_url, verify=False)
                with self.assertNotRaises(HTTPError):
                    entities.Domain(sc).search(
                        query={
                            'organization-id': self.role_org.id,
                            'location-id': self.role_loc.id,
                        }
                    )
                    entities.Subnet(sc).search(
                        query={
                            'organization-id': self.role_org.id,
                            'location-id': self.role_loc.id,
                        }
                    )
                self.assertIn(domain.id, [dom.id for dom in entities.Domain(sc).search()])
                self.assertIn(subnet.id, [sub.id for sub in entities.Subnet(sc).search()])

    @tier3
    def test_positive_user_group_users_access_contradict_as_org_admins(self):
        """Users in usergroup can/cannot have access to the resources in
        taxonomies depends on the taxonomies of Org Admin role is same/not_same

        :id: f597b8ca-0e4d-4970-837e-bbc943a93c24

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an user without assigning roles while creating them and
                assign Organization B and Location B
            4. Create another user without assigning roles while creating them
                and assign Organization A and Location A
            5. Create an user group, add above two users to the user group

        :expectedresults:

            1. User assigned to Organization B and Location B shouldn't have
                access to the resources of organization A,B and Location A,B
            2. User assigned to Organization A and Location A should have
                access to the resources of organization A and Location A

        :CaseLevel: System
        """

    @tier2
    def test_negative_assign_org_admin_to_user_group(self):
        """Users in usergroup can not have access to the resources in
        taxonomies if the taxonomies of Org Admin role is not same

        :id: 4ebcf809-9ba1-4634-8bfa-9e6c67b534f3

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create two users without assigning roles while creating them
            4. Assign Organization B and Location B to both users
            5. Create an user group add above two users to the user group

        :expectedresults: Both the user shouldn't have access to the resources
            of organization A,B and Location A,B

        :CaseLevel: System
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        user_one = self.create_simple_user(filter_taxos=True)
        user_two = self.create_simple_user(filter_taxos=True)
        ug_name = gen_string('alpha')
        user_group = entities.UserGroup(
            name=ug_name, role=[org_admin.id], user=[user_one.id, user_two.id]
        ).create()
        self.assertEqual(user_group.name, ug_name)
        dom = self.create_domain(orgs=[self.role_org.id], locs=[self.role_loc.id])
        for user in [user_one, user_two]:
            with self.subTest(user):
                sc = self.user_config(user)
                with self.assertRaises(HTTPError):
                    entities.Domain(sc, id=dom.id).read()

    @tier2
    def test_negative_assign_taxonomies_by_org_admin(self):
        """Org Admin doesn't have permissions to assign org to any of
        its entities

        :id: d8586573-70df-4438-937f-4869583a3d58

        :steps:

            1. Create Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A,B and Location A,B to the Org Admin
                role
            3. Create user and assign above Org Admin role
            4. Assign Organization A,B and Location A,B to the user
            5. Login from the new user and attempt to assign organization(s)
                to any resource

        :expectedresults: Org Admin should not be able to assign the
            organizations to any of its resources

        :CaseLevel: Integration
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        # Creating resource
        dom_name = gen_string('alpha')
        dom = entities.Domain(
            name=dom_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(dom_name, dom.name)
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(
            login=user_login,
            password=user_pass,
            role=[org_admin.id],
            organization=[self.role_org],
            location=[self.role_loc],
        ).create()
        self.assertEqual(user_login, user.login)
        sc = ServerConfig(auth=(user_login, user_pass), url=self.sat_url, verify=False)
        # Getting the domain from user1
        dom = entities.Domain(sc, id=dom.id).read()
        dom.organization = [self.filter_org]
        with self.assertRaises(HTTPError):
            dom.update(['organization'])

    @tier1
    def test_positive_remove_org_admin_role(self):
        """Super Admin user can remove Org Admin role

        :id: 03fac76c-22ac-43cf-9068-b96e255b3c3c

        :steps:

            1. Create Org Admin by cloning 'Organization admin' role
            2. Assign any taxonomies to it
            3. Create an user and assign above role to user
            4. Delete the Org Admin role

        :expectedresults: Super Admin should be able to remove Org Admin role

        :CaseImportance: Critical
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(login=user_login, password=user_pass, role=[org_admin.id]).create()
        self.assertEqual(user_login, user.login)
        with self.assertNotRaises(HTTPError):
            entities.Role(id=org_admin.id).delete()
        # Getting updated user
        user = entities.User(id=user.id).read()
        self.assertNotIn(org_admin.id, [role.id for role in user.role])

    @tier2
    def test_positive_taxonomies_control_to_superadmin_with_org_admin(self):
        """Super Admin can access entities in taxonomies assigned to Org Admin

        :id: 37db0b40-ed35-4e70-83e8-83cff27caae2

        :steps:

            1. Create Org Admin role and assign organization A and Location A
            2. Create User and assign above Org Admin role
            3. Login with SuperAdmin who created the above Org Admin role and
                access entities in Organization A and Location A

        :expectedresults: Super admin should be able to access the entities in
            taxonomies assigned to Org Admin

        :CaseLevel: Integration
        """
        user = self.create_org_admin_user(role_taxos=True, user_taxos=True, same_taxos=True)
        sc = self.user_config(user)
        # Creating resource
        dom_name = gen_string('alpha')
        dom = entities.Domain(
            sc, name=dom_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(dom_name, dom.name)
        with self.assertNotRaises(HTTPError):
            entities.Subnet().search(
                query={'organization-id': self.role_org.id, 'location-id': self.role_loc.id}
            )

    @tier2
    def test_positive_taxonomies_control_to_superadmin_without_org_admin(self):
        """Super Admin can access entities in taxonomies assigned to Org Admin
        after deleting Org Admin role/user

        :id: 446f66a5-16e0-4298-b326-262913502955

        :steps:

            1. Create Org Admin role and assign organization A and Location A
            2. Create User and assign above Org Admin role
            3. Delete Org Admin role also the User created above
            4. Login with SuperAdmin who created the above Org Admin role and
                access entities in Organization A and Location A

        :expectedresults: Super admin should be able to access the entities in
            taxonomies assigned to Org Admin after deleting Org Admin

        :CaseLevel: Integration
        """
        user = self.create_org_admin_user(role_taxos=True, user_taxos=True, same_taxos=True)
        sc = self.user_config(user)
        # Creating resource
        dom_name = gen_string('alpha')
        dom = entities.Domain(
            sc, name=dom_name, organization=[self.role_org], location=[self.role_loc]
        ).create()
        self.assertEqual(dom_name, dom.name)
        user_role = entities.Role(id=user.role[0].id).read()
        entities.Role(id=user_role.id).delete()
        entities.User(id=user.id).delete()
        with self.assertRaises(HTTPError):
            user_role.read()
            user.read()
        with self.assertNotRaises(HTTPError):
            entities.Domain().search(
                query={'organization-id': self.role_org.id, 'location-id': self.role_loc.id}
            )

    @tier1
    @upgrade
    def test_negative_create_roles_by_org_admin(self):
        """Org Admin doesnt have permissions to create new roles

        :id: 806ecc16-0dc7-405b-90d3-0584eced27a3

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to create a new role

        :expectedresults: Org Admin should not have permission by default to
            create new role
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(
            login=user_login,
            password=user_pass,
            role=[org_admin.id],
            organization=[self.role_org],
            location=[self.role_loc],
        ).create()
        self.assertEqual(user_login, user.login)
        sc = ServerConfig(auth=(user_login, user_pass), url=self.sat_url, verify=False)
        role_name = gen_string('alpha')
        with self.assertRaises(HTTPError):
            entities.Role(
                sc, name=role_name, organization=[self.role_org], location=[self.role_loc]
            ).create()

    @tier1
    def test_negative_modify_roles_by_org_admin(self):
        """Org Admin has no permissions to modify existing roles

        :id: 93ad9d7d-afad-4403-84a9-d59cc2ddfa58

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to update any existing role to modify

        :expectedresults: Org Admin should not have permissions to update
            existing roles
        """
        user = self.create_org_admin_user(role_taxos=True, user_taxos=True, same_taxos=True)
        test_role = entities.Role().create()
        sc = self.user_config(user)
        test_role = entities.Role(sc, id=test_role.id).read()
        with self.assertRaises(HTTPError):
            test_role.organization = [self.role_org]
            test_role.location = [self.role_loc]
            test_role.update(['organization', 'location'])

    @tier2
    def test_negative_admin_permissions_to_org_admin(self):
        """Org Admin has no access to Super Admin user

        :id: cdebf9a8-35c2-4730-8423-de47a2c15ff5

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to info Super Admin user

        :expectedresults: Org Admin should not have access of Admin user

        :CaseLevel: Integration
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(
            login=user_login,
            password=user_pass,
            role=[org_admin.id],
            organization=[self.role_org],
            location=[self.role_loc],
        ).create()
        self.assertEqual(user_login, user.login)
        sc = ServerConfig(auth=(user_login, user_pass), url=self.sat_url, verify=False)
        with self.assertRaises(HTTPError):
            entities.User(sc, id=1).read()

    @tier2
    @upgrade
    def test_positive_create_user_by_org_admin(self):
        """Org Admin can create new users

        :id: f4edbe25-3ee6-46d6-8fca-a04f6ddc8eed

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to create new users
            5. Attempt to create location

        :expectedresults:

            1. Org Admin should be able to create new users
            2. Only Org Admin role should be available to assign to its users
            3. Org Admin should be able to assign Org Admin role to its users
            4. Org Admin should be able create locations

        :BZ: 1538316, 1760701

        :CaseLevel: Integration
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(
            login=user_login,
            password=user_pass,
            role=[org_admin.id],
            organization=[self.role_org],
            location=[self.role_loc],
        ).create()
        self.assertEqual(user_login, user.login)
        sc_user = ServerConfig(auth=(user_login, user_pass), url=self.sat_url, verify=False)
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(
            sc_user,
            login=user_login,
            password=user_pass,
            role=[org_admin.id],
            organization=[self.role_org],
            location=[self.role_loc],
        ).create()
        self.assertEqual(user_login, user.login)
        self.assertEqual(org_admin.id, user.role[0].id)
        if not is_open('BZ:1760701'):
            name = gen_string('alphanumeric')
            location = entities.Location(sc_user, name=name).create()
            self.assertEqual(location.name, name)

    @tier2
    def test_positive_access_users_inside_org_admin_taxonomies(self):
        """Org Admin can access users inside its taxonomies

        :id: c43275de-e0ff-4a22-b103-391a5ab81874

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user A and assign Org A and Location A
            3. Assign Org Admin role to User A
            4. Create another user B and assign Org A and Location A
            5. Assign any role to user B that does have access to Org A and
                Location A
            6. Login with Org Admin user A and attempt to view user B

        :expectedresults: Org Admin should be able to access users inside
            its taxonomies

        :CaseLevel: Integration
        """
        user = self.create_org_admin_user(role_taxos=True, user_taxos=True, same_taxos=True)
        test_user = self.create_simple_user(filter_taxos=False)
        sc = self.user_config(user)
        with self.assertNotRaises(HTTPError):
            entities.User(sc, id=test_user.id).read()

    @pytest.mark.skip_if_open('BZ:1694199')
    @tier2
    def test_positive_create_nested_location(self):
        """Org Admin can create nested locations

        :id: 971bc909-96a5-4614-b254-04a51c708432

        :bz: 1694199

        :steps:
            1. Create a regular user and associate it with existing location
            2. Add org_admin rights to that user
            3. Attempt to create a nested location

        :expectedresults: after adding the needed permissions, user should be
            able to create nested locations

        :CaseLevel: Integration
        """
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(
            login=user_login,
            password=user_pass,
            organization=[self.role_org],
            location=[self.role_loc],
        ).create()
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id], locs=[self.role_loc.id])
        user.role = [org_admin]
        user = user.update(['role'])
        sc = ServerConfig(auth=(user_login, user_pass), url=self.sat_url, verify=False)
        name = gen_string('alphanumeric')
        location = entities.Location(sc, name=name, parent=self.role_loc.id).create()
        self.assertEqual(location.name, name)

    @tier2
    def test_negative_access_users_outside_org_admin_taxonomies(self):
        """Org Admin can not access users outside its taxonomies

        :id: c784b146-60e8-4d6b-ac87-f8351b7e61ab

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user A and assign Org A and Location A
            3. Assign Org Admin role to User A
            4. Create another user B and assign Org B and Location B
            5. Assign any role to user B that doesnt have access to Org A and
                Location A
            6. Login with Org Admin user A and attempt to view user B

        :expectedresults: Org Admin should not be able to access users outside
            its taxonomies

        :CaseLevel: Integration
        """
        user = self.create_org_admin_user(role_taxos=True, user_taxos=True, same_taxos=True)
        test_user = self.create_simple_user(filter_taxos=True)
        sc = self.user_config(user)
        with self.assertRaises(HTTPError):
            entities.User(sc, id=test_user.id).read()

    @tier1
    def test_negative_create_taxonomies_by_org_admin(self):
        """Org Admin cannot define/create organizations but can create
            locations

        :id: 56d9e204-395c-4d6a-b821-43c2f4fe8822

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to create Organizations and locations

        :expectedresults:

            1. Org Admin should not have access to create organizations
            2. Org Admin should have access to create locations
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id])
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(
            login=user_login,
            password=user_pass,
            role=[org_admin.id],
            organization=[self.role_org],
            location=[self.role_loc],
        ).create()
        self.assertEqual(user_login, user.login)
        sc = ServerConfig(auth=(user_login, user_pass), url=self.sat_url, verify=False)
        with self.assertRaises(HTTPError):
            entities.Organization(sc, name=gen_string('alpha')).create()
        with self.assertNotRaises(HTTPError):
            loc_name = gen_string('alpha')
            loc = entities.Location(sc, name=loc_name).create()
        self.assertEqual(loc_name, loc.name)

    @upgrade
    @tier1
    def test_positive_access_all_global_entities_by_org_admin(self):
        """Org Admin can access all global entities in any taxonomies
        regardless of its own assigned taxonomies

        :id: add5feb3-7a3f-45a1-a633-49f1141b029b

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user and assign Org A,B and Location A,B
            3. Assign Org Admin role to User
            4. Login with Org Admin user
            5. Attempt to create all the global entities in org B and Loc B
                e.g Architectures, Operating System

        :expectedresults: Org Admin should have access to all the global
            entities in any taxonomies
        """
        org_admin = self.create_org_admin_role(orgs=[self.role_org.id])
        user_login = gen_string('alpha')
        user_pass = gen_string('alphanumeric')
        user = entities.User(
            login=user_login,
            password=user_pass,
            role=[org_admin.id],
            organization=[self.role_org, self.filter_org],
            location=[self.role_loc, self.filter_loc],
        ).create()
        self.assertEqual(user_login, user.login)
        sc = ServerConfig(auth=(user_login, user_pass), url=self.sat_url, verify=False)
        with self.assertNotRaises(HTTPError):
            for entity in [
                entities.Architecture,
                entities.Audit,
                entities.Bookmark,
                entities.CommonParameter,
                entities.LibvirtComputeResource,
                entities.OVirtComputeResource,
                entities.VMWareComputeResource,
                entities.ConfigGroup,
                entities.Errata,
                entities.OperatingSystem,
            ]:
                entity(sc).search()

    @stubbed()
    @tier3
    def test_negative_access_entities_from_ldap_org_admin(self):
        """LDAP User can not access resources in taxonomies assigned to role if
        its own taxonomies are not same as its role

        :id: 7fab713a-035f-496a-a7a6-86407a46a480

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to LDAP user
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should not be able to access resources and
            permissions in taxonomies selected in Org Admin role

        :CaseLevel: System

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_ldap_user(self):
        """LDAP User can not access resources within its own taxonomies if
        assigned role does not have permissions for same taxonomies

        :id: cd8cec18-a0bf-4e9c-aad5-71fb46108690

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to LDAP user
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should not be able to access any resources
            and permissions in its own taxonomies

        :CaseLevel: System

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier3
    def test_positive_assign_org_admin_to_ldap_user_group(self):
        """Users in LDAP usergroup can access to the resources in taxonomies if
        the taxonomies of Org Admin role are same

        :id: d12d78f9-d3e9-4931-8b03-9fc22cfd8cfe

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an LDAP usergroup with two users
            4. Assign Organization A and Location A to LDAP usergroup
            5. Assign Org Admin role to LDAP usergroup

        :expectedresults: Users in LDAP usergroup should have access to the
            resources in taxonomies if the taxonomies of Org Admin role are
            same

        :CaseLevel: System

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier3
    def test_negative_assign_org_admin_to_ldap_user_group(self):
        """Users in LDAP usergroup can not have access to the resources in
        taxonomies if the taxonomies of Org Admin role is not same

        :id: f62800eb-5408-4dbe-8d11-6d8a2c770dbc

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an LDAP usergroup with two users
            4. Assign Organization B and Location B to LDAP usergroup
            5. Assign Org Admin role to LDAP usergroup

        :expectedresults: Users in LDAP usergroup should not have access to the
            resources in taxonomies if the taxonomies of Org Admin role is not
            same

        :CaseLevel: System

        :CaseAutomation: notautomated
        """


class RoleSearchFilterTestCase(APITestCase):
    """
    Tests adding additional search filters to role filters.
    """

    @stubbed
    @tier3
    def test_positive_role_lce_search(self):
        """Test role with search filter using lifecycle enviroment.

        :id: 7147f402-8cc0-4f6a-affe-5a0dd122a05a

        :steps:
            1. Create Lifecycle Environments DEV
            2. Create Host dev1 in DEV lifecycle environment.
            3. Create role 'integrationsrole' role:
                - see https://access.redhat.com/articles/3359731
                - Filters: "view host", "view hostgroups", "view facts"
                - Add search filter to view host rule "lifecycle_environment = DEV"
                - Set Organization and Location for integrationsrole to the same as dev1
            4. Create apiuser with integrationsrole.
            5. Using API with user apiuser read hosts facts of dev1.
                (ie  curl -s -u 'apiuser:redhat' -k https://$SATELLITE/api/v2/hosts/$dev1_id/facts)

        :expectedresults: The user is able to get dev1 facts.

        :BZ: 1651699
        """

    @stubbed
    @tier3
    def test_negative_role_lce_search(self):
        """Test role with search filter using lifecycle environment.

        :id: 19d97cda-642b-4758-94c9-b854ca84806d

        :steps:
            1. Create Lifecycle Environments DEV, QA (id=3)
            2. Create Host qa1 in QA lifecycle environment
            3. Create role 'integrationsrole' role:
                - see https://access.redhat.com/articles/3359731
                - Filters: "view host", "view hostgroups", "view facts"
                - Added search filter to view host rule "lifecycle_environment = DEV"
                - Set Organization and location for integrationsrole to the same as dev1
            4. Create apiuser with integrationsrole.
            5. Using API with user apiuser read hosts facts of qa1.
                (ie  curl -s -u 'apiuser:redhat' -k https://$SATELLITE/api/v2/hosts/$qa1_id/facts)

        :expectedresults: The user is not allowed to view qa1 facts.

        :BZ: 1651699
        """
