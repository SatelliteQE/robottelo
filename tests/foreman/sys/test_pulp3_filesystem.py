"""Tests for Pulp3 file system.

:Requirement: Pulp3 installed

:CaseAutomation: Automated

:CaseComponent: Pulp

:team: Artemis

:CaseImportance: High

"""

from datetime import UTC, datetime
import re

from fauxfactory import gen_string
from pulp_glue.common.exceptions import PulpException
import pytest

from robottelo.config import settings
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE


def test_selinux_status(target_sat):
    """Test SELinux status.

    :id: 43218070-ac5e-4679-b74a-3e2bcb497a0a

    :expectedresults: SELinux is enabled and there are no denials for pulp services

    :Verifies: SAT-23121
    """
    # check SELinux is enabled
    result = target_sat.execute('getenforce')
    assert 'Enforcing' in result.stdout
    # check there are no SELinux denials
    result = target_sat.execute('ausearch --input-logs -m avc -ts today --comm pulp --raw')
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
@pytest.mark.parametrize(
    ('unit', 'definition'),
    [
        ('pulp-api.service', '/etc/containers/systemd/pulp-api.container'),
        ('pulp-content.service', '/etc/containers/systemd/pulp-content.container'),
        ('pulp-worker@1.service', '/etc/containers/systemd/pulp-worker@.container'),
        ('pulp-worker.target', '/etc/systemd/system/pulp-worker.target'),
    ],
    ids=['pulp-api', 'pulp-content', 'pulp-worker-1', 'pulp-worker-target'],
)
def test_pulp_service_definitions(target_sat, unit, definition):
    """Check Pulp units are defined and included in foreman.target.

    :id: e584faea-dede-4895-8d7f-411cb074f6c0

    :parametrized: yes

    :steps:
        1. Read each Pulp unit and its source definition.
        2. Check that foreman.target depends on the unit.

    :expectedresults: Each Pulp unit is defined and is a dependency of foreman.target.
    """
    result = target_sat.execute(f'systemctl cat {unit}')
    assert result.status == 0, f'{unit}: {result.stderr}'
    assert target_sat.execute(f'test -f {definition}').status == 0, f'{definition} is missing'

    result = target_sat.execute('systemctl list-dependencies --plain --no-pager foreman.target')
    assert result.status == 0, result.stderr
    assert unit in result.stdout, f'{unit} is not a dependency of foreman.target'


def test_pulp_workers_status(target_sat):
    """Ensure Pulp worker services are active.

    :BZ: 1848111

    :id: f0b8b354-1a30-41c3-93d7-fb51e99c82b6

    :customerscenario: true

    :steps:
        1. List Pulp worker services.
        2. Check each worker is active.

    :expectedresults: Pulp worker services are active.
    """
    result = target_sat.execute(
        "systemctl list-units --all --type=service --no-legend --no-pager 'pulp-worker@*.service'"
    )
    assert result.status == 0, result.stderr
    workers = re.findall(r'pulp-worker@\d+\.service', result.stdout)
    assert workers, 'No Pulp worker services found'
    inactive = [
        unit for unit in workers if target_sat.execute(f'systemctl is-active {unit}').status
    ]
    assert not inactive, f'Inactive Pulp worker services: {inactive}'


def test_pulp_status(target_sat):
    """Test Pulp status via its API.

    :id: aa7fda5a-cfa1-4fa1-8714-8d5a2e2f89d9

    :steps:
        1. Query the Pulp status endpoint.

    :expectedresults:
        1. The Pulp API is reachable and returns status data.
        2. The pulp components are alive according to provided status.
    """
    try:
        status = target_sat.pulp_glue.call('status_read')
    except PulpException as error:
        if 'CERTIFICATE_VERIFY_FAILED' in str(error):
            error.add_note(target_sat.pulp_glue_tls_diagnostics())
        raise
    now = datetime.now(UTC)
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
    ca_opt = f'--cacert {target_sat.ca_cert_file}'
    result = target_sat.execute(f'curl -O -w "%{{http_code}}" -s {ca_opt} {download_url}')
    request.addfinalizer(lambda: target_sat.execute(f'rm -f {pkg_name}'))
    assert result.stdout.strip() == '200'
    result = target_sat.execute(f'curl -O -w "%{{http_code}}" -s {ca_opt} {download_url}')
    assert '404' in result.stdout, f'Expected 404 status, got: {result.stdout}'

    # 5. Check the downloaded file content contains 404 message.
    file_content = target_sat.execute(f'cat {pkg_name}')
    assert '404: Not Found' in file_content.stdout, (
        f'Expected "404: Not Found" in file content, got: {file_content.stdout}'
    )
