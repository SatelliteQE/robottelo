"""API Tests for the errata management feature"""

# For ease of use hc refers to host-collection throughout this document

from robottelo.decorators import stubbed, tier3
from robottelo.test import APITestCase


class ErrataTestCase(APITestCase):
    """API Tests for the errata management feature"""

    @stubbed()
    @tier3
    def test_positive_install(self):
        """Install errata in a host-collection

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. PUT /katello/api/systems/bulk/update_content

        @Assert: errata is installed in the host-collection.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_list(self):
        """View all errata specific to an Org

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps: Create two Orgs each having a product synced and contains
        errata.

        @Assert: Check that the errata belonging to one Org is not showing in
        the other.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_list_updated(self):
        """View all errata in an Org sorted by Updated

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @Assert: Errata is filtered by Org and sorted by Updated date.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_filter_by_cve(self):
        """Filter errata by CVE

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @Assert: Errata is filtered by CVE.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_list_affected_systems(self):
        """View a list of affected content hosts for an erratum

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/systems

        @Assert: List of affected content hosts for the given erratum is
        retrieved.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_filter_by_affected_systems(self):
        """Filter errata list based on affected content hosts

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @Assert: Errata is filtered based on affected content hosts.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_sort_by_issued_date(self):
        """Filter errata by issued date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @Assert: Errata is sorted by issued date.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_filter_by_envs(self):
        """Filter applicable errata for a content host by current and
        Library environments

        @Feature: Errata

        @Setup:

        1. Make sure multiple environments are present.
        2. One of Content host's previous environment has additional errata.

        @Steps:

        1. GET /katello/api/errata

        @Assert: The errata for the content host is filtered by current and
        Library environments.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_get_count_for_chost(self):
        """Available errata count when retrieving Content host

        @Feature: Errata

        @Setup:

        1. Errata synced on satellite server.
        2. Some Content hosts present.

        @Steps:

        1. GET /katello/api/systems

        @Assert: The available errata count is retrieved.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_get_diff_for_cv_envs(self):
        """Generate a difference in errata between a set of environments
        for a content view

        @Feature: Errata

        @Setup:

        1. Errata synced on satellite server.
        2. Multiple environments present.

        @Steps:

        1. GET /katello/api/compare

        @Assert: Difference in errata between a set of environments for a
        content view is retrieved.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_incremental_update_apply_to_envs_cvs(self):
        """Select multiple errata and apply them to multiple content
        views in multiple environments

        @Feature: Errata

        @Setup:

        1. Errata synced on satellite server.
        2. Multiple environments/content views present.

        @Steps:

        1. POST /katello/api/systems/bulk/available_incremental_updates

        @Assert: Selected errata are applied to multiple content views in
        multiple environments.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_incremental_update_query_envs_cvs(self):
        """Query a subset of environments or content views to push new
        errata

        @Feature: Errata

        @Setup:

        1. Errata synced on satellite server.
        2. Multiple environments/content views present.

        @Steps:

        1. POST /katello/api/content_view_versions/incremental_update

        @Assert: Subset of environments/content views retrieved.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_incremental_update_apply_packages_to_envs_cvs(self):
        """Select multiple packages and apply them to multiple content
        views in multiple environments

        @Feature: Errata

        @Setup:

        1. Errata synced on satellite server.
        2. Multiple environments/content views present.

        @Steps:

        1. POST /katello/api/content_view_versions/incremental_update

        @Assert: Packages are applied to multiple environments/content views.

        @Status: Manual
        """
