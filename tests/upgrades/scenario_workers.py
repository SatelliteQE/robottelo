import json
from pathlib import Path

import pytest
from automation_tools.satellite6.hammer import set_hammer_config
from fabric.api import env

import robottelo
from robottelo.config import settings


_json_file = 'upgrade_workers.json'


def save_worker_hostname(test_name):
    data = {}
    json_file = Path(_json_file)
    if json_file.exists():
        data = json.loads(json_file.read_text())
    # Removing the parameter name from test name before save
    test_name = test_name.split('[')[0] if '[' in test_name else test_name
    data.update({test_name: settings.server.hostname})
    json_file.write_text(json.dumps(data))


def get_worker_hostname(test_name):
    with open(_json_file) as rjson:
        data = json.load(rjson)
        return data.get(test_name)


@pytest.fixture(autouse=True)
def save_pre_upgrade_worker_hostname(request):
    """Saves the worker id of pre_upgrade test in json"""
    if request.node.get_closest_marker('pre_upgrade'):
        save_worker_hostname(request.node.name)


@pytest.fixture(autouse=True)
def set_post_upgrade_hostname(request):
    """Retrieves worker hostname of pre_upgrade and sets the same to run post_upgrade

    The limitation of this implementation is that the XDIST_BEHAVIOR won't be observed,
    and tests running under xdist will not be isolated.
    """
    post_upgrade = request.node.get_closest_marker('post_upgrade')
    if post_upgrade:
        depend_test = post_upgrade.kwargs.get('depend_on')
        if depend_test:
            pre_test_name = depend_test.__name__
            settings.configure()
            cache_proxy = robottelo.config.settings_proxy._cache
            pre_hostname = get_worker_hostname(pre_test_name)
            if (pre_hostname is None) or (pre_hostname not in settings.server.hostnames):
                pytest.skip(
                    'Skipping the post_upgrade test as the pre_upgrade hostname is not found!'
                )
            # Read the worker id of pre test name
            cache_proxy['server.hostname'] = env.host_string = pre_hostname
            env.user = 'root'
            settings.configure_nailgun()
            settings.configure_airgun()
            set_hammer_config()
