"""API Tests for the errata management feature

@Requirement: Errata

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

# For ease of use hc refers to host-collection throughout this document

from nailgun import entities
from robottelo.cli.factory import (
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.constants import (
    DISTRO_RHEL7,
    FAKE_9_YUM_ERRATUM,
    FAKE_9_YUM_OUTDATED_PACKAGES,
    FAKE_9_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    bz_bug_is_open,
    skip_if_not_set,
    stubbed,
    tier3,
    upgrade
)
from robottelo.test import APITestCase
from robottelo.vm import VirtualMachine
from time import sleep


class ErrataTestCase(APITestCase):
    """API Tests for the errata management feature"""

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key"""
        super(ErrataTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.env = entities.LifecycleEnvironment(
            organization=cls.org).create()
        cls.content_view = entities.ContentView(
            organization=cls.org).create()
        cls.activation_key = entities.ActivationKey(
            environment=cls.env,
            organization=cls.org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': cls.org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        }, force_manifest_upload=True)
        cls.custom_entities = setup_org_for_a_custom_repo({
            'url': FAKE_9_YUM_REPO,
            'organization-id': cls.org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })

    def _install_package(self, clients, host_ids, package_name):
        """Workaround BZ1374669 and install package via CLI while the bug is
        open.
        """
        if bz_bug_is_open(1374669):
            for client in clients:
                result = client.run('yum install -y {}'.format(package_name))
                self.assertEqual(result.return_code, 0)
                result = client.run('rpm -q {}'.format(package_name))
                self.assertEqual(result.return_code, 0)
            return
        entities.Host().install_content(data={
            'organization_id': self.org.id,
            'included': {'ids': host_ids},
            'content_type': 'package',
            'content': [package_name],
        })
        self._validate_package_installed(clients, package_name)

    def _validate_package_installed(self, hosts, package_name,
                                    expected_installed=True, timeout=120):
        """Check whether package was installed on the list of hosts."""
        for host in hosts:
            for _ in range(timeout / 15):
                result = host.run('rpm -q {0}'.format(package_name))
                if (result.return_code == 0 and expected_installed or
                        result.return_code != 0 and not expected_installed):
                    break
                sleep(15)
            else:
                self.fail(
                    u'Package {0} was not {1} host {2}'.format(
                        package_name,
                        'installed on' if expected_installed else
                        'removed from',
                        host.hostname,
                    )
                )

    @stubbed()
    @tier3
    @upgrade
    def test_positive_install(self):
        """Install errata in a host-collection

        @id: 6f0242df-6511-4c0f-95fc-3fa32c63a064

        @Setup: Errata synced on satellite server.

        @Steps:

        1. PUT /katello/api/hosts/bulk/update_content

        @expectedresults: errata is installed in the host-collection.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @tier3
    def test_positive_install_multiple_in_host(self):
        """For a host with multiple applicable errata install one and ensure
        the rest of errata is still available

        @id: 67b7e95b-9809-455a-a74e-f1815cc537fc

        @BZ: 1469800

        @expectedresults: errata installation task succeeded, available errata
            counter decreased by one; it's possible to schedule another errata
            installation

        @CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.org.label, self.activation_key.name)
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
            host = entities.Host().search(query={
                'search': 'name={0}'.format(client.hostname)})[0]
            for package in FAKE_9_YUM_OUTDATED_PACKAGES:
                self._install_package([client], [host.id], package)
            host = host.read()
            applicable_errata_count = host.content_facet_attributes[
                'errata_counts']['total']
            self.assertGreater(applicable_errata_count, 1)
            for errata in FAKE_9_YUM_ERRATUM[:2]:
                host.errata_apply(data={'errata_ids': [errata]})
                host = host.read()
                applicable_errata_count -= 1
                self.assertEqual(
                    host.content_facet_attributes['errata_counts']['total'],
                    applicable_errata_count
                )

    @stubbed()
    @tier3
    def test_positive_list(self):
        """View all errata specific to an Org

        @id: 1efceabf-9821-4804-bacf-2213ac0c7550

        @Setup: Errata synced on satellite server.

        @Steps: Create two Orgs each having a product synced and contains
        errata.

        @expectedresults: Check that the errata belonging to one Org is not
        showing in the other.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_list_updated(self):
        """View all errata in an Org sorted by Updated

        @id: 560d6584-70bd-4d1b-993a-cc7665a9e600

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @expectedresults: Errata is filtered by Org and sorted by Updated date.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_filter_by_cve(self):
        """Filter errata by CVE

        @id: a921d4c2-8d3d-4462-ba6c-fbd4b898a3f2

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @expectedresults: Errata is filtered by CVE.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_list_affected_hosts(self):
        """View a list of affected content hosts for an erratum

        @id: 27711bbd-b94f-4135-9b61-b004bd1cd365

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/hosts

        @expectedresults: List of affected content hosts for the given erratum
        is retrieved.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_filter_by_affected_hosts(self):
        """Filter errata list based on affected content hosts

        @id: 82b44455-98bf-49fb-9f31-e2c05b67e69e

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @expectedresults: Errata is filtered based on affected content hosts.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_sort_by_issued_date(self):
        """Filter errata by issued date

        @id: 6b4a783a-a7b4-4af4-b9e6-eb2928b7f7c1

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @expectedresults: Errata is sorted by issued date.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_filter_by_envs(self):
        """Filter applicable errata for a content host by current and
        Library environments

        @id: f41bfcc2-39ee-4ae1-a71f-d2c9288875be

        @Setup:

        1. Make sure multiple environments are present.
        2. One of Content host's previous environment has additional errata.

        @Steps:

        1. GET /katello/api/errata

        @expectedresults: The errata for the content host is filtered by
        current and Library environments.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_get_count_for_chost(self):
        """Available errata count when retrieving Content host

        @id: 2f35933f-8026-414e-8f75-7f4ec048faae

        @Setup:

        1. Errata synced on satellite server.
        2. Some Content hosts present.

        @Steps:

        1. GET /katello/api/hosts

        @expectedresults: The available errata count is retrieved.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_get_diff_for_cv_envs(self):
        """Generate a difference in errata between a set of environments
        for a content view

        @id: 96732506-4a89-408c-8d7e-f30c8d469769

        @Setup:

        1. Errata synced on satellite server.
        2. Multiple environments present.

        @Steps:

        1. GET /katello/api/compare

        @expectedresults: Difference in errata between a set of environments
        for a content view is retrieved.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_incremental_update_apply_to_envs_cvs(self):
        """Select multiple errata and apply them to multiple content
        views in multiple environments

        @id: 5d8f6aee-baac-4217-ba34-13adccdf1ca8

        @Setup:

        1. Errata synced on satellite server.
        2. Multiple environments/content views present.

        @Steps:

        1. POST /katello/api/hosts/bulk/available_incremental_updates

        @expectedresults: Selected errata are applied to multiple content views
        in multiple environments.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_incremental_update_query_envs_cvs(self):
        """Query a subset of environments or content views to push new
        errata

        @id: f6ec8066-36cc-42a8-9a1a-156721e733c3

        @Setup:

        1. Errata synced on satellite server.
        2. Multiple environments/content views present.

        @Steps:

        1. POST /katello/api/content_view_versions/incremental_update

        @expectedresults: Subset of environments/content views retrieved.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_incremental_update_apply_packages_to_envs_cvs(self):
        """Select multiple packages and apply them to multiple content
        views in multiple environments

        @id: 61549360-ce99-42a3-8d6b-2cd713f8b556

        @Setup:

        1. Errata synced on satellite server.
        2. Multiple environments/content views present.

        @Steps:

        1. POST /katello/api/content_view_versions/incremental_update

        @expectedresults: Packages are applied to multiple environments/content
        views.

        @caseautomation: notautomated

        @CaseLevel: System
        """
