"""Test class for ``katello-certs-check``.

:Requirement: katello-certs-check

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: Certificates

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
import re
from pathlib import Path

import pytest
from fauxfactory import gen_string

from robottelo import ssh
from robottelo.config import settings
from robottelo.helpers import get_data_file
from robottelo.ssh import download_file
from robottelo.ssh import get_connection
from robottelo.ssh import upload_file
from robottelo.utils.issue_handlers import is_open


@pytest.mark.run_in_one_thread
class TestKatelloCertsCheck:
    """Implements ``katello-certs-check`` tests.

    Depends on presence of scripts and files in
    tests/foreman/data/ which come from
    https://github.com/iNecas/ownca
    CA cert (a.k.a cacert.crt or rootCA.pem) can be used as bundle file.
    """

    invalid_inputs = [
        (
            {
                'check': "Checking CA bundle against the certificate file",
                'message': "error 26 at 0 depth lookup:unsupported certificate purpose",
            },
            "certs/invalid.crt",
            "certs/invalid.key",
            "certs/ca.crt",
        ),
        (
            {
                'check': "Checking for use of shortname as CN",
                'message': "shortname.crt is using a shortname for "
                "Common Name (CN) and cannot be used",
            },
            "certs/shortname.crt",
            "certs/shortname.key",
            "certs/ca.crt",
        ),
    ]

    @pytest.fixture(scope="module")
    def cert_data(self):
        """Get host name, scripts, and create working directory."""
        sat6_hostname = settings.server.hostname
        capsule_hostname = 'capsule.example.com'
        key_file_name = '{0}/{0}.key'.format(sat6_hostname)
        cert_file_name = '{0}/{0}.crt'.format(sat6_hostname)
        ca_bundle_file_name = 'cacert.crt'
        success_message = "Validation succeeded"
        cert_data = {
            'sat6_hostname': sat6_hostname,
            'capsule_hostname': capsule_hostname,
            'key_file_name': key_file_name,
            'cert_file_name': cert_file_name,
            'ca_bundle_file_name': ca_bundle_file_name,
            'success_message': success_message,
        }
        return cert_data

    @pytest.fixture()
    def cert_setup(self, cert_data):
        """copy all configuration files to satellite host for generating custom certs"""
        # Need a subdirectory under ssl-build with same name as Capsule name
        with get_connection(timeout=100) as connection:
            connection.run('mkdir ssl-build/{}'.format(cert_data['capsule_hostname']))
            # Ignore creation error, but assert directory exists
            assert connection.run('test -e ssl-build/{}'.format(cert_data['capsule_hostname']))
        upload_file(
            local_file=get_data_file('generate-ca.sh'),
            remote_file="generate-ca.sh",
        )
        upload_file(
            local_file=get_data_file('generate-crt.sh'),
            remote_file="generate-crt.sh",
        )
        upload_file(local_file=get_data_file('openssl.cnf'), remote_file="openssl.cnf")
        # create the CA cert.
        with get_connection(timeout=300) as connection:
            result = connection.run('echo 100001 > serial')
            result = connection.run("bash generate-ca.sh")
            assert result.return_code == 0
        # create the Satellite's cert
        with get_connection(timeout=300) as connection:
            result = connection.run(
                "yes | bash {} {}".format('generate-crt.sh', cert_data['sat6_hostname'])
            )
            assert result.return_code == 0

    @pytest.fixture()
    def certs_cleanup(self):
        """cleanup all cert configuration files"""
        yield
        files = [
            'cacert.crt',
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
            files = " ".join(files)
            result = connection.run(f"rm -rf {files}")
            assert result.return_code == 0

    @pytest.fixture()
    def generate_certs(self):
        """generate custom certs in satellite host"""
        upload_file(
            local_file=get_data_file('certs.sh'),
            remote_file="certs.sh",
        )
        upload_file(
            local_file=get_data_file('extensions.txt'),
            remote_file="extensions.txt",
        )
        with get_connection(timeout=300) as connection:
            result = connection.run("bash certs.sh")
            assert result.return_code == 0

    @pytest.fixture()
    def update_system_date(self):
        """update the satellite date to verify cert expiration"""
        result = ssh.command("date -s 'next year'")
        assert result.return_code == 0
        yield
        result = ssh.command("date -s 'last year'")
        assert result.return_code == 0, 'Failed to revert the date setting'

    def validate_output(self, result, cert_data):
        """Validate katello-certs-check output against a set.

        If CN part of Subject in the server cert matches the FQDN of the machine running
        the script, it is assumed the certs are meant for the Satellite and just
        "satellite-installer --scenario satellite" part of output should be printed.
        If FQDN doesn't match CN of Subject, just "capsule-certs-generate" part should be printed.
        """
        expected_result = {
            '--scenario',
            '--certs-server-cert',
            '--certs-server-key',
            '--certs-server-ca-cert',
            '--certs-update-server',
            '--certs-update-server-ca',
        }
        assert result.return_code == 0
        assert cert_data['success_message'] in result.stdout
        # validate all checks passed
        assert not any(flag for flag in re.findall(r"\[([A-Z]+)\]", result.stdout) if flag != 'OK')
        # validate options in output
        commands = result.stdout.split('To')
        commands.pop(0)
        options = []
        for cmd in commands:
            for i in cmd.split():
                if i.startswith('--'):
                    options.append(i)
        assert set(options) == expected_result

    @pytest.mark.tier1
    def test_positive_validate_katello_certs_check_output(
        self, cert_setup, cert_data, certs_cleanup
    ):
        """Validate that katello-certs-check generates correct output.

        :id: 4c9e4c6e-8d8e-4953-87a1-09cb55df3adf

        :steps:

            1. Use Jenkins provided custom certs
            2. Run katello-certs-check with the required valid arguments
               katello-certs-check -c CERT_FILE -k KEY_FILE -r REQ_FILE
               -b CA_BUNDLE_FILE
            3. Assert the output has correct commands with options

        :expectedresults: Katello-certs-check should generate correct commands
         with options.
        """
        with get_connection() as connection:
            result = connection.run(
                'katello-certs-check -c {} -k {} -b {}'.format(
                    cert_data['cert_file_name'],
                    cert_data['key_file_name'],
                    cert_data['ca_bundle_file_name'],
                ),
                output_format='plain',
            )
        self.validate_output(result, cert_data)

    @pytest.mark.tier1
    def test_katello_certs_check_output_wildcard_inputs(
        self, generate_certs, cert_data, certs_cleanup
    ):
        """Validate that katello-certs-check generates correct output with wildcard certs.

        :id: 7f9da806-5b23-11eb-b7ea-d46d6dd3b5b2

        :steps:

            1. Get valid wildcard certs from generate_certs
            2. Run katello-certs-check with the required valid arguments
               katello-certs-check -c CERT_FILE -k KEY_FILE -r REQ_FILE
               -b CA_BUNDLE_FILE
            3. Assert the output has correct commands with options

        :expectedresults: katello-certs-check should generate correct commands
         with options.
        """
        with get_connection() as connection:
            result = connection.run(
                'katello-certs-check -c certs/wildcard.crt -k certs/wildcard.key -b certs/ca.crt',
                output_format='plain',
            )
        self.validate_output(result, cert_data)

    @pytest.mark.parametrize("error, cert_file, key_file, ca_file", invalid_inputs)
    @pytest.mark.tier1
    def test_katello_certs_check_output_invalid_input(
        self, generate_certs, error, cert_file, key_file, ca_file, certs_cleanup
    ):
        """Validate that katello-certs-check raise the correct errors for invalid
         inputs

        :id: 37742f5e-598a-11eb-a349-d46d6dd3b5b2

        :steps:

            1. Get invalid certs from generate_certs
            2. Run katello-certs-check with the required valid arguments
               katello-certs-check -c CERT_FILE -k KEY_FILE -r REQ_FILE
               -b CA_BUNDLE_FILE
            3. Assert the output has correct error with message

        :expectedresults: Katello-certs-check should raise error when it receives the invalid
         inputs.
        """
        with get_connection() as connection:
            certs_check_result = connection.run(
                f'katello-certs-check -c {cert_file} -k {key_file} -b {ca_file}',
                output_format='plain',
            )
            for result in certs_check_result.stdout.split("\n\n"):
                if error['check'] in result:
                    assert '[FAIL]' in result
                    assert (
                        error['message']
                        in f'{certs_check_result.stdout} {certs_check_result.stderr}'
                    )
                    break
            else:
                pytest.fail('Failed to receive the error for invalid katello-cert-check')

    @pytest.mark.destructive
    def test_positive_update_katello_certs(self, cert_setup, cert_data, certs_cleanup):
        """Update certificates on a currently running satellite instance.

        :id: 0ddf6954-dc83-435e-b156-b567b877c2a5

        :steps:

            1. Use Jenkins provided custom certs
            2. Assert hammer ping reports running Satellite
            3. Update satellite with custom certs
            4. Assert output does not report SSL certificate error
            5. Assert all services are running


        :expectedresults: Katello-certs should be updated.

        :CaseAutomation: Automated
        """
        try:
            with get_connection(timeout=600) as connection:
                # Check for hammer ping SSL cert error
                result = connection.run('hammer ping')
                assert result.return_code == 0, 'Hammer Ping fail'
                result = connection.run(
                    'satellite-installer --scenario satellite '
                    '--certs-server-cert {} '
                    '--certs-server-key {} '
                    '--certs-server-ca-cert {} '
                    '--certs-update-server --certs-update-server-ca'.format(
                        cert_data['cert_file_name'],
                        cert_data['key_file_name'],
                        cert_data['ca_bundle_file_name'],
                    ),
                    timeout=500,
                )
                # assert no hammer ping SSL cert error
                result = connection.run('hammer ping')
                assert 'SSL certificate verification failed' not in result.stdout
                assert 'ok' in result.stdout[1]
                # assert all services are running
                result = connection.run('foreman-maintain health check --label services-up -y')
                assert result.return_code == 0, 'Not all services are running'
        finally:
            # revert to original certs
            with get_connection(timeout=600) as connection:
                result = connection.run(
                    'satellite-installer --scenario satellite --certs-reset', timeout=500
                )
                # Check for hammer ping SSL cert error
                result = connection.run('hammer ping')
                assert result.return_code == 0, 'Hammer Ping fail'
                # assert all services are running
                result = connection.run('foreman-maintain health check --label services-up -y')
                assert result.return_code == 0, 'Not all services are running'

    @pytest.mark.destructive
    def test_positive_generate_capsule_certs_using_absolute_path(
        self, cert_setup, cert_data, certs_cleanup
    ):
        """Create Capsule certs using absolute paths.

        :id: 72024757-be6f-49f0-8b88-c57c83f5e7e9

        :steps:

            1. Use Certificates generated in class setup
            2. Run capsule-certs-generate with custom certs and absolute path
               for --certs-tar
            3. Assert the certs tar file was created.
            4. Assert include cname in certificates when specified --foreman-proxy-cname'

        :expectedresults: Capsule certs are generated.

        :BZ: 1466688, 1899108, 1857176

        :CaseAutomation: Automated
        """
        with get_connection(timeout=300) as connection:
            connection.run('mkdir -p /root/capsule_cert')
            connection.run(
                f"cp {cert_data['ca_bundle_file_name']} /root/capsule_cert/ca_cert_bundle.pem"
            )
            connection.run(f"cp {cert_data['cert_file_name']} /root/capsule_cert/capsule_cert.pem")
            connection.run(
                f"cp {cert_data['key_file_name']} /root/capsule_cert/capsule_cert_key.pem"
            )
            result = connection.run(
                'capsule-certs-generate '
                f"--foreman-proxy-fqdn {cert_data['capsule_hostname']} "
                '--certs-tar /root/capsule_cert/capsule_certs_Abs.tar '
                '--server-cert /root/capsule_cert/capsule_cert.pem '
                '--server-key /root/capsule_cert/capsule_cert_key.pem '
                '--server-ca-cert /root/capsule_cert/ca_cert_bundle.pem '
                '--foreman-proxy-cname capsule.example1.com '
                '--certs-update-server'
            )
            assert result.return_code == 0, 'Capsule certs generate script failed.'
            # assert include cname in certificates when specified --foreman-proxy-cname'
            result = connection.run(
                'openssl x509 -in /root/ssl-build/capsule.example.com/'
                'capsule.example.com-foreman-client.crt -text | '
                'grep capsule.example1.com'
            )
            assert 'DNS:capsule.example1.com' in " ".join(result.stdout)
            # assert the certs.tar was built
            assert connection.run('test -e /root/capsule_cert/capsule_certs_Abs.tar')

    @pytest.mark.destructive
    @pytest.mark.upgrade
    def test_positive_generate_capsule_certs_using_relative_path(
        self, cert_setup, cert_data, certs_cleanup
    ):
        """Create Capsule certs using relative paths.

        :id: 50df0b87-d2d3-42fb-86d5-988ebaaa9ba3

        :steps:

            1. Use Certificates generated in class setup
            2. Run capsule-certs-generate with custom certs and relative path
               for --certs-tar
            3. Assert the certs tar file was created.

        :expectedresults: Capsule certs are generated.

        :BZ: 1466688, 1899108

        :CaseAutomation: Automated
        """
        with get_connection(timeout=300) as connection:
            connection.run('mkdir -p /root/capsule_cert')
            connection.run(
                'cp "{}" /root/capsule_cert/ca_cert_bundle.pem'.format(
                    cert_data['ca_bundle_file_name']
                )
            )
            connection.run(
                'cp "{}" /root/capsule_cert/capsule_cert.pem'.format(cert_data['cert_file_name'])
            )
            connection.run(
                'cp "{}" /root/capsule_cert/capsule_cert_key.pem'.format(
                    cert_data['key_file_name']
                )
            )
            result = connection.run(
                'capsule-certs-generate '
                '--foreman-proxy-fqdn {} '
                '--certs-tar ~/capsule_cert/capsule_certs_Rel.tar '
                '--server-cert ~/capsule_cert/capsule_cert.pem '
                '--server-key ~/capsule_cert/capsule_cert_key.pem '
                '--server-ca-cert ~/capsule_cert/ca_cert_bundle.pem '
                '--certs-update-server'.format(cert_data['capsule_hostname']),
                timeout=80,
            )
            assert result.return_code == 0, 'Capsule certs generate script failed.'
            # assert the certs.tar was built
            assert connection.run('test -e root/capsule_cert/capsule_certs_Rel.tar')

    @pytest.mark.tier1
    def test_negative_check_expiration_of_certificate(
        self, cert_setup, cert_data, update_system_date, certs_cleanup
    ):
        """Check expiration of certificate.

        :id: 0acce44f-ebe5-42e1-a74b-3d4d20b97946

        :steps:

            1. Generate the custom certificate
            2. Change the date of system to next year
            3. Run katello-certs-check with the required arguments

        :expectedresults: Checking expiration of certificate check should fail.

        :CaseAutomation: NotAutomated
        """
        with get_connection() as connection:
            result = connection.run(
                'katello-certs-check -c {} -k {} -b {}'.format(
                    cert_data['cert_file_name'],
                    cert_data['key_file_name'],
                    cert_data['ca_bundle_file_name'],
                ),
                output_format='plain',
            )
        messages = [
            'Checking expiration of certificate: \n[FAIL]',
            'Checking CA bundle against the certificate file: \n[FAIL]',
        ]
        checks = result.stdout.split('\n\n')
        for message in messages:
            for check in checks:
                if message == check:
                    assert message == check
                    break
            else:
                assert False, f'Failed, Unable to find message "{message}" in result'

    @pytest.mark.stubbed
    @pytest.mark.tier1
    def test_negative_validate_certificate_subject(self):
        """Validate certificate subject.

        :id: 4df45b22-d077-470e-a786-2be329cd68a7

        :steps:

            1. Have a certificate with invalid subject
            2. Run katello-certs-check with the required arguments

        :expectedresults: Check for validating the certificate subject should
            fail.

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier1
    def test_negative_check_private_key_match(self):
        """Validate private key match with certificate.

        :id: 358edbb3-08b0-47d7-856b-ce0d5ea95979

        :steps:

            1. Have KEY_FILE with invalid private key
            2. Run katello-certs-check with the required arguments

        :expectedresults: Private key match with the certificate should fail.

        :CaseAutomation: NotAutomated
        """


class TestCapsuleCertsCheckTestCase:
    """Implements Capsule certs checks on Satellite Server.

    Creates a temporary subdirectory and file under /var/tmp/
    on both Satellite Server's base system and on local host.
    """

    @pytest.fixture(scope="module")
    def file_setup(self):
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

    @pytest.mark.tier1
    def test_positive_validate_capsule_certificate(self, file_setup):
        """Check that Capsules cert handles additional proxy names.

        :id: 8b53fc3d-704f-44f4-899e-74654529bfcf

        :steps:

            1. Generate a Capsule certificate
            2. Confirm proxy server's FQDN for DNS is present
            3. Confirm that format of alternative names does not include []

        :expectedresults: Capsule certs has valid DNS values

        :BZ: 1747581

        :CaseAutomation: Automated
        """
        DNS_Check = False
        with get_connection(timeout=200) as connection:
            # extract the cert from the tar file
            result = connection.run(
                'tar -xf {0}/capsule_certs.tar --directory {0}/ '.format(file_setup['tmp_dir'])
            )
            assert result.return_code == 0, 'Extraction to working directory failed.'
            # Extract raw data from RPM to a file
            result = connection.run(
                'rpm2cpio {0}/ssl-build/{1}/'
                '{1}-qpid-router-server*.rpm'
                '>> {0}/ssl-build/{1}/cert-raw-data'.format(
                    file_setup['tmp_dir'], file_setup['capsule_hostname']
                )
            )
            # Extract the cert data from file cert-raw-data and write to cert-data
            result = connection.run(
                'openssl x509 -noout -text -in {0}/ssl-build/{1}/cert-raw-data'
                '>> {0}/ssl-build/{1}/cert-data'.format(
                    file_setup['tmp_dir'], file_setup['capsule_hostname']
                )
            )
            # use same location on remote and local for cert_file
            download_file(file_setup['caps_cert_file'])
            # search the file for the line with DNS
            with open(file_setup['caps_cert_file']) as file:
                for line in file:
                    if re.search(r'\bDNS:', line):
                        match = re.search(r'{}'.format(file_setup['capsule_hostname']), line)
                        assert match, "No proxy name found."
                        if is_open('BZ:1747581'):
                            DNS_Check = True
                        else:
                            match = re.search(r'\[]', line)
                            assert not match, "Incorrect parsing of alternative proxy name."
                            DNS_Check = True
                        break
                    # if no match for "DNS:" found, then raise error.
            assert DNS_Check, "Cannot find Subject Alternative Name"
