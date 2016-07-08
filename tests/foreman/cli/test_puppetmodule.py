# -*- encoding: utf-8 -*-
"""Test class for PuppetModule CLI

@Requirement: Puppetmodule

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.cli.factory import make_org, make_product, make_repository
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.constants import FAKE_0_PUPPET_REPO
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1
from robottelo.test import CLITestCase


class PuppetModuleTestCase(CLITestCase):
    """Tests for PuppetModule via Hammer CLI"""

    @classmethod
    def setUpClass(cls):
        super(PuppetModuleTestCase, cls).setUpClass()
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

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1283173)
    @tier1
    def test_positive_list(self):
        """Check if puppet-module list retrieves puppet-modules of
        the given org

        @id: 77635e70-19e7-424d-9c89-ec5dbe91de75

        @Assert: Puppet-modules are retrieved for the given org
        """
        result = PuppetModule.list({'organization-id': self.org['id']})
        # There are 4 puppet modules in the test puppet-module url
        self.assertEqual(len(result), 4)

    @run_only_on('sat')
    @tier1
    def test_positive_info(self):
        """Check if puppet-module info retrieves info for the given
        puppet-module id

        @id: 8aaa9243-5e20-49d6-95ce-620cc1ba18dc

        @Assert: The puppet-module info is retrieved
        """
        return_value = PuppetModule.list({
            'organization-id': self.org['id'],
        })
        for i in range(len(return_value)):
            result = PuppetModule.info(
                {'id': return_value[i]['id']},
                output_format='json'
            )
            self.assertEqual(result['id'], return_value[i]['id'])
