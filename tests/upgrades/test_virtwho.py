"""Test for Virt-who related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:Assignee: kuhuang

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import get_entity_data
from wait_for import wait_for

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC
from robottelo.utils.issue_handlers import is_open
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option


@pytest.fixture
def form_data(default_sat):
    esx = settings.virtwho.esx
    return {
        'debug': 1,
        'interval': '60',
        'hypervisor_id': 'hostname',
        'hypervisor_type': esx.hypervisor_type,
        'hypervisor_server': esx.hypervisor_server,
        'filtering_mode': 'none',
        'satellite_url': default_sat.hostname,
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

    @pre_upgrade
    def test_pre_create_virt_who_configuration(self, form_data):
        """Create and deploy virt-who configuration.

        :id: preupgrade-a36cbe89-47a2-422f-9881-0f86bea0e24e

        :steps: In Preupgrade Satellite, Create and deploy virt-who configuration.

        :expectedresults:
            1. Config can be created and deployed by command.
            2. No error msg in /var/log/rhsm/rhsm.log.
            3. Report is sent to satellite.
            4. Virtual sku can be generated and attached.
        """
        default_loc_id = entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0].id
        default_loc = entities.Location(id=default_loc_id).read()
        org = entities.Organization(name=ORG_DATA['name']).create()
        default_loc.organization.append(entities.Organization(id=org.id))
        default_loc.update(['organization'])
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        form_data.update({'organization_id': org.id})
        vhd = entities.VirtWhoConfig(**form_data).create()
        assert vhd.status == 'unknown'
        command = get_configure_command(vhd.id, org=org.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=org.label
        )
        virt_who_instance = (
            entities.VirtWhoConfig(organization_id=org.id)
            .search(query={'search': f'name={form_data["name"]}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (hypervisor_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'),
        ]
        for hostname, sku in hosts:
            if 'type=NORMAL' in sku:
                subscriptions = entities.Subscription(organization=org.id).search(
                    query={'search': sku}
                )
                vdc_id = subscriptions[0].id
            if 'type=STACK_DERIVED' in sku:
                subscriptions = entities.Subscription(organization=org.id).search(
                    query={'search': sku}
                )
                vdc_id = subscriptions[0].id
            host, time = wait_for(
                entities.Host(organization=org.id).search,
                func_args=(None, {'search': hostname}),
                fail_condition=[],
                timeout=5,
                delay=1,
            )
            entities.HostSubscription(host=host[0].id).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 1}]}
            )
            result = (
                entities.Host(organization=org.id).search(query={'search': hostname})[0].read_json()
            )
            assert result['subscription_status_label'] == 'Fully entitled'

        scenario_dict = {
            self.__class__.__name__: {
                'hypervisor_name': hypervisor_name,
                'guest_name': guest_name,
            }
        }
        create_dict(scenario_dict)

    @post_upgrade(depend_on=test_pre_create_virt_who_configuration)
    def test_post_crud_virt_who_configuration(self, form_data):
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
        org = entities.Organization().search(query={'search': f'name={ORG_DATA["name"]}'})[0]

        # Post upgrade, Verify virt-who exists and has same status.
        vhd = entities.VirtWhoConfig(organization_id=org.id).search(
            query={'search': f'name={form_data["name"]}'}
        )[0]
        if not is_open('BZ:1802395'):
            assert vhd.status == 'ok'
        # Verify virt-who status via CLI as we cannot check it via API now
        vhd_cli = VirtWhoConfig.exists(search=('name', form_data['name']))
        assert VirtWhoConfig.info({'id': vhd_cli['id']})['general-information']['status'] == 'OK'

        # Vefify the connection of the guest on Content host
        entity_data = get_entity_data(self.__class__.__name__)
        hypervisor_name = entity_data.get('hypervisor_name')
        guest_name = entity_data.get('guest_name')
        hosts = [hypervisor_name, guest_name]
        for hostname in hosts:
            result = (
                entities.Host(organization=org.id).search(query={'search': hostname})[0].read_json()
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
        assert not entities.VirtWhoConfig(organization_id=org.id).search(
            query={'search': f'name={modify_name}'}
        )
