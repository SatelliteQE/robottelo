# coding: utf-8
"""Configurations for py.test runner"""
import datetime
import pytest
from robottelo.config import settings
from robottelo.decorators import setting_is_set
from robottelo.bz_helpers import get_deselect_bug_ids, group_by_key
from robottelo.helpers import get_func_name


def log(message, level="DEBUG"):
    """Pytest has a limitation to use logging.logger from conftest.py
    so we need to emulate the logger by stdouting the output
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


def pytest_report_header(config):
    """Called when pytest session starts"""
    messages = []

    shared_function_enabled = 'OFF'
    scope = ''
    storage = 'file'
    if setting_is_set('shared_function'):
        if settings.shared_function.enabled:
            shared_function_enabled = 'ON'
        scope = settings.shared_function.scope
        if not scope:
            scope = ''
        storage = settings.shared_function.storage

    messages.append(
        'shared_function enabled - {0} - scope: {1} - storage: {2}'.format(
            shared_function_enabled, scope, storage))

    return messages


@pytest.fixture(scope="session")
def worker_id(request):
    """Gets the worker ID when running in multi-threading with xdist
    """
    if hasattr(request.config, 'slaveinput'):
        # return gw+(0..n)
        return request.config.slaveinput['slaveid']
    else:
        return 'master'


def pytest_namespace():
    """return dict of name->object to be made globally available in
    the pytest namespace.  This hook is called at plugin registration
    time.
    Object is accessible only via dotted notation `item.key.nested_key`

    Exposes the list of all WONTFIX bugs and a mapping between decorated
    functions and Bug IDS (populated by decorator).
    """
    log("Registering custom pytest_namespace")
    return {
        'bugzilla': {
            'wontfix_ids': get_deselect_bug_ids(log=log),
            'decorated_functions': []
        }
    }


def pytest_collection_modifyitems(items, config):
    """ called after collection has been performed, may filter or re-order
    the items in-place.

    Deselecting all tests skipped due to WONTFIX BZ.
    """
    if not settings.configured:
        settings.configure()

    if settings.bugzilla.wontfix_lookup is not True:
        # if lookup is disable return all collection unmodified
        log('Deselect of WONTFIX BZs is disabled in settings')
        return items

    deselected_items = []
    wontfix_ids = pytest.bugzilla.wontfix_ids
    decorated_functions = group_by_key(pytest.bugzilla.decorated_functions)

    log("Found WONTFIX in decorated tests %s" % wontfix_ids)
    log("Collected %s test cases" % len(items))

    for item in items:
        name = get_func_name(item.function)
        bug_ids = decorated_functions.get(name)
        if bug_ids:
            for bug_id in bug_ids:
                if bug_id in wontfix_ids:
                    deselected_items.append(item)
                    log("Deselected test %s due to WONTFIX" % name)
                    break

    config.hook.pytest_deselected(items=deselected_items)
    items[:] = [item for item in items if item not in deselected_items]
