"""Test class for Virtwho Configure CLI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:Team: Phoenix

:CaseImportance: High

"""

import pytest

from robottelo.utils.virtwho import (
    deploy_configure_by_command,
    deploy_configure_by_script,
    get_configure_command,
    get_configure_file,
    get_configure_option,
)


class TestVirtWhoConfigforNutanix:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_cli', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, virtwho_config_cli, target_sat, deploy_type_cli
    ):
        """Verify "hammer virt-who-config deploy & fetch"

        :id: 71750104-b436-4ad4-9b6b-6f0fe8c3ee4c

        :expectedresults:
            1. Config can be created and deployed
            2. Config can be created, fetch and deploy

        :CaseImportance: High
        """
        assert virtwho_config_cli['status'] == 'No Report Yet'
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify hypervisor_id option by hammer virt-who-config update"

        :id: 565228cd-2124-41ed-89b7-84ec6ff77213

        :expectedresults: hypervisor_id option can be updated.

        :CaseImportance: Medium
        """
        for value in ['uuid', 'hostname']:
            target_sat.cli.VirtWhoConfig.update(
                {'id': virtwho_config_cli['id'], 'hypervisor-id': value}
            )
            result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
            assert result['connection']['hypervisor-id'] == value
            config_file = get_configure_file(virtwho_config_cli['id'])
            command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, module_sca_manifest_org, target_sat, form_data_cli, deploy_type
    ):
        """Verify "hammer virt-who-config deploy & fetch" on nutanix prism central mode

        :id: 96fd691f-5b62-469c-adc7-f2739ddf4a62

        :expectedresults:
            1. Config can be created and deployed
            2. The prism_central has been set in /etc/virt-who.d/vir-who.conf file
            3. Config can be created, fetch and deploy

        :CaseImportance: High
        """
        form_data_cli['prism-flavor'] = "central"
        virtwho_config = target_sat.cli.VirtWhoConfig.create(form_data_cli)['general-information']
        assert virtwho_config['status'] == 'No Report Yet'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command,
                form_data_cli['hypervisor-type'],
                debug=True,
                org=module_sca_manifest_org.label,
            )
        elif deploy_type == "script":
            script = target_sat.cli.VirtWhoConfig.fetch(
                {'id': virtwho_config['id']}, output_format='base'
            )
            deploy_configure_by_script(
                script,
                form_data_cli['hypervisor-type'],
                debug=True,
                org=module_sca_manifest_org.label,
            )
        # Check the option "prism_central=true" should be set in etc/virt-who.d/virt-who.conf
        config_file = get_configure_file(virtwho_config['id'])
        assert get_configure_option("prism_central", config_file) == 'true'
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'

    @pytest.mark.tier2
    def test_positive_prism_element_prism_central_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify prism_central option by hammer virt-who-config update"

        :id: 68c75ae0-0beb-483e-874a-b14f8171f40a

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
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option("prism_central", config_file) == 'true'
