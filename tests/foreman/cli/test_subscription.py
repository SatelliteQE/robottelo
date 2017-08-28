"""Test class for Subscriptions

@Requirement: Subscription

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from robottelo import manifests
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_org
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.constants import PRDS, REPOS, REPOSET
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    tier1,
    tier2,
    upgrade
)
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


@run_in_one_thread
class SubscriptionTestCase(CLITestCase):
    """Manifest CLI tests"""

    def setUp(self):
        """Tests for content-view via Hammer CLI"""
        super(SubscriptionTestCase, self).setUp()
        self.org = make_org()

    # pylint: disable=no-self-use
    def _upload_manifest(self, org_id, manifest=None):
        """Uploads a manifest into an organization.

        A cloned manifest will be used if ``manifest`` is None.
        """
        if manifest is None:
            manifest = manifests.clone()
        upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            'organization-id': org_id,
        })
        manifest.content.close()

    @tier1
    def test_positive_manifest_upload(self):
        """upload manifest

        @id: e5a0e4f8-fed9-4896-87a0-ac33f6baa227

        @expectedresults: Manifest are uploaded properly
        """
        self._upload_manifest(self.org['id'])
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )

    @tier1
    @upgrade
    def test_positive_manifest_delete(self):
        """Delete uploaded manifest

        @id: 01539c07-00d5-47e2-95eb-c0fd4f39090f

        @expectedresults: Manifest are deleted properly
        """
        self._upload_manifest(self.org['id'])
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )
        Subscription.delete_manifest({
            'organization-id': self.org['id'],
        })
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )

    @tier2
    @upgrade
    def test_positive_enable_manifest_reposet(self):
        """enable repository set

        @id: cc0f8f40-5ea6-4fa7-8154-acdc2cb56b45

        @expectedresults: you are able to enable and synchronize repository
        contained in a manifest

        @CaseLevel: Integration
        """
        self._upload_manifest(self.org['id'])
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )
        RepositorySet.enable({
            'basearch': 'x86_64',
            'name': REPOSET['rhva6'],
            'organization-id': self.org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
        })
        Repository.synchronize({
            'name': REPOS['rhva6']['name'],
            'organization-id': self.org['id'],
            'product': PRDS['rhel'],
        })

    @tier1
    def test_positive_manifest_history(self):
        """upload manifest and check history

        @id: 000ab0a0-ec1b-497a-84ff-3969a965b52c

        @expectedresults: Manifest history is shown properly
        """
        self._upload_manifest(self.org['id'])
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=None,
        )
        history = Subscription.manifest_history({
            'organization-id': self.org['id'],
        })
        self.assertIn(
            '{0} file imported successfully.'.format(self.org['name']),
            ''.join(history),
        )

    @tier1
    @upgrade
    def test_positive_manifest_refresh(self):
        """upload manifest and refresh

        @id: 579bbbf7-11cf-4d78-a3b1-16d73bd4ca57

        @expectedresults: Manifests can be refreshed
        """
        self._upload_manifest(
            self.org['id'], manifests.original_manifest())
        subscription_list = Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )
        self.assertGreater(len(subscription_list), 0)
        Subscription.refresh_manifest({
            'organization-id': self.org['id'],
        })
        subscription_list = Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )
        Subscription.delete_manifest({
            'organization-id': self.org['id'],
        })
        self.assertGreater(len(subscription_list), 0)

    @skip_if_bug_open('bugzilla', 1226425)
    @tier1
    def test_negative_manifest_refresh(self):
        """manifest refresh must fail with a cloned manifest

        @id: 7f40795f-7841-4063-8a43-de0325c92b1f

        @expectedresults: the refresh command returns a non-zero return code

        @BZ: 1226425
        """
        self._upload_manifest(self.org['id'])
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )
        with self.assertRaises(CLIReturnCodeError):
            Subscription.refresh_manifest({
                'organization-id': self.org['id'],
            })
