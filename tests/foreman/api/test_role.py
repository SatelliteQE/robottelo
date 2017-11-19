"""Unit tests for the ``roles`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/roles.html


:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from nailgun.config import ServerConfig
from requests.exceptions import HTTPError
from robottelo.datafactory import gen_string, generate_strings_list
from robottelo.decorators import (
    bz_bug_is_open,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.test import APITestCase


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
        for name in generate_strings_list(exclude_types=['html']):
            with self.subTest(name):
                if bz_bug_is_open(1112657) and name in [
                        'cjk', 'latin1', 'utf8']:
                    self.skipTest('Bugzilla bug 1112657 is open.')
                self.assertEqual(entities.Role(name=name).create().name, name)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete a role with name ``name_generator()``.

        :id: 6e1d9f9c-3cbb-460b-8ef8-4a156e6552a0

        :expectedresults: The role cannot be fetched after it is deleted.

        :CaseImportance: Critical
        """
        for name in generate_strings_list(exclude_types=['html']):
            with self.subTest(name):
                if bz_bug_is_open(1112657) and name in [
                        'cjk', 'latin1', 'utf8']:
                    self.skipTest('Bugzilla bug 1112657 is open.')
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
        for name in generate_strings_list(exclude_types=['html']):
            with self.subTest(name):
                if bz_bug_is_open(1112657) and name in [
                        'cjk', 'latin1', 'utf8']:
                    self.skipTest('Bugzilla bug 1112657 is open.')
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
        default_org_admin = entities.Role().search(
            query={'search': u'name="Organization admin"'})
        org_admin = entities.Role(id=default_org_admin[0].id).clone(
            data={
                'role': {
                    'name': name,
                    'organization_ids': orgs or [],
                    'location_ids': locs or []
                }
            }
        )
        return entities.Role(id=org_admin['id']).read()

    @classmethod
    def setUpClass(cls):
        """Creates two orgs and locations that will be used by all the
        underlying tests
        """
        super(CannedRoleTestCases, cls).setUpClass()
        # These two will be used as role taxonomies
        cls.org1 = entities.Organization().create()
        cls.loc1 = entities.Location().create()
        # These two will be used as filter taxonomies
        cls.org2 = entities.Organization().create()
        cls.loc2 = entities.Location().create()

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
            name=role_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(role.name, role_name)
        self.assertIn(self.org1.id, [org.id for org in role.organization])
        self.assertIn(self.loc1.id, [loc.id for loc in role.location])

    @tier1
    def test_positive_create_role_without_taxonomies(self):
        """Create role without taxonomies

        :id: fe65a691-1b04-4bfe-a24b-adb48feb31d1

        :steps: Create new role without any taxonomies

        :expectedresults: New role is created without taxonomies

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role = entities.Role(
            name=role_name,
            organization=[],
            location=[]
        ).create()
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
        role1 = entities.Role(
            name=role_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(role1.name, role_name)
        dom_perm = entities.Permission(resource_type='Domain').search()
        filter1 = entities.Filter(permission=dom_perm, role=role1.id).create()
        self.assertEqual(role1.id, filter1.role.id)
        self.assertIn(self.org1.id, [org.id for org in filter1.organization])
        self.assertIn(self.loc1.id, [loc.id for loc in filter1.location])
        self.assertFalse(filter1.override)

    @tier1
    def test_positive_create_non_overridable_filter(self):
        """Create non overridable filter in role

        :id: f891e2e1-76f8-4edf-8c96-b41d05483298

        :steps: Create a filter to which taxonomies cannot be associated.
            e.g Architecture filter

        :expectedresults:

            1. Filter is created without taxonomies
            2. Override check is set to false
            3. Filter doesnt inherit taxonomies from role

        :CaseImportance: Critical
        """
        role_name = gen_string('alpha')
        role1 = entities.Role(name=role_name).create()
        self.assertEqual(role1.name, role_name)
        arch_perm = entities.Permission(resource_type='Architecture').search()
        filter1 = entities.Filter(permission=arch_perm, role=role1.id).create()
        self.assertEqual(role1.id, filter1.role.id)
        self.assertEqual(filter1.organization, [])
        self.assertEqual(filter1.location, [])
        self.assertFalse(filter1.override)

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
        role1 = entities.Role(name=role_name).create()
        self.assertEqual(role1.name, role_name)
        arch_perm = entities.Permission(resource_type='Architecture').search()
        with self.assertRaises(HTTPError):
            entities.Filter(
                permission=arch_perm,
                role=[role1.id],
                override=True,
                organization=[self.org2],
                location=[self.loc2]
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
        role1 = entities.Role(
            name=role_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(role1.name, role_name)
        dom_perm = entities.Permission(resource_type='Domain').search()
        filter1 = entities.Filter(
            permission=dom_perm,
            role=role1.id,
            override=True,
            organization=[self.org2],
            location=[self.loc2]
        ).create()
        self.assertEqual(role1.id, filter1.role.id)
        self.assertIn(self.org2.id, [org.id for org in filter1.organization])
        self.assertIn(self.loc2.id, [loc.id for loc in filter1.location])
        self.assertTrue(filter1.override)
        self.assertNotIn(
            self.org1.id,
            [org.id for org in filter1.organization])
        self.assertNotIn(self.loc1.id, [loc.id for loc in filter1.location])

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
        role1 = entities.Role(
            name=role_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(role1.name, role_name)
        dom_perm = entities.Permission(resource_type='Domain').search()
        filter1 = entities.Filter(permission=dom_perm, role=role1.id,).create()
        self.assertEqual(role1.id, filter1.role.id)
        role1.organization = [self.org2]
        role1.location = [self.loc2]
        role1 = role1.update(['organization', 'location'])
        # Updated Role
        role1 = entities.Role(id=role1.id).read()
        self.assertIn(self.org2.id, [org.id for org in role1.organization])
        self.assertIn(self.loc2.id, [loc.id for loc in role1.location])
        # Updated Filter
        filter1 = entities.Filter(id=filter1.id).read()
        self.assertIn(self.org2.id, [org.id for org in filter1.organization])
        self.assertIn(self.loc2.id, [loc.id for loc in filter1.location])

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
        role1 = entities.Role(
            name=role_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(role1.name, role_name)
        dom_perm = entities.Permission(resource_type='Domain').search()
        filter1 = entities.Filter(
            permission=dom_perm,
            role=role1.id,
            override=True,
            organization=[self.org2],
            location=[self.loc2]
        ).create()
        self.assertEqual(role1.id, filter1.role.id)
        # Creating new Taxonomies
        org3 = entities.Organization().create()
        loc3 = entities.Location().create()
        # Updating Taxonomies
        role1.organization = [org3]
        role1.location = [loc3]
        role1 = role1.update(['organization', 'location'])
        # Updated Role
        role1 = entities.Role(id=role1.id).read()
        self.assertIn(org3.id, [org.id for org in role1.organization])
        self.assertIn(loc3.id, [loc.id for loc in role1.location])
        # Updated Filter
        filter1 = entities.Filter(id=filter1.id).read()
        self.assertNotIn(org3.id, [org.id for org in filter1.organization])
        self.assertNotIn(loc3.id, [loc.id for loc in filter1.location])

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
        role1 = entities.Role(
            name=role_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(role1.name, role_name)
        dom_perm = entities.Permission(resource_type='Domain').search()
        filter1 = entities.Filter(
            permission=dom_perm,
            role=role1.id,
            override=True,
            organization=[self.org2],
            location=[self.loc2]
        ).create()
        self.assertEqual(role1.id, filter1.role.id)
        # Un-overriding
        filter1.override = False
        filter1 = filter1.update(['override'])
        self.assertFalse(filter1.override)
        self.assertNotIn(
            self.org2.id, [org.id for org in filter1.organization])
        self.assertNotIn(self.loc2.id, [loc.id for loc in filter1.location])

    @tier1
    def test_positive_create_org_admin_from_clone(self):
        """Create Org Admin role which has access to most of the resources
        within organization

        :id: bf33b70a-25a9-4eb1-982f-03448d008ec8

        :steps: Create Org Admin role by cloning 'Organization admin' role
            which has most resources permissions

        :expectedresults: Org Admin role should be created successfully

        :CaseImportance: Critical
        """
        default_org_admin = entities.Role().search(
            query={'search': u'name="Organization admin"'})
        org_admin = self.create_org_admin_role()
        default_filters = entities.Role(
            id=default_org_admin[0].id).read().filters
        orgadmin_filters = entities.Role(
            id=org_admin.id).read().filters
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
        org_admin = self.create_org_admin_role(
            orgs=[self.org1.id], locs=[self.loc1.id])
        org_admin = entities.Role(id=org_admin.id).read()
        self.assertIn(self.org1.id, [org.id for org in org_admin.organization])
        self.assertIn(self.loc1.id, [loc.id for loc in org_admin.location])

    @stubbed()
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

    @stubbed()
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
        role1_name = gen_string('alpha')
        role1 = entities.Role(name=role1_name).create()
        dom_perm = entities.Permission(resource_type='Domain').search()
        entities.Filter(permission=dom_perm, role=role1.id).create()
        cloned_role1_name = gen_string('alpha')
        cloned_role1 = entities.Role(id=role1.id).clone(
            data={'name': cloned_role1_name})
        self.assertEqual(cloned_role1_name, cloned_role1['name'])
        filter1_cloned_id = entities.Role(
            id=cloned_role1['id']).read().filters[0].id
        filter1_cloned = entities.Filter(id=filter1_cloned_id).read()
        filter1_cloned.override = True
        filter1_cloned.organization = [self.org1]
        filter1_cloned.location = [self.loc1]
        filter1_cloned = filter1_cloned.update(
            ['override', 'organization', 'location'])
        # Updated Filter
        filter1_cloned = entities.Filter(id=filter1_cloned_id).read()
        self.assertTrue(filter1_cloned.override)
        self.assertIn(
            self.org1.id,
            [org.id for org in filter1_cloned.organization]
        )
        self.assertIn(
            self.loc1.id,
            [loc.id for loc in filter1_cloned.location]
        )

    @stubbed()
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

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_override_empty_filter_taxonomies_in_cloned_role(self):
        """Taxonomies of filters in cloned role can be overridden for filters that
        are overridden in parent role

        :id: f393f303-e754-48e2-abce-9b1713a3c054

        :steps:

            1. Create a role with an overridden filter
            2. Overridden filter should have taxonomies assigned
            3. In cloned role, override 'parent roles overridden filter' by
                assigning some taxonomies to it

        :expectedresults: The taxonomies should be able to assign to
            'parent roles overridden filter' in cloned role

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_having_overridden_filter_with_taxonomies(self):# noqa
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

    @stubbed()
    @tier2
    def test_positive_clone_role_having_non_overridden_filter_with_taxonomies(self):# noqa
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

    @stubbed()
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

    @stubbed()
    @tier2
    def test_positive_clone_role_having_overridden_filter_without_taxonomies(self):# noqa
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

    @stubbed()
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
        """

    @stubbed()
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
        """

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
        role1_name = gen_string('alpha')
        role1 = entities.Role(
            name=role1_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(role1_name, role1.name)
        dom_perm = entities.Permission(resource_type='Domain').search()
        filter1 = entities.Filter(permission=dom_perm, role=role1.id).create()
        self.assertEqual(role1.id, filter1.role.id)
        self.assertFalse(filter1.override)
        self.assertFalse(filter1.unlimited)
        role1.organization = []
        role1.location = []
        role1 = role1.update(['organization', 'location'])
        self.assertEqual(role1.organization, [])
        self.assertEqual(role1.location, [])
        # Get updated filter
        filter1 = entities.Filter(id=filter1.id).read()
        self.assertTrue(filter1.unlimited)

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
        org_admin = self.create_org_admin_role(
            orgs=[self.org1.id], locs=[self.loc1.id])
        user1_login = gen_string('alpha')
        user1_pass = gen_string('alphanumeric')
        user1 = entities.User(
            login=user1_login,
            password=user1_pass,
            organization=[self.org1.id],
            location=[self.loc1.id]
        ).create()
        self.assertEqual(user1_login, user1.login)
        user2_login = gen_string('alpha')
        user2_pass = gen_string('alphanumeric')
        user2 = entities.User(
            login=user2_login,
            password=user2_pass,
            organization=[self.org1.id],
            location=[self.loc1.id]
        ).create()
        self.assertEqual(user2_login, user2.login)
        ug_name = gen_string('alpha')
        user_group = entities.UserGroup(
            name=ug_name,
            role=[org_admin.id],
            user=[user1.id, user2.id]
        ).create()
        self.assertEqual(user_group.name, ug_name)
        # Creating Subnets and Domains to verify if user really can access them
        subnet1 = entities.Subnet(
            name=gen_string('alpha'),
            organization=[self.org1.id],
            location=[self.loc1.id],
        ).create()
        domain1 = entities.Domain(
            name=gen_string('alpha'),
            organization=[self.org1.id],
            location=[self.loc1.id]
        ).create()
        sc1 = ServerConfig(
            auth=(user1_login, user1_pass),
            url=ServerConfig.get().url,
            verify=False
        )
        # User 1 Access Tests
        with self.assertNotRaises(HTTPError):
            entities.Domain(sc1).search(
                query={
                    'organization-id': self.org1.id,
                    'location-id': self.loc1.id
                }
            )
            entities.Subnet(sc1).search(
                query={
                    'organization-id': self.org1.id,
                    'location-id': self.loc1.id
                }
            )
        self.assertIn(
            domain1.id,
            [dom.id for dom in entities.Domain(sc1).search()]
        )
        self.assertIn(
            subnet1.id,
            [sub.id for sub in entities.Subnet(sc1).search()]
        )
        # User 2 Access Tests
        sc2 = ServerConfig(
            auth=(user2_login, user2_pass),
            url=ServerConfig.get().url,
            verify=False
        )
        with self.assertNotRaises(HTTPError):
            entities.Domain(sc2).search(
                query={
                    'organization-id': self.org1.id,
                    'location-id': self.loc1.id
                }
            )
            entities.Subnet(sc2).search(
                query={
                    'organization-id': self.org1.id,
                    'location-id': self.loc1.id
                }
            )
        self.assertIn(
            domain1.id,
            [dom.id for dom in entities.Domain(sc2).search()]
        )
        self.assertIn(
            subnet1.id,
            [sub.id for sub in entities.Subnet(sc2).search()]
        )

    @stubbed()
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

    @stubbed()
    @tier3
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
        org_admin = self.create_org_admin_role(
            orgs=[self.org1.id],
            locs=[self.loc1.id]
        )
        # Creating resource
        dom1_name = gen_string('alpha')
        dom1 = entities.Domain(
            name=dom1_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(dom1_name, dom1.name)
        user1_login = gen_string('alpha')
        user1_pass = gen_string('alphanumeric')
        user1 = entities.User(
            login=user1_login,
            password=user1_pass,
            role=[org_admin.id],
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(user1_login, user1.login)
        sc = ServerConfig(
            auth=(user1_login, user1_pass),
            url=ServerConfig.get().url,
            verify=False
        )
        # Getting the domain from user1
        dom1 = entities.Domain(sc, id=dom1.id).read()
        dom1.organization = [self.org2]
        with self.assertRaises(HTTPError):
            dom1.update(['organization'])

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
        org_admin = self.create_org_admin_role(
            orgs=[self.org1.id],
            locs=[self.loc1.id]
        )
        user1_login = gen_string('alpha')
        user1_pass = gen_string('alphanumeric')
        user1 = entities.User(
            login=user1_login,
            password=user1_pass,
            role=[org_admin.id]
        ).create()
        self.assertEqual(user1_login, user1.login)
        with self.assertNotRaises(HTTPError):
            entities.Role(id=org_admin.id).delete()
        # Getting updated user
        user1 = entities.User(id=user1.id).read()
        self.assertNotIn(org_admin.id, [role.id for role in user1.role])

    @stubbed()
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

    @stubbed()
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

    @tier1
    def test_positive_create_roles_by_org_admin(self):
        """Org Admin has permission to create new roles

        :id: 6c307e3c-069e-4c59-a187-18caf6f0894c

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to create a new role

        :expectedresults: Org Admin should have permission to create
            new role
        """
        org_admin = self.create_org_admin_role(
            orgs=[self.org1.id],
            locs=[self.loc1.id]
        )
        user1_login = gen_string('alpha')
        user1_pass = gen_string('alphanumeric')
        user1 = entities.User(
            login=user1_login,
            password=user1_pass,
            role=[org_admin.id],
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(user1_login, user1.login)
        sc = ServerConfig(
            auth=(user1_login, user1_pass),
            url=ServerConfig.get().url,
            verify=False
        )
        role2_name = gen_string('alpha')
        role2 = entities.Role(
            sc,
            name=role2_name,
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(role2_name, role2.name)

    @stubbed()
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
        org_admin = self.create_org_admin_role(
            orgs=[self.org1.id], locs=[self.loc1.id])
        user1_login = gen_string('alpha')
        user1_pass = gen_string('alphanumeric')
        user1 = entities.User(
            login=user1_login,
            password=user1_pass,
            role=[org_admin.id],
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(user1_login, user1.login)
        sc = ServerConfig(
            auth=(user1_login, user1_pass),
            url=ServerConfig.get().url,
            verify=False
        )
        with self.assertRaises(HTTPError):
            entities.User(sc, id=1).read()

    @tier2
    def test_positive_create_user_by_org_admin(self):
        """Org Admin can create new users

        :id: f4edbe25-3ee6-46d6-8fca-a04f6ddc8eed

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to create new users

        :expectedresults:

            1. Org Admin should be able to create new users
            2. Only Org Admin role should be available to assign to its users
            3. Org Admin should be able to assign Org Admin role to its users

        :CaseLevel: Integration
        """
        org_admin = self.create_org_admin_role(
            orgs=[self.org1.id],
            locs=[self.loc1.id]
        )
        user1_login = gen_string('alpha')
        user1_pass = gen_string('alphanumeric')
        user1 = entities.User(
            login=user1_login,
            password=user1_pass,
            role=[org_admin.id],
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(user1_login, user1.login)
        sc_user1 = ServerConfig(
            auth=(user1_login, user1_pass),
            url=ServerConfig.get().url,
            verify=False
        )
        user2_login = gen_string('alpha')
        user2_pass = gen_string('alphanumeric')
        user2 = entities.User(
            sc_user1,
            login=user2_login,
            password=user2_pass,
            role=[org_admin.id],
            location=[self.loc1]
        ).create()
        self.assertEqual(user2_login, user2.login)
        self.assertIn(org_admin.id, [role.id for role in user2.role])

    @stubbed()
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

    @stubbed()
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
        org_admin = self.create_org_admin_role(
            orgs=[self.org1.id], locs=[self.loc1.id])
        user1_login = gen_string('alpha')
        user1_pass = gen_string('alphanumeric')
        user1 = entities.User(
            login=user1_login,
            password=user1_pass,
            role=[org_admin.id],
            organization=[self.org1],
            location=[self.loc1]
        ).create()
        self.assertEqual(user1_login, user1.login)
        sc = ServerConfig(
            auth=(user1_login, user1_pass),
            url=ServerConfig.get().url,
            verify=False
        )
        with self.assertRaises(HTTPError):
            entities.Organization(sc, name=gen_string('alpha')).create()
        with self.assertNotRaises(HTTPError):
            loc1_name = gen_string('alpha')
            loc1 = entities.Location(sc, name=loc1_name).create()
        self.assertEqual(loc1_name, loc1.name)

    @stubbed()
    @tier1
    def test_negative_access_all_global_entities_by_org_admin(self):
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

    @stubbed()
    @tier3
    def test_positive_access_entities_from_ldap_org_admin(self):
        """LDAP User can access resources within its taxonomies if assigned
        role has permission for same taxonomies

        :id: 214ee608-6f69-434a-bd6d-804129ac5574

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with same taxonomies as role above
            3. Assign Org Admin role to user above
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should be able to access all the resources
            and permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

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
        """
