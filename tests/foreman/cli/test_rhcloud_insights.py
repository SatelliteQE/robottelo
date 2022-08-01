"""CLI tests for Insights part of RH Cloud - Inventory plugin.

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Inventory

:Assignee: addubey

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker import Broker

from robottelo.hosts import ContentHost


@pytest.mark.tier4
@pytest.mark.parametrize('distro', ['rhel7', 'rhel8'])
def test_positive_connection_option(organization_ak_setup, rhcloud_sat_host, distro):
    """Verify that 'insights-client --test-connection' successfully tests the proxy connection via
    the Satellite.

    :id: 61a4a39e-b484-49f4-a6fd-46ffc7736e50

    :customerscenario: true

    :Steps:

        1. Create RHEL7 and RHEL8 VM and register to insights within org having manifest.

        2. Run 'insights-client --test-connection'.

    :expectedresults: 'insights-client --test-connection' should return 0.

    :BZ: 1976754

    :CaseImportance: Critical
    """
    org, activation_key = organization_ak_setup
    with Broker(nick=distro, host_classes={'host': ContentHost}) as vm:
        vm.configure_rhai_client(rhcloud_sat_host, activation_key.name, org.label, distro)
        result = vm.run('insights-client --test-connection')
        assert result.status == 0, (
            'insights-client --test-connection failed.\n'
            f'status: {result.status}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}'
        )
