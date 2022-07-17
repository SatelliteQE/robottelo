"""Test class for puppet plugin CLI

:Requirement: Puppet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from pytest_fixtures.component.puppet import enable_capsule_cmd
from pytest_fixtures.component.puppet import enable_satellite_cmd
from robottelo.hosts import Satellite

puppet_cli_commands = [
    'puppet-environment',
    'puppet-class',
    'config-group',
    'host puppet-classes',
    'host sc-params',
    'hostgroup puppet-classes',
    'hostgroup sc-params',
]

err_msg = 'Error: No such sub-command'

pytestmark = pytest.mark.destructive


def assert_puppet_status(server, expected):
    result = server.get_features()
    assert ('puppet' in result) is expected
    assert ('puppetca' in result) is expected

    result = server.execute('rpm -q puppetserver')
    assert (result.status == 0) is expected
    assert ('package puppetserver is not installed' in result.stdout) is not expected

    result = server.execute('systemctl status puppetserver')
    assert ('active (running)' in result.stdout) is expected

    if type(server) is Satellite:
        for cmd in puppet_cli_commands:
            result = server.execute(f'hammer {cmd} --help')
            assert (result.status == 0) is expected
            assert (f"{err_msg} '{cmd.split()[-1]}'." in str(result.stderr)) is not expected


def test_positive_enable_disable_logic(target_sat, capsule_configured):
    """Test puppet enable/disable logic on Satellite and Capsule

    :id: a1909c3e-6d41-4235-97b1-4e8b64ee1a9e

    :setup:
        1. Satellite with registered external Capsule, both with disabled puppet.

    :steps:
        1. Check that puppet is disabled by default on both.
        2. Try to enable puppet on Capsule and check it failed.
        3. Enable puppet on Satellite and check it succeeded.
        4. Enable puppet on Capsule and check it succeeded.
        5. Try to disable puppet on Satellite and check it failed.
        6. Disable puppet on Capsule and check it succeeded.
        7. Disable puppet on Satellite and check it succeeded.

    :expectedresults:
        1. Puppet is missing on disabled setup.
        2. Puppet can't be enabled on Capsule when disabled on Satellite.
        3. Puppet can be enabled with service running on Satellite, CLI commands were added.
        4. Puppet can be enabled with service running on Capsule when enabled on Satellite.
        5. Puppet can't be disabled on Satellite when enabled on Capsule.
        6. Puppet can be disabled on Capsule
        7. Puppet can be disabled on Satellite when disabled on Capsule.

    :BZ: 2032928, 2034552, 2033336, 2039696
    """
    # Check that puppet is disabled by default on both.
    assert_puppet_status(target_sat, expected=False)
    assert_puppet_status(capsule_configured, expected=False)

    # Try to enable puppet on Capsule and check it failed.
    result = capsule_configured.execute(enable_capsule_cmd.get_command(), timeout='20m')
    assert result.status == 6
    assert 'failed to load one or more features (Puppet)' in result.stdout

    # Enable puppet on Satellite and check it succeeded.
    target_sat.download_repofile()
    result = target_sat.execute(enable_satellite_cmd.get_command(), timeout='20m')
    assert result.status == 0
    assert 'Success!' in result.stdout

    # workaround for BZ#2039696
    target_sat.execute('hammer -r')

    assert_puppet_status(target_sat, expected=True)

    # Enable puppet on Capsule and check it succeeded.
    result = capsule_configured.execute(enable_capsule_cmd.get_command(), timeout='20m')
    assert result.status == 0
    assert 'Success!' in result.stdout
    assert_puppet_status(capsule_configured, expected=True)

    # Try to disable puppet on Satellite and check it failed.
    result = target_sat.execute('satellite-maintain plugin purge-puppet')
    assert result.status == 1
    assert (
        f'The following proxies have Puppet feature: {capsule_configured.hostname}.'
        in result.stdout
    )

    # Disable puppet on Capsule and check it succeeded.
    result = capsule_configured.execute(
        'satellite-maintain plugin purge-puppet --remove-all-data', timeout='20m'
    )
    assert result.status == 0
    assert_puppet_status(capsule_configured, expected=False)

    # Disable puppet on Satellite and check it succeeded.
    result = target_sat.execute(
        'satellite-maintain plugin purge-puppet --remove-all-data', timeout='20m'
    )
    assert result.status == 0
    assert_puppet_status(target_sat, expected=False)


@pytest.mark.rhel_ver_match('[^9]')
def test_positive_install_configure(session_puppet_enabled_sat, rhel_contenthost):
    """Test that puppet-agent can be installed from the sat-client repo
    and configured to report back to the Satellite.

    :id: 07777fbb-4f2e-4fab-ba5a-2b698f9b9f38

    :setup:
        1. Satellite with enabled puppet plugin.
        2. Blank RHEL content host.

    :steps:
        1. Configure puppet on the content host. This creates sat-client repository,
           installs puppet-agent, configures it, runs it to create the puppet cert,
           signs in on the Satellite side and reruns it.
        2. Assert that Config report was created at the Satellite for the content host.

    :expectedresults:
        1. Configuration passes without errors.
        2. Config report is created.
    """
    rhel_contenthost.configure_puppet(proxy_hostname=session_puppet_enabled_sat.hostname)
    result = session_puppet_enabled_sat.cli.ConfigReport.list(
        {'search': f'host={rhel_contenthost.hostname},origin=Puppet'}
    )
    assert len(result)
