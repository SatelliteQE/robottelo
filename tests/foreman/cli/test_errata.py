"""CLI Tests for the errata management feature

@Requirement: Errata

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

# For ease of use hc refers to host-collection throughout this document

from robottelo.decorators import stubbed
from robottelo.test import CLITestCase


class HostCollectionErrataInstallTestCase(CLITestCase):
    """CLI Tests for the errata management feature"""

    @stubbed()
    def test_positive_install_by_hc_id_and_org_id(self):
        """Using hc-id and org id to install an erratum in a hc

        @id: 8b22eb9d-1321-4374-8127-6d7bfdb89ad5

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --id <id>
           --organization-id <orgid>

        @Assert: Erratum is installed.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_install_by_hc_id_and_org_name(self):
        """Using hc-id and org name to install an erratum in a hc

        @id: 7e5b87d7-f4d2-47b7-96aa-f86bcb64c742

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --id <id>
           --organization <org name>

        @Assert: Erratum is installed.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_install_by_hc_id_and_org_label(self):
        """Use hc-id and org label to install an erratum in a hc

        @id: bde80181-6526-43dc-bfc2-511bb5c00676

        @Setup: errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --id <id>
           --organization-label <org label>

        @Assert: Errata is installed.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_install_by_hc_name_and_org_id(self):
        """Use hc-name and org id to install an erratum in a hc

        @id: c4a38806-cbec-47cc-bbd6-228897b3b16d

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --name <name>
           --organization-id <orgid>

        @Assert: Erratum is installed.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_install_by_hc_name_and_org_name(self):
        """Use hc name and org name to install an erratum in a hc

        @id: 501319ea-9d3c-4329-9405-4366ce6ee797

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --name <name>
           --organization <org name>

        @Assert: Erratum is installed.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_install_by_hc_name_and_org_label(self):
        """Use hc-name and org label to install an erratum in a hc

        @id: 12287827-44df-4dda-872a-ac7e416e8bd7

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --name <name>
           --organization-label <org label>

        @Assert: Erratum is installed.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_negative_install_by_hc_id_without_errata_info(self):
        """Attempt to install an erratum in a hc using hc-id and not
        specifying the erratum info

        @id: 3635698d-4f09-4a60-91ea-1957e5949750

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --id <id> --organization-id <orgid>

        @Assert: Error message thrown.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_negative_install_by_hc_name_without_errata_info(self):
        """Attempt to install an erratum in a hc using hc-name and not
        specifying the erratum info

        @id: 12d78bca-efd1-407a-9bd3-f989c2bda6a8

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --name <name> --organization-id
           <orgid>

        @Assert: Error message thrown.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_negative_install_without_hc_info(self):
        """Attempt to install an erratum in a hc by not specifying hc
        info

        @id: 753d36f0-d19b-494d-a247-ce2d61c4cf74

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --organization-id
           <orgid>

        @Assert: Error message thrown.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_negative_install_by_hc_id_without_org_info(self):
        """Attempt to install an erratum in a hc using hc-id and not
        specifying org info

        @id: b7d32bb3-9c5f-452b-b421-f8e9976ca52c

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --id <id>

        @Assert: Error message thrown.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_negative_install_by_hc_name_without_org_info(self):
        """Attempt to install an erratum in a hc without specifying org
        info

        @id: 991f5b61-a4d1-444c-8a21-8ffe48e83f76

        @Setup: Errata synced on satellite server.

        @Steps:

        1. host-collection erratum install --errata <errata> --name <name>

        @Assert: Error message thrown.

        @caseautomation: notautomated

        """


class ErrataTestCase(CLITestCase):
    @stubbed()
    def test_positive_list_sort_by_issued_date(self):
        """Sort errata by Issued date

        @id: d838a969-d70a-43ae-9805-2e94dd985d6b

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --order 'issued ASC'
        2. erratum list --order 'issued DESC'

        @Assert: Errata is sorted by Issued date.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_id_and_sort_by_updated_date(self):
        """Filter errata by org id and sort by updated date

        @id: 9b7f98ee-bbde-47b6-8727-b02550df13ae

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-id=<orgid> --order 'updated ASC'
        2. erratum list --organization-id=<orgid> --order 'updated DESC'

        @Assert: Errata is filtered by org id and sorted by updated date.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_name_and_sort_by_updated_date(self):
        """Filter errata by org name and sort by updated date

        @id: f202616b-cd4f-4ab2-bf2a-2788579e355a

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization=<org name> --order 'updated ASC'
        2. erratum list --organization=<org name> --order 'updated DESC'

        @Assert: Errata is filtered by org name and sorted by updated date.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_label_and_sort_by_updated_date(self):
        """Filter errata by org label and sort by updated date

        @id: ce891bdf-cc2f-46e9-ab43-91527d40c3ed

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-label=<org_label> --order 'updated ASC'
        2. erratum list --organization-label=<org_label> --order 'updated DESC'

        @Assert: Errata is filtered by org label and sorted by updated date.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_id_and_sort_by_issued_date(self):
        """Filter errata by org id and sort by issued date

        @id: 5d0f396c-f930-4fe7-8d1e-5039a4ed359a

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-id=<org_id> --order 'issued ASC'
        2. erratum list --organization-id=<org_id> --order 'issued DESC'

        @Assert: Errata is filtered by org id and sorted by issued date.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_name_and_sort_by_issued_date(self):
        """Filter errata by org name and sort by issued date

        @id: 22f05ac0-fefa-48c4-861d-eeed41d9b235

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization=<org_name> --order 'issued ASC'
        2. erratum list --organization=<org_name> --order 'issued DESC'

        @Assert: Errata is filtered by org name and sorted by issued date.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_label_and_sort_by_issued_date(self):
        """Filter errata by org label and sort by issued date

        @id: 31acb734-8705-4d3c-b05e-edfd63d1ca3b

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-label=<org_label> --order 'issued ASC'
        2. erratum list --organization-label=<org_label> --order 'issued DESC'

        @Assert: Errata is filtered by org label and sorted by issued date.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_product_id(self):
        """Filter errata by product id

        @id: 7d06950a-c058-48b3-a384-c3565cbd643f

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product-id=<productid>

        @Assert: Errata is filtered by product id.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_product_id_and_org_id(self):
        """Filter errata by product id and Org id

        @id: caf14671-d8b2-4a23-8c7e-6667bb78d4b7

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product-id=<product_id> --organization-id=<org_id>

        @Assert: Errata is filtered by product id and Org id.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_product_id_and_org_name(self):
        """Filter errata by product id and Org name

        @id: 574a6f7e-a89e-482e-bf15-39cfd7730630

        @Setup: errata synced on satellite server.

        @Steps:

        1. erratum list --product-id=<product_id> --organization=<org_name>

        @Assert: Errata is filtered by product id and Org name.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_product_id_and_org_label(self):
        """Filter errata by product id and Org label

        @id: 7b92ee32-2386-452c-9443-65b0c233a564

        @Setup: errata synced on satellite server.

        @Steps:

        1. erratum list --product-id=<product_id>
           --organization-label=<org_label>

        @Assert: Errata is filtered by product id and Org label

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_product_name(self):
        """Filter errata by product name

        @id: c7a5988b-668f-4c48-bc1e-97cb968a2563

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product=<productname>

        @Assert: Errata is filtered by product name.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_product_name_and_org_id(self):
        """Filter errata by product name and Org id

        @id: 53f7afa2-285d-4d40-9fdd-5013b3f02462

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product=<product_name> --organization-id=<org_id>

        @Assert: Errata is filtered by product name and Org id.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_product_name_and_org_name(self):
        """Filter errata by product name and Org name

        @id: 8102d688-30d7-4ee5-a1aa-7e041d842a6f

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product=<product_name> --organization=<org_name>

        @Assert: Errata is filtered by product name and Org name.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_product_name_and_org_label(self):
        """Filter errata by product name and Org label

        @id: 64abb151-3f9d-4cad-b4a1-6bf0d73d8a3c

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --product=<product_name>
           --organization-label=<org_label>

        @Assert: Errata is filtered by product name and Org label.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_id(self):
        """Filter errata by Org id

        @id: eeb2b409-89dc-4576-9f89-520cf7152a5a

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-id=<orgid>

        @Assert: Errata is filtered by Org id.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_name(self):
        """Filter errata by Org name

        @id: f2b20bb5-0938-4c7b-af95-d2b3e2b36581

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization=<org name>

        @Assert: Errata is filtered by Org name.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_org_label(self):
        """Filter errata by Org label

        @id: 398123f5-d3ad-4a16-ac5d-e157d6d67595

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --organization-label=<org_label>

        @Assert: Errata is filtered by Org label.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_filter_by_cve(self):
        """Filter errata by CVE

        @id: 7791137c-95a7-4518-a56b-766a5680c5fb

        @Setup: Errata synced on satellite server.

        @Steps:

        1. erratum list --cve <cve_id>

        @Assert: Errata is filtered by CVE.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_user_permission(self):
        """Show errata only if the User has permissions to view them

        @id: f350c13b-8cf9-4aa5-8c3a-1c48397ea514

        @Setup:

        1. Create two products with one repo each. Sync them.
        2. Make sure that they both have errata.
        3. Create a user with view access on one product and not on the other.

        @Steps:

        1. erratum list --organization-id=<orgid>

        @Assert: Check that the new user is able to see errata for one
        product only.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_affected_chosts(self):
        """View a list of affected content hosts for an erratum

        @id: 3b592253-52c0-4165-9a48-ba55287e9ee9

        @Setup: Errata synced on satellite server.

        @Steps:

        1. content-host list --erratum-id=<erratum_id>
           --organization-id=<org_id>

        @Assert: List of affected content hosts for an erratum is displayed.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_list_affected_chosts_by_erratum_restrict_flag(self):
        """View a list of affected content hosts for an erratum filtered
        with restrict flags

        @id: 594acd48-892c-499e-b0cb-6506cea7cd64

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

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_view_available_count_in_affected_chosts(self):
        """Available errata count displayed while viewing a list of
        Content hosts

        @id: 1d174432-bb51-4192-990d-3c62087b96df

        @Setup:

        1. Errata synced on satellite server.
        2. Some content hosts present.

        @Steps:

        1. hammer content-host list --organization-id=<orgid>

        @Assert: The available errata count is retrieved.

        @caseautomation: notautomated

        """
