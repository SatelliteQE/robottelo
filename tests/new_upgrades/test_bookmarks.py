"""Test for bookmark related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Search

:Team: Endeavour

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo.constants import BOOKMARK_ENTITIES_SELECTION
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def disabled_bookmark_setup(search_upgrade_shared_satellite, upgrade_action):
    """Create public disabled bookmarks for system entities using available bookmark
    data.

    :id: preupgrade-13904b14-6340-4b85-a56f-98080cf50a92

    :steps:

        1. Create public disabled bookmarks before the upgrade for all system entities
        using available bookmark data.
        2. Check the bookmark attribute status(controller, name, query public)
        for all the system entities.

    :expectedresults: Public disabled bookmark should be created successfully.

    :BZ: 1833264, 1826734, 1862119

    :customerscenario: true

    :CaseImportance: Critical
    """
    target_sat = search_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'test_name': None,
            }
        )
        test_name = f'bookmark_upgrade_{gen_alpha()}'
        test_data.test_name = test_name
        for entity in BOOKMARK_ENTITIES_SELECTION:
            bookmark_name = entity["name"] + test_name
            bm = target_sat.api.Bookmark(
                controller=entity['controller'],
                name=bookmark_name,
                public=False,
                query=f"name={bookmark_name}",
            ).create()

            assert bm.controller == entity['controller']
            assert bm.name == bookmark_name
            assert bm.query == f"name={bookmark_name}"
            assert not bm.public
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.search_upgrades
def test_post_disabled_bookmark(disabled_bookmark_setup):
    """Check the status of public disabled bookmark for all the
    system entities(activation keys, tasks, compute profile, content hosts etc) after upgrade.

    :id: postupgrade-13904b14-6340-4b85-a56f-98080cf50a92

    :steps:

        1. Check the bookmark status after post-upgrade.
        2. Remove the bookmark.

    :expectedresults: Public disabled bookmarks details for all the system entities
        should be unchanged after upgrade.

    :CaseImportance: Critical
    """
    target_sat = disabled_bookmark_setup.target_sat
    test_name = disabled_bookmark_setup.test_name
    for entity in BOOKMARK_ENTITIES_SELECTION:
        bookmark_name = entity["name"] + test_name
        bm = target_sat.api.Bookmark().search(query={'search': f'name="{bookmark_name}"'})[0]
        assert bm.controller == entity['controller']
        assert bm.name == bookmark_name
        assert bm.query == f"name={bookmark_name}"
        assert not bm.public
        bm.delete()


@pytest.fixture
def enabled_bookmark_setup(search_upgrade_shared_satellite, upgrade_action):
    """Create public enable bookmark for system entities using available bookmark
    data.

    :id: preupgrade-93c419db-66b4-4c9a-a82a-a6a68703881f

    :steps:
        1. Create public enable bookmarks before the upgrade for all system entities
        using available bookmark data.
        2. Check the bookmark attribute(controller, name, query public) status
        for all the system entities.

    :expectedresults: Public enabled bookmark should be created successfully.

    :BZ: 1833264, 1826734, 1862119

    :CaseImportance: Critical

    :customerscenario: true
    """
    target_sat = search_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'test_name': None,
            }
        )
        test_name = f'bookmark_upgrade_{gen_alpha()}'
        test_data.test_name = test_name
        for entity in BOOKMARK_ENTITIES_SELECTION:
            bookmark_name = entity["name"] + test_name
            bm = target_sat.api.Bookmark(
                controller=entity['controller'],
                name=bookmark_name,
                public=True,
                query=f"name={bookmark_name}",
            ).create()
            assert bm.controller == entity['controller']
            assert bm.name == bookmark_name
            assert bm.query == f"name={bookmark_name}"
            assert bm.public
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.search_upgrades
def test_post_enabled_bookmark(enabled_bookmark_setup):
    """Check the status of public enabled bookmark for all the
    system entities(activation keys, tasks, compute profile, content hosts etc) after upgrade.

    :id: postupgrade-93c419db-66b4-4c9a-a82a-a6a68703881f

    :steps:
        1. Check the bookmark status after post-upgrade.
        2. Remove the bookmark.

    :expectedresults: Public disabled bookmarks details for all the system entities
        should be unchanged after upgrade.

    :CaseImportance: Critical
    """
    target_sat = enabled_bookmark_setup.target_sat
    test_name = enabled_bookmark_setup.test_name
    for entity in BOOKMARK_ENTITIES_SELECTION:
        bookmark_name = entity["name"] + test_name
        bm = target_sat.api.Bookmark().search(query={'search': f'name="{bookmark_name}"'})[0]
        assert bm.controller == entity['controller']
        assert bm.name == bookmark_name
        assert bm.query == f"name={bookmark_name}"
        assert bm.public
        bm.delete()
