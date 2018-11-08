"""Test classes for Bookmark tests

:Requirement: Bookmark

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

from airgun.session import Session
from fauxfactory import gen_string
from nailgun import entities

from robottelo.constants import BOOKMARK_ENTITIES
from robottelo.decorators import bz_bug_is_open, fixture, rm_bug_is_open, tier2


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def ui_entities(module_org):
    """Collects the list of all applicable UI entities for testing and does all
    required preconditions.
    """
    ui_entities = []
    for entity in BOOKMARK_ENTITIES:
        # Skip the entities, which can't be tested ATM (not implemented in
        # airgun or have open BZs)
        skip = entity.get('skip_for_ui')
        if isinstance(skip, tuple):
            bug_type, bug_id = skip
            if (bug_type == 'bugzilla' and bz_bug_is_open(bug_id)
                    or bug_type == 'redmine' and rm_bug_is_open(bug_id)):
                skip = True
        if skip is True:
            continue
        ui_entities.append(entity)
        # Some pages require at least 1 existing entity for search bar to
        # appear. Creating 1 entity for such pages
        entity_name, entity_setup = entity['name'], entity.get('setup')
        if entity_setup:
            # entities with 1 organization
            if entity_name in ('Host',):
                entity_setup(organization=module_org).create()
            # entities with no organizations
            elif entity_name in (
                    'ComputeProfile',
                    'ConfigGroup',
                    'GlobalParameter',
                    'HardwareModel',
                    'PuppetClass',
                    'UserGroup'):
                entity_setup().create()
            # entities with multiple organizations
            else:
                entity_setup(organization=[module_org]).create()
    return ui_entities


@fixture()
def random_entity(ui_entities):
    """Returns one random entity from list of available UI entities"""
    return ui_entities[random.randint(0, len(ui_entities) - 1)]


@tier2
def test_positive_create_bookmark_public(
        session, random_entity, module_viewer_user, test_name):
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
            ui_lib.create_bookmark({
                'name': name,
                'query': gen_string('alphanumeric'),
                'public': name == public_name,
            })
            assert session.bookmark.search(name)[0]['Name'] == name
    with Session(test_name, module_viewer_user.login, module_viewer_user.password) as session:
        assert session.bookmark.search(public_name)[0]['Name'] == public_name
        assert not session.bookmark.search(nonpublic_name)
