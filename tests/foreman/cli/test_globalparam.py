# -*- encoding: utf-8 -*-
"""Test class for Global parameters CLI

@Requirement: Globalparam

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from robottelo.cli.globalparam import GlobalParameter
from robottelo.decorators import run_only_on, tier1
from robottelo.test import CLITestCase


class GlobalParameterTestCase(CLITestCase):
    """GlobalParameter related CLI tests."""

    # pylint: disable=no-self-use
    @run_only_on('sat')
    @tier1
    def test_positive_set(self):
        """Check if Global Param can be set

        @id: af0d3338-d7a1-41e5-959a-289ebc326c5b

        @Assert: Global Param is set

        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-%s %s' % (
            gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({
            'name': name,
            'value': value,
        })

    @run_only_on('sat')
    @tier1
    def test_positive_list_by_name(self):
        """Test Global Param List

        @id: 8dd6c4e8-4ec9-4bee-8a04-f5788960973a

        @Assert: Global Param List is displayed

        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-%s %s' % (
            gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({
            'name': name,
            'value': value,
        })
        result = GlobalParameter().list({'search': name})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], value)

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_name(self):
        """Check if Global Param can be deleted

        @id: 2c44d9c9-2a21-4415-8e89-cfd3d963891b

        @Assert: Global Param is deleted

        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-%s %s' % (
            gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({
            'name': name,
            'value': value,
        })
        GlobalParameter().delete({'name': name})
        result = GlobalParameter().list({'search': name})
        self.assertEqual(len(result), 0)
