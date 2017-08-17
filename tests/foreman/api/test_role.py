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
from robottelo.decorators import bz_bug_is_open, tier1, upgrade
from robottelo.test import APITestCase


class RoleTestCase(APITestCase):
    """Tests for ``api/v2/roles``."""

    @tier1
    def test_positive_create(self):
        """Create a role with name ``name_generator()``.

        @id: 488a0970-f844-4286-b1eb-dd93005b4580

        @expectedresults: An entity can be created without receiving any
        errors, the entity can be fetched, and the fetched entity has the
        specified name.
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

        @id: 6e1d9f9c-3cbb-460b-8ef8-4a156e6552a0

        @expectedresults: The role cannot be fetched after it is deleted.
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

        @expectedresults: The role is updated with the given name.
        """
        for name in generate_strings_list(exclude_types=['html']):
            with self.subTest(name):
                if bz_bug_is_open(1112657) and name in [
                        'cjk', 'latin1', 'utf8']:
                    self.skipTest('Bugzilla bug 1112657 is open.')
                role = entities.Role().create()
                role.name = name
                self.assertEqual(role.update(['name']).name, name)
