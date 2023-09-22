"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.utils.virtwho import (
    deploy_configure_by_command,
    deploy_configure_by_script,
    get_configure_command,
    get_configure_file,
    get_configure_id,
    get_configure_option,
)


@pytest.fixture()
def form_data():
    form = {
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.hyperv.hypervisor_type,
        'hypervisor_content.server': settings.virtwho.hyperv.hypervisor_server,
        'hypervisor_content.username': settings.virtwho.hyperv.hypervisor_username,
        'hypervisor_content.password': settings.virtwho.hyperv.hypervisor_password,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data, target_sat, session):
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        yield virtwho_config
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


class TestVirtwhoConfigforHyperv:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_deploy_configure_by_id_script(
        self, default_org, virtwho_config, session, form_data, deploy_type
    ):
        """Verify configure created and deployed with id.

        :id: c8913398-c5c6-4f2c-bc53-0bbfb158b762

        :expectedresults:
            1. Config can be created and deployed by command/script
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = form_data['name']
        values = session.virtwho_configure.read(name)
        if deploy_type == "id":
            command = values['deploy']['command']
            hypervisor_name, guest_name = deploy_configure_by_command(
                command, form_data['hypervisor_type'], debug=True, org=default_org.label
            )
        elif deploy_type == "script":
            script = values['deploy']['script']
            hypervisor_name, guest_name = deploy_configure_by_script(
                script, form_data['hypervisor_type'], debug=True, org=default_org.label
            )
        assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
        hypervisor_display_name = session.contenthost.search(hypervisor_name)[0]['Name']
        vdc_physical = f'product_id = {settings.virtwho.sku.vdc_physical} and type=NORMAL'
        vdc_virtual = f'product_id = {settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'
        assert (
            session.contenthost.read_legacy_ui(hypervisor_display_name)['subscriptions']['status']
            == 'Unsubscribed hypervisor'
        )
        session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
        assert session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
        assert (
            session.contenthost.read_legacy_ui(guest_name)['subscriptions']['status']
            == 'Unentitled'
        )
        session.contenthost.add_subscription(guest_name, vdc_virtual)
        assert session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(self, default_org, virtwho_config, session, form_data):
        """Verify Hypervisor ID dropdown options.

        :id: f2efc018-d57e-4dc5-895e-53af320237de

        :expectedresults:
            hypervisor_id can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to uuid/hwuuid/hostname.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = form_data['name']
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, default_org.name)
        config_file = get_configure_file(config_id)
        values = ['uuid', 'hostname']
        for value in values:
            session.virtwho_configure.edit(name, {'hypervisor_id': value})
            results = session.virtwho_configure.read(name)
            assert results['overview']['hypervisor_id'] == value
            deploy_configure_by_command(
                config_command, form_data['hypervisor_type'], org=default_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value
