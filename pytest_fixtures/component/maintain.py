# Satellite-maintain fixtures
import pytest
from broker import VMBroker

from robottelo.config import settings
from robottelo.hosts import Satellite


@pytest.fixture(scope='module')
def sat_maintain(satellite_factory):
    if settings.remotedb.server:
        yield Satellite(settings.remotedb.server)
    else:
        sat = satellite_factory()
        yield sat
        VMBroker(hosts=[sat]).checkin()
