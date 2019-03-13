# -*- encoding: utf-8 -*-
"""Test class for ``katello-certs-check``

:Requirement: katello-certs-check

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
from robottelo.config import settings
from robottelo.decorators import destructive, stubbed, tier1, upgrade
from robottelo.ssh import get_connection, upload_file
from robottelo.test import TestCase

import os
import re


class KatelloCertsCheckTestCase(TestCase):
    """Implements ``katello-certs-check`` tests"""

    @classmethod
    def setUpClass(cls):
        """Get hostname and credentials"""
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
        """Validate that katello-certs-check generate correct output

        :id: 4c9e4c6e-8d8e-4953-87a1-09cb55df3adf

        :steps:

            1. Generate custom certs
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
    @stubbed()
    def test_positive_update_katello_certs(self):
        """Update certificates on a currently running satellite instance

        :id: 0ddf6954-dc83-435e-b156-b567b877c2a5

        :steps:

            1. Generate custom certs
            2. Run katello-certs-check with the required valid arguments
            3. Update satellite with custom certs
            4. Assert output is having correct capsule-certs-generate commands

        :expectedresults: Katello-certs should be updated.

        :CaseAutomation: notautomated
        """

    @destructive
    @stubbed()
    def test_positive_update_capsule_certs_using_absolute_path(self):
        """Update certificates on a currently running internal capsule

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
        """Update certificates on a currently running internal capsule

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
        """Check expiration of certificate

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
        """Check ca bundle file that contains invalid data

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
        """Validate certificate subject

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
        """Validate private key match with certificate

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
        """Validate expiration of ca bundle file

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
        """Validate non ascii character in certs

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
        """Check katello-certs-check without -r REQ_FILE generate
         correct command

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
