import json
from pathlib import Path

import pytest
from automation_tools.satellite6.hammer import set_hammer_config
from fabric.api import env

from robottelo.config import configure_airgun
from robottelo.config import configure_nailgun
from robottelo.config import settings


_json_file = 'upgrade_workers.json'
json_file = Path(_json_file)


def save_worker_hostname(test_name, default_sat):
    data = {}
    if json_file.exists():
        data = json.loads(json_file.read_text())
    # Removing the parameter name from test name before save
    test_name = test_name.split('[')[0] if '[' in test_name else test_name
    data.update({test_name: default_sat.hostname})
    json_file.write_text(json.dumps(data))


@pytest.fixture(scope='session')
def shared_workers():
    if json_file.exists():
        return json.loads(json_file.read_text())


def get_worker_hostname_from_testname(test_name, shared_workers):
    return shared_workers.get(test_name)


@pytest.fixture(autouse=True)
def save_pre_upgrade_worker_hostname(request, default_sat):
    """Saves the worker id of pre_upgrade test in json"""
    if request.node.get_closest_marker('pre_upgrade'):
        save_worker_hostname(request.node.name, default_sat)


@pytest.fixture(autouse=True)
def set_post_upgrade_hostname(request, shared_workers):
    """Retrieves worker hostname of pre_upgrade and sets the same to run post_upgrade

    The limitation of this implementation is that the XDIST_BEHAVIOR won't be observed,
    and tests running under xdist will not be isolated.

    This is overriding the session scoped align_to_satellite fixture
    """
    post_upgrade = request.node.get_closest_marker('post_upgrade')
    if post_upgrade:
        depend_test = post_upgrade.kwargs.get('depend_on')
        if depend_test:
            pre_test_name = depend_test.__name__
            pre_hostname = get_worker_hostname_from_testname(pre_test_name, shared_workers)
            if (pre_hostname is None) or (pre_hostname not in settings.server.hostnames):
                pytest.skip(
                    'Skipping the post_upgrade test as the pre_upgrade hostname is not found!'
                )
            # Read the worker id of pre test name
            settings.server.hostname = env.host_string = pre_hostname
            env.user = 'root'
            configure_nailgun()
            configure_airgun()
            set_hammer_config()
