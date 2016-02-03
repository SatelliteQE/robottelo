"""Test classes for Bookmark tests"""
# -*- encoding: utf-8 -*-
from robottelo.constants import BOOKMARK_ENTITIES
from robottelo.decorators import stubbed, tier1
from robottelo.test import APITestCase


class BookmarkTestCase(APITestCase):
    """Test for common Bookmark operations via API"""

    # CREATE TESTS
    @stubbed()
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

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
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

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_positive_create_public(self):
        """Create a public bookmark

        @Feature: Scoped Search Bookmark Visibility

        @Steps:

        1. Create a bookmark with a random name and public = true
        2. List the bookmarks

        @Assert: No errors, Bookmark is listed, controller matches the entity
        the bookmark was created for and is displayed as public

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_negative_create_empty_name(self):
        """Create a bookmark with empty name

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Create a bookmark with providing an empty name
        2. List the bookmarks

        @Assert: Error returned - name cannot be empty, Bookmark is not created
        (not listed)

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_negative_create_empty_query(self):
        """Create a bookmark with empty query

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Create a bookmark with providing an empty query
        2. List the bookmarks

        @Assert: Error notification - search query cannot be empty, Bookmark is
        not created (not listed)

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
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

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
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

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    # UPDATE TESTS
    @stubbed()
    @tier1
    def test_positive_update_name(self):
        """Update a bookmark

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a new bookmark with a random name and random query

        @Steps:

        1. Update the previously created bookmark with another random name

        @Assert: The new bookmark name is listed

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_negative_update_name(self):
        """Update a bookmark with name already taken

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create 2 bookmarks with a random names with random query

        @Steps:

        1. Try to update the name of the first (or second) Bookmark created in
        the Setup with the name of the second (or first) Bookmark

        @Assert: Error - name already taken, bookmark not updated

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_negative_update_empty_name(self):
        """Update a bookmark with an empty name

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query

        @Steps:

        1. Update the name of the previously created bookmarks to an empty
        value

        @Assert: Error - name cannot be empty, bookmark not updated

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_positive_update_query(self):
        """Update a bookmark query

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query

        @Steps:

        1. Update the query of the previously created bookmark

        @Assert: The updated query submitted

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_negative_update_empty_query(self):
        """Update a bookmark with an empty query

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query

        @Steps:

        1. Update the query of the pre-created bookmark with an empty value

        @Assert: Error - search query cannot be empty, bookmark not updated

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_positive_update_public(self):
        """Update a bookmark public state to private

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query with public
        attribute set to True

        @Steps:

        1. Update the bookmarks 'public' attribute to False
        3. List the bookmarks

        @Assert: Bookmark is now listed as private

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass

    @stubbed()
    @tier1
    def test_positive_update_private(self):
        """Update a bookmark public state to public

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark with a random name and random query with public
        attribute set to False

        @Steps:

        1. Update the bookmarks 'public' attribute to True
        3. List the bookmarks

        @Assert: Bookmark is now listed as public

        @Status: Manual
        """
        for entity in BOOKMARK_ENTITIES:
            with self.subTest(entity['controller']):
                pass
