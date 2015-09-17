# -*- encoding: utf-8 -*-
"""Test class for PuppetModule CLI"""

from robottelo.cli.factory import make_org, make_product, make_repository
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.constants import FAKE_0_PUPPET_REPO
from robottelo.decorators import run_only_on
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestPuppetModule(CLITestCase):
    """Tests for PuppetModule via Hammer CLI"""

    @classmethod
    def setUpClass(cls):
        super(TestPuppetModule, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({
            u'organization-id': cls.org['id']
        })
        cls.repo = make_repository({
            u'organization-id': cls.org['id'],
            u'product-id': cls.product['id'],
            u'content-type': u'puppet',
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': cls.repo['id']})

    def test_puppet_module_list(self):
        """@Test: Check if puppet-module list retrieves puppet-modules of
        the given org

        @Feature: Puppet-module

        @Assert: Puppet-modules are retrieved for the given org

        """
        result = PuppetModule.list({'organization-id': self.org['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # There are 4 puppet modules in the test puppet-module url
        self.assertEqual(len(result.stdout), 4)

    def test_puppet_module_info(self):
        """@Test: Check if puppet-module info retrieves info for the given
        puppet-module id

        @Feature: Puppet-module

        @Assert: The puppet-module info is retrieved

        """
        return_value = PuppetModule.list({
            'organization-id': self.org['id']
        })
        # There are 4 puppet modules in the test puppet-module url
        for i in range(4):
            result = PuppetModule.info(
                {'id': return_value.stdout[i]['id']},
                output_format='json'
            )
            self.assertEqual(result.return_code, 0)
            self.assertEqual(len(result.stderr), 0)
            self.assertEqual(result.stdout['ID'], return_value.stdout[i]['id'])
