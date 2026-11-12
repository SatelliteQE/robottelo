from contextlib import ExitStack

import pytest

from robottelo.cli.ansible import Ansible
from robottelo.utils.ansible import AnsibleSyncTasks, cleanup_ansible_roles


@pytest.fixture(scope="session")
def import_ansible_roles(default_smart_proxy):
    """Import ansible roles to default_smart_proxy for tests"""
    Ansible.roles_import({'proxy-id': default_smart_proxy.id})
    Ansible.variables_import({'proxy-id': default_smart_proxy.id})


@pytest.fixture
def synced_ansible_roles():
    """Import and remove ansible roles"""
    with ExitStack() as cleanup:

        def _sync(satellite, role_names):
            role_names = list(dict.fromkeys(role_names))
            existing = {role['name'] for role in satellite.cli.Ansible.roles_list()}
            missing = [name for name in role_names if name not in existing]
            if missing:
                tasks = AnsibleSyncTasks(satellite, missing, satellite.nailgun_smart_proxy.id)
                cleanup.callback(cleanup_ansible_roles, satellite, missing, tasks)
                satellite.cli.Ansible.roles_sync(
                    {'role-names': missing, 'proxy-id': satellite.nailgun_smart_proxy.id},
                    synchronous=True,
                    task_ids=tasks,
                )
                imported = {role['name'] for role in satellite.cli.Ansible.roles_list()}
                unavailable = [name for name in missing if name not in imported]
                assert not unavailable, f'Ansible roles were not imported: {unavailable}'
            return role_names

        yield _sync
