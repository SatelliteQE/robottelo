"""Test class for Reports CLI.

:Requirement: Report

:CaseAutomation: Automated

:CaseComponent: Puppet

:Team: Rocket

:CaseImportance: Critical

"""

import random

import pytest
from wait_for import wait_for

from robottelo.exceptions import CLIReturnCodeError


@pytest.fixture(scope='module')
def run_puppet_agent(session_puppet_enabled_sat):
    """Retrieves the client configuration from the puppet master and
    applies it to the local host. This is required to make sure
    that we have reports available.
    """
    session_puppet_enabled_sat.execute('puppet agent -t')


@pytest.mark.e2e
@pytest.mark.tier1
def test_positive_CRD_satellite(run_puppet_agent, session_puppet_enabled_sat):
    """Test puppet-agent creates a report for satellite when its run, read and delete by its ID

    :id: 32646d4b-7101-421a-85e0-777d3c6b71ec

    :expectedresults: Puppet reports are generated, readable, and deleteable
    """
    result = session_puppet_enabled_sat.cli.ConfigReport.list()
    assert len(result) > 0
    # Grab a random report
    report = random.choice(result)
    result = session_puppet_enabled_sat.cli.ConfigReport.info({'id': report['id']})
    assert report['id'] == result['id']
    # Delete ConfigReport by its ID
    session_puppet_enabled_sat.cli.ConfigReport.delete({'id': report['id']})
    with pytest.raises(CLIReturnCodeError):
        session_puppet_enabled_sat.cli.ConfigReport.info({'id': report['id']})


@pytest.mark.e2e
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_install_configure_host(
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
    for client, puppet_proxy in zip(content_hosts, puppet_infra_host, strict=True):
        client.configure_puppet(proxy_hostname=puppet_proxy.hostname)
        report = session_puppet_enabled_sat.cli.ConfigReport.list(
            {'search': f'host~{client.hostname}'}
        )
        assert len(report)
        assert report[0]['origin'] == 'Puppet'
        facts = session_puppet_enabled_sat.cli.Fact.list({'search': f'host~{client.hostname}'})
        assert len(facts)
        assert [f for f in facts if f['fact'] == 'puppetmaster_fqdn'][0][
            'value'
        ] == puppet_proxy.hostname
        session_puppet_enabled_sat.cli.ConfigReport.delete({'id': report[0]['id']})
        with pytest.raises(CLIReturnCodeError):
            session_puppet_enabled_sat.cli.ConfigReport.info({'id': report[0]['id']})


@pytest.mark.e2e
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_run_puppet_agent_generate_report_when_no_message(
    session_puppet_enabled_sat, rhel_contenthost
):
    """Verify that puppet-agent can be installed from the sat-client repo
    and configured to report back to the Satellite, and contains the origin

    :id: 07777fbb-4f2e-4fab-ba5a-2b698f9b9f39

    :setup:
        1. Satellite and Capsule with enabled puppet plugin.
        2. Blank RHEL content host

    :steps:
        1. Configure puppet on the content host. This creates sat-client repository,
           installs puppet-agent, configures it, runs it to create the puppet cert,
           signs in on the Satellite side and reruns it.
        2. Assert that Config report created in the Satellite for the content host,
           and has Puppet origin
        3. Assert that Facts were reported for the content host.

    :expectedresults:
        1. Configuration passes without errors.
        2. Config report is created and contains Puppet origin
        3. Facts are acquired.

    :customerscenario: true

    :BZ: 2192939, 2257327, 2257314
    :parametrized: yes
    """
    sat = session_puppet_enabled_sat
    client = rhel_contenthost
    client.configure_puppet(proxy_hostname=sat.hostname, run_puppet_agent=False)
    # Run either 'puppet agent --detailed-exitcodes' or 'systemctl restart puppet'
    # to generate Puppet config report for host without any messages
    assert client.execute('/opt/puppetlabs/bin/puppet agent --detailed-exitcodes').status == 0
    wait_for(
        lambda: sat.cli.ConfigReport.list({'search': f'host~{client.hostname}'}) != [],
        timeout=300,
        delay=30,
    )
    report = sat.cli.ConfigReport.list({'search': f'host~{client.hostname}'})
    assert len(report)
    assert report[0]['origin'] == 'Puppet'
    facts = sat.cli.Fact.list({'search': f'host~{client.hostname}'})
    assert len(facts)
    assert [f for f in facts if f['fact'] == 'puppetmaster_fqdn'][0]['value'] == sat.hostname
    sat.cli.ConfigReport.delete({'id': report[0]['id']})
    with pytest.raises(CLIReturnCodeError):
        sat.cli.ConfigReport.info({'id': report[0]['id']})
