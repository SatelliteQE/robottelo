"""Test class for Reports CLI.

:Requirement: Report

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Puppet

:Team: Rocket

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import random

import pytest

from robottelo.cli.base import CLIReturnCodeError

pytestmark = pytest.mark.e2e


@pytest.fixture(scope='module')
def run_puppet_agent(session_puppet_enabled_sat):
    """Retrieves the client configuration from the puppet master and
    applies it to the local host. This is required to make sure
    that we have reports available.
    """
    session_puppet_enabled_sat.execute('puppet agent -t')


@pytest.mark.tier1
def test_positive_info(run_puppet_agent, session_puppet_enabled_sat):
    """Test Info for Puppet report

    :id: 32646d4b-7101-421a-85e0-777d3c6b71ec

    :expectedresults: Puppet Report Info is displayed
    """
    result = session_puppet_enabled_sat.cli.ConfigReport.list()
    assert len(result) > 0
    # Grab a random report
    report = random.choice(result)
    result = session_puppet_enabled_sat.cli.ConfigReport.info({'id': report['id']})
    assert report['id'] == result['id']


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_by_id(run_puppet_agent, session_puppet_enabled_sat):
    """Check if Puppet Report can be deleted by its ID

    :id: bf918ec9-e2d4-45d0-b913-ab939b5d5e6a

    :expectedresults: Puppet Report is deleted
    """
    result = session_puppet_enabled_sat.cli.ConfigReport.list()
    assert len(result) > 0
    # Grab a random report
    report = random.choice(result)
    session_puppet_enabled_sat.cli.ConfigReport.delete({'id': report['id']})
    with pytest.raises(CLIReturnCodeError):
        session_puppet_enabled_sat.cli.ConfigReport.info({'id': report['id']})


@pytest.mark.e2e
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_install_configure(
    session_puppet_enabled_sat, session_puppet_enabled_capsule, content_hosts
):
    """Test that puppet-agent can be installed from the sat-client repo
    and configured to report back to the Satellite.

    :id: 07777fbb-4f2e-4fab-ba5a-2b698f9b9f38

    :setup:
        1. Satellite and Capsule with enabled puppet plugin.
        2. Blank RHEL content hosts.

    :steps:
        1. Configure puppet on the content host. This creates sat-client repository,
           installs puppet-agent, configures it, runs it to create the puppet cert,
           signs in on the Satellite side and reruns it.
        2. Assert that Config report was created at the Satellite for the content host.
        3. Assert that Facts were reported for the content host.

    :expectedresults:
        1. Configuration passes without errors.
        2. Config report is created.
        3. Facts are acquired.

    :customerscenario: true

    :BZ: 2126891, 2026239
    """
    puppet_infra_host = [session_puppet_enabled_sat, session_puppet_enabled_capsule]
    for client, puppet_proxy in zip(content_hosts, puppet_infra_host):
        client.configure_puppet(proxy_hostname=puppet_proxy.hostname)
        report = session_puppet_enabled_sat.cli.ConfigReport.list(
            {'search': f'host~{client.hostname},origin=Puppet'}
        )
        assert len(report)
        facts = session_puppet_enabled_sat.cli.Fact.list({'search': f'host~{client.hostname}'})
        assert len(facts)
        session_puppet_enabled_sat.cli.ConfigReport.delete({'id': report[0]['id']})
        with pytest.raises(CLIReturnCodeError):
            session_puppet_enabled_sat.cli.ConfigReport.info({'id': report[0]['id']})
