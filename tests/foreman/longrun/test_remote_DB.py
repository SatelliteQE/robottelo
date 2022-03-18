"""Test class for Remote DB feature

:Requirement: Offload DBs from Satellite Server

:CaseAutomation: ManualOnly

:CaseLevel: Integration

:CaseComponent: ForemanMaintain

:Assignee: lvrtelov

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
import pytest


@pytest.mark.stubbed
@pytest.mark.tier1
def test_install_external_foreman():
    """Install Satellite with external foreman database

    :id: 1f6c9243-7157-4bff-bd78-26fa4a6a55fb

    :Steps: run satellite-installer with foreman-db options set

    :expectedresults: Completed Satellite installation

    :CaseLevel: Integration

    :CaseComponent: Installer
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_install_external_candlepin():
    """Install Satellite with external candlepin database

    :id: 2da6173c-ba16-4130-8992-35d3daa40ab2

    :Steps: run satellite-installer with candlepin-db options set

    :expectedresults: Completed Satellite installation

    :CaseLevel: Integration

    :CaseComponent: Installer
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_install_external_pulp():
    """Install Satellite with external pulp database

    :id: 90347920-d183-487e-9b65-03f6d581a173

    :Steps: run satellite-installer with pulp-db options set

    :expectedresults: Completed Satellite installation

    :CaseLevel: Integration

    :CaseComponent: Installer
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_install_external_all_with_SSL():
    """Install Satellite with all external databases with SSL

    :id: 5b4fd17a-7562-4d25-94e2-cda8f088a949

    :Steps: Run satellite-installer with pulp, foreman and candlepin db options set

    :expectedresults: Successful installation, all services running

    :CaseLevel: System

    :CaseComponent: Installer
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_reset_satellite_installation_external_all_with_SSL():
    """Reset Satellite installation with all ext SSL

    :id: b8f3752e-d59f-40c5-9ecf-42a1dd1dca12

    :Steps:

        1. Run satellite-installer with pulp, foreman and candlepin db options set
        2. Run satellite-installer --reset

    :expectedresults:

        1. Successful installation, all services running
        2. Successful reset, all services running

    :CaseLevel: System

    :CaseComponent: Installer
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_offline_backup_external_all_with_SSL():
    """Perform offline backup of external database

    :id: dc452b72-66b8-4a69-adb1-da089a0d4942

    :Steps: Run satellite-maintain backup offline

    :expectedresults: Database backup created

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_online_backup_external_all_with_SSL():
    """Perform online backup of external database

    :id: 2781aeb7-742e-4c95-ad57-c2d1c025bf90

    :Steps: Run satellite-maintain backup online

    :expectedresults: Database backup created

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_snapshot_backup_external_all_with_SSL():
    """Perform snapshot backup of external database

    :id: e2d35b31-15ce-40da-bbbf-d302838d41b6

    :Steps: Run satellite-maintain backup snapshot

    :expectedresults: Database backup created

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_restore_offline_backup_external_all_with_SSL():
    """Restore offline backup of external databases

    :id: c3e38e31-0058-48e9-b0f2-59788df64c38

    :Steps: Run satellite-maintain restore - and provide it offline backup

    :expectedresults: Database backup restored

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_restore_online_backup_external_all_with_SSL():
    """Restore online backup of external databases

    :id: 5c724e98-af13-4d5f-ba2e-84c8767c0222

    :Steps: Run satellite-maintain restore

    :expectedresults: Database backup restored

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_restore_snapshot_backup_external_all_with_SSL():
    """Restore snapshot backup of external databases

    :id: e6439ddf-4f5a-450d-8911-73082589105d

    :Steps: Run satellite-maintain restore

    :expectedresults: Database backup restored

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_offload_internal_db_to_external_db_host():
    """Offload internal databases content to an external database host

    :id: d07235c8-4584-469a-a87d-ace4dadb0a1f

    :Steps: Run satellite-installer with foreman, candlepin and pulp settings
        pointing to external host

    :expectedresults: Installed successful, all services running

    :CaseLevel: Integration

    :CaseComponent: Installer
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_upgrade_satellite_eith_all_external_db_SSL():
    """Upgrade Satellite with all external databases with SSL

    :id: 5730a492-6ce4-11e9-a923-1681be663d3e

    :Steps:

        1. Run satellite-installer with pulp, foreman and candlepin db options set
        2. Upgrade with satellite-maintain

    :expectedresults:

        1. Successful installation, all services running
        2. Successful upgrade, all services running

    :CaseLevel: System
    """
