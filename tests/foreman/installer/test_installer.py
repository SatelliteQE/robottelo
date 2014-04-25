# Notes for installer testing:
# Perhaps there is a convenient log analyzer library out there that can parse
# logs?
# It would be better (and possibly less error-prone) than simply grepping for
# ERROR/FATAL

import logging
import unittest

from itertools import izip

from robottelo.common import ssh
from robottelo.common.decorators import stubbed
from robottelo.log import LogFile


logger = logging.getLogger('robottelo')


class InstallerTestCase(unittest.TestCase):

    def test_installer_check_services(self):
        # devnote:
        # maybe `hammer ping` command might be useful here to check the health
        # status
        """
        @test: Services services start correctly
        @feature: Installer
        @assert: All services {katello-jobs, tomcat6, foreman, pulp,
        passenger-analytics, httpd, foreman_proxy, elasticsearch, postgresql,
        mongod} are started
        """

        services = ('katello-jobs', 'tomcat6', 'foreman', 'httpd',
                    'elasticsearch', 'postgresql', 'mongod')

        # check `services` status using service command
        for service in services:
            result = ssh.command('service %s status' % service)
            logger.debug(result.stdout)

            if service == 'foreman':
                self.assertEqual(result.return_code, 1)
            else:
                self.assertEqual(result.return_code, 0)

            self.assertEqual(len(result.stderr), 0)

        # check status reported by hammer ping command
        result = ssh.command('hammer ping')

        # iterate over the lines grouping every 3 lines
        # example [1, 2, 3, 4, 5, 6] will return [(1, 2, 3), (4, 5, 6)]
        for service, status, server_response in izip(*[iter(result.stdout)]*3):
            service = service.replace(':', '').strip()
            status = status.split(':')[1].strip().lower()
            server_response = server_response.split(':', 1)[1].strip()
            logger.debug('%s [%s] - %s', service, status, server_response)
            self.assertEqual(status, 'ok',
                             '%s responded with %s' % (service,
                                                       server_response))

    def test_installer_logfile_check(self):
        """
        @test: Look for ERROR or FATAL references in logfiles
        @feature: Installer
        @steps:
        1.  search all relevant logfiles for ERROR/FATAL
        @assert: No ERROR/FATAL notifcations occur in {katello-jobs, tomcat6,
        foreman, pulp, passenger-analytics, httpd, foreman_proxy,
        elasticsearch, postgresql, mongod} logfiles.
        """

        logfiles = (
            {'path': '/var/log/candlepin/error.log',
             'pattern': r'ERROR'},
            {'path': '/var/log/katello/katello-install/katello-install.log',
             'pattern': r'\[\s*(ERROR|FATAL)'},
        )

        for logfile in logfiles:
            log = LogFile(logfile['path'], logfile['pattern'])
            result = log.filter()
            self.assertEqual(
                len(result), 0,
                '"%s" pattern found in %s lines:\n%s' % (logfile['pattern'],
                                                         logfile['path'],
                                                         ''.join(result)))

    @stubbed
    def test_installer_check_progress_meter(self):
        """
        @test:  Assure progress indicator/meter "works"
        @feature: Installer
        @assert: Progress indicator increases appropriately as install
        commences, through to completion
        @status: Manual
        """

    @stubbed
    def test_installer_from_iso(self):
        """
        @test:  Can install product from ISO
        @feature: Installer
        @assert: Install from ISO is sucessful.
        @status: Manual
        """

    @stubbed
    def test_installer_server_install(self):
        """
        @test:  Can install main satellite instance successfully via RPM
        @feature: Installer
        @assert: Install of main instance successful.
        @status: Manual
        """

    @stubbed
    def test_installer_node_install(self):
        """
        @test:  Can install node successfully via RPM
        @feature: Installer
        @assert: Install of node successful.
        @status: Manual
        """

    @stubbed
    def test_installer_capsule_install(self):
        """
        @test:  Can install capsule successfully via RPM
        @feature: Installer
        @assert: Install of capsule successful.
        @status: Manual
        """

    @stubbed
    def test_installer_disconnected_util_install(self):
        """
        @test: Can install  satellite disconnected utility successfully via
        RPM
        @feature: Installer
        @assert: Install of disconnected utility successful.
        @status: Manual
        """

    @stubbed
    def test_installer_capsule_registers(self):
        """
        @test: Upon installation, capsule instance self-registers itself to
        parent instance
        @feature: Installer
        @assert: capsule is communicating properly with parent, following
        install.
        @status: Manual
        """

    @stubbed
    def test_installer_clear_data(self):
        """
        @test:  User can run installer to clear existing data
        @feature: Installer
        @steps:
        @assert: All data is cleared from satellite instance
        @bz: 1072780
        @status: Manual
        """
