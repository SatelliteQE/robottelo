"""Test for bookmark related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Search

:Assignee: jhenner

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade

from robottelo.constants import BOOKMARK_ENTITIES


class TestPublicDisableBookmark:
    """
    Public disabled Bookmarks created before upgrade should be unchanged after upgrade.

    """

    @pre_upgrade
    def test_pre_create_public_disable_bookmark(self, request):
        """Create public disabled bookmarks for system entities using available bookmark
        data.

        :id: preupgrade-c4f90034-ea57-4a4d-9b73-0f57f824d89e

        :Steps:

            1. Create public disabled bookmarks before the upgrade for all system entities
            using available bookmark data.
            2. Check the bookmark attribute status(controller, name, query public)
            for all the system entities.

        :expectedresults: Public disabled bookmark should be created successfully.

        :BZ: 1833264, 1826734, 1862119

        :CaseImportance: Critical
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

    @post_upgrade(depend_on=test_pre_create_public_disable_bookmark)
    def test_post_create_public_disable_bookmark(self, dependent_scenario_name):
        """Check the status of public disabled bookmark for all the
        system entities(activation keys, tasks, compute profile, content hosts etc) after upgrade.

        :id: postupgrade-3b3abb85-cad2-4cbb-ad21-2780523351fd

        :Steps:

            1. Check the bookmark status after post-upgrade.
            2. Remove the bookmark.

        :expectedresults: Public disabled bookmarks details for all the system entities
        should be unchanged after upgrade.

        :CaseImportance: Critical
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


class TestPublicEnableBookmark:
    """
    Public enabled Bookmarks created before upgrade should be unchanged after upgrade.
    """

    @pre_upgrade
    def test_pre_create_public_enable_bookmark(self, request):
        """Create public enable bookmark for system entities using available bookmark
        data.

        :id: preupgrade-c4f90034-ea57-4a4d-9b73-0f57f824d89e

        :Steps:

            1. Create public enable bookmarks before the upgrade for all system entities
            using available bookmark data.
            2. Check the bookmark attribute(controller, name, query public) status
            for all the system entities.

        :expectedresults: Public enabled bookmark should be created successfully.

        :BZ: 1833264, 1826734, 1862119

        :CaseImportance: Critical
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

    @post_upgrade(depend_on=test_pre_create_public_enable_bookmark)
    def test_post_create_public_enable_bookmark(self, dependent_scenario_name):
        """Check the status of public enabled bookmark for all the
        system entities(activation keys, tasks, compute profile, content hosts etc) after upgrade.

        :id: postupgrade-3b3abb85-cad2-4cbb-ad21-2780523351fd

        :Steps:

            1. Check the bookmark status after post-upgrade.
            2. Remove the bookmark.

        :expectedresults: Public disabled bookmarks details for all the system entities
        should be unchanged after upgrade.

        :CaseImportance: Critical
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
