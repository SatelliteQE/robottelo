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
        'hypervisor-type': virtwho.rhevm.hypervisor_type,
        'hypervisor-server': virtwho.rhevm.hypervisor_server,
        'organization-id': 1,
        'filtering-mode': 'none',
        'satellite-url': settings.server.hostname,
        'hypervisor-username': virtwho.rhevm.hypervisor_username,
        'hypervisor-password': virtwho.rhevm.hypervisor_password,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data):
    return VirtWhoConfig.create(form_data)['general-information']


class TestVirtWhoConfigforRhevm:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(self, form_data, virtwho_config):
        """Verify " hammer virt-who-config deploy"

        :id: f8508ceb-229a-487d-be4b-fd622b431e36

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

        :id: 4c7c3159-8bd3-4fe8-a330-2211bfbcfa11

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

        :id: d8428508-3149-4558-8173-4386db5e3760

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        # esx and rhevm support hwuuid option
        values = ['uuid', 'hostname', 'hwuuid']
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
