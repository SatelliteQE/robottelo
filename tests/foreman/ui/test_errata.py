"""UI Tests for the errata management feature"""

from robottelo.decorators import stubbed, tier2, tier3
from robottelo.test import UITestCase


class ErrataTestCase(UITestCase):
    """UI Tests for the errata management feature"""

    @stubbed()
    @tier2
    def test_positive_sort(self):
        """Sort the columns of Errata page

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.
        2. Sort by Errata Id, Title, Type, Affected Content Hosts, Updated.

        @Assert: Errata is sorted by selected column.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_list(self):
        """View all errata in an Org

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Create two Orgs each having a product synced which contains errata.

        @Assert: Check that the errata belonging to one Org is not showing in
        the other.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_list_permission(self):
        """Show errata only if the User has permissions to view them

        @Feature: Errata

        @Setup:

        1. Create two products with one repo each. Sync them.
        2. Make sure that they both have errata.
        3. Create a user with view access on one product and not on the other.

        @Steps:

        1. Go to Content -> Errata.

        @Assert: Check that the new user is able to see errata for one product
        only.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_apply_for_host(self):
        """Apply an erratum for selected content hosts

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
        2. Select few Content Hosts and apply the erratum.

        @Assert: Check that the erratum is applied in the selected content
        hosts.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_apply_for_all_hosts(self):
        """Apply an erratum for all content hosts

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
        2. Select all Content Hosts and apply the erratum.

        @Assert: Check that the erratum is applied in all the content hosts.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_view(self):
        """View erratum similar to RH Customer portal

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata. Review the Errata page.

        @Assert: The following fields are displayed: Errata Id, Title, Type,
        Affected Content Hosts, Updated.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_view_details(self):
        """View erratum details similar to RH Customer portal

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.  Select an Errata -> Details tab.

        @Assert: The following fields are displayed: : Advisory, CVEs, Type,
        Severity, Issued, Last Update on, Reboot Suggested, Topic, Description,
        Solution, Affected Packages.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_view_products_and_repos(self):
        """View a list of products/repositories for an erratum

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.  Select an Errata -> Repositories tab.

        @Assert: The Repositories tab lists affected Products and Repositories.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_view_cve(self):
        """View CVE number(s) in Errata Details page

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.  Select an Errata.

        @Assert:

        1: Check if the CVE information is shown in Errata Details page.

        2. Check if 'N/A' is displayed if CVE information is not present.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_filter(self):
        """Filter Content hosts by environment

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.  Select an Errata -> Content Hosts tab ->
        Filter content hosts by Environment.

        @Assert: Content hosts can be filtered by Environment.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_search(self):
        """Check if autocomplete works in search field of Errata page

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. Go to Content -> Errata.

        @Assert: Check if autocomplete works in search field of Errata page.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_search_redirect(self):
        """Check if all the errata searches are redirected to the new
        errata page

        @Feature: Errata

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

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_content_host_previous(self):
        """Check if the applicable errata are available from the content
        host's previous environment

        @Feature: Errata

        @Setup:

        1. Make sure multiple environments are present.
        2. Content host's previous environments have additional errata.

        @Steps:

        1. Go to Content Hosts -> Select content host -> Errata Tab -> Select
        Previous environments.

        @Assert: The errata from previous enviornments are displayed.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_content_host_library(self):
        """Check if the applicable errata are available from the content
        host's Library

        @Feature: Errata

        @Setup:

        1. Make sure multiple environments are present.
        2. Content host's Library environment has additional errata.

        @Steps:

        1. Go to Content Hosts -> Select content host -> Errata Tab -> Select
        'Library'.

        @Assert: The errata from Library are displayed.

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_show_count_on_content_host_page(self):
        """Available errata count displayed in Content hosts page

        @Feature: Errata

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

        @Status: Manual

        """

    @stubbed()
    @tier2
    def test_positive_show_count_on_content_host_details_page(self):
        """Errata count on Content host Details page

        @Feature: Errata

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

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_incremental_update(self):
        """Update composite content views and environments with new
        point releases

        @Feature: Errata

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

        @Status: Manual

        """
