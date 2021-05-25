from pathlib import Path

import pytest
from fauxfactory import gen_string

from robottelo import ssh
from robottelo.config import settings
from robottelo.helpers import get_data_file
from robottelo.ssh import get_connection
from robottelo.ssh import upload_file


@pytest.fixture(scope="module")
def cert_data():
    """Get host name, scripts, and create working directory."""

    def _cert_data(hostname=None):
        sat6_hostname = hostname or settings.server.hostname
        capsule_hostname = 'capsule.example.com'
        key_file_name = '{0}/{0}.key'.format(sat6_hostname)
        cert_file_name = '{0}/{0}.crt'.format(sat6_hostname)
        ca_bundle_file_name = 'cacert.crt'
        success_message = 'Validation succeeded'
        cert_data = {
            'sat6_hostname': sat6_hostname,
            'capsule_hostname': capsule_hostname,
            'key_file_name': key_file_name,
            'cert_file_name': cert_file_name,
            'ca_bundle_file_name': ca_bundle_file_name,
            'success_message': success_message,
        }
        return cert_data

    return _cert_data


@pytest.fixture()
def cert_setup(cert_data):
    """copy all configuration files to satellite host for generating custom certs"""

    def _cert_setup(hostname=None):
        # Need a subdirectory under ssl-build with same name as Capsule name
        hostname = hostname or settings.server.hostname
        _cert_data = cert_data(hostname)
        with get_connection(timeout=100, hostname=hostname) as connection:
            connection.run('mkdir ssl-build/{}'.format(_cert_data['capsule_hostname']))
            # Ignore creation error, but assert directory exists
            assert connection.run('test -e ssl-build/{}'.format(_cert_data['capsule_hostname']))
        upload_file(
            local_file=get_data_file('generate-ca.sh'),
            remote_file='generate-ca.sh',
            hostname=hostname,
        )
        upload_file(
            local_file=get_data_file('generate-crt.sh'),
            remote_file='generate-crt.sh',
            hostname=hostname,
        )
        upload_file(
            local_file=get_data_file('openssl.cnf'), remote_file='openssl.cnf', hostname=hostname
        )
        # create the CA cert.
        with get_connection(timeout=300, hostname=hostname) as connection:
            result = connection.run('echo 100001 > serial')
            result = connection.run('bash generate-ca.sh')
            assert result.return_code == 0
        # create the Satellite's cert
        with get_connection(timeout=300, hostname=hostname) as connection:
            result = connection.run(
                'yes | bash {} {}'.format('generate-crt.sh', _cert_data['sat6_hostname'])
            )
            assert result.return_code == 0

    return _cert_setup


@pytest.fixture()
def certs_cleanup():
    """cleanup all cert configuration files"""
    yield
    files = [
        'cacert.crt',
        'certindex*',
        'generate-*.sh',
        'capsule_cert' 'openssl.cnf',
        'private',
        'serial*',
        'certs/*',
        settings.server.hostname,
    ]
    with get_connection(timeout=300) as connection:
        files = ' '.join(files)
        result = connection.run(f'rm -rf {files}')
        assert result.return_code == 0


@pytest.fixture()
def generate_certs():
    """generate custom certs in satellite host"""
    upload_file(
        local_file=get_data_file('certs.sh'),
        remote_file='certs.sh',
    )
    upload_file(
        local_file=get_data_file('extensions.txt'),
        remote_file='extensions.txt',
    )
    with get_connection(timeout=300) as connection:
        result = connection.run('bash certs.sh')
        assert result.return_code == 0


@pytest.fixture(scope='module')
def file_setup():
    """Create working directory and file."""
    capsule_hostname = 'capsule.example.com'
    tmp_dir = '/var/tmp/{}'.format(gen_string('alpha', 6))
    caps_cert_file = f'{tmp_dir}/ssl-build/capsule.example.com/cert-data'
    # Use same path locally as on remote for storing files
    Path(f'{tmp_dir}/ssl-build/capsule.example.com/').mkdir(parents=True, exist_ok=True)
    with get_connection(timeout=200) as connection:
        result = ssh.command(f'mkdir {tmp_dir}')
        assert result.return_code == 0, 'Create working directory failed.'
        # Generate a Capsule cert for capsule.example.com
        result = connection.run(
            'capsule-certs-generate '
            '--foreman-proxy-fqdn capsule.example.com '
            '--certs-tar {}/capsule_certs.tar '.format(tmp_dir),
            timeout=100,
        )
    return {
        'tmp_dir': tmp_dir,
        'caps_cert_file': caps_cert_file,
        'capsule_hostname': capsule_hostname,
    }


@pytest.fixture()
def custom_certs_factory(cert_data, cert_setup):
    """generate the custom certs based on-demand hostname"""

    def _custom_certs_factory(hostname=None):
        if hostname:
            cert_setup(hostname)
            return cert_data(hostname)
        else:
            cert_setup()
            return cert_data()

    return _custom_certs_factory
