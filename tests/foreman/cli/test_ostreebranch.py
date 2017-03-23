# -*- encoding: utf-8 -*-
"""Test class for Ostree Branch CLI.

:Requirement: Ostreebranch

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import random
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    make_content_view,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.ostreebranch import OstreeBranch
from robottelo.cli.repository import Repository
from robottelo.constants import FEDORA23_OSTREE_REPO
from robottelo.decorators import run_only_on, tier1
from robottelo.decorators.host import skip_if_os
from robottelo.test import CLITestCase


class OstreeBranchTestCase(CLITestCase):
    """Test class for Ostree Branch CLI. """

    @classmethod
    @skip_if_os('RHEL6')
    def setUpClass(cls):
        """Create an organization, product and ostree repo."""
        super(OstreeBranchTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({u'organization-id': cls.org['id']})
        # Create new custom ostree repo
        cls.ostree_repo = make_repository({
            u'product-id': cls.product['id'],
            u'content-type': u'ostree',
            u'publish-via-http': u'false',
            u'url': FEDORA23_OSTREE_REPO,
        })
        Repository.synchronize({'id': cls.ostree_repo['id']})
        cls.cv = make_content_view({u'organization-id': cls.org['id']})
        ContentView.publish({u'id': cls.cv['id']})
        cls.cv = ContentView.info({u'id': cls.cv['id']})

    @run_only_on('sat')
    @tier1
    def test_positive_list(self):
        """List Ostree Branches

        :id: 0f5e7e63-c0e3-43fc-8238-caf19a478a46

        :Assert: Ostree Branch List is displayed

        :CaseLevel: Critical
        """
        result = OstreeBranch.list()
        self.assertGreater(len(result), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_list_by_repo_id(self):
        """List Ostree branches by repo id

        :id: 8cf1a973-031c-4c02-af14-0faba22ab60b

        :Assert: Ostree Branch List is displayed

        :CaseLevel: Critical
        """
        result = OstreeBranch.list({'repository-id': self.ostree_repo['id']})
        self.assertGreater(len(result), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_list_by_product_id(self):
        """List Ostree branches by product id

        :id: e7b9d04d-cace-4271-b166-214017200c53

        :Assert: Ostree Branch List is displayed

        :CaseLevel: Critical
        """
        result = OstreeBranch.list({'product-id': self.product['id']})
        self.assertGreater(len(result), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_list_by_org_id(self):
        """List Ostree branches by org id

        :id: 5b169619-305f-4934-b363-068193330701

        :Assert: Ostree Branch List is displayed

        :CaseLevel: Critical
        """
        result = OstreeBranch.list({'organization-id': self.org['id']})
        self.assertGreater(len(result), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_list_by_cv_id(self):
        """List Ostree branches by cv id

        :id: 3654f107-44ee-4af2-a9e4-f9fd8c68491e

        :Assert: Ostree Branch List is displayed

        :CaseLevel: Critical
        """
        result = OstreeBranch.list({'content-view-id': self.cv['id']})
        self.assertGreater(len(result), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_info_by_id(self):
        """Get info for Ostree branch by id

        :id: 7838c9a8-56da-44de-883c-28571ecfa75c

        :Assert: Ostree Branch Info is displayed

        :CaseLevel: Critical
        """
        result = OstreeBranch.list()
        self.assertGreater(len(result), 0)
        # Grab a random branch
        branch = random.choice(result)
        result = OstreeBranch.info({'id': branch['id']})
        self.assertEqual(branch['id'], result['id'])
