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
import re

import pytest
import requests
from fauxfactory import gen_string

from robottelo.api.utils import wait_for_tasks
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.virtwho_utils import create_http_proxy
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_command_check
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import ETC_VIRTWHO_CONFIG
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_option
from robottelo.virtwho_utils import hypervisor_json_create
from robottelo.virtwho_utils import virtwho_package_locked


@pytest.fixture()
def form_data(target_sat, default_org):
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor-id': 'hostname',
        'hypervisor-type': settings.virtwho.esx.hypervisor_type,
        'hypervisor-server': settings.virtwho.esx.hypervisor_server,
        'organization-id': default_org.id,
        'filtering-mode': 'none',
        'satellite-url': target_sat.hostname,
        'hypervisor-username': settings.virtwho.esx.hypervisor_username,
        'hypervisor-password': settings.virtwho.esx.hypervisor_password,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data, target_sat):
    return target_sat.cli.VirtWhoConfig.create(form_data)['general-information']


class TestVirtWhoConfigforEsx:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify " hammer virt-who-config deploy"

        :id: 1885dd56-e3f9-43a7-af27-e496967b6256

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        command = get_configure_command(virtwho_config['id'], default_org.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data['hypervisor-type'], debug=True, org=default_org.label
        )
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        hosts = [
            (
                hypervisor_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL',
            ),
            (
                guest_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED',
            ),
        ]
        for hostname, sku in hosts:
            host = target_sat.cli.Host.list({'search': hostname})[0]
            subscriptions = target_sat.cli.Subscription.list(
                {'organization': default_org.name, 'search': sku}
            )
            vdc_id = subscriptions[0]['id']
            if 'type=STACK_DERIVED' in sku:
                for item in subscriptions:
                    if hypervisor_name.lower() in item['type']:
                        vdc_id = item['id']
                        break
            result = target_sat.cli.Host.subscription_attach(
                {'host-id': host['id'], 'subscription-id': vdc_id}
            )
            assert result.strip() == 'Subscription attached to the host successfully.'
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_deploy_configure_by_script(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify " hammer virt-who-config fetch"

        :id: 6aaffaeb-aaf2-42cf-b0dc-ca41a53d42a6

        :expectedresults: Config can be created, fetch and deploy

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        script = target_sat.cli.VirtWhoConfig.fetch(
            {'id': virtwho_config['id']}, output_format='base'
        )
        hypervisor_name, guest_name = deploy_configure_by_script(
            script, form_data['hypervisor-type'], debug=True, org=default_org.label
        )
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        hosts = [
            (
                hypervisor_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=NORMAL',
            ),
            (
                guest_name,
                f'product_id={settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED',
            ),
        ]
        for hostname, sku in hosts:
            host = target_sat.cli.Host.list({'search': hostname})[0]
            subscriptions = target_sat.cli.Subscription.list(
                {'organization': default_org.name, 'search': sku}
            )
            vdc_id = subscriptions[0]['id']
            if 'type=STACK_DERIVED' in sku:
                for item in subscriptions:
                    if hypervisor_name.lower() in item['type']:
                        vdc_id = item['id']
                        break
            result = target_sat.cli.Host.subscription_attach(
                {'host-id': host['id'], 'subscription-id': vdc_id}
            )
            assert result.strip() == 'Subscription attached to the host successfully.'
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_debug_option(self, default_org, form_data, virtwho_config, target_sat):
        """Verify debug option by hammer virt-who-config update"

        :id: c98bc518-828c-49ba-a644-542db3190263

        :expectedresults: debug option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        assert virtwho_config['name'] == form_data['name']
        new_name = gen_string('alphanumeric')
        target_sat.cli.VirtWhoConfig.update({'id': virtwho_config['id'], 'new-name': new_name})
        virt_who_instance_name = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['name']
        assert virt_who_instance_name == new_name
        options = {'true': '1', 'false': '0', 'yes': '1', 'no': '0'}
        for key, value in sorted(options.items(), key=lambda item: item[0]):
            target_sat.cli.VirtWhoConfig.update({'id': virtwho_config['id'], 'debug': key})
            command = get_configure_command(virtwho_config['id'], default_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor-type'], org=default_org.label
            )
            assert get_configure_option('debug', ETC_VIRTWHO_CONFIG) == value
        target_sat.cli.VirtWhoConfig.delete({'name': new_name})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', new_name))

    @pytest.mark.tier2
    def test_positive_interval_option(self, default_org, form_data, virtwho_config, target_sat):
        """Verify interval option by hammer virt-who-config update"

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
            target_sat.cli.VirtWhoConfig.update({'id': virtwho_config['id'], 'interval': key})
            command = get_configure_command(virtwho_config['id'], default_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor-type'], org=default_org.label
            )
            assert get_configure_option('interval', ETC_VIRTWHO_CONFIG) == value
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """Verify hypervisor_id option by hammer virt-who-config update"

        :id: 4e6bad11-2019-458b-a368-26ea95afc7f5

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        # esx and rhevm support hwuuid option
        values = ['uuid', 'hostname', 'hwuuid']
        for value in values:
            target_sat.cli.VirtWhoConfig.update(
                {'id': virtwho_config['id'], 'hypervisor-id': value}
            )
            result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})
            assert result['connection']['hypervisor-id'] == value
            config_file = get_configure_file(virtwho_config['id'])
            command = get_configure_command(virtwho_config['id'], default_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor-type'], org=default_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_filter_option(self, default_org, form_data, virtwho_config, target_sat):
        """Verify filter option by hammer virt-who-config update"

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
        command = get_configure_command(virtwho_config['id'], default_org.name)
        # Update Whitelist and check the result
        target_sat.cli.VirtWhoConfig.update(whitelist)
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['connection']['filtering'] == 'Whitelist'
        assert result['connection']['filtered-hosts'] == regex
        assert result['connection']['filter-host-parents'] == regex
        deploy_configure_by_command(command, form_data['hypervisor-type'], org=default_org.label)
        assert get_configure_option('filter_hosts', config_file) == regex
        assert get_configure_option('filter_host_parents', config_file) == regex
        # Update Blacklist and check the result
        target_sat.cli.VirtWhoConfig.update(blacklist)
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['connection']['filtering'] == 'Blacklist'
        assert result['connection']['excluded-hosts'] == regex
        assert result['connection']['exclude-host-parents'] == regex
        deploy_configure_by_command(command, form_data['hypervisor-type'], org=default_org.label)
        assert get_configure_option('exclude_hosts', config_file) == regex
        assert get_configure_option('exclude_host_parents', config_file) == regex
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_proxy_option(self, default_org, form_data, virtwho_config, target_sat):
        """Verify http_proxy option by hammer virt-who-config update"

        :id: 409d108e-e814-482b-93ed-09db89d21dda

        :expectedresults: http_proxy and no_proxy option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 1902199
        """
        # Check the https proxy option, update it via http proxy name
        https_proxy_url, https_proxy_name, https_proxy_id = create_http_proxy(org=default_org)
        no_proxy = 'test.satellite.com'
        target_sat.cli.VirtWhoConfig.update(
            {'id': virtwho_config['id'], 'http-proxy': https_proxy_name, 'no-proxy': no_proxy}
        )
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['http-proxy']['http-proxy-name'] == https_proxy_name
        assert result['connection']['ignore-proxy'] == no_proxy
        command = get_configure_command(virtwho_config['id'], default_org.name)
        deploy_configure_by_command(command, form_data['hypervisor-type'], org=default_org.label)
        assert get_configure_option('https_proxy', ETC_VIRTWHO_CONFIG) == https_proxy_url
        assert get_configure_option('no_proxy', ETC_VIRTWHO_CONFIG) == no_proxy

        # Check the http proxy option, update it via http proxy id
        http_proxy_url, http_proxy_name, http_proxy_id = create_http_proxy(
            http_type='http', org=default_org
        )
        target_sat.cli.VirtWhoConfig.update(
            {'id': virtwho_config['id'], 'http-proxy-id': http_proxy_id}
        )
        deploy_configure_by_command(command, form_data['hypervisor-type'], org=default_org.label)
        assert get_configure_option('http_proxy', ETC_VIRTWHO_CONFIG) == http_proxy_url

        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_rhsm_option(self, default_org, form_data, virtwho_config, target_sat):
        """Verify rhsm options in the configure file"

        :id: b5b93d4d-e780-41c0-9eaa-2407cc1dcc9b

        :expectedresults:
            rhsm_hostname, rhsm_prefix are ecpected
            rhsm_username is not a login account

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        config_file = get_configure_file(virtwho_config['id'])
        command = get_configure_command(virtwho_config['id'], default_org.name)
        deploy_configure_by_command(command, form_data['hypervisor-type'], org=default_org.label)
        rhsm_username = get_configure_option('rhsm_username', config_file)
        assert not User.exists(search=('login', rhsm_username))
        assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
        assert get_configure_option('rhsm_prefix', config_file) == '/rhsm'
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_post_hypervisors(self, function_org, target_sat):
        """Post large json file to /rhsm/hypervisors"

        :id: e344c9d2-3538-4432-9a74-b025e9ef852d

        :expectedresults:
            hypervisor/guest json can be posted and the task is success status

        :CaseLevel: Integration

        :customerscenario: true

        :CaseImportance: Medium

        :BZ: 1637042, 1769680
        """
        data = hypervisor_json_create(hypervisors=100, guests=10)
        url = f"{target_sat.url}/rhsm/hypervisors/{function_org.label}"
        auth = (settings.server.admin_username, settings.server.admin_password)
        result = requests.post(url, auth=auth, verify=False, json=data)
        if result.status_code != 200:
            if "foreman_tasks_sync_task_timeout" in result.text:
                task_id = re.findall('waiting for task (.*?) to finish', result.text)[-1]
                wait_for_tasks(search_query=f'id = {task_id}', max_tries=10)
            else:
                assert result.status_code == 200

    @pytest.mark.tier2
    def test_positive_foreman_packages_protection(
        self, default_org, form_data, virtwho_config, target_sat
    ):
        """foreman-protector should allow virt-who to be installed

        :id: 635ef99b-c5a3-4ac4-a0f1-09f7036d116e

        :expectedresults:
            virt-who packages can be installed
            the virt-who plugin can be deployed successfully

        :CaseLevel: Integration

        :customerscenario: true

        :CaseImportance: Medium

        :BZ: 1783987
        """
        virtwho_package_locked()
        command = get_configure_command(virtwho_config['id'], default_org.name)
        deploy_configure_by_command(command, form_data['hypervisor-type'], org=default_org.label)
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

    @pytest.mark.tier2
    def test_positive_deploy_configure_hypervisor_password_with_special_characters(
        self, default_org, form_data, target_sat
    ):
        """Verify " hammer virt-who-config deploy hypervisor with special characters"

        :id: 9892a94e-ff4b-44dd-87eb-1289d4a965be

        :expectedresults: Config can be created and deployed with any error

        :CaseLevel: Integration

        :CaseImportance: High

        :BZ: 1870816,1959136
        """
        # check the hypervisor password contains single quotes
        form_data['hypervisor-password'] = "Tes't"
        virtwho_config = target_sat.cli.VirtWhoConfig.create(form_data)['general-information']
        assert virtwho_config['status'] == 'No Report Yet'
        virtwho_config['id']
        command = get_configure_command(virtwho_config['id'], default_org.name)
        deploy_status = deploy_configure_by_command_check(command)
        assert deploy_status == 'Finished successfully'
        config_file = get_configure_file(virtwho_config['id'])
        assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
        assert (
            get_configure_option('username', config_file)
            == settings.virtwho.esx.hypervisor_username
        )
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))

        # check the hypervisor password contains backtick
        form_data['hypervisor-password'] = r"my\`password"
        virtwho_config = target_sat.cli.VirtWhoConfig.create(form_data)['general-information']
        assert virtwho_config['status'] == 'No Report Yet'
        virtwho_config['id']
        command = get_configure_command(virtwho_config['id'], default_org.name)
        deploy_status = deploy_configure_by_command_check(command)
        assert deploy_status == 'Finished successfully'
        config_file = get_configure_file(virtwho_config['id'])
        assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
        assert (
            get_configure_option('username', config_file)
            == settings.virtwho.esx.hypervisor_username
        )
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))
