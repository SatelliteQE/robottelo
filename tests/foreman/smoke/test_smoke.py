"""Smoke tests to check installation health"""
import re

from robottelo.common import ssh
from robottelo.test import TestCase


class SELinuxTestCase(TestCase):
    """Checks SELinux installation status"""

    version_regex = re.compile(r'((\d\.?)+[-.]\d)')

    def test_selinux_foreman_module(self):
        """@Test: SELinux foreman module have the right version

        @Feature: Server health

        @Assert: Foreman RPM and SELinux module versions match

        """
        rpm_result = ssh.command('rpm -q foreman-selinux')
        self.assertEqual(rpm_result.return_code, 0)
        semodule_result = ssh.command('semodule -l | grep foreman')
        self.assertEqual(semodule_result.return_code, 0)

        # Sample rpm output: foreman-selinux-1.7.2.8-1.el7sat.noarch
        rpm_version = self.version_regex.search(
            ''.join(rpm_result.stdout)).group(1)
        # Sample semodule output: foreman        1.7.2.8.1
        semodule_version = self.version_regex.search(
            ''.join(semodule_result.stdout)).group(1)

        if rpm_version.endswith('-0'):
            # Examples of matching RPM and semodule version numbers:
            #
            # 1.7.2.8-0    1.7.2.8
            # 1.7.2.8-1    1.7.2.8.1
            # 1.7.2.8-2    1.7.2.8.2
            rpm_version = rpm_version[:-2]

        self.assertEqual(rpm_version.replace('-', '.'), semodule_version)
