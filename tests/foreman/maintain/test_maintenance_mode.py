"""Test class for satellite-maintain maintenance-mode functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ForemanMaintain

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
import yaml

from robottelo.config import robottelo_tmp_dir

pytestmark = pytest.mark.destructive


@pytest.mark.tier2
def test_positive_maintenance_mode(request, sat_maintain, setup_sync_plan):
    """Test satellite-maintain maintenance-mode subcommand

    :id: 51d76219-d3cc-43c0-9894-7bcb75c163c3

    :setup:
        1. Create a sync-plans which is enabled
        2. set ':manage_crond: true' in /etc/foreman-maintain/foreman_maintain.yml

    :steps:
        1. Verify that maintenance-mode is Off.
        2. Start maintenance-mode.
        3. Verify that active sync-plans got disabled or not.
        4. Verify that FOREMAN_MAINTAIN_TABLE is mentioned in nftables list.
        5. Verify that crond.service is stopped.
        6. Validate maintenance-mode status command's output.
        7. Validate maintenance-mode is-enabled command's output.
        8. Stop maintenance-mode.
        9. Verify that disabled sync-plans got re-enabled or not.
        10. Verify that FOREMAN_MAINTAIN_TABLE is not mentioned in nftables list.
        11. Verify that crond.service is running.
        12. Validate maintenance-mode status command's output.
        13. Validate maintenance-mode is-enabled command's output.

    :expectedresults: satellite-maintain maintenance-mode start/stop able
        to disable/enable sync-plan, stop/start crond.service and is able to add
        FOREMAN_MAINTAIN_TABLE rule in nftables.
    """
    enable_sync_ids = setup_sync_plan
    data_yml_path = '/var/lib/foreman-maintain/data.yml'
    local_data_yml_path = f'{robottelo_tmp_dir}/data.yml'

    maintenance_mode_off = [
        'Status of maintenance-mode: Off',
        'Nftables table: absent',
        'sync plans: enabled',
        'cron jobs: running',
    ]
    maintenance_mode_on = [
        'Status of maintenance-mode: On',
        'Nftables table: present',
        'sync plans: disabled',
        'cron jobs: not running',
    ]

    # Verify maintenance-mode status
    result = sat_maintain.cli.MaintenanceMode.status()
    assert 'FAIL' not in result.stdout
    assert 'OK' in result.stdout
    assert result.status == 0

    # Verify maintenance-mode is-enabled
    result = sat_maintain.cli.MaintenanceMode.is_enabled()
    assert 'FAIL' not in result.stdout
    assert 'OK' in result.stdout
    assert result.status == 1
    assert 'Maintenance mode is Off' in result.stdout

    # Verify maintenance-mode start
    result = sat_maintain.cli.MaintenanceMode.start()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    assert f'Total {len(enable_sync_ids)} sync plans are now disabled.' in result.stdout
    sat_maintain.get(remote_path=data_yml_path, local_path=local_data_yml_path)
    with open(local_data_yml_path) as f:
        data_yml = yaml.safe_load(f)
    assert len(enable_sync_ids) == len(data_yml[':default'][':sync_plans'][':disabled'])

    # Assert FOREMAN_MAINTAIN_TABLE listed in nftables
    result = sat_maintain.execute('nft list tables')
    assert 'FOREMAN_MAINTAIN_TABLE' in result.stdout

    result = sat_maintain.cli.Service.status(options={'only': 'crond.service'})
    assert result.status == 1
    assert 'Active: inactive (dead)' in result.stdout

    # Verify maintenance-mode status
    result = sat_maintain.cli.MaintenanceMode.status()
    assert 'FAIL' not in result.stdout
    assert 'OK' in result.stdout
    assert result.status == 0
    for i in maintenance_mode_on:
        assert i in result.stdout

    # Verify maintenance-mode is-enabled
    result = sat_maintain.cli.MaintenanceMode.is_enabled()
    assert 'FAIL' not in result.stdout
    assert 'OK' in result.stdout
    assert result.status == 0
    assert 'Maintenance mode is On' in result.stdout

    # Verify maintenance-mode stop
    result = sat_maintain.cli.MaintenanceMode.stop()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    assert f'Total {len(enable_sync_ids)} sync plans are now enabled.' in result.stdout
    sat_maintain.get(remote_path=data_yml_path, local_path=local_data_yml_path)
    with open(local_data_yml_path) as f:
        data_yml = yaml.safe_load(f)
    assert len(enable_sync_ids) == len(data_yml[':default'][':sync_plans'][':enabled'])

    # Assert FOREMAN_MAINTAIN_TABLE not listed in nftables
    result = sat_maintain.execute('nft list tables')
    assert 'FOREMAN_MAINTAIN_TABLE' not in result.stdout

    result = sat_maintain.cli.Service.status(options={'only': 'crond.service'})
    assert result.status == 0
    assert 'Active: active (running)' in result.stdout

    # Verify maintenance-mode status
    result = sat_maintain.cli.MaintenanceMode.status()
    assert 'FAIL' not in result.stdout
    assert 'OK' in result.stdout
    assert result.status == 0
    for i in maintenance_mode_off:
        assert i in result.stdout

    # Verify maintenance-mode is-enabled
    result = sat_maintain.cli.MaintenanceMode.is_enabled()
    assert 'FAIL' not in result.stdout
    assert 'OK' in result.stdout
    assert result.status == 1
    assert 'Maintenance mode is Off' in result.stdout

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.cli.MaintenanceMode.stop().status == 0
