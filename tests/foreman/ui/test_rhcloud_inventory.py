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
import hashlib
import json
import os
import tarfile

import pytest
from nailgun import entities

from robottelo import manifests
from robottelo import ssh
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.vm import VirtualMachine


def get_host_counts(tarobj):
    metadata_counts = {}
    slices_counts = {}
    for file_ in tarobj.getmembers():
        file_name = os.path.basename(file_.name)
        if not file_name.endswith(".json"):
            continue
        json_data = json.load(tarobj.extractfile(file_))
        if file_name == "metadata.json":
            metadata_counts = {
                f"{key}.json": value['number_hosts']
                for key, value in json_data['report_slices'].items()
            }
        else:
            slices_counts[file_name] = len(json_data['hosts'])

    return {
        "metadata_counts": metadata_counts,
        "slices_counts": slices_counts,
    }


def get_local_file_data(path):
    size = os.path.getsize(path)

    with open(path, 'rb') as fh:
        file_content = fh.read()
    checksum = hashlib.sha256(file_content).hexdigest()

    try:
        tarobj = tarfile.open(path, mode='r')
        host_counts = get_host_counts(tarobj)
        tarobj.close()
        extractable = True
        json_files_parsable = True
    except (tarfile.TarError, json.JSONDecodeError):
        host_counts = {}
        extractable = False
        json_files_parsable = False

    return {
        "size": size,
        "checksum": checksum,
        "extractable": extractable,
        "json_files_parsable": json_files_parsable,
        **host_counts,
    }


def get_remote_report_checksum(org_id):
    remote_paths = [
        f"/var/lib/foreman/red_hat_inventory/uploads/done/report_for_{org_id}.tar.gz",
        f"/var/lib/foreman/red_hat_inventory/uploads/report_for_{org_id}.tar.gz",
    ]

    for path in remote_paths:
        result = ssh.command(f"sha256sum {path}", output_format='plain')
        if result.return_code != 0:
            continue
        checksum, _ = result.stdout.split(maxsplit=1)
        return checksum
    return ""


@pytest.fixture(scope="module")
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope="module")
def organization_ak_setup(module_org):
    with manifests.clone() as manifest:
        upload_manifest(module_org.id, manifest.content)
    ak = entities.ActivationKey(
        content_view=module_org.default_content_view,
        organization=module_org,
        environment=entities.LifecycleEnvironment(id=module_org.library.id),
        auto_attach=True,
    ).create()
    subscription = entities.Subscription(organization=module_org).search(
        query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    ak.add_subscriptions(data={"quantity": 10, "subscription_id": subscription.id})
    return module_org, ak


@pytest.mark.libvirt_content_host
@pytest.fixture(scope="module")
def virtual_host():
    with VirtualMachine(distro=DISTRO_RHEL7) as vm:
        yield vm


@pytest.mark.libvirt_content_host
@pytest.fixture(scope="module")
def baremetal_host():
    with VirtualMachine(distro=DISTRO_RHEL7) as vm:
        vm.set_infrastructure_type("physical")
        yield vm


@pytest.fixture(scope="module")
def registered_hosts(organization_ak_setup, virtual_host, baremetal_host):
    org, ak = organization_ak_setup
    for vm in (virtual_host, baremetal_host):
        vm.install_katello_ca()
        vm.register_contenthost(org.label, ak.name)
        assert vm.subscribed
    return virtual_host, baremetal_host


@pytest.mark.tier3
def test_rhcloud_inventory_e2e(organization_ak_setup, registered_hosts, session):
    """Generate report and verify its basic properties

    :id: 833bd61d-d6e7-4575-887a-9e0729d0fa76

    :expectedresults:

        1. Report can be generated
        2. Report can be downloaded
        3. Report has non-zero size
        4. Report can be extracted
        5. JSON files inside report can be parsed
        6. metadata.json lists all and only slice JSON files in tar
        7. Host counts in metadata matches host counts in slices
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = registered_hosts
    with session:
        session.organization.select(org_name=org.name)
        session.cloudinventory.generate_report(org.name)
        report_path = session.cloudinventory.download_report(org.name)
        inventory_data = session.cloudinventory.read(org.name)

    local_file_data = get_local_file_data(report_path)
    upload_success_msg = (
        f"Done: /var/lib/foreman/red_hat_inventory/uploads/report_for_{org.id}.tar.gz"
    )
    upload_error_messages = ["NSS error", "Permission denied"]

    assert "Successfully generated" in inventory_data['generating']['terminal']
    assert upload_success_msg in inventory_data['uploading']['terminal']
    assert "x-rh-insights-request-id" in inventory_data['uploading']['terminal'].lower()
    for error_msg in upload_error_messages:
        assert error_msg not in inventory_data['uploading']['terminal']

    assert local_file_data['checksum'] == get_remote_report_checksum(org.id)
    assert local_file_data['size'] > 0
    assert local_file_data['extractable']
    assert local_file_data['json_files_parsable']

    slices_in_metadata = set(local_file_data['metadata_counts'].keys())
    slices_in_tar = set(local_file_data['slices_counts'].keys())
    assert slices_in_metadata == slices_in_tar
    for slice_name, hosts_count in local_file_data['metadata_counts'].items():
        assert hosts_count == local_file_data['slices_counts'][slice_name]


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
