import datetime

from _pytest.junitxml import xml_key
import pytest
from xdist import get_xdist_worker_id

from robottelo.config import setting_is_set, settings
from robottelo.hosts import get_sat_rhel_version
from robottelo.logging import logger
from robottelo.utils.ohsnap import container_image_properties

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
        f'shared_function enabled - {shared_function_enabled} - scope: {scope} - storage: {storage}'
    )
    return messages


def pytest_sessionstart(session):
    """Workaround for https://github.com/pytest-dev/pytest/issues/7767

    remove if resolved and set autouse=True for record_testsuite_timestamp_xml fixture
    """
    if get_xdist_worker_id(session) == 'master' and session.config.pluginmanager.hasplugin(
        'junitxml'
    ):
        xml = session.config._store.get(xml_key, None)
        if xml:
            xml.add_global_property(
                'start_time', datetime.datetime.now(datetime.UTC).strftime(FMT_XUNIT_TIME)
            )
            rhel_version = get_sat_rhel_version().base_version
            sat_version = settings.server.version.get('release')
            snap_version = settings.server.version.get('snap', '')
            xml.add_global_property("SatelliteNetworkType", str(settings.server.network_type))
            xml.add_global_property("SatelliteVersion", sat_version)
            xml.add_global_property("SnapVersion", snap_version)
            xml.add_global_property("BaseOS", rhel_version)
            try:
                if settings.server.deploy_arguments.get('deploy_container'):
                    for name, value in container_image_properties(
                        settings.ohsnap,
                        sat_version,
                        snap_version,
                    ):
                        xml.add_global_property(name, value)
            except Exception:
                logger.warning('Failed to fetch container image properties for JUnit XML')


@pytest.fixture(autouse=False, scope='session')
def record_testsuite_timestamp_xml(record_testsuite_property):
    now = datetime.datetime.now(datetime.UTC)
    record_testsuite_property('start_time', now.strftime(FMT_XUNIT_TIME))
