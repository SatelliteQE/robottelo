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
from robottelo.cli.org import Org
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.decorators import fixture
from robottelo.decorators import tier2
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option
from robottelo.virtwho_utils import hypervisor_json_create
from robottelo.virtwho_utils import virtwho
from robottelo.virtwho_utils import virtwho_package_locked
from robottelo.virtwho_utils import VIRTWHO_SYSCONFIG


@fixture()
def form_data():
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor-id': 'hostname',
        'hypervisor-type': virtwho.esx.hypervisor_type,
        'hypervisor-server': virtwho.esx.hypervisor_server,
        'organization-id': 1,
        'filtering-mode': 'none',
        'satellite-url': settings.server.hostname,
        'hypervisor-username': virtwho.esx.hypervisor_username,
        'hypervisor-password': virtwho.esx.hypervisor_password,
    }
    return form


@fixture()
def virtwho_config(form_data):
    return VirtWhoConfig.create(form_data)['general-information']


class TestVirtWhoConfigforEsx:
    @tier2
    def test_positive_deploy_configure_by_id(self, form_data, virtwho_config):
        """ Verify " hammer virt-who-config deploy"

        :id: 1885dd56-e3f9-43a7-af27-e496967b6256

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        command = get_configure_command(virtwho_config['id'])
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor-type'], debug=True
        )
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={virtwho.sku.vdc_physical} and type=NORMAL',),
            (guest_name, f'product_id={virtwho.sku.vdc_physical} and type=STACK_DERIVED',),
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

        :id: 6aaffaeb-aaf2-42cf-b0dc-ca41a53d42a6

        :expectedresults: Config can be created, fetch and deploy

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        script = VirtWhoConfig.fetch({'id': virtwho_config['id']}, output_format='base')
        hypervisor_name, guest_name = deploy_configure_by_script(
            script, form_data['hypervisor-type'], debug=True
        )
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        hosts = [
            (hypervisor_name, f'product_id={virtwho.sku.vdc_physical} and type=NORMAL',),
            (guest_name, f'product_id={virtwho.sku.vdc_physical} and type=STACK_DERIVED',),
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

        :id: c98bc518-828c-49ba-a644-542db3190263

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
            deploy_configure_by_command(command, form_data['hypervisor-type'])
            assert get_configure_option('VIRTWHO_DEBUG', VIRTWHO_SYSCONFIG), value
        VirtWhoConfig.delete({'name': new_name})
        assert not VirtWhoConfig.exists(search=('name', new_name))

    @tier2
    def test_positive_interval_option(self, form_data, virtwho_config):
        """ Verify interval option by hammer virt-who-config update"

        :id: 5d558bca-534c-4bd4-b401-a0c362033c57

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
            deploy_configure_by_command(command, form_data['hypervisor-type'])
            assert get_configure_option('VIRTWHO_INTERVAL', VIRTWHO_SYSCONFIG) == value
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @tier2
    def test_positive_hypervisor_id_option(self, form_data, virtwho_config):
        """ Verify hypervisor_id option by hammer virt-who-config update"

        :id: 4e6bad11-2019-458b-a368-26ea95afc7f5

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

    @tier2
    def test_positive_filter_option(self, form_data, virtwho_config):
        """ Verify filter option by hammer virt-who-config update"

        :id: aaf45c5e-9504-47ce-8f25-b8073c2de036

        :expectedresults: filter and filter_hosts can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        regex = '.*redhat.com'
        whitelist = {'id': virtwho_config['id'], 'filtering-mode': 'whitelist', 'whitelist': regex}
        blacklist = {'id': virtwho_config['id'], 'filtering-mode': 'blacklist', 'blacklist': regex}
        # esx support filter-host-parents and exclude-host-parents options
        whitelist['filter-host-parents'] = regex
        blacklist['exclude-host-parents'] = regex
        config_file = get_configure_file(virtwho_config['id'])
        command = get_configure_command(virtwho_config['id'])
        # Update Whitelist and check the result
        VirtWhoConfig.update(whitelist)
        result = VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['connection']['filtering'] == 'Whitelist'
        assert result['connection']['filtered-hosts'] == regex
        assert result['connection']['filter-host-parents'] == regex
        deploy_configure_by_command(command, form_data['hypervisor-type'])
        assert get_configure_option('filter_hosts', config_file) == regex
        assert get_configure_option('filter_host_parents', config_file) == regex
        # Update Blacklist and check the result
        VirtWhoConfig.update(blacklist)
        result = VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['connection']['filtering'] == 'Blacklist'
        assert result['connection']['excluded-hosts'] == regex
        assert result['connection']['exclude-host-parents'] == regex
        deploy_configure_by_command(command, form_data['hypervisor-type'])
        assert get_configure_option('exclude_hosts', config_file) == regex
        assert get_configure_option('exclude_host_parents', config_file) == regex
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @tier2
    def test_positive_proxy_option(self, form_data, virtwho_config):
        """ Verify http_proxy option by hammer virt-who-config update"

        :id: 409d108e-e814-482b-93ed-09db89d21dda

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
        deploy_configure_by_command(command, form_data['hypervisor-type'])
        assert get_configure_option('http_proxy', VIRTWHO_SYSCONFIG) == http_proxy
        assert get_configure_option('NO_PROXY', VIRTWHO_SYSCONFIG) == no_proxy
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))

    @tier2
    def test_positive_rhsm_option(self, form_data, virtwho_config):
        """ Verify rhsm options in the configure file"

        :id: b5b93d4d-e780-41c0-9eaa-2407cc1dcc9b

        :expectedresults:
            rhsm_hostname, rhsm_prefix are ecpected
            rhsm_username is not a login account

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        config_file = get_configure_file(virtwho_config['id'])
        command = get_configure_command(virtwho_config['id'])
        deploy_configure_by_command(command, form_data['hypervisor-type'])
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
        org = Org.info({'name': DEFAULT_ORG})
        data = hypervisor_json_create(hypervisors=100, guests=10)
        url = f"https://{settings.server.hostname}/rhsm/hypervisors/{org['label']}"
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

        :id: 635ef99b-c5a3-4ac4-a0f1-09f7036d116e

        :expectedresults:
            virt-who packages can be installed
            the virt-who plugin can be deployed successfully

        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 1783987
        """
        virtwho_package_locked()
        command = get_configure_command(virtwho_config['id'])
        deploy_configure_by_command(command, form_data['hypervisor-type'])
        virt_who_instance = VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not VirtWhoConfig.exists(search=('name', form_data['name']))
