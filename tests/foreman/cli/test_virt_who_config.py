"""Test for virt-who configure CLI

:Requirement: Virtwho-configure

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier2, tier3
from robottelo.test import TestCase, CLITestCase

class VirtWhoConfigCLITestCase(CLITestCase):
    def test_positive_create_cli_deploy_ui(self):
        """Verify  “hammer virt-who-config”

        :id: e273e2b3-79dc-46f5-8925-688f45f6b192

        :steps:
            1. Create config in UI, deploy using “hammer virt-who-config deploy”
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_cli_deploy_cli(self):
        """ Verify  “hammer virt-who-config

        :id: 776abf86-a96a-4b3a-8a6e-92face670471

        :steps:
            1. Create config using hammer, deploy using hammer.
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_virt_who_user_login(self):
        """ Make sure the users created by virt-who config is not able to access UI/CLI

        :id: 1fe2daec-b1b0-4dd9-bfa2-cd81ee13977b

        :steps:
            1. Create a virt-who configuration
            2. Attempt to login the UI with the user created by the virt-who configurator. Verify the login is blocked
            3. Attempt to login using Hammer with the user created by the virt-who configurator. Verify the login is blocked
            4. Attempt to click the username link displayed in related task details.
        """