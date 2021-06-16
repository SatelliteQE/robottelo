"""Test class for Virtwho Configure CLI

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

from robottelo.cli.host import Host
from robottelo.cli.subscription import Subscription
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option
from robottelo.virtwho_utils import virtwho


@pytest.fixture()
def form_data():
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor-id': 'hostname',
        'hypervisor-type': virtwho.kubevirt.hypervisor_type,
        'organization-id': 1,
        'filtering-mode': 'none',
        'satellite-url': settings.server.hostname,
        'kubeconfig': virtwho.kubevirt.hypervisor_config_file,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data):
    return VirtWhoConfig.create(form_data)['general-information']


@pytest.mark.skip_if_open('BZ:1735540')
class TestVirtWhoConfigforKubevirt:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(self, form_data, virtwho_config):
        """Verify " hammer virt-who-config deploy"

        :id: d0b109f5-2699-43e4-a6cd-d682204d97a7

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        command = get_configure_command(virtwho_config['id'])
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor-type'], debug=True
        )
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})['general-information'][
            'status'
        ]
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={virtwho.sku.vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={virtwho.sku.vdc_physical} and type=STACK_DERIVED'),
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
            result = Host.subscription_attach({'host-id': host['id'], 'subscription-id': vdc_id})
            assert 'attached to the host successfully' in '\n'.join(result)
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_deploy_configure_by_script(self, form_data, virtwho_config):
        """Verify " hammer virt-who-config fetch"

        :id: 273df8e0-5ef5-47d9-9567-543157be7dd8

        :expectedresults: Config can be created, fetch and deploy

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        script = VirtWhoConfig.fetch({'id': virtwho_config['id']}, output_format='base')
        hypervisor_name, guest_name = deploy_configure_by_script(
            script, form_data['hypervisor-type'], debug=True
        )
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})['general-information'][
            'status'
        ]
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={virtwho.sku.vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={virtwho.sku.vdc_physical} and type=STACK_DERIVED'),
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
            result = Host.subscription_attach({'host-id': host['id'], 'subscription-id': vdc_id})
            assert 'attached to the host successfully' in '\n'.join(result)
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(self, form_data, virtwho_config):
        """Verify hypervisor_id option by hammer virt-who-config update"

        :id: 57b89c7e-538e-4ab8-98b5-af4b9f587792

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        values = ['uuid', 'hostname']
        for value in values:
            VirtWhoConfig.update({'id': virtwho_config['id'], 'hypervisor-id': value})
            result = VirtWhoConfig.info({'id': virtwho_config['id']})
            assert result['connection']['hypervisor-id'] == value
            config_file = get_configure_file(virtwho_config['id'])
            command = get_configure_command(virtwho_config['id'])
            deploy_configure_by_command(command, form_data['hypervisor-type'])
            assert get_configure_option('hypervisor_id', config_file) == value
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))
