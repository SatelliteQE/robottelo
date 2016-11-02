# -*- encoding: utf-8 -*-
"""Test class for Puppet Classes CLI

@Requirement: Puppetclass

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.cli.contentview import ContentView
from robottelo.cli.environment import Environment
from robottelo.cli.factory import (
    make_content_view,
    make_org,
    make_product,
    make_repository,
    make_smart_variable,
)
from robottelo.cli.puppet import Puppet
from robottelo.cli.repository import Repository
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.decorators import (
    tier2,
    run_only_on
)
from robottelo.test import CLITestCase


class PuppetClassTestCase(CLITestCase):
    """Implements puppet class tests in CLI."""

    @classmethod
    def setUpClass(cls):
        """Import a parametrized puppet class.
        """
        super(PuppetClassTestCase, cls).setUpClass()
        puppet_module = "robottelo/generic_2"
        org = make_org()
        product = make_product({u'organization-id': org['id']})
        repo = make_repository({
            u'product-id': product['id'],
            u'content-type': 'puppet',
            u'url': CUSTOM_PUPPET_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({u'organization-id': org['id']})
        ContentView.puppet_module_add({
            u'author': puppet_module.split('/')[0],
            u'name': puppet_module.split('/')[1],
            u'content-view-id': cv['id'],
        })
        ContentView.publish({u'id': cv['id']})
        cls.env = Environment.list({
            u'search': 'content_view="{0}"'.format(cv['name'])
        })[0]
        cls.puppet = Puppet.info({
            u'name': puppet_module.split('/')[1]
        })

    @run_only_on('sat')
    @tier2
    def test_positive_list_smart_class_parameters(self):
        """List smart class parameters associated with the puppet class.

        @id: 56b370c2-8fc6-49be-9676-242178cc709a

        @assert: Smart class parameters listed for the class.
        """
        class_sc_parameters = Puppet.sc_params({
            u'puppet-class': self.puppet['name']})
        self.assertGreater(len(class_sc_parameters), 0)

    @run_only_on('sat')
    @tier2
    def test_positive_list_smart_variables(self):
        """List smart variables associated with the puppet class.

        @id: cb2b41c0-29cc-4c0b-a7c8-38403d6dda5b

        @assert: Smart variables listed for the class.
        """
        make_smart_variable({'puppet-class': self.puppet['name']})
        class_smart_variables = Puppet.smart_variables({
            u'puppet-class': self.puppet['name']})
        self.assertGreater(len(class_smart_variables), 0)
