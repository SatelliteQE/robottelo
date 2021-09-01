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
from attrdict import AttrDict
from broker.broker import VMBroker
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.hosts import ContentHost
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
                'check': 'Checking CA bundle against the certificate file',
                'message': 'error 26 at 0 depth lookup:unsupported certificate purpose',
            },
            'certs/invalid.crt',
            'certs/invalid.key',
            'certs/ca.crt',
        ),
        (
            {
                'check': 'Checking for use of shortname as CN',
                'message': 'shortname.crt is using a shortname for '
                'Common Name (CN) and cannot be used',
            },
            'certs/shortname.crt',
            'certs/shortname.key',
            'certs/ca.crt',
        ),
    ]

    @pytest.fixture(scope='module')
    def cert_data(self):
        """common data is used across the fixtures"""
        capsule_hostname = 'capsule.example.com'
        ca_bundle_file_name = 'cacert.crt'
        success_message = "Validation succeeded"
        cert_data = {
            'capsule_hostname': capsule_hostname,
            'ca_bundle_file_name': ca_bundle_file_name,
            'success_message': success_message,
        }
        return cert_data

    @pytest.fixture()
    def vm_setup(self, request, cert_data):
        """Create VM and register content host"""
        target_cores = request.param.get('target_cores', 1)
        target_memory = request.param.get('target_memory', '1GiB')
        with VMBroker(
            nick=request.param['nick'],
            host_classes={'host': ContentHost},
            target_cores=target_cores,
            target_memory=target_memory,
        ) as host:
            cert_data['key_file_name'] = f'{host.hostname}/{host.hostname}.key'
            cert_data['cert_file_name'] = f'{host.hostname}/{host.hostname}.crt'
            host.custom_cert_generate(cert_data['capsule_hostname'])
            yield cert_data, host

    @pytest.fixture
    def cert_setup_destructive_teardown(self, destructive_sat, cert_data):
        """Get host name, scripts, and create working directory."""
        cert_data['key_file_name'] = f'{destructive_sat.hostname}/{destructive_sat.hostname}.key'
        cert_data['cert_file_name'] = f'{destructive_sat.hostname}/{destructive_sat.hostname}.crt'
        destructive_sat.custom_cert_generate(cert_data['capsule_hostname'])
        yield cert_data, destructive_sat
        destructive_sat.custom_certs_cleanup()

    @pytest.fixture(scope='module')
    def cert_setup_teardown(self, default_sat, cert_data):
        """Get host name, scripts, and create working directory."""
        cert_data['key_file_name'] = f'{default_sat.hostname}/{default_sat.hostname}.key'
        cert_data['cert_file_name'] = f'{default_sat.hostname}/{default_sat.hostname}.crt'
        default_sat.custom_cert_generate(cert_data['capsule_hostname'])
        yield cert_data, default_sat
        default_sat.custom_certs_cleanup()

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
        assert result.status == 0
        assert cert_data['success_message'] in result.stdout

        # validate correct installer used
        pattern, count = 'satellite-installer --scenario satellite', 2
        assert len(re.findall(pattern, result.stdout)) == count
        pattern, count = 'foreman-installer --scenario katello', 0
        assert len(re.findall(pattern, result.stdout)) == count

        # validate all checks passed
        assert not any(flag for flag in re.findall(r'\[([A-Z]+)\]', result.stdout) if flag != 'OK')
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
    def test_positive_validate_katello_certs_check_output(self, cert_setup_teardown):
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
        cert_data, default_sat = cert_setup_teardown
        hostname = default_sat.hostname
        command = (
            f'katello-certs-check -c {hostname}/{hostname}.crt '
            f'-k {hostname}/{hostname}.key -b cacert.crt'
        )
        result = default_sat.execute(command)
        self.validate_output(result, cert_data)

    @pytest.mark.tier1
    def test_katello_certs_check_output_wildcard_inputs(self, cert_setup_teardown):
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
        cert_data, default_sat = cert_setup_teardown
        command = 'katello-certs-check -c certs/wildcard.crt -k certs/wildcard.key -b certs/ca.crt'
        result = default_sat.execute(command)
        self.validate_output(result, cert_data)

    @pytest.mark.parametrize('error, cert_file, key_file, ca_file', invalid_inputs)
    @pytest.mark.tier1
    def test_katello_certs_check_output_invalid_input(
        self,
        cert_setup_teardown,
        error,
        cert_file,
        key_file,
        ca_file,
    ):
        """Validate that katello-certs-check raise the correct errors for invalid
         inputs

        :id: 37742f5e-598a-11eb-a349-d46d6dd3b5b2

        :parametrized: yes

        :steps:

            1. Get invalid certs from generate_certs
            2. Run katello-certs-check with the required valid arguments
               katello-certs-check -c CERT_FILE -k KEY_FILE -r REQ_FILE
               -b CA_BUNDLE_FILE
            3. Assert the output has correct error with message

        :expectedresults: Katello-certs-check should raise error when it receives the invalid
         inputs.
        """
        cert_data, default_sat = cert_setup_teardown
        command = f'katello-certs-check -c {cert_file} -k {key_file} -b {ca_file}'
        certs_check_result = default_sat.execute(command)
        for result in certs_check_result.stdout.split('\n\n'):
            if error['check'] in result:
                assert '[FAIL]' in result
                assert (
                    error['message'] in f'{certs_check_result.stdout} {certs_check_result.stderr}'
                )
                break
        else:
            pytest.fail('Failed to receive the error for invalid katello-cert-check')

    @pytest.mark.destructive
    def test_positive_update_katello_certs(self, cert_setup_destructive_teardown):
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
            cert_data, satellite = cert_setup_destructive_teardown
            result = satellite.execute('hammer ping')
            assert result.status == 0, f'Hammer Ping failed:\n{result.stderr}'
            command = (
                'satellite-installer --scenario satellite '
                f'--certs-server-cert "/root/{cert_data["cert_file_name"]}" '
                f'--certs-server-key "/root/{cert_data["key_file_name"]}" '
                f'--certs-server-ca-cert "/root/{cert_data["ca_bundle_file_name"]}" '
                '--certs-update-server --certs-update-server-ca'
            )
            result = satellite.execute(command)
            assert result.status == 0
            # assert no hammer ping SSL cert error
            result = satellite.execute('hammer ping')
            assert 'SSL certificate verification failed' not in result.stdout
            assert result.stdout.count('ok') == 7
            # assert all services are running
            result = satellite.execute('foreman-maintain health check --label services-up -y')
            assert result.status == 0, 'Not all services are running'
        finally:
            # revert to original certs
            command = 'satellite-installer --scenario satellite --certs-reset'
            result = satellite.execute(command)
            assert result.status == 0
            # Check for hammer ping SSL cert error
            result = satellite.execute('hammer ping')
            assert result.status == 0, f'Hammer Ping failed:\n{result.stderr}'
            # assert all services are running
            result = satellite.execute('foreman-maintain health check --label services-up -y')
            assert result.status == 0, 'Not all services are running'

    @pytest.mark.destructive
    @pytest.mark.parametrize(
        'vm_setup',
        [{'nick': 'rhel7', 'target_memory': '20GiB', 'target_cores': 4}],
        ids=['rhel7'],
        indirect=True,
    )
    def test_positive_install_sat_with_katello_certs(self, vm_setup):
        """Update certificates on a currently running satellite instance.

        :id: 47e3a57f-d7a2-40d2-bbc7-d1bb3d79a7e1

        :steps:

            1. Generate the custom certs on RHEL 7 machine
            2. Install satellite with custom certs
            3. Assert output does not report SSL certificate error
            4. Assert all services are running


        :expectedresults: Satellite should be installed using the custom certs.

        :CaseAutomation: Automated
        """
        cert_data, rhel_vm = vm_setup
        rhel_vm.execute(
            f'yum -y localinstall {settings.repos.dogfood_repo_host}'
            f'/pub/katello-ca-consumer-latest.noarch.rpm'
        )
        rhel_vm.execute(
            f'subscription-manager register --org {settings.subscription.dogfood_org} '
            f'--activationkey "{settings.subscription.dogfood_activationkey}" '
        )
        rhel_vm.execute('yum -y update')
        result = rhel_vm.execute('yum -y install satellite')
        assert result.status == 0
        command = (
            'satellite-installer --scenario satellite '
            f'--certs-server-cert "/root/{cert_data["cert_file_name"]}" '
            f'--certs-server-key "/root/{cert_data["key_file_name"]}" '
            f'--certs-server-ca-cert "/root/{cert_data["ca_bundle_file_name"]}" '
        )
        result = rhel_vm.execute(command, timeout=2200)
        assert result.status == 0
        # assert no hammer ping SSL cert error
        result = rhel_vm.execute('hammer ping')
        assert 'SSL certificate verification failed' not in result.stdout
        assert result.stdout.count('ok') == 7
        # assert all services are running
        result = rhel_vm.execute('foreman-maintain health check --label services-up -y')
        assert result.status == 0, 'Not all services are running'

    @pytest.mark.destructive
    def test_positive_generate_capsule_certs_using_absolute_path(
        self, cert_setup_destructive_teardown
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

        :customerscenario: true

        :BZ: 1466688, 1899108, 1857176

        :CaseAutomation: Automated
        """
        cert_data, satellite = cert_setup_destructive_teardown
        satellite.execute('mkdir -p /root/capsule_cert')
        satellite.execute(
            f'cp {cert_data["ca_bundle_file_name"]} /root/capsule_cert/ca_cert_bundle.pem'
        )
        satellite.execute(f'cp {cert_data["cert_file_name"]} /root/capsule_cert/capsule_cert.pem')
        satellite.execute(
            f'cp {cert_data["key_file_name"]} /root/capsule_cert/capsule_cert_key.pem'
        )
        result = satellite.execute(
            'capsule-certs-generate '
            f'--foreman-proxy-fqdn {cert_data["capsule_hostname"]} '
            '--certs-tar /root/capsule_cert/capsule_certs_Abs.tar '
            '--server-cert /root/capsule_cert/capsule_cert.pem '
            '--server-key /root/capsule_cert/capsule_cert_key.pem '
            '--server-ca-cert /root/capsule_cert/ca_cert_bundle.pem '
            '--foreman-proxy-cname capsule.example1.com '
            '--certs-update-server'
        )
        assert result.status == 0, 'Capsule certs generate script failed.'
        # assert include cname in certificates when specified --foreman-proxy-cname'
        result = satellite.execute(
            'openssl x509 -in /root/ssl-build/capsule.example.com/'
            'capsule.example.com-foreman-client.crt -text | '
            'grep capsule.example1.com'
        )
        assert 'DNS:capsule.example1.com' in result.stdout
        # assert the certs.tar was built
        assert satellite.execute('test -e /root/capsule_cert/capsule_certs_Abs.tar')

    @pytest.mark.destructive
    @pytest.mark.upgrade
    def test_positive_generate_capsule_certs_using_relative_path(
        self, cert_setup_destructive_teardown
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
        cert_data, satellite = cert_setup_destructive_teardown
        satellite.execute('mkdir -p /root/capsule_cert')
        satellite.execute(
            f'cp "{cert_data["ca_bundle_file_name"]}" /root/capsule_cert/ca_cert_bundle.pem'
        )
        satellite.execute(f'cp "{cert_data["cert_file_name"]}" /root/capsule_cert/capsule_cert.pem')
        satellite.execute(
            f'cp "{cert_data["key_file_name"]}" /root/capsule_cert/capsule_cert_key.pem'
        )
        result = satellite.execute(
            'capsule-certs-generate '
            f'--foreman-proxy-fqdn {cert_data["capsule_hostname"]} '
            '--certs-tar ~/capsule_cert/capsule_certs_Rel.tar '
            '--server-cert ~/capsule_cert/capsule_cert.pem '
            '--server-key ~/capsule_cert/capsule_cert_key.pem '
            '--server-ca-cert ~/capsule_cert/ca_cert_bundle.pem '
            '--certs-update-server',
        )
        assert result.status == 0, 'Capsule certs generate script failed.'
        # assert the certs.tar was built
        assert satellite.execute('test -e root/capsule_cert/capsule_certs_Rel.tar')

    @pytest.mark.tier1
    def test_negative_check_expiration_of_certificate(self, cert_setup_teardown):
        """Check expiration of certificate.

        :id: 0acce44f-ebe5-42e1-a74b-3d4d20b97946

        :steps:

            1. Generate the custom certificate
            2. Change the date of system to next year
            3. Run katello-certs-check with the required arguments

        :expectedresults: Checking expiration of certificate check should fail.

        :CaseAutomation: NotAutomated
        """
        cert_data, default_sat = cert_setup_teardown
        hostname = default_sat.hostname
        default_sat.execute("date -s 'next year'")
        command = (
            f'katello-certs-check -c {hostname}/{hostname}.key '
            f'-k {hostname}/{hostname}.crt -b cacert.crt'
        )
        result = default_sat.execute(command)
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
        default_sat.execute("date -s 'last year'")

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

    @pytest.fixture
    def capsule_certs_teardown(self, default_sat):
        """Create working directory and file."""
        capsule = AttrDict({'hostname': 'capsule.example.com'})
        tmp_dir = '/var/tmp/{}'.format(gen_string('alpha', 6))
        caps_cert_file = f'{tmp_dir}/ssl-build/capsule.example.com/cert-data'
        # Use same path locally as on remote for storing files
        Path(f'{tmp_dir}/ssl-build/capsule.example.com/').mkdir(parents=True, exist_ok=True)
        result = default_sat.execute(f'mkdir {tmp_dir}')
        assert result.status == 0, 'Create working directory failed.'
        # Generate a Capsule cert for capsule.example.com
        default_sat.capsule_certs_generate(capsule, f'{tmp_dir}/capsule_certs.tar')
        return {
            'tmp_dir': tmp_dir,
            'caps_cert_file': caps_cert_file,
            'capsule_hostname': capsule.hostname,
        }, default_sat

    @pytest.mark.destructive
    @pytest.mark.tier1
    def test_positive_validate_capsule_certificate(self, capsule_certs_teardown):
        """Check that Capsules cert handles additional proxy names.

        :id: 8b53fc3d-704f-44f4-899e-74654529bfcf

        :customerscenario: true

        :steps:

            1. Generate a Capsule certificate
            2. Confirm proxy server's FQDN for DNS is present
            3. Confirm that format of alternative names does not include []

        :expectedresults: Capsule certs has valid DNS values

        :BZ: 1747581

        :CaseAutomation: Automated
        """
        file_setup, default_sat = capsule_certs_teardown
        DNS_Check = False
        # extract the cert from the tar file
        result = default_sat.execute(
            f'tar -xf {file_setup["tmp_dir"]}/capsule_certs.tar '
            f'--directory {file_setup["tmp_dir"]}/ '
        )
        assert result.status == 0, 'Extraction to working directory failed.'
        # Extract raw data from RPM to a file
        default_sat.execute(
            'rpm2cpio {0}/ssl-build/{1}/'
            '{1}-qpid-router-server*.rpm'
            '>> {0}/ssl-build/{1}/cert-raw-data'.format(
                file_setup['tmp_dir'], file_setup['capsule_hostname']
            )
        )
        # Extract the cert data from file cert-raw-data and write to cert-data
        default_sat.execute(
            'openssl x509 -noout -text -in {0}/ssl-build/{1}/cert-raw-data'
            '>> {0}/ssl-build/{1}/cert-data'.format(
                file_setup['tmp_dir'], file_setup['capsule_hostname']
            )
        )
        # use same location on remote and local for cert_file
        default_sat.get(file_setup['caps_cert_file'])
        # search the file for the line with DNS
        with open(file_setup['caps_cert_file']) as file:
            for line in file:
                if re.search(r'\bDNS:', line):
                    match = re.search(r'{}'.format(file_setup['capsule_hostname']), line)
                    assert match, 'No proxy name found.'
                    if is_open('BZ:1747581'):
                        DNS_Check = True
                    else:
                        match = re.search(r'\[]', line)
                        assert not match, 'Incorrect parsing of alternative proxy name.'
                        DNS_Check = True
                    break
                # if no match for "DNS:" found, then raise error.
        assert DNS_Check, 'Cannot find Subject Alternative Name'
