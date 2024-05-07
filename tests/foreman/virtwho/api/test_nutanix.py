"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

:CaseImportance: High

"""

import pytest

from robottelo.config import settings
from robottelo.utils.virtwho import (
    check_message_in_rhsm_log,
    deploy_configure_by_command,
    deploy_configure_by_script,
    get_configure_command,
    get_configure_file,
    get_configure_option,
    get_hypervisor_ahv_mapping,
)


@pytest.mark.usefixtures('delete_host')
class TestVirtWhoConfigforNutanix:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_api', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, default_org, virtwho_config_api, target_sat, deploy_type_api
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: b1d8d261-80e0-498f-89fc-b1a246b46b83

        :expectedresults: Config can be created and deployed

        :CaseImportance: High
        """
        assert virtwho_config_api.status == 'unknown'
        hypervisor_name, guest_name = deploy_type_api
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config_api.name}'})[0]
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
        self, default_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 15e8c907-0e4c-40be-94e1-9734a85c2195

        :expectedresults: hypervisor_id option can be updated.

        :CaseImportance: Medium
        """
        values = ['uuid', 'hostname']
        for value in values:
            virtwho_config_api.hypervisor_id = value
            virtwho_config_api.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config_api.id)
            command = get_configure_command(virtwho_config_api.id, default_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=default_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, default_org, form_data_api, target_sat, deploy_type
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs" on nutanix prism central mode

        :id: e7652f64-eaf8-45a5-ac01-eb40d53b6603

        :expectedresults:
            Config can be created and deployed
            The prism_central has been set in /etc/virt-who.d/vir-who.conf file

        :CaseImportance: High
        """
        form_data_api['prism_flavor'] = "central"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
        assert virtwho_config.status == 'unknown'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config.id, default_org.name)
            hypervisor_name, guest_name = deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], debug=True, org=default_org.label
            )
        elif deploy_type == "script":
            script = virtwho_config.deploy_script()
            hypervisor_name, guest_name = deploy_configure_by_script(
                script['virt_who_config_script'],
                form_data_api['hypervisor_type'],
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
        self, default_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify prism_flavor option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 7f3b18c7-178c-4547-86ed-0e34772f755f

        :expectedresults: prism_flavor option can be updated.

        :CaseImportance: Medium
        """
        value = 'central'
        virtwho_config_api.prism_flavor = value
        virtwho_config_api.update(['prism_flavor'])
        config_file = get_configure_file(virtwho_config_api.id)
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=default_org.label
        )
        assert get_configure_option("prism_central", config_file) == 'true'

    @pytest.mark.tier2
    def test_positive_ahv_internal_debug_option(
        self, default_org, form_data_api, virtwho_config_api, target_sat
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

        :CaseImportance: Medium

        :BZ: 2141719

        :customerscenario: true
        """
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], debug=True, org=default_org.label
        )
        result = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config_api.name}'})[0]
            .ahv_internal_debug
        )
        assert str(result) == 'False'
        # ahv_internal_debug does not set in virt-who-config-X.conf
        config_file = get_configure_file(virtwho_config_api.id)
        option = 'ahv_internal_debug'
        env_error = f"option {option} is not exist or not be enabled in {config_file}"
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - TODO determine better exception
            get_configure_option("ahv_internal_debug", config_file)
        assert str(exc_info.value) == env_error
        # check message exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert check_message_in_rhsm_log(message) == message

        # Update ahv_internal_debug option to true
        value = 'true'
        virtwho_config_api.ahv_internal_debug = value
        virtwho_config_api.update(['ahv_internal_debug'])
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], debug=True, org=default_org.label
        )
        assert (
            get_hypervisor_ahv_mapping(form_data_api['hypervisor_type']) == 'Host UUID found for VM'
        )
        result = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config_api.name}'})[0]
            .ahv_internal_debug
        )
        assert str(result) == 'True'
        # ahv_internal_debug bas been set to true in virt-who-config-X.conf
        config_file = get_configure_file(virtwho_config_api.id)
        assert get_configure_option("ahv_internal_debug", config_file) == 'true'
        # check message does not exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert str(check_message_in_rhsm_log(message)) == 'False'
