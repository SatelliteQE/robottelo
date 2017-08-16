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

from robottelo.decorators import stubbed, tier3, upgrade
from robottelo.test import APITestCase


class ErrataTestCase(APITestCase):
    """API Tests for the errata management feature"""

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
