"""Test for bookmark related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Search

:Assignee: jhenner

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.constants import BOOKMARK_ENTITIES


class TestPublicDisabledBookmarkPostUpgrade:
    """
    Test public disabled Bookmarks created before upgrade should be unchanged after upgrade.

    :id: c4f90034-ea57-4a4d-9b73-0f57f824d89e

    :steps:

        1. Create public disabled bookmarks before the upgrade for all system entities
        using available bookmark data.
        2. Check the bookmark attribute status(controller, name, query public)
        for all the system entities.
        3. Upgrade the satellite.
        4. Check the bookmark status after post-upgrade.
        5. Remove the bookmark.

    :expectedresults:

        1. Before upgrade, Public disabled bookmark should be created successfully.
        2. After upgrade,Public disabled bookmarks details for all the system entities
        should be unchanged after upgrade.

    :bz: 1833264, 1826734, 1862119
    """

    @pytest.mark.pre_upgrade
    def test_pre_create_public_disable_bookmark(self, request):
        """
        Create public disabled bookmarks for system entities using available bookmark data.
        """

        for entity in BOOKMARK_ENTITIES:
            book_mark_name = entity["name"] + request.node.name
            bm = entities.Bookmark(
                controller=entity['controller'],
                name=book_mark_name,
                public=False,
                query=f"name={book_mark_name}",
            ).create()

            assert bm.controller == entity['controller']
            assert bm.name == book_mark_name
            assert bm.query == f"name={book_mark_name}"
            assert not bm.public

    @pytest.mark.post_upgrade(depend_on=test_pre_create_public_disable_bookmark)
    def test_post_create_public_disable_bookmark(self, dependent_scenario_name):
        """
        Check the status of public disabled bookmark for all the system entities(activation keys,
        tasks, compute profile, content hosts etc) after upgrade.
        """
        pre_test_name = dependent_scenario_name
        for entity in BOOKMARK_ENTITIES:
            book_mark_name = entity["name"] + pre_test_name
            bm = entities.Bookmark().search(query={'search': f'name="{book_mark_name}"'})[0]
            assert bm.controller == entity['controller']
            assert bm.name == book_mark_name
            assert bm.query == f"name={book_mark_name}"
            assert not bm.public
            bm.delete()


class TestPublicEnabledBookmarkPostUpgrade:
    """
    Test public enabled Bookmarks created before upgrade should be unchanged after upgrade.

    :id: c4f90034-ea57-4a4d-9b73-0f57f824d89e

    :steps:

        1. Create public enable bookmarks before the upgrade for all system entities
        using available bookmark data.
        2. Check the bookmark attribute(controller, name, query public) status
        for all the system entities.
        3. Upgrade the Satellite.
        4. Check the bookmark status after post-upgrade.
        5. Remove the bookmark.

    :expectedresults:

        1. Before upgrade, Public enabled bookmark should be created successfully.
        2. After upgrade, Public disabled bookmarks details for all the system entities
        should be unchanged after upgrade.

    :bz: 1833264, 1826734, 1862119
    """

    @pytest.mark.pre_upgrade
    def test_pre_create_public_enable_bookmark(self, request):
        """
        Create public enable bookmark for system entities using available bookmark data.
        """

        for entity in BOOKMARK_ENTITIES:
            book_mark_name = entity["name"] + request.node.name
            bm = entities.Bookmark(
                controller=entity['controller'],
                name=book_mark_name,
                public=True,
                query=f"name={book_mark_name}",
            ).create()
            assert bm.controller == entity['controller']
            assert bm.name == book_mark_name
            assert bm.query == f"name={book_mark_name}"
            assert bm.public

    @pytest.mark.post_upgrade(depend_on=test_pre_create_public_enable_bookmark)
    def test_post_create_public_enable_bookmark(self, dependent_scenario_name):
        """Check the status of public enabled bookmark for all the
        system entities(activation keys, tasks, compute profile, content hosts etc) after upgrade.
        """
        pre_test_name = dependent_scenario_name
        for entity in BOOKMARK_ENTITIES:
            book_mark_name = entity["name"] + pre_test_name
            bm = entities.Bookmark().search(query={'search': f'name="{book_mark_name}"'})[0]
            assert bm.controller == entity['controller']
            assert bm.name == book_mark_name
            assert bm.query == f"name={book_mark_name}"
            assert bm.public
            bm.delete()
