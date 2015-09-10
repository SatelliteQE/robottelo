"""Smoke tests to check installation health"""
import re

from itertools import izip
from robottelo import ssh
from robottelo.helpers import get_host_info, get_server_credentials
from robottelo.log import LogFile
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

    def test_installer_check_services(self):
        """@Test: Services services start correctly

        @Feature: Installer

        @Assert: All services {'elasticsearch', 'foreman-proxy',
        'foreman-tasks', 'httpd', 'mongod', 'postgresql', 'pulp_celerybeat',
        'pulp_resource_manager', 'pulp_workers', 'qdrouterd', 'qpidd',
        'tomcat'} are started

        """
        services = (
            'elasticsearch',
            'foreman-proxy',
            'foreman-tasks',
            'httpd',
            'mongod',
            'postgresql',
            'pulp_celerybeat',
            'pulp_resource_manager',
            'pulp_workers',
            'qdrouterd',
            'qpidd',
            'tomcat',
        )

        # check `services` status using service command
        if get_host_info()[1] >= 7:
            status_format = 'systemctl status {0}'
        else:
            status_format = 'service {0} status'

        for service in services:
            result = ssh.command(status_format.format(service))
            self.assertEqual(result.return_code, 0)
            self.assertEqual(len(result.stderr), 0)

        # check status reported by hammer ping command
        result = ssh.command(u'hammer -u {0[0]} -p {0[1]} ping'.format(
            get_server_credentials()
        ))

        # iterate over the lines grouping every 3 lines
        # example [1, 2, 3, 4, 5, 6] will return [(1, 2, 3), (4, 5, 6)]
        for service, status, server_response in izip(
                *[iter(result.stdout)] * 3):
            service = service.replace(':', '').strip()
            status = status.split(':')[1].strip().lower()
            server_response = server_response.split(':', 1)[1].strip()
            self.assertEqual(
                status, 'ok',
                '{0} responded with {1}'.format(service, server_response)
            )

    def test_installer_logfile_check(self):
        """@Test: Look for ERROR or FATAL references in logfiles

        @Feature: Installer

        @Steps:

        1. search all relevant logfiles for ERROR/FATAL

        @Assert: No ERROR/FATAL notifcations occur in {katello-jobs, tomcat6,
        foreman, pulp, passenger-analytics, httpd, foreman_proxy,
        elasticsearch, postgresql, mongod} logfiles.

        """
        logfiles = (
            {
                'path': '/var/log/candlepin/error.log',
                'pattern': r'ERROR'
            },
            {
                'path': '/var/log/katello-installer/katello-installer.log',
                'pattern': r'\[\s*(ERROR|FATAL)'
            },
        )

        for logfile in logfiles:
            try:
                log = LogFile(logfile['path'], logfile['pattern'])
            except IOError:
                self.fail(
                    'Could not find {0} file on server'.format(logfile['path'])
                )
            self.assertEqual(len(log.filter()), 0)
