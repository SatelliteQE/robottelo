import os

import pytest

from robottelo import ssh
from robottelo.helpers import file_downloader
from robottelo.test import settings


@pytest.fixture(scope="session")
def tailoring_file_path():
    """ Return Tailoring file path."""
    local = file_downloader(file_url=settings.oscap.tailoring_path)[0]
    satellite = file_downloader(
        file_url=settings.oscap.tailoring_path, hostname=settings.server.hostname
    )[0]
    return {'local': local, 'satellite': satellite}


@pytest.fixture(scope="session")
def oscap_content_path():
    """ Download scap content from satellite and return local path of it."""
    _, file_name = os.path.split(settings.oscap.content_path)
    local_file = f"/tmp/{file_name}"
    ssh.download_file(settings.oscap.content_path, local_file)
    return local_file
