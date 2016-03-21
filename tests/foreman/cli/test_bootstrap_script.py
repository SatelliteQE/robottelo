# -*- encoding: utf-8 -*-
"""Test for bootstrap script"""
from robottelo.decorators import stubbed, tier1
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

        @Feature: Bootstrap Script

        @Steps:

        1. assure system is not registered
        2. register a system

        @Assert: system is registered, host is created

        @Status: Manual
        """

    @tier1
    @stubbed()
    def test_positive_reregister(self):
        """Registered system is re-registered

        @Feature: Bootstrap Script

        @Steps:

        1. register a system
        2. assure system is registered
        3. register system once again

        @Assert: system is newly registered, host is created

        @Status: Manual
        """

    @tier1
    @stubbed()
    def test_positive_migrate(self):
        """RHN registered system is migrated

        @Feature: Bootstrap Script

        @Steps:

        1. register system to SAT5 (or use precreated stored registration)
        2. assure system is registered with rhn classic
        3. migrate system

        @Assert: system is migrated, ie. registered

        @Status: Manual
        """

    @tier1
    @stubbed()
    def test_negative_register_no_subs(self):
        """Attempt to register when no subscriptions are available

        @Feature: Bootstrap Script

        @Steps:

        1. create AK with no available subscriptions
        2. try to register a system

        @Assert: ends gracefully, reason displayed to user

        @Status: Manual
        """

    @tier1
    @stubbed()
    def test_negative_register_bad_hostgroup(self):
        """Attempt to register when hostgroup doesn't meet all criteria

        @Feature: Bootstrap Script

        @Steps:

        1. create hostgroup not matching required criteria for bootstrapping
           (Domain can't be blank...)
        2. try to register a system

        @Assert: ends gracefully, reason displayed to user

        @Status: Manual
        """

    @tier1
    @stubbed()
    def test_positive_register_host_collision(self):
        """Attempt to register with already created host

        @Feature: Bootstrap Script

        @Steps:

        1. create host profile
        2. register a system

        @Assert: system is registered, pre-created host profile is used

        @Status: Manual
        """

    @tier1
    @stubbed()
    def test_negative_register_missing_sattools(self):
        """Attempt to register when sat tools not available

        @Feature: Bootstrap Script

        @Steps:

        1. create env without available sat tools repo
           (AK or hostgroup being used doesn't provide CV that have sattools)
        2. try to register a system

        @Assert: ends gracefully, reason displayed to user

        @Status: Manual
        """
