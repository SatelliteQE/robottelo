"""Test class for Virtwho Configure API

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
    @pytest.mark.parametrize('deploy_type_api', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, default_org, virtwho_config_api, target_sat, deploy_type_api
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: 81731df9-9bfc-411b-9836-ff298fd5228d

        :expectedresults: Config can be created and deployed

        :CaseImportance: High
        """
        assert virtwho_config_api.status == 'unknown'
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config_api.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 850cc280-3f5a-498e-9132-5672dfe2f865

        :expectedresults: hypervisor_id option can be updated.

        :CaseImportance: Medium
        """
        for value in ['uuid', 'hostname']:
            virtwho_config_api.hypervisor_id = value
            virtwho_config_api.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config_api.id)
            command = get_configure_command(virtwho_config_api.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, module_sca_manifest_org, form_data_api, target_sat, deploy_type
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs" on nutanix prism central mode

        :id: 14b87abb-9355-4669-929a-20e656cdf446

        :expectedresults:
            Config can be created and deployed
            The prism_central has been set in /etc/virt-who.d/vir-who.conf file

        :CaseImportance: High
        """
        form_data_api['prism_flavor'] = "central"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
        assert virtwho_config.status == 'unknown'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command,
                form_data_api['hypervisor_type'],
                debug=True,
                org=module_sca_manifest_org.label,
            )
        elif deploy_type == "script":
            script = virtwho_config.deploy_script()
            deploy_configure_by_script(
                script['virt_who_config_script'],
                form_data_api['hypervisor_type'],
                debug=True,
                org=module_sca_manifest_org.label,
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

    @pytest.mark.tier2
    def test_positive_prism_central_prism_central_option(
        self, module_sca_manifest_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify prism_flavor option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: f6ca8722-8f39-47b2-b7c0-e0c554aa7c65

        :expectedresults: prism_flavor option can be updated.

        :CaseImportance: Medium
        """
        value = 'central'
        virtwho_config_api.prism_flavor = value
        virtwho_config_api.update(['prism_flavor'])
        config_file = get_configure_file(virtwho_config_api.id)
        command = get_configure_command(virtwho_config_api.id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option("prism_central", config_file) == 'true'
