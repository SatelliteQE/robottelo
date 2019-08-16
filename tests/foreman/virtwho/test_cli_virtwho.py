"""Test class for Virtwho Configure CLI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: notautomated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import tier1
from robottelo.test import CLITestCase
from robottelo.config import settings
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.cli.subscription import Subscription
from robottelo.cli.host import Host
from robottelo.cli.user import User
from robottelo.constants import DEFAULT_ORG
from fauxfactory import gen_string
from .utils import (
    deploy_configure_by_command,
    deploy_configure_by_script,
    get_configure_id,
    get_configure_file,
    get_configure_option,
    get_configure_command,
    VIRTWHO_SYSCONFIG,
)


class VirtWhoConfigTestCase(CLITestCase):

    @classmethod
    def setUpClass(cls):
        super(VirtWhoConfigTestCase, cls).setUpClass()
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
            u'hypervisor-id': 'hostname',
            u'hypervisor-type': self.hypervisor_type,
            u'hypervisor-server': self.hypervisor_server,
            u'organization-id': 1,
            u'filtering-mode': 'none',
            u'satellite-url': self.satellite_url,
        }
        if self.hypervisor_type == 'libvirt':
            args[u'hypervisor-username'] = self.hypervisor_username
        elif self.hypervisor_type == 'kubevirt':
            args[u'kubeconfig'] = self.hypervisor_config_file
        else:
            args['hypervisor-username'] = self.hypervisor_username
            args['hypervisor-password'] = self.hypervisor_password
        return args

    @tier1
    def test_positive_deploy_configure_by_id(self):
        """ Verify " hammer virt-who-config deploy"

        :id: 19ffe76e-7e3d-48c7-b846-10a83afe0f3e

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = VirtWhoConfig.create(args)['general-information']
        self.assertEquals(vhd['status'], 'No Report Yet')
        command = get_configure_command(vhd['id'])
        hypervisor_name, guest_name = deploy_configure_by_command(command, debug=True)
        self.assertEquals(
            VirtWhoConfig.info({'id': vhd['id']})['general-information']['status'], 'OK')
        hosts = [
            (hypervisor_name, 'product_id={}'.format(self.vdc_physical)),
            (guest_name, 'type=STACK_DERIVED')]
        for hostname, sku in hosts:
            host = Host.list({'search': hostname})[0]
            vdc = Subscription.list({
                'organization': DEFAULT_ORG,
                'search': sku,
            })[0]
            result = Host.subscription_attach({
                'host-id': host['id'],
                'subscription-id': vdc['id']
            })
            self.assertTrue('attached to the host successfully' in '\n'.join(result))
        VirtWhoConfig.delete({'name': name})
        self.assertFalse(VirtWhoConfig.exists(search=('name', name)))

    @tier1
    def test_positive_deploy_configure_by_script(self):
        """ Verify " hammer virt-who-config fetch"

        :id: ef0f1e33-7084-4d0e-95f1-d3080dfbb4cc

        :expectedresults: Config can be created, fetch and deploy

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = VirtWhoConfig.create(args)['general-information']
        self.assertEquals(vhd['status'], 'No Report Yet')
        script = VirtWhoConfig.fetch({'id': vhd['id']}, output_format='plain')
        hypervisor_name, guest_name = deploy_configure_by_script(script, debug=True)
        self.assertEquals(
            VirtWhoConfig.info({'id': vhd['id']})['general-information']['status'], 'OK')
        hosts = [
            (hypervisor_name, 'product_id={}'.format(self.vdc_physical)),
            (guest_name, 'type=STACK_DERIVED')]
        for hostname, sku in hosts:
            host = Host.list({'search': hostname})[0]
            vdc = Subscription.list({
                'organization': DEFAULT_ORG,
                'search': sku,
            })[0]
            result = Host.subscription_attach({
                'host-id': host['id'],
                'subscription-id': vdc['id']
            })
            self.assertTrue('attached to the host successfully' in '\n'.join(result))
        VirtWhoConfig.delete({'name': name})
        self.assertFalse(VirtWhoConfig.exists(search=('name', name)))

    @tier1
    def test_positive_debug_option(self):
        """ Verify debug option by hammer virt-who-config update"

        :id: 27ae5606-16a8-4b4a-9596-e0fa97e81c0d

        :expectedresults: debug option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        new_name = gen_string('alphanumeric')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = VirtWhoConfig.create(args)['general-information']
        self.assertEquals(vhd['name'], name)
        VirtWhoConfig.update({'id': vhd['id'], 'new-name': new_name})
        self.assertEquals(
            VirtWhoConfig.info({'id': vhd['id']})['general-information']['name'],
            new_name)
        options = {'true': '1', 'false': '0', 'yes': '1', 'no': '0'}
        for key, value in sorted(options.items(), key=lambda item: item[0]):
            VirtWhoConfig.update({'id': vhd['id'], 'debug': key})
            command = get_configure_command(vhd['id'])
            deploy_configure_by_command(command)
            self.assertEquals(
                get_configure_option('VIRTWHO_DEBUG', VIRTWHO_SYSCONFIG), value)
        VirtWhoConfig.delete({'name': new_name})
        self.assertFalse(VirtWhoConfig.exists(search=('name', name)))

    @tier1
    def test_positive_interval_option(self):
        """ Verify interval option by hammer virt-who-config update"

        :id: cf754c07-99d2-4758-b9dc-ab47443855b3

        :expectedresults: interval option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = VirtWhoConfig.create(args)['general-information']
        options = {
            '60': '3600',
            '120': '7200',
            '240': '14400',
            '480': '28800',
            '720': '43200',
            '1440': '86400',
            '2880': '172800',
            '4320': '259200',
        }
        for key, value in sorted(options.items(), key=lambda item: int(item[0])):
            VirtWhoConfig.update({'id': vhd['id'], 'interval': key})
            command = get_configure_command(vhd['id'])
            deploy_configure_by_command(command)
            self.assertEquals(
                get_configure_option('VIRTWHO_INTERVAL', VIRTWHO_SYSCONFIG), value)
        VirtWhoConfig.delete({'name': name})
        self.assertFalse(VirtWhoConfig.exists(search=('name', name)))

    @tier1
    def test_positive_hypervisor_id_option(self):
        """ Verify hypervisor_id option by hammer virt-who-config update"

        :id: eae7e767-8a71-424c-87da-475c91ac2ea1

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = VirtWhoConfig.create(args)['general-information']
        values = ['uuid', 'hwuuid', 'hostname']
        for value in values:
            VirtWhoConfig.update({'id': vhd['id'], 'hypervisor-id': value})
            result = VirtWhoConfig.info({'id': vhd['id']})
            self.assertEquals(result['connection']['hypervisor-id'], value)
            config_file = get_configure_file(vhd['id'])
            command = get_configure_command(vhd['id'])
            deploy_configure_by_command(command)
            self.assertEquals(
                get_configure_option('hypervisor_id', config_file), value)
        VirtWhoConfig.delete({'name': name})
        self.assertFalse(VirtWhoConfig.exists(search=('name', name)))

    @tier1
    def test_positive_filter_option(self):
        """ Verify filter option by hammer virt-who-config update"

        :id: f46e4aa8-c325-4281-8744-f85e819e68c1

        :expectedresults: filter and filter_hosts can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = VirtWhoConfig.create(args)['general-information']
        regex = '.*redhat.com'
        whitelist = {
            'id': vhd['id'],
            'filtering-mode': 'whitelist',
            'whitelist': regex,
        }
        VirtWhoConfig.update(whitelist)
        result = VirtWhoConfig.info({'id': vhd['id']})
        self.assertEquals(result['connection']['filtering'], 'Whitelist')
        self.assertEquals(result['connection']['filtered-hosts'], regex)
        config_file = get_configure_file(vhd['id'])
        command = get_configure_command(vhd['id'])
        deploy_configure_by_command(command)
        self.assertEquals(get_configure_option('filter_hosts', config_file), regex)
        VirtWhoConfig.delete({'name': name})
        self.assertFalse(VirtWhoConfig.exists(search=('name', name)))

    @tier1
    def test_positive_proxy_option(self):
        """ Verify http_proxy option by hammer virt-who-config update"

        :id: becd00f7-e140-481a-9249-8a3082297a4b

        :expectedresults: http_proxy and no_proxy option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = VirtWhoConfig.create(args)['general-information']
        http_proxy = 'test.rexample.com:3128'
        no_proxy = 'test.satellite.com'
        VirtWhoConfig.update({
            'id': vhd['id'],
            'proxy': http_proxy,
            'no-proxy': no_proxy,
        })
        result = VirtWhoConfig.info({'id': vhd['id']})
        self.assertEquals(result['connection']['http-proxy'], http_proxy)
        self.assertEquals(result['connection']['ignore-proxy'], no_proxy)
        command = get_configure_command(vhd['id'])
        deploy_configure_by_command(command)
        self.assertEquals(
            get_configure_option('http_proxy', VIRTWHO_SYSCONFIG), http_proxy)
        self.assertEquals(
            get_configure_option('NO_PROXY', VIRTWHO_SYSCONFIG), no_proxy)
        VirtWhoConfig.delete({'name': name})
        self.assertFalse(VirtWhoConfig.exists(search=('name', name)))

    @tier1
    def test_positive_rhsm_option(self):
        """ Verify rhsm options in the configure file"

        :id: 5155d145-0a8d-4443-81d3-6fb7cef0533b

        :expectedresults:
            rhsm_hostname, rhsm_prefix are ecpected
            rhsm_username is not a login account

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = VirtWhoConfig.create(args)['general-information']
        config_file = get_configure_file(vhd['id'])
        command = get_configure_command(vhd['id'])
        deploy_configure_by_command(command)
        rhsm_username = get_configure_option('rhsm_username', config_file)
        self.assertFalse(User.exists(search=('login', rhsm_username)))
        self.assertEquals(
            get_configure_option('rhsm_hostname', config_file), self.satellite_url)
        self.assertEquals(
            get_configure_option('rhsm_prefix', config_file), '/rhsm')
        VirtWhoConfig.delete({'name': name})
        self.assertFalse(VirtWhoConfig.exists(search=('name', name)))
