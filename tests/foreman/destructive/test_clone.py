"""Tests for satellite-maintain clone

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SatelliteClone

:Assignee: lpramuk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.hosts import Satellite

SSH_PASS = settings.server.ssh_password
pytestmark = pytest.mark.destructive


@pytest.mark.parametrize("sat_ready_rhel", [8], indirect=True)
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
@pytest.mark.parametrize('skip_pulp', [False, True], ids=['include_pulp', 'skip_pulp'])
def test_positive_clone_backup(target_sat, sat_ready_rhel, backup_type, skip_pulp):
    """Make an online/offline backup with/without pulp data of Satellite and clone it (restore it).

    :id: 5b9182d5-6789-4d2c-bcc3-6641b96ab277

    :steps:
        1. Create an online/offline backup with/without pulp data
        2. Copy it to target rhel
        3. Install satellite-clone
        4. Run satellite clone on target rhel

    :expectedresult:
        1. Satellite-clone ran successfully

    :parametrized: yes
    """
    rhel_version = sat_ready_rhel._v_major
    sat_version = target_sat.version

    # SATELLITE PART - SOURCE SERVER
    # Enabling and starting services
    assert target_sat.cli.Service.enable().status == 0
    assert target_sat.cli.Service.start().status == 0

    # Doing backup
    backup_result = target_sat.cli.Backup.run_backup(
        backup_dir='/var/backup',
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'skip-pulp-content': skip_pulp},
    )
    assert backup_result.status == 0
    sat_backup_dir = backup_result.stdout.strip().split()[-2]

    if skip_pulp:
        # Copying satellite pulp data to target RHEL
        assert sat_ready_rhel.execute('mkdir -p /var/lib/pulp').status == 0
        assert (
            target_sat.execute(
                f'''sshpass -p "{SSH_PASS}" scp -o StrictHostKeyChecking=no \
                -r /var/lib/pulp root@{sat_ready_rhel.hostname}:/var/lib/pulp/pulp'''
            ).status
            == 0
        )
    # Copying satellite backup to target RHEL
    assert (
        target_sat.execute(
            f'''sshpass -p "{SSH_PASS}" scp -o StrictHostKeyChecking=no \
            -r {sat_backup_dir} root@{sat_ready_rhel.hostname}:/backup/'''
        ).status
        == 0
    )
    assert target_sat.cli.Service.stop().status == 0
    assert target_sat.cli.Service.disable().status == 0

    # RHEL PART - TARGET SERVER
    assert sat_ready_rhel.execute('ls /backup/config_files.tar.gz').status == 0
    # Registering to cdn
    sat_ready_rhel.register_to_cdn()
    # Disabling repositories
    assert sat_ready_rhel.execute('subscription-manager repos --disable=*').status == 0
    # Getting satellite maintenace repo
    sat_ready_rhel.download_repofile(product='satellite', release=sat_version)
    # Enabling repositories
    for repo in getattr(constants, f"OHSNAP_RHEL{rhel_version}_REPOS"):
        sat_ready_rhel.enable_repo(repo, force=True)
    # Enabling satellite module
    assert sat_ready_rhel.execute(f'dnf module enable -y satellite:el{rhel_version}').status == 0
    # Install satellite-clone
    assert sat_ready_rhel.execute('yum install satellite-clone -y').status == 0
    # Disabling CDN repos as we install from dogfdood
    assert (
        sat_ready_rhel.execute(
            'echo "enable_repos: false" >> /etc/satellite-clone/satellite-clone-vars.yml'
        ).status
        == 0
    )
    # Run satellite-clone
    assert sat_ready_rhel.execute('satellite-clone -y', timeout='3h').status == 0
    cloned_sat = Satellite(sat_ready_rhel.hostname)
    assert cloned_sat.cli.Health.check().status == 0
