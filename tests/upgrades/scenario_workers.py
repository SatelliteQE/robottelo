import json
import os

import pytest
from automation_tools.satellite6.hammer import set_hammer_config
from fabric.api import env

import robottelo
from robottelo.config import settings


_json_file = 'upgrade_workers.json'


def save_worker_id(test_name, worker_id):
    data = {}
    if os.path.exists(_json_file):
        with open(_json_file) as rjson:
            data = json.load(rjson)
    with open(_json_file, 'w') as wjson:
        # Removing the parameter name from test name before save
        test_name = test_name.split('[')[0] if '[' in test_name else test_name
        data.update({test_name: worker_id})
        wjson.seek(0)
        json.dump(data, wjson)


def get_worker_id(test_name):
    with open(_json_file) as rjson:
        data = json.load(rjson)
        return data.get(test_name)


@pytest.fixture(autouse=True)
def save_pretest_worker_id(request, worker_id):
    """Saves the worker id of pre_upgrade test in json"""
    if request.node.get_closest_marker('pre_upgrade'):
        save_worker_id(request.node.name, worker_id)


@pytest.fixture(autouse=True)
def set_posttest_worker_id(request):
    """Retrieves worker_id of pre_upgrade and sets the same to run post_upgrade"""
    post_upgrade = request.node.get_closest_marker('post_upgrade')
    if post_upgrade:
        depend_test = post_upgrade.kwargs.get('depend_on')
        if depend_test:
            pre_test_name = depend_test.__name__
            # settings.configure()
            cache_proxy = robottelo.config.settings_proxy._cache
            # Read the worker id of pre test name
            worker_int = int(get_worker_id(pre_test_name).replace('gw', ''))
            cache_proxy['server.hostname'] = settings.server.hostnames[worker_int]
            settings.configure_nailgun()
            settings.configure_airgun()
            env.host_string = settings.server.hostname
            env.user = 'root'
            set_hammer_config()
