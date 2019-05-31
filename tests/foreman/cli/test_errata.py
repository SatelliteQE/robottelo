"""CLI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ErrataManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from operator import itemgetter
from fauxfactory import gen_string
from robottelo import manifests, ssh
from robottelo.cleanup import vm_cleanup
from robottelo.cli.factory import (
    make_activation_key,
    make_content_view,
    make_filter,
    make_host_collection,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
    make_role,
    make_user,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.task import Task
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.erratum import Erratum
from robottelo.cli.filter import Filter
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.org import Org
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.constants import (
    DISTRO_RHEL7,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_0_ERRATA_ID,
    FAKE_1_ERRATA_ID,
    FAKE_2_ERRATA_ID,
    FAKE_3_ERRATA_ID,
    FAKE_0_YUM_ERRATUM_COUNT,
    FAKE_1_YUM_ERRATUM_COUNT,
    FAKE_3_YUM_ERRATUM_COUNT,
    FAKE_6_YUM_ERRATUM_COUNT,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    FAKE_3_YUM_REPO,
    FAKE_6_YUM_REPO,
    REAL_4_ERRATA_ID,
    REAL_4_ERRATA_CVES,
    REPOS,
    REPOSET,
    PRDS,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier3,
    upgrade,
)
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine

ERRATUM_MAX_IDS_INFO = 10


@run_in_one_thread
class HostCollectionErrataInstallTestCase(CLITestCase):
    """CLI Tests for the errata management feature"""

    CUSTOM_REPO_URL = FAKE_6_YUM_REPO
    CUSTOM_PACKAGE = FAKE_1_CUSTOM_PACKAGE
    CUSTOM_ERRATA_ID = FAKE_2_ERRATA_ID
    CUSTOM_PACKAGE_ERRATA_APPLIED = FAKE_2_CUSTOM_PACKAGE
    VIRTUAL_MACHINES_COUNT = 2

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key,
        Host, Host-Collection

        @BZ: 1405428, 1418026, 1457977
        """
        super(HostCollectionErrataInstallTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.env = make_lifecycle_environment({
            'organization-id': cls.org['id']
        })
        cls.content_view = make_content_view({
            'organization-id': cls.org['id']
        })
        cls.activation_key = make_activation_key({
            'lifecycle-environment-id': cls.env['id'],
            'organization-id': cls.org['id']
        })
        # add subscription to Satellite Tools repo to activation key
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': cls.org['id'],
            'content-view-id': cls.content_view['id'],
            'lifecycle-environment-id': cls.env['id'],
            'activationkey-id': cls.activation_key['id']
        })
        # create custom repository and add subscription to activation key
        setup_org_for_a_custom_repo({
            'url': cls.CUSTOM_REPO_URL,
            'organization-id': cls.org['id'],
            'content-view-id': cls.content_view['id'],
            'lifecycle-environment-id': cls.env['id'],
            'activationkey-id': cls.activation_key['id']
        })

    def setUp(self):
        """Create and setup host collection, hosts and virtual machines."""
        super(HostCollectionErrataInstallTestCase, self).setUp()
        self.virtual_machines = []
        self.host_collection = make_host_collection({
            'organization-id': self.org['id']
        })
        for _ in range(self.VIRTUAL_MACHINES_COUNT):
            # create VM
            virtual_machine = VirtualMachine(distro=DISTRO_RHEL7)
            virtual_machine.create()
            self.addCleanup(vm_cleanup, virtual_machine)
            self.virtual_machines.append(virtual_machine)
            virtual_machine.install_katello_ca()
            # register content host
            virtual_machine.register_contenthost(
                self.org['name'],
                activation_key=self.activation_key['name']
            )
            # enable red hat satellite repository
            virtual_machine.enable_repo(REPOS['rhst7']['id'])
            # install katello-agent
            virtual_machine.install_katello_agent()
            host = Host.info({'name': virtual_machine.hostname})
            HostCollection.add_host({
                'id': self.host_collection['id'],
                'organization-id': self.org['id'],
                'host-ids': host['id']
            })
        ActivationKey.add_host_collection({
            'id': self.activation_key['id'],
            'host-collection-id': self.host_collection['id'],
            'organization-id': self.org['id']
        })
        # install the custom package for each host
        for virtual_machine in self.virtual_machines:
            virtual_machine.run(
                'yum install -y {0}'.format(self.CUSTOM_PACKAGE)
            )
            result = virtual_machine.run(
                'rpm -q {0}'.format(self.CUSTOM_PACKAGE))
            self.assertEqual(result.return_code, 0)

    def _is_errata_package_installed(self, virtual_machine):
        """Check whether errata package is installed.

        :type virtual_machine: robottelo.vm.VirtualMachine
        :rtype: bool
        """
        result = virtual_machine.run(
            'rpm -q {0}'.format(self.CUSTOM_PACKAGE_ERRATA_APPLIED))
        return True if result.return_code == 0 else False

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1457977)
    @tier3
    def test_positive_install_by_hc_id_and_org_id(self):
        """Using hc-id and org id to install an erratum in a hc

        :id: 8b22eb9d-1321-4374-8127-6d7bfdb89ad5

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata> --id <id>
            --organization-id <orgid>

        :expectedresults: Erratum is installed.

        :CaseLevel: System
        """
        install_task = HostCollection.erratum_install({
            'id': self.host_collection['id'],
            'organization-id': self.org['id'],
            'errata': [self.CUSTOM_ERRATA_ID]
        })
        Task.progress({'id': install_task[0]['id']})
        for virtual_machine in self.virtual_machines:
            self.assertTrue(self._is_errata_package_installed(virtual_machine))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1457977)
    @tier3
    def test_positive_install_by_hc_id_and_org_name(self):
        """Using hc-id and org name to install an erratum in a hc

        :id: 7e5b87d7-f4d2-47b7-96aa-f86bcb64c742

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata> --id <id>
            --organization <org name>

        :expectedresults: Erratum is installed.

        :CaseLevel: System
        """
        install_task = HostCollection.erratum_install({
            'id': self.host_collection['id'],
            'organization': self.org['name'],
            'errata': [self.CUSTOM_ERRATA_ID]
        })
        Task.progress({'id': install_task[0]['id']})
        for virtual_machine in self.virtual_machines:
            self.assertTrue(self._is_errata_package_installed(virtual_machine))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1457977)
    @tier3
    def test_positive_install_by_hc_id_and_org_label(self):
        """Use hc-id and org label to install an erratum in a hc

        :id: bde80181-6526-43dc-bfc2-511bb5c00676

        :Setup: errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata> --id <id>
            --organization-label <org label>

        :expectedresults: Errata is installed.

        :CaseLevel: System
        """
        install_task = HostCollection.erratum_install({
            'id': self.host_collection['id'],
            'organization-label': self.org['label'],
            'errata': [self.CUSTOM_ERRATA_ID]
        })
        Task.progress({'id': install_task[0]['id']})
        for virtual_machine in self.virtual_machines:
            self.assertTrue(self._is_errata_package_installed(virtual_machine))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1457977)
    @tier3
    def test_positive_install_by_hc_name_and_org_id(self):
        """Use hc-name and org id to install an erratum in a hc

        :id: c4a38806-cbec-47cc-bbd6-228897b3b16d

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata> --name <name>
            --organization-id <orgid>

        :expectedresults: Erratum is installed.

        :CaseLevel: System
        """
        install_task = HostCollection.erratum_install({
            'name': self.host_collection['name'],
            'organization-id': self.org['id'],
            'errata': [self.CUSTOM_ERRATA_ID]
        })
        Task.progress({'id': install_task[0]['id']})
        for virtual_machine in self.virtual_machines:
            self.assertTrue(self._is_errata_package_installed(virtual_machine))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1457977)
    @tier3
    def test_positive_install_by_hc_name_and_org_name(self):
        """Use hc name and org name to install an erratum in a hc

        :id: 501319ea-9d3c-4329-9405-4366ce6ee797

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata> --name <name>
            --organization <org name>

        :expectedresults: Erratum is installed.

        :CaseLevel: System
        """
        install_task = HostCollection.erratum_install({
            'name': self.host_collection['name'],
            'organization': self.org['name'],
            'errata': [self.CUSTOM_ERRATA_ID]
        })
        Task.progress({'id': install_task[0]['id']})
        for virtual_machine in self.virtual_machines:
            self.assertTrue(self._is_errata_package_installed(virtual_machine))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1457977)
    @tier3
    def test_positive_install_by_hc_name_and_org_label(self):
        """Use hc-name and org label to install an erratum in a hc

        :id: 12287827-44df-4dda-872a-ac7e416e8bd7

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata> --name <name>
            --organization-label <org label>

        :expectedresults: Erratum is installed.

        :CaseLevel: System
        """
        install_task = HostCollection.erratum_install({
            'name': self.host_collection['name'],
            'organization-label': self.org['label'],
            'errata': [self.CUSTOM_ERRATA_ID]
        })
        Task.progress({'id': install_task[0]['id']})
        for virtual_machine in self.virtual_machines:
            self.assertTrue(self._is_errata_package_installed(virtual_machine))

    @tier3
    @run_only_on('sat')
    def test_negative_install_by_hc_id_without_errata_info(self):
        """Attempt to install an erratum in a hc using hc-id and not
        specifying the erratum info

        :id: 3635698d-4f09-4a60-91ea-1957e5949750

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --id <id> --organization-id
            <orgid>

        :expectedresults: Error message thrown.

        :CaseImportance: Low

        :CaseLevel: System
        """
        with self.assertRaises(CLIReturnCodeError) as context:
            HostCollection.erratum_install({
                'id': self.host_collection['id'],
                'organization-id': self.org['id'],
            })
        self.assertIn(
            "Error: Option '--errata' is required",
            context.exception.stderr
        )

    @tier3
    @run_only_on('sat')
    def test_negative_install_by_hc_name_without_errata_info(self):
        """Attempt to install an erratum in a hc using hc-name and not
        specifying the erratum info

        :id: 12d78bca-efd1-407a-9bd3-f989c2bda6a8

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --name <name> --organization-id
            <orgid>

        :expectedresults: Error message thrown.

        :CaseImportance: Low

        :CaseLevel: System
        """
        with self.assertRaises(CLIReturnCodeError) as context:
            HostCollection.erratum_install({
                'name': self.host_collection['name'],
                'organization-id': self.org['id'],
            })
        self.assertIn(
            "Error: Option '--errata' is required",
            context.exception.stderr
        )

    @tier3
    @run_only_on('sat')
    def test_negative_install_without_hc_info(self):
        """Attempt to install an erratum in a hc by not specifying hc
        info

        :id: 753d36f0-d19b-494d-a247-ce2d61c4cf74

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata>
            --organization-id <orgid>

        :expectedresults: Error message thrown.

        :CaseImportance: Low

        :CaseLevel: System
        """
        with self.assertRaises(CLIReturnCodeError):
            HostCollection.erratum_install({
                'organization-id': self.org['id'],
                'errata': [self.CUSTOM_ERRATA_ID]
            })

    @tier3
    @run_only_on('sat')
    def test_negative_install_by_hc_id_without_org_info(self):
        """Attempt to install an erratum in a hc using hc-id and not
        specifying org info

        :id: b7d32bb3-9c5f-452b-b421-f8e9976ca52c

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata> --id <id>

        :expectedresults: Error message thrown.

        :CaseImportance: Low

        :CaseLevel: System
        """
        with self.assertRaises(CLIReturnCodeError) as context:
            HostCollection.erratum_install({
                'id': self.host_collection['id'],
                'errata': [self.CUSTOM_ERRATA_ID]
            })
        self.assertIn(
            'Error: Could not find organization',
            context.exception.stderr
        )

    @tier3
    @run_only_on('sat')
    def test_negative_install_by_hc_name_without_org_info(self):
        """Attempt to install an erratum in a hc without specifying org
        info

        :id: 991f5b61-a4d1-444c-8a21-8ffe48e83f76

        :Setup: Errata synced on satellite server.

        :Steps: host-collection erratum install --errata <errata> --name <name>

        :expectedresults: Error message thrown.

        :CaseImportance: Low

        :CaseLevel: System
        """
        with self.assertRaises(CLIReturnCodeError) as context:
            HostCollection.erratum_install({
                'name': self.host_collection['name'],
                'errata': [self.CUSTOM_ERRATA_ID]
            })
        self.assertIn(
            'Error: Could not find organization',
            context.exception.stderr
        )


class ErrataTestCase(CLITestCase):
    """Hammer CLI Tests for Erratum command"""

    @classmethod
    def setUpClass(cls):
        """Create 3 organizations

           1. Create an org with one custom product & repository
           2. Create an other org with an other custom product & repository
           3. Create a multi products org with two other products, each
              containing one custom repository

           note: all products repositories contain erratum
           """
        super(ErrataTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.org_product = make_product(
            options={'organization-id': cls.org['id']})
        repo = make_repository({
            'download-policy': 'immediate',
            'organization-id': cls.org['id'],
            'product-id': cls.org_product['id'],
            'url': FAKE_6_YUM_REPO
        })
        Repository.synchronize({'id': repo['id']})
        cls.org_product_erratum_count = FAKE_6_YUM_ERRATUM_COUNT
        cls.org_product_errata_id = FAKE_2_ERRATA_ID
        # create an other org
        cls.errata_org = make_org()
        cls.errata_org_product = make_product(
            options={'organization-id': cls.errata_org['id']})
        repo = make_repository({
            'download-policy': 'immediate',
            'organization-id': cls.errata_org['id'],
            'product-id': cls.errata_org_product['id'],
            'url': FAKE_1_YUM_REPO
        })
        Repository.synchronize({'id': repo['id']})
        cls.errata_org_product_erratum_count = FAKE_1_YUM_ERRATUM_COUNT
        cls.errata_org_product_errata_id = FAKE_1_ERRATA_ID
        # create org_multi, a new org with multi products
        cls.org_multi = make_org()
        cls.org_multi_product_small = make_product(
            options={'organization-id': cls.org_multi['id']})
        repo = make_repository({
            'download-policy': 'immediate',
            'organization-id': cls.org_multi['id'],
            'product-id': cls.org_multi_product_small['id'],
            'url': FAKE_2_YUM_REPO
        })
        Repository.synchronize({'id': repo['id']})
        cls.org_multi_product_small_erratum_count = FAKE_0_YUM_ERRATUM_COUNT
        cls.org_multi_product_small_errata_id = FAKE_0_ERRATA_ID
        cls.org_multi_product_big = make_product(
            options={'organization-id': cls.org_multi['id']})
        repo = make_repository({
            'download-policy': 'immediate',
            'organization-id': cls.org_multi['id'],
            'product-id': cls.org_multi_product_big['id'],
            'url': FAKE_3_YUM_REPO
        })
        Repository.synchronize({'id': repo['id']})
        cls.org_multi_product_big_erratum_count = FAKE_3_YUM_ERRATUM_COUNT
        cls.org_multi_product_big_errata_id = FAKE_3_ERRATA_ID

    @staticmethod
    def _get_sorted_erratum_ids_info(erratum_ids, sort_by='issued',
                                     sort_reversed=False):
        """Query hammer for erratum ids info

        :param erratum_ids: a list of errata id
        :param sort_by: the field to sort by the results (issued or updated)
        :param sort_reversed: whether the sort should be reversed
               (not ascending)
        :return: a list of errata info dict for each errata id in erratum_ids
        :type erratum_ids: list[str]
        :type sort_by: str
        :type sort_reversed: bool
        :rtype: list[dict]
        """
        if len(erratum_ids) > ERRATUM_MAX_IDS_INFO:
            raise Exception('Erratum ids length exceeded')
        erratum_info_list = []
        for errata_id in erratum_ids:
            erratum_info_list.append(
                Erratum.info(options={'id': errata_id}, output_format='json'))
        sorted_erratum_info_list = sorted(
            erratum_info_list, key=itemgetter(sort_by), reverse=sort_reversed)
        return sorted_erratum_info_list

    @tier3
    @upgrade
    def test_positive_list_sort_by_issued_date(self):
        """Sort errata by Issued date

        :id: d838a969-d70a-43ae-9805-2e94dd985d6b

        :Setup: Errata synced on satellite server.

        :Steps:

            1. erratum list --order 'issued ASC'
            2. erratum list --order 'issued DESC'

        :expectedresults: Errata is sorted by Issued date.
        """
        sort_data = [('issued', 'ASC'), ('issued', 'DESC')]
        for sort_field, sort_order in sort_data:
            sort_text = '{0} {1}'.format(sort_field, sort_order)
            sort_reversed = True if sort_order == 'DESC' else False
            with self.subTest(sort_text):
                erratum_list = Erratum.list({
                    'order': sort_text,
                    'per-page': ERRATUM_MAX_IDS_INFO
                })
                # note: the erratum_list, contain a list of restraint info
                # (id, errata-id, type, title) about each errata
                self.assertGreater(len(erratum_list), 0)
                # build a list of erratum id received from Erratum.list
                erratum_ids = [
                    errata['id']
                    for errata in erratum_list
                ]
                # build a list of errata-id field value in the same order as
                # received from Erratum.list
                errata_ids = [
                    errata['errata-id']
                    for errata in erratum_list
                ]
                # build a sorted more detailed erratum info list, that also
                # contain the sort field
                sorted_errata_info_list = self._get_sorted_erratum_ids_info(
                    erratum_ids,
                    sort_by=sort_field,
                    sort_reversed=sort_reversed
                )
                # build a list of sort field (issued/updated) values in the
                # same order as received from the detailed sorted erratum info
                # list
                sort_field_values = [
                    errata[sort_field]
                    for errata in sorted_errata_info_list
                ]
                # ensure that the sort field (issued/updated) values are sorted
                # as needed
                self.assertEqual(
                    sort_field_values,
                    sorted(sort_field_values, reverse=sort_reversed)
                )
                # build a list of errata-id field value in the same order as
                # received from the detailed sorted errata info list
                sorted_errata_ids = [
                    errata['errata-id']
                    for errata in sorted_errata_info_list
                ]
                # ensure that the errata ids received by Erratum.list is sorted
                # as needed
                self.assertEqual(errata_ids, sorted_errata_ids)

    @tier3
    def test_positive_list_filter_by_org_id_and_sort_by_updated_date(self):
        """Filter errata by org id and sort by updated date

        :id: 9b7f98ee-bbde-47b6-8727-b02550df13ae

        :Setup: Errata synced on satellite server.

        :Steps:

            1. erratum list --organization-id=<orgid> --order 'updated ASC'
            2. erratum list --organization-id=<orgid> --order 'updated DESC'

        :expectedresults: Errata is filtered by org id and sorted by updated
            date.
        """
        sort_data = [('updated', 'ASC'), ('updated', 'DESC')]
        for sort_field, sort_order in sort_data:
            sort_text = '{0} {1}'.format(sort_field, sort_order)
            sort_reversed = True if sort_order == 'DESC' else False
            with self.subTest(sort_text):
                erratum_list = Erratum.list({
                    'organization-id': self.org['id'],
                    'order': sort_text,
                    'per-page': ERRATUM_MAX_IDS_INFO
                })
                # note: the erratum_list, contain a list of restraint info
                # (id, errata-id, type, title) about each errata
                self.assertGreater(len(erratum_list), 0)
                # build a list of erratum id received from Erratum.list
                erratum_ids = [
                    errata['id']
                    for errata in erratum_list
                ]
                # build a list of errata-id field value in the same order as
                # received from Erratum.list
                errata_ids = [
                    errata['errata-id']
                    for errata in erratum_list
                ]
                # build a sorted more detailed erratum info list, that also
                # contain the sort field
                sorted_errata_info_list = self._get_sorted_erratum_ids_info(
                    erratum_ids,
                    sort_by=sort_field,
                    sort_reversed=sort_reversed
                )
                # build a list of sort field (issued/updated) values in the
                # same order as received from the detailed sorted erratum info
                # list
                sort_field_values = [
                    errata[sort_field]
                    for errata in sorted_errata_info_list
                ]
                # ensure that the sort field (issued/updated) values are sorted
                # as needed
                self.assertEqual(
                    sort_field_values,
                    sorted(sort_field_values, reverse=sort_reversed)
                )
                # build a list of errata-id field value in the same order as
                # received from the detailed sorted errata info list
                sorted_errata_ids = [
                    errata['errata-id']
                    for errata in sorted_errata_info_list
                ]
                # ensure that the errata ids received by Erratum.list is sorted
                # as needed
                self.assertEqual(errata_ids, sorted_errata_ids)

    @tier3
    def test_positive_list_filter_by_org_name_and_sort_by_updated_date(self):
        """Filter errata by org name and sort by updated date

        :id: f202616b-cd4f-4ab2-bf2a-2788579e355a

        :Setup: Errata synced on satellite server.

        :Steps:

            1. erratum list --organization=<org name> --order 'updated ASC'
            2. erratum list --organization=<org name> --order 'updated DESC'

        :expectedresults: Errata is filtered by org name and sorted by updated
            date.
        """
        sort_data = [('updated', 'ASC'), ('updated', 'DESC')]
        for sort_field, sort_order in sort_data:
            sort_text = '{0} {1}'.format(sort_field, sort_order)
            sort_reversed = True if sort_order == 'DESC' else False
            with self.subTest(sort_text):
                erratum_list = Erratum.list({
                    'organization': self.org['name'],
                    'order': sort_text,
                    'per-page': ERRATUM_MAX_IDS_INFO
                })
                # note: the erratum_list, contain a list of restraint info
                # (id, errata-id, type, title) about each errata
                self.assertGreater(len(erratum_list), 0)
                # build a list of erratum id received from Erratum.list
                erratum_ids = [
                    errata['id']
                    for errata in erratum_list
                ]
                # build a list of errata-id field value in the same order as
                # received from Erratum.list
                errata_ids = [
                    errata['errata-id']
                    for errata in erratum_list
                ]
                # build a sorted more detailed erratum info list, that also
                # contain the sort field
                sorted_errata_info_list = self._get_sorted_erratum_ids_info(
                    erratum_ids,
                    sort_by=sort_field,
                    sort_reversed=sort_reversed
                )
                # build a list of sort field (issued/updated) values in the
                # same order as received from the detailed sorted erratum info
                # list
                sort_field_values = [
                    errata[sort_field]
                    for errata in sorted_errata_info_list
                ]
                # ensure that the sort field (issued/updated) values are sorted
                # as needed
                self.assertEqual(
                    sort_field_values,
                    sorted(sort_field_values, reverse=sort_reversed)
                )
                # build a list of errata-id field value in the same order as
                # received from the detailed sorted errata info list
                sorted_errata_ids = [
                    errata['errata-id']
                    for errata in sorted_errata_info_list
                ]
                # ensure that the errata ids received by Erratum.list is sorted
                # as needed
                self.assertEqual(errata_ids, sorted_errata_ids)

    @tier3
    def test_positive_list_filter_by_org_label_and_sort_by_updated_date(self):
        """Filter errata by org label and sort by updated date

        :id: ce891bdf-cc2f-46e9-ab43-91527d40c3ed

        :Setup: Errata synced on satellite server.

        :Steps:

            1. erratum list --organization-label=<org_label> --order 'updated
               ASC'
            2. erratum list --organization-label=<org_label> --order 'updated
               DESC'

        :expectedresults: Errata is filtered by org label and sorted by updated
            date.
        """
        sort_data = [('updated', 'ASC'), ('updated', 'DESC')]
        for sort_field, sort_order in sort_data:
            sort_text = '{0} {1}'.format(sort_field, sort_order)
            sort_reversed = True if sort_order == 'DESC' else False
            with self.subTest(sort_text):
                erratum_list = Erratum.list({
                    'organization-label': self.org['label'],
                    'order': sort_text,
                    'per-page': ERRATUM_MAX_IDS_INFO
                })
                # note: the erratum_list, contain a list of restraint info
                # (id, errata-id, type, title) about each errata
                self.assertGreater(len(erratum_list), 0)
                # build a list of erratum id received from Erratum.list
                erratum_ids = [
                    errata['id']
                    for errata in erratum_list
                ]
                # build a list of errata-id field value in the same order as
                # received from Erratum.list
                errata_ids = [
                    errata['errata-id']
                    for errata in erratum_list
                ]
                # build a sorted more detailed erratum info list, that also
                # contain the sort field
                sorted_errata_info_list = self._get_sorted_erratum_ids_info(
                    erratum_ids,
                    sort_by=sort_field,
                    sort_reversed=sort_reversed
                )
                # build a list of sort field (issued/updated) values in the
                # same order as received from the detailed sorted erratum info
                # list
                sort_field_values = [
                    errata[sort_field]
                    for errata in sorted_errata_info_list
                ]
                # ensure that the sort field (issued/updated) values are sorted
                # as needed
                self.assertEqual(
                    sort_field_values,
                    sorted(sort_field_values, reverse=sort_reversed)
                )
                # build a list of errata-id field value in the same order as
                # received from the detailed sorted errata info list
                sorted_errata_ids = [
                    errata['errata-id']
                    for errata in sorted_errata_info_list
                ]
                # ensure that the errata ids received by Erratum.list is sorted
                # as needed
                self.assertEqual(errata_ids, sorted_errata_ids)

    @tier3
    def test_positive_list_filter_by_org_id_and_sort_by_issued_date(self):
        """Filter errata by org id and sort by issued date

        :id: 5d0f396c-f930-4fe7-8d1e-5039a4ed359a

        :Setup: Errata synced on satellite server.

        :Steps:

            1. erratum list --organization-id=<org_id> --order 'issued ASC'
            2. erratum list --organization-id=<org_id> --order 'issued DESC'

        :expectedresults: Errata is filtered by org id and sorted by issued
            date.
        """
        sort_data = [('issued', 'ASC'), ('issued', 'DESC')]
        for sort_field, sort_order in sort_data:
            sort_text = '{0} {1}'.format(sort_field, sort_order)
            sort_reversed = True if sort_order == 'DESC' else False
            with self.subTest(sort_text):
                erratum_list = Erratum.list({
                    'organization-id': self.org['id'],
                    'order': sort_text,
                    'per-page': ERRATUM_MAX_IDS_INFO
                })
                # note: the erratum_list, contain a list of restraint info
                # (id, errata-id, type, title) about each errata
                self.assertGreater(len(erratum_list), 0)
                # build a list of erratum id received from Erratum.list
                erratum_ids = [
                    errata['id']
                    for errata in erratum_list
                ]
                # build a list of errata-id field value in the same order as
                # received from Erratum.list
                errata_ids = [
                    errata['errata-id']
                    for errata in erratum_list
                ]
                # build a sorted more detailed erratum info list, that also
                # contain the sort field
                sorted_errata_info_list = self._get_sorted_erratum_ids_info(
                    erratum_ids,
                    sort_by=sort_field,
                    sort_reversed=sort_reversed
                )
                # build a list of sort field (issued/updated) values in the
                # same order as received from the detailed sorted erratum info
                # list
                sort_field_values = [
                    errata[sort_field]
                    for errata in sorted_errata_info_list
                ]
                # ensure that the sort field (issued/updated) values are sorted
                # as needed
                self.assertEqual(
                    sort_field_values,
                    sorted(sort_field_values, reverse=sort_reversed)
                )
                # build a list of errata-id field value in the same order as
                # received from the detailed sorted errata info list
                sorted_errata_ids = [
                    errata['errata-id']
                    for errata in sorted_errata_info_list
                ]
                # ensure that the errata ids received by Erratum.list is sorted
                # as needed
                self.assertEqual(errata_ids, sorted_errata_ids)

    @tier3
    def test_positive_list_filter_by_org_name_and_sort_by_issued_date(self):
        """Filter errata by org name and sort by issued date

        :id: 22f05ac0-fefa-48c4-861d-eeed41d9b235

        :Setup: Errata synced on satellite server.

        :Steps:

            1. erratum list --organization=<org_name> --order 'issued ASC'
            2. erratum list --organization=<org_name> --order 'issued DESC'

        :expectedresults: Errata is filtered by org name and sorted by issued
            date.
        """
        sort_data = [('issued', 'ASC'), ('issued', 'DESC')]
        for sort_field, sort_order in sort_data:
            sort_text = '{0} {1}'.format(sort_field, sort_order)
            sort_reversed = True if sort_order == 'DESC' else False
            with self.subTest(sort_text):
                erratum_list = Erratum.list({
                    'organization': self.org['name'],
                    'order': sort_text,
                    'per-page': ERRATUM_MAX_IDS_INFO
                })
                # note: the erratum_list, contain a list of restraint info
                # (id, errata-id, type, title) about each errata
                self.assertGreater(len(erratum_list), 0)
                # build a list of erratum id received from Erratum.list
                erratum_ids = [
                    errata['id']
                    for errata in erratum_list
                ]
                # build a list of errata-id field value in the same order as
                # received from Erratum.list
                errata_ids = [
                    errata['errata-id']
                    for errata in erratum_list
                ]
                # build a sorted more detailed erratum info list, that also
                # contain the sort field
                sorted_errata_info_list = self._get_sorted_erratum_ids_info(
                    erratum_ids,
                    sort_by=sort_field,
                    sort_reversed=sort_reversed
                )
                # build a list of sort field (issued/updated) values in the
                # same order as received from the detailed sorted erratum info
                # list
                sort_field_values = [
                    errata[sort_field]
                    for errata in sorted_errata_info_list
                ]
                # ensure that the sort field (issued/updated) values are sorted
                # as needed
                self.assertEqual(
                    sort_field_values,
                    sorted(sort_field_values, reverse=sort_reversed)
                )
                # build a list of errata-id field value in the same order as
                # received from the detailed sorted errata info list
                sorted_errata_ids = [
                    errata['errata-id']
                    for errata in sorted_errata_info_list
                ]
                # ensure that the errata ids received by Erratum.list is sorted
                # as needed
                self.assertEqual(errata_ids, sorted_errata_ids)

    @tier3
    def test_positive_list_filter_by_org_label_and_sort_by_issued_date(self):
        """Filter errata by org label and sort by issued date

        :id: 31acb734-8705-4d3c-b05e-edfd63d1ca3b

        :Setup: Errata synced on satellite server.

        :Steps:

            1. erratum list --organization-label=<org_label> --order 'issued
               ASC'
            2. erratum list --organization-label=<org_label> --order 'issued
               DESC'

        :expectedresults: Errata is filtered by org label and sorted by issued
            date.
        """
        sort_data = [('issued', 'ASC'), ('issued', 'DESC')]
        for sort_field, sort_order in sort_data:
            sort_text = '{0} {1}'.format(sort_field, sort_order)
            sort_reversed = True if sort_order == 'DESC' else False
            with self.subTest(sort_text):
                erratum_list = Erratum.list({
                    'organization-label': self.org['label'],
                    'order': sort_text,
                    'per-page': ERRATUM_MAX_IDS_INFO
                })
                # note: the erratum_list, contain a list of restraint info
                # (id, errata-id, type, title) about each errata
                self.assertGreater(len(erratum_list), 0)
                # build a list of erratum id received from Erratum.list
                erratum_ids = [
                    errata['id']
                    for errata in erratum_list
                ]
                # build a list of errata-id field in the same order as received
                # from Erratum.list
                errata_ids = [
                    errata['errata-id']
                    for errata in erratum_list
                ]
                # build a sorted more detailed erratum info list, that also
                # contain the sort field
                sorted_errata_info_list = self._get_sorted_erratum_ids_info(
                    erratum_ids,
                    sort_by=sort_field,
                    sort_reversed=sort_reversed
                )
                # build a list of sort field (issued/updated) values in the
                # same order as received from the detailed sorted erratum info
                # list
                sort_field_values = [
                    errata[sort_field]
                    for errata in sorted_errata_info_list
                ]
                # ensure that the sort field (issued/updated) values are sorted
                # as needed
                self.assertEqual(
                    sort_field_values,
                    sorted(sort_field_values, reverse=sort_reversed)
                )
                # build a list of errata-id field value in the same order as
                # received from the detailed sorted errata info list
                sorted_errata_ids = [
                    errata['errata-id']
                    for errata in sorted_errata_info_list
                ]
                # ensure that the errata ids received by Erratum.list is sorted
                # as needed
                self.assertEqual(errata_ids, sorted_errata_ids)

    @tier3
    def test_positive_list_filter_by_product_id(self):
        """Filter errata by product id

        :id: 7d06950a-c058-48b3-a384-c3565cbd643f

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product-id=<productid>

        :expectedresults: Errata is filtered by product id.
        """
        org_product_erratum_list = Erratum.list({
            'product-id': self.org_product['id'],
            'per-page': 1000
        })
        org_product_errata_ids = {
            errata['errata-id']
            for errata in org_product_erratum_list
            }
        errata_org_product_erratum_list = Erratum.list({
            'product-id': self.errata_org_product['id'],
            'per-page': 1000
        })
        errata_org_product_errata_ids = {
            errata['errata-id']
            for errata in errata_org_product_erratum_list
        }
        self.assertEqual(
            len(org_product_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(errata_org_product_errata_ids),
            self.errata_org_product_erratum_count
        )
        self.assertIn(self.org_product_errata_id, org_product_errata_ids)
        self.assertIn(
            self.errata_org_product_errata_id, errata_org_product_errata_ids)
        self.assertEqual(
            org_product_errata_ids.intersection(errata_org_product_errata_ids),
            set([])
        )

    @tier3
    def test_positive_list_filter_by_product_id_and_org_id(self):
        """Filter errata by product id and Org id

        :id: caf14671-d8b2-4a23-8c7e-6667bb78d4b7

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product-id=<product_id>
            --organization-id=<org_id>

        :expectedresults: Errata is filtered by product id and Org id.
        """
        product_erratum_list = Erratum.list({
            'organization-id': self.org['id'],
            'product-id': self.org_product['id'],
            'per-page': 1000
        })
        product_errata_ids = {
            errata['errata-id']
            for errata in product_erratum_list
        }
        product_small_erratum_list = Erratum.list({
            'organization-id': self.org_multi['id'],
            'product-id': self.org_multi_product_small['id'],
            'per-page': 1000
        })
        product_small_errata_ids = {
            errata['errata-id']
            for errata in product_small_erratum_list
        }
        product_big_erratum_list = Erratum.list({
            'organization-id': self.org_multi['id'],
            'product-id': self.org_multi_product_big['id'],
            'per-page': 1000
        })
        product_big_errata_ids = {
            errata['errata-id']
            for errata in product_big_erratum_list
        }
        self.assertEqual(
            len(product_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(product_small_errata_ids),
            self.org_multi_product_small_erratum_count
        )
        self.assertEqual(
            len(product_big_errata_ids),
            self.org_multi_product_big_erratum_count
        )
        self.assertIn(self.org_product_errata_id, product_errata_ids)
        self.assertIn(
            self.org_multi_product_small_errata_id, product_small_errata_ids)
        self.assertIn(
            self.org_multi_product_big_errata_id, product_big_errata_ids)
        self.assertEqual(
            product_errata_ids.intersection(
                product_small_errata_ids),
            set([])
        )
        self.assertEqual(
            product_errata_ids.intersection(
                product_big_errata_ids),
            set([])
        )
        self.assertEqual(
            product_small_errata_ids.intersection(
                product_big_errata_ids),
            set([])
        )

    @tier3
    def test_positive_list_filter_by_product_id_and_org_name(self):
        """Filter errata by product id and Org name

        :id: 574a6f7e-a89e-482e-bf15-39cfd7730630

        :Setup: errata synced on satellite server.

        :Steps: erratum list --product-id=<product_id>
            --organization=<org_name>

        :expectedresults: Errata is filtered by product id and Org name.
        """
        product_erratum_list = Erratum.list({
            'organization': self.org['name'],
            'product-id': self.org_product['id'],
            'per-page': 1000
        })
        product_errata_ids = {
            errata['errata-id']
            for errata in product_erratum_list
        }
        product_small_erratum_list = Erratum.list({
            'organization': self.org_multi['name'],
            'product-id': self.org_multi_product_small['id'],
            'per-page': 1000
        })
        product_small_errata_ids = {
            errata['errata-id']
            for errata in product_small_erratum_list
        }
        product_big_erratum_list = Erratum.list({
            'organization': self.org_multi['name'],
            'product-id': self.org_multi_product_big['id'],
            'per-page': 1000
        })
        product_big_errata_ids = {
            errata['errata-id']
            for errata in product_big_erratum_list
        }
        self.assertEqual(
            len(product_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(product_small_errata_ids),
            self.org_multi_product_small_erratum_count
        )
        self.assertEqual(
            len(product_big_errata_ids),
            self.org_multi_product_big_erratum_count
        )
        self.assertIn(self.org_product_errata_id, product_errata_ids)
        self.assertIn(
            self.org_multi_product_small_errata_id, product_small_errata_ids)
        self.assertIn(
            self.org_multi_product_big_errata_id, product_big_errata_ids)
        self.assertEqual(
            product_errata_ids.intersection(product_small_errata_ids),
            set([])
        )
        self.assertEqual(
            product_errata_ids.intersection(
                product_big_errata_ids),
            set([])
        )
        self.assertEqual(
            product_small_errata_ids.intersection(
                product_big_errata_ids),
            set([])
        )

    @tier3
    def test_positive_list_filter_by_product_id_and_org_label(self):
        """Filter errata by product id and Org label

        :id: 7b92ee32-2386-452c-9443-65b0c233a564

        :Setup: errata synced on satellite server.

        :Steps: erratum list --product-id=<product_id>
            --organization-label=<org_label>

        :expectedresults: Errata is filtered by product id and Org label
        """
        product_erratum_list = Erratum.list({
            'organization-label': self.org['label'],
            'product-id': self.org_product['id'],
            'per-page': 1000
        })
        product_errata_ids = {
            errata['errata-id']
            for errata in product_erratum_list
        }
        product_small_erratum_list = Erratum.list({
            'organization-label': self.org_multi['label'],
            'product-id': self.org_multi_product_small['id'],
            'per-page': 1000
        })
        product_small_errata_ids = {
            errata['errata-id']
            for errata in product_small_erratum_list
        }
        product_big_erratum_list = Erratum.list({
            'organization-label': self.org_multi['label'],
            'product-id': self.org_multi_product_big['id'],
            'per-page': 1000
        })
        product_big_errata_ids = {
            errata['errata-id']
            for errata in product_big_erratum_list
        }
        self.assertEqual(
            len(product_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(product_small_errata_ids),
            self.org_multi_product_small_erratum_count
        )
        self.assertEqual(
            len(product_big_errata_ids),
            self.org_multi_product_big_erratum_count
        )
        self.assertIn(self.org_product_errata_id, product_errata_ids)
        self.assertIn(
            self.org_multi_product_small_errata_id, product_small_errata_ids)
        self.assertIn(
            self.org_multi_product_big_errata_id, product_big_errata_ids)
        self.assertEqual(
            product_errata_ids.intersection(product_small_errata_ids),
            set([])
        )
        self.assertEqual(
            product_errata_ids.intersection(product_big_errata_ids),
            set([])
        )
        self.assertEqual(
            product_small_errata_ids.intersection(product_big_errata_ids),
            set([])
        )

    @skip_if_bug_open('bugzilla', 1400235)
    @tier3
    def test_negative_list_filter_by_product_name(self):
        """Attempt to Filter errata by product name

        :id: c7a5988b-668f-4c48-bc1e-97cb968a2563

        :BZ: 1400235

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product=<product_name>

        :expectedresults: Error must be returned.

        :CaseImportance: Low

        :CaseLevel: System
        """
        with self.assertRaises(CLIReturnCodeError):
            Erratum.list({
                'product': self.org_product['name'],
                'per-page': 1000
            })

    @tier3
    def test_positive_list_filter_by_product_name_and_org_id(self):
        """Filter errata by product name and Org id

        :id: 53f7afa2-285d-4d40-9fdd-5013b3f02462

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product=<product_name>
            --organization-id=<org_id>

        :expectedresults: Errata is filtered by product name and Org id.
        """
        product_erratum_list = Erratum.list({
            'organization-id': self.org['id'],
            'product': self.org_product['name'],
            'per-page': 1000
        })
        product_errata_ids = {
            errata['errata-id']
            for errata in product_erratum_list
        }
        product_small_erratum_list = Erratum.list({
            'organization-id': self.org_multi['id'],
            'product': self.org_multi_product_small['name'],
            'per-page': 1000
        })
        product_small_errata_ids = {
            errata['errata-id']
            for errata in product_small_erratum_list
        }
        product_big_erratum_list = Erratum.list({
            'organization-id': self.org_multi['id'],
            'product': self.org_multi_product_big['name'],
            'per-page': 1000
        })
        product_big_errata_ids = {
            errata['errata-id']
            for errata in product_big_erratum_list
        }
        self.assertEqual(
            len(product_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(product_small_errata_ids),
            self.org_multi_product_small_erratum_count
        )
        self.assertEqual(
            len(product_big_errata_ids),
            self.org_multi_product_big_erratum_count
        )
        self.assertIn(self.org_product_errata_id, product_errata_ids)
        self.assertIn(
            self.org_multi_product_small_errata_id, product_small_errata_ids)
        self.assertIn(
            self.org_multi_product_big_errata_id, product_big_errata_ids)
        self.assertEqual(
            product_errata_ids.intersection(product_small_errata_ids),
            set([])
        )
        self.assertEqual(
            product_errata_ids.intersection(product_big_errata_ids),
            set([])
        )
        self.assertEqual(
            product_small_errata_ids.intersection(product_big_errata_ids),
            set([])
        )

    @tier3
    def test_positive_list_filter_by_product_name_and_org_name(self):
        """Filter errata by product name and Org name

        :id: 8102d688-30d7-4ee5-a1aa-7e041d842a6f

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product=<product_name> --organization=<org_name>

        :expectedresults: Errata is filtered by product name and Org name.
        """
        product_erratum_list = Erratum.list({
            'organization': self.org['name'],
            'product': self.org_product['name'],
            'per-page': 1000
        })
        product_errata_ids = {
            errata['errata-id']
            for errata in product_erratum_list
        }
        product_small_erratum_list = Erratum.list({
            'organization': self.org_multi['name'],
            'product': self.org_multi_product_small['name'],
            'per-page': 1000
        })
        product_small_errata_ids = {
            errata['errata-id']
            for errata in product_small_erratum_list
        }
        product_big_erratum_list = Erratum.list({
            'organization': self.org_multi['name'],
            'product': self.org_multi_product_big['name'],
            'per-page': 1000
        })
        product_big_errata_ids = {
            errata['errata-id']
            for errata in product_big_erratum_list
        }
        self.assertEqual(
            len(product_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(product_small_errata_ids),
            self.org_multi_product_small_erratum_count
        )
        self.assertEqual(
            len(product_big_errata_ids),
            self.org_multi_product_big_erratum_count
        )
        self.assertIn(self.org_product_errata_id, product_errata_ids)
        self.assertIn(
            self.org_multi_product_small_errata_id, product_small_errata_ids)
        self.assertIn(
            self.org_multi_product_big_errata_id, product_big_errata_ids)
        self.assertEqual(
            product_errata_ids.intersection(product_small_errata_ids),
            set([])
        )
        self.assertEqual(
            product_errata_ids.intersection(product_big_errata_ids),
            set([])
        )
        self.assertEqual(
            product_small_errata_ids.intersection(product_big_errata_ids),
            set([])
        )

    @tier3
    def test_positive_list_filter_by_product_name_and_org_label(self):
        """Filter errata by product name and Org label

        :id: 64abb151-3f9d-4cad-b4a1-6bf0d73d8a3c

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product=<product_name>
            --organization-label=<org_label>

        :expectedresults: Errata is filtered by product name and Org label.
        """
        product_erratum_list = Erratum.list({
            'organization-label': self.org['label'],
            'product': self.org_product['name'],
            'per-page': 1000
        })
        product_errata_ids = {
            errata['errata-id']
            for errata in product_erratum_list
        }
        product_small_erratum_list = Erratum.list({
            'organization-label': self.org_multi['label'],
            'product': self.org_multi_product_small['name'],
            'per-page': 1000
        })
        product_small_errata_ids = {
            errata['errata-id']
            for errata in product_small_erratum_list
        }
        product_big_erratum_list = Erratum.list({
            'organization-label': self.org_multi['label'],
            'product': self.org_multi_product_big['name'],
            'per-page': 1000
        })
        product_big_errata_ids = {
            errata['errata-id']
            for errata in product_big_erratum_list
        }
        self.assertEqual(
            len(product_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(product_small_errata_ids),
            self.org_multi_product_small_erratum_count
        )
        self.assertEqual(
            len(product_big_errata_ids),
            self.org_multi_product_big_erratum_count
        )
        self.assertIn(self.org_product_errata_id, product_errata_ids)
        self.assertIn(
            self.org_multi_product_small_errata_id, product_small_errata_ids)
        self.assertIn(
            self.org_multi_product_big_errata_id, product_big_errata_ids)
        self.assertEqual(
            product_errata_ids.intersection(product_small_errata_ids),
            set([])
        )
        self.assertEqual(
            product_errata_ids.intersection(product_big_errata_ids),
            set([])
        )
        self.assertEqual(
            product_small_errata_ids.intersection(product_big_errata_ids),
            set([])
        )

    @tier3
    def test_positive_list_filter_by_org_id(self):
        """Filter errata by Org id

        :id: eeb2b409-89dc-4576-9f89-520cf7152a5a

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --organization-id=<orgid>

        :expectedresults: Errata is filtered by Org id.
        """
        org_erratum_list = Erratum.list({
            'organization-id': self.org['id'],
            'per-page': 1000
        })
        org_errata_ids = {
            errata['errata-id']
            for errata in org_erratum_list
        }
        errata_org_erratum_list = Erratum.list({
            'organization-id': self.errata_org['id'],
            'per-page': 1000
        })
        errata_org_errata_ids = {
            errata['errata-id']
            for errata in errata_org_erratum_list
        }
        self.assertEqual(len(org_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(errata_org_errata_ids), self.errata_org_product_erratum_count)
        self.assertIn(self.org_product_errata_id, org_errata_ids)
        self.assertIn(self.errata_org_product_errata_id, errata_org_errata_ids)
        self.assertEqual(
            org_errata_ids.intersection(errata_org_errata_ids),
            set([])
        )

    @tier3
    def test_positive_list_filter_by_org_name(self):
        """Filter errata by Org name

        :id: f2b20bb5-0938-4c7b-af95-d2b3e2b36581

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --organization=<org name>

        :expectedresults: Errata is filtered by Org name.
        """
        org_erratum_list = Erratum.list({
            'organization': self.org['name'],
            'per-page': 1000
        })
        org_errata_ids = {
            errata['errata-id']
            for errata in org_erratum_list
        }
        errata_org_erratum_list = Erratum.list({
            'organization': self.errata_org['name'],
            'per-page': 1000
        })
        errata_org_errata_ids = {
            errata['errata-id']
            for errata in errata_org_erratum_list
        }
        self.assertEqual(len(org_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(errata_org_errata_ids), self.errata_org_product_erratum_count)
        self.assertIn(self.org_product_errata_id, org_errata_ids)
        self.assertIn(self.errata_org_product_errata_id, errata_org_errata_ids)
        self.assertEqual(
            org_errata_ids.intersection(errata_org_errata_ids),
            set([])
        )

    @tier3
    def test_positive_list_filter_by_org_label(self):
        """Filter errata by Org label

        :id: 398123f5-d3ad-4a16-ac5d-e157d6d67595

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --organization-label=<org_label>

        :expectedresults: Errata is filtered by Org label.
        """
        org_erratum_list = Erratum.list({
            'organization-label': self.org['label'],
            'per-page': 1000
        })
        org_errata_ids = {
            errata['errata-id']
            for errata in org_erratum_list
        }
        errata_org_erratum_list = Erratum.list({
            'organization-label': self.errata_org['label'],
            'per-page': 1000
        })
        errata_org_errata_ids = {
            errata['errata-id']
            for errata in errata_org_erratum_list
        }
        self.assertEqual(len(org_errata_ids), self.org_product_erratum_count)
        self.assertEqual(
            len(errata_org_errata_ids), self.errata_org_product_erratum_count)
        self.assertIn(self.org_product_errata_id, org_errata_ids)
        self.assertIn(self.errata_org_product_errata_id, errata_org_errata_ids)
        self.assertEqual(
            org_errata_ids.intersection(errata_org_errata_ids),
            set([])
        )

    @run_in_one_thread
    @run_only_on('sat')
    @tier3
    def test_positive_list_filter_by_cve(self):
        """Filter errata by CVE

        :id: 7791137c-95a7-4518-a56b-766a5680c5fb

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --cve <cve_id>

        :expectedresults: Errata is filtered by CVE.

        """
        org = make_org()
        with manifests.clone() as manifest:
            ssh.upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': org['id'],
        })
        RepositorySet.enable({
            'name': REPOSET['rhva6'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        })
        Repository.synchronize({
            'name': REPOS['rhva6']['name'],
            'organization-id': org['id'],
            'product': PRDS['rhel']
        })
        repository_info = Repository.info({
                u'name': REPOS['rhva6']['name'],
                u'organization-id': org['id'],
                u'product': PRDS['rhel'],
        })
        erratum = Erratum.list({'repository-id': repository_info['id']})
        errata_ids = [errata['errata-id'] for errata in erratum]
        self.assertIn(REAL_4_ERRATA_ID, errata_ids)
        for errata_cve in REAL_4_ERRATA_CVES:
            with self.subTest(errata_cve):
                cve_erratum = Erratum.list({'cve': errata_cve})
                cve_errata_ids = [
                    cve_errata['errata-id']
                    for cve_errata in cve_erratum
                ]
                self.assertIn(REAL_4_ERRATA_ID, cve_errata_ids)

    @tier3
    @upgrade
    def test_positive_user_permission(self):
        """Show errata only if the User has permissions to view them

        :id: f350c13b-8cf9-4aa5-8c3a-1c48397ea514

        :Setup:

            1. Create two products with one repo each. Sync them.
            2. Make sure that they both have errata.
            3. Create a user with view access on one product and not on the
               other.

        :Steps: erratum list --organization-id=<orgid>

        :expectedresults: Check that the new user is able to see errata for one
            product only.

        :BZ: 1403947
        """
        user_password = gen_string('alphanumeric')
        user_name = gen_string('alphanumeric')
        org = self.org_multi
        product = self.org_multi_product_small
        # get the available permissions
        permissions = Filter.available_permissions()
        user_required_permissions_names = ['view_products']
        # get the user required permissions ids
        user_required_permissions_ids = [
            permission['id']
            for permission in permissions
            if permission['name'] in user_required_permissions_names
        ]
        self.assertGreater(len(user_required_permissions_ids), 0)
        # create a role
        role = make_role({'organization-ids': org['id']})
        # create a filter with the required permissions for role with product
        # one only
        make_filter({
            'permission-ids': user_required_permissions_ids,
            'role-id': role['id'],
            'search': 'name = {0}'.format(product['name'])
        })
        # create a new user and assign him the created role permissions
        user = make_user({
            'admin': False,
            'login': user_name,
            'password': user_password,
            'organization-ids': [org['id']],
            'default-organization-id': org['id'],
        })
        User.add_role({'id': user['id'], 'role-id': role['id']})
        # make sure the user is not admin and has only the permissions assigned
        user = User.info({'id': user['id']})
        self.assertEqual(user['admin'], 'no')
        self.assertEqual(set(user['roles']), {role['name']})
        # try to get organization info
        # get the info as admin user first
        org_info = Org.info({'id': org['id']})
        self.assertEqual(org['id'], org_info['id'])
        self.assertEqual(org['name'], org_info['name'])
        # get the organization info as the created user
        with self.assertRaises(CLIReturnCodeError) as context:
            Org.with_user(user_name, user_password).info({'id': org['id']})
        self.assertIn(
            'Missing one of the required permissions: view_organizations',
            context.exception.stderr
        )
        # try to get the erratum products list by organization id only
        if not bz_bug_is_open('1403947'):
            # ensure that all products erratum are accessible by admin user
            admin_org_erratum_info_list = Erratum.list({
                'organization-id': org['id']})
            admin_org_errata_ids = [
                errata['errata-id']
                for errata in admin_org_erratum_info_list
            ]
            self.assertIn(
                self.org_multi_product_small_errata_id, admin_org_errata_ids)
            self.assertIn(
                self.org_multi_product_big_errata_id, admin_org_errata_ids)
            org_erratum_count = (self.org_multi_product_small_erratum_count +
                                 self.org_multi_product_big_erratum_count)
            self.assertEqual(len(admin_org_errata_ids), org_erratum_count)
        # ensure that the created user see only the erratum product that was
        # assigned in permissions
        user_org_erratum_info_list = Erratum.with_user(
            user_name, user_password).list({'organization-id': org['id']})
        user_org_errata_ids = [
            errata['errata-id']
            for errata in user_org_erratum_info_list
        ]
        self.assertEqual(
            len(user_org_errata_ids),
            self.org_multi_product_small_erratum_count
        )
        self.assertIn(
            self.org_multi_product_small_errata_id, user_org_errata_ids)
        self.assertNotIn(
            self.org_multi_product_big_errata_id, user_org_errata_ids)

    @stubbed()
    @upgrade
    def test_positive_list_affected_chosts(self):
        """View a list of affected content hosts for an erratum

        :id: 3b592253-52c0-4165-9a48-ba55287e9ee9

        :Setup: Errata synced on satellite server.

        :Steps: content-host list --erratum-id=<erratum_id>
            --organization-id=<org_id>

        :expectedresults: List of affected content hosts for an erratum is
            displayed.

        :CaseAutomation: notautomated

        """

    @stubbed()
    def test_positive_list_affected_chosts_by_erratum_restrict_flag(self):
        """View a list of affected content hosts for an erratum filtered
        with restrict flags

        :id: 594acd48-892c-499e-b0cb-6506cea7cd64

        :Setup: Errata synced on satellite server.

        :Steps:

            1. content-host list --erratum-id=<erratum_id>
               --organization-id=<org_id> --erratum-restrict-available=1
            2. content-host list --erratum-id=<erratum_id>
               --organization-id=<org_id> --erratum-restrict-unavailable=1
            3. content-host list --erratum-id=<erratum_id>
               --organization-id=<org_id> --erratum-restrict-available=0
            4. content-host list --erratum-id=<erratum_id>
               --organization-id=<org_id> --erratum-restrict-unavailable=0

        :expectedresults: List of affected content hosts for an erratum is
            displayed filtered with corresponding restrict flags.

        :CaseAutomation: notautomated

        """

    @stubbed()
    def test_positive_view_available_count_in_affected_chosts(self):
        """Available errata count displayed while viewing a list of
        Content hosts

        :id: 1d174432-bb51-4192-990d-3c62087b96df

        :Setup:

            1. Errata synced on satellite server.
            2. Some content hosts present.

        :Steps: hammer content-host list --organization-id=<orgid>

        :expectedresults: The available errata count is retrieved.

        :CaseAutomation: notautomated

        """
