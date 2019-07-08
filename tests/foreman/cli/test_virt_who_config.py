"""Test for virt-who configure CLI

:Requirement: Virtwho-configure

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:TestType: Functional

:CaseImportance: High

:CaseAutomation: notautomated

:Upstream: No
"""

from robottelo.decorators import stubbed, tier1
from robottelo.test import CLITestCase


class VirtWhoConfigTestCase(CLITestCase):

    def test_positive_create_ui_deploy_cli(self):
        """ Verify "hammer virt-who-config"

        :id: e273e2b3-79dc-46f5-8925-688f45f6b192

        :steps:
            1. Create config in UI.
            2. Deploy with "hammer virt-who-config deploy"

        :expectedresults:
            Virt-who is correctly configured, and sends reports to satellite.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_create_cli_deploy_cli(self):
        """ Verify  "hammer virt-who-config"

        :id: 776abf86-a96a-4b3a-8a6e-92face670471

        :steps:
            1. Create config using hammer.
            2. Deploy using hammer.

        :expectedresults:
            Virt-who is correctly configured, and sends reports to satellite.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_virt_who_user_login(self):
        """ Make sure users created by virt-who config plugin
         is not able to access CLI

        :id: 1fe2daec-b1b0-4dd9-bfa2-cd81ee13977b

        :steps:
            1. Create a virt-who configuration
            2. Attempt to login the UI with the user created by the
               virt-who config plugin. Verify the login is blocked
            3. Attempt to login using Hammer with the user created by the
               virt-who config plugin. Verify the login is blocked
            4. Attempt to click the username link displayed in related
               task details.

        :expectedresults:
            Users created by virt-who config plugin is not able to access CLI

        :CaseAutomation: notautomated
        """
