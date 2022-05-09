"""Test for bootstrap script (bootstrap.py)

:Requirement: Bootstrap Script

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Bootstrap

:Assignee: swadeley

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker.broker import VMBroker

from robottelo.hosts import ContentHost


@pytest.mark.tier1
def test_positive_register(
    module_org, module_location, module_lce, module_ak_cv_lce, module_published_cv, target_sat
):
    """System is registered

    :id: e34561fd-e0d6-4587-84eb-f86bd131aab1

    :Steps:

        1. Ensure system is not registered
        2. Register a system
        3. Ensure system is registered
        4. Register system once again


    :expectedresults: system is registered, host is created

    :CaseAutomation: Automated

    :CaseImportance: Critical
    """
    hg = target_sat.api.HostGroup(location=[module_location], organization=[module_org]).create()
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as vm:
        # assure system is not registered
        result = vm.execute('subscription-manager identity')
        # result will be 1 if not registered
        assert result.status == 1
        assert vm.execute(
            f'curl -o /root/bootstrap.py "http://{target_sat.hostname}/pub/bootstrap.py" '
        )
        assert vm.execute(
            f'python /root/bootstrap.py -s {target_sat.hostname} -o {module_org.name}'
            f' -L {module_location.name} -a {module_ak_cv_lce.name} --hostgroup={hg.name}'
            ' --skip puppet --skip foreman'
        )
        # assure system is registered
        result = vm.execute('subscription-manager identity')
        # result will be 0 if registered
        assert result.status == 0
        # register system once again
        assert vm.execute(
            f'python /root/bootstrap.py -s "{target_sat.hostname}" -o {module_org.name} '
            f'-L {module_location.name} -a {module_ak_cv_lce.name} --hostgroup={hg.name}'
            '--skip puppet --skip foreman '
        )
        # assure system is registered
        result = vm.execute('subscription-manager identity')
        # result will be 0 if registered
        assert result.status == 0
