"""Test for UI CSV EXPORT

:Requirement: UICSVExport

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:CaseAutomation: notautomated

:Upstream: No
"""

from robottelo.decorators import stubbed, tier1
from robottelo.test import UITestCase


class CSVExportHostsTestCase(UITestCase):

    @stubbed()
    @tier1
    def test_positive_single_page(self):
        """
        :id: be5e2b2d-3a93-4803-8c6e-d81a97c5a1a5

        :steps:
            1. Populate host page with <20  items.
            2. Press export CSV button

        :expectedresults: Exported CSV will have all rows
        """

    @stubbed()
    @tier1
    def test_positive_multi_page(self):
        """
        :id: cb615ed3-2f4c-45b5-904e-890ccb587842

        :steps:
            1. Populate page with >20 (or max# per-page) items. For example 30
            2. Press export CSV button

        :expectedresults: Exported CSV will have all rows (30)

        """

    @tier1
    @stubbed()
    def test_positive_organization_filter(self):
        """
        :id: 76756510-eaf1-48be-bd87-8f218c5378cb

        :setup:
            1. Create hosts in orgA and orgB

        :steps:
            1. Open host pages for OrgA
            2. Export Host page to CSV
            3. Open host page for OrgB
            4. Export Host page to CSV


        :expectedresults:
            Only Org A hosts are show in OrgA CSV and
            only orgB hosts are show in orgB csv.
        """

    @tier1
    @stubbed()
    def test_negative_organization_filter(self):
        """
        :id: dee26a14-3e8f-4e12-a3ac-e09205c702cc
        :setup:
            1. Create hosts in orgA and orgB

        :steps:
            1. Set Organizations to "Any"
            2. Export Host page to CSV.

        :expectedresults: All hosts are listed in CSV file.
        """

    @tier1
    @stubbed()
    def test_positive_location_filter(self):
        """
        :id: d526794c-07a2-4db2-a737-01c2827d5cec

        :setup:
            1. Create hosts in locA and locB

        :steps:
            1. Open host pages for locA
            2. Export Host page to CSV
            3. Open host page for locB
            4. Export Host page to CSV


        :expectedresults:
            Only Org A hosts are show in locA CSV
            and only locB hosts are show in locB csv.
        """

    @tier1
    @stubbed()
    def test_negative_location_filter(self):
        """
        :id: 0d6da07f-b5df-49a9-816d-033daa504482
        :setup:
            1. Create hosts in locA and locB

        :steps:
            1. Set Location to "Any"
            2. Export Host page to CSV.

        :expectedresults: All hosts are listed in CSV file.
        """

    @tier1
    @stubbed()
    def test_combo_filter(self):
        """
        :id: 46b61542-994a-48ca-b4b0-90c886158614

        :setup:
            1. Chose some host filter (filterA)
            2. Create multiple hosts, such that some match
               filterA and some dont

        :steps:
            1. Filter the host page with filterA
            2. Export the host page to CSV

        :expectedresults: CSV only contains filtered hosts
        """

    @tier1
    @stubbed()
    def test_positive_filter_multi_page(self):
        """
        :id: c506d83f-de27-43cd-840c-dae57b889a8f

        :setup:
            1. Chose some host filter (filterA)
            2. Create greater then per page max of hosts, such that
               some match filterA and some dont
        :steps:
            1. Filter the host page with filterA
            2. Export the host page to CSV

        :expectedresults: CSV only contains filtered hosts from all pages
        """

    @tier1
    @stubbed()
    def test_positive_filter_single_page(self):
        """

        :id: 67f0bf54-0db9-45f4-899b-081ed1c83e70

        :setup:
            1. Chose some host filter (filterA)
            2. Create less then per page max of hosts, such that
               some match filterA and some dont
        :steps:
            1. Filter the host page with filterA
            2. Export the host page to CSV

        :expectedresults: CSV contains filtered hosts from page.
        """


class UICSVExportHostsColumnsTestCase(UITestCase):

    @tier1
    @stubbed()
    def test_positive_column_contents(self):
        """
        :id: 2f86176d-f90a-4589-ab52-a56fbd5fc713

        :setup:
            Populate hosts multiple hosts with a mix of Puppet Enviromets,
            Hostgroups, OS, etc

        :steps:
            1. Export the CSV Page in the UI

        :expectedresults:
            Exported CSV will contain text representations of all columns.


        """

    @tier1
    @stubbed()
    def test_positive_name(self):
        """
        :id: b3a189c4-3f08-41e0-a1d3-e8f1a0b1f60c

        :setup:
            Create multiple host with all variations of hostname
        :steps:
            1. Export the CSV page in the UI.

        :expectedresults: Exported CSV contains the correct text for Hostname
        """

    @tier1
    @stubbed()
    def test_positive_os(self):
        """
        :id: cb9ac24e-9a25-4641-ace3-370c74ecf91f
        :setup:
            Create multiple host with multiple variations of OS
        :steps:
            1. Export the CSV page in the UI.

        :expectedresults: Exported CSV will contain the correct text for OS
        """

    @tier1
    @stubbed()
    def test_positive_enviroment(self):
        """
        :id: 099f253a-ec8f-4544-bb28-988c9ab03d5d
        :setup:
            Create multiple host with multiple variations of Enviroment
        :steps:
            1. Export the CSV page in the UI.

        :expectedresults: Exported CSV contains the correct text for Enviroment
        """

    @tier1
    @stubbed()
    def test_negative_enviroment(self):
        """
        :id: d25760e6-4111-4f84-9447-db548ccb43f4

        :setup:
            Create  host with no enviroment
        :steps:
            1. Export the CSV page in the UI.

        :expectedresults: Exported CSV Enviroment coloumn will be empty.
        """

    @tier1
    @stubbed()
    def test_positive_model_baremetal(self):
        """
        :id: 517095bc-8903-431e-9100-970b06be35ea

        :setup:
            Create  baremetal host
        :steps:
            1. Export the CSV page in the UI.

        :expectedresults: Hardware model info is included in the CSV file
        """

    @tier1
    @stubbed()
    def test_positive_compute_resource(self):
        """
        :id: 81fdde68-cd63-4793-9a44-f26b5098fbd9

        :setup:
            Create Compute resource host

        :steps:
            1. Export Hosts page to CSV

        :expectedresults:
            Compute resource name is in the model column in the exported CSV
        """

    @tier1
    @stubbed()
    def test_positive_last_report(self):
        """
        :id: ae283c17-75b8-4933-acbe-af5a6fa5b145

        :setup:
            Cause host to send report so last report time is populated
        :steps:
            1. Export Host CSV page in the UI

        :expectedresults:
            Last reported time is in the correct format in the CSV.

        """

    @tier1
    @stubbed()
    def test_negative_last_report(self):
        """
        :id: c4293168-8217-447f-add2-e5ab495f9acd

        :setup:
            Populate host page with entries with no last report time
        :steps:
            1. Export CSV page in the UI

        :expectedresults:
            Last reported time is in the correct format in the CSV.
        """


class UICSVExportFactsTestCase(UITestCase):

    @tier1
    @stubbed()
    def test_positive_single_page(self):
        """
        :id: 87229ff1-f80a-43a3-ad66-eab16eb7786d

        :steps:
            1. Populate facts page with <20  items.
            2. Press export CSV button

        :expectedresults: Exported CSV will have all rows
        """

    @tier1
    @stubbed()
    def test_positive_multipage(self):
        """
        :id: 178bc116-961b-47e2-8b39-3d0a13cfb96e

        :setup:
            1. Populate page with >20 (or max# per-page) items. For example 30

        :steps:

            2. Press export CSV button

        :expectedresults: Exported CSV will have all rows (30)

        """

    @tier1
    @stubbed()
    def test_positive_organization_filter(self):
        """
        :id: 36292666-229a-468c-9ef8-d3d9ce138dcf

        :setup:
            1. Create hosts in orgA and orgB

        :steps:
            1. Open Facts pages for OrgA
            2. Export Facts page to CSV
            3. Open Facts page for OrgB
            4. Export Facts page to CSV


        :expectedresults:
            Only Org A hosts are show in OrgA CSV and only orgB hosts
            are show in orgB csv.
        """

    @tier1
    @stubbed()
    def test_negative_organization_filter(self):
        """
        :id: cbdd8eb3-2b90-48ea-8548-3c07b36eb93f

        :setup:
            1. Create hosts in orgA and orgB

        :steps:
            1. Set Organizations to "Any"
            2. Export Host Facts page to CSV.

        :expectedresults: All hosts are listed in CSV file.
        """

    @tier1
    @stubbed()
    def test_positive_location_filter(self):
        """
        :id: 3bae203c-0343-43fc-873e-a187d6ba023a

        :setup:
            1. Create hosts in locA and locB

        :steps:
            1. Open facts pages for locA
            2. Export facts page to CSV
            3. Open facts page for locB
            4. Export facts page to CSV


        :expectedresults:
            Only Org A facts are show in locA CSV and
            only locB facts are show in locB csv.
        """

    @tier1
    @stubbed()
    def test_negative_location_filter(self):
        """
        :id: 8971a782-6995-4e8a-bfbd-3b0ecd7dc484

        :setup:
            1. Create hosts in locA and locB

        :steps:
            1. Set Location to "Any"
            2. Export facts page to CSV.

        :expectedresults: All facts are listed in CSV file.
        """

    @tier1
    @stubbed()
    def test_positive_combo_filter(self):
        """

        :id: 001ff58d-4405-45b5-8c6a-cbbb035852f0

        :setup:
            1. Chose some facts filter (filterA)
            2. Create multiple hosts with facts, such that
               some match filterA and some dont

        :steps:
            1. Filter the facts page with filterA
            2. Export the facts page to CSV

        :expectedresults: CSV only contains filtered facts
        """

    @tier1
    @stubbed()
    def test_negitive_combo_filter(self):
        """ Test filter which results in empty list.

        :id: 5f265a5c-6d0a-45d3-a7ef-6397ad513053

        :setup:
            1. Chose some facts filter (filterA)
            2. Create multiple hosts with facts, such that NO hosts are matched
               by filterA

        :steps:
            1. Filter the facts page with filterA
            2. Export the facts page to CSV

        :expectedresults: CSV Contains only the header row, and nothing else
        """

    @tier1
    @stubbed()
    def test_positive_filter_multi_page(self):
        """
        :id: c83ae156-6582-4b54-a6d5-f6e83f921b91

        :setup:
            1. Chose some host filter (filterA)
            2. Create greater then per page max of hosts, such that some match
               filterA and some dont

        :steps:
            1. Filter the host page with filterA
            2. Export the host page to CSV

        :expectedresults: CSV only contains filtered hosts from all pages
        """

    @tier1
    @stubbed()
    def test_positive_filter_single_page(self):
        """

        :id: 9d0e9f54-5c65-4ba7-b786-31196dbe549f

        :setup:
            1. Chose some facts filter (filterA)
            2. Create less then per page max of facts, such that some match
               filterA and some dont

        :steps:
            1. Filter the facts page with filterA
            2. Export the facts page to CSV

        :expectedresults: CSV contains filtered facts from page.
        """


class UICSVExportFactsColumnsTestCase(UITestCase):

    def setUp(self):
        pass

    @tier1
    @stubbed()
    def test_positive_host(self):
        """
        :id: 01db2369-afe8-4390-9877-715c2b0e775d

        :setup:
            Populate system facts with variations of hostnames

        :steps:
            1. Export Facts page

        :expectedresults: Hostname column has all correct values.

        """

    @tier1
    @stubbed()
    def test_positive_name(self):
        """
        :id: ce8bca9d-228d-478e-840d-76d31801dd01

        :setup:
            Populate system facts with all variations of fact names

        :steps:
            1. Export Facts page

        :expectedresults: Facts name column has all correct values.
        """

    @tier1
    @stubbed()
    def test_positive_value(self):
        """
        :id: 591a9da2-2c2e-488e-8e13-487053bbf730

        :setup:
            Populate system facts with multiple variations of fact values

        :steps:
            1. Export Facts page

        :expectedresults: Facts value column has all correct values.
        """

    @tier1
    @stubbed()
    def test_positive_origin(self):
        """
        :id: 3637aa16-5eb4-44b8-94b2-7546d8c78161

        :steps:
            1. populate facts from multiple orgins (Puppet, etc)
            2. Export facts page

        :expectedresults: Orgin column is correct for all rows.
        """

    @tier1
    @stubbed()
    def test_positive_reported(self):
        """
        :id: 4367aaa9-4b30-458b-8573-e5dc285b18fb

        :steps:
            1. Populate facts at multiple times
            2. export facts page


        :expectedresults: Reported time is correct for all values
        """

    @tier1
    @stubbed()
    def test_postive_nested_value(self):
        """
        :id: 558eb900-c39e-4f8a-a816-4b935ca4aa17

        :steps:
            1. reproduce:
               https://bugzilla.redhat.com/show_bug.cgi?id=1477341

        :expectedresults:
            What ever the decision from the BZ is.

        """


class UICSVExportFactsNestedTestCase(UITestCase):

    @tier1
    @stubbed()
    def test_positive_nested_facts(self):
        """
        :id: 7732f49c-8d29-4548-a20c-5955cdfa2a14

        :steps:
            1. Recurse down a nested fact (ex DMI)
            2. Export CSV for each level

        :expectedresults: Values are in CSV at each level.
        """


class CSVExportConfigMgmtReportsTestCase(UITestCase):

    @stubbed()
    @tier1
    def test_positive_single_page(self):
        """
        :id: 9006c4fa-1e46-4f9f-bb22-5b5fb96ba94b

        :steps:
            1. Populate page with <20 (or max# per-page) items. ie 15
            2. Press export CSV button

        :expectedresults: Exported CSV will have all rows (15)

        """
    @stubbed()
    @tier1
    def test_positive_multi_page(self):
        """
        :id: ce093a5f-3538-452c-9397-c50479433bbd

        :steps:
            1. Populate page with >20 (or max# per-page) items. For example 30
            2. Press export CSV button

        :expectedresults: Exported CSV will have all rows (30)

        """

    @tier1
    @stubbed()
    def test_positive_organization_filter(self):
        """
        :id: ce83dace-5349-4627-b9d4-e116df46a986

        :setup:
            1. Create hosts in orgA and orgB

        :steps:
            1. Open host pages for OrgA
            2. Export Host page to CSV
            3. Open host page for OrgB
            4. Export Host page to CSV


        :expectedresults:
            Only Org A hosts are show in OrgA CSV and only orgB hosts are
            show in orgB csv.
        """

    @tier1
    @stubbed()
    def test_negative_organization_filter(self):
        """
        :id: 79f50ca9-61fe-4e0c-a098-bf5c0bfb4b9c

        :setup:
            1. Create hosts in orgA and orgB

        :steps:
            1. Set Organizations to "Any"
            2. Export Host page to CSV.

        :expectedresults: All hosts are listed in CSV file.
        """

    @tier1
    @stubbed()
    def test_positive_location_filter(self):
        """
        :id: d61aec9a-4e9d-4705-9bdd-abe9acdbe465

        :setup:
            1. Create hosts in locA and locB

        :steps:
            1. Open host pages for locA
            2. Export Host page to CSV
            3. Open host page for locB
            4. Export Host page to CSV


        :expectedresults:
            Only Org A hosts are show in locA CSV and
            only locB hosts are show in locB csv.
        """

    @tier1
    @stubbed()
    def test_negative_location_filter(self):
        """
        :id: feb300bd-c256-4564-8604-cba2ba0b34d6

        :setup:
            1. Create hosts in locA and locB

        :steps:
            1. Set Location to "Any"
            2. Export Host page to CSV.

        :expectedresults: All hosts are listed in CSV file.
        """

    @tier1
    @stubbed()
    def test_combo_filter(self):
        """
        :id: 18be8590-99a0-4e5e-a35b-5dce0197bb5e

        :setup:
            1. Chose some host filter (filterA)
            2. Create multiple hosts, such that some match filterA and
               some dont

        :steps:
            1. Filter the host page with filterA
            2. Export the host page to CSV

        :expectedresults: CSV only contains filtered hosts
        """

    @tier1
    @stubbed()
    def test_positive_filter_multi_page(self):
        """

        :id: 815a3caf-5d7b-4ff2-91d0-6bcbc47b7e67

        :setup:
            1. Chose some host filter (filterA)
            2. Create greater then per page max of hosts, such that some
               match filterA and some dont
        :steps:
            1. Filter the host page with filterA
            2. Export the host page to CSV

        :expectedresults: CSV only contains filtered hosts from all pages
        """

    @tier1
    @stubbed()
    def test_positive_filter_single_page(self):
        """

        :id: 50ad42ac-cfcd-4ae1-9836-a974512b57bf

        :setup:
            1. Chose some host filter (filterA)
            2. Create less then per page max of hosts, such that some match
               filterA and some dont
        :steps:
            1. Filter the host page with filterA
            2. Export the host page to CSV

        :expectedresults: CSV contains filtered hosts from page.
        """


class CSVExportConfigMgmtColumnsTestCase(UITestCase):
    @tier1
    @stubbed()
    def test_positive_column_values(self):
        """

        :id: e01e604c-40dc-48b1-9f4c-e045aa7936a3

        :setup:
            Cause a number of Configuration Managment reports to be generated
            of each type (Host,Reported At,Applied,Restarted,
            Failed,Failed Restarts,Skipped,Pending)

        :steps:
            1. Export the Reports page to CSV

        :expectedresults: The column values are correct.
        """
