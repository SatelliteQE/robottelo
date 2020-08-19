"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from wait_for import wait_for

from robottelo.config import settings
from robottelo.decorators import fixture
from robottelo.decorators import skipif
from robottelo.decorators import tier2
from robottelo.helpers import is_open
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option
from robottelo.virtwho_utils import virtwho


@fixture(scope='class')
def default_org():
    return entities.Organization().search(query={'search': 'name="Default Organization"'})[0]


@fixture()
def form_data(default_org):
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor_id': 'hostname',
        'hypervisor_type': virtwho.kubevirt.hypervisor_type,
        'organization_id': default_org.id,
        'filtering_mode': 'none',
        'satellite_url': settings.server.hostname,
        'kubeconfig': virtwho.kubevirt.hypervisor_config_file,
    }
    return form


@fixture()
def virtwho_config(form_data):
    return entities.VirtWhoConfig(**form_data).create()


@skipif(
    condition=(is_open('BZ:1735540')), reason='We have not supported kubevirt hypervisor yet',
)
class TestVirtWhoConfigforKubevirt:
    def _try_to_get_guest_bonus(self, hypervisor_name, sku):
        subscriptions = entities.Subscription().search(query={'search': sku})
        for item in subscriptions:
            item = item.read_json()
            if hypervisor_name.lower() in item['hypervisor']['name']:
                return item['id']

    def _get_guest_bonus(self, hypervisor_name, sku):
        vdc_id, time = wait_for(
            self._try_to_get_guest_bonus,
            func_args=(hypervisor_name, sku),
            fail_condition=None,
            timeout=15,
            delay=1,
        )
        return vdc_id

    @tier2
    def test_positive_deploy_configure_by_id(self, form_data, virtwho_config):
        """ Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: 97f776af-cbd0-4885-9a74-603a3bc01157

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        command = get_configure_command(virtwho_config.id)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor-type'], debug=True
        )
        virt_who_instance = (
            entities.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (hypervisor_name, f'product_id={virtwho.sku.vdc_physical} and type=NORMAL',),
            (guest_name, f'product_id={virtwho.sku.vdc_physical} and type=STACK_DERIVED',),
        ]
        for hostname, sku in hosts:
            if 'type=NORMAL' in sku:
                subscriptions = entities.Subscription().search(query={'search': sku})
                vdc_id = subscriptions[0].id
            if 'type=STACK_DERIVED' in sku:
                vdc_id = self._get_guest_bonus(hypervisor_name, sku)
            host, time = wait_for(
                entities.Host().search,
                func_args=(None, {'search': hostname}),
                fail_condition=[],
                timeout=5,
                delay=1,
            )
            entities.HostSubscription(host=host[0].id).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 1}]}
            )
            result = entities.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'
        virtwho_config.delete()
        assert not entities.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})

    @tier2
    def test_positive_deploy_configure_by_script(self, form_data, virtwho_config):
        """ Verify "GET /foreman_virt_who_configure/api/

        v2/configs/:id/deploy_script"

        :id: 77100dc7-644a-44a4-802a-2da562246cba

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        script = virtwho_config.deploy_script()
        hypervisor_name, guest_name = deploy_configure_by_script(
            script['virt_who_config_script'], form_data['hypervisor-type'], debug=True
        )
        virt_who_instance = (
            entities.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        hosts = [
            (hypervisor_name, f'product_id={virtwho.sku.vdc_physical} and type=NORMAL',),
            (guest_name, f'product_id={virtwho.sku.vdc_physical} and type=STACK_DERIVED',),
        ]
        for hostname, sku in hosts:
            if 'type=NORMAL' in sku:
                subscriptions = entities.Subscription().search(query={'search': sku})
                vdc_id = subscriptions[0].id
            if 'type=STACK_DERIVED' in sku:
                vdc_id = self._get_guest_bonus(hypervisor_name, sku)
            host, time = wait_for(
                entities.Host().search,
                func_args=(None, {'search': hostname}),
                fail_condition=[],
                timeout=5,
                delay=1,
            )
            entities.HostSubscription(host=host[0].id).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 1}]}
            )
            result = entities.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'
        virtwho_config.delete()
        assert not entities.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})

    @tier2
    def test_positive_hypervisor_id_option(self, form_data, virtwho_config):
        """ Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: c1ca38e8-6030-4a3f-8880-00ab3f29574a

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
