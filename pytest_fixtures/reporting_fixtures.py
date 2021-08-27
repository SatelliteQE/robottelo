import datetime

import pytest
from _pytest.junitxml import xml_key
from xdist import get_xdist_worker_id

from robottelo.config import setting_is_set
from robottelo.config import settings


FMT_XUNIT_TIME = '%Y-%m-%dT%H:%M:%S'


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
        f'shared_function enabled - {shared_function_enabled} - '
        f'scope: {scope} - storage: {storage}'
    )
    return messages


def pytest_sessionstart(session):
    """Workaround for https://github.com/pytest-dev/pytest/issues/7767

    remove if resolved and set autouse=True for record_testsuite_timestamp_xml fixture
    """
    if get_xdist_worker_id(session) == 'master':
        if session.config.pluginmanager.hasplugin('junitxml'):
            xml = session.config._store.get(xml_key, None)
            if xml:
                xml.add_global_property(
                    'start_time', datetime.datetime.utcnow().strftime(FMT_XUNIT_TIME)
                )


@pytest.fixture(autouse=False, scope='session')
def record_testsuite_timestamp_xml(record_testsuite_property):
    now = datetime.datetime.utcnow()
    record_testsuite_property('start_time', now.strftime(FMT_XUNIT_TIME))
