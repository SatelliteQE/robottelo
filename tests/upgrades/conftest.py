
import logging

import pytest

from upgrade_tests.helpers.scenarios import get_entity_data

LOGGER = logging.getLogger('robottelo')


def _skip_if_dependant_test_failed(item, marker):
    depending_test = marker.kwargs.get('depend_on')
    scenario_class_name = item.nodeid.split('::')[-2]
    scenario_entity = get_entity_data(scenario_class_name)
    if scenario_entity.get(depending_test) == "failed":
        skip_test = pytest.mark.skip(reason="As dependent pre-upgrade {1} test got failed".
                                     format(item.name, depending_test))
        item.add_marker(skip_test)


def pytest_collection_modifyitems(items):
    """ called after collection has been performed, will skip item/post-upgrade test if
    pre-upgrade test status is failed.

    """
    for item in items:
        try:
            for marker in item.own_markers:
                if 'post_upgrade' in marker.name and 'depend_on' in marker.kwargs:
                    _skip_if_dependant_test_failed(item, marker)
        except OSError as e:
            LOGGER.error("Error: {0}".format(e.errno))
        except KeyError:
            LOGGER.error("Error: Failed to find key in scenario_entities File")
        except ValueError:
            LOGGER.error("Error: scenario_entities file is empty")
