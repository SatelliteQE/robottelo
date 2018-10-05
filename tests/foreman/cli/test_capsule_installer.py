# -*- encoding: utf-8 -*-
"""Test for capsule installer CLI

:Requirement: Capsule Installer

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os
from tempfile import mkstemp

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.capsule import Capsule
from robottelo.config import settings
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier3,
)
from robottelo.helpers import extract_capsule_satellite_installer_command
from robottelo.test import CLITestCase
from robottelo.vm_capsule import CapsuleVirtualMachine


class CapsuleInstallerTestCase(CLITestCase):
    """Test class for capsule installer CLI"""

    @stubbed()
    def test_positive_basic(self):
        """perform a basic install of capsule.

        :id: 47445685-5924-4980-89d0-bbb2fb608f4d

        :Steps:

            1. Assure your target capsule has ONLY the Capsule repo enabled. In
               other words, the Satellite repo itself is not enabled by
               default.
            2. attempt to perform a basic, functional install the capsule using
               `capsule-installer`.

        :expectedresults: product is installed

        :caseautomation: notautomated

        """

    @stubbed()
    def test_positive_option_qpid_router(self):
        """assure the --qpid-router flag can be used in
        capsule-installer to enable katello-agent functionality via
        remote clients

        :id: d040a72d-72b2-41cf-b14e-a8e37e80200d

        :Steps: Install capsule-installer with the '--qpid-router=true` flag

        :expectedresults: Capsule installs correctly and qpid functionality is
            enabled.

        :caseautomation: notautomated

        """

    @stubbed()
    def test_positive_option_reverse_proxy(self):
        """ assure the --reverse-proxy flag can be used in
        capsule-installer to enable katello-agent functionality via
        remote clients

        :id: 756fd76a-0183-4637-93c8-fe7c375be751

        :Steps: Install using the '--reverse-proxy=true' flag

        :expectedresults: Capsule installs correctly and functionality is
            enabled.

        :caseautomation: notautomated

        """

    @stubbed()
    def test_negative_invalid_parameters(self):
        """invalid (non-boolean) parameters cannot be passed to flag

        :id: f4366c87-e436-42b4-ada4-55f0e66a481e

        :Steps: attempt to provide a variety of invalid parameters to installer
            (strings, numerics, whitespace, etc.)

        :expectedresults: user is told that such parameters are invalid and
            install aborts.

        :caseautomation: notautomated

        """

    @stubbed()
    def test_negative_option_parent_reverse_proxy_port(self):
        """invalid (non-integer) parameters cannot be passed to flag

        :id: a1af16d3-84da-4e94-818e-90bc82cc5698

        :Setup: na

        :Steps: attempt to provide a variety of invalid parameters to
            --parent-reverse-proxy-port flag (strings, numerics, whitespace,
            etc.)

        :expectedresults: user told parameters are invalid; install aborts.

        :caseautomation: notautomated

        """

    @stubbed()
    def test_positive_option_parent_reverse_proxy(self):
        """ valid parameters can be passed to --parent-reverse-proxy
        (true)

        :id: a905f4ca-a729-4efb-84fc-43923737f75b

        :Setup: note that this requires an accompanying, valid port value

        :Steps: Attempt to provide a value of "true" to --parent-reverse-proxy

        :expectedresults: Install commences/completes with proxy installed
            correctly.

        :caseautomation: notautomated

        """

    @stubbed()
    def test_positive_option_parent_reverse_proxy_port(self):
        """valid parameters can be passed to
        --parent-reverse-proxy-port (integer)

        :id: 32238045-53e2-4ed4-ac86-57917e7aedcd

        :Setup: note that this requires an accompanying, valid host for proxy
            parameter

        :Steps: Attempt to provide a valid proxy port # to flag

        :expectedresults: Install commences and completes with proxy installed
            correctly.

        :caseautomation: notautomated

        """

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_reinstall_on_same_node_after_remove(self):
        """Reinstall capsule on the same node after remove

        :id: fac35a44-0bc9-44e9-a2c3-398e1aa9900c

        :customerscenario: true

        :expectedresults: The capsule successfully reinstalled

        :BZ: 1327442

        :CaseLevel: System
        """
        # Note: capsule-remove has been replaced by katello-remove
        with CapsuleVirtualMachine() as capsule_vm:
            # ensure that capsule refresh-features succeed
            with self.assertNotRaises(CLIReturnCodeError):
                Capsule.refresh_features(
                    {'name': capsule_vm._capsule_hostname})
            # katello-remove command request to confirm by typing Y and then by
            # typing remove
            result = capsule_vm.run("printf 'Y\nremove\n' | katello-remove")
            self.assertEqual(result.return_code, 0)
            # ensure that capsule refresh-features fail
            with self.assertRaises(CLIReturnCodeError):
                Capsule.refresh_features(
                    {'name': capsule_vm._capsule_hostname})
            # reinstall katello certs as they have been removed
            capsule_vm.install_katello_ca()
            # install satellite-capsule package
            result = capsule_vm.run('yum install -y satellite-capsule')
            self.assertEqual(result.return_code, 0)
            # generate capsule certs and installer command
            cert_file_path = '/tmp/{0}-certs.tar'.format(capsule_vm.hostname)
            result = ssh.command(
                'capsule-certs-generate '
                '--foreman-proxy-fqdn {0} '
                '--certs-tar {1}'
                .format(capsule_vm.hostname, cert_file_path)
            )
            self.assertEqual(result.return_code, 0)
            # retrieve the installer command from the result output
            installer_cmd = extract_capsule_satellite_installer_command(
                result.stdout
            )
            # copy the generated certs to capsule vm
            _, temporary_local_cert_file_path = mkstemp(suffix='-certs.tar')
            ssh.download_file(
                remote_file=cert_file_path,
                local_file=temporary_local_cert_file_path,
                hostname=settings.server.hostname
            )
            ssh.upload_file(
                local_file=temporary_local_cert_file_path,
                remote_file=cert_file_path,
                hostname=capsule_vm.ip_addr
            )
            # delete the temporary file
            os.remove(temporary_local_cert_file_path)
            result = capsule_vm.run(installer_cmd, timeout=1500)
            self.assertEqual(result.return_code, 0)
            # ensure that capsule refresh-features succeed
            with self.assertNotRaises(CLIReturnCodeError):
                Capsule.refresh_features(
                    {'name': capsule_vm.hostname})
