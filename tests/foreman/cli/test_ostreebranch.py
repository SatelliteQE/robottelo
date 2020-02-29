# -*- encoding: utf-8 -*-
"""Test class for Ostree Branch CLI.

:Requirement: Ostreebranch

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ContentManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest

from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_org_with_credentials
from robottelo.cli.factory import make_product_with_credentials
from robottelo.cli.factory import make_repository_with_credentials
from robottelo.cli.factory import make_user
from robottelo.cli.ostreebranch import OstreeBranch
from robottelo.cli.repository import Repository
from robottelo.constants import FEDORA27_OSTREE_REPO
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.decorators.host import skip_if_os
from robottelo.test import CLITestCase


@pytest.mark.skip_if_open("BZ:1625783")
@skip_if_os('RHEL6')
class OstreeBranchTestCase(CLITestCase):
    """Test class for Ostree Branch CLI. """

    @classmethod
    def setUpClass(cls):
        """Create an organization, product and ostree repo."""
        super(OstreeBranchTestCase, cls).setUpClass()
        password = 'password'
        cls.user = make_user({'admin': 'true', 'password': password})
        cls.user['password'] = password
        credentials = cls.get_user_credentials()
        cls.org = make_org_with_credentials(credentials=credentials)
        cls.product = make_product_with_credentials(
            {u'organization-id': cls.org['id']}, credentials
        )
        # Create new custom ostree repo
        cls.ostree_repo = make_repository_with_credentials(
            {
                u'product-id': cls.product['id'],
                u'content-type': u'ostree',
                u'publish-via-http': u'false',
                u'url': FEDORA27_OSTREE_REPO,
            },
            credentials,
        )
        Repository.with_user(*credentials).synchronize({'id': cls.ostree_repo['id']})
        cls.cv = make_content_view(
            {u'organization-id': cls.org['id'], u'repository-ids': [cls.ostree_repo['id']]},
            credentials,
        )
        ContentView.with_user(*credentials).publish({u'id': cls.cv['id']})
        cls.cv = ContentView.with_user(*credentials).info({u'id': cls.cv['id']})

    @classmethod
    def get_user_credentials(cls):
        return cls.user['login'], cls.user['password']

    @tier3
    def test_positive_list(self):
        """List Ostree Branches

        :id: 0f5e7e63-c0e3-43fc-8238-caf19a478a46

        :expectedresults: Ostree Branch List is displayed
        """
        result = OstreeBranch.with_user(*self.get_user_credentials()).list()
        self.assertGreater(len(result), 0)

    @tier3
    @upgrade
    def test_positive_list_by_repo_id(self):
        """List Ostree branches by repo id

        :id: 8cf1a973-031c-4c02-af14-0faba22ab60b

        :expectedresults: Ostree Branch List is displayed

        """

        branch = OstreeBranch.with_user(*self.get_user_credentials())
        result = branch.list({'repository-id': self.ostree_repo['id']})
        self.assertGreater(len(result), 0)

    @tier3
    def test_positive_list_by_product_id(self):
        """List Ostree branches by product id

        :id: e7b9d04d-cace-4271-b166-214017200c53

        :expectedresults: Ostree Branch List is displayed
        """
        result = OstreeBranch.with_user(*self.get_user_credentials()).list(
            {'product-id': self.product['id']}
        )
        self.assertGreater(len(result), 0)

    @tier3
    def test_positive_list_by_org_id(self):
        """List Ostree branches by org id

        :id: 5b169619-305f-4934-b363-068193330701

        :expectedresults: Ostree Branch List is displayed
        """
        result = OstreeBranch.with_user(*self.get_user_credentials()).list(
            {'organization-id': self.org['id']}
        )
        self.assertGreater(len(result), 0)

    @tier3
    def test_positive_list_by_cv_id(self):
        """List Ostree branches by cv id

        :id: 3654f107-44ee-4af2-a9e4-f9fd8c68491e

        :expectedresults: Ostree Branch List is displayed

        """
        result = OstreeBranch.with_user(*self.get_user_credentials()).list(
            {'content-view-id': self.cv['id']}
        )
        self.assertGreater(len(result), 0)

    @tier3
    def test_positive_info_by_id(self):
        """Get info for Ostree branch by id

        :id: 7838c9a8-56da-44de-883c-28571ecfa75c

        :expectedresults: Ostree Branch Info is displayed
        """
        result = OstreeBranch.with_user(*self.get_user_credentials()).list()
        self.assertGreater(len(result), 0)
        # Grab a random branch
        branch = random.choice(result)
        result = OstreeBranch.with_user(*self.get_user_credentials()).info({'id': branch['id']})
        self.assertEqual(branch['id'], result['id'])
