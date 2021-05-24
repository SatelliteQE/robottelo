"""Tests for RH Cloud - Inventory, also known as Insights Inventory Upload

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Inventory

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.rh_cloud_utils import get_local_file_data
from robottelo.rh_cloud_utils import get_remote_report_checksum


@pytest.mark.tier3
def test_rhcloud_inventory_e2e(session, module_org):
    """Generate report and verify its basic properties

    :id: 833bd61d-d6e7-4575-887a-9e0729d0fa76

    :expectedresults:

        1. Report can be generated
        2. Report can be downloaded
        3. Report has non-zero size
        4. Report can be extracted
        5. JSON files inside report can be parsed
        6. metadata.json lists all and only slice JSON files in tar.
        7. Host counts in metadata matches host counts in slices.
    """
    org = module_org
    with session:
        session.organization.select(org_name=org.name)
        session.cloudinventory.generate_report(org.name)
        report_path = session.cloudinventory.download_report(org.name)
        inventory_data = session.cloudinventory.read(org.name)

@pytest.mark.stubbed
def test_hits_synchronization():
    """Synchronize hits data from cloud and verify it is displayed in Satellite

    :id: c3d1edf5-f43a-4f85-bd80-825bde58f6b2

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. In Satellite UI, Configure -> Insights -> Sync now
        4. Go to Hosts -> All Hosts and assert there is "Insights" column with content
        5. Open host page and assert there is new Insights recommendation tab

    :expectedresults:
        1. There's Insights column with number of recommendations and link to cloud
        2. Recommendations are listed on single host page

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_hosts_synchronization():
    """Synchronize list of available hosts from cloud and mark them in Satellite

    :id: 2f1bdd42-140d-46f8-bad5-299c54620ee8

    :Steps:

        1. Prepare machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. In Satellite UI, Configure -> Inventory upload -> Sync inventory status
        4. Assert content of toast message once synchronization finishes
        5. Go to Hosts -> All Hosts and assert content of status popover
        6. Open host page and assert status on "Properties" tab

    :expectedresults:
        1. Toast message contains number of hosts synchronized and missed
        2. Presence in cloud is displayed in popover status of host
        3. Presence in cloud is displayed in "Properties" tab on single host page

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_obfuscate_host_names():
    """Test whether `Obfuscate host names` setting works as expected.

    :id: 3c3a36b6-6566-446b-b803-3f8f9aab2511

    :Steps:

        1. Prepare machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. Go to Configure > Inventory upload > enable “Obfuscate host names” setting.
        4. Generate report after enabling the setting.
        5. Check if host names are obfuscated in generated reports.
        6. Disable previous setting.
        7. Go to Administer > Settings > RH Cloud and enable "Obfuscate host names" setting.
        8. Generate report after enabling the setting.
        9. Check if host names are obfuscated in generated reports.

    :expectedresults:
        1. Obfuscated host names in reports generated.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_obfuscate_host_ipv4_addresses():
    """Test whether `Obfuscate host ipv4 addresses` setting works as expected.

    :id: c0fc4ee9-a6a1-42c0-83f0-0f131ca9ab41

    :Steps:

        1. Prepare machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. Go to Configure > Inventory upload > enable “Obfuscate host ipv4 addresses” setting.
        4. Generate report after enabling the setting.
        5. Check if hosts ipv4 addresses are obfuscated in generated reports.
        6. Disable previous setting.
        7. Go to Administer > Settings > RH Cloud and enable "Obfuscate IPs" setting.
        8. Generate report after enabling the setting.
        9. Check if hosts ipv4 addresses are obfuscated in generated reports.

    :expectedresults:
        1. Obfuscated host ipv4 addresses in generated reports.

    :BZ: 1852594

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_exclude_packages_setting():
    """Test whether `Exclude Packages` setting works as expected.

    :id: 646093fa-fdd6-4f70-82aa-725e31fa3f12

    :Steps:

        1. Prepare machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. Go to Configure > Inventory upload > enable “Exclude Packages” setting.
        4. Generate report after enabling the setting.
        5. Check if packages are excluded from generated reports.
        6. Disable previous setting.
        7. Go to Administer > Settings > RH Cloud and enable
            "Don't upload installed packages" setting.
        8. Generate report after enabling the setting.
        9. Check if packages are excluded from generated reports.

    :expectedresults:
        1. Packages are excluded from reports generated.

    :BZ: 1852594

    :CaseAutomation: NotAutomated
    """
