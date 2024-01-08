"""Test class for Virtwho Configure CLI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:Team: Phoenix

:TestType: Functional

:Upstream: No
"""
import re

from fauxfactory import gen_string
import pytest
import requests

from robottelo.config import settings
from robottelo.utils.virtwho import (
    ETC_VIRTWHO_CONFIG,
    create_http_proxy,
    deploy_configure_by_command,
    deploy_configure_by_command_check,
    get_configure_command,
    get_configure_file,
    get_configure_option,
    hypervisor_json_create,
    virtwho_package_locked,
)


class TestVirtWhoConfigforEsx:
    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'deploy_type_cli',
        ['id', 'script', 'name', 'location-id', 'organization-title'],
        indirect=True,
    )
    def test_positive_deploy_configure_by_id_script_name_locationid_organizationtitle(
        self, module_sca_manifest_org, target_sat, virtwho_config_cli, deploy_type_cli
    ):
        """Verify "hammer virt-who-config deploy & fetch"

        :id: 04f2cef8-c88e-4a21-9d2f-c17238eea308

        :expectedresults:
            1. Config can be created and deployed
            2. Config can be created, fetch and deploy

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config_cli['status'] == 'No Report Yet'
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify hypervisor_id option by hammer virt-who-config update"

        :id: 995a6709-e839-4198-89db-37cde8fd0a7b

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        for value in ['uuid', 'hostname']:
            target_sat.cli.VirtWhoConfig.update(
                {'id': virtwho_config_cli['id'], 'hypervisor-id': value}
            )
            result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
            assert result['connection']['hypervisor-id'] == value
            config_file = get_configure_file(virtwho_config_cli['id'])
            command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    def test_positive_debug_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify debug option by hammer virt-who-config update"

        :id: 1a776b6f-2d7c-4e17-8e19-86ecde407805

        :expectedresults: debug option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        assert virtwho_config_cli['name'] == form_data_cli['name']
        options = {'false': '0', 'no': '0', 'true': '1', 'yes': '1'}
        for key, value in options.items():
            target_sat.cli.VirtWhoConfig.update({'id': virtwho_config_cli['id'], 'debug': key})
            command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('debug', ETC_VIRTWHO_CONFIG) == value

    @pytest.mark.tier2
    def test_positive_name_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify debug option by hammer virt-who-config update"

        :id: 8d22c7b8-756b-4f79-83be-34ccb2609388

        :expectedresults: name option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        assert virtwho_config_cli['name'] == form_data_cli['name']
        new_name = gen_string('alphanumeric')
        target_sat.cli.VirtWhoConfig.update({'id': virtwho_config_cli['id'], 'new-name': new_name})
        virt_who_instance_name = target_sat.cli.VirtWhoConfig.info(
            {'id': virtwho_config_cli['id']}
        )['general-information']['name']
        assert virt_who_instance_name == new_name
        target_sat.cli.VirtWhoConfig.update(
            {'id': virtwho_config_cli['id'], 'new-name': form_data_cli['name']}
        )

    @pytest.mark.tier2
    def test_positive_interval_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify interval option by hammer virt-who-config update"

        :id: 9b2ffa5a-c0e9-43e7-bf63-f64832cf7715

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
        for key, value in options.items():
            target_sat.cli.VirtWhoConfig.update({'id': virtwho_config_cli['id'], 'interval': key})
            command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('interval', ETC_VIRTWHO_CONFIG) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('filter_type', ['whitelist', 'blacklist'])
    @pytest.mark.parametrize('option_type', ['edit', 'create'])
    def test_positive_filter_option(
        self,
        module_sca_manifest_org,
        form_data_cli,
        virtwho_config_cli,
        target_sat,
        filter_type,
        option_type,
    ):
        """Verify filter option by hammer virt-who-config update"

        :id: 24ef69bb-52bb-41d5-a8f7-87c14e58e42a

        :expectedresults:
            1. filter and filter_hosts can be updated.
            2. create virt-who config with filter and filter_hosts options work well.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        regex = '.*redhat.com'
        if option_type == "edit":
            # Update whitelist or blacklist and check the result
            if filter_type == "whitelist":
                whitelist = {
                    'id': virtwho_config_cli['id'],
                    'filtering-mode': 'whitelist',
                    'whitelist': regex,
                }
                # esx support filter-host-parents and exclude-host-parents options
                whitelist['filter-host-parents'] = regex
                target_sat.cli.VirtWhoConfig.update(whitelist)
            elif filter_type == "blacklist":
                blacklist = {
                    'id': virtwho_config_cli['id'],
                    'filtering-mode': 'blacklist',
                    'blacklist': regex,
                }
                blacklist['exclude-host-parents'] = regex
                target_sat.cli.VirtWhoConfig.update(blacklist)
            result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
            config_file = get_configure_file(virtwho_config_cli['id'])
            command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
            )
            if filter_type == "whitelist":
                assert result['connection']['filtering'] == 'Whitelist'
                assert result['connection']['filtered-hosts'] == regex
                assert result['connection']['filter-host-parents'] == regex
                assert get_configure_option('filter_hosts', config_file) == regex
                assert get_configure_option('filter_host_parents', config_file) == regex
            elif filter_type == "blacklist":
                assert result['connection']['filtering'] == 'Blacklist'
                assert result['connection']['excluded-hosts'] == regex
                assert result['connection']['exclude-host-parents'] == regex
                assert get_configure_option('exclude_hosts', config_file) == regex
                assert get_configure_option('exclude_host_parents', config_file) == regex
        elif option_type == "create":
            # Create a new virt-who config with filtering-mode whitelist or blacklist
            target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config_cli['name']})
            assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data_cli['name']))
            form_data_cli['filtering-mode'] = filter_type
            form_data_cli[filter_type] = regex
            form_data_cli['filter-host-parents'] = regex
            form_data_cli['exclude-host-parents'] = regex
            virtwho_config_cli = target_sat.cli.VirtWhoConfig.create(form_data_cli)[
                'general-information'
            ]
            result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
            if filter_type == "whitelist":
                assert result['connection']['filtering'] == 'Whitelist'
                assert result['connection']['filtered-hosts'] == regex
                assert result['connection']['filter-host-parents'] == regex
            elif filter_type == "blacklist":
                assert result['connection']['filtering'] == 'Blacklist'
                assert result['connection']['excluded-hosts'] == regex
                assert result['connection']['exclude-host-parents'] == regex
            command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
            )
            config_file = get_configure_file(virtwho_config_cli['id'])
            if filter_type == "whitelist":
                assert get_configure_option('filter_hosts', config_file) == regex
                assert get_configure_option('filter_host_parents', config_file) == regex
            elif filter_type == "blacklist":
                assert get_configure_option('exclude_hosts', config_file) == regex
                assert get_configure_option('exclude_host_parents', config_file) == regex

    @pytest.mark.tier2
    def test_positive_proxy_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify http_proxy option by hammer virt-who-config update"

        :id: b506992e-d043-46b7-91ba-bbad401d45fd

        :expectedresults:
            1. http_proxy and no_proxy option can be updated.
            2. create virt-who config with http_proxy and no_proxy options work well.

        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 1902199
        """
        # Check the https proxy option, update it via http proxy name
        https_proxy_url, https_proxy_name, https_proxy_id = create_http_proxy(
            org=module_sca_manifest_org
        )
        no_proxy = 'test.satellite.com'
        target_sat.cli.VirtWhoConfig.update(
            {'id': virtwho_config_cli['id'], 'http-proxy': https_proxy_name, 'no-proxy': no_proxy}
        )
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
        assert result['http-proxy']['http-proxy-name'] == https_proxy_name
        assert result['connection']['ignore-proxy'] == no_proxy
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option('https_proxy', ETC_VIRTWHO_CONFIG) == https_proxy_url
        assert get_configure_option('no_proxy', ETC_VIRTWHO_CONFIG) == no_proxy

        # Check the http proxy option, update it via http proxy id
        http_proxy_url, http_proxy_name, http_proxy_id = create_http_proxy(
            http_type='http', org=module_sca_manifest_org
        )
        target_sat.cli.VirtWhoConfig.update(
            {'id': virtwho_config_cli['id'], 'http-proxy-id': http_proxy_id}
        )
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option('http_proxy', ETC_VIRTWHO_CONFIG) == http_proxy_url

        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config_cli['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data_cli['name']))

        # Check the http proxy option, create virt-who config via http proxy id
        form_data_cli['http-proxy-id'] = http_proxy_id
        virtwho_config_cli = target_sat.cli.VirtWhoConfig.create(form_data_cli)[
            'general-information'
        ]
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option('http_proxy', ETC_VIRTWHO_CONFIG) == http_proxy_url
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config_cli['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data_cli['name']))

        # Check the https proxy option, create virt-who config via http proxy name
        no_proxy = 'test.satellite.com'
        form_data_cli['http-proxy'] = https_proxy_name
        form_data_cli['no-proxy'] = no_proxy
        virtwho_config_cli = target_sat.cli.VirtWhoConfig.create(form_data_cli)[
            'general-information'
        ]
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})
        assert result['http-proxy']['http-proxy-name'] == https_proxy_name
        assert result['connection']['ignore-proxy'] == no_proxy
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
        )
        get_configure_file(virtwho_config_cli['id'])
        assert get_configure_option('https_proxy', ETC_VIRTWHO_CONFIG) == https_proxy_url
        assert get_configure_option('no_proxy', ETC_VIRTWHO_CONFIG) == no_proxy

    @pytest.mark.tier2
    def test_positive_rhsm_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """Verify rhsm options in the configure file"

        :id: 2aad374a-c493-4e3c-91e3-60f21181fd29

        :expectedresults:
            1. rhsm_hostname, rhsm_prefix are expected
            2. rhsm_username is not a login account

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        config_file = get_configure_file(virtwho_config_cli['id'])
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
        )
        rhsm_username = get_configure_option('rhsm_username', config_file)
        assert not target_sat.cli.User.exists(search=('login', rhsm_username))
        assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
        assert get_configure_option('rhsm_prefix', config_file) == '/rhsm'

    @pytest.mark.tier2
    def test_positive_post_hypervisors(self, function_org, target_sat):
        """Post large json file to /rhsm/hypervisors"

        :id: 6d08e37a-ac72-455e-b173-155f376caff9

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
                target_sat.wait_for_tasks(search_query=f'id = {task_id}', max_tries=10)
            else:
                assert result.status_code == 200

    @pytest.mark.tier2
    def test_positive_foreman_packages_protection(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """foreman-protector should allow virt-who to be installed

        :id: a3a2a4b2-32f5-4fb6-ace6-287ef5bb6309

        :expectedresults:
            1. virt-who packages can be installed
            2. the virt-who plugin can be deployed successfully

        :CaseLevel: Integration

        :customerscenario: true

        :CaseImportance: Medium

        :BZ: 1783987
        """
        virtwho_package_locked()
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], org=module_sca_manifest_org.label
        )
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'

    @pytest.mark.tier2
    def test_positive_deploy_configure_hypervisor_password_with_special_characters(
        self, module_sca_manifest_org, form_data_cli, target_sat
    ):
        """Verify "hammer virt-who-config deploy hypervisor with special characters"

        :id: a691267a-008e-4f22-ab49-c1ec1612a628

        :expectedresults: Config can be created and deployed without any error

        :CaseLevel: Integration

        :CaseImportance: High

        :BZ: 1870816,1959136

        :customerscenario: true
        """
        # check the hypervisor password contains single quotes
        form_data_cli['hypervisor-password'] = "Tes't"
        virtwho_config_cli = target_sat.cli.VirtWhoConfig.create(form_data_cli)[
            'general-information'
        ]
        assert virtwho_config_cli['status'] == 'No Report Yet'
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_status = deploy_configure_by_command_check(command)
        assert deploy_status == 'Finished successfully'
        config_file = get_configure_file(virtwho_config_cli['id'])
        assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
        assert (
            get_configure_option('username', config_file)
            == settings.virtwho.esx.hypervisor_username
        )
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config_cli['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data_cli['name']))

        # check the hypervisor password contains backtick
        form_data_cli['hypervisor-password'] = r"my\`password"
        virtwho_config_cli = target_sat.cli.VirtWhoConfig.create(form_data_cli)[
            'general-information'
        ]
        assert virtwho_config_cli['status'] == 'No Report Yet'
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_status = deploy_configure_by_command_check(command)
        assert deploy_status == 'Finished successfully'
        config_file = get_configure_file(virtwho_config_cli['id'])
        assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
        assert (
            get_configure_option('username', config_file)
            == settings.virtwho.esx.hypervisor_username
        )
        target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config_cli['name']})
        assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data_cli['name']))

    @pytest.mark.tier2
    def test_positive_remove_env_option(
        self, module_sca_manifest_org, form_data_cli, virtwho_config_cli, target_sat
    ):
        """remove option 'env=' from the virt-who configuration file and without any error

        :id: 1a8a3be9-bd0a-4fb9-891f-4e7f53bdaa18

        :expectedresults:
            1. the option "env=" should be removed from etc/virt-who.d/virt-who.conf
            2. /var/log/messages should not display warning message

        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 1834897

        :customerscenario: true
        """
        command = get_configure_command(virtwho_config_cli['id'], module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], debug=True, org=module_sca_manifest_org.label
        )
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config_cli['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'
        # Check the option "env=" should be removed from etc/virt-who.d/virt-who.conf
        option = "env"
        config_file = get_configure_file(virtwho_config_cli['id'])
        env_error = (
            f"option {{\'{option}\'}} is not exist or not be enabled in {{\'{config_file}\'}}"
        )
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - TODO determine better exception
            get_configure_option({option}, {config_file})
        assert str(exc_info.value) == env_error
        # Check /var/log/messages should not display warning message
        env_warning = f"Ignoring unknown configuration option \"{option}\""
        result = target_sat.execute(f'grep "{env_warning}" /var/log/messages')
        assert result.status == 1
