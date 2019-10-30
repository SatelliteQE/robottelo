# -*- encoding: utf-8 -*-
"""Test class for ``katello-certs-check``.

:Requirement: katello-certs-check

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: Certificates

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
import os
import re

from fauxfactory import gen_string
from pathlib import Path

from robottelo.config import settings
from robottelo.ssh import get_connection, upload_file, download_file
from robottelo.test import TestCase
from robottelo.helpers import is_open
from robottelo.decorators import (
    destructive,
    run_in_one_thread,
    skip_if_not_set,
    stubbed,
    tier1,
    upgrade,
    )


@run_in_one_thread
class KatelloCertsCheckTestCase(TestCase):
    """Implements ``katello-certs-check`` tests.

    Depends on presence of custom certificates at path given
    in robottello.properties file.
    """

    @classmethod
    @skip_if_not_set('certs')
    def setUpClass(cls):
        """Get host name and credentials."""
        super(KatelloCertsCheckTestCase, cls).setUpClass()
        _, cls.ca_bundle_file_name = os.path.split(
            settings.certs.ca_bundle_file
        )
        _, cls.cert_file_name = os.path.split(settings.certs.cert_file)
        _, cls.key_file_name = os.path.split(settings.certs.key_file)
        cls.ca_bundle_file = settings.certs.ca_bundle_file
        cls.cert_file = settings.certs.cert_file
        cls.key_file = settings.certs.key_file
        cls.SUCCESS_MSG = "Validation succeeded"
        # uploads certs to satellite
        upload_file(
            local_file=settings.certs.ca_bundle_file,
            remote_file="/tmp/{0}".format(cls.ca_bundle_file_name)
        )
        upload_file(
            local_file=settings.certs.cert_file,
            remote_file="/tmp/{0}".format(cls.cert_file_name)
        )
        upload_file(
            local_file=settings.certs.key_file,
            remote_file="/tmp/{0}".format(cls.key_file_name)
        )

    def validate_output(self, result):
        """Validate katello-certs-check output against a set."""
        expected_result = set(
            ['--server-cert', '--server-key', '--certs-update-server',
                '--foreman-proxy-fqdn', '--certs-tar', '--server-ca-cert'])
        self.assertEqual(result.return_code, 0)
        self.assertIn(self.SUCCESS_MSG, result.stdout)
        # validate all checks passed
        self.assertEqual(any(
            flag for flag in re.findall(
                r"\[([A-Z]+)\]",
                result.stdout
            ) if flag != 'OK'), False)
        # validate options in output
        commands = result.stdout.split('To')
        commands.pop(0)
        options = []
        for cmd in commands:
            for i in cmd.split():
                if i.startswith('--'):
                    options.append(i)
        self.assertEqual(set(options), expected_result)

    @tier1
    def test_positive_validate_katello_certs_check_output(self):
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
                'katello-certs-check -c /tmp/{0} -k /tmp/{1} '
                '-b /tmp/{2}'.format(
                    self.cert_file_name,
                    self.key_file_name,
                    self.ca_bundle_file_name
                ),
                output_format='plain'
            )
            self.validate_output(result)

    @destructive
    def test_positive_update_katello_certs(self):
        """Update certificates on a currently running satellite instance.

        :id: 0ddf6954-dc83-435e-b156-b567b877c2a5

        :steps:

            1. Use Jenkins provided custom certs
            2. Assert hammer ping reports running Satellite
            3. Update satellite with custom certs
            4. Assert output does not report SSL certificate error
            5. Assert all services are running


        :expectedresults: Katello-certs should be updated.

        :CaseAutomation: automated
        """
        try:
            with get_connection(timeout=600) as connection:
                # Check for hammer ping SSL cert error
                result = connection.run('hammer ping')
                assert result.return_code == 0, 'Hammer Ping fail'
                result = connection.run(
                    'satellite-installer --scenario satellite '
                    '--certs-server-cert /tmp/server.valid.crt '
                    '--certs-server-key /tmp/server.key '
                    '--certs-server-ca-cert /tmp/rootCA.pem '
                    '--certs-update-server --certs-update-server-ca', timeout=500)
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
                    'satellite-installer --scenario satellite '
                    '--certs-reset', timeout=500)
                # Check for hammer ping SSL cert error
                result = connection.run('hammer ping')
                assert result.return_code == 0, 'Hammer Ping fail'
                # assert all services are running
                result = connection.run('foreman-maintain health check --label services-up -y')
                assert result.return_code == 0, 'Not all services are running'

    @destructive
    @stubbed()
    def test_positive_update_capsule_certs_using_absolute_path(self):
        """Update certificates on a currently running internal capsule.

        :id: 72024757-be6f-49f0-8b88-c57c83f5e7e9

        :steps:

            1. Generate custom certs
            2. Run katello-certs-check with the required valid arguments
            3. Run  capsule-certs-generate with custom certs and absolute path
               for --certs-tar

        :expectedresults: Katello-certs should be updated.

        :CaseAutomation: notautomated
        """

    @destructive
    @stubbed()
    @upgrade
    def test_positive_update_capsule_certs_using_relative_path(self):
        """Update certificates on a currently running internal capsule.

        :id: 50df0b87-d2d3-42fb-86d5-988ebaaa9ba3

        :steps:

            1. Generate custom certs
            2. Run katello-certs-check with the required valid arguments
            3. Run  capsule-certs-generate with custom certs and relative path
               for --certs-tar

        :expectedresults: Katello-certs should be updated.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_check_expiration_of_certificate(self):
        """Check expiration of certificate.

        :id: 0acce44f-ebe5-42e1-a74b-3d4d20b97946

        :steps:

            1. Use expired certificate
            2. Run katello-certs-check with the required arguments

        :expectedresults: Checking expiration of certificate check should fail.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_check_ca_bundle(self):
        """Check ca bundle file that contains invalid data.

        :id: ca89e3b9-db15-413b-a395-eaa80bd30c9c

        :steps:

            1. Have in the CA bundle any other data instead of the cert.request
            2. Run katello-certs-check with the required arguments

        :expectedresults: Checking ca bundle against the cert file should fail.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_validate_certificate_subject(self):
        """Validate certificate subject.

        :id: 4df45b22-d077-470e-a786-2be329cd68a7

        :steps:

            1. Have a certificate with invalid subject
            2. Run katello-certs-check with the required arguments

        :expectedresults: Check for validating the certificate subject should
            fail.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_check_private_key_match(self):
        """Validate private key match with certificate.

        :id: 358edbb3-08b0-47d7-856b-ce0d5ea95979

        :steps:

            1. Have KEY_FILE with invalid private key
            2. Run katello-certs-check with the required arguments

        :expectedresults: Private key match with the certificate should fail.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_check_expiration_of_ca_bundle(self):
        """Validate expiration of ca bundle file.

        :id: 09276306-41dd-49b9-953c-3ba74c74790d

        :steps:

            1. Have expired CA_BUNDLE_FILE
            2. Run katello-certs-check with the required arguments

        :expectedresults: Checking expiration of CA bundle should fail.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_check_for_non_ascii_characters(self):
        """Validate non ascii character in certs.

        :id: c6a5e60d-e6d6-420c-b153-c6edb4ad7c99

        :steps:

            1. Create certs with ascii characters
            2. Run katello-certs-check with the required arguments

        :expectedresults: Check for non ascii character should fail gracefully
                          e.g. no traces.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_validate_without_req_file_output(self):
        """Check katello-certs-check without -r REQ_FILE generates correct command.

        :id: b7d782eb-28ea-47e9-8661-1b5e5201c82f

        :steps:

            1. Generate custom certs
            2. Run katello-certs-check with the required valid arguments and
               without -r REQ_FILE option
               katello-certs-check -c CERT_FILE -k KEY_FILE -b CA_BUNDLE_FILE
            3. Assert the output has correct commands with options

        :expectedresults: Katello-certs-check should generate correct commands
            with options.

        :CaseAutomation: notautomated
        """

    @tier1
    def test_positive_validate_capsule_certificate(self):
        """Check that Capsules cert handles additional proxy names.

        :id: 8b53fc3d-704f-44f4-899e-74654529bfcf

        :steps:

            1. Generate a Capsule certificate
            2. Confirm proxy server's FQDN for DNS is present
            3. Confirm that format of alternative names does not include []

        :expectedresults: Capsule certs has valid DNS values

        :BZ: 1747581

        :CaseAutomation: automated
        """
        DNS_Check = False
        tmp_dir = '/var/tmp/{0}'.format(gen_string('alpha', 6))
        cert_file = '{0}/ssl-build/capsule.example.com/cert-data'.format(tmp_dir)
        # Use same path locally as on remote for storing files
        Path(f'{tmp_dir}/ssl-build/capsule.example.com/').mkdir(parents=True, exist_ok=True)
        with get_connection(timeout=200) as connection:
            result = connection.run(
                'mkdir {0}'.format(tmp_dir))
            assert result.return_code == 0, 'Create working directory failed.'
            result = connection.run(
                'capsule-certs-generate '
                '--foreman-proxy-fqdn capsule.example.com '
                '--certs-tar {0}/capsule_certs.tar '.format(tmp_dir), timeout=100)
            # extract the cert from the tar file
            result = connection.run('tar -xf {0}/capsule_certs.tar'
                                    ' --directory {0}/ '.format(tmp_dir))
            assert result.return_code == 0, 'Extraction to working directory failed.'
            # Extract raw data from RPM to a file
            result = connection.run(
                'rpm2cpio {0}/ssl-build/capsule.example.com/'
                'capsule.example.com-qpid-router-server*.rpm'
                '>> {0}/ssl-build/capsule.example.com/cert-raw-data'
                .format(tmp_dir))
            # Extract the cert data from file cert-raw-data and write to cert-data
            result = connection.run(
                'openssl x509 -noout -text -in {0}/ssl-build/capsule.example.com/cert-raw-data'
                '>> {0}/ssl-build/capsule.example.com/cert-data'.format(tmp_dir))
            # use same location on remote and local for cert_file
            download_file(cert_file)
            # search the file for the line with DNS
            with open(cert_file, "r") as file:
                for line in file:
                    if re.search(r'\bDNS:', line):
                        self.logger.info('Found the line with alternative names for DNS')
                        match = re.search(r'capsule.example.com', line)
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
