"""UI Tests for the errata management feature

@Requirement: Errata

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from nailgun import entities
from robottelo.cli.factory import (
    make_content_view_filter,
    make_content_view_filter_rule,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.contentview import ContentView
from robottelo.constants import (
    DISTRO_RHEL7,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    run_in_one_thread,
    stubbed,
    tier2,
    tier3,
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

    @stubbed()
    @tier2
    def test_positive_sort(self):
        """Sort the columns of Errata page

        @id: 213b8592-ccb5-485d-b5fa-e445b853b20c

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.
        2. Sort by Errata Id, Title, Type, Affected Content Hosts, Updated.

        @expectedresults: Errata is sorted by selected column.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_list(self):
        """View all errata in an Org

        @id: 71c7a054-a644-4c1e-b304-6bc34ea143f4

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Create two Orgs each having a product synced which contains errata.

        @expectedresults: Check that the errata belonging to one Org is not
        showing in the other.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_list_permission(self):
        """Show errata only if the User has permissions to view them

        @id: cdb28f6a-23df-47a2-88ab-cd3b492126b2

        @Setup:

        1. Create two products with one repo each. Sync them.
        2. Make sure that they both have errata.
        3. Create a user with view access on one product and not on the other.

        @Steps:

        1. Go to Content -> Errata.

        @expectedresults: Check that the new user is able to see errata for one
        product only.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_apply_for_host(self):
        """Apply an erratum for selected content hosts

        @id: 442d1c20-bf7e-4e4c-9a48-ab3f4809fa61

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
        2. Select few Content Hosts and apply the erratum.

        @expectedresults: Check that the erratum is applied in the selected
        content hosts.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_apply_for_all_hosts(self):
        """Apply an erratum for all content hosts

        @id: d70a1bee-67f4-4883-a0b9-2ccc08a91738

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
        2. Select all Content Hosts and apply the erratum.

        @expectedresults: Check that the erratum is applied in all the content
        hosts.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_view(self):
        """View erratum similar to RH Customer portal

        @id: 7d0814fd-70e8-4451-ac96-c632cae55731

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata. Review the Errata page.

        @expectedresults: The following fields are displayed: Errata Id, Title,
        Type, Affected Content Hosts, Updated.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_view_details(self):
        """View erratum details similar to RH Customer portal

        @id: c00aeacc-eefb-4371-a0ee-5a68041a16a2

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.  Select an Errata -> Details tab.

        @expectedresults: The following fields are displayed: : Advisory, CVEs,
        Type, Severity, Issued, Last Update on, Reboot Suggested, Topic,
        Description, Solution, Affected Packages.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_view_products_and_repos(self):
        """View a list of products/repositories for an erratum

        @id: 3023006d-514f-436a-b12b-dc08d9609fa6

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.  Select an Errata -> Repositories tab.

        @expectedresults: The Repositories tab lists affected Products and
        Repositories.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_view_cve(self):
        """View CVE number(s) in Errata Details page

        @id: e1c2de13-fed8-448e-b618-c2adb6e82a35

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.  Select an Errata.

        @expectedresults:

        1: Check if the CVE information is shown in Errata Details page.

        2. Check if 'N/A' is displayed if CVE information is not present.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_filter(self):
        """Filter Content hosts by environment

        @id: 578c3a92-c4d8-4933-b122-7ff511c276ec

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.  Select an Errata -> Content Hosts tab ->
        Filter content hosts by Environment.

        @expectedresults: Content hosts can be filtered by Environment.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_search(self):
        """Check if autocomplete works in search field of Errata page

        @id: d93941d9-faad-4a31-9815-87dff9132082

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.

        @expectedresults: Check if autocomplete works in search field of Errata
        page.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_search_redirect(self):
        """Check if all the errata searches are redirected to the new
        errata page

        @id: 3de38510-d0d9-447e-8dee-a3aadba1f3c7

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Products -> Repositories ->
        Click on any of the errata hyperlink.
        2. Go to Content -> Products -> Repositories -> Click on a repository->
        Click on any of the errata hyperlink.
        3. Go to Content -> Content Views -> Select a Content View -> Yum
        Content -> Click on any of the errata hyperlink.
        4. Go to Content -> Content Views -> Select a Content View -> Yum
        Content -> Filters -> Select a Filter -> Click on any of the errata
        hyperlink.

        @expectedresults: Check if all the above mentioned scenarios redirect
        to the new errata page.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_content_host_previous(self):
        """Check if the applicable errata are available from the content
        host's previous environment

        @id: 78110ba8-3942-46dd-8c14-bffa1dbd5195

        @Setup:

        1. Make sure multiple environments are present.
        2. Content host's previous environments have additional errata.

        @Steps:

        1. Go to Content Hosts -> Select content host -> Errata Tab -> Select
        Previous environments.

        @expectedresults: The errata from previous enviornments are displayed.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_content_host_library(self):
        """Check if the applicable errata are available from the content
        host's Library

        @id: 4e627410-b7b8-471b-b9b4-a18e77fdd3f8

        @Setup:

        1. Make sure multiple environments are present.
        2. Content host's Library environment has additional errata.

        @Steps:

        1. Go to Content Hosts -> Select content host -> Errata Tab -> Select
        'Library'.

        @expectedresults: The errata from Library are displayed.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_show_count_on_content_host_page(self):
        """Available errata count displayed in Content hosts page

        @id: 8575e282-d56e-41dc-80dd-f5f6224417cb

        @Setup:

        1. Errata synced on satellite server.
        2. Some content hosts are present.

        @Steps:

        1. Go to Hosts -> Content Hosts.

        @expectedresults:

        1. The available errata count is displayed.
        2. Errata count is displayed with color icons.

           - An errata count of 0 = green
           - If security errata, >0 = red
           - If any other errata, >0 = yellow

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_show_count_on_content_host_details_page(self):
        """Errata count on Content host Details page

        @id: 388229da-2b0b-41aa-a457-9b5ecbf3df4b

        @Setup:

        1. Errata synced on satellite server.
        2. Some content hosts are present.

        @Steps:

        1. Go to Hosts -> Content Hosts -> Select Content Host -> Details page.

        @expectedresults:

        1. The errata section should be displayed with Security, Bugfix,
        Enhancement types.
        2. The number should link to the errata details page, filtered  by
        type.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @tier3
    def test_positive_incremental_update(self):
        """Update composite content views and environments with new
        point releases

        @id: d30bae6f-e45f-4ba9-9151-32dfa14ed2b8

        @Setup:

        1. Errata synced on satellite server.
        2. Composite content views present.

        @Steps:

        1. As a user, I would expect updated point releases to update
        composites with a new point release as well in the respective
        environments (i.e. if ComponentA gets updated from 1.0 to 1.1, any
        composite that is using 1.0 will have a new point release bumped and
        published with the new 1.1 ComponentA and pushed to the environment
        it was in.

        @expectedresults: Composite content views updated with point releases.

        @caseautomation: notautomated


        @CaseLevel: System
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
    def test_positive_errata_status_installable_param(self):
        """Filter errata for specific content view and verify that host that
        was registered using that content view has different states in
        correspondence to filtered errata and `errata status installable`
        settings flag value

        @id: ed94cf34-b8b9-4411-8edc-5e210ea6af4f

        @Steps:

        1. Prepare setup: Create Lifecycle Environment, Content View,
        Activation Key and all necessary repos
        2. Register Content Host using created data
        3. Create necessary Content View Filter and Rule for repository errata
        4. Publish and Promote Content View to a new version and remove old
        ones.
        5. Go to created Host page and check its properties
        6. Change 'errata status installable' flag in the settings and check
        host properties once more

        @expectedresults: Check that 'errata status installable' flag works as
        intended

        @BZ: 1368254

        @CaseLevel: System
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
        })
        custom_entitites = setup_org_for_a_custom_repo({
            'url': CUSTOM_REPO_URL,
            'organization-id': self.session_org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            result = client.register_contenthost(
                self.session_org.label,
                activation_key.name,
            )
            self.assertEqual(result.return_code, 0)
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
            with Session(self.browser) as session:
                edit_param(
                    session,
                    tab_locator=tab_locators['settings.tab_katello'],
                    param_name='errata_status_installable',
                    value_type='dropdown',
                    param_value='true',
                )
                expected_dict = {
                    'Status': u'Warning',
                    'Errata': u'Non-security errata installable',
                    'Subscription': u'Fully entitled',
                }
                actual_dict = self.hosts.get_host_properties(
                    client.hostname, expected_dict.keys())
                self.assertEqual(expected_dict, actual_dict)
                edit_param(
                    session,
                    tab_locator=tab_locators['settings.tab_katello'],
                    param_name='errata_status_installable',
                    value_type='dropdown',
                    param_value='false',
                )
                expected_dict = {
                    'Status': u'Error',
                    'Errata': u'Security errata applicable',
                    'Subscription': u'Fully entitled',
                }
                actual_dict = self.hosts.get_host_properties(
                    client.hostname, expected_dict.keys())
                self.assertEqual(expected_dict, actual_dict)
