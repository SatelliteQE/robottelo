# -*- encoding: utf-8 -*-
"""Test classes for Bookmark tests

:Requirement: Bookmarks

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Usability

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import BOOKMARK_ENTITIES
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import tier1
from robottelo.test import APITestCase

# Create a new list reference to prevent constant modification
BOOKMARK_ENTITIES = list(BOOKMARK_ENTITIES)


class BookmarkTestCase(APITestCase):
    """Test for common Bookmark operations via API"""

    @classmethod
    def setUpClass(cls):
        """Filter entities list if affected by BZ"""
        super(BookmarkTestCase, cls).setUpClass()

    # CREATE TESTS
    @tier1
    def test_positive_create_with_name(self):
        """Create a bookmark

        :id: aeef0944-379a-4a27-902d-aa5969dbd441

        :Steps:

            1. Create a bookmark with a random name, query and random valid
               controller
            2. List the bookmarks

        :expectedresults: No errors, Bookmark is listed, controller matches the
            controller the bookmark was created for

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                for name in valid_data_list():
                    with self.subTest(name):
                        bm = entities.Bookmark(
                            controller=entity['controller'],
                            name=name,
                            public=False,
                        ).create()
                        self.assertEqual(bm.controller, entity['controller'])
                        self.assertEqual(bm.name, name)

    @tier1
    def test_positive_create_with_query(self):
        """Create a bookmark

        :id: 9fb6d485-92b5-43ea-b776-012c13734100

        :Steps:

            1. Create a bookmark with a random query, name and random valid
               controller
            2. List the bookmarks

        :expectedresults: No errors, Bookmark is listed, controller matches the
            controller the bookmark was created for

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                for query in valid_data_list():
                    with self.subTest(query):
                        bm = entities.Bookmark(
                            controller=entity['controller'],
                            query=query,
                        ).create()
                        self.assertEqual(bm.controller, entity['controller'])
                        self.assertEqual(bm.query, query)

    @tier1
    def test_positive_create_public(self):
        """Create a public bookmark

        :id: 511b9bcf-0661-4e44-b1bc-475a1c207aa9

        :Steps:

            1. Create a bookmark with a random name and public = true
            2. List the bookmarks

        :expectedresults: No errors, Bookmark is listed, controller matches the
            entity the bookmark was created for and is displayed as public

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                for public in (True, False):
                    with self.subTest(public):
                        bm = entities.Bookmark(
                            controller=entity['controller'],
                            public=public,
                        ).create()
                        self.assertEqual(bm.controller, entity['controller'])
                        self.assertEqual(bm.public, public)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create a bookmark with invalid name

        :id: 9a79c561-8225-43fc-8ec7-b6858e9665e2

        :Steps:

            1. Attempt to create a bookmark with providing an invalid name
            2. List the bookmarks

        :expectedresults: Error returned, Bookmark is not created (not listed)

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                for name in invalid_values_list():
                    with self.subTest(name):
                        with self.assertRaises(HTTPError):
                            entities.Bookmark(
                                controller=entity['controller'],
                                name=name,
                                public=False,
                            ).create()
                        result = entities.Bookmark().search(
                            query={'search': u'name="{0}"'.format(name)})
                        self.assertEqual(len(result), 0)

    @tier1
    def test_negative_create_empty_query(self):
        """Create a bookmark with empty query

        :id: 674d569f-6f86-43ba-b9cc-f43e05e8ab1c

        :Steps:

            1. Create a bookmark with providing an empty query
            2. List the bookmarks

        :expectedresults: Error notification - search query cannot be empty,
            Bookmark is not created (not listed)

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                name = gen_string('alpha')
                with self.assertRaises(HTTPError):
                    entities.Bookmark(
                        controller=entity['controller'],
                        name=name,
                        query='',
                    ).create()
                result = entities.Bookmark().search(
                    query={'search': u'name="{0}"'.format(name)})
                self.assertEqual(len(result), 0)

    @tier1
    def test_negative_create_same_name(self):
        """Create bookmarks with the same names

        :id: f78f6e97-da77-4a61-95c2-622c439d325d

        :Setup: Create a bookmark with a random name

        :Steps:

            1. Create a new bookmark using a random name
            2. Create a second bookmark, using the same name as the previous
               Bookmark. Assert that an error is raised.
            3. List the bookmarks. Assert that the Bookmark created is present
               and there's only one listed

        :expectedresults: Error notification - name already taken, Bookmark is
            not created (not listed)

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                name = gen_string('alphanumeric')
                entities.Bookmark(
                    controller=entity['controller'],
                    name=name,
                ).create()
                with self.assertRaises(HTTPError):
                    entities.Bookmark(
                        controller=entity['controller'],
                        name=name,
                    ).create()
                result = entities.Bookmark().search(
                    query={'search': u'name="{0}"'.format(name)})
                self.assertEqual(len(result), 1)

    @tier1
    def test_negative_create_null_public(self):
        """Create a bookmark omitting the public parameter

        :id: 0a4cb5ea-912b-445e-a874-b345e43d3eac

        :Steps:

            1. Create a new bookmark using a random name, random query and omit
               the 'public' parameter
            2. List the bookmarks

        :expectedresults: Error notification - public is required, Bookmark is
            not created (not listed)

        :BZ: 1302725

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                name = gen_string('alphanumeric')
                with self.assertRaises(HTTPError):
                    entities.Bookmark(
                        controller=entity['controller'],
                        name=name,
                        public=None,
                    ).create()
                result = entities.Bookmark().search(
                    query={'search': u'name="{0}"'.format(name)})
                self.assertEqual(len(result), 0)

    # UPDATE TESTS
    @tier1
    def test_positive_update_name(self):
        """Update a bookmark

        :id: 1cde270a-26fb-4cff-bdff-89fef17a7624

        :Setup: Create a new bookmark with a random name and random query

        :Steps: Update the previously created bookmark with another random name

        :expectedresults: The new bookmark name is listed

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                bm = entities.Bookmark(
                    controller=entity['controller'],
                    public=False,
                ).create()
                for new_name in valid_data_list():
                    with self.subTest(new_name):
                        bm.name = new_name
                        bm = bm.update(['name'])
                        self.assertEqual(bm.name, new_name)

    @tier1
    def test_negative_update_same_name(self):
        """Update a bookmark with name already taken

        :id: 6becf121-2bea-4f7e-98f4-338bd88b8f4b

        :Setup: Create 2 bookmarks with a random names with random query

        :Steps: Try to update the name of the first (or second) Bookmark
            created in the Setup with the name of the second (or first)
            Bookmark

        :expectedresults: Error - name already taken, bookmark not updated

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                name = gen_string('alphanumeric')
                entities.Bookmark(
                    controller=entity['controller'],
                    name=name,
                ).create()
                bm = entities.Bookmark(
                    controller=entity['controller'],
                ).create()
                bm.name = name
                with self.assertRaises(HTTPError):
                    bm.update(['name'])
                bm = bm.read()
                self.assertNotEqual(bm.name, name)

    @tier1
    def test_negative_update_invalid_name(self):
        """Update a bookmark with an invalid name

        :id: 479795bb-aeed-45b3-a7e3-d3449c808087

        :Setup: Create a bookmark with a random name and random query

        :Steps: Update the name of the previously created bookmarks to an
            invalid value

        :expectedresults: Error - bookmark not updated

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                bm = entities.Bookmark(
                    controller=entity['controller'],
                    public=False,
                ).create()
                for new_name in invalid_values_list():
                    with self.subTest(new_name):
                        bm.name = new_name
                        with self.assertRaises(HTTPError):
                            bm.update(['name'])
                        bm = bm.read()
                        self.assertNotEqual(bm.name, new_name)

    @tier1
    def test_positive_update_query(self):
        """Update a bookmark query

        :id: 92a31de2-bebf-4396-94f5-adf59f8d66a5

        :Setup: Create a bookmark with a random name and random query

        :Steps: Update the query of the previously created bookmark

        :expectedresults: The updated query submitted

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                bm = entities.Bookmark(
                    controller=entity['controller'],
                ).create()
                for new_query in valid_data_list():
                    with self.subTest(new_query):
                        bm.query = new_query
                        bm = bm.update(['query'])
                        self.assertEqual(bm.query, new_query)

    @tier1
    def test_negative_update_empty_query(self):
        """Update a bookmark with an empty query

        :id: 948602d3-532a-47fe-b313-91e3fab809bf

        :Setup: Create a bookmark with a random name and random query

        :Steps: Update the query of the pre-created bookmark with an empty
            value

        :expectedresults: Error - search query cannot be empty, bookmark not
            updated

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                bm = entities.Bookmark(
                    controller=entity['controller'],
                ).create()
                bm.query = ''
                with self.assertRaises(HTTPError):
                    bm.update(['query'])
                bm = bm.read()
                self.assertNotEqual(bm.query, '')

    @tier1
    def test_positive_update_public(self):
        """Update a bookmark public state to private and vice versa

        :id: 2717360d-37c4-4bb9-bce1-b1edabdf11b3

        :Setup: Create a bookmark with a random name and random query with
            public attribute set to True/False

        :Steps:

            1. Update the bookmarks 'public' attribute
            2. List the bookmarks

        :expectedresults: Bookmark is updated with new public state

        :CaseImportance: Critical
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                for public in (True, False):
                    with self.subTest(public):
                        bm = entities.Bookmark(
                            controller=entity['controller'],
                            public=not public,
                        ).create()
                        self.assertNotEqual(bm.public, public)
                        bm.public = public
                        bm = bm.update(['public'])
                        self.assertEqual(bm.public, public)
