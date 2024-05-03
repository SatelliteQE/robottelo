"""Tests for BootdiskPlugin

:Requirement: Bootdisk

:CaseAutomation: Automated

:CaseComponent: BootdiskPlugin

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_mac, gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import HTTPS_MEDIUM_URL


@pytest.mark.rhel_ver_match('[^6]')
def test_positive_bootdisk_download_https(
    request,
    module_location,
    module_sync_kickstart_content,
    module_provisioning_capsule,
    module_target_sat,
    module_sca_manifest_org,
    module_default_org_view,
    module_lce_library,
    default_architecture,
    default_partitiontable,
):
    """Verify bootdisk is able to download using https url media .

    :id: ebced3cf-99e8-4ed6-a41d-d53789e90f8e

    :steps:
        1. Create a host with https url media
        2. Download the full host bootdisk
        3. Check if bootdisk is downloaded properly

    :expectedresults: Full host bootdisk is downloaded properly

    :BZ: 2173199

    :customerscenario: true

    :parametrized: yes
    """

    macaddress = gen_mac(multicast=False)
    capsule = module_target_sat.nailgun_smart_proxy
    # create medium with https url
    media = module_target_sat.cli_factory.make_medium(
        {
            'name': gen_string('alpha'),
            'operatingsystem-ids': module_sync_kickstart_content.os.id,
            'location-ids': module_provisioning_capsule.id,
            'organization-ids': module_sca_manifest_org.id,
            'path': HTTPS_MEDIUM_URL,
            'os-family': 'Redhat',
        }
    )
    host = module_target_sat.cli_factory.make_host(
        {
            'organization-id': module_sca_manifest_org.id,
            'location-id': module_location.id,
            'name': gen_string('alpha').lower(),
            'mac': macaddress,
            'operatingsystem-id': module_sync_kickstart_content.os.id,
            'medium-id': media['id'],
            'architecture-id': default_architecture.id,
            'domain-id': module_sync_kickstart_content.domain.id,
            'build': 'true',
            'root-password': settings.provisioning.host_root_password,
            'partition-table-id': default_partitiontable.id,
            'content-source-id': capsule.id,
            'content-view-id': module_default_org_view.id,
            'lifecycle-environment-id': module_lce_library.id,
        }
    )

    @request.addfinalizer
    def _finalize():
        module_target_sat.api.Host(id=host.id).delete()
        module_target_sat.api.Media(id=media['id']).delete()

    # Check if full-host bootdisk can be downloaded.
    bootdisk = module_target_sat.cli.Bootdisk.host({'host-id': host['id'], 'full': 'true'})
    assert 'Successfully downloaded host disk image' in bootdisk['message']
