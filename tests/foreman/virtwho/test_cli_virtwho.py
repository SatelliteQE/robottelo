"""Test class for Virtwho Configure CLI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re

import requests
from fauxfactory import gen_string

from robottelo.api.utils import wait_for_tasks
from robottelo.cli.host import Host
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.decorators import fixture
from robottelo.decorators import skipif
from robottelo.decorators import tier2
from robottelo.utils.issue_handlers import is_open
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option
from robottelo.virtwho_utils import hypervisor_json_create
from robottelo.virtwho_utils import virtwho_package_locked
from robottelo.virtwho_utils import VIRTWHO_SYSCONFIG


@fixture()
def form_data():
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor-id': 'hostname',
        'hypervisor-type': settings.virtwho.hypervisor_type,
        'hypervisor-server': settings.virtwho.hypervisor_server,
        'organization-id': 1,
        'filtering-mode': 'none',
        'satellite-url': settings.server.hostname,
    }
    if settings.virtwho.hypervisor_type == 'libvirt':
        form['hypervisor-username'] = settings.virtwho.hypervisor_username
    elif settings.virtwho.hypervisor_type == 'kubevirt':
        form['kubeconfig'] = settings.virtwho.hypervisor_config_file
    else:
        form['hypervisor-username'] = settings.virtwho.hypervisor_username
        form['hypervisor-password'] = settings.virtwho.hypervisor_password
    return form


@fixture()
def virtwho_config(form_data):
    return VirtWhoConfig.create(form_data)['general-information']


@skipif(
    condition=(settings.virtwho.hypervisor_type == 'kubevirt' and is_open('BZ:1735540')),
    reason='We have not supported kubevirt hypervisor yet',
)
class TestVirtWhoConfigCLICases:
    @tier2
    def test_positive_deploy_configure_by_id(self, form_data, virtwho_config):
        """ Verify " hammer virt-who-config deploy"

        :id: 19ffe76e-7e3d-48c7-b846-10a83afe0f3e

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        command = get_configure_command(virtwho_config['id'])
        hypervisor_name, guest_name = deploy_configure_by_command(command, debug=True)
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={settings.virtwho.sku_vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={settings.virtwho.sku_vdc_physical} and type=STACK_DERIVED'),
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

    @tier2
    def test_positive_deploy_configure_by_script(self, form_data, virtwho_config):
        """ Verify " hammer virt-who-config fetch"

        :id: ef0f1e33-7084-4d0e-95f1-d3080dfbb4cc

        :expectedresults: Config can be created, fetch and deploy

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        script = VirtWhoConfig.fetch({'id': virtwho_config['id']}, output_format='base')
        hypervisor_name, guest_name = deploy_configure_by_script(script, debug=True)
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={settings.virtwho.sku_vdc_physical} and type=NORMAL'),
            (guest_name, f'product_id={settings.virtwho.sku_vdc_physical} and type=STACK_DERIVED'),
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

    @tier2
    def test_positive_debug_option(self, form_data, virtwho_config):
        """ Verify debug option by hammer virt-who-config update"

        :id: 27ae5606-16a8-4b4a-9596-e0fa97e81c0d

        :expectedresults: debug option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        assert virtwho_config['name'] == form_data['name']
        new_name = gen_string('alphanumeric')
        VirtWhoConfig.update({'id': virtwho_config['id'], 'new-name': new_name})
        virt_who_instance_name = VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['name']
        assert virt_who_instance_name == new_name
        options = {'true': '1', 'false': '0', 'yes': '1', 'no': '0'}
        for key, value in sorted(options.items(), key=lambda item: item[0]):
            VirtWhoConfig.update({'id': virtwho_config['id'], 'debug': key})
            command = get_configure_command(virtwho_config['id'])
            deploy_configure_by_command(command)
            assert get_configure_option('VIRTWHO_DEBUG', VIRTWHO_SYSCONFIG), value
        VirtWhoConfig.delete({'name': new_name})
        assert not VirtWhoConfig.exists(search=('name', new_name))

    @tier2
    def test_positive_interval_option(self, form_data, virtwho_config):
        """ Verify interval option by hammer virt-who-config update"

        :id: cf754c07-99d2-4758-b9dc-ab47443855b3

        :expectedresults: interval option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
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
            VirtWhoConfig.update({'id': virtwho_config['id'], 'interval': key})
            command = get_configure_command(virtwho_config['id'])
            deploy_configure_by_command(command)
            assert get_configure_option('VIRTWHO_INTERVAL', VIRTWHO_SYSCONFIG) == value
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @tier2
    def test_positive_hypervisor_id_option(self, form_data, virtwho_config):
        """ Verify hypervisor_id option by hammer virt-who-config update"

        :id: eae7e767-8a71-424c-87da-475c91ac2ea1

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        values = ['uuid', 'hostname']
        if settings.virtwho.hypervisor_type in ('esx', 'rhevm'):
            values.append('hwuuid')
        for value in values:
            VirtWhoConfig.update({'id': virtwho_config['id'], 'hypervisor-id': value})
            result = VirtWhoConfig.info({'id': virtwho_config['id']})
            assert result['connection']['hypervisor-id'] == value
            config_file = get_configure_file(virtwho_config['id'])
            command = get_configure_command(virtwho_config['id'])
            deploy_configure_by_command(command)
            assert get_configure_option('hypervisor_id', config_file) == value
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @tier2
    def test_positive_filter_option(self, form_data, virtwho_config):
        """ Verify filter option by hammer virt-who-config update"

        :id: f46e4aa8-c325-4281-8744-f85e819e68c1

        :expectedresults: filter and filter_hosts can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        regex = '.*redhat.com'
        whitelist = {'id': virtwho_config['id'], 'filtering-mode': 'whitelist', 'whitelist': regex}
        blacklist = {'id': virtwho_config['id'], 'filtering-mode': 'blacklist', 'blacklist': regex}
        if settings.virtwho.hypervisor_type == 'esx':
            whitelist['filter-host-parents'] = regex
            blacklist['exclude-host-parents'] = regex
        config_file = get_configure_file(virtwho_config['id'])
        command = get_configure_command(virtwho_config['id'])
        # Update Whitelist and check the result
        VirtWhoConfig.update(whitelist)
        result = VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['connection']['filtering'] == 'Whitelist'
        assert result['connection']['filtered-hosts'] == regex
        if settings.virtwho.hypervisor_type == 'esx':
            assert result['connection']['filter-host-parents'] == regex
        deploy_configure_by_command(command)
        assert get_configure_option('filter_hosts', config_file) == regex
        if settings.virtwho.hypervisor_type == 'esx':
            assert get_configure_option('filter_host_parents', config_file) == regex
        # Update Blacklist and check the result
        VirtWhoConfig.update(blacklist)
        result = VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['connection']['filtering'] == 'Blacklist'
        assert result['connection']['excluded-hosts'] == regex
        if settings.virtwho.hypervisor_type == 'esx':
            assert result['connection']['exclude-host-parents'] == regex
        deploy_configure_by_command(command)
        assert get_configure_option('exclude_hosts', config_file) == regex
        if settings.virtwho.hypervisor_type == 'esx':
            assert get_configure_option('exclude_host_parents', config_file) == regex
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @tier2
    def test_positive_proxy_option(self, form_data, virtwho_config):
        """ Verify http_proxy option by hammer virt-who-config update"

        :id: becd00f7-e140-481a-9249-8a3082297a4b

        :expectedresults: http_proxy and no_proxy option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        http_proxy = 'test.example.com:3128'
        no_proxy = 'test.satellite.com'
        VirtWhoConfig.update(
            {'id': virtwho_config['id'], 'proxy': http_proxy, 'no-proxy': no_proxy}
        )
        result = VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['connection']['http-proxy'] == http_proxy
        assert result['connection']['ignore-proxy'] == no_proxy
        command = get_configure_command(virtwho_config['id'])
        deploy_configure_by_command(command)
        assert get_configure_option('http_proxy', VIRTWHO_SYSCONFIG) == http_proxy
        assert get_configure_option('NO_PROXY', VIRTWHO_SYSCONFIG) == no_proxy
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @tier2
    def test_positive_rhsm_option(self, form_data, virtwho_config):
        """ Verify rhsm options in the configure file"

        :id: 5155d145-0a8d-4443-81d3-6fb7cef0533b

        :expectedresults:
            rhsm_hostname, rhsm_prefix are ecpected
            rhsm_username is not a login account

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        config_file = get_configure_file(virtwho_config['id'])
        command = get_configure_command(virtwho_config['id'])
        deploy_configure_by_command(command)
        rhsm_username = get_configure_option('rhsm_username', config_file)
        assert not User.exists(search=('login', rhsm_username))
        assert get_configure_option('rhsm_hostname', config_file) == settings.server.hostname
        assert get_configure_option('rhsm_prefix', config_file) == '/rhsm'
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @tier2
    def test_positive_post_hypervisors(self):
        """ Post large json file to /rhsm/hypervisors"

        :id: e344c9d2-3538-4432-9a74-b025e9ef852d

        :expectedresults:
            hypervisor/guest json can be posted and the task is success status

        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 1637042, 1769680
        """
        data = hypervisor_json_create(hypervisors=100, guests=10)
        owner = "owner=Default_Organization&env=Library"
        url = f'https://{settings.server.hostname}/rhsm/hypervisors?{owner}'
        auth = (settings.server.admin_username, settings.server.admin_password)
        result = requests.post(url, auth=auth, verify=False, json=data)
        if result.status_code != 200:
            if "foreman_tasks_sync_task_timeout" in result.text:
                task_id = re.findall('waiting for task (.*?) to finish', result.text)[-1]
                wait_for_tasks(search_query=f'id = {task_id}', max_tries=10)
            else:
                assert result.status_code == 200

    @tier2
    def test_positive_foreman_packages_protection(self, form_data, virtwho_config):
        """foreman-protector should allow virt-who to be installed

        :id: 73dc895f-50b8-4de5-91de-ea55da935fe5

        :expectedresults:
            virt-who packages can be installed
            the virt-who plugin can be deployed successfully

        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 1783987
        """
        virtwho_package_locked()
        command = get_configure_command(virtwho_config['id'])
        deploy_configure_by_command(command)
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))
