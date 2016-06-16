"""Test classes for Bookmark tests"""
# -*- encoding: utf-8 -*-
import random

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import BOOKMARK_ENTITIES, STRING_TYPES
from robottelo.decorators import (
    bz_bug_is_open,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
)
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


class BookmarkTestCase(UITestCase):
    """Test for common Bookmark operations in UI"""

    @classmethod
    def setUpClass(cls):
        """Display all the bookmarks on the same page, create user and entities
        for testing.
        """
        super(BookmarkTestCase, cls).setUpClass()
        cls.per_page = entities.Setting().search(
            query={'search': 'name="entries_per_page"'})[0]
        cls.saved_per_page = str(cls.per_page.value)
        cls.per_page.value = '100000'
        cls.per_page.update({'value'})
        cls.entities = []

        for entity in BOOKMARK_ENTITIES:
            # Skip the entities, which can't be tested ATM (require framework
            # update)
            skip = entity.get('skip_for_ui')
            if skip and (skip is True or bz_bug_is_open(skip)):
                continue
            cls.entities.append(entity)
            # Some pages require at least 1 existing entity for search bar to
            # appear. Creating 1 entity for such pages
            if entity.get('setup'):
                # entities with 1 organization
                if entity['name'] in ('Hosts',):
                    entity['setup'](organization=cls.session_org).create()
                # entities with no organizations
                elif entity['name'] in (
                        'Compute_Profile',
                        'ConfigGroups',
                        'HardwareModel',
                        'PuppetClasses',
                        'UserGroup'):
                    entity['setup']().create()
                # entities with multiple organizations
                else:
                    entity['setup'](organization=[cls.session_org]).create()

    @classmethod
    def set_session_org(cls):
        cls.session_org = entities.Organization(
            name=gen_string('alphanumeric')).create()

    @classmethod
    def tearDownClass(cls):
        """Restore previous 'entries_per_page' value"""
        cls.per_page.value = cls.saved_per_page
        cls.per_page.update({'value'})
        super(BookmarkTestCase, cls).tearDownClass()

    @classmethod
    def getOneEntity(cls):
        """Return 1 entity to test"""
        return [cls.entities[random.randint(0, len(cls.entities)-1)]]

    # CREATE TESTS
    @tier1
    def test_positive_create_bookmark_populate_auto(self):
        """Create a bookmark with auto-populating of the query

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Navigate to the entity page
        2. Input a random text into the search field
        3. Choose "bookmark this search" from the search drop-down menu
        4. Input a random name for a bookmark name
        5. Verify the query field is automatically populated and the public
           option is checked
        6. Click the create button
        7. Verify that bookmark's name appears in the search dropdown
        8. List the bookmarks (Navigate to Administer -> Bookmarks)

        @Assert: No errors, Bookmark is displayed, controller matches the
        entity the bookmark was created for
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        searchbox_query=gen_string(
                            random.choice(STRING_TYPES)
                        ),
                    )
                    self.assertIsNotNone(
                        self.bookmark.search(entity['controller'], name))

    @tier1
    def test_positive_create_bookmark_populate_manual(self):
        """Create a bookmark with manually populating the name and query

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Navigate to the entity page
        2. Choose "bookmark this search" from the search drop-down menu
        3. Input a random name for a bookmark name
        4. Enter random text into Query field
        5. Click the create button
        6. Verify that bookmark's name appears in the search dropdown
        7. List the bookmarks (Navigate to Administer -> Bookmarks)

        @Assert: No errors, Bookmark is displayed, controller matches the
        entity the bookmark was created for
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=gen_string(random.choice(STRING_TYPES)),
                    )
                    self.assertIsNotNone(
                        self.bookmark.search(entity['controller'], name))

    @stubbed()
    @tier2
    def test_positive_create_bookmark_public(self):
        """Create and check visibility of the (non)public bookmarks

        @Feature: Scoped Search Bookmark Visibility

        @Setup:

        1. Create a non-admin user with 'viewer' role

        @Steps:

        1. Navigate to the entity page
        2. Input a random text into the search field
        3. Choose "bookmark this search" from the search drop-down menu
        4. Input a random name for a bookmark name
        5. Verify the query field is automatically populated and the public
           option is checked
        6. Click the create button
        7. Choose "bookmark this search" from the search drop-down menu
        8. Input a random name for a bookmark name
        9. Verify the query field is automatically populated and the public
           option is unchecked
        10. Click the create button
        11. Verify that bookmark's name appears in the search dropdown
        12. List the bookmarks (Navigate to Administer -> Bookmarks)
        13. Login as the pre-created user
        14. Navigate to the entity
        15. Click the dropdown
        16. Verify that the non-public bookmark is not listed

        @Assert: No errors, Bookmark is displayed, controller matches the
        entity the bookmark was created for

        @Status: Manual
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                pass

    @skip_if_bug_open('bugzilla', 1326633)
    @tier1
    def test_negative_create_bookmark_no_name(self):
        """Create a bookmark with empty name

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Navigate to the entity page
        2. Choose "bookmark this search" from the search drop-down menu
        3. Input empty string for name
        4. Enter random text into Query field
        5. Click the create button
        6. List the bookmarks (Navigate to Administer -> Bookmarks)

        @Assert: Error notification - name cannot be empty, Bookmark is not
        created (not listed)
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser) as session:
                    name = ''
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=gen_string(random.choice(STRING_TYPES)),
                    )
                    # Not sure what kind of validation will be added when
                    # BZ1326633 is fixed. Need to double check that when BZ is
                    # closed.
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )

    @tier1
    def test_negative_create_bookmark_no_query(self):
        """Create a bookmark with empty query

        @Feature: Scoped Search Bookmark Create

        @Steps:

        1. Navigate to the entity page
        2. Choose "bookmark this search" from the search drop-down menu
        3. Enter random text into name field
        4. Input empty string for search query
        5. Click the create button
        6. List the bookmarks (Navigate to Administer -> Bookmarks)

        @Assert: Error notification - search query cannot be empty, Bookmark is
        not created (not listed)
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query='',
                    )
                    self.assertIsNone(
                        self.bookmark.search(entity['controller'], name))

    @tier1
    def test_negative_create_bookmark_same_name(self):
        """Create bookmarks with the same names

        @Feature: Scoped Search Bookmark Create

        @Setup:

        1. Create a bookmark of a random name

        @Steps:

        1. Navigate to the entity page
        2. Choose "bookmark this search" from the search drop-down menu
        3. Input the same name as the pre-created bm
        4. Enter random text into Query field
        5. Click the create button
        6. List the bookmarks (Navigate to Administer -> Bookmarks)

        @Assert: Error notification - name already taken, Bookmark is not
        created (not listed)
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    for _ in range(2):
                        ui_lib.create_a_bookmark(
                            name=name,
                            public=True,
                            query=gen_string(random.choice(STRING_TYPES)),
                        )
                    self.bookmark.navigate_to_entity()
                    strategy, value = locators['bookmark.select_name']
                    bms = self.browser.find_elements(
                        strategy, value % (entity['controller'], name))
                    self.assertEqual(len(bms), 1)

    # UPDATE TESTS
    @tier1
    def test_positive_update_bookmark_name(self):
        """Update and save a bookmark

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark of a random name with random query

        @Steps:

        1. List the bookmarks (Navigate to Administer -> Bookmarks)
        2. Click the pre-created bookmark
        3. Edit the name
        4. Submit
        5. Navigate to the entity page
        6. Click the search dropdown

        @Assert: The new bookmark name is listed
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    query = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=query,
                    )
                    new_name = gen_string(random.choice(STRING_TYPES))
                    self.bookmark.update(
                        entity['controller'], name, new_name, query)
                    self.assertIsNotNone(
                        self.bookmark.search(entity['controller'], new_name))

    @tier1
    def test_negative_update_bookmark_name(self):
        """Update and save a bookmark with name already taken

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create 2 bookmarks of random names with random query

        @Steps:

        1. List the bookmarks (Navigate to Administer -> Bookmarks)
        2. Select the first pre-created bookmark
        3. Edit the name to one of the other pre-created bookmarks
        4. Submit

        @Assert: Error - name already taken, bookmark not updated
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    bm1_name = gen_string(random.choice(STRING_TYPES))
                    bm2_name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    for name in (bm1_name, bm2_name):
                        ui_lib.create_a_bookmark(
                            name=name,
                            public=True,
                            query=gen_string(random.choice(STRING_TYPES)),
                        )
                    self.bookmark.update(
                        entity['controller'],
                        bm2_name,
                        bm1_name,
                        gen_string(random.choice(STRING_TYPES)),
                    )
                    self.assertTrue(self.bookmark.wait_until_element(
                        common_locators['name_haserror']))
                    self.assertIsNotNone(
                        self.bookmark.search(entity['controller'], bm2_name))

    @tier1
    def test_negative_update_bookmark_name_empty(self):
        """Update and save a bookmark with an empty name

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark of a random name with random query

        @Steps:

        1. List the bookmarks (Navigate to Administer -> Bookmarks)
        2. Click the pre-created bookmark
        3. Delete the name
        4. Submit
        5. Navigate to the entity page
        6. Click the search dropdown

        @Assert: Error - name cannot be empty, bookmark not updated
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    query = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=query,
                    )
                    self.bookmark.update(
                        entity['controller'], name, '', query)
                    self.assertTrue(self.bookmark.wait_until_element(
                        common_locators['name_haserror']))
                    self.assertIsNotNone(
                        self.bookmark.search(entity['controller'], name))

    @skip_if_bug_open('bugzilla', 1324484)
    @tier1
    def test_positive_update_bookmark_query(self):
        """Update and save a bookmark query

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark of a random name with random query

        @Steps:

        1. List the bookmarks (Navigate to Administer -> Bookmarks)
        2. Click the pre-created bookmark
        3. Edit the Search query field
        4. Submit
        5. Navigate to the entity page
        6. Select the updated bookmark from the query

        @Assert: The updated query is populated and submitted
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=gen_string(random.choice(STRING_TYPES)),
                    )
                    new_query = gen_string(random.choice(STRING_TYPES))
                    self.bookmark.update(
                        entity['controller'], name, new_query=new_query)
                    self.assertTrue(
                        self.bookmark.validate_field(
                            entity['controller'], name, 'query', new_query)
                    )

    @skip_if_bug_open('bugzilla', 1324484)
    @tier1
    def test_negative_update_bookmark_query_empty(self):
        """Update and save a bookmark with an empty query

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create a bookmark of a random name with random query

        @Steps:

        1. List the bookmarks (Navigate to Administer -> Bookmarks)
        2. Click the pre-created bookmark
        3. Delete the search query
        4. Submit
        5. Navigate to the entity page
        6. Click the search dropdown

        @Assert: Error - search query cannot be empty, bookmark not updated
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    query = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=query,
                    )
                    self.bookmark.update(
                        entity['controller'], name, new_query='')
                    self.assertTrue(self.bookmark.wait_until_element(
                        common_locators['haserror']))
                    self.assertTrue(
                        self.bookmark.validate_field(
                            entity['controller'], name, 'query', query)
                    )

    @stubbed()
    @tier2
    def test_positive_update_bookmark_public(self):
        """Update and save a bookmark public state

        @Feature: Scoped Search Bookmark Update

        @Setup:

        1. Create 2 bookmarks of a random name with random query, one public
        and one private
        2. Create a non-admin user with 'viewer' role

        @Steps:

        1. Login to Satellite server (establish a UI session) as
        the pre-created user
        2. Navigate to the entity
        3. List the bookmarks by clicking the drop down menu
        4. Verify that only the public bookmark is listed
        5. Log out
        6. Login to Satellite server (establish a UI session) as the admin
        user
        7. List the bookmarks (Navigate to Administer -> Bookmarks)
        8. Click the public pre-created bookmark
        9. Uncheck 'public'
        10. Submit
        11. Click the private pre-created bookmark
        12. Check 'public'
        13. Submit
        14. Logout
        15. Login to Satellite server (establish a UI session) as the
        pre-created user
        16. Navigate to the entity
        17. List the bookmarks by clicking the drop down menu

        @Assert: New public bookmark is listed, and the private
        one is hidden

        @Status: Manual
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                pass

    # DELETE TESTS
    @tier1
    def test_positive_delete_bookmark(self):
        """Simple removal of a bookmark query

        @Feature: Scoped Search Bookmark Delete

        @Setup:

        1. Create a bookmark of a random name with random query

        @Steps:

        1. List the bookmarks (Navigate to Administer -> Bookmarks)
        2. Click Delete next to a pre-created bookmark
        3. Verify the bookmark is no longer listed

        @Assert: The bookmark is deleted
        """
        for entity in self.entities:
            with self.subTest(entity):
                with Session(self.browser):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=gen_string(random.choice(STRING_TYPES)),
                    )
                    self.assertIsNotNone(
                        self.bookmark.search(entity['controller'], name))
                    self.bookmark.delete(entity['controller'], name)

    @stubbed()
    @tier2
    def test_negative_delete_bookmark(self):
        """Simple removal of a bookmark query without permissions

        @Feature: Scoped Search Bookmark Delete

        @Setup:

        1. Create a bookmark of a random name with random query
        2. Create a non-admin user without destroy_bookmark role (e.g. viewer)

        @Steps:

        1. Login to Satellite server (establish a UI session) as a non-admin
        user
        2. List the bookmarks (Navigate to Administer -> Bookmarks)

        @Assert: The delete buttons are not displayed

        @Status: Manual
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                pass
