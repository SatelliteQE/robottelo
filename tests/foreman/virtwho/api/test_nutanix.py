"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:Assignee: yanpliu

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option


@pytest.fixture()
def form_data(default_org, target_sat):
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.ahv.hypervisor_type,
        'hypervisor_server': settings.virtwho.ahv.hypervisor_server,
        'organization_id': default_org.id,
        'filtering_mode': 'none',
        'satellite_url': target_sat.hostname,
        'hypervisor_username': settings.virtwho.ahv.hypervisor_username,
        'hypervisor_password': settings.virtwho.ahv.hypervisor_password,
        'prism_flavor': settings.virtwho.ahv.prism_flavor,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data, target_sat):
    return target_sat.api.VirtWhoConfig(**form_data).create()


class TestVirtWhoConfigforNutanix:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: b1d8d261-80e0-498f-89fc-b1a246b46b83

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        command = get_configure_command(virtwho_config.id, default_org.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=default_org.label
        )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (
                hypervisor_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL',
            ),
            (
                guest_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED',
            ),
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
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'
        virtwho_config.delete()
        assert not target_sat.api.VirtWhoConfig().search(
            query={'search': f"name={form_data['name']}"}
        )

    @pytest.mark.tier2
    def test_positive_deploy_configure_by_script(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify "GET /foreman_virt_who_configure/api/

        v2/configs/:id/deploy_script"

        :id: 7aabfa3e-0ec0-44a3-8b7c-b67476318c2c

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        script = virtwho_config.deploy_script()
        hypervisor_name, guest_name = deploy_configure_by_script(
            script['virt_who_config_script'],
            form_data['hypervisor_type'],
            debug=True,
            org=default_org.label,
        )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (
                hypervisor_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL',
            ),
            (
                guest_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED',
            ),
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
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'
        virtwho_config.delete()
        target_sat.api.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 15e8c907-0e4c-40be-94e1-9734a85c2195

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        values = ['uuid', 'hostname']
        for value in values:
            virtwho_config.hypervisor_id = value
            virtwho_config.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config.id)
            command = get_configure_command(virtwho_config.id, default_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor_type'], org=default_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value
        virtwho_config.delete()
        assert not target_sat.api.VirtWhoConfig().search(
            query={'search': f"name={form_data['name']}"}
        )

    @pytest.mark.tier2
    def test_positive_prism_central_deploy_configure_by_id(
        self, default_org, form_data, target_sat
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs" on nutanix prism central mode

        :id: e7652f64-eaf8-45a5-ac01-eb40d53b6603

        :expectedresults:
            Config can be created and deployed
            The prism_central has been set in /etc/virt-who.d/vir-who.conf file

        :CaseLevel: Integration

        :CaseImportance: High
        """
        form_data['prism_flavor'] = "central"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data).create()
        assert virtwho_config.status == 'unknown'
        command = get_configure_command(virtwho_config.id, default_org.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=default_org.label
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
                f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL',
            ),
            (
                guest_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED',
            ),
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
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'
        virtwho_config.delete()
        assert not target_sat.api.VirtWhoConfig().search(
            query={'search': f"name={form_data['name']}"}
        )

    @pytest.mark.tier2
    def test_positive_prism_central_deploy_configure_by_script(
        self, default_org, form_data, target_sat
    ):
        """Verify "GET /foreman_virt_who_configure/api/ on nutanix prism central mode

        v2/configs/:id/deploy_script"

        :id: d139d70b-7c4a-4325-a892-4829c83755cd

        :expectedresults:
            Config can be created and deployed on nutanix prism central mode
            The prism_central has been set in /etc/virt-who.d/vir-who.conf file

        :CaseLevel: Integration

        :CaseImportance: High
        """
        form_data['prism_flavor'] = "central"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data).create()
        assert virtwho_config.status == 'unknown'
        script = virtwho_config.deploy_script()
        hypervisor_name, guest_name = deploy_configure_by_script(
            script['virt_who_config_script'],
            form_data['hypervisor_type'],
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
                f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL',
            ),
            (
                guest_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED',
            ),
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
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'
        virtwho_config.delete()
        target_sat.api.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})

    @pytest.mark.tier2
    def test_positive_prism_central_prism_central_option(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify prism_flavor option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 7f3b18c7-178c-4547-86ed-0e34772f755f

        :expectedresults: prism_flavor option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        value = 'central'
        virtwho_config.prism_flavor = value
        virtwho_config.update(['prism_flavor'])
        config_file = get_configure_file(virtwho_config.id)
        command = get_configure_command(virtwho_config.id, default_org.name)
        deploy_configure_by_command(command, form_data['hypervisor_type'], org=default_org.label)
        assert get_configure_option("prism_central", config_file) == 'true'
        virtwho_config.delete()
        assert not target_sat.api.VirtWhoConfig().search(
            query={'search': f"name={form_data['name']}"}
        )
