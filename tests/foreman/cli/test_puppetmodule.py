# -*- encoding: utf-8 -*-
"""Test class for PuppetModule CLI

:Requirement: Puppetmodule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.constants import FAKE_0_PUPPET_REPO
from robottelo.constants import FAKE_1_PUPPET_REPO
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class PuppetModuleTestCase(CLITestCase):
    """Tests for PuppetModule via Hammer CLI"""

    @classmethod
    def setUpClass(cls):
        super(PuppetModuleTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({u'organization-id': cls.org['id']})
        cls.repo = make_repository(
            {
                u'organization-id': cls.org['id'],
                u'product-id': cls.product['id'],
                u'content-type': u'puppet',
                u'url': FAKE_0_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': cls.repo['id']})

    @tier1
    def test_positive_list(self):
        """Check if puppet-module list retrieves puppet-modules of
        the given org

        :id: 77635e70-19e7-424d-9c89-ec5dbe91de75

        :expectedresults: Puppet-modules are retrieved for the given org

        :BZ: 1283173

        :CaseImportance: Critical
        """
        result = PuppetModule.list({'organization-id': self.org['id']})
        # There are 4 puppet modules in the test puppet-module url
        self.assertEqual(len(result), 4)

    @tier1
    def test_positive_info(self):
        """Check if puppet-module info retrieves info for the given
        puppet-module id

        :id: 8aaa9243-5e20-49d6-95ce-620cc1ba18dc

        :expectedresults: The puppet-module info is retrieved

        :CaseImportance: Critical
        """
        return_value = PuppetModule.list({'organization-id': self.org['id']})
        for i in range(len(return_value)):
            result = PuppetModule.info({'id': return_value[i]['id']}, output_format='json')
            self.assertEqual(result['id'], return_value[i]['id'])

    @tier2
    @upgrade
    def test_positive_list_multiple_repos(self):
        """Verify that puppet-modules list for specific repo is correct
        and does not affected by other repositories.

        :id: f36d25b3-2495-4e89-a1cf-e39d52762d95

        :expectedresults: Number of modules has no changed after a second repo
            was synced.

        :CaseImportance: Critical
        """
        # Verify that number of synced modules is correct
        repo1 = Repository.info({'id': self.repo['id']})
        repo_content_count = repo1['content-counts']['puppet-modules']
        modules_num = len(PuppetModule.list({'repository-id': repo1['id']}))
        self.assertEqual(repo_content_count, str(modules_num))
        # Create and sync second repo
        repo2 = make_repository(
            {
                u'organization-id': self.org['id'],
                u'product-id': self.product['id'],
                u'content-type': u'puppet',
                u'url': FAKE_1_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': repo2['id']})
        # Verify that number of modules from the first repo has not changed
        self.assertEqual(modules_num, len(PuppetModule.list({'repository-id': repo1['id']})))
