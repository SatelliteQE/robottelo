"""Test for Virt-who related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.host import Host
from robottelo.cli.subscription import Subscription
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC
from robottelo.utils.issue_handlers import is_open
from robottelo.utils.virtwho import deploy_configure_by_command
from robottelo.utils.virtwho import get_configure_command
from robottelo.utils.virtwho import get_configure_file
from robottelo.utils.virtwho import get_configure_option


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
        'name': 'preupgrade_virt_who',
    }


ORG_DATA = {'name': 'virtwho_upgrade_org_name'}


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
        self, form_data, save_test_data, target_sat, function_entitlement_manifest
    ):
        """Create and deploy virt-who configuration.

        :id: preupgrade-a36cbe89-47a2-422f-9881-0f86bea0e24e

        :steps: In Preupgrade Satellite, Create and deploy virt-who configuration.

        :expectedresults:
            1. Config can be created and deployed by command.
            2. No error msg in /var/log/rhsm/rhsm.log.
            3. Report is sent to satellite.
            4. Virtual sku can be generated and attached.
        """
        default_loc_id = (
            target_sat.api.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0].id
        )
        default_loc = target_sat.api.Location(id=default_loc_id).read()
        org = target_sat.api.Organization(name=ORG_DATA['name']).create()
        default_loc.organization.append(target_sat.api.Organization(id=org.id))
        default_loc.update(['organization'])
        org.sca_disable()
        target_sat.upload_manifest(org.id, function_entitlement_manifest.content)
        form_data.update({'organization_id': org.id})
        vhd = target_sat.api.VirtWhoConfig(**form_data).create()
        assert vhd.status == 'unknown'
        command = get_configure_command(vhd.id, org=org.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=org.label
        )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig(organization_id=org.id)
            .search(query={'search': f'name={form_data["name"]}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (hypervisor_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'),
        ]
        for hostname, sku in hosts:
            host = Host.list({'search': hostname})[0]
            subscriptions = Subscription.list({'organization-id': org.id, 'search': sku})
            vdc_id = subscriptions[0]['id']
            if 'type=STACK_DERIVED' in sku:
                for item in subscriptions:
                    if hypervisor_name.lower() in item['type']:
                        vdc_id = item['id']
                        break
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = (
                target_sat.api.Host(organization=org.id)
                .search(query={'search': hostname})[0]
                .read_json()
            )
            assert result['subscription_status_label'] == 'Fully entitled'

        save_test_data(
            {
                'hypervisor_name': hypervisor_name,
                'guest_name': guest_name,
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
            4. Update virt-who config with new name.
            5. Delete virt-who config.

        :expectedresults:
            1. virt-who config is intact post upgrade.
            2. the config and guest connection have the same status.
            3. virt-who config should update and delete successfully.
        """
        org = target_sat.api.Organization().search(query={'search': f'name={ORG_DATA["name"]}'})[0]

        # Post upgrade, Verify virt-who exists and has same status.
        vhd = target_sat.api.VirtWhoConfig(organization_id=org.id).search(
            query={'search': f'name={form_data["name"]}'}
        )[0]
        if not is_open('BZ:1802395'):
            assert vhd.status == 'ok'
        # Verify virt-who status via CLI as we cannot check it via API now
        vhd_cli = VirtWhoConfig.exists(search=('name', form_data['name']))
        assert VirtWhoConfig.info({'id': vhd_cli['id']})['general-information']['status'] == 'OK'

        # Vefify the connection of the guest on Content host
        hypervisor_name = pre_upgrade_data.get('hypervisor_name')
        guest_name = pre_upgrade_data.get('guest_name')
        hosts = [hypervisor_name, guest_name]
        for hostname in hosts:
            result = (
                target_sat.api.Host(organization=org.id)
                .search(query={'search': hostname})[0]
                .read_json()
            )
            assert result['subscription_status_label'] == 'Fully entitled'

        # Verify the virt-who config-file exists.
        config_file = get_configure_file(vhd.id)
        get_configure_option('hypervisor_id', config_file),

        # Update virt-who config
        modify_name = gen_string('alpha')
        vhd.name = modify_name
        vhd.update(['name'])

        # Delete virt-who config
        vhd.delete()
        assert not target_sat.api.VirtWhoConfig(organization_id=org.id).search(
            query={'search': f'name={modify_name}'}
        )
