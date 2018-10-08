"""Test classes for Bookmark tests

:Requirement: Bookmark

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
# -*- encoding: utf-8 -*-
import random

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import BOOKMARK_ENTITIES, STRING_TYPES
from robottelo.decorators import (
    bz_bug_is_open,
    rm_bug_is_open,
    tier1,
    tier2,
)
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
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
        cls.entities = []

        # Custom user for bookmark visibility testing
        role = entities.Role().search(query={'search': 'name="Viewer"'})[0]
        cls.custom_password = gen_string('alphanumeric')
        cls.custom_user = entities.User(
            role=[role],
            password=cls.custom_password,
        ).create()

        for entity in BOOKMARK_ENTITIES:
            # Skip the entities, which can't be tested ATM (require framework
            # update)
            skip = entity.get('skip_for_ui')
            if isinstance(skip, tuple):
                if (skip[0] == 'bugzilla' and bz_bug_is_open(skip[1])
                        or skip[0] == 'redmine' and rm_bug_is_open(skip[1])):
                    skip = True
            if skip is True:
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
                        'GlobalParameters',
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
    def getOneEntity(cls):
        """Return 1 entity to test"""
        return [cls.entities[random.randint(0, len(cls.entities)-1)]]

    # CREATE TESTS
    @tier1
    def test_positive_create_bookmark_populate_auto(self):
        """Create a bookmark with auto-populating of the query

        :id: 6a51a8d4-b641-4148-9ee8-a62f09aaa4af

        :Steps:

            1. Navigate to the entity page
            2. Input a random text into the search field
            3. Choose "bookmark this search" from the search drop-down menu
            4. Input a random name for a bookmark name
            5. Verify the query field is automatically populated and the public
                option is checked
            6. Click the create button
            7. Verify that bookmark's name appears in the search dropdown
            8. List the bookmarks (Navigate to Administer -> Bookmarks)

        :expectedresults: No errors, Bookmark is displayed, controller matches
            the entity the bookmark was created for

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        searchbox_query=gen_string(
                            random.choice(STRING_TYPES)
                        ),
                    )
                    self.assertIsNotNone(self.bookmark.search(name))

    @tier1
    def test_positive_create_bookmark_populate_manual(self):
        """Create a bookmark with manually populating the name and query

        :id: 6ab2221d-8fd5-484f-ac99-b856db9fa70a

        :Steps:

            1. Navigate to the entity page
            2. Choose "bookmark this search" from the search drop-down menu
            3. Input a random name for a bookmark name
            4. Enter random text into Query field
            5. Click the create button
            6. Verify that bookmark's name appears in the search dropdown
            7. List the bookmarks (Navigate to Administer -> Bookmarks)

        :expectedresults: No errors, Bookmark is displayed, controller matches
            the entity the bookmark was created for

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=gen_string(random.choice(STRING_TYPES)),
                    )
                    self.assertIsNotNone(self.bookmark.search(name))

    @tier1
    def test_negative_create_bookmark_no_name(self):
        """Create a bookmark with empty name

        :id: ebb64459-a865-4029-bc7e-93e8d13dd877

        :Steps:

            1. Navigate to the entity page
            2. Choose "bookmark this search" from the search drop-down menu
            3. Input empty string for name
            4. Enter random text into Query field
            5. Click the create button
            6. List the bookmarks (Navigate to Administer -> Bookmarks)

        :expectedresults: Error notification - name cannot be empty, Bookmark
            is not created (not listed)

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self) as session:
                    name = ''
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=gen_string(random.choice(STRING_TYPES)),
                    )
                    # Foreman and Katello entities return different kinds of
                    # errors, try to catch both.
                    self.assertTrue(
                        session.nav.wait_until_element(
                            common_locators['alert.error'], timeout=1)
                        or
                        session.nav.wait_until_element(
                            common_locators['haserror'], timeout=1)
                    )

    @tier1
    def test_negative_create_bookmark_no_query(self):
        """Create a bookmark with empty query

        :id: 2c22ba18-a465-4977-8013-9336d1f648e8

        :Steps:

            1. Navigate to the entity page
            2. Choose "bookmark this search" from the search drop-down menu
            3. Enter random text into name field
            4. Input empty string for search query
            5. Click the create button
            6. List the bookmarks (Navigate to Administer -> Bookmarks)

        :expectedresults: Error notification - search query cannot be empty,
            Bookmark is not created (not listed)

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query='',
                    )
                    self.assertIsNone(self.bookmark.search(name))

    @tier1
    def test_negative_create_bookmark_same_name(self):
        """Create bookmarks with the same names

        :id: 210c36b2-29bd-40d9-b120-16a1a031b20c

        :Setup: Create a bookmark of a random name

        :Steps:

            1. Navigate to the entity page
            2. Choose "bookmark this search" from the search drop-down menu
            3. Input the same name as the pre-created bm
            4. Enter random text into Query field
            5. Click the create button
            6. List the bookmarks (Navigate to Administer -> Bookmarks)

        :expectedresults: Error notification - name already taken, Bookmark is
            not created (not listed)

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    for _ in range(2):
                        ui_lib.create_a_bookmark(
                            name=name,
                            public=True,
                            query=gen_string(random.choice(STRING_TYPES)),
                        )
                    self.bookmark.search(
                        name,
                        _raw_query='controller={}'.format(entity['controller'])
                    )
                    bms = self.bookmark.find_elements(
                        locators['bookmark.select_name'] % name)
                    self.assertEqual(len(bms), 1)

    # UPDATE TESTS
    @tier1
    def test_positive_update_bookmark_name(self):
        """Update and save a bookmark

        :id: 095ba7c5-82bd-4ed3-ae6d-f6ba0ad7480c

        :Setup: Create a bookmark of a random name with random query

        :Steps:

            1. List the bookmarks (Navigate to Administer -> Bookmarks)
            2. Click the pre-created bookmark
            3. Edit the name
            4. Submit
            5. Navigate to the entity page
            6. Click the search dropdown

        :expectedresults: The new bookmark name is listed

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    query = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=query,
                    )
                    new_name = gen_string(random.choice(STRING_TYPES))
                    self.bookmark.update(name, new_name, query)
                    self.assertIsNotNone(self.bookmark.search(new_name))

    @tier1
    def test_negative_update_bookmark_name(self):
        """Update and save a bookmark with name already taken

        :id: 3e74cf60-2863-4ca3-9440-7081547f3c4f

        :Setup: Create 2 bookmarks of random names with random query

        :Steps:

            1. List the bookmarks (Navigate to Administer -> Bookmarks)
            2. Select the first pre-created bookmark
            3. Edit the name to one of the other pre-created bookmarks
            4. Submit

        :expectedresults: Error - name already taken, bookmark not updated

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
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
                        bm2_name,
                        bm1_name,
                        gen_string(random.choice(STRING_TYPES)),
                    )
                    self.assertTrue(self.bookmark.wait_until_element(
                        common_locators['name_haserror']))
                    self.assertIsNotNone(self.bookmark.search(bm2_name))

    @tier1
    def test_negative_update_bookmark_name_empty(self):
        """Update and save a bookmark with an empty name

        :id: 7d7f713d-e377-446e-a9e9-06364bcc25c0

        :Setup: Create a bookmark of a random name with random query

        :Steps:

            1. List the bookmarks (Navigate to Administer -> Bookmarks)
            2. Click the pre-created bookmark
            3. Delete the name
            4. Submit
            5. Navigate to the entity page
            6. Click the search dropdown

        :expectedresults: Error - name cannot be empty, bookmark not updated

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    query = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=query,
                    )
                    self.bookmark.update(name, '', query)
                    self.assertTrue(self.bookmark.wait_until_element(
                        common_locators['name_haserror']))
                    self.assertIsNotNone(self.bookmark.search(name))

    @tier1
    def test_positive_update_bookmark_query(self):
        """Update and save a bookmark query

        :id: 19c994f0-2567-47bb-8486-bc441602bc7a

        :Setup: Create a bookmark of a random name with random query

        :Steps:

            1. List the bookmarks (Navigate to Administer -> Bookmarks)
            2. Click the pre-created bookmark
            3. Edit the Search query field
            4. Submit
            5. Navigate to the entity page
            6. Select the updated bookmark from the query

        :expectedresults: The updated query is populated and submitted

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=gen_string(random.choice(STRING_TYPES)),
                    )
                    new_query = gen_string(random.choice(STRING_TYPES))
                    self.bookmark.update(name, new_query=new_query)
                    self.assertTrue(
                        self.bookmark.validate_field(name, 'query', new_query))

    @tier1
    def test_negative_update_bookmark_query_empty(self):
        """Update and save a bookmark with an empty query

        :id: 516b314b-7712-455a-b1d4-d09730acbec9

        :Setup: Create a bookmark of a random name with random query

        :Steps:

            1. List the bookmarks (Navigate to Administer -> Bookmarks)
            2. Click the pre-created bookmark
            3. Delete the search query
            4. Submit
            5. Navigate to the entity page
            6. Click the search dropdown

        :expectedresults: Error - search query cannot be empty, bookmark not
            updated

        :CaseImportance: Critical
        """
        for entity in self.getOneEntity():
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    query = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=query,
                    )
                    self.bookmark.update(name, new_query='')
                    self.assertTrue(self.bookmark.wait_until_element(
                        common_locators['haserror']))
                    self.assertTrue(
                        self.bookmark.validate_field(name, 'query', query))

    @tier2
    def test_positive_update_bookmark_public(self):
        """Update and save a bookmark public state

        :id: 63646c41-5441-4547-a4d0-744286122405

        :Setup:

            1. Create 2 bookmarks of a random name with random query, one
               public and one private
            2. Create a non-admin user with 'viewer' role

        :Steps:

            1. Login to Satellite server (establish a UI session) as the
               pre-created user
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

        :expectedresults: New public bookmark is listed, and the private one is
            hidden

        :CaseLevel: Integration
        """
        with Session(self):
            bm1_name = gen_string(random.choice(STRING_TYPES))
            bm1_entity = self.getOneEntity()[0]
            bm2_name = gen_string(random.choice(STRING_TYPES))
            bm2_entity = self.getOneEntity()[0]
            bm1_page = getattr(self, bm1_entity['name'].lower())
            bm1_page.create_a_bookmark(
                name=bm1_name,
                public=True,
                query=gen_string('alphanumeric'),
            )
            bm2_page = getattr(self, bm2_entity['name'].lower())
            bm2_page.create_a_bookmark(
                name=bm2_name,
                public=False,
                query=gen_string('alphanumeric'),
            )
        with Session(self, user=self.custom_user.login,
                     password=self.custom_password):
            self.assertIsNotNone(self.bookmark.search(bm1_name))
            self.assertIsNone(self.bookmark.search(bm2_name))
        with Session(self):
            self.bookmark.update(bm1_name, new_public=False)
            self.bookmark.update(bm2_name, new_public=True)
        with Session(self, user=self.custom_user.login,
                     password=self.custom_password):
            self.assertIsNone(self.bookmark.search(bm1_name))
            self.assertIsNotNone(self.bookmark.search(bm2_name))

    # DELETE TESTS
    @tier1
    def test_positive_delete_bookmark(self):
        """Simple removal of a bookmark query

        :id: 46c7cf47-7e86-4d81-ba07-4c2405801552

        :Setup: Create a bookmark of a random name with random query

        :Steps:

            1. List the bookmarks (Navigate to Administer -> Bookmarks)
            2. Click Delete next to a pre-created bookmark
            3. Verify the bookmark is no longer listed

        :expectedresults: The bookmark is deleted

        :CaseImportance: Critical
        """
        for entity in self.entities:
            with self.subTest(entity):
                with Session(self):
                    name = gen_string(random.choice(STRING_TYPES))
                    ui_lib = getattr(self, entity['name'].lower())
                    ui_lib.create_a_bookmark(
                        name=name,
                        public=True,
                        query=gen_string(random.choice(STRING_TYPES)),
                    )
                    self.assertIsNotNone(self.bookmark.search(name))
                    self.bookmark.delete(name)

    @tier2
    def test_negative_delete_bookmark(self):
        """Simple removal of a bookmark query without permissions

        :id: 1a94bf2b-bcc6-4663-b70d-e13244a0783b

        :Setup:

            1. Create a bookmark of a random name with random query
            2. Create a non-admin user without destroy_bookmark role (e.g.
               viewer)

        :Steps:

            1. Login to Satellite server (establish a UI session) as a
               non-admin user
            2. List the bookmarks (Navigate to Administer -> Bookmarks)

        :expectedresults: The delete buttons are not displayed

        :CaseLevel: Integration
        """
        bm = entities.Bookmark(
            controller=self.getOneEntity()[0]['controller'],
            public=True,
        ).create()
        with Session(self, user=self.custom_user.login,
                     password=self.custom_password):
            with self.assertRaises(UIError):
                self.bookmark.delete(bm.name)
