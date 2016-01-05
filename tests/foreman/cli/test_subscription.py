"""Test class for Subscriptions"""
from robottelo import manifests
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_org
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


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
        """@Test: upload manifest

        @Feature: Subscriptions/Manifest Upload

        @Assert: Manifest are uploaded properly
        """
        self._upload_manifest(self.org['id'])
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )

    @tier1
    def test_positive_manifest_delete(self):
        """@Test: Delete uploaded manifest

        @Feature: Subscriptions/Manifest Delete

        @Assert: Manifest are deleted properly
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
    def test_positive_enable_manifest_reposet(self):
        """@Test: enable repository set

        @Feature: Subscriptions/Repository Sets

        @Assert: you are able to enable and synchronize
        repository contained in a manifest
        """
        self._upload_manifest(self.org['id'])
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )
        RepositorySet.enable({
            'basearch': 'x86_64',
            'name': (
                'Red Hat Enterprise Virtualization Agents '
                'for RHEL 6 Workstation (RPMs)'
            ),
            'organization-id': self.org['id'],
            'product': 'Red Hat Enterprise Linux Workstation',
            'releasever': '6Workstation',
        })
        Repository.synchronize({
            'name': (
                'Red Hat Enterprise Virtualization Agents '
                'for RHEL 6 Workstation '
                'RPMs x86_64 6Workstation'
            ),
            'organization-id': self.org['id'],
            'product': 'Red Hat Enterprise Linux Workstation',
        })

    @tier1
    def test_positive_manifest_history(self):
        """@Test: upload manifest and check history

        @Feature: Subscriptions/Manifest History

        @Assert: Manifest history is shown properly
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
    def test_positive_manifest_refresh(self):
        """@Test: upload manifest and refresh

        @Feature: Subscriptions/Manifest refresh

        @Assert: Manifests can be refreshed
        """
        self._upload_manifest(
            self.org['id'], manifests.original_manifest())
        Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )
        Subscription.refresh_manifest({
            'organization-id': self.org['id'],
        })
        Subscription.delete_manifest({
            'organization-id': self.org['id'],
        })

    @skip_if_bug_open('bugzilla', 1226425)
    @tier1
    def test_negative_manifest_refresh(self):
        """@Test: manifest refresh must fail with a cloned manifest

        @Feature: Subscriptions/Manifest refresh

        @Assert: the refresh command returns a non-zero return code

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
