"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: notautomated

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
from robottelo.decorators import skip_if
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier2
from robottelo.helpers import is_open
from robottelo.test import APITestCase
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option
from robottelo.virtwho_utils import VIRTWHO_SYSCONFIG


class VirtWhoConfigApiTestCase(APITestCase):
    @classmethod
    @skip_if_not_set('virtwho')
    @skip_if(settings.virtwho.hypervisor_type == 'kubevirt' and is_open('BZ:1735540'))
    def setUpClass(cls):
        super(VirtWhoConfigApiTestCase, cls).setUpClass()
        cls.org = entities.Organization().search(query={'search': 'name="Default Organization"'})[
            0
        ]
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
            'debug': 1,
            'interval': '60',
            'hypervisor_id': 'hostname',
            'hypervisor_type': self.hypervisor_type,
            'hypervisor_server': self.hypervisor_server,
            'organization_id': self.org.id,
            'filtering_mode': 'none',
            'satellite_url': self.satellite_url,
        }
        if self.hypervisor_type == 'libvirt':
            args['hypervisor_username'] = self.hypervisor_username
        elif self.hypervisor_type == 'kubevirt':
            args['kubeconfig'] = self.hypervisor_config_file
        else:
            args['hypervisor_username'] = self.hypervisor_username
            args['hypervisor_password'] = self.hypervisor_password
        return args

    def _try_to_get_guest_bonus(self, hypervisor_name, sku):
        subscriptions = entities.Subscription().search(query={'search': '{0}'.format(sku)})
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
    def test_positive_deploy_configure_by_id(self):
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
        hypervisor_name, guest_name = deploy_configure_by_command(command, debug=True)
        self.assertEqual(
            entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)})[0].status,
            'ok',
        )
        hosts = [
            (hypervisor_name, 'product_id={} and type=NORMAL'.format(self.vdc_physical)),
            (guest_name, 'product_id={} and type=STACK_DERIVED'.format(self.vdc_physical)),
        ]
        for hostname, sku in hosts:
            if 'type=NORMAL' in sku:
                subscriptions = entities.Subscription().search(query={'search': '{0}'.format(sku)})
                vdc_id = subscriptions[0].id
            if 'type=STACK_DERIVED' in sku:
                vdc_id = self._get_guest_bonus(hypervisor_name, sku)
            host, time = wait_for(
                entities.Host().search,
                func_args=(None, {'search': "{0}".format(hostname)}),
                fail_condition=[],
                timeout=5,
                delay=1,
            )
            entities.HostSubscription(host=host[0].id).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 1}]}
            )
            result = (
                entities.Host().search(query={'search': '{0}'.format(hostname)})[0].read_json()
            )
            self.assertEqual(result['subscription_status_label'], 'Fully entitled')
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)}))

    @tier2
    def test_positive_deploy_configure_by_script(self):
        """ Verify "GET /foreman_virt_who_configure/api/

        v2/configs/:id/deploy_script"

        :id: bb673b27-c258-4517-8fb9-436a4b51ba9d

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = entities.VirtWhoConfig(**args).create()
        self.assertEqual(vhd.status, 'unknown')
        script = vhd.deploy_script()
        hypervisor_name, guest_name = deploy_configure_by_script(
            script['virt_who_config_script'], debug=True
        )
        self.assertEqual(
            entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)})[0].status,
            'ok',
        )
        hosts = [
            (hypervisor_name, 'product_id={} and type=NORMAL'.format(self.vdc_physical)),
            (guest_name, 'product_id={} and type=STACK_DERIVED'.format(self.vdc_physical)),
        ]
        for hostname, sku in hosts:
            if 'type=NORMAL' in sku:
                subscriptions = entities.Subscription().search(query={'search': '{0}'.format(sku)})
                vdc_id = subscriptions[0].id
            if 'type=STACK_DERIVED' in sku:
                vdc_id = self._get_guest_bonus(hypervisor_name, sku)
            host, time = wait_for(
                entities.Host().search,
                func_args=(None, {'search': "{0}".format(hostname)}),
                fail_condition=[],
                timeout=5,
                delay=1,
            )
            entities.HostSubscription(host=host[0].id).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 1}]}
            )
            result = (
                entities.Host().search(query={'search': '{0}'.format(hostname)})[0].read_json()
            )
            self.assertEqual(result['subscription_status_label'], 'Fully entitled')
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)}))

    @tier2
    def test_positive_debug_option(self):
        """ Verify debug option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 75a20b8c-bed8-4c55-b291-14bca6cac364

        :expectedresults: debug option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = entities.VirtWhoConfig(**args).create()
        options = {'true': '1', 'false': '0', '1': '1', '0': '0'}
        for key, value in sorted(options.items(), key=lambda item: item[0]):
            vhd.debug = key
            vhd.update(['debug'])
            command = get_configure_command(vhd.id)
            deploy_configure_by_command(command)
            self.assertEqual(get_configure_option('VIRTWHO_DEBUG', VIRTWHO_SYSCONFIG), value)
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)}))

    @tier2
    def test_positive_interval_option(self):
        """ Verify interval option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 9a96c25b-fddd-47c3-aa9f-3b6dc298d068

        :expectedresults: interval option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = entities.VirtWhoConfig(**args).create()
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
            vhd.interval = key
            vhd.update(['interval'])
            command = get_configure_command(vhd.id)
            deploy_configure_by_command(command)
            self.assertEqual(get_configure_option('VIRTWHO_INTERVAL', VIRTWHO_SYSCONFIG), value)
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)}))

    @tier2
    def test_positive_hypervisor_id_option(self):
        """ Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 9aa17bbc-e417-473a-831c-4d87781f41d8

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = entities.VirtWhoConfig(**args).create()
        values = ['uuid', 'hostname']
        if self.hypervisor_type in ('esx', 'rhevm'):
            values.append('hwuuid')
        for value in values:
            vhd.hypervisor_id = value
            vhd.update(['hypervisor_id'])
            config_file = get_configure_file(vhd.id)
            command = get_configure_command(vhd.id)
            deploy_configure_by_command(command)
            self.assertEqual(get_configure_option('hypervisor_id', config_file), value)
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)}))

    @tier2
    def test_positive_filter_option(self):
        """ Verify filter option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 89cc1134-69d9-4da8-9ba9-a296c17f4f16

        :expectedresults: filter and filter_hosts can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = entities.VirtWhoConfig(**args).create()
        whitelist = {'filtering_mode': '1', 'whitelist': '.*redhat.com'}
        blacklist = {'filtering_mode': '2', 'blacklist': '.*redhat.com'}
        if self.hypervisor_type == 'esx':
            whitelist['filter_host_parents'] = '.*redhat.com'
            blacklist['exclude_host_parents'] = '.*redhat.com'
        # Update Whitelist and check the result
        vhd.filtering_mode = whitelist['filtering_mode']
        vhd.whitelist = whitelist['whitelist']
        if self.hypervisor_type == 'esx':
            vhd.filter_host_parents = whitelist['filter_host_parents']
        vhd.update(whitelist.keys())
        config_file = get_configure_file(vhd.id)
        command = get_configure_command(vhd.id)
        deploy_configure_by_command(command)
        self.assertEqual(get_configure_option('filter_hosts', config_file), whitelist['whitelist'])
        if self.hypervisor_type == 'esx':
            self.assertEqual(
                get_configure_option('filter_host_parents', config_file),
                whitelist['filter_host_parents'],
            )
        # Update Blacklist and check the result
        vhd.filtering_mode = blacklist['filtering_mode']
        vhd.blacklist = blacklist['blacklist']
        if self.hypervisor_type == 'esx':
            vhd.exclude_host_parents = blacklist['exclude_host_parents']
        vhd.update(blacklist.keys())
        config_file = get_configure_file(vhd.id)
        command = get_configure_command(vhd.id)
        deploy_configure_by_command(command)
        self.assertEqual(
            get_configure_option('exclude_hosts', config_file), blacklist['blacklist']
        )
        if self.hypervisor_type == 'esx':
            self.assertEqual(
                get_configure_option('exclude_host_parents', config_file),
                blacklist['exclude_host_parents'],
            )
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)}))

    @tier2
    def test_positive_proxy_option(self):
        """ Verify http_proxy option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id""

        :id: 11352fee-5e00-4b24-9515-30a790685ede

        :expectedresults: http_proxy and no_proxy option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = entities.VirtWhoConfig(**args).create()
        command = get_configure_command(vhd.id)
        deploy_configure_by_command(command)
        self.assertEqual(get_configure_option('NO_PROXY', VIRTWHO_SYSCONFIG), '*')
        proxy = 'test.example.com:3128'
        no_proxy = 'test.satellite.com'
        vhd.proxy = proxy
        vhd.no_proxy = no_proxy
        vhd.update(['proxy', 'no_proxy'])
        command = get_configure_command(vhd.id)
        deploy_configure_by_command(command)
        self.assertEqual(get_configure_option('http_proxy', VIRTWHO_SYSCONFIG), proxy)
        self.assertEqual(get_configure_option('NO_PROXY', VIRTWHO_SYSCONFIG), no_proxy)
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)}))

    @tier2
    def test_positive_configure_organization_list(self):
        """ Verify "GET /foreman_virt_who_configure/

        api/v2/organizations/:organization_id/configs"

        :id: 7434a875-e96a-40bd-9652-83d0805997a5

        :expectedresults: Config can be searched in org list

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        args = self._make_virtwho_configure()
        args.update({'name': name})
        vhd = entities.VirtWhoConfig(**args).create()
        command = get_configure_command(vhd.id)
        deploy_configure_by_command(command)
        search_result = vhd.get_organization_configs(data={'per_page': 1000})
        self.assertTrue([item for item in search_result['results'] if item['name'] == name])
        vhd.delete()
        self.assertFalse(entities.VirtWhoConfig().search(query={'search': 'name={}'.format(name)}))
