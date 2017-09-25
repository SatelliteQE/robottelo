"""Test for virt-who configure API

:Requirement: Virtwho-configure

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:CaseAutomation: notautomated


:Upstream: No
"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier4
from robottelo.test import UITestCase


class VirtWhoConfigTestCase(UITestCase):
    """Implements Virt-who-configure UI tests"""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_welcome_page(self):
        """
        :id: e25804fd-98cb-46bb-aa29-958ceb361292

        :steps:
            1. Verify UI Elements on welcome page

        :expectedresults:
            UI Welcome page describes the feature and includes a button
            to create the first config. The button brings the use to the
            config page

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_configurations_page(self):
        """ config page listings

        :id: fa6d5ce4-08b7-41fa-b7ab-ac5a018cf68a

        :steps:
            1. Create virt-who-configuration

        :expectedresults:
            Verify list the created configuration


        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_postitve_config_change_redeploy(self):
        """ change the config and redeploy the script.

        :id: 466d07b3-3cc7-43ef-b820-a5510b43e4dd

        :steps:
            1. Edit virt-who configuration and verify the updated shell script,
               redeploy the script

        :expectedresults:
            Verify the script correctly configures virt-who.

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_virt_who_user_login(self):
        """ Verify users created by virt-who config is not able to access UI

        :id: 9a8bb27a-af91-47cc-9004-6e3497363dbb

        :steps:
            1. Create a virt-who configuration
            2. Attempt to login the UI with the user created by the
               virt-who configurator. Verify the login is blocked
            3. Attempt to login using Hammer with the user created by the
               virt-who configurator. Verify the login is blocked
            4. Attempt to click the username link displayed in related task
               details.

        :expectedresults:
            users created by virt-who config is not able to access UI
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_config_page_populated(self):
        """ verify page when populated

        :id: db6bbc68-2047-4c7d-af5b-31aee0030318

        :steps:
            1. Create multiple virt-who configurations


        :expectedresults: All configurations are listed on the config page

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_config_page_empty(self):
        """ verify page when empty

        :id: bb208160-9bd0-49ee-8971-6f71d48808fb

        :steps:
            1. Create multiple virt-who configurations
            2. Delete all configurations

        :expectedresults:
            The welcome page is shown when no configs are present.
        """


class VirtWhoConfigDashboardTestCase(UITestCase):
    """
    6. Review UI Dashboard
        - No reports
        - Out of Date
        - Up to Date
        - Latest out of date Configurations

    """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_dashboard_no_reports(self):
        """ No reports

        :id: 28720130-746b-4646-830e-bff8d735ef3c

        :steps:
            1. Create 2 virt-who configurations.
            2. Ensure there are no reports from any of the configs

        :expectedresults:
            Dashboard widget "No Reports" count is 2 (number of configs)

        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_dashboard_out_of_date(self):
        """ Out of Date

        :id: de39275f-4534-49ad-8389-f7e8b405d6b6

        :steps:
            1. Create 2 virt-who configurations.
            2. Cause virt-who reports to be out of date

        :expectedresults:
            Dashboard widget  "No Change" count is 2 (number of configs)

        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_dashboard_up_to_date(self):
        """ Up to Date

        :id: 5ac051f0-4540-46e5-ac3b-367721625ebb

        :steps:
            1. Create 2 virt-who configurations.
            2. Ensure virt-who reports are up to date.

        :expectedresults:
            Dashboard widget  "OK" count is 2 (number of configs)


        """
    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_lastest_out_of_date(self):
        """Verify dashboard widget Latest out of date Configurations

        :id: 1df6d171-df57-41ef-9443-c7bb15aab473

        :steps:
            1. Create 2 virt-who configurations.
            2. Cause virt-who reports to be out of date

        :expectedresults:
            The 2 virt-who configs are list in the latest out of date section
            of the widget.
        """
