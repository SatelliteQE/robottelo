"""Test for Virt-who related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
from manifester import Manifester
import pytest

from robottelo.config import settings
from robottelo.utils.shared_resource import SharedResource
from robottelo.utils.virtwho import (
    deploy_configure_by_command,
    deploy_validation,
    get_configure_command,
    get_configure_file,
    get_guest_info,
    get_configure_option,
    runcmd,
    VirtWhoError
)


@pytest.fixture
def form_data(virt_who_upgrade_shared_satellite):
    esx = settings.virtwho.esx
    return {
        'debug': 1,
        'interval': '60',
        'hypervisor_id': 'hostname',
        'hypervisor_type': esx.hypervisor_type,
        'hypervisor_server': esx.hypervisor_server,
        'filtering_mode': 'none',
        'satellite_url': virt_who_upgrade_shared_satellite.hostname,
        'hypervisor_username': esx.hypervisor_username,
        'hypervisor_password': esx.hypervisor_password,
        'name': f'preupgrade_virt_who_{gen_alpha()}',
    }


@pytest.fixture
def virt_who_upgrade_manifest():
    with Manifester(manifest_category=settings.manifest.golden_ticket) as manifest:
        yield manifest


ORG_DATA = {'name': f'virtwho_upgrade_{gen_alpha()}'}


# class TestScenarioPositiveVirtWho:
"""Virt-who config is intact post upgrade and verify the config can be updated and deleted.
:steps:

    1. In Preupgrade Satellite, create virt-who-config.
    2. Upgrade the satellite to next/latest version.
    3. Postupgrade, Verify the virt-who config is intact, update and delete.

:expectedresults: Virtwho config should be created, updated and deleted successfully.
"""

@pytest.fixture
def create_virt_who_configuration_setup(
    virt_who_upgrade_shared_satellite, form_data, virt_who_upgrade_manifest, upgrade_action,
):
    """Create and deploy virt-who configuration.

    :id: preupgrade-a36cbe89-47a2-422f-9881-0f86bea0e24e

    :steps: In Preupgrade Satellite, Create and deploy virt-who configuration.

    :expectedresults:
        1. Config can be created and deployed by command.
        2. No error msg in /var/log/rhsm/rhsm.log.
        3. Report is sent to satellite.
    """
    target_sat = virt_who_upgrade_shared_satellite
    manifest = virt_who_upgrade_manifest
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'virt_who_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        library_id = int(
            target_sat.cli.LifecycleEnvironment.list(
                {'organization-id': org.id, 'library': 'true'}
            )[0]['id']
        )
        lce = target_sat.api.LifecycleEnvironment(
            name=f'{test_name}_lce', organization=org, prior=library_id
        ).create()
        content_view = target_sat.publish_content_view(org, [], f'{test_name}_cv')
        ak = target_sat.api.ActivationKey(
            name=f'{test_name}_ak', organization=org.id, environment=lce, content_view=content_view
        ).create()
        test_data = Box(
            {
                'hypervisor_name': None,
                'guest_name': None,
                'org': org,
                'vhd': None,
                
            }
        )
        target_sat.upload_manifest(org.id, manifest.content)
        form_data.update({'organization_id': org.id})
        vhd = target_sat.api.VirtWhoConfig(**form_data).create()
        test_data.vhd = vhd
        assert vhd.status == 'unknown'
        command = get_configure_command(vhd.id, org=org.name)
        result = rhel_contenthost.api_register(
            target_sat, organization=org, activation_keys=[ak.name], location=location,
        )
        assert f'The registered system name is: {rhel_contenthost.hostname}' in result.stdout
        register host
        ret, stdout = runcmd(command, system=target_sat.hostname)
        if ret != 0 or 'Finished successfully' not in stdout:
            raise VirtWhoError(f'Failed to deploy configure by {command}')
        hypervisor_name, guest_name = deploy_validation('esx')
        # hypervisor_name, guest_name = deploy_configure_by_command(
        #     command, form_data['hypervisor_type'], debug=True, org=org.label
        # )
        test_data.hypervisor_name = hypervisor_name
        test_data.guest_name = guest_name
        virt_who_instance = (
            target_sat.api.VirtWhoConfig(organization_id=org.id)
            .search(query={'search': f'name={form_data["name"]}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        sat_upgrade.ready()
        yield test_data


@pytest.mark.virt_who_upgrades
def test_post_crud_virt_who_configuration(create_virt_who_configuration_setup, form_data):
    """Virt-who config is intact post upgrade and verify the config can be updated and deleted.

    :id: postupgrade-d7ae7b2b-3291-48c8-b412-cb54e444c7a4

    :steps:
        1. Post upgrade, Verify virt-who exists and has same status.
        2. Verify the connection of the guest on Content host.
        3. Verify the virt-who config-file exists.
        4. Verify Report is sent to satellite.
        5. Update virt-who config with new name.
        6. Delete virt-who config.

    :expectedresults:
        1. virt-who config is intact post upgrade.
        2. the config and guest connection have the same status.
        3. Report is sent to satellite.
        4. virt-who config should update and delete successfully.
    """
    target_sat = create_virt_who_configuration_setup.satellite
    org = create_virt_who_configuration_setup.org
    vhd = create_virt_who_configuration_setup.vhd

    # Post upgrade, Verify virt-who exists and has same status.
    assert vhd.status == 'ok'
    # Verify virt-who status via CLI as we cannot check it via API now
    vhd_cli = target_sat.cli.VirtWhoConfig.exists(search=('name', vhd.name))
    assert (
        target_sat.cli.VirtWhoConfig.info({'id': vhd_cli['id']})['general-information'][
            'status'
        ]
        == 'OK'
    )

    # Vefify the connection of the guest on Content host
    hypervisor_name = create_virt_who_configuration_setup.hypervisor_name
    guest_name = create_virt_who_configuration_setup.guest_name
    result = (
        target_sat.api.Host(organization=org.id)
        .search(query={'search': hypervisor_name})[0]
        .read_json()
    )
    assert result['subscription_facet_attributes']['virtual_guests'][0]['name'] == guest_name
    result = (
        target_sat.api.Host(organization=org.id)
        .search(query={'search': guest_name})[0]
        .read_json()
    )
    assert hypervisor_name in result['subscription_facet_attributes']['virtual_host']['name']

    # Verify the virt-who config-file exists.
    config_file = get_configure_file(vhd.id)
    get_configure_option('hypervisor_id', config_file)

    # Verify Report is sent to satellite.
    command = get_configure_command(vhd.id, org=org.name)
    deploy_configure_by_command(
        command, form_data['hypervisor_type'], debug=True, org=org.label
    )
    virt_who_instance = (
        target_sat.api.VirtWhoConfig(organization_id=org.id)
        .search(query={'search': f'name={vhd.name}'})[0]
        .status
    )
    assert virt_who_instance == 'ok'

    # Update virt-who config
    modify_name = gen_string('alpha')
    vhd.name = modify_name
    vhd.update(['name'])

    # Delete virt-who config
    vhd.delete()
    assert not target_sat.api.VirtWhoConfig(organization_id=org.id).search(
        query={'search': f'name={modify_name}'}
    )
