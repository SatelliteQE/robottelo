# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from robottelo.common.constants import NOT_IMPLEMENTED
import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest


class TestSSOCLI(BaseCLI):

    # Notes for installer testing:
    # Perhaps there is a convenient log analyzer library out there
    # that can parse logs? It would be better (and possibly less
    # error-prone) than simply grepping for ERROR/FATAL

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_check_services(self):
        # devnote:
        # maybe `hammer ping` command might be useful here to check
        # the health status
        """
        @feature: Installer
        @test: Services services start correctly
        @assert: All services {katello-jobs, tomcat6, foreman, pulp,
        passenger-analytics, httpd, foreman_proxy, elasticsearch, postgresql,
        mongod} are started
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_logfile_check(self):
        """
        @feature: Installer
        @test: Look for ERROR or FATAL references in logfiles
        @steps:
        1.  search all relevant logfiles for ERROR/FATAL
        @assert: No ERROR/FATAL notifcations occur in {katello-jobs, tomcat6,
        foreman, pulp, passenger-analytics,httpd, foreman_proxy, elasticsearch,
        postgresql, mongod} logfiles.
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_check_progress_meter(self):
        """
        @feature: Installer
        @test:  Assure progress indicator/meter "works"
        @assert: Progress indicator increases appropriately as install
        commences,
        through to completion
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_from_iso(self):
        """
        @feature: Installer
        @test:  Can install product from ISO
        @assert: Install from ISO is sucessful.
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_server_install(self):
        """
        @feature: Installer
        @test:  Can install main satellite instance successfully via RPM
        @assert: Install of main instance successful.
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_node_install(self):
        """
        @feature: Installer
        @test:  Can install node successfully via RPM
        @assert: Install of node successful.
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_smartproxy_install(self):
        """
        @feature: Installer
        @test:  Can install smart-proxy successfully via RPM
        @assert: Install of smart-proxy successful.
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_disconnected_util_install(self):
        """
        @feature: Installer
        @test:  Can install  satellite disconnected utility successfully
        via RPM
        @assert: Install of disconnected utility successful.
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_smartproxy_registers(self):
        """
        @feature: Installer
        @test: Upon installation, smart-proxy instance self-registers
        itself to parent instance
        @assert: smart-proxy is communicating properly with parent,
        following install.
        @status: Manual
        """
        pass

    @unittest.skip(NOT_IMPLEMENTED)
    def test_installer_clear_data(self):
        """
        @feature: Installer
        @test:  User can run installer to clear existing data
        @steps:
        @assert: All data is cleared from satellite instance
        @bz: 1072780
        @status: Manual
        """
        pass
