"""Tests for Insights client rpm

:Requirement: Rhai Client

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RHCloud-Insights

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import DISTRO_RHEL8


@pytest.mark.tier4
@pytest.mark.run_in_one_thread
def test_positive_connection_option(rhel7_contenthost, module_org, activation_key, default_sat):
    """Verify that 'insights-client --test-connection' successfully tests the proxy connection via
    the Satellite.

    :id: 167758c9-cbfa-4a81-9a11-27f88aaf9118

    :expectedresults: 'insights-client --test-connection' should return 0.
    """
    rhel7_contenthost.configure_rhai_client(
        default_sat, activation_key.name, module_org.label, DISTRO_RHEL7
    )
    result = rhel7_contenthost.execute('insights-client --test-connection')
    assert result.status == 0, (
        'insights-client --test-connection failed.\n'
        f'status: {result.status}\n'
        f'stdout: {result.stdout}\n'
        f'stderr: {result.stderr}'
    )


@pytest.mark.tier4
@pytest.mark.run_in_one_thread
def test_positive_connection_option_non_rhel7(
    rhel8_contenthost, module_org, activation_key, default_sat
):
    """Verify that 'insights-client --test-connection' successfully tests the proxy connection via
    the Satellite.

    :id: 0051b2af-eae1-488e-9ca6-768eb81efb03

    :Steps:

        0. Create a RHEL6 or RHEL8 VM and register to insights within org having manifest.

        1. Run 'insights-client --test-connection'.

    :expectedresults: 'insights-client --test-connection' should return 0.
    """
    rhel8_contenthost.configure_rhai_client(
        default_sat, activation_key.name, module_org.label, DISTRO_RHEL8
    )
    result = rhel8_contenthost.execute('insights-client --test-connection')
    assert result.status == 0, (
        'insights-client --test-connection failed.\n'
        f'status: {result.status}\n'
        f'stdout: {result.stdout}\n'
        f'stderr: {result.stderr}'
    )
