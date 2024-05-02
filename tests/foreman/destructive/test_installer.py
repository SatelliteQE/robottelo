"""Smoke tests to check installation health

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Platform

:CaseImportance: Critical

"""

import random

from fauxfactory import gen_domain, gen_string
import pytest

from robottelo.constants import SATELLITE_ANSWER_FILE
from robottelo.utils.installer import InstallerCommand

pytestmark = pytest.mark.destructive


@pytest.fixture
def set_random_fqdn(target_sat):
    shortname = gen_string('alpha')
    new_domain = gen_domain()
    target_sat.execute(
        f'echo "search {new_domain}" >> /etc/resolv.conf; hostnamectl set-hostname {shortname}'
    )
    yield shortname, new_domain
    target_sat.execute(f'hostnamectl set-hostname {target_sat.hostname}')


def test_installer_sat_pub_directory_accessibility(target_sat):
    """Verify the public directory accessibility from satellite url after disabling it from
    the custom-hiera

    :id: 2ef78840-098c-4be2-a9e5-db60f16bb803

    :steps:
        1. Check the public directory accessibility from http and https satellite url
        2. Add the foreman_proxy_content::pub_dir::pub_dir_options:"+FollowSymLinks -Indexes"
            in custom-hiera.yaml file.
        3. Run the satellite-installer.
        4. Check the public directory accessibility from http and https satellite url

    :expectedresults: Public directory accessibility from http and https satellite url.
        1. It should be accessible if accessibility is enabled(by default it is enabled).
        2. It should not be accessible if accessibility is disabled in custom_hiera.yaml file.

    :CaseImportance: High

    :BZ: 1960801

    :customerscenario: true
    """
    custom_hiera_location = '/etc/foreman-installer/custom-hiera.yaml'
    custom_hiera_settings = (
        'foreman_proxy_content::pub_dir::pub_dir_options: "+FollowSymLinks -Indexes"'
    )
    http_curl_command = f'curl -i {target_sat.url.replace("https", "http")}/pub/ -k'
    https_curl_command = f'curl -i {target_sat.url}/pub/ -k'
    for command in [http_curl_command, https_curl_command]:
        accessibility_check = target_sat.execute(command)
        assert (
            'HTTP/1.1 200 OK' in accessibility_check.stdout
            or 'HTTP/2 200' in accessibility_check.stdout
        )
    target_sat.get(
        local_path='custom-hiera-satellite.yaml',
        remote_path=f'{custom_hiera_location}',
    )
    _ = target_sat.execute(f'echo {custom_hiera_settings} >> {custom_hiera_location}')
    command_output = target_sat.execute('satellite-installer', timeout='20m')
    assert 'Success!' in command_output.stdout
    for command in [http_curl_command, https_curl_command]:
        accessibility_check = target_sat.execute(command)
        assert 'HTTP/1.1 200 OK' not in accessibility_check.stdout
        assert 'HTTP/2 200' not in accessibility_check.stdout
    target_sat.put(
        local_path='custom-hiera-satellite.yaml',
        remote_path=f'{custom_hiera_location}',
    )
    command_output = target_sat.execute('satellite-installer', timeout='20m')
    assert 'Success!' in command_output.stdout


def test_positive_mismatched_satellite_fqdn(target_sat, set_random_fqdn):
    """The satellite-installer should display the mismatched FQDN

    :id: 264910ca-23c8-4192-a993-24bc04994a4c

    :steps:
        1. Set incorrect satellite hostname.
        2. assert that output of 'facter fqdn' and 'hostname --fqdn' is different.
        3. Run satellite-installer.
        4. Assert that satellite-installer command displays mismatched FQDN.

    :expectedresults: The satellite-installer should display the mismatched FQDN.
    """
    shortname, new_domain = set_random_fqdn
    facter_command_output = target_sat.execute('facter fqdn').stdout.strip()
    hostname_command_output = target_sat.execute('hostname --fqdn').stdout.strip()
    assert facter_command_output == f'{shortname}.{new_domain}'
    assert hostname_command_output == shortname
    assert facter_command_output != hostname_command_output
    warning_message = (
        f"Output of 'facter fqdn' "
        f"({facter_command_output}) is different from 'hostname -f' "
        f"({hostname_command_output})"
    )
    installer_command_output = target_sat.execute('satellite-installer').stderr
    assert warning_message in str(installer_command_output)


def test_positive_installer_certs_regenerate(target_sat):
    """Ensure "satellite-installer --certs-regenerate true" command correctly generates
    /etc/tomcat/cert-users.properties after editing answers file

    :id: db6152c3-4459-425b-998d-4a7992ca1f72

    :steps:
        1. Update /etc/foreman-installer/scenarios.d/satellite-answers.yaml
        2. Fill some empty strings in certs category for 'state'
        3. Run satellite-installer --certs-regenerate true
        4. hammer ping

    :expectedresults: Correct generation of /etc/tomcat/cert-users.properties

    :BZ: 1964037

    :customerscenario: true
    """
    target_sat.execute(f'sed -i "s/state: North Carolina/state: \'\'/g" {SATELLITE_ANSWER_FILE}')
    result = target_sat.execute(f'grep state: {SATELLITE_ANSWER_FILE}')
    assert "state: ''" in result.stdout
    result = target_sat.install(
        InstallerCommand(
            'certs-update-all',
            'certs-update-server',
            'certs-update-server-ca',
            certs_regenerate=['true'],
        )
    )
    assert result.status == 0
    assert 'FAIL' not in target_sat.cli.Base.ping()


def test_positive_installer_puma_worker_count(target_sat):
    """Installer should set the puma worker count and thread max without having to manually
    restart the foreman service.

    :id: d0e7d958-dd3e-4962-bf5a-8d7ec36f3485

    :steps:
        1. Check how many puma workers there are
        2. Select a new worker count that is less than the default
        2. Change answer's file to have new count for puma workers
        3. Run satellite-installer --foreman-foreman-service-puma-workers new_count --foreman-foreman-service-puma-threads-max new_count

    :expectedresults: aux should show there are only new_count puma workers after installer runs

    :BZ: 2025760

    :customerscenario: true
    """
    count = int(target_sat.execute('pgrep --full "puma: cluster worker" | wc -l').stdout)
    worker_count = str(random.randint(1, count - 1))
    result = target_sat.install(
        InstallerCommand(
            foreman_foreman_service_puma_workers=worker_count,
            foreman_foreman_service_puma_threads_max=worker_count,
        )
    )
    assert result.status == 0
    result = target_sat.execute(f'grep "foreman_service_puma_workers" {SATELLITE_ANSWER_FILE}')
    assert worker_count in result.stdout
    result = target_sat.execute('ps aux | grep -v grep | grep -e USER -e puma')
    for i in range(count):
        if i < int(worker_count):
            assert f'cluster worker {i}' in result.stdout
        else:
            assert f'cluster worker {i}' not in result.stdout


def test_negative_handle_invalid_certificate(cert_setup_destructive_teardown):
    """Satellite installer should not do any harmful changes to existing satellite after attempt
    to use invalid certificates.

    :id: 97b72faf-4684-4d8c-ae0e-1ebd5085620b

    :steps:
        1. Launch satellite installer and attempt to use invalid certificates

    :expectedresults: Satellite installer should fail and Satellite should be running

    :BZ: 2221621, 2238363

    :customerscenario: true

    """
    cert_data, satellite = cert_setup_destructive_teardown

    # check if satellite is running
    result = satellite.execute('hammer ping')
    assert result.status == 0, f'Hammer Ping failed:\n{result.stderr}'

    # attempt to use invalid certificates
    result = satellite.install(
        InstallerCommand(
            'certs-update-server',
            'certs-update-server-ca',
            scenario='satellite',
            certs_server_cert='/root/certs/invalid.crt',
            certs_server_key='/root/certs/invalid.key',
            certs_server_ca_cert=f'"/root/{cert_data["ca_bundle_file_name"]}"',
        )
    )
    # installer should fail with non-zero value
    assert result.status != 0
    assert "verification failed" in result.stdout

    result = satellite.execute('hammer ping')
    assert result.status == 0, f'Hammer Ping failed:\n{result.stderr}'
