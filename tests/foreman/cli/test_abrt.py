"""Test for abrt report"""
from robottelo.test import CLITestCase


class TestAbrt(CLITestCase):
    """Test class for generating abrt report in CLI."""

    def test_abrt_1(self):
        """@test: a crashed program and abrt reports are send

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. start a sleep process in background, kill it send the report using
        smart-proxy-abrt-send

        @Assert: A abrt report with ccpp.* extension  created under
        /var/tmp/abrt

        @Status: Manual

        """

    def test_abrt_2(self):
        """@test: Counts are correct when abrt sends multiple reports

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. Create multiple reports of abrt
        2. Keep track of counts

        @Assert: Count is updated in proper manner

        @Status: Manual

        """

    def test_abrt_3(self):
        """@test: Edit the smart-proxy-abrt timer

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. edit the timer for /etc/cron.d/rubygem-smart_proxy_abrt

        @Assert: the timer file is edited

        @Status: Manual

        """

    def test_abrt_4(self):
        """@test: Identifying the hostnames

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. UI => Settings => Abrt tab => edit hostnames

        @Assert: Assertion of hostnames is possible

        @Status: Manual

        """

    def test_abrt_5(self):
        """@test: Able to retrieve reports in CLI

        @Feature: Abrt

        @Setup: abrt

        @Steps:

        1. access /var/tmp/abrt/ccpp-* files

        @Assert: Assertion of parameters

        @Status: Manual

        """
