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

from robottelo import ssh
from robottelo.api.utils import delete_puppet_class
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_smart_variable
from robottelo.cli.proxy import Proxy
from robottelo.cli.puppet import Puppet
from robottelo.config import settings
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.decorators import (
    tier2,
    run_only_on
)
from robottelo.helpers import get_data_file
from robottelo.test import CLITestCase


class PuppetClassTestCase(CLITestCase):
    """Implements puppet class tests in CLI."""

    @classmethod
    def setUpClass(cls):
        """Import a parametrized puppet class.
        """
        super(PuppetClassTestCase, cls).setUpClass()
        cls.puppet_module = "puppetlabs-ntp"
        cls.host_name = settings.server.hostname
        ssh.upload_file(
            local_file=get_data_file(PUPPET_MODULE_NTP_PUPPETLABS),
            remote_file='/tmp/{0}'.format(PUPPET_MODULE_NTP_PUPPETLABS)
        )
        ssh.command('puppet module install --force /tmp/{0}'.format(
            PUPPET_MODULE_NTP_PUPPETLABS))
        cls.env = Environment.info({u'name': 'production'})
        Proxy.importclasses({
            u'environment': cls.env['name'],
            u'name': cls.host_name,
        })
        cls.puppet = Puppet.info({u'name': 'ntp'})

    @classmethod
    def tearDownClass(cls):
        """Removes entire module from the system and re-imports classes into
        proxy. This is required as other tests use the same module.
        """
        super(PuppetClassTestCase, cls).tearDownClass()
        delete_puppet_class(
            cls.puppet['name'],
            cls.puppet_module,
            cls.host_name,
            cls.env['name']
        )

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
