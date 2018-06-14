"""Test class for Subscriptions

:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import tempfile
import csv
import os

from robottelo import manifests
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.csv_ import CSV_
from robottelo.cli.factory import (
    activationkey_add_subscription_to_repo,
    make_activation_key,
    make_lifecycle_environment,
    make_org,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.host import Host
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.constants import (
    PRDS,
    REPOS,
    REPOSET,
    DEFAULT_SUBSCRIPTION_NAME,
    SATELLITE_SUBSCRIPTION_NAME,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.ssh import download_file, upload_file
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


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

    @tier1
    def test_positive_manifest_history(self):
        """upload manifest and check history

        :id: 000ab0a0-ec1b-497a-84ff-3969a965b52c

        :expectedresults: Manifest history is shown properly

        :CaseImportance: Critical
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
    @tier1
    def test_negative_manifest_refresh(self):
        """manifest refresh must fail with a cloned manifest

        :id: 7f40795f-7841-4063-8a43-de0325c92b1f

        :expectedresults: the refresh command returns a non-zero return code

        :BZ: 1226425

        :CaseImportance: Critical
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

    @tier3
    def test_positive_restore_ak_and_content_hosts_subscriptions(self):
        """Restore activation key and content hosts subscriptions

        :id: a44fdeda-9c8c-4316-85b4-a9b6b9f1ffdb

        :customerscenario: true

        :steps:
            1. Setup activation key , lifecycle environment and content view
               with RH repository
            2. Add RH subscription to activation key
            3. Setup hosts (minimum two) and subscribe them to activation key
            4. Attach RH subscription to the created content hosts
            5. export the activation key and content hosts subscriptions
            6. Delete the subscription manifest
            7. Ensure that the activation key and content hosts subscriptions
               does not exist
            8. Upload the subscription manifest
            9. Ensure the activation key and content hosts subscriptions does
               not exist
            10. Restore the activation key and content hosts subscriptions

        :expectedresults: activation key and content hosts subscriptions
            restored

        :CaseImportance: Critical
        """
        lce = make_lifecycle_environment({'organization-id': self.org['id']})
        activation_key = make_activation_key({
            'organization-id': self.org['id'],
            'lifecycle-environment-id': lce['id'],
        })
        ActivationKey.update({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
            'auto-attach': 'false',
        })
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': self.org['id'],
            'lifecycle-environment-id': lce['id'],
            'activationkey-id': activation_key['id'],
        }, force_use_cdn=True)
        org_subs = Subscription.list({u'organization-id': self.org['id']})
        default_subscription_id = None
        for sub in org_subs:
            if sub['name'] == DEFAULT_SUBSCRIPTION_NAME:
                default_subscription_id = sub['id']
                break
        self.assertIsNotNone(
            default_subscription_id, msg='Default subscription not found')
        ak_subs = ActivationKey.subscriptions({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
        }, output_format='json')
        self.assertIn(
            DEFAULT_SUBSCRIPTION_NAME, [sub['name'] for sub in ak_subs])
        with VirtualMachine() as client1, VirtualMachine() as client2:
            hosts = []
            for client in [client1, client2]:
                client.install_katello_ca()
                client.register_contenthost(
                    self.org['label'], activation_key=activation_key['name'])
                self.assertTrue(client.subscribed)
                host = Host.info({'name': client.hostname})
                hosts.append(host)
                Host.subscription_attach({
                    'host-id': host['id'],
                    'subscription-id': default_subscription_id,
                })
                host_subscriptions = ActivationKey.subscriptions({
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'host-id': host['id'],
                }, output_format='json')
                self.assertIn(
                    DEFAULT_SUBSCRIPTION_NAME,
                    [sub['name'] for sub in host_subscriptions]
                )
            # export the current activations and content hosts subscriptions
            ak_file_path = '/tmp/ak_{0}.csv'.format(self.org['label'])
            ch_file_path = '/tmp/content_hosts_{0}.csv'.format(
                self.org['label'])
            CSV_.activation_keys({
                'export': True,
                'file': ak_file_path,
                'organization': self.org['name'],
                'itemized-subscriptions': True,
            })
            CSV_.content_hosts({
                'export': True,
                'file': ch_file_path,
                'organization': self.org['name'],
                'itemized-subscriptions': True,
            })
            # delete the manifest
            Subscription.delete_manifest({'organization-id': self.org['id']})
            # ensure that the subscription does not exist any more
            ak_subs = ActivationKey.subscriptions({
                'organization-id': self.org['id'],
                'id': activation_key['id'],
            }, output_format='json')
            self.assertNotIn(
                DEFAULT_SUBSCRIPTION_NAME, [sub['name'] for sub in ak_subs])
            for host in hosts:
                host_subscriptions = ActivationKey.subscriptions({
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'host-id': host['id'],
                }, output_format='json')
                self.assertNotIn(
                    DEFAULT_SUBSCRIPTION_NAME,
                    [sub['name'] for sub in host_subscriptions]
                )
            # upload the manifest again
            self._upload_manifest(self.org['id'])
            # ensure that the subscription was not auto attached
            ak_subs = ActivationKey.subscriptions({
                'organization-id': self.org['id'],
                'id': activation_key['id'],
            }, output_format='json')
            self.assertNotIn(
                DEFAULT_SUBSCRIPTION_NAME, [sub['name'] for sub in ak_subs])
            for host in hosts:
                host_subscriptions = ActivationKey.subscriptions({
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'host-id': host['id'],
                }, output_format='json')
                self.assertNotIn(
                    DEFAULT_SUBSCRIPTION_NAME,
                    [sub['name'] for sub in host_subscriptions]
                )
            # restore from the saved activation key and content hosts
            # subscriptions
            CSV_.activation_keys({
                'file': ak_file_path,
                'organization': self.org['name'],
                'itemized-subscriptions': True,
            })
            CSV_.content_hosts({
                'file': ch_file_path,
                'organization': self.org['name'],
                'itemized-subscriptions': True,
            })
            # ensure that the subscriptions has been restored
            ak_subs = ActivationKey.subscriptions({
                'organization-id': self.org['id'],
                'id': activation_key['id'],
            }, output_format='json')
            self.assertIn(
                DEFAULT_SUBSCRIPTION_NAME, [sub['name'] for sub in ak_subs])
            for host in hosts:
                host_subscriptions = ActivationKey.subscriptions({
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'host-id': host['id'],
                }, output_format='json')
                self.assertIn(
                    DEFAULT_SUBSCRIPTION_NAME,
                    [sub['name'] for sub in host_subscriptions]
                )

    @tier3
    def test_positive_restore_content_hosts_with_modified_subscription(self):
        """Restore content hosts subscription from an exported content host csv
        file with modified subscription.

        :id: d8ac08fe-24e0-41e7-b3d8-0ca13a702a64

        :customerscenario: true

        :steps:
            1. Setup activation key , lifecycle environment and content view
               with RH tools repository
            2. Setup hosts (minimum two) and subscribe them to activation key
            3. Attach RH subscription to the created content hosts
            4. Export the organization content hosts to a csv file
            5. Create a new csv file and modify the subscription with an other
               one (the new subscription must have other data than the default
               one)
            6. Import the new csv file to organization content hosts

        :expectedresults: content hosts restored with the new subscription

        :BZ: 1296978

        :CaseImportance: Critical
        """
        lce = make_lifecycle_environment({'organization-id': self.org['id']})
        activation_key = make_activation_key({
            'organization-id': self.org['id'],
            'lifecycle-environment-id': lce['id'],
        })
        ActivationKey.update({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
            'auto-attach': 'false',
        })
        # Create RH tools repository and contents, this step should upload
        # the default manifest
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': self.org['id'],
            'lifecycle-environment-id': lce['id'],
            'activationkey-id': activation_key['id'],
        }, force_use_cdn=True)
        # Export and download the organization subscriptions to prepare the new
        # subscription (The replacement of the default subscription)
        org_subs_csv_filename = 'subs_{0}.csv'.format(self.org['name'])
        org_subs_csv_remote_file_path = '/tmp/{0}'.format(
            org_subs_csv_filename)
        # export organization subscription to csv file
        CSV_.subscriptions({
            'export': True,
            'file': org_subs_csv_remote_file_path,
            'organization': self.org['name'],
        })
        # download the organization subscriptions
        org_subs_csv_local_file_path = os.path.join(
            tempfile.gettempdir(), org_subs_csv_filename)
        download_file(
            org_subs_csv_remote_file_path, org_subs_csv_local_file_path)
        _, org_subscriptions = self._read_csv_file(
            org_subs_csv_local_file_path)
        new_subscription = None
        for sub in org_subscriptions:
            if sub['Subscription Name'] == SATELLITE_SUBSCRIPTION_NAME:
                new_subscription = sub
                break
        self.assertIsNotNone(new_subscription)
        # retrieve the default subscription id
        org_subs = Subscription.list({u'organization-id': self.org['id']})
        default_subscription_id = None
        for sub in org_subs:
            if sub['name'] == DEFAULT_SUBSCRIPTION_NAME:
                default_subscription_id = sub['id']
                break
        self.assertIsNotNone(
            default_subscription_id, msg='Default subscription not found')
        # create 2 Virtual machines
        with VirtualMachine() as client1, VirtualMachine() as client2:
            hosts = []
            for client in [client1, client2]:
                client.install_katello_ca()
                client.register_contenthost(
                    self.org['label'], activation_key=activation_key['name'])
                self.assertTrue(client.subscribed)
                host = Host.info({'name': client.hostname})
                hosts.append(host)
                Host.subscription_attach({
                    'host-id': host['id'],
                    'subscription-id': default_subscription_id,
                })
                host_subscriptions = ActivationKey.subscriptions({
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'host-id': host['id'],
                }, output_format='json')
                self.assertEqual(len(host_subscriptions), 1)
                self.assertEqual(
                    host_subscriptions[0]['name'], DEFAULT_SUBSCRIPTION_NAME)
            # export the content host data to csv file
            chs_export_file_name = 'chs_export_{0}.csv'.format(
                self.org['label'])
            chs_export_remote_file_path = (
                '/tmp/{0}'.format(chs_export_file_name)
            )
            CSV_.content_hosts({
                'export': True,
                'file': chs_export_remote_file_path,
                'organization': self.org['name'],
            })
            # download the csv file
            chs_export_local_file_path = os.path.join(
                tempfile.gettempdir(), chs_export_file_name)
            download_file(
                chs_export_remote_file_path, chs_export_local_file_path)
            # modify the content hosts subscription
            field_names, csv_data = self._read_csv_file(
                chs_export_local_file_path)
            # each client is represented by one row of data
            self.assertEqual(len(csv_data), 2)
            for row_data in csv_data:
                # The subscription is saved in the following format:
                # """<quantity>|<sku>|<name>|<contract>|<account>"""
                subscription_data = row_data['Subscriptions'].strip(
                    '"').split('|')
                # change the subscription SKU (looks like RH00001)
                subscription_data[1] = new_subscription['Subscription SKU']
                # change the name
                subscription_data[2] = new_subscription['Subscription Name']
                # change the contract number
                subscription_data[3] = new_subscription[
                    'Subscription Contract']
                # change the subscription account
                subscription_data[4] = new_subscription[
                    'Subscription Account']
                # modify the subscription data
                row_data['Subscriptions'] = '"{0}"'.format(
                    '|'.join(subscription_data))
            # generate a new csv file
            chs_import_file_name = 'chs_import_{0}.csv'.format(
                self.org['name'])
            chs_import_local_file_path = os.path.join(
                tempfile.gettempdir(), chs_import_file_name)
            self._write_csv_file(
                chs_import_local_file_path, field_names, csv_data)
            # upload the file
            chs_import_remote_file_path = (
                '/tmp/{0}'.format(chs_import_file_name)
            )
            upload_file(
                chs_import_local_file_path, chs_import_remote_file_path)
            # import content hosts data from csv file
            CSV_.content_hosts({
                'file': chs_import_remote_file_path,
                'organization': self.org['name'],
            })
            for host in hosts:
                host_subscriptions = ActivationKey.subscriptions({
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'host-id': host['id'],
                }, output_format='json')
                self.assertEqual(len(host_subscriptions), 1)
                self.assertEqual(
                    host_subscriptions[0]['name'], SATELLITE_SUBSCRIPTION_NAME)
                self.assertEqual(
                    host_subscriptions[0]['contract'],
                    new_subscription['Subscription Contract'])
                self.assertEqual(
                    host_subscriptions[0]['account'],
                    new_subscription['Subscription Account'])

    @tier3
    def test_positive_restore_ak_with_modified_subscription(self):
        """Restore activation key subscription from an exported activation key
        csv file with modified subscription.

        :id: 40b86d1c-88f8-451c-bf19-c5bf11223cb6

        :steps:
            1. Upload a manifest
            2. Create an activation key
            3. Attach RH subscription to the created activation key
            4. Export the organization activation keys to a csv file
            5. Create a new csv file and modify the subscription with an other
               one (the new subscription must have other data than the default
               one)
            6. Import the new csv file to organization activation keys

        :expectedresults: activation key restored with the new subscription

        :BZ: 1296978

        :CaseImportance: Critical
        """
        # upload the organization default manifest
        self._upload_manifest(self.org['id'])
        # Export and download the organization subscriptions to prepare the new
        # subscription (The replacement of the default subscription)
        org_subs_csv_filename = 'subs_{0}.csv'.format(self.org['name'])
        org_subs_csv_remote_file_path = '/tmp/{0}'.format(
            org_subs_csv_filename)
        # export organization subscription to csv file
        CSV_.subscriptions({
            'export': True,
            'file': org_subs_csv_remote_file_path,
            'organization': self.org['name'],
        })
        # download the organization subscriptions
        org_subs_csv_local_file_path = os.path.join(
            tempfile.gettempdir(), org_subs_csv_filename)
        download_file(
            org_subs_csv_remote_file_path, org_subs_csv_local_file_path)
        _, org_subscriptions = self._read_csv_file(
            org_subs_csv_local_file_path)
        new_subscription = None
        for sub in org_subscriptions:
            if sub['Subscription Name'] == SATELLITE_SUBSCRIPTION_NAME:
                new_subscription = sub
                break
        self.assertIsNotNone(new_subscription)
        # Create an activation key and add the default subscription
        activation_key = make_activation_key({
            'organization-id': self.org['id'],
        })
        activationkey_add_subscription_to_repo({
            'organization-id': self.org['id'],
            'activationkey-id': activation_key['id'],
            'subscription': DEFAULT_SUBSCRIPTION_NAME,
        })
        org_subs = Subscription.list({u'organization-id': self.org['id']})
        default_subscription_id = None
        for sub in org_subs:
            if sub['name'] == DEFAULT_SUBSCRIPTION_NAME:
                default_subscription_id = sub['id']
                break
        self.assertIsNotNone(
            default_subscription_id, msg='Default subscription not found')
        ak_subs = ActivationKey.subscriptions({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
        }, output_format='json')
        self.assertEqual(len(ak_subs), 1)
        self.assertEqual(
            ak_subs[0]['name'], DEFAULT_SUBSCRIPTION_NAME)
        # export activation key data to csv file
        ak_export_file_name = 'ak_{0}_{1}_export.csv'.format(
            self.org['name'], activation_key['name'])
        ak_remote_export_file_path = '/tmp/{0}'.format(ak_export_file_name)
        CSV_.activation_keys({
            'export': True,
            'file': ak_remote_export_file_path,
            'organization': self.org['name'],
        })
        # download the file to local temp dir
        ak_local_export_file_path = os.path.join(
            tempfile.gettempdir(), ak_export_file_name)
        download_file(
            ak_remote_export_file_path, local_file=ak_local_export_file_path)
        # modify the file with new subscription data and upload it
        field_names, csv_ak_data = self._read_csv_file(
            ak_local_export_file_path)
        self.assertEqual(len(csv_ak_data), 1)
        csv_ak_data = csv_ak_data[0]
        field_names = csv_ak_data.keys()
        self.assertIn('Subscriptions', field_names)
        self.assertIn('Subscriptions', csv_ak_data)
        # The subscription is saved in the following format:
        # """<quantity>|<sku>|<name>|<contract>|<account>"""
        subscription_data = csv_ak_data['Subscriptions'].strip('"').split('|')
        # change the subscription SKU (looks like RH00001)
        subscription_data[1] = new_subscription['Subscription SKU']
        # change the name
        subscription_data[2] = new_subscription['Subscription Name']
        # change the contract number
        subscription_data[3] = new_subscription['Subscription Contract']
        # change the subscription account
        subscription_data[4] = new_subscription['Subscription Account']
        # modify the subscription data and generate a new csv file
        csv_ak_data['Subscriptions'] = '"{0}"'.format(
            '|'.join(subscription_data))
        ak_import_file_name = 'ak_{0}_{1}_import.csv'.format(
            self.org['name'], activation_key['name'])
        ak_local_import_file_path = os.path.join(
            tempfile.gettempdir(), ak_import_file_name)
        self._write_csv_file(
            ak_local_import_file_path, field_names, [csv_ak_data])
        # upload the generated file
        ak_remote_import_file_path = '/tmp/{0}'.format(ak_import_file_name)
        upload_file(ak_local_import_file_path, ak_remote_import_file_path)
        # import the generated csv file
        CSV_.activation_keys({
            'file': ak_remote_import_file_path,
            'organization': self.org['name'],
        })
        ak_subs = ActivationKey.subscriptions({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
        }, output_format='json')
        self.assertEqual(len(ak_subs), 1)
        self.assertEqual(
            ak_subs[0]['name'], SATELLITE_SUBSCRIPTION_NAME)
        self.assertEqual(
            ak_subs[0]['contract'],
            new_subscription['Subscription Contract'])
        self.assertEqual(
            ak_subs[0]['account'], new_subscription['Subscription Account'])
