"""Test for Virt-who related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.utils.issue_handlers import is_open
from robottelo.utils.virtwho import (
    deploy_configure_by_command,
    get_configure_command,
    get_configure_file,
    get_configure_option,
)


@pytest.fixture
def form_data(target_sat):
    esx = settings.virtwho.esx
    return {
        'debug': 1,
        'interval': '60',
        'hypervisor_id': 'hostname',
        'hypervisor_type': esx.hypervisor_type,
        'hypervisor_server': esx.hypervisor_server,
        'filtering_mode': 'none',
        'satellite_url': target_sat.hostname,
        'hypervisor_username': esx.hypervisor_username,
        'hypervisor_password': esx.hypervisor_password,
        'name': f'preupgrade_virt_who_{gen_string("alpha")}',
    }


ORG_DATA = {'name': f'virtwho_upgrade_{gen_string("alpha")}'}


class TestScenarioPositiveVirtWho:
    """Virt-who config is intact post upgrade and verify the config can be updated and deleted.
    :steps:

        1. In Preupgrade Satellite, create virt-who-config.
        2. Upgrade the satellite to next/latest version.
        3. Postupgrade, Verify the virt-who config is intact, update and delete.

    :expectedresults: Virtwho config should be created, updated and deleted successfully.
    """

    @pytest.mark.pre_upgrade
    def test_pre_create_virt_who_configuration(
        self, form_data, save_test_data, target_sat, module_sca_manifest_org
    ):
        """Create and deploy virt-who configuration.

        :id: preupgrade-a36cbe89-47a2-422f-9881-0f86bea0e24e

        :steps: In Preupgrade Satellite, Create and deploy virt-who configuration.

        :expectedresults:
            1. Config can be created and deployed by command.
            2. No error msg in /var/log/rhsm/rhsm.log.
            3. Report is sent to satellite.
        """
        form_data.update({'organization_id': module_sca_manifest_org.id})
        vhd = target_sat.api.VirtWhoConfig(**form_data).create()
        assert vhd.status == 'unknown'
        command = get_configure_command(vhd.id, org=module_sca_manifest_org.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=module_sca_manifest_org.label
        )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig(organization_id=module_sca_manifest_org.id)
            .search(query={'search': f'name={form_data["name"]}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        save_test_data(
            {
                'hypervisor_name': hypervisor_name,
                'guest_name': guest_name,
                'org_id': module_sca_manifest_org.id,
                'org_name': module_sca_manifest_org.name,
                'org_label': module_sca_manifest_org.label,
                'name': vhd.name,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_create_virt_who_configuration)
    def test_post_crud_virt_who_configuration(self, form_data, pre_upgrade_data, target_sat):
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
        org_id = pre_upgrade_data.get('org_id')
        org_name = pre_upgrade_data.get('org_name')
        org_label = pre_upgrade_data.get('org_label')
        name = pre_upgrade_data.get('name')

        # Post upgrade, Verify virt-who exists and has same status.
        vhd = target_sat.api.VirtWhoConfig(organization_id=org_id).search(
            query={'search': f'name={name}'}
        )[0]
        if not is_open('BZ:1802395'):
            assert vhd.status == 'ok'
        # Verify virt-who status via CLI as we cannot check it via API now
        vhd_cli = target_sat.cli.VirtWhoConfig.exists(search=('name', name))
        assert (
            target_sat.cli.VirtWhoConfig.info({'id': vhd_cli['id']})['general-information'][
                'status'
            ]
            == 'OK'
        )

        # Vefify the connection of the guest on Content host
        hypervisor_name = pre_upgrade_data.get('hypervisor_name')
        guest_name = pre_upgrade_data.get('guest_name')
        hosts = [hypervisor_name, guest_name]
        for hostname in hosts:
            result = (
                target_sat.api.Host(organization=org_id)
                .search(query={'search': hostname})[0]
                .read_json()
            )
            assert result['subscription_status_label'] == 'Simple Content Access'

        # Verify the virt-who config-file exists.
        config_file = get_configure_file(vhd.id)
        get_configure_option('hypervisor_id', config_file)

        # Verify Report is sent to satellite.
        command = get_configure_command(vhd.id, org=org_name)
        deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=org_label
        )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig(organization_id=org_id)
            .search(query={'search': f'name={name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'

        # Update virt-who config
        modify_name = gen_string('alpha')
        vhd.name = modify_name
        vhd.update(['name'])

        # Delete virt-who config
        vhd.delete()
        assert not target_sat.api.VirtWhoConfig(organization_id=org_id).search(
            query={'search': f'name={modify_name}'}
        )
