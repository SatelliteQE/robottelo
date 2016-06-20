"""UI Tests for the errata management feature

@Requirement: Errata

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import stubbed, tier2, tier3
from robottelo.test import UITestCase


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

        @Assert: Errata is sorted by selected column.

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

        @Assert: Check that the errata belonging to one Org is not showing in
        the other.

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

        @Assert: Check that the new user is able to see errata for one product
        only.

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

        @Assert: Check that the erratum is applied in the selected content
        hosts.

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

        @Assert: Check that the erratum is applied in all the content hosts.

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

        @Assert: The following fields are displayed: Errata Id, Title, Type,
        Affected Content Hosts, Updated.

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

        @Assert: The following fields are displayed: : Advisory, CVEs, Type,
        Severity, Issued, Last Update on, Reboot Suggested, Topic, Description,
        Solution, Affected Packages.

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

        @Assert: The Repositories tab lists affected Products and Repositories.

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

        @Assert:

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

        @Assert: Content hosts can be filtered by Environment.

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

        @Assert: Check if autocomplete works in search field of Errata page.

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

        @Assert: Check if all the above mentioned scenarios redirect to the new
        errata page.

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

        @Assert: The errata from previous enviornments are displayed.

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

        @Assert: The errata from Library are displayed.

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

        @Assert:

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

        @Assert:

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

        @Assert: Composite content views updated with point releases.

        @caseautomation: notautomated


        @CaseLevel: System
        """
