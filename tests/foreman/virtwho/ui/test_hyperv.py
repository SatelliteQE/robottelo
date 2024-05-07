"""Test class for Virtwho Configure UI

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
    get_configure_id,
    get_configure_option,
)


class TestVirtwhoConfigforHyperv:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_ui', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, default_org, org_session, form_data_ui, deploy_type_ui
    ):
        """Verify configure created and deployed with id.

        :id: c8913398-c5c6-4f2c-bc53-0bbfb158b762

        :expectedresults:
            1. Config can be created and deployed by command/script
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

        :id: f2efc018-d57e-4dc5-895e-53af320237de

        :expectedresults:
            hypervisor_id can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to uuid/hwuuid/hostname.

        :CaseImportance: Medium
        """
        name = form_data_ui['name']
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, default_org.name)
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
