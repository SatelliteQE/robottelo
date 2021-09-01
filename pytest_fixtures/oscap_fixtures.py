from pathlib import PurePath

import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.cli.factory import make_scapcontent
from robottelo.config import robottelo_tmp_dir
from robottelo.config import settings
from robottelo.constants import OSCAP_PROFILE
from robottelo.helpers import file_downloader


@pytest.fixture(scope="session")
def tailoring_file_path():
    """Return Tailoring file path."""
    local = file_downloader(file_url=settings.oscap.tailoring_path)[0]
    satellite = file_downloader(
        file_url=settings.oscap.tailoring_path, hostname=settings.server.hostname
    )[0]
    return {'local': local, 'satellite': satellite}


@pytest.fixture(scope="session")
def oscap_content_path(default_sat):
    """Download scap content from satellite and return local path of it."""
    local_file = robottelo_tmp_dir.joinpath(PurePath(settings.oscap.content_path).name)
    default_sat.put(remote_path=settings.oscap.content_path, local_path=local_file)
    return local_file


@pytest.fixture(scope="module")
def scap_content(import_ansible_roles, import_puppet_classes):
    title = f"rhel-content-{gen_string('alpha')}"
    scap_info = make_scapcontent({'title': title, 'scap-file': f'{settings.oscap.content_path}'})
    scap_id = scap_info['id']
    scap_info = entities.ScapContents(id=scap_id).read()

    scap_profile_id = [
        profile['id']
        for profile in scap_info.scap_content_profiles
        if OSCAP_PROFILE['security7'] in profile['title']
    ][0]
    return {
        "title": title,
        "scap_id": scap_id,
        "scap_profile_id": scap_profile_id,
    }


@pytest.fixture(scope="module")
def tailoring_file(module_org, module_location, tailoring_file_path):
    """Create Tailoring file."""
    tailoring_file_name = f"tailoring-file-{gen_string('alpha')}"
    tf_info = entities.TailoringFile(
        name=f"{tailoring_file_name}",
        scap_file=f"{tailoring_file_path['local']}",
        organization=[module_org],
        location=[module_location],
    ).create()
    return {
        "name": tailoring_file_name,
        "tailoring_file_id": tf_info.id,
        "tailoring_file_profile_id": tf_info.tailoring_file_profiles[0]['id'],
    }
