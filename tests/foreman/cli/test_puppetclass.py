# -*- encoding: utf-8 -*-
"""Test class for Puppet Classes CLI

:Requirement: Puppetclass

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_smart_variable
from robottelo.cli.factory import publish_puppet_module
from robottelo.cli.puppet import Puppet
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class PuppetClassTestCase(CLITestCase):
    """Implements puppet class tests in CLI."""

    @classmethod
    def setUpClass(cls):
        """Import a parametrized puppet class.
        """
        super(PuppetClassTestCase, cls).setUpClass()
        cls.puppet_modules = [{'author': 'robottelo', 'name': 'generic_1'}]
        cls.org = make_org()
        cv = publish_puppet_module(cls.puppet_modules, CUSTOM_PUPPET_REPO, cls.org['id'])
        cls.env = Environment.list({'search': 'content_view="{0}"'.format(cv['name'])})[0]
        cls.puppet = Puppet.info(
            {'name': cls.puppet_modules[0]['name'], 'environment': cls.env['name']}
        )

    @tier2
    @upgrade
    def test_positive_list_smart_class_parameters(self):
        """List smart class parameters associated with the puppet class.

        :id: 56b370c2-8fc6-49be-9676-242178cc709a

        :expectedresults: Smart class parameters listed for the class.
        """
        class_sc_parameters = Puppet.sc_params({'puppet-class': self.puppet['name']})
        self.assertGreater(len(class_sc_parameters), 0)

    @tier2
    @upgrade
    def test_positive_list_smart_variables(self):
        """List smart variables associated with the puppet class.

        :id: cb2b41c0-29cc-4c0b-a7c8-38403d6dda5b

        :expectedresults: Smart variables listed for the class.
        """
        make_smart_variable({'puppet-class': self.puppet['name']})
        class_smart_variables = Puppet.smart_variables({'puppet-class': self.puppet['name']})
        self.assertGreater(len(class_smart_variables), 0)
