"""Fixtures specific to or relating to pytest's xdist plugin"""
import pytest

from robottelo.config import settings


@pytest.fixture(scope="session", autouse=True)
def align_xdist_satellites(worker_id):
    """Set a different Satellite per worker when available in robottelo's config"""
    settings.configure()
    settings.server.hostname = settings.server.get_hostname(worker_id)
    settings._configure_entities()
    settings._configure_airgun()
