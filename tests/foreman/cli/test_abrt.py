"""Test for abrt report"""
from robottelo.decorators import stubbed
from robottelo.test import CLITestCase


class AbrtTestCase(CLITestCase):
    """Test class for generating abrt report in CLI."""

    @stubbed()
    def test_positive_create_report(self):
        """a crashed program and abrt reports are send

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. start a sleep process in background, kill it send the report using
        smart-proxy-abrt-send

        @Assert: A abrt report with ccpp.* extension  created under
        /var/tmp/abrt

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_reports(self):
        """Counts are correct when abrt sends multiple reports

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. Create multiple reports of abrt
        2. Keep track of counts

        @Assert: Count is updated in proper manner

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_timer(self):
        """Edit the smart-proxy-abrt timer

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. edit the timer for /etc/cron.d/rubygem-smart_proxy_abrt

        @Assert: the timer file is edited

        @Status: Manual

        """

    @stubbed()
    def test_positive_identify_hostname(self):
        """Identifying the hostnames

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. UI => Settings => Abrt tab => edit hostnames

        @Assert: Assertion of hostnames is possible

        @Status: Manual

        """

    @stubbed()
    def test_positive_search_report(self):
        """Able to retrieve reports in CLI

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. access /var/tmp/abrt/ccpp-* files

        @Assert: Assertion of parameters

        @Status: Manual

        """
