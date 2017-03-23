"""Test for upgrading Puppet to Puppet4

:Requirement: Puppet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.config import settings
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier4,
)
from robottelo.test import CLITestCase


@run_in_one_thread
class PuppetUpgradeTestCase(CLITestCase):
    """Implements Puppet test scenario"""

    @classmethod
    @skip_if_not_set('clients')
    def setUpClass(cls):
        super(PuppetUpgradeTestCase, cls).setUpClass()
        cls.sat6_hostname = settings.server.hostname

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_puppet_upgrade(self):
        """Upgrade Satellite/client puppet versions

        :id: fd311168-afda-49b6-ac5f-533c4fd411b5

        :Steps:

            1. register client (p3)
            2. prepare puppet module
            3. upgrade Satellite from p3 to p4
            4. apply puppet module to p3 client
            5. upgrade client from p3 to p4
            6. apply puppet module to the client
            7. register another client (p4)
            8. apply puppet module to the client

        :expectedresults: multiple asserts along the code that motd module was
            applied

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_puppet_capsule_upgrade(self):
        """Upgrade standalone Capsule/client puppet versions

        :id: 7e8e9047-d012-4fc5-9e6e-f11c1b05df5d

        :Steps:

            1. register client (p3)
            2. prepare puppet module
            3. upgrade Capsule from p3 to p4
            4. apply puppet module to p3 client
            5. upgrade client from p3 to p4
            6. apply puppet module to the client
            7. register another client (p4)
            8. apply puppet module to the client

        :expectedresults: multiple asserts along the code that motd module was
            applied

        :caseautomation: notautomated

        :CaseLevel: System
        """
