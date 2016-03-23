"""Test classes for Bookmark tests"""
# -*- encoding: utf-8 -*-
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import BOOKMARK_ENTITIES
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import skip_if_bug_open, tier1
from robottelo.test import APITestCase


class BookmarkTestCase(APITestCase):
    """Test for common Bookmark operations via API"""

    # CREATE TESTS
    @tier1
    def test_positive_create_with_name(self):
        """Create a bookmark

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Create a bookmark with a random name, query and random valid
        controller
        2. List the bookmarks

        @Assert: No errors, Bookmark is listed, controller matches the
        controller the bookmark was created for
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                for name in valid_data_list():
                    with self.subTest(name):
                        bm = entities.Bookmark(
                            controller=entity['controller'],
                            name=name,
                        ).create()
                        self.assertEqual(bm.controller, entity['controller'])
                        self.assertEqual(bm.name, name)

    @tier1
    def test_positive_create_with_query(self):
        """Create a bookmark

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Create a bookmark with a random query, name and random valid
        controller
        2. List the bookmarks

        @Assert: No errors, Bookmark is listed, controller matches the
        controller the bookmark was created for
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

        @Feature: Scoped Search Bookmark Visibility

        @Steps:

        1. Create a bookmark with a random name and public = true
        2. List the bookmarks

        @Assert: No errors, Bookmark is listed, controller matches the entity
        the bookmark was created for and is displayed as public
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

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Attempt to create a bookmark with providing an invalid name
        2. List the bookmarks

        @Assert: Error returned, Bookmark is not created (not listed)
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                for name in invalid_values_list():
                    with self.subTest(name):
                        with self.assertRaises(HTTPError):
                            entities.Bookmark(
                                controller=entity['controller'],
                                name=name,
                            ).create()
                        result = entities.Bookmark().search(
                            query={'search': u'name="{0}"'.format(name)})
                        self.assertEqual(len(result), 0)

    @tier1
    def test_negative_create_empty_query(self):
        """Create a bookmark with empty query

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Create a bookmark with providing an empty query
        2. List the bookmarks

        @Assert: Error notification - search query cannot be empty, Bookmark is
        not created (not listed)
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

        @Feature: Scoped Search Bookmark Create

        @Setup:

        1. Create a bookmark with a random name

        @Steps:

        1. Create a new bookmark using a random name
        2. Create a second bookmark, using the same name as
        the previous Bookmark. Assert that an error is raised.
        3. List the bookmarks. Assert that the Bookmark created is present and
        there's only one listed

        @Assert: Error notification - name already taken, Bookmark is not
        created (not listed)
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

    @skip_if_bug_open('bugzilla', 1302725)
    @tier1
    def test_negative_create_null_public(self):
        """Create a bookmark omitting the public parameter

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Create a new bookmark using a random name, random query and omit the
        'public' parameter
        2. List the bookmarks

        @Assert: Error notification – public is required, Bookmark is not
        created (not listed)

        @BZ: 1302725
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

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a new bookmark with a random name and random query

        @Steps:

        1. Update the previously created bookmark with another random name

        @Assert: The new bookmark name is listed
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                bm = entities.Bookmark(
                    controller=entity['controller']).create()
                for new_name in valid_data_list():
                    with self.subTest(new_name):
                        bm.name = new_name
                        bm = bm.update(['name'])
                        self.assertEqual(bm.name, new_name)

    @tier1
    def test_negative_update_same_name(self):
        """Update a bookmark with name already taken

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create 2 bookmarks with a random names with random query

        @Steps:

        1. Try to update the name of the first (or second) Bookmark created in
        the Setup with the name of the second (or first) Bookmark

        @Assert: Error - name already taken, bookmark not updated
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

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query

        @Steps:

        1. Update the name of the previously created bookmarks to an invalid
        value

        @Assert: Error - bookmark not updated
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                bm = entities.Bookmark(
                    controller=entity['controller'],
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

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query

        @Steps:

        1. Update the query of the previously created bookmark

        @Assert: The updated query submitted
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

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query

        @Steps:

        1. Update the query of the pre-created bookmark with an empty value

        @Assert: Error - search query cannot be empty, bookmark not updated
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

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query with public
        attribute set to True/False

        @Steps:

        1. Update the bookmarks 'public' attribute
        2. List the bookmarks

        @Assert: Bookmark is updated with new public state
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
