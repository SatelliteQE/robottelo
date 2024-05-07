"""Test class foreman ansible modules

:Requirement: Other

:CaseAutomation: Automated

:CaseImportance: High

:CaseComponent: AnsibleCollection

:Team: Platform

"""

from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.constants import (
    FAM_MODULE_PATH,
    FAM_ROOT_DIR,
    FAM_TEST_PLAYBOOKS,
    FOREMAN_ANSIBLE_MODULES,
    RH_SAT_ROLES,
)


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


@pytest.fixture(scope='module')
def setup_fam(module_target_sat, module_sca_manifest):
    # Execute AAP WF for FAM setup
    Broker().execute(workflow='fam-test-setup', source_vm=module_target_sat.name)

    # Setup provisioning resources and copy config files to the Satellite
    module_target_sat.configure_libvirt_cr()
    module_target_sat.put(
        settings.fam.server.to_yaml(),
        f'{FAM_ROOT_DIR}/tests/test_playbooks/vars/server.yml',
        temp_file=True,
    )
    module_target_sat.put(
        settings.fam.compute_profile.to_yaml(),
        f'{FAM_ROOT_DIR}/tests/test_playbooks/vars/compute_profile.yml',
        temp_file=True,
    )

    # Edit Makefile to not try to rebuild the collection when tests run
    module_target_sat.execute(f"sed -i '/^live/ s/$(MANIFEST)//' {FAM_ROOT_DIR}/Makefile")

    # Upload manifest to test playbooks directory
    module_target_sat.put(str(module_sca_manifest.path), str(module_sca_manifest.name))
    module_target_sat.execute(
        f'mv {module_sca_manifest.name} {FAM_ROOT_DIR}/tests/test_playbooks/data'
    )
    config_file = f'{FAM_ROOT_DIR}/tests/test_playbooks/vars/server.yml'
    module_target_sat.execute(
        f'''sed -i 's|subscription_manifest_path:.*|subscription_manifest_path: "data/{module_sca_manifest.name}"|g' {config_file}'''
    )


@pytest.mark.pit_server
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


@pytest.mark.e2e
@pytest.mark.pit_server
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


@pytest.mark.e2e
@pytest.mark.parametrize('ansible_module', FAM_TEST_PLAYBOOKS)
def test_positive_run_modules_and_roles(module_target_sat, setup_fam, ansible_module):
    """Run all FAM modules and roles on the Satellite

    :id: b595756f-627c-44ea-b738-aa17ff5b1d39

    :expectedresults: All modules and roles run successfully
    """
    # Execute test_playbook
    result = module_target_sat.execute(
        f'export NO_COLOR=True && . ~/localenv/bin/activate && cd {FAM_ROOT_DIR} && make livetest_{ansible_module}'
    )
    assert 'PASSED' in result.stdout
    assert result.status == 0
