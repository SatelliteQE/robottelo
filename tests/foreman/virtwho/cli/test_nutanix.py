"""Test class for Virtwho Configure CLI

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


class TestVirtWhoConfigforNutanix:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_cli', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, default_org, virtwho_config_cli, target_sat, deploy_type_cli
    ):
        """Verify "hammer virt-who-config deploy & fetch"

        :id: 129d8e57-b4fc-4d95-ad33-5aa6ec6fb146

        :expectedresults:
            1. Config can be created and deployed
            2. Config can be created, fetch and deploy

        :CaseImportance: High
        """
        assert virtwho_config_cli['status'] == 'No Report Yet'
        hypervisor_name, guest_name = deploy_type_cli
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'),
        ]
        for hostname, sku in hosts:
            host = target_sat.cli.Host.list({'search': hostname})[0]
            subscriptions = target_sat.cli.Subscription.list(
                {'organization': default_org.name, 'search': sku}
            )
            vdc_id = subscriptions[0]['id']
            if 'type=STACK_DERIVED' in sku:
                for item in subscriptions:
                    if hypervisor_name.lower() in item['type']:
                        vdc_id = item['id']
                        break
            result = target_sat.cli.Host.subscription_attach(
                {'host-id': host['id'], 'subscription-id': vdc_id}
            )
            assert result.strip() == 'Subscription attached to the host successfully.'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, default_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify hypervisor_id option by hammer virt-who-config update"

        :id: af92b814-fe7a-4969-b2ab-7b68859de3ce

        :expectedresults: hypervisor_id option can be updated.

        :CaseImportance: Medium
        """
        values = ['uuid', 'hostname']
        for value in values:
            target_sat.cli.VirtWhoConfig.update(
                {'id': virtwho_config_cli['id'], 'hypervisor-id': value}
            )
            result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
            assert result['connection']['hypervisor-id'] == value
            config_file = get_configure_file(virtwho_config_cli['id'])
            command = get_configure_command(virtwho_config_cli['id'], default_org.name)
            deploy_configure_by_command(
                command, form_data_cli['hypervisor-type'], org=default_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, default_org, form_data_cli, target_sat, deploy_type
    ):
        """Verify "hammer virt-who-config deploy" on nutanix prism central mode

        :id: 224ad753-6186-4b09-a72c-458839a8e412

        :expectedresults:
            Config can be created and deployed
            The prism_central has been set in /etc/virt-who.d/vir-who.conf file

        :CaseImportance: High
        """
        form_data_cli['prism-flavor'] = "central"
        virtwho_config = target_sat.cli.VirtWhoConfig.create(form_data_cli)['general-information']
        assert virtwho_config['status'] == 'No Report Yet'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config['id'], default_org.name)
            hypervisor_name, guest_name = deploy_configure_by_command(
                command, form_data_cli['hypervisor-type'], debug=True, org=default_org.label
            )
        elif deploy_type == "script":
            script = target_sat.cli.VirtWhoConfig.fetch(
                {'id': virtwho_config['id']}, output_format='base'
            )
            hypervisor_name, guest_name = deploy_configure_by_script(
                script, form_data_cli['hypervisor-type'], debug=True, org=default_org.label
            )
        # Check the option "prism_central=true" should be set in etc/virt-who.d/virt-who.conf
        config_file = get_configure_file(virtwho_config['id'])
        assert get_configure_option("prism_central", config_file) == 'true'
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'),
        ]
        for hostname, sku in hosts:
            host = target_sat.cli.Host.list({'search': hostname})[0]
            subscriptions = target_sat.cli.Subscription.list(
                {'organization': default_org.name, 'search': sku}
            )
            vdc_id = subscriptions[0]['id']
            if 'type=STACK_DERIVED' in sku:
                for item in subscriptions:
                    if hypervisor_name.lower() in item['type']:
                        vdc_id = item['id']
                        break
            result = target_sat.cli.Host.subscription_attach(
                {'host-id': host['id'], 'subscription-id': vdc_id}
            )
            assert result.strip() == 'Subscription attached to the host successfully.'

    @pytest.mark.tier2
    def test_positive_prism_central_prism_central_option(
        self, default_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify prism_central option by hammer virt-who-config update"

        :id: 701e0390-2bfb-404a-a9bd-fa0fb5ecfdf8

        :expectedresults: prism_central option can be updated.

        :CaseImportance: Medium
        """
        value = 'central'
        result = target_sat.cli.VirtWhoConfig.update(
            {'id': virtwho_config_cli['id'], 'prism-flavor': value}
        )
        assert (
            result[0]['message'] == f"Virt Who configuration [{virtwho_config_cli['name']}] updated"
        )
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
        assert result['general-information']['ahv-prism-flavor'] == value
        config_file = get_configure_file(virtwho_config_cli['id'])
        command = get_configure_command(virtwho_config_cli['id'], default_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], org=default_org.label
        )
        assert get_configure_option("prism_central", config_file) == 'true'

    @pytest.mark.tier2
    def test_positive_ahv_internal_debug_option(
        self, default_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify ahv_internal_debug option by hammer virt-who-config"

        :id: a169a843-6ec7-4ef1-b471-649304e77cf1268

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
        command = get_configure_command(virtwho_config_cli['id'], default_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], debug=True, org=default_org.label
        )
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
        assert result['general-information']['enable-ahv-debug'] == 'no'
        # ahv_internal_debug does not set in virt-who-config-X.conf
        config_file = get_configure_file(virtwho_config_cli['id'])
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
        result = target_sat.cli.VirtWhoConfig.update(
            {'id': virtwho_config_cli['id'], 'ahv-internal-debug': value}
        )
        assert (
            result[0]['message'] == f"Virt Who configuration [{virtwho_config_cli['name']}] updated"
        )
        command = get_configure_command(virtwho_config_cli['id'], default_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], debug=True, org=default_org.label
        )
        assert (
            get_hypervisor_ahv_mapping(form_data_cli['hypervisor-type']) == 'Host UUID found for VM'
        )
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
        assert result['general-information']['enable-ahv-debug'] == 'yes'
        # ahv_internal_debug bas been set to true in virt-who-config-X.conf
        config_file = get_configure_file(virtwho_config_cli['id'])
        assert get_configure_option("ahv_internal_debug", config_file) == 'true'
        # check message does not exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert str(check_message_in_rhsm_log(message)) == 'False'
