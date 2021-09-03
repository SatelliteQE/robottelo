"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:Assignee: kuhuang

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.cli.host import Host
from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option


@pytest.fixture(scope='class')
def default_org():
    return entities.Organization().search(query={'search': 'name="Default Organization"'})[0]


@pytest.fixture()
def form_data(default_org, default_sat):
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.hyperv.hypervisor_type,
        'hypervisor_server': settings.virtwho.hyperv.hypervisor_server,
        'organization_id': default_org.id,
        'filtering_mode': 'none',
        'satellite_url': default_sat.hostname,
        'hypervisor_username': settings.virtwho.hyperv.hypervisor_username,
        'hypervisor_password': settings.virtwho.hyperv.hypervisor_password,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data):
    return entities.VirtWhoConfig(**form_data).create()


class TestVirtWhoConfigforHyperv:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(self, form_data, virtwho_config):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: f5228e01-bb8d-4c8e-877e-cd8bc494f00e

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        command = get_configure_command(virtwho_config.id)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True
        )
        virt_who_instance = (
            entities.VirtWhoConfig()
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
            host = Host.list({'search': hostname})[0]
            subscriptions = Subscription.list({'organization': DEFAULT_ORG, 'search': sku})
            vdc_id = subscriptions[0]['id']
            if 'type=STACK_DERIVED' in sku:
                for item in subscriptions:
                    if hypervisor_name.lower() in item['type']:
                        vdc_id = item['id']
                        break
            entities.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 1}]}
            )
            result = entities.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'
        virtwho_config.delete()
        assert not entities.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})

    @pytest.mark.tier2
    def test_positive_deploy_configure_by_script(self, form_data, virtwho_config):
        """Verify "GET /foreman_virt_who_configure/api/

        v2/configs/:id/deploy_script"

        :id: 2c58b131-5d68-41d2-b804-4548f998ab5f

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        script = virtwho_config.deploy_script()
        hypervisor_name, guest_name = deploy_configure_by_script(
            script['virt_who_config_script'], form_data['hypervisor_type'], debug=True
        )
        virt_who_instance = (
            entities.VirtWhoConfig()
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
            host = Host.list({'search': hostname})[0]
            subscriptions = Subscription.list({'organization': DEFAULT_ORG, 'search': sku})
            vdc_id = subscriptions[0]['id']
            if 'type=STACK_DERIVED' in sku:
                for item in subscriptions:
                    if hypervisor_name.lower() in item['type']:
                        vdc_id = item['id']
                        break
            entities.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 1}]}
            )
            result = entities.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'
        virtwho_config.delete()
        assert not entities.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(self, form_data, virtwho_config):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 16344235-1607-4f60-950b-5a91546cf8f4

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        values = ['uuid', 'hostname']
        for value in values:
            virtwho_config.hypervisor_id = value
            virtwho_config.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config.id)
            command = get_configure_command(virtwho_config.id)
            deploy_configure_by_command(command, form_data['hypervisor_type'])
            assert get_configure_option('hypervisor_id', config_file) == value
        virtwho_config.delete()
        assert not entities.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})
