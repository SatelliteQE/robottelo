"""Tests for Red Hat Access Insights Client rpm

:Requirement: Rhai Client

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RHCloud-Insights

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker.broker import VMBroker

from robottelo.constants import DISTRO_RHEL7
from robottelo.hosts import ContentHost


@pytest.mark.skip_if_open('BZ:1892405')
def test_positive_connection_option(module_org, activation_key):
    """Verify that '--test-connection' option for insights-client
    client rpm tests the connection with the satellite server connection
    with satellite server

    :id: 167758c9-cbfa-4a81-9a11-27f88aaf9118

    :expectedresults: 'insights-client --test-connection' should
        return zero on a successfully registered machine to RHAI service
    """
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as vm:
        vm.configure_rhai_client(activation_key.name, module_org.label, DISTRO_RHEL7)
        test_connection = vm.run('insights-client --test-connection')
        assert test_connection.status == 0
