import datetime
import functools
import json
import logging
import os


from pytest import fixture, hookspec

from robottelo.decorators.func_locker import lock_function
from robottelo.helpers import get_func_name

LOGGER = logging.getLogger('robottelo')

pre_upgrade_failed_tests = []


PRE_UPGRADE_TESTS_FILE_OPTION = 'pre_upgrade_tests_file'
PRE_UPGRADE_TESTS_FILE_PATH = '/var/tmp/robottelo_pre_upgrade_failed_tests.json'
PRE_UPGRADE = False
POST_UPGRADE = False
PRE_UPGRADE_MARK = 'pre_upgrade'
POST_UPGRADE_MARK = 'post_upgrade'

__initiated = False


def log(message, level="DEBUG"):
    """Pytest has a limitation to use logging.logger from conftest.py
    so we need to emulate the logger by std-out the output
    """
    now = datetime.datetime.now()
    full_message = "{date} - conftest - {level} - {message}\n".format(
        date=now.strftime("%Y-%m-%d %H:%M:%S"),
        level=level,
        message=message
    )
    print(full_message)  # noqa
    with open('robottelo.log', 'a') as log_file:
        log_file.write(full_message)


# todo remove when upgrade_tests will be python 3 compatible
def _create_dict(entities_dict):
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
def _get_entity_data(scenario_name):
    """Fetches the dictionary of entities from the disk depending on the
    Scenario name (class name in which test is defined)

    :param string scenario_name : The name of the class for which the data is
        to fetched
    :returns dict entity_data : Returns a dictionary of entities
    """
    with open('scenario_entities') as pref:
        entity_data = json.load(pref)
        entity_data = entity_data.get(scenario_name)
    return entity_data


def _get_request_test_name(request):
    return '.'.join([request.module.__name__, request.node.name])


def _get_node_id_test_name(node_id):
    test_name = node_id.replace('.py', '')
    test_name = test_name.replace(os.sep, '.')
    test_name = test_name.replace('::', '.')
    return test_name


@lock_function
def _save_test_data(test_name, value):
    _create_dict({test_name: value})


@fixture
def save_test_data(request):
    test_name = _get_request_test_name(request)
    return functools.partial(_save_test_data, test_name)


@fixture
def pre_upgrade_data(request):
    dependant_on_functions = []
    for marker in request.node.iter_markers(POST_UPGRADE_MARK):
        depend_on = marker.kwargs.get('depend_on')
        if isinstance(depend_on, (list, tuple)):
            dependant_on_functions.extend(depend_on)
        elif depend_on is not None:
            dependant_on_functions.append(depend_on)
    depend_on_names = [get_func_name(f) for f in dependant_on_functions]
    data = [_get_entity_data(func_name) for func_name in depend_on_names]
    if len(data) == 1:
        data = data[0]
    return data


def pytest_addoption(parser):
    parser.addoption(
        '--{0}'.format(PRE_UPGRADE_TESTS_FILE_OPTION),
        action='store',
        default=PRE_UPGRADE_TESTS_FILE_PATH
    )


def __initiate(config):
    global __initiated
    if __initiated:
        return
    global pre_upgrade_failed_tests
    global PRE_UPGRADE
    global POST_UPGRADE
    global PRE_UPGRADE_TESTS_FILE_PATH
    PRE_UPGRADE_TESTS_FILE_PATH = getattr(config.option, PRE_UPGRADE_TESTS_FILE_OPTION)
    if not [upgrade_mark for upgrade_mark in (PRE_UPGRADE_MARK, POST_UPGRADE_MARK)
            if upgrade_mark in config.option.markexpr]:
        raise Exception('options error: pre_upgrade or post_upgrade marks must be selected')
    if PRE_UPGRADE_MARK in config.option.markexpr:
        pre_upgrade_failed_tests = []
        PRE_UPGRADE = True
        # remove file before begin
        if os.path.exists(PRE_UPGRADE_TESTS_FILE_PATH):
            os.unlink(PRE_UPGRADE_TESTS_FILE_PATH)
    if POST_UPGRADE_MARK in config.option.markexpr:
        if PRE_UPGRADE:
            raise Exception('options error: cannot do pre_upgrade and post_upgrade at the same'
                            ' time')
        POST_UPGRADE = True
        pre_upgrade_failed_tests = []
        if os.path.exists(PRE_UPGRADE_TESTS_FILE_PATH):
            with open(PRE_UPGRADE_TESTS_FILE_PATH, 'r') as json_file:
                pre_upgrade_failed_tests = json.load(json_file)
    __initiated = True


def pytest_report_header(config):
    __initiate(config)


@hookspec(firstresult=True)
def pytest_report_teststatus(report):
    global pre_upgrade_failed_tests
    if PRE_UPGRADE and report.outcome != 'passed':
        pre_upgrade_failed_tests.append(report.nodeid)


def pytest_terminal_summary(terminalreporter, exitstatus):
    """Add a section to terminal summary reporting."""
    if PRE_UPGRADE and exitstatus:
        failed_test_reports = list(terminalreporter.stats.get('failed', []))
        failed_test_reports.extend(terminalreporter.stats.get('error', []))
        failed_test_names = [_get_node_id_test_name(test_report.nodeid)
                             for test_report in failed_test_reports]
        LOGGER.info('Save failed tests to file %s', PRE_UPGRADE_TESTS_FILE_PATH)
        with open(PRE_UPGRADE_TESTS_FILE_PATH, 'w') as json_file:
            json.dump(failed_test_names, json_file)


def pytest_collection_modifyitems(items, config):
    """Called after collection has been performed, will skip item/post_upgrade test if
    pre_upgrade test status is failed.
    """
    __initiate(config)
    if POST_UPGRADE:
        post_upgrade_items = [
            item
            for item in items if item.get_marker(POST_UPGRADE_MARK) is not None
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
                depend_on_names = [get_func_name(f) for f in dependant_on_functions]
                # raise Exception(depend_on_names)
                for depend_on_name in depend_on_names:
                    if depend_on_name in pre_upgrade_failed_tests:
                        log('Deselected (because of dependant test failed): {}'.format(
                            get_func_name(item.function, item)), 'INFO')
                        deselected_items.append(item)

        config.hook.pytest_deselected(items=deselected_items)
        items[:] = [item for item in items if item not in deselected_items]
