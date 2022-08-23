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
import requests

from robottelo import constants
from robottelo.config import settings

USER = settings.subscription.rhn_username
PASSWORD = settings.subscription.rhn_password
SSH_PASS = settings.server.ssh_password
POOL = settings.subscription.rhn_poolid
BACKUP_DIR = '/var/backup'


@pytest.mark.parametrize(
    "sat_ready_rhel", [7, 8] if settings.server.version.rhel_version < 8 else [8], indirect=True
)
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_clone_backup(target_sat, sat_ready_rhel, backup_type):
    rhel_version = sat_ready_rhel._v_major

    # SATELLITE PART - SOURCE SERVER
    # Enabling and starting services
    assert target_sat.execute('satellite-maintain service enable').status == 0
    assert target_sat.execute('satellite-maintain service start').status == 0
    # Doing backup
    backup_result = target_sat.execute(
        f'satellite-maintain backup {backup_type} --assumeyes /var/backup'
    )
    assert backup_result.status == 0
    # Getting backup directory
    sat_backup_dir = backup_result.stdout.strip().split()[-2]

    source_sat = target_sat
    # Copying satellite backup to target RHEL
    assert (
        source_sat.execute(
            f'sshpass -p "{SSH_PASS}" scp -o StrictHostKeyChecking=no -r {sat_backup_dir}'
            f'root@{sat_ready_rhel.hostname}:/backup/'
        ).status
        == 0
    )

    # RHEL PART - TARGET SERVER
    assert sat_ready_rhel.execute('ls /backup/config_files.tar.gz').status == 0
    # Registering to cdn
    sat_ready_rhel.register_to_cdn()
    # Disabling repositories
    assert sat_ready_rhel.execute('subscription-manager repos --disable=*').status == 0
    # Getting satellite maintenance repo
    res = requests.get(
        f'http://ohsnap.sat.engineering.redhat.com/api/releases/{target_sat.version}/'
        f'el{rhel_version}/satellite/repo_file'
    )
    escaped = res.text.replace('$', '\\$')
    assert sat_ready_rhel.execute(f'echo "{escaped}" > /etc/yum.repos.d/satellite.repo').status == 0
    assert sat_ready_rhel.execute('ls /etc/yum.repos.d/satellite.repo').status == 0
    # Getting repos to enable according to version of used rhel
    repos_to_enable = getattr(constants, f'OHSNAP_RHEL{rhel_version}_REPOS')
    subscription_mng_cmd = 'subscription-manager repos'
    for repo in repos_to_enable:
        subscription_mng_cmd += f' --enable={repo}'
    # Enabling repositories
    assert sat_ready_rhel.execute(subscription_mng_cmd).status == 0

    # If we want to do restore on rhel 8 we need to enable satellite module
    if rhel_version == 8:
        # Enabling satellite module
        assert sat_ready_rhel.execute('dnf module enable -y satellite:el8').status == 0

    # Install satellite-clone
    assert sat_ready_rhel.execute('yum install satellite-clone -y').status == 0
    # Run satellite-clone
    assert sat_ready_rhel.execute('satellite-clone -y', timeout='3h').status == 0
    assert sat_ready_rhel.execute('foreman-maintain health check').status == 0


@pytest.mark.parametrize(
    "sat_ready_rhel", [7, 8] if settings.server.version.rhel_version < 8 else [8], indirect=True
)
def test_positive_clone_no_pulp_data(target_sat, sat_ready_rhel):
    rhel_version = sat_ready_rhel._v_major

    # SATELLITE PART - SOURCE SERVER
    # Enabling and starting services
    assert target_sat.execute('satellite-maintain service enable').status == 0
    assert target_sat.execute('satellite-maintain service start').status == 0
    # Doing backup
    no_pulp_backup_result = target_sat.execute(
        '''
        satellite-maintain backup offline --skip-pulp-content \
        --assumeyes /var/backup'''
    )
    assert no_pulp_backup_result.status == 0
    sat_backup_dir = no_pulp_backup_result.stdout.strip().split()[-2]

    source_sat = target_sat
    # Copying satellite pulp data to target RHEL
    assert sat_ready_rhel.execute('mkdir -p /var/lib/pulp').status == 0
    assert (
        source_sat.execute(
            f'sshpass -p "{SSH_PASS}" scp -o StrictHostKeyChecking=no '
            f'-r /var/lib/pulp root@{sat_ready_rhel.hostname}:/var/lib/pulp/pulp'
        ).status
        == 0
    )
    # Copying satellite backup to target RHEL
    assert (
        source_sat.execute(
            f'sshpass -p "{SSH_PASS}" scp -o StrictHostKeyChecking=no '
            f'-r {sat_backup_dir} root@{sat_ready_rhel.hostname}:/backup/'
        ).status
        == 0
    )

    # RHEL PART - TARGET SERVER
    assert sat_ready_rhel.execute('ls /backup/config_files.tar.gz').status == 0
    # Registering to cdn
    sat_ready_rhel.register_to_cdn()
    # Disabling repositories
    assert sat_ready_rhel.execute('subscription-manager repos --disable=*').status == 0
    # Getting satellite maintenace repo
    res = requests.get(
        f'http://ohsnap.sat.engineering.redhat.com/api/releases/{target_sat.version}/'
        f'el{rhel_version}/satellite/repo_file'
    )
    escaped = res.text.replace('$', '\\$')
    assert sat_ready_rhel.execute(f'echo "{escaped}" > /etc/yum.repos.d/satellite.repo').status == 0
    assert sat_ready_rhel.execute('ls /etc/yum.repos.d/satellite.repo').status == 0
    # Getting repos to enable according to version of used rhel
    repos_to_enable = getattr(constants, f'OHSNAP_RHEL{rhel_version}_REPOS')
    subscription_mng_cmd = 'subscription-manager repos'
    for repo in repos_to_enable:
        subscription_mng_cmd += f' --enable={repo}'
    # Enabling repositories
    assert sat_ready_rhel.execute(subscription_mng_cmd).status == 0

    # If we want to do restore on rhel 8 we need to enable satellite module
    if rhel_version == 8:
        # Enabling satellite module
        assert sat_ready_rhel.execute('dnf module enable -y satellite:el8').status == 0
    # Install satellite-clone
    assert sat_ready_rhel.execute('yum install satellite-clone -y').status == 0
    # Run satellite-clone
    assert sat_ready_rhel.execute('satellite-clone -y', timeout='3h').status == 0
    assert sat_ready_rhel.execute('foreman-maintain health check').status == 0
