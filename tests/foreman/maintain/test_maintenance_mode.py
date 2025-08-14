"""Test class for satellite-maintain maintenance-mode functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Rocket

:CaseImportance: Critical

"""

import pytest
import yaml

from robottelo.config import robottelo_tmp_dir


@pytest.mark.include_satellite_iop
@pytest.mark.e2e
def test_positive_maintenance_mode(request, sat_maintain, setup_sync_plan):
    """Test satellite-maintain maintenance-mode subcommand

    :id: 51d76219-d3cc-43c0-9894-7bcb75c163c3

    :setup:
        1. Get a Satellite(default and/or IoP-enabled Satellite)
        2. Create a sync-plan which is enabled
        3. set ':manage_crond: true' in /etc/foreman-maintain/foreman_maintain.yml

    :steps:
        1. Verify that maintenance-mode is Off.
        2. For IoP-enabled Satellite, verify that IoP timer is active.
        3. Start maintenance-mode.
        4. Verify that active sync-plans got disabled or not.
        5. Verify that FOREMAN_MAINTAIN_TABLE is mentioned in nftables list.
        6. Verify that crond.service is stopped.
        7. For IoP-enabled Satellite, verify that IoP timer is inactive.
        8. Validate maintenance-mode status command's output.
        9. Validate maintenance-mode is-enabled command's output.
        10. Stop maintenance-mode.
        11. Verify that disabled sync-plans got re-enabled or not.
        12. Verify that FOREMAN_MAINTAIN_TABLE is not mentioned in nftables list.
        13. For IoP-enabled Satellite, verify that IoP timer is active.
        14. Verify that crond.service is running.
        15. Validate maintenance-mode status command's output.
        16. Validate maintenance-mode is-enabled command's output.

    :expectedresults: satellite-maintain maintenance-mode start/stop able
        to disable/enable sync-plan, stop/start crond.service, stop/start IoP timer,
        and is able to add FOREMAN_MAINTAIN_TABLE rule in nftables.
    """

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.cli.MaintenanceMode.stop().status == 0

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
    local_advisor_enabled = sat_maintain.local_advisor_enabled

    # Verify maintenance-mode status
    mm_status = sat_maintain.cli.MaintenanceMode.status()
    assert 'FAIL' not in mm_status.stdout
    assert 'OK' in mm_status.stdout
    assert mm_status.status == 0

    # Verify maintenance-mode is-enabled
    mm_is_enabled = sat_maintain.cli.MaintenanceMode.is_enabled()
    assert 'FAIL' not in mm_is_enabled.stdout
    assert 'OK' in mm_is_enabled.stdout
    assert mm_is_enabled.status == 1
    assert 'Maintenance mode is Off' in mm_is_enabled.stdout

    if local_advisor_enabled:
        timer_status = sat_maintain.execute('systemctl status iop-service-vuln-vmaas-sync.timer')
        assert timer_status.status == 0
        assert 'Active: active (running)' in timer_status.stdout

    # Verify maintenance-mode start
    mm_start = sat_maintain.cli.MaintenanceMode.start()
    assert 'FAIL' not in mm_start.stdout
    assert mm_start.status == 0
    assert f'Total {len(enable_sync_ids)} sync plans are now disabled.' in mm_start.stdout
    sat_maintain.get(remote_path=data_yml_path, local_path=local_data_yml_path)
    with open(local_data_yml_path) as f:
        data_yml = yaml.safe_load(f)
    assert len(enable_sync_ids) == len(data_yml[':default'][':sync_plans'][':disabled'])

    if local_advisor_enabled:
        assert 'All timers stopped' in mm_start.stdout
        timer_status = sat_maintain.execute('systemctl status iop-service-vuln-vmaas-sync.timer')
        assert timer_status.status == 3
        assert 'Active: inactive (dead)' in timer_status.stdout

    # Assert FOREMAN_MAINTAIN_TABLE listed in nftables
    nftables = sat_maintain.execute('nft list tables')
    assert 'FOREMAN_MAINTAIN_TABLE' in nftables.stdout

    cron_status = sat_maintain.cli.Service.status(options={'only': 'crond.service'})
    assert cron_status.status == 1
    assert 'Active: inactive (dead)' in cron_status.stdout

    # Verify maintenance-mode status
    mm_status = sat_maintain.cli.MaintenanceMode.status()
    assert 'FAIL' not in mm_status.stdout
    assert 'OK' in mm_status.stdout
    assert mm_status.status == 0
    for i in maintenance_mode_on:
        assert i in mm_status.stdout

    # Verify maintenance-mode is-enabled
    mm_is_enabled = sat_maintain.cli.MaintenanceMode.is_enabled()
    assert 'FAIL' not in mm_is_enabled.stdout
    assert 'OK' in mm_is_enabled.stdout
    assert mm_is_enabled.status == 0
    assert 'Maintenance mode is On' in mm_is_enabled.stdout

    # Verify maintenance-mode stop
    mm_stop = sat_maintain.cli.MaintenanceMode.stop()
    assert 'FAIL' not in mm_stop.stdout
    assert mm_stop.status == 0
    assert f'Total {len(enable_sync_ids)} sync plans are now enabled.' in mm_stop.stdout
    sat_maintain.get(remote_path=data_yml_path, local_path=local_data_yml_path)
    with open(local_data_yml_path) as f:
        data_yml = yaml.safe_load(f)
    assert len(enable_sync_ids) == len(data_yml[':default'][':sync_plans'][':enabled'])

    if local_advisor_enabled:
        assert 'All timers started' in mm_stop.stdout
        timer_status = sat_maintain.execute('systemctl status iop-service-vuln-vmaas-sync.timer')
        assert timer_status.status == 0
        assert 'Active: active (waiting)' in timer_status.stdout

    # Assert FOREMAN_MAINTAIN_TABLE not listed in nftables
    nftables = sat_maintain.execute('nft list tables')
    assert 'FOREMAN_MAINTAIN_TABLE' not in nftables.stdout

    cron_status = sat_maintain.cli.Service.status(options={'only': 'crond.service'})
    assert cron_status.status == 0
    assert 'Active: active (running)' in cron_status.stdout

    # Verify maintenance-mode status
    mm_status = sat_maintain.cli.MaintenanceMode.status()
    assert 'FAIL' not in mm_status.stdout
    assert 'OK' in mm_status.stdout
    assert mm_status.status == 0
    for i in maintenance_mode_off:
        assert i in mm_status.stdout

    # Verify maintenance-mode is-enabled
    mm_is_enabled = sat_maintain.cli.MaintenanceMode.is_enabled()
    assert 'FAIL' not in mm_is_enabled.stdout
    assert 'OK' in mm_is_enabled.stdout
    assert mm_is_enabled.status == 1
    assert 'Maintenance mode is Off' in mm_is_enabled.stdout
