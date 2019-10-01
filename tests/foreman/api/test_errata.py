"""API Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: ErrataManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

# For ease of use hc refers to host-collection throughout this document
import pytest

from nailgun import entities
from robottelo.cli.factory import (
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.config import settings
from robottelo.constants import (
    CUSTOM_SWID_TAG_REPO,
    DEFAULT_ARCHITECTURE,
    DEFAULT_RELEASE_VERSION,
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    DISTRO_RHEL8,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_3_ERRATA_ID,
    FAKE_3_YUM_REPO,
    FAKE_9_YUM_ERRATUM,
    FAKE_9_YUM_OUTDATED_PACKAGES,
    FAKE_9_YUM_REPO,
    PRDS,
    REAL_0_ERRATA_ID,
    REAL_0_RH_PACKAGE,
    REAL_1_ERRATA_ID,
    REAL_2_ERRATA_ID,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_not_set,
    stubbed,
    tier3,
    upgrade
)
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.products import (
    YumRepository,
    RepositoryCollection,
)

from robottelo.test import APITestCase
from robottelo.api.utils import enable_rhrepo_and_fetchid, promote
from robottelo.vm import VirtualMachine
from time import sleep

CUSTOM_REPO_URL = FAKE_9_YUM_REPO
CUSTOM_REPO_ERRATA_ID = FAKE_2_ERRATA_ID


@run_in_one_thread
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

    def _install_package(self, clients, host_ids, package_name, via_ssh=True,
                         rpm_package_name=None):
        """Install package via SSH CLI if via_ssh is True, otherwise
        install via http api: PUT /api/v2/hosts/bulk/install_content
        """
        if via_ssh:
            for client in clients:
                result = client.run('yum install -y {}'.format(package_name))
                self.assertEqual(result.return_code, 0)
                result = client.run('rpm -q {}'.format(package_name))
                self.assertEqual(result.return_code, 0)
        else:
            entities.Host().install_content(data={
                'organization_id': self.org.id,
                'included': {'ids': host_ids},
                'content_type': 'package',
                'content': [package_name],
            })
            self._validate_package_installed(clients, rpm_package_name)

    def _validate_package_installed(self, hosts, package_name,
                                    expected_installed=True, timeout=120):
        """Check whether package was installed on the list of hosts."""
        for host in hosts:
            for _ in range(timeout // 15):
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

    def _validate_errata_counts(self, host, errata_type, expected_value,
                                timeout=120):
        """Check whether host contains expected errata counts."""
        for _ in range(timeout // 5):
            host = host.read()
            if (host.content_facet_attributes[
                    'errata_counts'][errata_type] == expected_value):
                break
            sleep(5)
        else:
            self.fail(
                u'Host {0} contains {1} {2} errata, but expected to contain '
                '{3} of them'.format(
                    host.name,
                    host.content_facet_attributes[
                        'errata_counts'][errata_type],
                    errata_type,
                    expected_value,
                )
            )

    def _fetch_available_errata(self, host, expected_amount, timeout=120):
        """Fetch available errata for host."""
        errata = host.errata()
        for _ in range(timeout // 5):
            if len(errata['results']) == expected_amount:
                return errata['results']
            sleep(5)
            errata = host.errata()
        else:
            self.fail(
                u'Host {0} contains {1} available errata, but expected to '
                'contain {2} of them'.format(
                    host.name,
                    len(errata['results']),
                    expected_amount,
                )
            )

    @upgrade
    @tier3
    def test_positive_bulk_install_package(self):
        """Bulk install package to a collection of hosts

        :id: c5167851-b456-457a-92c3-59f8de5b27ee

        :Steps: PUT /api/v2/hosts/bulk/install_content

        :expectedresults: package is installed in the hosts.

        :BZ: 1528275

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.org.label, self.activation_key.name)
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
            host_id = entities.Host().search(query={
                'search': 'name={0}'.format(client.hostname)})[0].id
            self._install_package(
                [client],
                [host_id],
                FAKE_1_CUSTOM_PACKAGE_NAME,
                via_ssh=False,
                rpm_package_name=FAKE_2_CUSTOM_PACKAGE
            )

    @upgrade
    @tier3
    def test_positive_install_in_hc(self):
        """Install errata in a host-collection

        :id: 6f0242df-6511-4c0f-95fc-3fa32c63a064

        :Setup: Errata synced on satellite server.

        :Steps: PUT /api/v2/hosts/bulk/update_content

        :expectedresults: errata is installed in the host-collection.

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client1, VirtualMachine(
                distro=DISTRO_RHEL7) as client2:
            clients = [client1, client2]
            for client in clients:
                client.install_katello_ca()
                client.register_contenthost(
                    self.org.label, self.activation_key.name)
                self.assertTrue(client.subscribed)
                client.enable_repo(REPOS['rhst7']['id'])
                client.install_katello_agent()
            host_ids = [
                entities.Host().search(query={
                    'search': 'name={0}'.format(client.hostname)})[0].id
                for client in clients
                ]
            self._install_package(clients, host_ids, FAKE_1_CUSTOM_PACKAGE)
            entities.Host().install_content(data={
                'organization_id': self.org.id,
                'included': {'ids': host_ids},
                'content_type': 'errata',
                'content': [CUSTOM_REPO_ERRATA_ID],
            })
            self._validate_package_installed(clients, FAKE_2_CUSTOM_PACKAGE)

    @tier3
    def test_positive_install_in_host(self):
        """Install errata in a host

        :id: 1e6fc159-b0d6-436f-b945-2a5731c46df5

        :Setup: Errata synced on satellite server.

        :Steps: PUT /api/v2/hosts/:id/errata/apply

        :expectedresults: errata is installed in the host.

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.org.label, self.activation_key.name)
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
            host_id = entities.Host().search(query={
                    'search': 'name={0}'.format(client.hostname)})[0].id
            self._install_package([client], [host_id], FAKE_1_CUSTOM_PACKAGE)
            entities.Host(id=host_id).errata_apply(data={
                'errata_ids': [CUSTOM_REPO_ERRATA_ID]})
            self._validate_package_installed([client], FAKE_2_CUSTOM_PACKAGE)

    @tier3
    def test_positive_install_multiple_in_host(self):
        """For a host with multiple applicable errata install one and ensure
        the rest of errata is still available

        :id: 67b7e95b-9809-455a-a74e-f1815cc537fc

        :customerscenario: true

        :BZ: 1469800

        :expectedresults: errata installation task succeeded, available errata
            counter decreased by one; it's possible to schedule another errata
            installation

        :CaseLevel: System
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

    @tier3
    def test_positive_list(self):
        """View all errata specific to repository

        :id: 1efceabf-9821-4804-bacf-2213ac0c7550

        :Setup: Errata synced on satellite server.

        :Steps: Create two repositories each synced and containing errata

        :expectedresults: Check that the errata belonging to one repo is not
            showing in the other.

        :CaseLevel: System
        """
        repo1 = entities.Repository(
            id=self.custom_entities['repository-id']).read()
        repo2 = entities.Repository(
            product=entities.Product().create(),
            url=FAKE_3_YUM_REPO,
        ).create()
        repo2.sync()
        repo1_errata_ids = [
            errata['errata_id']
            for errata
            in repo1.errata(data={'per_page': 1000})['results']
        ]
        repo2_errata_ids = [
            errata['errata_id']
            for errata
            in repo2.errata(data={'per_page': 1000})['results']
        ]
        self.assertEqual(len(repo1_errata_ids), 4)
        self.assertEqual(len(repo2_errata_ids), 79)
        self.assertIn(CUSTOM_REPO_ERRATA_ID, repo1_errata_ids)
        self.assertNotIn(CUSTOM_REPO_ERRATA_ID, repo2_errata_ids)
        self.assertIn(FAKE_3_ERRATA_ID, repo2_errata_ids)
        self.assertNotIn(FAKE_3_ERRATA_ID, repo1_errata_ids)

    @tier3
    def test_positive_list_updated(self):
        """View all errata in an Org sorted by Updated

        :id: 560d6584-70bd-4d1b-993a-cc7665a9e600

        :Setup: Errata synced on satellite server.

        :Steps: GET /katello/api/errata

        :expectedresults: Errata is filtered by Org and sorted by Updated date.

        :CaseLevel: System
        """
        repo = entities.Repository(name=REPOS['rhva6']['name']).search(
                query={'organization_id': self.org.id})
        if repo:
            repo = repo[0]
        else:
            repo_with_cves_id = enable_rhrepo_and_fetchid(
                basearch=DEFAULT_ARCHITECTURE,
                org_id=self.org.id,
                product=PRDS['rhel'],
                repo=REPOS['rhva6']['name'],
                reposet=REPOSET['rhva6'],
                releasever=DEFAULT_RELEASE_VERSION,
            )
            repo = entities.Repository(id=repo_with_cves_id)
        self.assertEqual(repo.sync()['result'], 'success')
        erratum_list = entities.Errata(repository=repo).search(query={
            'order': 'updated ASC',
            'per_page': 1000,
        })
        updated = [errata.updated for errata in erratum_list]
        self.assertEqual(updated, sorted(updated))

    @tier3
    def test_positive_filter_by_cve(self):
        """Filter errata by CVE

        :id: a921d4c2-8d3d-4462-ba6c-fbd4b898a3f2

        :Setup: Errata synced on satellite server.

        :Steps: GET /katello/api/errata

        :expectedresults: Errata is filtered by CVE.

        :CaseLevel: System
        """
        repo = entities.Repository(name=REPOS['rhva6']['name']).search(
            query={'organization_id': self.org.id})
        if repo:
            repo = repo[0]
        else:
            repo_with_cves_id = enable_rhrepo_and_fetchid(
                basearch=DEFAULT_ARCHITECTURE,
                org_id=self.org.id,
                product=PRDS['rhel'],
                repo=REPOS['rhva6']['name'],
                reposet=REPOSET['rhva6'],
                releasever=DEFAULT_RELEASE_VERSION,
            )
            repo = entities.Repository(id=repo_with_cves_id)
        self.assertEqual(repo.sync()['result'], 'success')
        erratum_list = entities.Errata(repository=repo).search(query={
            'order': 'cve DESC',
            'per_page': 1000,
        })
        # Most of Errata don't have any CVEs. Removing empty CVEs from results
        erratum_cves = [
            errata.cves for errata in erratum_list if errata.cves
        ]
        # Verifying each errata have its CVEs sorted in DESC order
        for errata_cves in erratum_cves:
            cve_ids = [cve['cve_id'] for cve in errata_cves]
            self.assertEqual(cve_ids, sorted(cve_ids, reverse=True))

    @tier3
    def test_positive_sort_by_issued_date(self):
        """Filter errata by issued date

        :id: 6b4a783a-a7b4-4af4-b9e6-eb2928b7f7c1

        :Setup: Errata synced on satellite server.

        :Steps: GET /katello/api/errata

        :expectedresults: Errata is sorted by issued date.

        :CaseLevel: System
        """
        repo = entities.Repository(name=REPOS['rhva6']['name']).search(
            query={'organization_id': self.org.id})
        if repo:
            repo = repo[0]
        else:
            repo_with_cves_id = enable_rhrepo_and_fetchid(
                basearch=DEFAULT_ARCHITECTURE,
                org_id=self.org.id,
                product=PRDS['rhel'],
                repo=REPOS['rhva6']['name'],
                reposet=REPOSET['rhva6'],
                releasever=DEFAULT_RELEASE_VERSION,
            )
            repo = entities.Repository(id=repo_with_cves_id)
        self.assertEqual(repo.sync()['result'], 'success')
        erratum_list = entities.Errata(repository=repo).search(query={
            'order': 'issued ASC',
            'per_page': 1000,
        })
        issued = [errata.issued for errata in erratum_list]
        self.assertEqual(issued, sorted(issued))

    @tier3
    @pytest.mark.skip(reason="BZ:1682940")
    def test_positive_filter_by_envs(self):
        """Filter applicable errata for a content host by current and
        Library environments

        :id: f41bfcc2-39ee-4ae1-a71f-d2c9288875be

        :Setup:

            1. Make sure multiple environments are present.
            2. One of Content host's previous environment has additional
               errata.

        :Steps: GET /katello/api/errata

        :expectedresults: The errata for the content host is filtered by
            current and Library environments.

        :CaseLevel: System

        :BZ: 1682940
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(
            organization=org).create()
        content_view = entities.ContentView(
            organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        new_cv = entities.ContentView(organization=org).create()
        new_repo = entities.Repository(
            product=entities.Product(organization=org).create(),
            url=CUSTOM_REPO_URL,
        ).create()
        self.assertEqual(new_repo.sync()['result'], 'success')
        new_cv = new_cv.read()
        new_cv.repository.append(new_repo)
        new_cv = new_cv.update(['repository'])
        new_cv.publish()
        library_env = entities.LifecycleEnvironment(
            name='Library',
            organization=org,
        ).search()[0]
        errata_library = entities.Errata(environment=library_env).search(query={'per_page': 1000})
        errata_env = entities.Errata(environment=env).search(query={'per_page': 1000})
        self.assertGreater(len(errata_library), len(errata_env))

    @tier3
    def test_positive_get_count_for_host(self):
        """Available errata count when retrieving Host

        :id: 2f35933f-8026-414e-8f75-7f4ec048faae

        :Setup:

            1. Errata synced on satellite server.
            2. Some Content hosts present.

        :Steps: GET /api/v2/hosts

        :expectedresults: The available errata count is retrieved.

        :CaseLevel: System
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(
            organization=org).create()
        content_view = entities.ContentView(
            organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst6'],
            'repository': REPOS['rhst6']['name'],
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        }, force_manifest_upload=True)
        setup_org_for_a_custom_repo({
            'url': CUSTOM_REPO_URL,
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        repo_id = enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhva6']['name'],
            reposet=REPOSET['rhva6'],
            releasever=DEFAULT_RELEASE_VERSION,
        )
        repo = entities.Repository(id=repo_id)
        self.assertEqual(repo.sync()['result'], 'success')
        content_view = content_view.read()
        content_view.repository.append(repo)
        content_view = content_view.update(['repository'])
        content_view.publish()
        versions = sorted(content_view.read().version, key=lambda ver: ver.id)
        cvv = versions[-1].read()
        promote(cvv, env.id)
        with VirtualMachine(distro=DISTRO_RHEL6) as client:
            client.install_katello_ca()
            client.register_contenthost(org.label, activation_key.name)
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst6']['id'])
            client.enable_repo(REPOS['rhva6']['id'])
            client.install_katello_agent()
            host = entities.Host().search(query={
                'search': 'name={0}'.format(client.hostname)})[0].read()
            for errata in ('security', 'bugfix', 'enhancement'):
                self._validate_errata_counts(host, errata, 0)
            client.run(
                'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            self._validate_errata_counts(host, 'security', 1)
            client.run('yum install -y {0}'.format(REAL_0_RH_PACKAGE))
            for errata in ('bugfix', 'enhancement'):
                self._validate_errata_counts(host, errata, 1)

    @upgrade
    @tier3
    def test_positive_get_applicable_for_host(self):
        """Get applicable errata ids for a host

        :id: 51d44d51-eb3f-4ee4-a1df-869629d427ac

        :Setup:
            1. Errata synced on satellite server.
            2. Some Content hosts present.

        :Steps: GET /api/v2/hosts/:id/errata

        :expectedresults: The available errata is retrieved.

        :CaseLevel: System
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(
            organization=org).create()
        content_view = entities.ContentView(
            organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst6'],
            'repository': REPOS['rhst6']['name'],
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        }, force_manifest_upload=True)
        setup_org_for_a_custom_repo({
            'url': CUSTOM_REPO_URL,
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        repo_id = enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhva6']['name'],
            reposet=REPOSET['rhva6'],
            releasever=DEFAULT_RELEASE_VERSION,
        )
        repo = entities.Repository(id=repo_id)
        self.assertEqual(repo.sync()['result'], 'success')
        content_view = content_view.read()
        content_view.repository.append(repo)
        content_view = content_view.update(['repository'])
        content_view.publish()
        versions = sorted(content_view.read().version, key=lambda ver: ver.id)
        cvv = versions[-1].read()
        promote(cvv, env.id)
        with VirtualMachine(distro=DISTRO_RHEL6) as client:
            client.install_katello_ca()
            client.register_contenthost(org.label, activation_key.name)
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst6']['id'])
            client.enable_repo(REPOS['rhva6']['id'])
            client.install_katello_agent()
            host = entities.Host().search(query={
                'search': 'name={0}'.format(client.hostname)})[0].read()
            erratum = self._fetch_available_errata(host, 0)
            self.assertEqual(len(erratum), 0)
            client.run(
                'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            erratum = self._fetch_available_errata(host, 1)
            self.assertEqual(len(erratum), 1)
            self.assertIn(
                CUSTOM_REPO_ERRATA_ID,
                [errata['errata_id'] for errata in erratum],
            )
            client.run('yum install -y {0}'.format(REAL_0_RH_PACKAGE))
            erratum = self._fetch_available_errata(host, 3)
            self.assertEqual(len(erratum), 3)
            self.assertTrue(
                {REAL_1_ERRATA_ID, REAL_2_ERRATA_ID}.issubset(
                    {errata['errata_id'] for errata in erratum})
            )

    @tier3
    def test_positive_get_diff_for_cv_envs(self):
        """Generate a difference in errata between a set of environments
        for a content view

        :id: 96732506-4a89-408c-8d7e-f30c8d469769

        :Setup:

            1. Errata synced on satellite server.
            2. Multiple environments present.

        :Steps: GET /katello/api/compare

        :expectedresults: Difference in errata between a set of environments
            for a content view is retrieved.

        :CaseLevel: System
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(
            organization=org).create()
        content_view = entities.ContentView(
            organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        }, force_use_cdn=True)
        setup_org_for_a_custom_repo({
            'url': CUSTOM_REPO_URL,
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        new_env = entities.LifecycleEnvironment(
            organization=org,
            prior=env,
        ).create()
        cvvs = content_view.read().version[-2:]
        promote(cvvs[-1], new_env.id)
        result = entities.Errata().compare(data={
            'content_view_version_ids': [cvv.id for cvv in cvvs],
            'per_page': 9999,
        })
        cvv2_only_errata = next(
            errata for errata in result['results']
            if errata['errata_id'] == CUSTOM_REPO_ERRATA_ID
        )
        self.assertEqual([cvvs[-1].id], cvv2_only_errata['comparison'])
        both_cvvs_errata = next(
            errata for errata in result['results']
            if errata['errata_id'] == REAL_0_ERRATA_ID
        )
        self.assertEqual(
            set(cvv.id for cvv in cvvs), set(both_cvvs_errata['comparison']))

    @stubbed()
    @tier3
    def test_positive_incremental_update_apply_to_envs_cvs(self):
        """Select multiple errata and apply them to multiple content
        views in multiple environments

        :id: 5d8f6aee-baac-4217-ba34-13adccdf1ca8

        :Setup:
            1. Errata synced on satellite server.
            2. Multiple environments/content views present.

        :Steps: POST /katello/api/hosts/bulk/available_incremental_updates

        :expectedresults: Selected errata are applied to multiple content views
            in multiple environments.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_incremental_update_query_envs_cvs(self):
        """Query a subset of environments or content views to push new
        errata

        :id: f6ec8066-36cc-42a8-9a1a-156721e733c3

        :Setup:
            1. Errata synced on satellite server.
            2. Multiple environments/content views present.

        :Steps: POST /katello/api/content_view_versions/incremental_update

        :expectedresults: Subset of environments/content views retrieved.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @upgrade
    @stubbed()
    @tier3
    def test_positive_incremental_update_apply_packages_to_envs_cvs(self):
        """Select multiple packages and apply them to multiple content
        views in multiple environments

        :id: 61549360-ce99-42a3-8d6b-2cd713f8b556

        :Setup:
            1. Errata synced on satellite server.
            2. Multiple environments/content views present.

        :Steps: POST /katello/api/content_view_versions/incremental_update

        :expectedresults: Packages are applied to multiple environments/content
            views.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """


@run_in_one_thread
class ErrataSwidTagsTestCase(APITestCase):
    """API Tests for the errata management feature with swid tags"""

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key"""
        super(ErrataSwidTagsTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.lce = entities.LifecycleEnvironment(organization=cls.org).create()
        cls.repos_collection = RepositoryCollection(
            distro=DISTRO_RHEL8,
            repositories=[
                YumRepository(url=CUSTOM_SWID_TAG_REPO),
            ]
        )
        cls.repos_collection.setup_content(
            cls.org.id,
            cls.lce.id,
            upload_manifest=True
        )

    def _run_remote_command_on_content_host(self, command, vm, return_result=False):
        result = vm.run(command)
        self.assertEquals(result.return_code, 0)
        if return_result:
            return result.stdout

    def _set_prerequisites_for_swid_repos(self, vm):
        self._run_remote_command_on_content_host(
            "wget --no-check-certificate {}".format(settings.swid_tools_repo),
            vm)
        self._run_remote_command_on_content_host("mv *swid*.repo /etc/yum.repos.d", vm)
        self._run_remote_command_on_content_host("yum install -y swid-tools", vm)
        self._run_remote_command_on_content_host("dnf install -y dnf-plugin-swidtags", vm)

    def _validate_swid_tags_installed(self, vm, module_name):
        result = self._run_remote_command_on_content_host(
            "swidq -i -n {} | grep 'Name'".format(module_name),
            vm,
            return_result=True)
        self.assertIn(module_name, result)

    @tier3
    @upgrade
    def test_errata_installation_with_swidtags(self):
        """Verify errata installation with swid_tags and swid tags get updated after
        module stream update.

        :id: 43a59b9a-eb9b-4174-8b8e-73d923b1e51e

        :steps:

            1. create product and repository having swid tags
            2. create content view and published it with repository
            3. create activation key and register content host
            4. create rhel8, swid repos on content host
            5. install swid-tools, dnf-plugin-swidtags packages on content host
            6. install older module stream and generate errata, swid tag
            7. assert errata count, swid tags are generated
            8. install errata vis updating module stream
            9. assert errata count and swid tag after module update

        :expectedresults: swid tags should get updated after errata installation via
            module stream update

        :CaseAutomation: Automated

        :CaseImportance: Critical

        :CaseLevel: System
        """
        with VirtualMachine(distro=self.repos_collection.distro) as vm:
            module_name = 'kangaroo'
            version = '20180704111719'
            # setup rhel8 and sat_tools_repos
            vm.create_custom_repos(**{
                repo_name: settings.rhel8_os[repo_name] for repo_name in ('baseos', 'appstream')
            })
            self.repos_collection.setup_virtual_machine(
                vm,
                install_katello_agent=False)

            # install older module stream
            add_remote_execution_ssh_key(vm.ip_addr)
            self._set_prerequisites_for_swid_repos(vm=vm)
            self._run_remote_command_on_content_host(
                'dnf -y module install {}:0:{}'.format(module_name, version),
                vm)

            # validate swid tags Installed
            before_errata_apply_result = self._run_remote_command_on_content_host(
                "swidq -i -n {} | grep 'File' | grep -o 'rpm-.*.swidtag'".format(module_name),
                vm,
                return_result=True)
            self.assertNotEqual(before_errata_apply_result, '')
            host = entities.Host().search(query={
                'search': 'name={0}'.format(vm.hostname)})[0]
            host = host.read()
            applicable_errata_count = host.content_facet_attributes[
                'errata_counts']['total']
            self.assertEquals(applicable_errata_count, 1)

            # apply modular errata
            self._run_remote_command_on_content_host(
                'dnf -y module update {}'.format(module_name),
                vm)
            self._run_remote_command_on_content_host(
                'dnf -y upload-profile',
                vm)
            host = host.read()
            applicable_errata_count -= 1
            self.assertEqual(
                host.content_facet_attributes['errata_counts']['total'],
                applicable_errata_count
            )
            after_errata_apply_result = self._run_remote_command_on_content_host(
                "swidq -i -n {} | grep 'File'| grep -o 'rpm-.*.swidtag'".format(module_name),
                vm,
                return_result=True)

            # swidtags get updated based on package version
            self.assertNotEqual(before_errata_apply_result, after_errata_apply_result)
