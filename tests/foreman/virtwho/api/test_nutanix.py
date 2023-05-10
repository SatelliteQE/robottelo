"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

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

from robottelo.config import settings
from robottelo.utils.virtwho import check_message_in_rhsm_log
from robottelo.utils.virtwho import deploy_configure_by_command
from robottelo.utils.virtwho import deploy_configure_by_script
from robottelo.utils.virtwho import get_configure_command
from robottelo.utils.virtwho import get_configure_file
from robottelo.utils.virtwho import get_configure_option
from robottelo.utils.virtwho import get_guest_info
from robottelo.utils.virtwho import get_hypervisor_ahv_mapping


@pytest.fixture()
def form_data(default_org, target_sat):
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.ahv.hypervisor_type,
        'hypervisor_server': settings.virtwho.ahv.hypervisor_server,
        'organization_id': default_org.id,
        'filtering_mode': 'none',
        'satellite_url': target_sat.hostname,
        'hypervisor_username': settings.virtwho.ahv.hypervisor_username,
        'hypervisor_password': settings.virtwho.ahv.hypervisor_password,
        'prism_flavor': settings.virtwho.ahv.prism_flavor,
        'ahv_internal_debug': 'false',
    }
    return form


@pytest.fixture()
def virtwho_config(form_data, target_sat):
    virtwho_config = target_sat.api.VirtWhoConfig(**form_data).create()
    yield virtwho_config
    virtwho_config.delete()
    assert not target_sat.api.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})


@pytest.fixture(autouse=True)
def clean_host(form_data, target_sat):
    guest_name, _ = get_guest_info(form_data['hypervisor_type'])
    results = target_sat.api.Host().search(query={'search': guest_name})
    if results:
        target_sat.api.Host(id=results[0].read_json()['id']).delete()


@pytest.mark.usefixtures('clean_host')
class TestVirtWhoConfigforNutanix:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: b1d8d261-80e0-498f-89fc-b1a246b46b83

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        command = get_configure_command(virtwho_config.id, default_org.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=default_org.label
        )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (
                hypervisor_name,
                settings.virtwho.sku.vdc_physical,
                'NORMAL',
            ),
            (
                guest_name,
                settings.virtwho.sku.vdc_virtual,
                'STACK_DERIVED',
            ),
        ]
        for hostname, sku, type in hosts:
            host = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            subscriptions = target_sat.api.Organization(id=default_org.id).subscriptions()[
                'results'
            ]
            for item in subscriptions:
                if item['type'] == type and item['product_id'] == sku:
                    vdc_id = item['id']
                    if (
                        'hypervisor' in item
                        and hypervisor_name.lower() in item['hypervisor']['name']
                    ):
                        break
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'

    @pytest.mark.tier2
    def test_positive_deploy_configure_by_script(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify "GET /foreman_virt_who_configure/api/

        v2/configs/:id/deploy_script"

        :id: 7aabfa3e-0ec0-44a3-8b7c-b67476318c2c

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        script = virtwho_config.deploy_script()
        hypervisor_name, guest_name = deploy_configure_by_script(
            script['virt_who_config_script'],
            form_data['hypervisor_type'],
            debug=True,
            org=default_org.label,
        )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (
                hypervisor_name,
                settings.virtwho.sku.vdc_physical,
                'NORMAL',
            ),
            (
                guest_name,
                settings.virtwho.sku.vdc_virtual,
                'STACK_DERIVED',
            ),
        ]
        for hostname, sku, type in hosts:
            host = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            subscriptions = target_sat.api.Organization(id=default_org.id).subscriptions()[
                'results'
            ]
            for item in subscriptions:
                if item['type'] == type and item['product_id'] == sku:
                    vdc_id = item['id']
                    if (
                        'hypervisor' in item
                        and hypervisor_name.lower() in item['hypervisor']['name']
                    ):
                        break
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 15e8c907-0e4c-40be-94e1-9734a85c2195

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        values = ['uuid', 'hostname']
        for value in values:
            virtwho_config.hypervisor_id = value
            virtwho_config.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config.id)
            command = get_configure_command(virtwho_config.id, default_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor_type'], org=default_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, default_org, form_data, target_sat, deploy_type
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs" on nutanix prism central mode

        :id: e7652f64-eaf8-45a5-ac01-eb40d53b6603

        :expectedresults:
            Config can be created and deployed
            The prism_central has been set in /etc/virt-who.d/vir-who.conf file

        :CaseLevel: Integration

        :CaseImportance: High
        """
        form_data['prism_flavor'] = "central"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data).create()
        assert virtwho_config.status == 'unknown'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config.id, default_org.name)
            hypervisor_name, guest_name = deploy_configure_by_command(
                command, form_data['hypervisor_type'], debug=True, org=default_org.label
            )
        elif deploy_type == "script":
            script = virtwho_config.deploy_script()
            hypervisor_name, guest_name = deploy_configure_by_script(
                script['virt_who_config_script'],
                form_data['hypervisor_type'],
                debug=True,
                org=default_org.label,
            )
        # Check the option "prism_central=true" should be set in etc/virt-who.d/virt-who.conf
        config_file = get_configure_file(virtwho_config.id)
        assert get_configure_option("prism_central", config_file) == 'true'
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (
                hypervisor_name,
                settings.virtwho.sku.vdc_physical,
                'NORMAL',
            ),
            (
                guest_name,
                settings.virtwho.sku.vdc_virtual,
                'STACK_DERIVED',
            ),
        ]
        for hostname, sku, type in hosts:
            host = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            subscriptions = target_sat.api.Organization(id=default_org.id).subscriptions()[
                'results'
            ]
            for item in subscriptions:
                if item['type'] == type and item['product_id'] == sku:
                    vdc_id = item['id']
                    if (
                        'hypervisor' in item
                        and hypervisor_name.lower() in item['hypervisor']['name']
                    ):
                        break
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'

    @pytest.mark.tier2
    def test_positive_prism_central_prism_central_option(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify prism_flavor option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 7f3b18c7-178c-4547-86ed-0e34772f755f

        :expectedresults: prism_flavor option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        value = 'central'
        virtwho_config.prism_flavor = value
        virtwho_config.update(['prism_flavor'])
        config_file = get_configure_file(virtwho_config.id)
        command = get_configure_command(virtwho_config.id, default_org.name)
        deploy_configure_by_command(command, form_data['hypervisor_type'], org=default_org.label)
        assert get_configure_option("prism_central", config_file) == 'true'

    @pytest.mark.tier2
    def test_positive_ahv_internal_debug_option(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify ahv_internal_debug option by hammer virt-who-config"

        :id: aa6a7443-62ae-4a87-8c27-4a7808f4b1da308

        :expectedresults:
            1. enable-ahv-debug option has been set to no
            2. ahv_internal_debug bas been set to false in virt-who-config-X.conf
            3. warning message exist in log file /var/log/rhsm/rhsm.log
            4. ahv_internal_debug option can be updated
            5. message Host UUID {system_uuid} found for VM: {guest_uuid} exist in rhsm.log
            6. ahv_internal_debug bas been set to true in virt-who-config-X.conf
            7. warning message does not exist in log file /var/log/rhsm/rhsm.log
        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 2141719
        """
        command = get_configure_command(virtwho_config.id, default_org.name)
        deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=default_org.label
        )
        result = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .ahv_internal_debug
        )
        assert str(result) == 'False'
        # ahv_internal_debug does not set in virt-who-config-X.conf
        config_file = get_configure_file(virtwho_config.id)
        option = 'ahv_internal_debug'
        env_error = f"option {option} is not exist or not be enabled in {config_file}"
        try:
            get_configure_option("ahv_internal_debug", config_file)
        except Exception as VirtWhoError:
            assert env_error == str(VirtWhoError)
        # check message exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert check_message_in_rhsm_log(message) == message

        # Update ahv_internal_debug option to true
        value = 'true'
        virtwho_config.ahv_internal_debug = value
        virtwho_config.update(['ahv_internal_debug'])
        command = get_configure_command(virtwho_config.id, default_org.name)
        deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=default_org.label
        )
        assert get_hypervisor_ahv_mapping(form_data['hypervisor_type']) == 'Host UUID found for VM'
        result = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .ahv_internal_debug
        )
        assert str(result) == 'True'
        # ahv_internal_debug bas been set to true in virt-who-config-X.conf
        config_file = get_configure_file(virtwho_config.id)
        assert get_configure_option("ahv_internal_debug", config_file) == 'true'
        # check message does not exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert str(check_message_in_rhsm_log(message)) == 'False'
