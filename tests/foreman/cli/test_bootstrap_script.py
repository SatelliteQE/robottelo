"""Test for bootstrap script (bootstrap.py)

:Requirement: Bootstrap Script

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Bootstrap

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.test import CLITestCase


class BootstrapScriptTestCase(CLITestCase):
    """Test class for bootstrap script."""

    @classmethod
    def setUpClass(cls):
        """create VM for testing """
        super().setUpClass()

    @pytest.mark.tier1
    @pytest.mark.stubbed
    def test_positive_register(self):
        """System is registered

        :id: e34561fd-e0d6-4587-84eb-f86bd131aab1

        :Steps:

            1. assure system is not registered
            2. register a system

        :expectedresults: system is registered, host is created

        :CaseAutomation: NotAutomated

        :CaseImportance: Critical
        """

    @pytest.mark.tier1
    @pytest.mark.stubbed
    @pytest.mark.upgrade
    def test_positive_reregister(self):
        """Registered system is re-registered

        :id: d8a7aef1-7522-47a8-8478-77e81ca236be

        :Steps:

            1. register a system
            2. assure system is registered
            3. register system once again

        :expectedresults: system is newly registered, host is created

        :CaseAutomation: NotAutomated

        :CaseImportance: Critical
        """
