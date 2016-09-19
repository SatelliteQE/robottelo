"""Unit tests for the ``roles`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/roles.html


@Requirement: Role

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import bz_bug_is_open, stubbed, tier1, tier2
from robottelo.test import APITestCase


class RoleTestCase(APITestCase):
    """Tests for ``api/v2/roles``."""

    @tier1
    def test_positive_create(self):
        """Create a role with name ``name_generator()``.

        @id: 488a0970-f844-4286-b1eb-dd93005b4580

        @Assert: An entity can be created without receiving any errors, the
        entity can be fetched, and the fetched entity has the specified name.
        """
        for name in generate_strings_list(exclude_types=['html']):
            with self.subTest(name):
                if bz_bug_is_open(1112657) and name in [
                        'cjk', 'latin1', 'utf8']:
                    self.skipTest('Bugzilla bug 1112657 is open.')
                self.assertEqual(entities.Role(name=name).create().name, name)

    @tier1
    def test_positive_delete(self):
        """Delete a role with name ``name_generator()``.

        @id: 6e1d9f9c-3cbb-460b-8ef8-4a156e6552a0

        @Assert: The role cannot be fetched after it is deleted.
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

        @id: 30cb4b42-24cd-48a0-a3c5-7ca44c060e2e

        @Assert: The role is updated with the given name.
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
    """Implements Canned Roles tests from UI"""

    @stubbed
    @tier1
    def test_positive_create_role_with_taxonomies(self):
        """create role with taxonomies

        @id: fa449217-889c-429b-89b5-0b6c018ffd9e

        @steps: Create new role with taxonomies

        @assert: New role is created with taxonomies

        @caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_create_role_without_taxonomies(self):
        """Create role without taxonomies

        @id: fe65a691-1b04-4bfe-a24b-adb48feb31d1

        @steps: Create new role without any taxonomies

        @assert: New role is created without taxonomies

        @caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_create_filter_without_override(self):
        """Create filter in role w/o overriding it

        @id: 1aadb7ea-ff76-4171-850f-188ba6f87021

        @steps:

        1. Create a role with taxonomies assigned
        2. Create filter in role without overriding it

        @assert:

        1. Filter w/o override is created in role
        2. The taxonomies of role are inherited to filter
        3. Override check is not marked by default in filters table

        @caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_create_non_overridable_filter(self):
        """Create non overridable filter in role

        @id: f891e2e1-76f8-4edf-8c96-b41d05483298

        @steps:

        1. Create a filter to which taxonomies cannot be associated.
        e.g Architecture filter

        @assert:

        1. Filter is created without taxonomies.
        2. Override check is set to false
        3. Filter doesnt inherit taxonomies from role

        @caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_negative_override_non_overridable_filter(self):
        """Override non overridable filter

        @id: 7793be96-e8eb-451b-a986-51a46a1ab4f9

        @steps:

        1. Attempt to override a filter to which taxonomies cannot be
        associated.
        e.g Architecture filter

        @assert: Filter is not overrided as taxonomies cannot be applied to
        that filter

        @caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_create_overridable_filter(self):
        """Create overridable filter in role

        @id: c7ea9377-9b9e-495e-accd-3576166d504e

        @steps:

        1. Create a filter to which taxonomies can be associated.
        e.g Domain filter
        2. Override a filter with some taxonomies

        @assert:

        1. Filter is created with taxonomies
        2. Override check is set to true
        3. Filter doesnt inherits taxonomies from role

        @caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_role_taxonomies(self):
        """Update role taxonomies which applies to its non-overrided filters

        @id: 902dcb32-2126-4ff4-b733-3e86749ccd1e

        @steps:

        1. Update existing role with different taxonomies

        @assert: The taxonomies are applied only to non-overrided role filters

        @caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_negative_update_role_taxonomies(self):
        """Update role taxonomies which doesnt applies to its overrided filters

        @id: 9f3bf95a-f71a-4063-b51c-12610bc655f2

        @steps:

        1. Update existing role with different taxonomies

        @assert: The overridden role filters are not updated

        @caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_disable_filter_override(self):
        """Unset override resets filter taxonomies

        @id: eaa7b921-7c12-45c5-989b-d82aa2b6e3a6

        @steps:

        1. Create role with overridden filter having different taxonomies than
        its role.
        2. Unset the override flag in above role filter

        @assert: The taxonomies of filters resets/synced to role taxonomies

        @caseautomation: notautomated
        """

    @stubbed
    @tier2
    def test_positive_access_resources_from_role_taxonomies(self):
        """Test user access resources from taxonomies of assigned role

        @id: 706a8cea-5f65-4736-81ae-eb6fa4ea8c7a

        @steps:

        1. Create role with taxonomies
        2. Create resource(s) filter(s) without overriding them
        3. Create user with taxonomies same as role taxonomies
        4. Assign step 1 role to user

        @assert: User should be able to access the resource(s) of the assigned
        role

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed
    @tier2
    def test_negative_access_resources_outside_role_taxonomies(self):
        """Test user cannot access resources from non associated taxonomies to
        role

        @id: 87317ca9-b47b-4a6f-a80f-e2bbd1d9cf4e

        @steps:

        1. Create role with taxonomies
        2. Create resource(s) filter(s) without overriding them
        3. Create user with taxonomies not matching role taxonomies
        4. Assign step 1 role to user

        @assert: User should not be able to access the resource(s) that are not
        associated to assigned role

        @caseautomation: notautomated

        @CaseLevel: Integration
        """
