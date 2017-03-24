"""Smoke tests to check installation health

@Requirement: Installer

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: INSTALLER

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
import re

from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION
from robottelo.helpers import get_host_info
from robottelo.log import LogFile
from robottelo.test import TestCase
from six.moves import zip


class SELinuxTestCase(TestCase):
    """Checks SELinux installation status"""

    version_regex = re.compile(r'((\d\.?)+[-.]\d)')

    def test_positive_foreman_module(self):
        """Check if SELinux foreman module has the right version

        @id: a0736b3a-3d42-4a09-a11a-28c1d58214a5

        @expectedresults: Foreman RPM and SELinux module versions match

        """
        rpm_result = ssh.command('rpm -q foreman-selinux')
        self.assertEqual(rpm_result.return_code, 0)
        semodule_result = ssh.command('semodule -l | grep foreman')
        self.assertEqual(semodule_result.return_code, 0)

        # Sample rpm output: foreman-selinux-1.7.2.8-1.el7sat.noarch
        rpm_version = self.version_regex.search(
            ''.join(rpm_result.stdout)).group(1)
        # Sample semodule output: foreman        1.7.2.8
        semodule_version = self.version_regex.search(
            ''.join(semodule_result.stdout)).group(1)

        rpm_version = rpm_version[:-2]
        self.assertEqual(rpm_version.replace('-', '.'), semodule_version)

    def test_positive_check_installer_services(self):
        """Check if services start correctly

        @id: 85fd4388-6d94-42f5-bed2-24be38e9f104

        @expectedresults: All services {'elasticsearch', 'foreman-proxy',
        'foreman-tasks', 'httpd', 'mongod', 'postgresql', 'pulp_celerybeat',
        'pulp_resource_manager', 'pulp_workers', 'qdrouterd', 'qpidd',
        'tomcat'} are started

        """
        major_version = get_host_info()[1]
        services = (
            'foreman-proxy',
            'foreman-tasks',
            'httpd',
            'mongod',
            'postgresql',
            'pulp_celerybeat',
            'pulp_resource_manager',
            'pulp_streamer',
            'pulp_workers',
            'qdrouterd',
            'qpidd',
            'smart_proxy_dynflow_core',
            'squid',
            'tomcat6' if major_version == RHEL_6_MAJOR_VERSION else 'tomcat',
        )

        # check `services` status using service command
        if major_version >= RHEL_7_MAJOR_VERSION:
            status_format = 'systemctl status {0}'
        else:
            status_format = 'service {0} status'

        for service in services:
            with self.subTest(service):
                result = ssh.command(status_format.format(service))
                self.assertEqual(result.return_code, 0)
                self.assertEqual(len(result.stderr), 0)

        # check status reported by hammer ping command
        result = ssh.command(u'hammer -u {0[0]} -p {0[1]} ping'.format(
            settings.server.get_credentials()
        ))

        # iterate over the lines grouping every 3 lines
        # example [1, 2, 3, 4, 5, 6] will return [(1, 2, 3), (4, 5, 6)]
        for service, status, server_response in zip(
                *[iter(result.stdout)] * 3):
            service = service.replace(':', '').strip()
            status = status.split(':')[1].strip().lower()
            server_response = server_response.split(':', 1)[1].strip()
            self.assertEqual(
                status, 'ok',
                '{0} responded with {1}'.format(service, server_response)
            )

    def test_positive_check_installer_logfile(self):
        """Look for ERROR or FATAL references in logfiles

        @id: 80537809-8be4-42db-9cc8-5155378ee4d4

        @Steps:

        1. search all relevant logfiles for ERROR/FATAL

        @expectedresults: No ERROR/FATAL notifcations occur in {katello-jobs,
        tomcat6, foreman, pulp, passenger-analytics, httpd, foreman_proxy,
        elasticsearch, postgresql, mongod} logfiles.

        """
        logfiles = (
            {
                'path': '/var/log/candlepin/error.log',
                'pattern': r'ERROR'
            },
            {
                'path': '/var/log/foreman-installer/satellite.log',
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
