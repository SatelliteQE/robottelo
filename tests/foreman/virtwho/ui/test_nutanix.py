"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.utils.virtwho import (
    check_message_in_rhsm_log,
    deploy_configure_by_command,
    deploy_configure_by_script,
    get_configure_command,
    get_configure_file,
    get_configure_id,
    get_configure_option,
    get_hypervisor_ahv_mapping,
)


class TestVirtwhoConfigforNutanix:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_ui', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, default_org, org_session, form_data_ui, deploy_type_ui
    ):
        """Verify configure created and deployed with id.

        :id: becea4d0-db4e-4a85-93d2-d40e86da0e2f

        :expectedresults:
            1. Config can be created and deployed by command
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseImportance: High
        """
        hypervisor_name, guest_name = deploy_type_ui
        assert org_session.virtwho_configure.search(form_data_ui['name'])[0]['Status'] == 'ok'
        hypervisor_display_name = org_session.contenthost.search(hypervisor_name)[0]['Name']
        vdc_physical = f'product_id = {settings.virtwho.sku.vdc_physical} and type=NORMAL'
        vdc_virtual = f'product_id = {settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'
        assert (
            org_session.contenthost.read_legacy_ui(hypervisor_display_name)['subscriptions'][
                'status'
            ]
            == 'Unsubscribed hypervisor'
        )
        org_session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
        assert org_session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
        assert (
            org_session.contenthost.read_legacy_ui(guest_name)['subscriptions']['status']
            == 'Unentitled'
        )
        org_session.contenthost.add_subscription(guest_name, vdc_virtual)
        assert org_session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, default_org, virtwho_config_ui, org_session, form_data_ui
    ):
        """Verify Hypervisor ID dropdown options.

        :id: e076a305-88f4-42fb-8ef2-cb55e38eb912

        :expectedresults:
            hypervisor_id can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to uuid/hwuuid/hostname.

        :CaseImportance: Medium
        """
        name = form_data_ui['name']
        values = org_session.virtwho_configure.read(name)
        config_id = get_configure_id(name)
        config_command = values['deploy']['command']
        config_file = get_configure_file(config_id)
        values = ['uuid', 'hostname']
        for value in values:
            org_session.virtwho_configure.edit(name, {'hypervisor_id': value})
            results = org_session.virtwho_configure.read(name)
            assert results['overview']['hypervisor_id'] == value
            deploy_configure_by_command(
                config_command, form_data_ui['hypervisor_type'], org=default_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, default_org, org_session, form_data_ui, deploy_type
    ):
        """Verify configure created and deployed with id on nutanix prism central mode

        :id: 74fb3b05-2f88-4ebf-8d0d-4973ee8536d8

        :expectedresults:
            1. Config can be created and deployed by command
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. The prism_central has been set true in /etc/virt-who.d/vir-who.conf file
            5. Virtual sku can be generated and attached
            6. Config can be deleted

        :CaseImportance: High
        """
        name = gen_string('alpha')
        form_data_ui['name'] = name
        form_data_ui['hypervisor_content.prism_flavor'] = "Prism Central"
        with org_session:
            org_session.virtwho_configure.create(form_data_ui)
            values = org_session.virtwho_configure.read(name)
            if deploy_type == "id":
                command = values['deploy']['command']
                hypervisor_name, guest_name = deploy_configure_by_command(
                    command, form_data_ui['hypervisor_type'], debug=True, org=default_org.label
                )
            elif deploy_type == "script":
                script = values['deploy']['script']
                hypervisor_name, guest_name = deploy_configure_by_script(
                    script, form_data_ui['hypervisor_type'], debug=True, org=default_org.label
                )
            # Check the option "prism_central=true" should be set in etc/virt-who.d/virt-who.conf
            config_id = get_configure_id(name)
            config_file = get_configure_file(config_id)
            assert get_configure_option("prism_central", config_file) == 'true'
            assert org_session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            hypervisor_display_name = org_session.contenthost.search(hypervisor_name)[0]['Name']
            vdc_physical = f'product_id = {settings.virtwho.sku.vdc_physical} and type=NORMAL'
            vdc_virtual = f'product_id = {settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'
            assert (
                org_session.contenthost.read_legacy_ui(hypervisor_display_name)['subscriptions'][
                    'status'
                ]
                == 'Unsubscribed hypervisor'
            )
            org_session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
            assert (
                org_session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
            )
            assert (
                org_session.contenthost.read_legacy_ui(guest_name)['subscriptions']['status']
                == 'Unentitled'
            )
            org_session.contenthost.add_subscription(guest_name, vdc_virtual)
            assert org_session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'
            org_session.virtwho_configure.delete(name)
            assert not org_session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_prism_central_prism_flavor_option(
        self, default_org, virtwho_config_ui, org_session, form_data_ui
    ):
        """Verify prism_flavor dropdown options.

        :id: c76d94dd-25da-447d-8194-44217a36808b

        :expectedresults:
            prism_flavor can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to prism central.

        :CaseImportance: Medium
        """
        name = form_data_ui['name']
        results = org_session.virtwho_configure.read(name)
        assert results['overview']['prism_flavor'] == "element"
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, default_org.name)
        config_file = get_configure_file(config_id)
        org_session.virtwho_configure.edit(
            name, {'hypervisor_content.prism_flavor': "Prism Central"}
        )
        results = org_session.virtwho_configure.read(name)
        assert results['overview']['prism_flavor'] == "central"
        deploy_configure_by_command(
            config_command, form_data_ui['hypervisor_type'], org=default_org.label
        )
        assert get_configure_option('prism_central', config_file) == 'true'

    @pytest.mark.tier2
    def test_positive_ahv_internal_debug_option(
        self, default_org, virtwho_config_ui, org_session, form_data_ui
    ):
        """Verify ahv_internal_debug option by hammer virt-who-config"

        :id: af92b814-fe7a-4969-b2ab-7b68859de3ce155

        :expectedresults:
            1. enable-ahv-debug option has been set to false
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
        name = form_data_ui['name']
        config_id = get_configure_id(name)
        values = org_session.virtwho_configure.read(name)
        command = values['deploy']['command']
        config_file = get_configure_file(config_id)
        deploy_configure_by_command(
            command, form_data_ui['hypervisor_type'], debug=True, org=default_org.label
        )
        results = org_session.virtwho_configure.read(name)
        assert str(results['overview']['ahv_internal_debug']) == 'False'
        # ahv_internal_debug does not set in virt-who-config-X.conf
        option = 'ahv_internal_debug'
        env_error = f"option {option} is not exist or not be enabled in {config_file}"
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - TODO determine better exception
            get_configure_option("ahv_internal_debug", config_file)
        assert str(exc_info.value) == env_error
        # check message exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert check_message_in_rhsm_log(message) == message

        # Update ahv_internal_debug option to true
        org_session.virtwho_configure.edit(name, {'ahv_internal_debug': True})
        results = org_session.virtwho_configure.read(name)
        command = results['deploy']['command']
        assert str(results['overview']['ahv_internal_debug']) == 'True'
        deploy_configure_by_command(
            command, form_data_ui['hypervisor_type'], debug=True, org=default_org.label
        )
        assert (
            get_hypervisor_ahv_mapping(form_data_ui['hypervisor_type']) == 'Host UUID found for VM'
        )
        # ahv_internal_debug bas been set to true in virt-who-config-X.conf
        config_file = get_configure_file(config_id)
        assert get_configure_option("ahv_internal_debug", config_file) == 'true'
        # check message does not exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert str(check_message_in_rhsm_log(message)) == 'False'
