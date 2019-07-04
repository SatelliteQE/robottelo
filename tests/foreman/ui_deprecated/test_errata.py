"""UI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.cli.factory import (
    make_content_view_filter,
    make_content_view_filter_rule,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.contentview import ContentView
from robottelo.cli.host import Host
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_RELEASE_VERSION,
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_3_ERRATA_ID,
    FAKE_3_YUM_REPO,
    FAKE_6_YUM_REPO,
    PRDS,
    REAL_0_ERRATA_ID,
    REAL_0_RH_PACKAGE,
    REAL_4_ERRATA_ID,
    REAL_4_ERRATA_CVES,
    REAL_4_ERRATA_DETAILS,
    REPOS,
    REPOSET,
    TOOLS_ERRATA_TABLE_DETAILS,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier2,
    tier3,
    upgrade,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import edit_param
from robottelo.ui.locators import tab_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


CUSTOM_REPO_URL = FAKE_6_YUM_REPO
CUSTOM_REPO_ERRATA_ID = FAKE_2_ERRATA_ID


@run_in_one_thread
class ErrataTestCase(UITestCase):
    """UI Tests for the errata management feature"""

    @classmethod
    def set_session_org(cls):
        """Create an organization for tests, which will be selected
        automatically"""
        cls.session_org = entities.Organization().create()

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Set up single org with subscription to 1 RH and 1 custom products to
        reuse in tests
        """
        super(ErrataTestCase, cls).setUpClass()
        cls.env = entities.LifecycleEnvironment(
            organization=cls.session_org).create()
        cls.content_view = entities.ContentView(
            organization=cls.session_org).create()
        cls.activation_key = entities.ActivationKey(
            environment=cls.env,
            organization=cls.session_org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        }, force_manifest_upload=True)
        cls.custom_entitites = setup_org_for_a_custom_repo({
            'url': CUSTOM_REPO_URL,
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })
        rhva_repo = enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=cls.session_org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhva6']['name'],
            reposet=REPOSET['rhva6'],
            releasever=DEFAULT_RELEASE_VERSION,
        )
        assert entities.Repository(id=rhva_repo).sync()['result'] == 'success'
        cls.rhva_errata_id = REAL_4_ERRATA_ID
        cls.rhva_errata_cves = REAL_4_ERRATA_CVES

    @stubbed()
    @tier2
    def test_positive_sort(self):
        """Sort the columns of Errata page

        :id: 213b8592-ccb5-485d-b5fa-e445b853b20c

        :Setup: Errata synced on satellite server.

        :Steps:

            1. Go to Content -> Errata.
            2. Sort by Errata Id, Title, Type, Affected Content Hosts, Updated.

        :expectedresults: Errata is sorted by selected column.

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @tier2
    def test_positive_list(self):
        """View all errata in an Org

        :id: 71c7a054-a644-4c1e-b304-6bc34ea143f4

        :Setup: Errata synced on satellite server.

        :Steps: Create two Orgs each having a product synced which contains
            errata.

        :expectedresults: Check that the errata belonging to one Org is not
            showing in the other.

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_custom_repo({
            'url': FAKE_3_YUM_REPO,
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        with Session(self) as session:
            session.nav.go_to_errata()
            self.errata.show_only_applicable(False)
            self.assertIsNone(self.errata.search(FAKE_3_ERRATA_ID))
            self.assertIsNotNone(self.errata.search(CUSTOM_REPO_ERRATA_ID))
            session.nav.go_to_select_org(org.name)
            session.nav.go_to_errata()
            self.errata.show_only_applicable(False)
            self.assertIsNone(self.errata.search(CUSTOM_REPO_ERRATA_ID))
            self.assertIsNotNone(self.errata.search(FAKE_3_ERRATA_ID))

    @tier2
    def test_positive_list_permission(self):
        """Show errata only if the User has permissions to view them

        :id: cdb28f6a-23df-47a2-88ab-cd3b492126b2

        :Setup:

            1. Create two products with one repo each. Sync them.
            2. Make sure that they both have errata.
            3. Create a user with view access on one product and not on the
                other.

        :Steps: Go to Content -> Errata.

        :expectedresults: Check that the new user is able to see errata for one
            product only.

        :CaseLevel: Integration
        """
        role = entities.Role().create()
        entities.Filter(
            organization=[self.session_org],
            permission=entities.Permission(
                resource_type='Katello::Product').search(),
            role=role,
            search='name = "{0}"'.format(PRDS['rhel']),
        ).create()
        user_password = gen_string('alphanumeric')
        user = entities.User(
            default_organization=self.session_org,
            organization=[self.session_org],
            role=[role],
            password=user_password,
        ).create()
        with Session(self, user.login, user_password) as session:
            session.nav.go_to_errata()
            self.errata.show_only_applicable(False)
            self.assertIsNotNone(self.errata.search(self.rhva_errata_id))
            self.assertIsNone(self.errata.search(CUSTOM_REPO_ERRATA_ID))

    @tier3
    def test_positive_apply_for_host(self):
        """Apply an erratum for selected content hosts

        :id: 442d1c20-bf7e-4e4c-9a48-ab3f4809fa61

        :customerscenario: true

        :Setup: Errata synced on satellite server.

        :Steps:

            1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
            2. Select few Content Hosts and apply the erratum.

        :expectedresults: Check that the erratum is applied in the selected
            content hosts.

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.session_org.label,
                self.activation_key.name,
            )
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
            client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            with Session(self):
                result = self.errata.install(
                    CUSTOM_REPO_ERRATA_ID, client.hostname)
                self.assertEqual(result, 'success')
                self.assertIsNotNone(self.contenthost.package_search(
                    client.hostname, FAKE_2_CUSTOM_PACKAGE))

    @tier3
    @upgrade
    def test_positive_apply_for_all_hosts(self):
        """Apply an erratum for all content hosts

        :id: d70a1bee-67f4-4883-a0b9-2ccc08a91738

        :Setup: Errata synced on satellite server.

        :Steps:

            1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
            2. Select all Content Hosts and apply the erratum.

        :expectedresults: Check that the erratum is applied in all the content
            hosts.

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client1, VirtualMachine(
                distro=DISTRO_RHEL7) as client2:
            clients = [client1, client2]
            for client in clients:
                client.install_katello_ca()
                client.register_contenthost(
                    self.session_org.label,
                    self.activation_key.name,
                )
                self.assertTrue(client.subscribed)
                client.enable_repo(REPOS['rhst7']['id'])
                client.install_katello_agent()
                client.run(
                    'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            with Session(self):
                result = self.errata.install(
                    CUSTOM_REPO_ERRATA_ID,
                    [client.hostname for client in clients],
                )
                self.assertEqual(result, 'success')
                for client in clients:
                    self.assertIsNotNone(self.contenthost.package_search(
                        client.hostname, FAKE_2_CUSTOM_PACKAGE))

    @tier2
    def test_positive_view(self):
        """View erratum similar to RH Customer portal

        :id: 7d0814fd-70e8-4451-ac96-c632cae55731

        :Setup: Errata synced on satellite server.

        :Steps: Go to Content -> Errata. Review the Errata page.

        :expectedresults: The following fields: Errata Id, Title, Type,
            Affected Content Hosts, Updated has expected values for errata
            table.

        :CaseLevel: Integration
        """
        with Session(self):
            self.errata.validate_table_fields(
                REAL_0_ERRATA_ID,
                only_applicable=False,
                values_list=TOOLS_ERRATA_TABLE_DETAILS
            )

    @tier2
    def test_positive_view_details(self):
        """View erratum details similar to RH Customer portal

        :id: c00aeacc-eefb-4371-a0ee-5a68041a16a2

        :Setup: Errata synced on satellite server.

        :Steps: Go to Content -> Errata.  Select an Errata -> Details tab.

        :expectedresults: The following fields are displayed: : Advisory, CVEs,
            Type, Severity, Issued, Last Update on, Reboot Suggested, Topic,
            Description, Solution, Affected Packages.

        :CaseLevel: Integration
        """
        with Session(self):
            self.errata.check_errata_details(
                REAL_4_ERRATA_ID,
                REAL_4_ERRATA_DETAILS,
                only_applicable=False,
            )

    @tier2
    def test_positive_view_products_and_repos(self):
        """View a list of products/repositories for an erratum

        :id: 3023006d-514f-436a-b12b-dc08d9609fa6

        :Setup: Errata synced on satellite server.

        :Steps: Go to Content -> Errata.  Select an Errata -> Repositories tab.

        :expectedresults: The Repositories tab lists affected Products and
            Repositories.

        :CaseLevel: Integration
        """
        product = entities.Product(
            id=self.custom_entitites['product-id']).read()
        repo = entities.Repository(
            id=self.custom_entitites['repository-id']).read()
        with Session(self):
            self.assertIsNotNone(
                self.errata.repository_search(
                    CUSTOM_REPO_ERRATA_ID,
                    repo.name,
                    product.name,
                    only_applicable=False,
                )
            )

    @tier2
    @upgrade
    def test_positive_view_cve(self):
        """View CVE number(s) in Errata Details page

        :id: e1c2de13-fed8-448e-b618-c2adb6e82a35

        :Setup: Errata synced on satellite server.

        :Steps: Go to Content -> Errata.  Select an Errata.

        :expectedresults:

            1. Check if the CVE information is shown in Errata Details page.
            2. Check if 'N/A' is displayed if CVE information is not present.

        :CaseLevel: Integration
        """
        real_errata_id = self.rhva_errata_id
        real_errata_cves = set(self.rhva_errata_cves)
        with Session(self):
            self.errata.check_errata_details(
                real_errata_id,
                [['CVEs', real_errata_cves]],
                only_applicable=False,
            )
            self.errata.check_errata_details(
                CUSTOM_REPO_ERRATA_ID,
                [['CVEs_NA', 'N/A']],
                only_applicable=False,
            )

    @skip_if_bug_open('bugzilla', 1383729)
    @tier3
    @upgrade
    def test_positive_filter(self):
        """Filter Content hosts by environment

        :id: 578c3a92-c4d8-4933-b122-7ff511c276ec

        :Setup: Errata synced on satellite server.

        :Steps: Go to Content -> Errata.  Select an Errata -> Content Hosts tab
            -> Filter content hosts by Environment.

        :expectedresults: Content hosts can be filtered by Environment.

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client1, VirtualMachine(
                distro=DISTRO_RHEL7) as client2:
            for client in client1, client2:
                client.install_katello_ca()
                client.register_contenthost(
                    self.session_org.label,
                    self.activation_key.name,
                )
                self.assertTrue(client.subscribed)
                client.enable_repo(REPOS['rhst7']['id'])
                client.install_katello_agent()
                client.run(
                    'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            last_env_id = max(
                lce.id
                for lce
                in entities.LifecycleEnvironment(
                    organization=self.session_org).search()
            )
            new_env = entities.LifecycleEnvironment(
                organization=self.session_org,
                prior=last_env_id,
            ).create()
            cvv = ContentView.info({
                'id': self.content_view.id})['versions'][-1]
            ContentView.version_promote({
                'id': cvv['id'],
                'organization-id': self.session_org.id,
                'to-lifecycle-environment-id': new_env.id,
            })
            Host.update({
                'name': client1.hostname,
                'lifecycle-environment-id': new_env.id,
                'organization-id': self.session_org.id,
            })
            with Session(self):
                self.assertIsNotNone(
                    self.errata.contenthost_search(
                        CUSTOM_REPO_ERRATA_ID,
                        client1.hostname,
                        environment=new_env.name,
                    )
                )
                self.assertIsNone(
                    self.errata.contenthost_search(
                        CUSTOM_REPO_ERRATA_ID,
                        client2.hostname,
                        environment=new_env.name,
                    )
                )
                self.assertIsNotNone(
                    self.errata.contenthost_search(
                        CUSTOM_REPO_ERRATA_ID,
                        client2.hostname,
                        environment=self.env.name,
                    )
                )
                self.assertIsNone(
                    self.errata.contenthost_search(
                        CUSTOM_REPO_ERRATA_ID,
                        client1.hostname,
                        environment=self.env.name,
                    )
                )

    @tier2
    def test_positive_search_autocomplete(self):
        """Check if autocomplete works in search field of Errata page

        :id: d93941d9-faad-4a31-9815-87dff9132082

        :Setup: Errata synced on satellite server.

        :Steps: Go to Content -> Errata.

        :expectedresults: Check if autocomplete works in search field of Errata
            page.

        :CaseLevel: Integration
        """
        with Session(self):
            self.assertIsNotNone(
                self.errata.auto_complete_search(
                    CUSTOM_REPO_ERRATA_ID, only_applicable=False)
            )

    @stubbed()
    @tier2
    def test_positive_search_redirect(self):
        """Check if all the errata searches are redirected to the new
        errata page

        :id: 3de38510-d0d9-447e-8dee-a3aadba1f3c7

        :Setup: Errata synced on satellite server.

        :Steps:

            1. Go to Content -> Products -> Repositories -> Click on any of the
                errata hyperlink.
            2. Go to Content -> Products -> Repositories -> Click on a
                repository-> Click on any of the errata hyperlink.
            3. Go to Content -> Content Views -> Select a Content View -> Yum
                Content -> Click on any of the errata hyperlink.
            4. Go to Content -> Content Views -> Select a Content View -> Yum
                Content -> Filters -> Select a Filter -> Click on any of the
                errata hyperlink.

        :expectedresults: Check if all the above mentioned scenarios redirect
            to the new errata page.

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @tier3
    @upgrade
    def test_positive_chost_previous_env(self):
        """Check if the applicable errata are available from the content
        host's previous environment

        :id: 78110ba8-3942-46dd-8c14-bffa1dbd5195

        :Setup:

            1. Make sure multiple environments are present.
            2. Content host's previous environments have additional errata.

        :Steps: Go to Content Hosts -> Select content host -> Errata Tab ->
            Select Previous environments.

        :expectedresults: The errata from previous environments are displayed.

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.session_org.label,
                self.activation_key.name,
            )
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
            client.run(
                'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            last_env_id = max(lce.id for lce in entities.LifecycleEnvironment(
                    organization=self.session_org).search()
            )
            new_env = entities.LifecycleEnvironment(
                organization=self.session_org,
                prior=last_env_id,
            ).create()
            cvv = ContentView.info({
                'id': self.content_view.id
            })['versions'][-1]
            ContentView.version_promote({
                'id': cvv['id'],
                'organization-id': self.session_org.id,
                'to-lifecycle-environment-id': new_env.id,
            })
            Host.update({
                'name': client.hostname,
                'lifecycle-environment-id': new_env.id,
                'organization-id': self.session_org.id,
            })
            with Session(self):
                self.assertIsNotNone(
                    self.contenthost.errata_search(
                        client.hostname,
                        CUSTOM_REPO_ERRATA_ID,
                        environment_name=self.env.name,
                    )
                )

    @tier3
    def test_positive_chost_library(self):
        """Check if the applicable errata are available from the content
        host's Library

        :id: 4e627410-b7b8-471b-b9b4-a18e77fdd3f8

        :Setup:

            1. Make sure multiple environments are present.
            2. Content host's Library environment has additional errata.

        :Steps: Go to Content Hosts -> Select content host -> Errata Tab ->
            Select 'Library'.

        :expectedresults: The errata from Library are displayed.

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.session_org.label,
                self.activation_key.name,
            )
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
            client.run(
                'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            with Session(self):
                self.assertIsNotNone(
                    self.contenthost.errata_search(
                        client.hostname,
                        CUSTOM_REPO_ERRATA_ID,
                        environment_name='Library Synced Content',
                    )
                )

    @tier3
    def test_positive_show_count_on_chost_page(self):
        """Available errata count displayed in Content hosts page

        :id: 8575e282-d56e-41dc-80dd-f5f6224417cb

        :Setup:

            1. Errata synced on satellite server.
            2. Some content hosts are present.

        :Steps: Go to Hosts -> Content Hosts.

        :expectedresults:

            1. The available errata count is displayed.
            2. Errata count is displayed with color icons.

           - An errata count of 0 = black
           - If security errata, >0 = red
           - If any other errata, >0 = yellow

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
        RepositorySet.enable({
            'basearch': DEFAULT_ARCHITECTURE,
            'name': REPOSET['rhva6'],
            'organization-id': org.id,
            'product': PRDS['rhel'],
            'releasever': DEFAULT_RELEASE_VERSION,
        })
        rhel_repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'organization-id': org.id,
            'product': PRDS['rhel'],
        })
        Repository.synchronize({
            'name': REPOS['rhva6']['name'],
            'organization-id': org.id,
            'product': PRDS['rhel'],
        })
        ContentView.add_repository({
            'id': content_view.id,
            'organization-id': org.id,
            'repository-id': rhel_repo['id'],
        })
        ContentView.publish({'id': content_view.id})
        cvv = ContentView.info({'id': content_view.id})['versions'][-1]
        ContentView.version_promote({
            'id': cvv['id'],
            'organization-id': org.id,
            'to-lifecycle-environment-id': env.id,
        })
        with VirtualMachine(distro=DISTRO_RHEL6) as client:
            client.install_katello_ca()
            client.register_contenthost(org.label, activation_key.name)
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst6']['id'])
            client.enable_repo(REPOS['rhva6']['id'])
            client.install_katello_agent()
            with Session(self) as session:
                session.nav.go_to_select_org(org.name)
                result = self.contenthost.fetch_errata_counts(client.hostname)
                for errata in ('security', 'bug_fix', 'enhancement'):
                    self.assertEqual(result[errata]['value'], 0)
                    if bz_bug_is_open(1484044):
                        self.assertNotIn(
                            result['security']['color'], ('red', 'yellow'))
                    else:
                        self.assertEqual(result['security']['color'], 'black')

                client.run(
                    'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
                result = self.contenthost.fetch_errata_counts(client.hostname)
                self.assertEqual(result['security']['value'], 1)
                self.assertEqual(result['security']['color'], 'red')
                client.run('yum install -y {0}'.format(REAL_0_RH_PACKAGE))
                result = self.contenthost.fetch_errata_counts(client.hostname)
                for errata in ('bug_fix', 'enhancement'):
                    self.assertEqual(result[errata]['value'], 1)
                    self.assertEqual(result[errata]['color'], 'yellow')

    @tier3
    def test_positive_show_count_on_chost_details_page(self):
        """Errata count on Content host Details page

        :id: 388229da-2b0b-41aa-a457-9b5ecbf3df4b

        :Setup:

            1. Errata synced on satellite server.
            2. Some content hosts are present.

        :Steps: Go to Hosts -> Content Hosts -> Select Content Host -> Details
            page.

        :expectedresults:

            1. The errata section should be displayed with Security, Bugfix,
                Enhancement types.
            2. The number should link to the errata details page, filtered  by
                type.

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
        RepositorySet.enable({
            'basearch': DEFAULT_ARCHITECTURE,
            'name': REPOSET['rhva6'],
            'organization-id': org.id,
            'product': PRDS['rhel'],
            'releasever': DEFAULT_RELEASE_VERSION,
        })
        rhel_repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'organization-id': org.id,
            'product': PRDS['rhel'],
        })
        Repository.synchronize({
            'name': REPOS['rhva6']['name'],
            'organization-id': org.id,
            'product': PRDS['rhel'],
        })
        ContentView.add_repository({
            'id': content_view.id,
            'organization-id': org.id,
            'repository-id': rhel_repo['id'],
        })
        ContentView.publish({'id': content_view.id})
        cvv = ContentView.info({'id': content_view.id})['versions'][-1]
        ContentView.version_promote({
            'id': cvv['id'],
            'organization-id': org.id,
            'to-lifecycle-environment-id': env.id,
        })
        with VirtualMachine(distro=DISTRO_RHEL6) as client:
            client.install_katello_ca()
            client.register_contenthost(org.label, activation_key.name)
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst6']['id'])
            client.enable_repo(REPOS['rhva6']['id'])
            client.install_katello_agent()
            with Session(self) as session:
                session.nav.go_to_select_org(org.name)
                result = self.contenthost.fetch_errata_counts(
                    client.hostname, details_page=True)
                for errata in ('security', 'bug_fix', 'enhancement'):
                    self.assertEqual(result[errata]['value'], 0)
                if bz_bug_is_open(1484044):
                    self.assertNotIn(
                        result['security']['color'], ('red', 'yellow'))
                else:
                    self.assertEqual(result['security']['color'], 'black')
                client.run(
                    'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
                result = self.contenthost.fetch_errata_counts(
                    client.hostname, details_page=True)
                self.assertEqual(result['security']['value'], 1)
                self.assertEqual(result['security']['color'], 'red')
                client.run('yum install -y {0}'.format(REAL_0_RH_PACKAGE))
                result = self.contenthost.fetch_errata_counts(
                    client.hostname, details_page=True)
                for errata in ('bug_fix', 'enhancement'):
                    self.assertEqual(result[errata]['value'], 1)
                    self.assertEqual(result[errata]['color'], 'yellow')

    @stubbed()
    @tier3
    def test_positive_incremental_update(self):
        """Update composite content views and environments with new
        point releases

        :id: d30bae6f-e45f-4ba9-9151-32dfa14ed2b8

        :Setup:

            1. Errata synced on satellite server.
            2. Composite content views present.

        :Steps: As a user, I would expect updated point releases to update
            composites with a new point release as well in the respective
            environments (i.e. if ComponentA gets updated from 1.0 to 1.1, any
            composite that is using 1.0 will have a new point release bumped
            and published with the new 1.1 ComponentA and pushed to the
            environment it was in.

        :expectedresults: Composite content views updated with point releases.

        :caseautomation: notautomated

        :CaseLevel: System
        """


@run_in_one_thread
class FilteredErrataTestCase(UITestCase):
    """UI Tests for filtering functionality of errata management feature"""

    @classmethod
    def set_session_org(cls):
        """Create an organization for tests, which will be selected
        automatically"""
        cls.session_org = entities.Organization().create()

    @tier3
    @upgrade
    def test_positive_errata_status_installable_param(self):
        """Filter errata for specific content view and verify that host that
        was registered using that content view has different states in
        correspondence to filtered errata and `errata status installable`
        settings flag value

        :id: ed94cf34-b8b9-4411-8edc-5e210ea6af4f

        :Steps:

            1. Prepare setup: Create Lifecycle Environment, Content View,
                Activation Key and all necessary repos
            2. Register Content Host using created data
            3. Create necessary Content View Filter and Rule for repository
                errata
            4. Publish and Promote Content View to a new version and remove old
                ones.
            5. Go to created Host page and check its properties
            6. Change 'errata status installable' flag in the settings and
                check host properties once more

        :expectedresults: Check that 'errata status installable' flag works as
            intended

        :BZ: 1368254

        :CaseLevel: System
        """
        env = entities.LifecycleEnvironment(
            organization=self.session_org).create()
        content_view = entities.ContentView(
            organization=self.session_org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=self.session_org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': self.session_org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        }, force_manifest_upload=True)
        custom_entitites = setup_org_for_a_custom_repo({
            'url': CUSTOM_REPO_URL,
            'organization-id': self.session_org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.session_org.label,
                activation_key.name,
            )
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
            client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            # Adding content view filter and content view filter rule to
            # exclude errata that we are going to track
            cvf = make_content_view_filter({
                u'content-view-id': content_view.id,
                u'inclusion': 'false',
                u'organization-id': self.session_org.id,
                u'repository-ids': custom_entitites['repository-id'],
                u'type': 'erratum',
            })
            make_content_view_filter_rule({
                u'content-view-id': content_view.id,
                u'content-view-filter-id': cvf['filter-id'],
                u'errata-id': CUSTOM_REPO_ERRATA_ID,
            })
            ContentView.publish({u'id': content_view.id})
            cvv = ContentView.info({u'id': content_view.id})['versions'][-1]
            ContentView.version_promote({
                u'id': cvv['id'],
                u'organization-id': self.session_org.id,
                u'to-lifecycle-environment-id': env.id,
            })
            # Remove old cv versions to have unambiguous one for testing
            cvvs = ContentView.info({u'id': content_view.id})['versions']
            self.assertGreater(len(cvvs), 1)
            for i in range(len(cvvs)-1):
                ContentView.version_delete({u'id': cvvs[i]['id']})
            with Session(self) as session:
                edit_param(
                    session,
                    tab_locator=tab_locators['settings.tab_content'],
                    param_name='errata_status_installable',
                    param_value='Yes',
                )
                expected_dict = {
                    'Status': 'OK',
                    'Errata': 'All errata applied',
                    'Subscription': 'Fully entitled',
                }
                actual_dict = self.hosts.get_host_properties(
                    client.hostname, expected_dict.keys())
                self.assertEqual(expected_dict, actual_dict)
                edit_param(
                    session,
                    tab_locator=tab_locators['settings.tab_content'],
                    param_name='errata_status_installable',
                    param_value='No',
                )
                expected_dict = {
                    'Status': 'Error',
                    'Errata': 'Security errata applicable',
                    'Subscription': 'Fully entitled',
                }
                actual_dict = self.hosts.get_host_properties(
                    client.hostname, expected_dict.keys())
                self.assertEqual(expected_dict, actual_dict)
