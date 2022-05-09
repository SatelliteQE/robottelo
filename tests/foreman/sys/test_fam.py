"""Test class foreman ansible modules

:Requirement: Other

:CaseAutomation: Automated

:CaseLevel: System

:TestType: Functional

:CaseImportance: High

:CaseComponent: AnsibleCollection

:Assignee: gsulliva

:Upstream: No
"""
import pytest

from robottelo.constants import FAM_MODULE_PATH
from robottelo.constants import FOREMAN_ANSIBLE_MODULES
from robottelo.constants import RH_SAT_ROLES


@pytest.fixture
def sync_roles(target_sat):
    """Sync all redhat.satellite roles and delete when finished
    Returns: A dict of the sync response and role names
    """
    roles = [f'redhat.satellite.{role}' for role in RH_SAT_ROLES]
    proxy_list = target_sat.cli.Proxy.list({'search': f'name={target_sat.hostname}'})
    proxy_id = proxy_list[0].get('id')
    sync = target_sat.cli.Ansible.roles_sync({'role-names': roles, 'proxy-id': proxy_id})
    yield {'task': sync, 'roles': roles}
    roles_list = target_sat.cli.Ansible.roles_list()
    for role in roles_list:
        role_id = role.get('id')
        target_sat.cli.Ansible.roles_delete({'id': role_id})


@pytest.mark.run_in_one_thread
def test_positive_ansible_modules_installation(target_sat):
    """Foreman ansible modules installation test

    :id: 553a927e-2665-4227-8542-0258d7b1ccc4

    :expectedresults: ansible-collection-redhat-satellite package is
        available and supported modules are contained

    """
    # list installed modules
    result = target_sat.execute(f'ls {FAM_MODULE_PATH} | grep .py$ | sed "s/.[^.]*$//"')
    assert result.status == 0
    installed_modules = result.stdout.split('\n')
    installed_modules.remove('')
    # see help for installed modules
    for module_name in installed_modules:
        result = target_sat.execute(f'ansible-doc redhat.satellite.{module_name} -s')
        assert result.status == 0
        doc_name = result.stdout.split('\n')[1].lstrip()[:-1]
        assert doc_name == module_name
    # check installed modules against the expected list
    assert FOREMAN_ANSIBLE_MODULES.sort() == installed_modules.sort()


@pytest.mark.tier1
def test_positive_import_run_roles(sync_roles, target_sat):
    """Import a FAM role and run the role on the Satellite

    :id: d3379fd3-b847-43ce-a51f-c02170e7b267

    :expectedresults: fam roles import and run successfully

    """
    roles = sync_roles.get('roles')
    target_sat.cli.Host.ansible_roles_assign({'ansible-roles': roles, 'name': target_sat.hostname})
    play = target_sat.cli.Host.ansible_roles_play({'name': target_sat.hostname})
    assert 'Ansible roles are being played' in play[0]['message']
