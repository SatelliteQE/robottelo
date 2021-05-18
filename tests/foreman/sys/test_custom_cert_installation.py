"""Test class for ``custom-cert-installation``.

:Requirement: custom-cert-installation

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: Certificates

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
import pytest

from robottelo.config import settings
from robottelo.ssh import get_connection


@pytest.mark.tier1
def test_custom_cert_update_satellite(satellite_latest, custom_certs_factory):
    """Update the satellite instance with new custom certs.

    :id: 6408226e-6c7f-4394-8a60-fb86f058f3fd

    :steps:
        1. Generate the custom certs
        2. Update satellite with custom certs
        3. Assert output does not report SSL certificate error
        4. Assert all services are running

    :expectedresults: Satellite should be updated with custom certs
    """
    satellite = satellite_latest.hostname
    cert_data = custom_certs_factory(hostname=satellite)
    with get_connection(hostname=satellite) as connection:
        result = connection.run(
            'katello-certs-check -c {} -k {} -b {}'.format(
                cert_data['cert_file_name'],
                cert_data['key_file_name'],
                cert_data['ca_bundle_file_name'],
            ),
            output_format='plain',
        )
        assert result.return_code == 0, 'Failed to generate the custom cert check command'

        # update the custom certs in Satellite
        command = f'satellite-installer --scenario satellite \
                          --certs-server-cert "/root/{satellite}/{satellite}.crt" \
                          --certs-server-key "/root/{satellite}/{satellite}.key" \
                          --certs-server-ca-cert "/root/cacert.crt" \
                          --certs-update-server --certs-update-server-ca'
        result = connection.run(command, output_format='plain', timeout=800)
        assert result.return_code == 0, 'Failed to update the satellite with custom certs'
        # assert no hammer ping SSL cert error
        result = connection.run('hammer ping')
        assert 'SSL certificate verification failed' not in result.stdout
        assert 'ok' in result.stdout[1]
        # assert all services are running
        result = connection.run('foreman-maintain health check --label services-up -y')
        assert result.return_code == 0, 'Not all services are running'


@pytest.mark.tier1
def test_custom_cert_install_satellite(rhel7_host, custom_certs_factory):
    """Install the satellite instance with new custom certs.

    :id: 1580564c-a714-4cd7-a80f-0e635dcec78e

    :steps:
        1. Generate the custom certs
        2. Install satellite with custom certs
        3. Assert output does not report SSL certificate error
        4. Assert all services are running

    :expectedresults: Satellite should be updated with custom certs
    """
    satellite = rhel7_host.hostname
    custom_certs_factory(hostname=satellite)
    with get_connection(hostname=satellite) as connection:
        # subscribe satellite dog_food server
        dogfood_url = (
            f'{settings.repos.dogfood_repo_host}/pub/katello-ca-consumer-latest.noarch.rpm'
        )
        activation_key = f'satellite-{settings.robottelo.satellite_version}-qa-rhel7'
        result = connection.run(f'yum -y localinstall {dogfood_url}', output_format='plain')
        assert result.return_code == 0, 'Failed to install the katello-ca-consumer certs'
        result = connection.run(
            f'subscription-manager register --org Sat6-CI --activationkey {activation_key}',
            output_format='plain',
        )
        assert result.return_code == 0, 'Failed to subscribe the host to dogfood'
        connection.run(
            'yum -y update && yum -y install satellite', output_format='plain', timeout=500
        )

        # install the satellite using custom certs
        installer_command = f'satellite-installer --scenario satellite \
                                          --certs-server-cert "/root/{satellite}/{satellite}.crt" \
                                          --certs-server-key "/root/{satellite}/{satellite}.key" \
                                          --certs-server-ca-cert "/root/cacert.crt"'
        result = connection.run(installer_command, output_format='plain', timeout=800)
        assert result.return_code == 0, 'Failed to install the satellite with custom certs'

        # assert no hammer ping SSL cert error
        result = connection.run('hammer ping')
        assert 'SSL certificate verification failed' not in result.stdout
        assert 'ok' in result.stdout[1]
        # assert all services are running
        result = connection.run('foreman-maintain health check --label services-up -y')
        assert result.return_code == 0, 'Not all services are running'
