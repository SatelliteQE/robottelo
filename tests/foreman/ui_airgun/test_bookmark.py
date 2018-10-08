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
def custom_user(module_org):
    """Custom user with viewer role for tests validating 'public' bookmark
    option.
    """
    viewer_role = entities.Role().search(query={'search': 'name="Viewer"'})[0]
    bm_role = entities.Role().create()
    entities.Filter(
        permission=entities.Permission(
            resource_type='Bookmark').search(
            filters={'name': 'view_bookmarks'}),
        role=bm_role,
    ).create()
    custom_password = gen_string('alphanumeric')
    custom_user = entities.User(
        default_organization=module_org,
        organization=[module_org],
        role=[viewer_role, bm_role],
        password=custom_password,
    ).create()
    custom_user.password = custom_password
    return custom_user


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
            if (skip[0] == 'bugzilla' and bz_bug_is_open(skip[1])
                    or skip[0] == 'redmine' and rm_bug_is_open(skip[1])):
                skip = True
        if skip is True:
            continue
        ui_entities.append(entity)
        # Some pages require at least 1 existing entity for search bar to
        # appear. Creating 1 entity for such pages
        if entity.get('setup'):
            # entities with 1 organization
            if entity['name'] in ('Host',):
                entity['setup'](organization=module_org).create()
            # entities with no organizations
            elif entity['name'] in (
                    'ComputeProfile',
                    'ConfigGroup',
                    'GlobalParameter',
                    'HardwareModel',
                    'PuppetClass',
                    'UserGroup'):
                entity['setup']().create()
            # entities with multiple organizations
            else:
                entity['setup'](organization=[module_org]).create()
    return ui_entities


@fixture()
def random_entity(ui_entities):
    """Returns one random entity from list of available UI entities"""
    return ui_entities[random.randint(0, len(ui_entities) - 1)]


@tier2
def test_positive_create_bookmark_public(
        session, random_entity, custom_user, test_name):
    """Create and check visibility of the (non)public bookmarks

    :id: 93139529-7690-429b-83fe-3dcbac4f91dc

    :Setup: Create a non-admin user with 'viewer' role

    :Steps:

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

    :expectedresults: No errors, Bookmark is displayed, controller matches
        the entity the bookmark was created for

    :CaseLevel: Integration
    """
    name = gen_string('alphanumeric')
    with session:
        ui_lib = getattr(session, random_entity['name'].lower())
        ui_lib.create_bookmark({
            'name': name,
            'query': gen_string('alphanumeric'),
            'public': False,
        })
        assert session.bookmark.search(name)[0]['Name'] == name
    with Session(
            test_name, custom_user.login, custom_user.password) as session:
        assert not session.bookmark.search(name)
