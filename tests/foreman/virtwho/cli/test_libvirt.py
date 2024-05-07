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
    deploy_configure_by_command,
    get_configure_command,
    get_configure_file,
    get_configure_option,
)


class TestVirtWhoConfigforLibvirt:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_cli', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, default_org, virtwho_config_cli, target_sat, deploy_type_cli
    ):
        """Verify " hammer virt-who-config deploy & fetch"

        :id: e66bf88a-bd4e-409a-91a8-bc5e005d95dd

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

        :id: 082a0eec-f024-4605-b876-a8959cf68e0c

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
