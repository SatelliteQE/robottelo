"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: notautomated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from fauxfactory import gen_string
from robottelo.test import APITestCase
from robottelo.config import settings
from robottelo.decorators import tier1

from .utils import (
    deploy_configure_by_command,
    get_configure_command,
)


class VirtWhoConfigApiTestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(VirtWhoConfigApiTestCase, cls).setUpClass()
        org = entities.Organization().search(
            query={'search': 'name="Default Organization"'}
        )[0]
        cls.org = org.read()
        cls.satellite_url = settings.server.hostname
        cls.hypervisor_type = settings.virtwho.hypervisor_type
        cls.hypervisor_server = settings.virtwho.hypervisor_server
        cls.hypervisor_username = settings.virtwho.hypervisor_username
        cls.hypervisor_password = settings.virtwho.hypervisor_password
        cls.hypervisor_config_file = settings.virtwho.hypervisor_config_file
        cls.vdc_physical = settings.virtwho.sku_vdc_physical
        cls.vdc_virtual = settings.virtwho.sku_vdc_virtual

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

    @tier1
    def test_positive_deploy_configure_id(self):
        """ Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: b469822f-8b1f-437b-8193-6723ad3648dd

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = entities.VirtWhoConfig(**args).create()
        self.assertEqual(vhd.status, 'unknown')
        command = get_configure_command(vhd.id)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, debug=True)
        status = entities.VirtWhoConfig().search(
            query={'search': 'name={}'.format(name)}
        )[0].status
        self.assertEqual(status, 'ok')
        hosts = [
            (hypervisor_name, 'product_id={}'.format(self.vdc_physical)),
            (guest_name, 'type = STACK_DERIVED')]
        for hostname, sku in hosts:
            host = entities.Host().search(
                query={'search': "{0}".format(hostname)})[0]
            product_subscription = entities.Subscription().search(
                query={'search': '{0}'.format(sku)})[0]
            entities.HostSubscription(host=host.id).add_subscriptions(
                data={'subscriptions': [{
                              'id': product_subscription.id,
                              'quantity': 1}]})
            result = entities.Host().search(
                query={'search': '{0}'.format(hypervisor_name)})[0].read_json()
            self.assertEqual(
                result['subscription_status_label'],
                'Fully entitled')
        vhd.delete()
        self.assertEqual(entities.VirtWhoConfig().search(
            query={'search': 'name={}'.format(name)}), [])
