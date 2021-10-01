"""Test classes for Bookmark tests

:Requirement: Bookmark

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Search

:Assignee: jhenner

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from airgun.exceptions import DisabledWidgetError
from airgun.session import Session
from fauxfactory import gen_string
from nailgun import entities
from widgetastic.exceptions import NoSuchElementException

from robottelo.constants import BOOKMARK_ENTITIES
from robottelo.helpers import get_nailgun_config
from robottelo.utils.issue_handlers import is_open


@pytest.fixture(scope='module')
def ui_entities(module_org, module_location):
    """Collects the list of all applicable UI entities for testing and does all
    required preconditions.
    """
    ui_entities = []
    for entity in BOOKMARK_ENTITIES:
        # Skip the entities, which can't be tested ATM (not implemented in
        # airgun or have open BZs)
        skip = entity.get('skip_for_ui')
        if isinstance(skip, (tuple, list)):
            skip = any([is_open(issue) for issue in skip])
        if skip is True:
            continue
        ui_entities.append(entity)
        # Some pages require at least 1 existing entity for search bar to
        # appear. Creating 1 entity for such pages
        entity_name, entity_setup = entity['name'], entity.get('setup')
        if entity_setup:
            # entities with 1 organization and location
            if entity_name in ('Host',):
                entity_setup(organization=module_org, location=module_location).create()
            # entities with no organizations and locations
            elif entity_name in (
                'ComputeProfile',
                'ConfigGroup',
                'GlobalParameter',
                'HardwareModel',
                'PuppetClass',
                'UserGroup',
            ):
                entity_setup().create()
            # entities with multiple organizations and locations
            else:
                entity_setup(organization=[module_org], location=[module_location]).create()
    return ui_entities


@pytest.fixture()
def random_entity(ui_entities):
    """Returns one random entity from list of available UI entities"""
    return ui_entities[random.randint(0, len(ui_entities) - 1)]


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, random_entity):
    """Perform end to end testing for bookmark component

    :id: 13e89c36-6332-451e-a4b5-2ab46346211f

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    query = gen_string('alphanumeric')
    with session:
        # Create new bookmark
        ui_lib = getattr(session, random_entity['name'].lower())
        ui_lib.create_bookmark({'name': name, 'query': query, 'public': True})
        assert session.bookmark.search(name)[0]['Name'] == name
        bookmark_values = session.bookmark.read(name)
        assert bookmark_values['name'] == name
        assert bookmark_values['query'] == query
        assert bookmark_values['public'] is True
        # Update bookmark with new name
        session.bookmark.update(name, {'name': new_name})
        assert session.bookmark.search(new_name)[0]['Name'] == new_name
        assert not session.bookmark.search(name)
        # Delete bookmark
        session.bookmark.delete(new_name)
        assert not session.bookmark.search(new_name)


@pytest.mark.tier2
def test_positive_create_bookmark_public(session, random_entity, default_viewer_role, test_name):
    """Create and check visibility of the (non)public bookmarks

    :id: 93139529-7690-429b-83fe-3dcbac4f91dc

    :Setup: Create a non-admin user with 'viewer' role

    :Steps:

        1. Navigate to the entity page
        2. Choose "bookmark this search" from the search drop-down menu
        3. Input a random name and query for a bookmark
        4. Uncheck 'Public' checkbox for the bookmark
        5. Click the create button
        6. Repeat steps 2-5 with 'Public' checked off
        7. Verify the bookmarks are listed at Administer -> Bookmarks
        8. Login as the pre-created user
        9. Verify that the non-public bookmark is not listed at Administer ->
            Bookmarks

    :expectedresults: No errors, public bookmarks is displayed for all users,
        non-public bookmark is displayed for creator but not for different user

    :CaseLevel: Integration
    """
    public_name = gen_string('alphanumeric')
    nonpublic_name = gen_string('alphanumeric')
    with session:
        ui_lib = getattr(session, random_entity['name'].lower())
        for name in (public_name, nonpublic_name):
            ui_lib.create_bookmark(
                {'name': name, 'query': gen_string('alphanumeric'), 'public': name == public_name}
            )
            assert session.bookmark.search(name)[0]['Name'] == name
    with Session(test_name, default_viewer_role.login, default_viewer_role.password) as session:
        assert session.bookmark.search(public_name)[0]['Name'] == public_name
        assert not session.bookmark.search(nonpublic_name)


@pytest.mark.tier2
def test_positive_update_bookmark_public(
    session, random_entity, default_viewer_role, module_user, test_name
):
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
    public_name = gen_string('alphanumeric')
    nonpublic_name = gen_string('alphanumeric')
    cfg = get_nailgun_config()
    cfg.auth = (module_user.login, module_user.password)
    for name in (public_name, nonpublic_name):
        entities.Bookmark(
            cfg, name=name, controller=random_entity['controller'], public=name == public_name
        ).create()
    with Session(
        test_name, default_viewer_role.login, default_viewer_role.password
    ) as non_admin_session:
        assert non_admin_session.bookmark.search(public_name)[0]['Name'] == public_name
        assert not non_admin_session.bookmark.search(nonpublic_name)
    with session:
        session.bookmark.update(public_name, {'public': False})
        session.bookmark.update(nonpublic_name, {'public': True})
    with Session(
        test_name, default_viewer_role.login, default_viewer_role.password
    ) as non_admin_session:
        assert non_admin_session.bookmark.search(nonpublic_name)[0]['Name'] == nonpublic_name
        assert not non_admin_session.bookmark.search(public_name)


@pytest.mark.tier2
def test_negative_delete_bookmark(random_entity, default_viewer_role, test_name):
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
    bookmark = entities.Bookmark(controller=random_entity['controller'], public=True).create()
    with Session(
        test_name, default_viewer_role.login, default_viewer_role.password
    ) as non_admin_session:
        assert non_admin_session.bookmark.search(bookmark.name)[0]['Name'] == bookmark.name
        with pytest.raises(NoSuchElementException):
            non_admin_session.bookmark.delete(bookmark.name)
        assert non_admin_session.bookmark.search(bookmark.name)[0]['Name'] == bookmark.name


@pytest.mark.tier2
def test_negative_create_with_duplicate_name(session, random_entity):
    """Create bookmark with duplicate name

    :id: 18168c9c-bdd1-4839-a506-cf9b06c4ab44

    :Setup:

        1. Create a bookmark of a random name with random query.

    :Steps:

        1. Create new bookmark with duplicate name.

    :expectedresults: Bookmark can't be created, submit button is disabled

    :BZ: 1920566, 1992652

    :CaseLevel: Integration
    """
    query = gen_string('alphanumeric')
    bookmark = entities.Bookmark(controller=random_entity['controller'], public=True).create()
    with session:
        assert session.bookmark.search(bookmark.name)[0]['Name'] == bookmark.name
        ui_lib = getattr(session, random_entity['name'].lower())
        with pytest.raises(DisabledWidgetError) as error:
            ui_lib.create_bookmark({'name': bookmark.name, 'query': query, 'public': True})
            assert error == 'name already exists'
        assert len(session.bookmark.search(bookmark.name)) == 1
