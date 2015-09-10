"""API Tests for the errata management feature"""

# For ease of use hc refers to host-collection throughout this document

from robottelo.decorators import stubbed
from robottelo.test import APITestCase


class ErrataTestCase(APITestCase):
    """API Tests for the errata management feature"""

    @stubbed()
    def test_hc_errata_install_1(self):
        """@Test: Install errata in a host-collection

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. PUT /katello/api/systems/bulk/update_content

        @Assert: errata is installed in the host-collection.

        @Status: Manual

        """

    @stubbed()
    def test_errata_list_1(self):
        """@Test: View all errata specific to an Org

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps: Create two Orgs each having a product synced and contains
        errata.

        @Assert: Check that the errata belonging to one Org is not showing in
        the other.

        @Status: Manual

        """

    @stubbed()
    def test_errata_list_2(self):
        """@Test: View all errata in an Org sorted by Updated

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @Assert: Errata is filtered by Org and sorted by Updated date.

        @Status: Manual

        """

    @stubbed()
    def test_errata_list_3(self):
        """@Test: Filter errata by CVE

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @Assert: Errata is filtered by CVE.

        @Status: Manual

        """

    @stubbed()
    def test_errata_systems_list_1(self):
        """@Test: View a list of affected content hosts for an erratum

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/systems

        @Assert: List of affected content hosts for the given erratum is
        retrieved.

        @Status: Manual

        """

    @stubbed()
    def test_errata_systems_list_2(self):
        """@Test: Filter errata list based on affected content hosts

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @Assert: Errata is filtered based on affected content hosts.

        @Status: Manual

        """

    @stubbed()
    def test_errata_sort_1(self):
        """@Test: Filter errata by issued date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. GET /katello/api/errata

        @Assert: Errata is sorted by issued date.

        @Status: Manual

        """

    @stubbed()
    def test_errata_content_host_1(self):
        """@Test: Filter applicable errata for a content host by current and
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
    def test_errata_content_host_2(self):
        """@Test: Available errata count when retrieving Content host

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
    def test_errata_content_view_1(self):
        """@Test: Generate a difference in errata between a set of enviroments
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
    def test_incremental_update_1(self):
        """@Test: Select multiple errata and apply them to multiple content
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
    def test_incremental_update_2(self):
        """@Test: Query a subset of environments or content views to push new
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
    def test_incremental_update_3(self):
        """@Test: Select multiple packages and apply them to multiple content
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
