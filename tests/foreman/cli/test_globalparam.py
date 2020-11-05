"""Test class for Global parameters CLI

:Requirement: Globalparam

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Parameters

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.globalparam import GlobalParameter
from robottelo.test import CLITestCase


class GlobalParameterTestCase(CLITestCase):
    """GlobalParameter related CLI tests."""

    @pytest.mark.tier1
    def test_positive_set(self):
        """Check if Global Param can be set

        :id: af0d3338-d7a1-41e5-959a-289ebc326c5b

        :expectedresults: Global Param is set


        :CaseImportance: Critical
        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-{} {}'.format(gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({'name': name, 'value': value})

    @pytest.mark.tier1
    def test_positive_list_by_name(self):
        """Test Global Param List

        :id: 8dd6c4e8-4ec9-4bee-8a04-f5788960973a

        :expectedresults: Global Param List is displayed


        :CaseImportance: Critical
        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-{} {}'.format(gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({'name': name, 'value': value})
        result = GlobalParameter().list({'search': name})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], value)

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_delete_by_name(self):
        """Check if Global Param can be deleted

        :id: 2c44d9c9-2a21-4415-8e89-cfd3d963891b

        :expectedresults: Global Param is deleted


        :CaseImportance: Critical
        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-{} {}'.format(gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({'name': name, 'value': value})
        GlobalParameter().delete({'name': name})
        result = GlobalParameter().list({'search': name})
        self.assertEqual(len(result), 0)
