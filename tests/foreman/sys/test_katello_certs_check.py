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

import pytest


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
                'message': 'error 26 at 0 depth lookup: unsupported certificate purpose',
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
        cert_data, target_sat = cert_setup_teardown
        hostname = target_sat.hostname
        command = (
            f'katello-certs-check -c {hostname}/{hostname}.crt '
            f'-k {hostname}/{hostname}.key -b cacert.crt'
        )
        result = target_sat.execute(command)
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
        cert_data, target_sat = cert_setup_teardown
        command = 'katello-certs-check -c certs/wildcard.crt -k certs/wildcard.key -b certs/ca.crt'
        result = target_sat.execute(command)
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
        cert_data, target_sat = cert_setup_teardown
        command = f'katello-certs-check -c {cert_file} -k {key_file} -b {ca_file}'
        certs_check_result = target_sat.execute(command)
        for result in certs_check_result.stdout.split('\n\n'):
            if error['check'] in result:
                assert '[FAIL]' in result
                assert (
                    error['message'] in f'{certs_check_result.stdout} {certs_check_result.stderr}'
                )
                break
        else:
            pytest.fail('Failed to receive the error for invalid katello-cert-check')

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
        cert_data, target_sat = cert_setup_teardown
        hostname = target_sat.hostname
        target_sat.execute("date -s 'next year'")
        command = (
            f'katello-certs-check -c {hostname}/{hostname}.key '
            f'-k {hostname}/{hostname}.crt -b cacert.crt'
        )
        result = target_sat.execute(command)
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
        target_sat.execute("date -s 'last year'")

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
