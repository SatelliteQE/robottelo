"""Test class for Virtwho Configure CLI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

"""

import pytest

from robottelo.utils.virtwho import (
    deploy_configure_by_command,
    get_configure_command,
    get_configure_file,
    get_configure_option,
)


class TestVirtWhoConfigforLibvirt:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_cli', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, virtwho_config_cli, target_sat, deploy_type_cli
    ):
        """Verify " hammer virt-who-config deploy & fetch"

        :id: 53143fc3-97e0-4403-8114-4d7f20fde98e

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

        :id: e68421b5-ff3d-4f25-926d-8330b92f2cdf

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
