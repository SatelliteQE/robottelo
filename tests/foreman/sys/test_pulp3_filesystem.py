"""Tests for Pulp3 file system.

:Requirement: Pulp3 installed

:CaseAutomation: Automated

:CaseComponent: Pulp

:team: Artemis

:CaseImportance: High

"""

from datetime import UTC, datetime
import json

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.utils.issue_handlers import is_open


@pytest.mark.upgrade
def test_selinux_status(target_sat):
    """Test SELinux status.

    :id: 43218070-ac5e-4679-b74a-3e2bcb497a0a

    :expectedresults: SELinux is enabled and there are no denials

    :BZ: 2263294
    """
    # check SELinux is enabled
    result = target_sat.execute('getenforce')
    assert 'Enforcing' in result.stdout
    # check there are no SELinux denials
    if not is_open('SAT-23121'):
        result = target_sat.execute('ausearch --input-logs -m avc -ts today --raw')
        assert result.status == 1, 'Some SELinux denials were found in journal.'


@pytest.mark.upgrade
@pytest.mark.parametrize(
    'directory',
    [
        '/var/lib/pulp/assets',
        '/var/lib/pulp/media',
        '/var/lib/pulp/tmp',
    ],
)
def test_pulp_directory_exists(target_sat, directory):
    """Check Pulp3 directories are present.

    :id: 96a64932-9e89-4063-9d5b-55c811375361

    :parametrized: yes

    :expectedresults: Directories are present
    """
    # check pulp3 directories present
    assert target_sat.execute(f'test -d {directory}').status == 0, f'{directory} must exist.'


@pytest.mark.upgrade
def test_pulp_service_definitions(target_sat):
    """Test systemd settings for Pulp3 file system layout.

    :id: e584faea-dede-4895-8d7f-411cb074f6c0

    :expectedresults: systemd files are present
    """
    # check pulpcore settings
    result = target_sat.execute('systemctl cat pulpcore-content.socket')
    assert result.status == 0
    assert 'ListenStream=/run/pulpcore-content.sock' in result.stdout
    result = target_sat.execute('systemctl cat pulpcore-content.service')
    assert result.status == 0
    assert 'Requires=pulpcore-content.socket' in result.stdout
    result = target_sat.execute('systemctl cat pulpcore-api.service')
    assert result.status == 0
    assert 'Requires=pulpcore-api.socket' in result.stdout
    # check pulp3 configuration file present
    result = target_sat.execute('test -f /etc/pulp/settings.py')
    assert result.status == 0


def test_pulp_workers_status(target_sat):
    """Ensure pulpcore-workers are in active (running) state

    :BZ: 1848111

    :id: f0b8b354-1a30-41c3-93d7-fb51e99c82b6

    :customerscenario: true

    :expectedresults: Pulpcore-workers are in active (running) state
    """
    output = target_sat.execute('systemctl status pulpcore-worker* | grep Active')
    result = output.stdout.rstrip().splitlines()
    assert all('Active: active (running)' in r for r in result)


def test_pulp_status(target_sat):
    """Test pulp status via pulp-cli.

    :id: aa7fda5a-cfa1-4fa1-8714-8d5a2e2f89d9

    :steps:
        1. Run pulp status command and parse the output.

    :expectedresults:
        1. Pulp-cli is installed and configured to work properly.
        2. The pulp components are alive according to provided status.
    """
    result = target_sat.execute('pulp status')
    now = datetime.now(UTC)
    assert not result.status
    status = json.loads(result.stdout)
    assert status['database_connection']['connected']
    assert status['redis_connection']['connected']

    workers_beats = [
        datetime.strptime(worker['last_heartbeat'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=UTC)
        for worker in status['online_workers']
    ]
    assert all((now - beat).seconds < 20 for beat in workers_beats), (
        'Some pulp workers seem to me dead!'
    )
    apps_beats = [
        datetime.strptime(app['last_heartbeat'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=UTC)
        for app in status['online_content_apps']
    ]
    assert all((now - beat).seconds < 20 for beat in apps_beats), (
        'Some content apps seem to me dead!'
    )


@pytest.mark.destructive
def test_content_validation_on_download(request, target_sat, function_org, function_product):
    """Test content validation on download with corrupted repository.

    :id: 9c07451f-1bd5-4d1c-9f18-b8a50de9a5d8

    :Verifies: SAT-22998, SAT-36451

    :steps:
        1. Download some yum repository on local filesystem into the pub directory.
        2. Create a yum repository with upstream_url pointing to the local repo, sync it.
           Note: The repo must be 'on_demand' so the content artifacts are NOT downloaded on sync.
        3. Corrupt one of the packages.
        4. Attempt to download the corrupted package from published_at URL,
           ensure 200 status on first and 404 status on second download.
        5. Check the downloaded file content contains 404 message.

    :expectedresults:
        1. Download attempt returns 404 status.
        2. Downloaded file content contains "404: Not Found".
    """
    pkg_name = f'{FAKE_0_CUSTOM_PACKAGE}.rpm'
    repo_fsname = f'test_{gen_string("alpha")}'
    pub_dir = f'/var/www/html/pub/{repo_fsname}/'

    # 1. Download some yum repository on local filesystem into the pub directory.
    target_sat.execute(f'mkdir -p {pub_dir}')
    request.addfinalizer(lambda: target_sat.execute(f'rm -rf {pub_dir}'))
    result = target_sat.execute(
        f'cd {pub_dir} && wget -r -np -nH --cut-dirs=1 {settings.repos.yum_0.url}/'
    )
    assert result.status == 0, 'Failed to download repository content'

    # 2. Create a yum repository with upstream_url pointing to the local repo, sync it.
    # Note: The repo must be 'on_demand' so the content artifacts are NOT downloaded on sync.
    repo = target_sat.api.Repository(
        organization=function_org,
        product=function_product,
        content_type='yum',
        download_policy='on_demand',
        url=f'http://{target_sat.hostname}/pub/{repo_fsname}/',
    ).create()
    repo.sync()

    # 3. Corrupt one of the packages.
    target_sat.execute(f'echo "CORRUPTED" >> {pub_dir}{pkg_name}')

    # 4. Attempt to download the corrupted package from published_at URL,
    #    ensure 200 status on first and 404 status on second download.
    download_url = f"{repo.full_path}Packages/{pkg_name[0]}/{pkg_name}"
    result = target_sat.execute(f'curl -O -w "%{{http_code}}" -s {download_url}')
    request.addfinalizer(lambda: target_sat.execute(f'rm -f {pkg_name}'))
    assert '200' in result.stdout, f'Expected 200 status, got: {result.stdout}'
    result = target_sat.execute(f'curl -O -w "%{{http_code}}" -s {download_url}')
    assert '404' in result.stdout, f'Expected 404 status, got: {result.stdout}'

    # 5. Check the downloaded file content contains 404 message.
    file_content = target_sat.execute(f'cat {pkg_name}')
    assert '404: Not Found' in file_content.stdout, (
        f'Expected "404: Not Found" in file content, got: {file_content.stdout}'
    )
