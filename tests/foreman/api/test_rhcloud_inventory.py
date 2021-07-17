"""API tests for RH Cloud - Inventory, also known as Insights Inventory Upload

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


def test_rhcloud_inventory_api_e2e():
    """Generate report using rh_cloud plugin api's and verify its basic properties.

    :id: 8ead1ff6-a8f5-461b-9dd3-f50d96d6ed57

    :expectedresults:

        1. Report can be generated
        2. Report can be downloaded
        3. Report has non-zero size
        4. Report can be extracted
        5. JSON files inside report can be parsed
        6. metadata.json lists all and only slice JSON files in tar
        7. Host counts in metadata matches host counts in slices
        8. Assert Hostnames, IP addresses, and installed packages are present in report.

    :BZ: 1807829, 1926100
    """


@pytest.mark.stubbed
def test_rhcloud_inventory_api_hosts_synchronization():
    """Test RH Cloud plugin api to synchronize list of available hosts
    from cloud and mark them in Satellite.

    :id: 7be22e1c-906b-4ae5-93dd-5f79f395601c

    :Steps:

        1. Prepare machine and upload its data to Insights.
        2. Add Cloud API key in Satellite
        3. Sync inventory status using RH Cloud plugin api.
        4. Assert content of response message once synchronization finishes.
        5. Get host details.
        6. Assert inventory status for the host.

    :expectedresults:
        1. Response of RH Cloud plugins api for syncing inventory status
        should contain number of hosts synchronized and missed.
        2. Presence in cloud is displayed in host properties.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_rhcloud_inventory_bz_1893439():
    """Verify that the hosts having mtu field value as string in foreman's Nic object
    is present in the inventory report.

    :id: df6d5f4f-5ee1-4f34-bf24-b93fbd089322

    :customerscenario: true

    :Steps:
        1. Register a content host.
        2. If value of mtu field is not a string then use foreman-rake to change it.
        3. Generate inventory report.
        4. Assert that host is listed in the inventory report.
        5. Assert that value of mtu field in generated report is a number.

    :expectedresults:
        1. Host having string mtu field value is present in the inventory report.
        2. Value of mtu field in generated inventory report is a number.

    :BZ: 1893439

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_rhcloud_inventory_bz_1845113():
    """Verify that system_purpose_sla field is present in the inventory report
    for the host subscribed using Activation key with service level set in it.

    :id: 3974338c-3a66-41ac-af32-ee76e3c37aef

    :customerscenario: true

    :Steps:
        1. Create an activation key with service level set in it.
        2. Register a content host using the created activation key.
        3. Generate inventory report.
        4. Assert that host is listed in the inventory report.
        5. Assert that system_purpose_sla field is present in the inventory report.

    :expectedresults:
        1. Host is present in the inventory report.
        2. system_purpose_sla field is present in the inventory report.

    :BZ: 1845113

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_rhcloud_inventory_auto_upload_setting():
    """Verify that Automatic inventory upload setting works as expected.

    :id: 0475aaaf-c228-45af-b80c-21d459f62ecb

    :customerscenario: true

    :Steps:
        1. Register a content host with satellite.
        2. Enable "Automatic inventory upload" setting.
        3. Verify that satellite automatically generate and upload
        inventory report once a day.
        4. Disable "Automatic inventory upload" setting.
        5. Verify that satellite is not automatically generating and uploading
        inventory report.

    :expectedresults:
        1. If "Automatic inventory upload" setting is enabled then satellite
        automatically generate and upload inventory report.
        2. If "Automatic inventory upload" setting is disable then satellite
        does not generate and upload inventory report automatically.

    :BZ: 1793017

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_rhcloud_inventory_bz_1936906():
    """Verify that inventory report generate and upload process finish
    successfully when satellite is using http proxy listening on port 80.

    :id: 310a0c91-e313-474d-a5c6-64e85cea4e12

    :customerscenario: true

    :Steps:
        1. Create a http proxy which is using port 80.
        2. Register a content host with satellite.
        3. Set Default HTTP Proxy setting.
        4. Generate and upload inventory report.
        5. Assert that host is listed in the inventory report.
        6. Assert that upload process finished successfully.

    :expectedresults:
        1. Inventory report generate and upload process finished successfully.
        2. Host is present in the inventory report.

    :BZ: 1936906

    :CaseAutomation: NotAutomated
    """
