# Hostgroup Fixtures
import pytest
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.logging import logger


@pytest.fixture(scope='module')
def module_hostgroup():
    return entities.HostGroup().create()


@pytest.fixture(scope='class')
def class_hostgroup(class_org, class_location):
    """Create a hostgroup linked to specific org and location created at the class scope"""
    hostgroup = entities.HostGroup(organization=[class_org], location=[class_location]).create()
    yield hostgroup
    try:
        hostgroup.delete()
    except HTTPError:
        logger.exception('Exception while deleting class scope hostgroup entity in teardown')
