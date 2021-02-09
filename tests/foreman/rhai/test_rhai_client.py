"""Tests for Insights client rpm

:Requirement: Rhai Client

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RHCloud-Insights

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.constants import DISTRO_RHEL7


@pytest.mark.skip_if_open('BZ:1892405')
@pytest.mark.run_in_one_thread
def test_positive_connection_option(rhel7_contenthost, module_org, activation_key):
    """Verify that 'insights-client --test-connection' successfully tests the proxy connection via
    the Satellite.

    :id: 167758c9-cbfa-4a81-9a11-27f88aaf9118

    :expectedresults: 'insights-client --test-connection' should return 0.
    """
    rhel7_contenthost.configure_rhai_client(activation_key.name, module_org.label, DISTRO_RHEL7)
    result = rhel7_contenthost.execute('insights-client --test-connection')
    assert result.status == 0, (
        'insights-client --test-connection failed.\n'
        f'status: {result.status}\n'
        f'stdout: {result.stdout}\n'
        f'stderr: {result.stderr}'
    )
