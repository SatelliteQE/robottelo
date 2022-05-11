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


@pytest.mark.destructive
@pytest.mark.run_in_one_thread
def test_positive_ansible_modules_installation(default_sat):
    """Foreman ansible modules installation test

    :id: 553a927e-2665-4227-8542-0258d7b1ccc4

    :expectedresults: ansible-collection-redhat-satellite package is
        available and supported modules are contained

    """
    result = default_sat.execute(
        'yum install -y ansible-collection-redhat-satellite --disableplugin=foreman-protector'
    )
    assert result.status == 0
    # list installed modules
    result = default_sat.execute(f'ls {FAM_MODULE_PATH} | grep .py$ | sed "s/.[^.]*$//"')
    assert result.status == 0
    installed_modules = result.stdout.split('\n')
    installed_modules.remove('')
    # see help for installed modules
    for module_name in installed_modules:
        result = default_sat.execute(f'ansible-doc redhat.satellite.{module_name} -s')
        assert result.status == 0
        doc_name = result.stdout.split('\n')[1].lstrip()[:-1]
        assert doc_name == module_name
    # check installed modules against the expected list
    assert FOREMAN_ANSIBLE_MODULES.sort() == installed_modules.sort()
