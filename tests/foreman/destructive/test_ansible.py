"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Ansible

:Assignee: sbible

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

pytestmark = pytest.mark.destructive


def test_positive_persistent_ansible_cfg_change(target_sat):
    """Check if changes in ansible.cfg are persistent after running satellite-installer

    :id: c22fcd47-8627-4230-aa1f-7d4fc8517a0e

    :BZ: 1786358

    :customerscenario: true

    :Steps:
        1. Update value in ansible.cfg.
        2. Verify value is updated in the file.
        3. Run "satellite-installer".
        4. Verify the changes are persistent in the file.

    :expectedresults: Changes in ansible.cfg are persistent after running
        "satellite-installer".
    """
    ansible_cfg = '/etc/ansible/ansible.cfg'
    param = 'local_tmp = /tmp'
    command = f'''echo "{param}" >> {ansible_cfg}'''
    target_sat.execute(command)
    assert param in target_sat.execute(f'cat {ansible_cfg}').stdout.splitlines()
    target_sat.execute('satellite-installer')
    assert param in target_sat.execute(f'cat {ansible_cfg}').stdout.splitlines()
