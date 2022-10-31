"""Tests for common Bookmark operations via API

:Requirement: Bookmarks

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
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.constants import BOOKMARK_ENTITIES
from robottelo.utils.datafactory import invalid_values_list
from robottelo.utils.datafactory import valid_data_list


# List of unique bookmark controller values, preserving order
CONTROLLERS = list(dict.fromkeys(entity['controller'] for entity in BOOKMARK_ENTITIES))


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_positive_create_with_name(controller):
    """Create a bookmark

    :id: aeef0944-379a-4a27-902d-aa5969dbd441

    :parametrized: yes

    :Steps:

        1. Create a bookmark with a random name and valid controller.
        2. List the bookmarks.

    :expectedresults:

        2. bookmark is listed. Name and controller match the ones specified.

    :CaseImportance: Critical
    """
    name = random.choice(list(valid_data_list().values()))
    bm = entities.Bookmark(controller=controller, name=name, public=False).create()
    assert bm.controller == controller
    assert bm.name == name


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_positive_create_with_query(controller):
    """Create a bookmark

    :id: 9fb6d485-92b5-43ea-b776-012c13734100

    :parametrized: yes

    :Steps:

        1. Create a bookmark with a random query and valid controller.
        2. List the bookmarks.

    :expectedresults:

        2. Bookmark is listed. Query and controller match the ones specified.

    :CaseImportance: Critical
    """
    query = random.choice(list(valid_data_list().values()))
    bm = entities.Bookmark(controller=controller, query=query).create()
    assert bm.controller == controller
    assert bm.query == query


@pytest.mark.tier1
@pytest.mark.parametrize('public', (True, False))
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_positive_create_public(controller, public):
    """Create a public bookmark

    :id: 511b9bcf-0661-4e44-b1bc-475a1c207aa9

    :parametrized: yes

    :Steps:

        1. Create a bookmark with a valid controller and public attribute True or False.
        2. List the bookmarks.

    :expectedresults:

        2. Bookmark is listed. Controller and public attribute match the ones specified.

    :CaseImportance: Critical
    """
    bm = entities.Bookmark(controller=controller, public=public).create()
    assert bm.controller == controller
    assert bm.public == public


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_negative_create_with_invalid_name(controller):
    """Create a bookmark with invalid name

    :id: 9a79c561-8225-43fc-8ec7-b6858e9665e2

    :parametrized: yes

    :Steps:

        1. Attempt to create a bookmark with an invalid name.
        2. List the bookmarks.

    :expectedresults:

        1. Error returned.
        2. Bookmark is not listed.

    :CaseImportance: Critical
    """
    name = random.choice(invalid_values_list())
    with pytest.raises(HTTPError):
        entities.Bookmark(controller=controller, name=name, public=False).create()
    result = entities.Bookmark().search(query={'search': f'name="{name}"'})
    assert len(result) == 0


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_negative_create_empty_query(controller):
    """Create a bookmark with empty query

    :id: 674d569f-6f86-43ba-b9cc-f43e05e8ab1c

    :parametrized: yes

    :Steps:

        1. Attempt to create a bookmark with a random name, valid controller, and empty query.
        2. List the bookmarks.

    :expectedresults:

        1. Error returned.
        2. Bookmark is not listed.

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with pytest.raises(HTTPError):
        entities.Bookmark(controller=controller, name=name, query='').create()
    result = entities.Bookmark().search(query={'search': f'name="{name}"'})
    assert len(result) == 0


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_negative_create_same_name(controller):
    """Create bookmarks with the same names

    :id: f78f6e97-da77-4a61-95c2-622c439d325d

    :parametrized: yes

    :Steps:

        1. Create a bookmark with a random name and valid controller.
        2. Attempt to create a second bookmark, using the same name as the previous bookmark.
        3. List the bookmarks.

    :expectedresults:

        2. Error returned.
        3. Only the first bookmark is listed.

    :CaseImportance: Critical
    """
    name = gen_string('alphanumeric')
    entities.Bookmark(controller=controller, name=name).create()
    with pytest.raises(HTTPError):
        entities.Bookmark(controller=controller, name=name).create()
    result = entities.Bookmark().search(query={'search': f'name="{name}"'})
    assert len(result) == 1


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_negative_create_null_public(controller):
    """Create a bookmark omitting the public parameter

    :id: 0a4cb5ea-912b-445e-a874-b345e43d3eac

    :parametrized: yes

    :Steps:

        1. Attempt to create a bookmark with a random name and valid controller, with public
        attribute set to None.
        2. List the bookmarks.

    :expectedresults:

        1. Error returned.
        2. Bookmark is not listed.

    :BZ: 1302725

    :CaseImportance: Critical
    """
    name = gen_string('alphanumeric')
    with pytest.raises(HTTPError):
        entities.Bookmark(controller=controller, name=name, public=None).create()
    result = entities.Bookmark().search(query={'search': f'name="{name}"'})
    assert len(result) == 0


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_positive_update_name(controller):
    """Update a bookmark

    :id: 1cde270a-26fb-4cff-bdff-89fef17a7624

    :parametrized: yes

    :Steps:

        1. Create a bookmark with a valid controller.
        2. Update the bookmark with a random name.

    :expectedresults:

        2. The updated bookmark has the new name.

    :CaseImportance: Critical
    """
    new_name = random.choice(list(valid_data_list().values()))
    bm = entities.Bookmark(controller=controller, public=False).create()
    bm.name = new_name
    bm = bm.update(['name'])
    assert bm.name == new_name


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_negative_update_same_name(controller):
    """Update a bookmark with name already taken

    :id: 6becf121-2bea-4f7e-98f4-338bd88b8f4b

    :parametrized: yes

    :Steps:

        1. Create a bookmark with a random name and valid controller.
        2. Create a second bookmark for the same controller.
        3. Attempt to update the second bookmark to have the same name as the first bookmark.

    :expectedresults:

        3. Error returned. Second bookmark's name is not updated.

    :CaseImportance: Critical
    """
    name = gen_string('alphanumeric')
    entities.Bookmark(controller=controller, name=name).create()
    bm = entities.Bookmark(controller=controller).create()
    bm.name = name
    with pytest.raises(HTTPError):
        bm.update(['name'])
    bm = bm.read()
    assert bm.name != name


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_negative_update_invalid_name(controller):
    """Update a bookmark with an invalid name

    :id: 479795bb-aeed-45b3-a7e3-d3449c808087

    :parametrized: yes

    :Steps:

        1. Create a bookmark with valid controller.
        2. Attempt to update the bookmark with an invalid name.

    :expectedresults:

        2. Error returned. Bookmark name is not updated.

    :CaseImportance: Critical
    """
    new_name = random.choice(invalid_values_list())
    bm = entities.Bookmark(controller=controller, public=False).create()
    bm.name = new_name
    with pytest.raises(HTTPError):
        bm.update(['name'])
    bm = bm.read()
    assert bm.name != new_name


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_positive_update_query(controller):
    """Update a bookmark query

    :id: 92a31de2-bebf-4396-94f5-adf59f8d66a5

    :parametrized: yes

    :Steps:

        1. Create a bookmark with a valid controller.
        2. Update the bookmark's query with a random value.

    :expectedresults:

        2. The updated bookmark has the new query.

    :CaseImportance: Critical
    """
    new_query = random.choice(list(valid_data_list().values()))
    bm = entities.Bookmark(controller=controller).create()
    bm.query = new_query
    bm = bm.update(['query'])
    assert bm.query == new_query


@pytest.mark.tier1
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_negative_update_empty_query(controller):
    """Update a bookmark with an empty query

    :id: 948602d3-532a-47fe-b313-91e3fab809bf

    :parametrized: yes

    :Steps:

        1. Create a bookmark for a valid controller.
        2. Attempt to update the query to an empty value.

    :expectedresults:

        2. Error returned. Query is not empty.

    :CaseImportance: Critical
    """
    bm = entities.Bookmark(controller=controller).create()
    bm.query = ''
    with pytest.raises(HTTPError):
        bm.update(['query'])
    bm = bm.read()
    assert bm.query != ''


@pytest.mark.tier1
@pytest.mark.parametrize('public', (True, False))
@pytest.mark.parametrize('controller', CONTROLLERS)
def test_positive_update_public(controller, public):
    """Update a bookmark public state to private and vice versa

    :id: 2717360d-37c4-4bb9-bce1-b1edabdf11b3

    :parametrized: yes

    :Steps:

        1. Create a bookmark for a valid controller.
        2. Update the bookmark's public attribute.
        3. List the bookmarks.

    :expectedresults:

        3. Bookmark is updated with the new public attribute.

    :CaseImportance: Critical
    """
    bm = entities.Bookmark(controller=controller, public=not public).create()
    assert bm.public != public
    bm.public = public
    bm = bm.update(['public'])
    assert bm.public == public
