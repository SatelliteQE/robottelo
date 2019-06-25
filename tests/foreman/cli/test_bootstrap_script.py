# -*- encoding: utf-8 -*-
"""Test for bootstrap script (bootstrap.py)

:Requirement: Bootstrap Script

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Bootstrap

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, tier1, upgrade
from robottelo.test import CLITestCase


class BootstrapScriptTestCase(CLITestCase):
    """Test class for bootstrap script."""

    @classmethod
    def setUpClass(cls):
        """create VM for testing """
        super(BootstrapScriptTestCase, cls).setUpClass()

    @tier1
    @stubbed()
    def test_positive_register(self):
        """System is registered

        :id: e34561fd-e0d6-4587-84eb-f86bd131aab1

        :Steps:

            1. assure system is not registered
            2. register a system

        :expectedresults: system is registered, host is created

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    @upgrade
    def test_positive_reregister(self):
        """Registered system is re-registered

        :id: d8a7aef1-7522-47a8-8478-77e81ca236be

        :Steps:

            1. register a system
            2. assure system is registered
            3. register system once again

        :expectedresults: system is newly registered, host is created

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_positive_migrate(self):
        """RHN registered system is migrated

        :id: 26911dce-f2e3-4aef-a490-ad55236493bf

        :Steps:

            1. register system to SAT5 (or use precreated stored registration)
            2. assure system is registered with rhn classic
            3. migrate system

        :expectedresults: system is migrated, ie. registered

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_negative_register_no_subs(self):
        """Attempt to register when no subscriptions are available

        :id: 26f04562-6242-4542-8852-4242156f6e45

        :Steps:

            1. create AK with no available subscriptions
            2. try to register a system

        :expectedresults: ends gracefully, reason displayed to user

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_negative_register_bad_hostgroup(self):
        """Attempt to register when hostgroup doesn't meet all criteria

        :id: 29551e22-ae63-47f2-86f3-5f1444df8493

        :Steps:

            1. create hostgroup not matching required criteria for
               bootstrapping (Domain can't be blank...)
            2. try to register a system

        :expectedresults: ends gracefully, reason displayed to user

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_positive_register_host_collision(self):
        """Attempt to register with already created host

        :id: ec39c981-5b8a-43a3-84f1-71871a951c53

        :Steps:

            1. create host profile
            2. register a system

        :expectedresults: system is registered, pre-created host profile is
            used

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_negative_register_missing_sattools(self):
        """Attempt to register when sat tools not available

        :id: 88f95080-a6f1-4a4f-bd7a-5d030c0bd2e0

        :Steps:

            1. create env without available sat tools repo (AK or hostgroup
               being used doesn't provide CV that have sattools)
            2. try to register a system

        :expectedresults: ends gracefully, reason displayed to user

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """
