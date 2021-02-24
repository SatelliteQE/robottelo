"""Test class for Subscriptions

:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SubscriptionManagement

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import csv

import pytest
from broker.broker import VMBroker
from fauxfactory import gen_string
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_activation_key
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.host import Host
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.hosts import ContentHost
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


@pytest.fixture(scope='class')
def golden_ticket_host_setup(request):
    org = make_org()
    with manifests.clone(name='golden_ticket') as manifest:
        upload_manifest(org['id'], manifest.content)
    new_product = make_product({'organization-id': org['id']})
    new_repo = make_repository({'product-id': new_product['id']})
    Repository.synchronize({'id': new_repo['id']})
    new_ak = make_activation_key(
        {
            'lifecycle-environment': 'Library',
            'content-view': 'Default Organization View',
            'organization-id': org['id'],
            'auto-attach': False,
        }
    )
    request.cls.org_setup = org
    request.cls.ak_setup = new_ak


@pytest.mark.run_in_one_thread
class SubscriptionTestCase(CLITestCase):
    """Manifest CLI tests"""

    def setUp(self):
        """Tests for content-view via Hammer CLI"""
        super().setUp()
        self.org = make_org()

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
        with open(file_path) as csv_file:
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

    @pytest.mark.tier1
    def test_positive_manifest_upload(self):
        """upload manifest

        :id: e5a0e4f8-fed9-4896-87a0-ac33f6baa227

        :expectedresults: Manifest are uploaded properly

        :CaseImportance: Critical
        """
        self._upload_manifest(self.org['id'])
        Subscription.list({'organization-id': self.org['id']}, per_page=False)

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_manifest_delete(self):
        """Delete uploaded manifest

        :id: 01539c07-00d5-47e2-95eb-c0fd4f39090f

        :expectedresults: Manifest are deleted properly

        :CaseImportance: Critical
        """
        self._upload_manifest(self.org['id'])
        Subscription.list({'organization-id': self.org['id']}, per_page=False)
        Subscription.delete_manifest({'organization-id': self.org['id']})
        Subscription.list({'organization-id': self.org['id']}, per_page=False)

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_enable_manifest_reposet(self):
        """enable repository set

        :id: cc0f8f40-5ea6-4fa7-8154-acdc2cb56b45

        :expectedresults: you are able to enable and synchronize repository
            contained in a manifest

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        self._upload_manifest(self.org['id'])
        Subscription.list({'organization-id': self.org['id']}, per_page=False)
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': REPOSET['rhva6'],
                'organization-id': self.org['id'],
                'product': PRDS['rhel'],
                'releasever': '6Server',
            }
        )
        Repository.synchronize(
            {
                'name': REPOS['rhva6']['name'],
                'organization-id': self.org['id'],
                'product': PRDS['rhel'],
            }
        )

    @pytest.mark.tier3
    def test_positive_manifest_history(self):
        """upload manifest and check history

        :id: 000ab0a0-ec1b-497a-84ff-3969a965b52c

        :expectedresults: Manifest history is shown properly

        :CaseImportance: Medium
        """
        self._upload_manifest(self.org['id'])
        Subscription.list({'organization-id': self.org['id']}, per_page=None)
        history = Subscription.manifest_history({'organization-id': self.org['id']})
        assert '{} file imported successfully.'.format(self.org['name']) in ''.join(history)

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_manifest_refresh(self):
        """upload manifest and refresh

        :id: 579bbbf7-11cf-4d78-a3b1-16d73bd4ca57

        :expectedresults: Manifests can be refreshed

        :CaseImportance: Critical
        """
        self._upload_manifest(self.org['id'], manifests.original_manifest())
        Subscription.list({'organization-id': self.org['id']}, per_page=False)
        Subscription.refresh_manifest({'organization-id': self.org['id']})
        Subscription.delete_manifest({'organization-id': self.org['id']})

    @pytest.mark.skip_if_open("BZ:1686916")
    @pytest.mark.tier2
    def test_positive_subscription_list(self):
        """Verify that subscription list contains start and end date

        :id: 4861bcbc-785a-436d-98ce-14cfef7d6907

        :expectedresults: subscription list contains the start and end date

        :BZ: 1686916

        :CaseImportance: Medium
        """
        self._upload_manifest(self.org['id'])
        subscription_list = Subscription.list({'organization-id': self.org['id']}, per_page=False)
        for column in ['start-date', 'end-date']:
            assert column in subscription_list[0].keys()

    @pytest.mark.tier2
    def test_positive_delete_manifest_as_another_user(self):
        """Verify that uploaded manifest if visible and deletable
            by a different user than the one who uploaded it

        :id: 4861bcbc-785a-436d-98cf-13cfef7d6907

        :expectedresults: manifest is refreshed

        :BZ: 1669241

        :CaseImportance: Medium
        """
        org = entities.Organization().create()
        user1_password = gen_string('alphanumeric')
        user1 = entities.User(
            admin=True, password=user1_password, organization=[org], default_organization=org
        ).create()
        user2_password = gen_string('alphanumeric')
        user2 = entities.User(
            admin=True, password=user2_password, organization=[org], default_organization=org
        ).create()
        # use the first admin to upload a manifest
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.with_user(username=user1.login, password=user1_password).upload(
            {'file': manifest.filename, 'organization-id': org.id}
        )
        # try to search and delete the manifest with another admin
        Subscription.with_user(username=user2.login, password=user2_password).delete_manifest(
            {'organization-id': org.id}
        )
        assert len(Subscription.list({'organization-id': org.id})) == 0

    @pytest.mark.tier2
    @pytest.mark.stubbed
    @pytest.mark.usefixtures("golden_ticket_host_setup")
    def test_positive_subscription_status_disabled_golden_ticket(self):
        """Verify that Content host Subscription status is set to 'Disabled'
         for a golden ticket manifest

        :id: 42e10499-3a0d-48cd-ab71-022421a74add

        :expectedresults: subscription status is 'Disabled'

        :BZ: 1789924

        :CaseImportance: Medium
        """

    @pytest.mark.stubbed
    def test_positive_candlepin_events_processed_by_STOMP(self):
        """Verify that Candlepin events are being read and processed by
           attaching subscriptions, validating host subscriptions status,
           and viewing processed and failed Candlepin events

        :id: d54a7652-f87d-4277-a0ec-a153e27b4487

        :steps:

            1. Register Content Host without subscriptions attached
            2. Verify subscriptions status is invalid
            3. Import a Manifest
            4. Attach subs to content host
            5. Verify subscription status is green, "valid", with
               "hammer subscription list --host-id x"
            6. Check for processed and failed Candlepin events

        :expectedresults: Candlepin events are being read and processed
                          correctly without any failures
        :BZ: #1826515

        :CaseImportance: High
        """

    @pytest.mark.tier2
    @pytest.mark.libvirt_content_host
    @pytest.mark.usefixtures("golden_ticket_host_setup")
    def test_positive_auto_attach_disabled_golden_ticket(self):
        """Verify that Auto-Attach is disabled or "Not Applicable"
        when a host organization is in Simple Content Access mode (Golden Ticket)

        :id: 668fae4d-7364-4167-967f-6fc31ba52d26

        :expectedresults: auto attaching a subscription is not allowed
            and returns an error message

        :BZ: 1718954

        :CaseImportance: Medium
        """
        with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.org_setup['label'], self.ak_setup['name'])
            assert vm.subscribed
            host = Host.list({'search': vm.hostname})
            host_id = host[0]['id']
            with pytest.raises(CLIReturnCodeError) as context:
                Host.subscription_auto_attach({'host-id': host_id})
            assert "This host's organization is in Simple Content Access mode" in str(
                context.value
            )
