"""
This module is intended to be used for upgrade tests, that have two run stages,

    First stage: pre_upgrade::

        The test marked as pre_upgrade will be run the tests can save data, to be restored later in
        post upgrade stage.

        pytest -m "pre_upgrade" tests/foreman/upgrade

    Second stage: post_upgrade::

        The test marked as post upgrade will be run, any saved data in dependent pre_upgrade stage
        can be restored, if a dependent test fail, the post upgrade test will be skipped

        pytest -m "post_upgrade" tests/foreman/upgrade

    Example upgrade test module content: file test_upgrade.py::

        import pytest

        from upgrade_tests import pre_upgrade, post_upgrade

        @pre_upgrade
        def test_capsule_pre_upgrade(save_test_data):
            '''A pre upgrade test that should pass and save data'''
            assert 1 == 1
            data_value = {'id': 100, 'env_id': 500}
            save_test_data(data_value)


        @pre_upgrade
        def test_capsule_pre_upgrade_2(save_test_data):
            '''A pre upgrade test that should pass and save data'''
            assert 1 == 1
            data_value = {'id': 1, 'cv_id': 3}
            save_test_data(data_value)


        @pre_upgrade
        def test_capsule_pre_upgrade_fail():
            '''A pre upgrade test that should fail'''
            assert 1 == 0

        @pytest.mark.skip(reason="The post upgrade dependent tests should skip too")
        @pre_upgrade
        def test_capsule_pre_upgrade_skipped():
            '''A pre upgrade test that should be skipped'''
            assert 1 == 0


        @post_upgrade(depend_on=test_capsule_pre_upgrade)
        def test_capsule_post_upgrade(pre_upgrade_data):
            '''Test with one dependent pre_upgrade test'''
            assert pre_upgrade_data == {'id': 100, 'env_id': 500}


        # The post_upgrade test can depend from many pre_upgrade tests

        @post_upgrade(depend_on=[test_capsule_pre_upgrade, test_capsule_pre_upgrade_2])
        def test_capsule_post_upgrade_2(pre_upgrade_data):
            '''Test with multiple dependent pre_upgrade tests'''
            # The saved data is restored in the same order as in the list in depend_on
            test_data, test_data_2 = pre_upgrade_data
            assert test_data == {'id': 100, 'env_id': 500}
            assert test_data_2 == {'id': 1, 'cv_id': 3}


        @post_upgrade(depend_on=test_capsule_pre_upgrade_fail)
        def test_capsule_post_upgrade_fail(pre_upgrade_data):
            '''Test must be skipped as test_capsule_pre_upgrade_fail should fail'''
            assert 1 == 0


        @post_upgrade(depend_on=test_capsule_pre_upgrade_skipped)
        def test_capsule_post_upgrade_skipped(pre_upgrade_data):
            '''Test must be skipped as test_capsule_pre_upgrade_skipped should be skipped'''
            assert 1 == 0

        # in pre_upgrade scenario, test results should be
        #  1 failed, 2 passed, 1 skipped, 4 deselected

        # in post_upgrade scenario, test results should be
        #  2 passed, 6 deselected
"""
import datetime
import functools
import json
import os

import pytest
from automation_tools.satellite6.hammer import set_hammer_config
from fabric.api import env

from robottelo.config import settings
from robottelo.decorators.func_locker import lock_function
from robottelo.logging import logger


pytest_plugins = 'tests.upgrades.scenario_workers'

pre_upgrade_failed_tests = []


PRE_UPGRADE_TESTS_FILE_OPTION = 'pre_upgrade_tests_file'
PRE_UPGRADE_TESTS_FILE_PATH = '/var/tmp/robottelo_pre_upgrade_failed_tests.json'
PRE_UPGRADE = False
POST_UPGRADE = False
PRE_UPGRADE_MARK = 'pre_upgrade'
POST_UPGRADE_MARK = 'post_upgrade'
TEST_NODE_ID_NAME = '__pytest_node_id'

__initiated = False


class OptionMarksError(Exception):
    """ "Raised when upgrade marks are missing or badly used in runner options"""


def log(message, level="DEBUG"):
    """Pytest has a limitation to use logging.logger from conftest.py
    so we need to emulate the logger by std-out the output
    """
    now = datetime.datetime.now()
    full_message = "{date} - conftest - {level} - {message}\n".format(
        date=now.strftime("%Y-%m-%d %H:%M:%S"), level=level, message=message
    )
    print(full_message)  # noqa
    with open('robottelo.log', 'a') as log_file:
        log_file.write(full_message)


# todo remove when upgrade_tests will be python 3 compatible
def create_dict(entities_dict):
    """Stores a global dictionary of entities created in satellite by the
    scenarios tested, so that these entities can be retrieved post upgrade
    to assert the test cases.

    :param dict entities_dict: A dictionary of entities created in
        satellite
    """
    if os.path.exists('scenario_entities'):
        with open('scenario_entities') as entities_data:
            data = json.load(entities_data)
        data.update(entities_dict)
        with open('scenario_entities', 'w') as entities_data:
            json.dump(data, entities_data)
    else:
        with open('scenario_entities', 'w') as entities_data:
            json.dump(entities_dict, entities_data)


# todo remove when upgrade_tests will be python 3 compatible
def get_entity_data(scenario_name):
    """Fetches the dictionary of entities from the disk depending on the
    Scenario name (class name in which test is defined)

    :param str scenario_name: The name of the class for which the data is
        to fetched
    :returns dict entity_data: Returns a dictionary of entities
    """
    with open('scenario_entities') as pref:
        entity_data = json.load(pref)
        entity_data = entity_data.get(scenario_name)
    return entity_data


def _read_test_data(test_node_id):
    """Read the saved data of test at node id"""
    try:
        data = get_entity_data(test_node_id)
    except KeyError:
        data = None
    return data


def _set_test_node_id(test_func, node_id):
    """Mark the test function with it's node_id"""
    setattr(test_func, TEST_NODE_ID_NAME, node_id)


def _get_test_node_id(test_func):
    """Return the test function node_id"""
    return getattr(test_func, TEST_NODE_ID_NAME)


@lock_function
def _save_test_data(test_node_id, value):
    """Save the test data value with key node_id"""
    create_dict({test_node_id: value})


@pytest.fixture
def save_test_data(request):
    """A fixture to allow saving test data

    Usage::

        @pre_upgrade
        def test_something_pre_upgrade(save_test_data):
            ...

            save_test_data({'key': some_value})
    """
    test_node_id = _get_test_node_id(request.function)
    return functools.partial(_save_test_data, test_node_id)


@pytest.fixture
def pre_upgrade_data(request):
    """A fixture to allow restoring the saved data in pre_upgrade stage

    Usage::

       @post_upgrade(depend_on=test_something_pre_upgrade)
       def test_something_post_upgrade(pre_upgrade_data):
           # restoring
           pre_upgrade_key_value = pre_upgrade_data['key']
    """
    dependant_on_functions = []
    for marker in request.node.iter_markers(POST_UPGRADE_MARK):
        depend_on = marker.kwargs.get('depend_on')
        if isinstance(depend_on, (list, tuple)):
            dependant_on_functions.extend(depend_on)
        elif depend_on is not None:
            dependant_on_functions.append(depend_on)
    depend_on_node_ids = [_get_test_node_id(f) for f in dependant_on_functions]
    data = [_read_test_data(test_node_id) for test_node_id in depend_on_node_ids]
    if len(data) == 1:
        data = data[0]
    return data


def pytest_sessionstart(session):
    """Do some setup for automation-tools and satellite6-upgrade"""
    # Fabric Config setup
    env.host_string = settings.server.hostname
    env.user = settings.server.ssh_username
    # Hammer Config Setup
    set_hammer_config(user=settings.server.admin_username, password=settings.server.admin_password)


def pytest_addoption(parser):
    """This will add an option to the runner to be able to customize the location of the failed
    tests file.

    Usage::

        pytest --pre_upgrade_tests_file file_location

    Note: default location is /var/tmp/robottelo_pre_upgrade_failed_tests.json
    """
    parser.addoption(
        f'--{PRE_UPGRADE_TESTS_FILE_OPTION}',
        action='store',
        default=PRE_UPGRADE_TESTS_FILE_PATH,
    )


def __initiate(config):
    """Do basic initialization for this module"""
    global __initiated
    if __initiated:
        return
    global pre_upgrade_failed_tests
    global PRE_UPGRADE
    global POST_UPGRADE
    global PRE_UPGRADE_TESTS_FILE_PATH
    PRE_UPGRADE_TESTS_FILE_PATH = getattr(config.option, PRE_UPGRADE_TESTS_FILE_OPTION)
    if not [
        upgrade_mark
        for upgrade_mark in (PRE_UPGRADE_MARK, POST_UPGRADE_MARK)
        if upgrade_mark in config.option.markexpr
    ]:
        pytest.skip(
            'options error: pre_upgrade or post_upgrade marks must be selected',
            allow_module_level=True,
        )
    if PRE_UPGRADE_MARK in config.option.markexpr:
        pre_upgrade_failed_tests = []
        PRE_UPGRADE = True
        # remove file before begin
        if os.path.exists(PRE_UPGRADE_TESTS_FILE_PATH):
            os.unlink(PRE_UPGRADE_TESTS_FILE_PATH)
    if POST_UPGRADE_MARK in config.option.markexpr:
        if PRE_UPGRADE:
            raise OptionMarksError(
                'options error: cannot do pre_upgrade and post_upgrade at the same time'
            )
        POST_UPGRADE = True
        pre_upgrade_failed_tests = []
        if os.path.exists(PRE_UPGRADE_TESTS_FILE_PATH):
            with open(PRE_UPGRADE_TESTS_FILE_PATH) as json_file:
                pre_upgrade_failed_tests = json.load(json_file)
    __initiated = True


def pytest_report_header(config):
    """Initialise at test runner startup"""
    __initiate(config)


def pytest_terminal_summary(terminalreporter, exitstatus):
    """Add a section to terminal summary reporting."""
    if PRE_UPGRADE:
        # Save the failed tests to file
        failed_test_reports = []
        for key in ['failed', 'error', 'skipped']:
            failed_test_reports.extend(terminalreporter.stats.get(key, []))
        failed_test_node_ids = [test_report.nodeid for test_report in failed_test_reports]
        logger.info('Save failed tests to file %s', PRE_UPGRADE_TESTS_FILE_PATH)
        with open(PRE_UPGRADE_TESTS_FILE_PATH, 'w') as json_file:
            json.dump(failed_test_node_ids, json_file)


def pytest_collection_modifyitems(items, config):
    """Called after collection has been performed"""
    # ensure initiated
    __initiate(config)

    # mark the pre upgrade test functions with node_id
    pre_upgrade_items = [
        item for item in items if item.get_closest_marker(PRE_UPGRADE_MARK) is not None
    ]
    for item in pre_upgrade_items:
        _set_test_node_id(item.function, item.nodeid)

    if POST_UPGRADE:
        # will skip item/post_upgrade test if pre_upgrade test status failed.
        post_upgrade_items = [
            item for item in items if item.get_closest_marker(POST_UPGRADE_MARK) is not None
        ]
        deselected_items = []
        for item in post_upgrade_items:
            dependant_on_functions = []
            for marker in item.iter_markers(POST_UPGRADE_MARK):
                depend_on = marker.kwargs.get('depend_on')
                if isinstance(depend_on, (list, tuple)):
                    dependant_on_functions.extend(depend_on)
                elif depend_on is not None:
                    dependant_on_functions.append(depend_on)
                depend_on_node_ids = [_get_test_node_id(f) for f in dependant_on_functions]
                for depend_on_node_id in depend_on_node_ids:
                    if depend_on_node_id in pre_upgrade_failed_tests:
                        log(
                            f'Deselected (because of dependant test failed): {item.nodeid}',
                            'INFO',
                        )
                        deselected_items.append(item)

        config.hook.pytest_deselected(items=deselected_items)
        items[:] = [item for item in items if item not in deselected_items]
