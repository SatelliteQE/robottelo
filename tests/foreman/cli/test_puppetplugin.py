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


@pytest.mark.skip_if_open("BZ:2034552")
def test_positive_enable_disable_logic(destructive_sat, destructive_caps):
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
        7. Disable puppet on Sastellite and check it succeeded.

    :expectedresults:
        1. Puppet is missing on disabled setup.
        2. Puppet can't be enabled on Capsule when disabled on Satellite.
        3. Puppet can be enabled with service running on Satellite, CLI commands were added.
        4. Puppet can be enabled with service running on Capsule when enabled on Satellite.
        5. Puppet can't be disabled on Satellite when enabled on Capsule.
        6. Puppet can be disabled on Capsule
        7. Puppet can be disabled on Satellite when disabled on Capsule.
    """
    # Check that puppet is disabled by default on both.
    result = destructive_sat.execute('rpm -q puppetserver')
    assert result.status == 1
    assert 'package puppetserver is not installed' in result.stdout

    for cmd in puppet_cli_commands:
        result = destructive_sat.execute(f'hammer {cmd} --help')
        assert result.status == 64
        assert f"{err_msg} '{cmd.split()[-1]}'." in str(result.stderr)

    result = destructive_caps.execute('rpm -q puppetserver')
    assert result.status == 1
    assert 'package puppetserver is not installed' in result.stdout

    # Try to enable puppet on Capsule and check it failed.
    result = destructive_caps.execute(enable_capsule_cmd.get_command(), timeout=900000)
    assert result.status == 6  # == 6
    assert 'failed to load one or more features (Puppet)' in result.stdout

    # Enable puppet on Satellite and check it succeeded.
    destructive_sat.register_to_dogfood()
    result = destructive_sat.execute(enable_satellite_cmd.get_command(), timeout=900000)
    assert result.status == 0
    assert 'Success!' in result.stdout

    result = destructive_sat.execute('rpm -q puppetserver')
    assert result.status == 0
    result = destructive_sat.execute('systemctl status puppetserver')
    assert 'active (running)' in result.stdout

    # TODO: an issue identified, DEVs investigating
    # for cmd in puppet_commands:
    #     result = destructive_sat.execute(f'hammer {cmd} --help')
    #     assert result.status == 0

    # Enable puppet on Capsule and check it succeeded.
    result = destructive_caps.execute(enable_capsule_cmd.get_command(), timeout=900000)
    assert result.status == 0
    assert 'Success!' in result.stdout

    result = destructive_caps.execute('rpm -q puppetserver')
    assert result.status == 0
    result = destructive_caps.execute('systemctl status puppetserver')
    assert 'active (running)' in result.stdout

    # Try to disable puppet on Satellite and check it failed.
    result = destructive_sat.execute('foreman-maintain plugin purge-puppet')
    assert result.status == 1
    assert f'The following proxies have Puppet feature: {destructive_caps.hostname}.'

    # Disable puppet on Capsule and check it succeeded.
    result = destructive_caps.execute('foreman-maintain plugin purge-puppet')
    assert result.status == 0

    result = destructive_caps.execute('rpm -q puppetserver')
    assert result.status == 1
    assert 'package puppetserver is not installed' in result.stdout

    # Disable puppet on Satellite and check it succeeded.
    result = destructive_caps.execute('foreman-maintain plugin purge-puppet')
    assert result.status == 0
    result = destructive_sat.execute('rpm -q puppetserver')
    assert result.status == 1
    assert 'package puppetserver is not installed' in result.stdout

    for cmd in puppet_cli_commands:
        result = destructive_sat.execute(f'hammer {cmd} --help')
        assert result.status == 64
        assert f"{err_msg} '{cmd.split()[-1]}'." in str(result.stderr)
