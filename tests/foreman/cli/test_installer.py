# -*- encoding: utf-8 -*-
"""Tests for Installer"""
from robottelo.decorators import run_only_on, stubbed
from robottelo.test import CLITestCase


class InstallerTestCase(CLITestCase):
    """Test class for installer"""
    # Notes for installer testing:
    # Perhaps there is a convenient log analyzer library out there
    # that can parse logs? It would be better (and possibly less
    # error-prone) than simply grepping for ERROR/FATAL

    @stubbed()
    @run_only_on('sat')
    def test_positive_installer_check_services(self):
        # devnote:
        # maybe `hammer ping` command might be useful here to check
        # the health status
        """Services services start correctly

        @feature: Installer

        @assert: All services {katello-jobs, tomcat6, foreman, pulp,
        passenger-analytics, httpd, foreman_proxy, elasticsearch, postgresql,
        mongod} are started

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    def test_positive_installer_logfile_check(self):
        """Look for ERROR or FATAL references in logfiles

        @feature: Installer

        @steps:
        1.  search all relevant logfiles for ERROR/FATAL

        @assert: No ERROR/FATAL notifcations occur in {katello-jobs, tomcat6,
        foreman, pulp, passenger-analytics,httpd, foreman_proxy, elasticsearch,
        postgresql, mongod} logfiles.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    def test_positive_installer_check_progress_meter(self):
        """ Assure progress indicator/meter "works"

        @feature: Installer

        @assert: Progress indicator increases appropriately as install
        commences, through to completion

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    def test_positive_server_installer_from_iso(self):
        """ Can install product from ISO

        @feature: Installer

        @assert: Install from ISO is sucessful.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    def test_positive_server_installer_from_repository(self):
        """ Can install main satellite instance successfully via RPM

        @feature: Installer

        @assert: Install of main instance successful.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    def test_positive_capsule_installer_from_repository(self):
        """ Can install capsule successfully via RPM

        @feature: Installer

        @assert: Install of capsule successful.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    def test_positive_disconnected_util_installer(self):
        """ Can install  satellite disconnected utility successfully
        via RPM

        @feature: Installer

        @assert: Install of disconnected utility successful.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    def test_positive_capsule_installer_and_register(self):
        """Upon installation, capsule instance self-registers
        itself to parent instance

        @feature: Installer

        @assert: capsule is communicating properly with parent,
        following install.

        @status: Manual
        """

    @stubbed()
    @run_only_on('sat')
    def test_positive_installer_clear_data(self):
        """ User can run installer to clear existing data

        @feature: Installer

        @assert: All data is cleared from satellite instance

        @bz: 1072780

        @status: Manual
        """
