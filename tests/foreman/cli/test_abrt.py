"""Test for abrt report

:Requirement: Abrt

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, upgrade
from robottelo.test import CLITestCase


class AbrtTestCase(CLITestCase):
    """Test class for generating abrt report in CLI."""

    @stubbed()
    @upgrade
    def test_positive_create_report(self):
        """a crashed program and abrt reports are send

        :id: 6e6e7525-895a-4192-9e56-4a0df1ad41ff

        :Setup: abrt

        :Steps: start a sleep process in background, kill it send the report
            using smart-proxy-abrt-send

        :expectedresults: A abrt report with ccpp.* extension  created under
            /var/tmp/abrt

        :caseautomation: notautomated

        """

    @stubbed()
    def test_positive_create_reports(self):
        """Counts are correct when abrt sends multiple reports

        :id: 13aed05c-b72d-4a35-aa0e-5ac2029300e7

        :Setup: abrt

        :Steps:

            1. Create multiple reports of abrt
            2. Keep track of counts

        :expectedresults: Count is updated in proper manner

        :caseautomation: notautomated

        """

    @stubbed()
    def test_positive_update_timer(self):
        """Edit the smart-proxy-abrt timer

        :id: 8e62d8d4-9b1c-4eb7-9352-c001be09a4d9

        :Setup: abrt

        :Steps: edit the timer for /etc/cron.d/rubygem-smart_proxy_abrt

        :expectedresults: the timer file is edited

        :caseautomation: notautomated

        """

    @stubbed()
    def test_positive_identify_hostname(self):
        """Identifying the hostnames

        :id: d9ab279b-45cf-412e-bc0f-af31737cfa74

        :Setup: abrt

        :Steps: UI => Settings => Abrt tab => edit hostnames

        :expectedresults: Assertion of hostnames is possible

        :caseautomation: notautomated

        """

    @stubbed()
    def test_positive_search_report(self):
        """Able to retrieve reports in CLI

        :id: b0623309-1b76-466d-a026-496e117f2d04

        :Setup: abrt

        :Steps: access /var/tmp/abrt/ccpp-* files

        :expectedresults: Assertion of parameters

        :caseautomation: notautomated

        """
