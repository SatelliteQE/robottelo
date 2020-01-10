"""Test for Virt-who related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import skip_if_not_set
from robottelo.test import APITestCase, settings
from robottelo.virtwho_utils import (
    deploy_configure_by_command,
    get_configure_command,
    get_configure_file,
    get_configure_option,
    get_hypervisor_info
)
from upgrade_tests import pre_upgrade, post_upgrade
from wait_for import wait_for


class scenario_positive_virt_who(APITestCase):
    """Virt-who config is intact post upgrade and verify virt-who update/delete

    :steps:

        1. In Preupgrade Satellite, create virt-who-config
        2. Upgrade the satellite to next/latest version
        3. Postupgrade, Verify the virt-who config is intact, update and delete

    :expectedresults: Virtwho config should be created, updated and deleted successfully.
    """
    @classmethod
    @skip_if_not_set('virtwho')
    def setUpClass(cls):
        cls.org = entities.Organization().search(
            query={'search': 'name="Default Organization"'}
        )[0]
        cls.satellite_url = settings.server.hostname
        cls.hypervisor_type = settings.virtwho.hypervisor_type
        cls.hypervisor_server = settings.virtwho.hypervisor_server
        cls.hypervisor_username = settings.virtwho.hypervisor_username
        cls.hypervisor_password = settings.virtwho.hypervisor_password
        cls.hypervisor_config_file = settings.virtwho.hypervisor_config_file
        cls.vdc_physical = settings.virtwho.sku_vdc_physical
        cls.vdc_virtual = settings.virtwho.sku_vdc_virtual

        cls.name = 'preupgrade_virt_who'

    def _make_virtwho_configure(self):
        args = {
            u'debug': 1,
            u'interval': '60',
            u'hypervisor_id': 'hostname',
            u'hypervisor_type': self.hypervisor_type,
            u'hypervisor_server': self.hypervisor_server,
            u'organization_id': self.org.id,
            u'filtering_mode': 'none',
            u'satellite_url': self.satellite_url,
        }
        if self.hypervisor_type == 'libvirt':
            args[u'hypervisor_username'] = self.hypervisor_username
        elif self.hypervisor_type == 'kubevirt':
            args[u'kubeconfig'] = self.hypervisor_config_file
        else:
            args[u'hypervisor_username'] = self.hypervisor_username
            args[u'hypervisor_password'] = self.hypervisor_password
        return args

    def _try_to_get_guest_bonus(self, hypervisor_name, sku):
        subscriptions = entities.Subscription().search(
            query={'search': sku})
        for item in subscriptions:
            item = item.read_json()
            if hypervisor_name.lower() in item['hypervisor']['name']:
                return item['id']

    def _get_guest_bonus(self, hypervisor_name, sku):
        vdc_id, time = wait_for(self._try_to_get_guest_bonus,
                                func_args=(hypervisor_name, sku),
                                fail_condition=None,
                                timeout=15,
                                delay=1)
        return vdc_id

    @pre_upgrade
    def test_pre_create_virt_who_configuration(self):
        """Create and deploy virt-who configuration

        :id: preupgrade-a36cbe89-47a2-422f-9881-0f86bea0e24e

        :steps: In Preupgrade Satellite, Create and deploy virt-who configuration.

        :expectedresults:
            1. Config can be created and deployed by command.
            2. No error msg in /var/log/rhsm/rhsm.log.
            3. Report is sent to satellite.
            4. Virtual sku can be generated and attached.
        """
        args = self._make_virtwho_configure()
        args.update({'name': self.name})
        vhd = entities.VirtWhoConfig(**args).create()
        self.assertEqual(vhd.status, 'unknown')
        command = get_configure_command(vhd.id)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, debug=True)
        self.assertEqual(
            entities.VirtWhoConfig().search(
                query={'search': 'name={}'.format(self.name)})[0].status,
            'ok')
        hosts = [
            (hypervisor_name, 'product_id={} and type=NORMAL'.format(
                self.vdc_physical)),
            (guest_name, 'product_id={} and type=STACK_DERIVED'.format(
                self.vdc_physical))]
        for hostname, sku in hosts:
            if 'type=NORMAL' in sku:
                subscriptions = entities.Subscription().search(
                    query={'search': sku})
                vdc_id = subscriptions[0].id
            if 'type=STACK_DERIVED' in sku:
                vdc_id = self._get_guest_bonus(hypervisor_name, sku)
            host, time = wait_for(entities.Host().search,
                                  func_args=(None, {'search': hostname}),
                                  fail_condition=[],
                                  timeout=5,
                                  delay=1)
            entities.HostSubscription(host=host[0].id).add_subscriptions(
                data={'subscriptions': [{
                    'id': vdc_id,
                    'quantity': 1}]})
            result = entities.Host().search(
                query={'search': hostname})[0].read_json()
            self.assertEqual(
                result['subscription_status_label'],
                'Fully entitled')

    @post_upgrade(depend_on=test_pre_create_virt_who_configuration)
    def test_post_crud_virt_who_configuration(self):
        """Virt-who config is intact post upgrade and update/delete config works

        :id: postupgrade-d7ae7b2b-3291-48c8-b412-cb54e444c7a4

        :steps:
            1. Post upgrade, Verify virt-who exists and has same status.
            2. Verify the connection of the guest on Content host.
            3. Verify the virt-who config-file exist.
            4. Update virt-who config with new name.
            5. Delete virt-who config.

        :expectedresults:
            1. virt-who config is intact post upgrade.
            2. the config and guest connection have the same status.
            2. virt-who config should update and delete successfully.
        """
        # virt-who config exist and check status
        vhd = entities.VirtWhoConfig().search(
            query={'search': 'name={}'.format(self.name)})[0]
        self.assertEqual(vhd.status, 'ok')

        # Vefify the connection of the guest on Content host
        hypervisor_name, guest_name = get_hypervisor_info()
        hosts = [hypervisor_name, guest_name]
        for hostname in hosts:
            result = entities.Host().search(
                query={'search': hostname})[0].read_json()
            self.assertEqual(
                result['subscription_status_label'],
                'Fully entitled')

        # Verify the virt-who config-file exist.
        config_file = get_configure_file(vhd.id)
        get_configure_option('hypervisor_id', config_file),

        # Update virt-who config after upgrade
        modify_name = gen_string('alpha')
        vhd.name = modify_name
        vhd.update(['name'])

        # Delete virt-who config
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(
            query={'search': 'name={}'.format(modify_name)}))
