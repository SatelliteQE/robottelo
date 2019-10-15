"""Test class for Subscriptions

:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SubscriptionManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import csv

from robottelo import manifests
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_org
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.constants import (
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    tier1,
    tier2,
    tier3,
    upgrade
)
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
        self.upload_manifest(org_id, manifest)

    @staticmethod
    def _read_csv_file(file_path):
        """Read a csv file as a dictionary

        :param str file_path: The file location path to read as csv

        :returns a tuple (list, list[dict]) that represent field_names, data
        """
        csv_data = []
        with open(file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            field_names = csv_reader.fieldnames
            for csv_row in csv_reader:
                csv_data.append(csv_row)
        return field_names, csv_data

    @staticmethod
    def _write_csv_file(file_path, filed_names, csv_data):
        """Write to csv file

        :param str file_path: The file location path to write as csv
        :param list filed_names: The field names to be written
        :param list[dict] csv_data: the list dict data to be saved
        """
        with open(file_path, 'w') as csv_file:
            csv_writer = csv.DictWriter(csv_file, filed_names, delimiter=',')
            csv_writer.writeheader()
            for csv_row in csv_data:
                csv_writer.writerow(csv_row)

    @tier1
    def test_positive_manifest_upload(self):
        """upload manifest

        :id: e5a0e4f8-fed9-4896-87a0-ac33f6baa227

        :expectedresults: Manifest are uploaded properly

        :CaseImportance: Critical
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

        :id: 01539c07-00d5-47e2-95eb-c0fd4f39090f

        :expectedresults: Manifest are deleted properly

        :CaseImportance: Critical
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

        :id: cc0f8f40-5ea6-4fa7-8154-acdc2cb56b45

        :expectedresults: you are able to enable and synchronize repository
            contained in a manifest

        :CaseLevel: Integration

        :CaseImportance: Critical
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

    @tier3
    def test_positive_manifest_history(self):
        """upload manifest and check history

        :id: 000ab0a0-ec1b-497a-84ff-3969a965b52c

        :expectedresults: Manifest history is shown properly

        :CaseImportance: Medium
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

        :id: 579bbbf7-11cf-4d78-a3b1-16d73bd4ca57

        :expectedresults: Manifests can be refreshed

        :CaseImportance: Critical
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
    @tier2
    def test_negative_manifest_refresh(self):
        """manifest refresh must fail with a cloned manifest

        :id: 7f40795f-7841-4063-8a43-de0325c92b1f

        :expectedresults: the refresh command returns a non-zero return code

        :BZ: 1226425

        :CaseImportance: High
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

    @skip_if_bug_open('bugzilla', 1686916)
    @tier2
    def test_positive_subscription_list(self):
        """Verify that subscription list contains start and end date

        :id: 4861bcbc-785a-436d-98ce-14cfef7d6907

        :expectedresults: subscription list contains the start and end date

        :BZ: 1686916

        :CaseImportance: Medium
        """
        self._upload_manifest(self.org['id'])
        subscription_list = Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False,
        )
        for column in ['start-date', 'end-date']:
            self.assertTrue(column in subscription_list[0].keys())
