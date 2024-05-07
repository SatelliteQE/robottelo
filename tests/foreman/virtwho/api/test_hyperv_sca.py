"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

:CaseImportance: High

"""

import pytest

from robottelo.utils.virtwho import (
    deploy_configure_by_command,
    get_configure_command,
    get_configure_file,
    get_configure_option,
)


class TestVirtWhoConfigforHyperv:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_api', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, virtwho_config_api, target_sat, deploy_type_api
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: d238e2c0-a9e9-40ec-8a80-81d3e9fa1d7e

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

        :id: 893c043f-a22d-4564-99ce-b7dcc14059bf

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
