"""CLI Tests for the errata management feature"""

# For ease of use hc refers to host-collection throughout this document

from robottelo.decorators import stubbed
from robottelo.test import CLITestCase


class HostCollectionErrataInstallTestCase(CLITestCase):
    """CLI Tests for the errata management feature"""

    @stubbed()
    def test_positive_install_by_hc_id_and_org_id(self):
        """@Test: Using hc-id and org id to install an erratum in a hc

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --id <id>
           --organization-id <orgid>

        @Assert: Erratum is installed.

        @Status: Manual

        """

    @stubbed()
    def test_positive_install_by_hc_id_and_org_name(self):
        """@Test: Using hc-id and org name to install an erratum in a hc

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --id <id>
           --organization <org name>

        @Assert: Erratum is installed.

        @Status: Manual

        """

    @stubbed()
    def test_positive_install_by_hc_id_and_org_label(self):
        """@Test: Use hc-id and org label to install an erratum in a hc

        @Feature: Errata

        @Setup: errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --id <id>
           --organization-label <org label>

        @Assert: Errata is installed.

        @Status: Manual

        """

    @stubbed()
    def test_positive_install_by_hc_name_and_org_id(self):
        """@Test: Use hc-name and org id to install an erratum in a hc

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --name <name>
           --organization-id <orgid>

        @Assert: Erratum is installed.

        @Status: Manual

        """

    @stubbed()
    def test_positive_install_by_hc_name_and_org_name(self):
        """@Test: Use hc name and org name to install an erratum in a hc

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --name <name>
           --organization <org name>

        @Assert: Erratum is installed.

        @Status: Manual

        """

    @stubbed()
    def test_positive_install_by_hc_name_and_org_label(self):
        """@Test: Use hc-name and org label to install an erratum in a hc

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --name <name>
           --organization-label <org label>

        @Assert: Erratum is installed.

        @Status: Manual

        """

    @stubbed()
    def test_negative_install_by_hc_id_without_errata_info(self):
        """@Test: Attempt to install an erratum in a hc using hc-id and not
        specifying the erratum info

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --id <id> --organization-id <orgid>

        @Assert: Error message thrown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_install_by_hc_name_without_errata_info(self):
        """@Test: Attempt to install an erratum in a hc using hc-name and not
        specifying the erratum info

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --name <name> --organization-id
           <orgid>

        @Assert: Error message thrown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_install_without_hc_info(self):
        """@Test: Attempt to install an erratum in a hc by not specifying hc
        info

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --organization-id
           <orgid>

        @Assert: Error message thrown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_install_by_hc_id_without_org_info(self):
        """@Test: Attempt to install an erratum in a hc using hc-id and not
        specifying org info

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --id <id>

        @Assert: Error message thrown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_install_by_hc_name_without_org_info(self):
        """@Test: Attempt to install an erratum in a hc without specifying org
        info

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --name <name>

        @Assert: Error message thrown.

        @Status: Manual

        """


class ErrataTestCase(CLITestCase):
    @stubbed()
    def test_positive_list_sort_by_issued_date(self):
        """@Test: Sort errata by Issued date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --order 'issued ASC'
        2. erratum list --order 'issued DESC'

        @Assert: Errata is sorted by Issued date.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_id_and_sort_by_updated_date(self):
        """@Test: Filter errata by org id and sort by updated date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-id=<orgid> --order 'updated ASC'
        2. erratum list --organization-id=<orgid> --order 'updated DESC'

        @Assert: Errata is filtered by org id and sorted by updated date.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_name_and_sort_by_updated_date(self):
        """@Test: Filter errata by org name and sort by updated date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization=<org name> --order 'updated ASC'
        2. erratum list --organization=<org name> --order 'updated DESC'

        @Assert: Errata is filtered by org name and sorted by updated date.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_label_and_sort_by_updated_date(self):
        """@Test: Filter errata by org label and sort by updated date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-label=<org_label> --order 'updated ASC'
        2. erratum list --organization-label=<org_label> --order 'updated DESC'

        @Assert: Errata is filtered by org label and sorted by updated date.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_id_and_sort_by_issued_date(self):
        """@Test: Filter errata by org id and sort by issued date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-id=<org_id> --order 'issued ASC'
        2. erratum list --organization-id=<org_id> --order 'issued DESC'

        @Assert: Errata is filtered by org id and sorted by issued date.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_name_and_sort_by_issued_date(self):
        """@Test: Filter errata by org name and sort by issued date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization=<org_name> --order 'issued ASC'
        2. erratum list --organization=<org_name> --order 'issued DESC'

        @Assert: Errata is filtered by org name and sorted by issued date.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_label_and_sort_by_issued_date(self):
        """@Test: Filter errata by org label and sort by issued date

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-label=<org_label> --order 'issued ASC'
        2. erratum list --organization-label=<org_label> --order 'issued DESC'

        @Assert: Errata is filtered by org label and sorted by issued date.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_product_id(self):
        """@Test: Filter errata by product id

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product-id=<productid>

        @Assert: Errata is filtered by product id.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_product_id_and_org_id(self):
        """@Test: Filter errata by product id and Org id

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product-id=<product_id> --organization-id=<org_id>

        @Assert: Errata is filtered by product id and Org id.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_product_id_and_org_name(self):
        """@Test: Filter errata by product id and Org name

        @Feature: Errata

        @Setup: errata synced on satellite server.

        @Steps:

        1. erratum list --product-id=<product_id> --organization=<org_name>

        @Assert: Errata is filtered by product id and Org name.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_product_id_and_org_label(self):
        """@Test: Filter errata by product id and Org label

        @Feature: Errata

        @Setup: errata synced on satellite server.

        @Steps:

        1. erratum list --product-id=<product_id>
           --organization-label=<org_label>

        @Assert: Errata is filtered by product id and Org label

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_product_name(self):
        """@Test: Filter errata by product name

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product=<productname>

        @Assert: Errata is filtered by product name.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_product_name_and_org_id(self):
        """@Test: Filter errata by product name and Org id

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product=<product_name> --organization-id=<org_id>

        @Assert: Errata is filtered by product name and Org id.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_product_name_and_org_name(self):
        """@Test: Filter errata by product name and Org name

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product=<product_name> --organization=<org_name>

        @Assert: Errata is filtered by product name and Org name.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_product_name_and_org_label(self):
        """@Test: Filter errata by product name and Org label

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product=<product_name>
           --organization-label=<org_label>

        @Assert: Errata is filtered by product name and Org label.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_id(self):
        """@Test: Filter errata by Org id

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-id=<orgid>

        @Assert: Errata is filtered by Org id.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_name(self):
        """@Test: Filter errata by Org name

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization=<org name>

        @Assert: Errata is filtered by Org name.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_org_label(self):
        """@Test: Filter errata by Org label

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-label=<org_label>

        @Assert: Errata is filtered by Org label.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_filter_by_cve(self):
        """@Test: Filter errata by CVE

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --cve <cve_id>

        @Assert: Errata is filtered by CVE.

        @Status: Manual

        """

    @stubbed()
    def test_positive_user_permission(self):
        """@Test: Show errata only if the User has permissions to view them

        @Feature: Errata

        @Setup:

        1. Create two products with one repo each. Sync them.
        2. Make sure that they both have errata.
        3. Create a user with view access on one product and not on the other.

        @Steps:

        1. erratum list --organization-id=<orgid>

        @Assert: Check that the new user is able to see errata for one
        product only.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_affected_chosts(self):
        """@Test: View a list of affected content hosts for an erratum

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. content-host list --erratum-id=<erratum_id>
           --organization-id=<org_id>

        @Assert: List of affected content hosts for an erratum is displayed.

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_affected_chosts_by_erratum_restrict_flag(self):
        """@Test: View a list of affected content hosts for an erratum filtered
        with restrict flags

        @Feature: Errata

        @Setup: Errata synced on satellite server.

        @Steps:

        1. content-host list --erratum-id=<erratum_id>
           --organization-id=<org_id> --erratum-restrict-available=1
        2. content-host list --erratum-id=<erratum_id>
           --organization-id=<org_id> --erratum-restrict-unavailable=1
        3. content-host list --erratum-id=<erratum_id>
           --organization-id=<org_id> --erratum-restrict-available=0
        4. content-host list --erratum-id=<erratum_id>
           --organization-id=<org_id> --erratum-restrict-unavailable=0

        @Assert: List of affected content hosts for an erratum is displayed
        filtered with corresponding restrict flags.

        @Status: Manual

        """

    @stubbed()
    def test_positive_view_available_count_in_affected_chosts(self):
        """@Test: Available errata count displayed while viewing a list of
        Content hosts

        @Feature: Errata

        @Setup:

        1. Errata synced on satellite server.
        2. Some content hosts present.

        @Steps:

        1. hammer content-host list --organization-id=<orgid>

        @Assert: The available errata count is retrieved.

        @Status: Manual

        """
