"""Test class for Virtwho Configure CLI

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

from robottelo.cli.host import Host
from robottelo.cli.subscription import Subscription
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import get_configure_command


@pytest.fixture()
def form_data(default_sat, default_org):
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor-id': 'hostname',
        'hypervisor-type': settings.virtwho.ahv.hypervisor_type,
        'hypervisor-server': settings.virtwho.ahv.hypervisor_server,
        'organization-id': default_org.id,
        'filtering-mode': 'none',
        'satellite-url': default_sat.hostname,
        'hypervisor-username': settings.virtwho.ahv.hypervisor_username,
        'hypervisor-password': settings.virtwho.ahv.hypervisor_password,
        'prism-flavor': settings.virtwho.ahv.prism_flavor,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data):
    return VirtWhoConfig.create(form_data)['general-information']


class TestVirtWhoConfigforNutanix:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(self, default_org, form_data, virtwho_config):
        """Verify " hammer virt-who-config deploy"

        :id: 129d8e57-b4fc-4d95-ad33-5aa6ec6fb146

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        command = get_configure_command(virtwho_config['id'], default_org.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor-type'], debug=True, org=default_org.label
        )
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})['general-information'][
            'status'
        ]
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'),
        ]
        for hostname, sku in hosts:
            host = Host.list({'search': hostname})[0]
            subscriptions = Subscription.list({'organization': default_org.name, 'search': sku})
            vdc_id = subscriptions[0]['id']
            if 'type=STACK_DERIVED' in sku:
                for item in subscriptions:
                    if hypervisor_name.lower() in item['type']:
                        vdc_id = item['id']
                        break
            result = Host.subscription_attach({'host-id': host['id'], 'subscription-id': vdc_id})
            assert result.strip() == 'Subscription attached to the host successfully.'
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))
