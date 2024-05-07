"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

:CaseImportance: High

"""

import pytest

from robottelo.config import settings
from robottelo.utils.virtwho import (
    ETC_VIRTWHO_CONFIG,
    create_http_proxy,
    deploy_configure_by_command,
    deploy_configure_by_command_check,
    get_configure_command,
    get_configure_file,
    get_configure_option,
)


@pytest.mark.usefixtures('delete_host')
class TestVirtWhoConfigforEsx:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type_api', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, default_org, target_sat, virtwho_config_api, deploy_type_api
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: 72d74c05-2580-4f38-b6c0-999ff470d4d6

        :expectedresults: Config can be created and deployed

        :CaseImportance: High
        """
        assert virtwho_config_api.status == 'unknown'
        hypervisor_name, guest_name = deploy_type_api
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config_api.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
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
            target_sat.api.HostSubscription(host=host['id']).add_subscriptions(
                data={'subscriptions': [{'id': vdc_id, 'quantity': 'Automatic'}]}
            )
            result = target_sat.api.Host().search(query={'search': hostname})[0].read_json()
            assert result['subscription_status_label'] == 'Fully entitled'

    @pytest.mark.tier2
    def test_positive_debug_option(
        self, default_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify debug option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: be395108-3944-4a04-bee4-6bac3fa03a19

        :expectedresults: debug option can be updated.

        :CaseImportance: Medium
        """
        options = {'true': '1', 'false': '0', '1': '1', '0': '0'}
        for key, value in sorted(options.items(), key=lambda item: item[0]):
            virtwho_config_api.debug = key
            virtwho_config_api.update(['debug'])
            command = get_configure_command(virtwho_config_api.id, default_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=default_org.label
            )
            assert get_configure_option('debug', ETC_VIRTWHO_CONFIG) == value

    @pytest.mark.tier2
    def test_positive_interval_option(
        self, default_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify interval option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 65f4138b-ca8f-4f1e-805c-1a331b951be5

        :expectedresults: interval option can be updated.

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
            virtwho_config_api.interval = key
            virtwho_config_api.update(['interval'])
            command = get_configure_command(virtwho_config_api.id, default_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=default_org.label
            )
            assert get_configure_option('interval', ETC_VIRTWHO_CONFIG) == value

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, default_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: f232547f-c4b2-41bc-ab8d-e7579a49ab69

        :expectedresults: hypervisor_id option can be updated.

        :CaseImportance: Medium
        """
        # esx and rhevm support hwuuid option
        values = ['uuid', 'hostname', 'hwuuid']
        for value in values:
            virtwho_config_api.hypervisor_id = value
            virtwho_config_api.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config_api.id)
            command = get_configure_command(virtwho_config_api.id, default_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=default_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    def test_positive_filter_option(
        self, default_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify filter option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 1f251d89-5e22-4470-be4c-0aeba84c0273

        :expectedresults: filter and filter_hosts can be updated.

        :CaseImportance: Medium
        """
        whitelist = {'filtering_mode': '1', 'whitelist': '.*redhat.com'}
        blacklist = {'filtering_mode': '2', 'blacklist': '.*redhat.com'}
        # esx support filter-host-parents and exclude-host-parents options
        whitelist['filter_host_parents'] = '.*redhat.com'
        blacklist['exclude_host_parents'] = '.*redhat.com'
        # Update Whitelist and check the result
        virtwho_config_api.filtering_mode = whitelist['filtering_mode']
        virtwho_config_api.whitelist = whitelist['whitelist']
        virtwho_config_api.filter_host_parents = whitelist['filter_host_parents']
        virtwho_config_api.update(whitelist.keys())
        config_file = get_configure_file(virtwho_config_api.id)
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=default_org.label
        )
        assert get_configure_option('filter_hosts', config_file) == whitelist['whitelist']
        assert (
            get_configure_option('filter_host_parents', config_file)
            == whitelist['filter_host_parents']
        )
        # Update Blacklist and check the result
        virtwho_config_api.filtering_mode = blacklist['filtering_mode']
        virtwho_config_api.blacklist = blacklist['blacklist']
        virtwho_config_api.exclude_host_parents = blacklist['exclude_host_parents']
        virtwho_config_api.update(blacklist.keys())
        config_file = get_configure_file(virtwho_config_api.id)
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=default_org.label
        )
        assert get_configure_option('exclude_hosts', config_file) == blacklist['blacklist']
        assert (
            get_configure_option('exclude_host_parents', config_file)
            == blacklist['exclude_host_parents']
        )

    @pytest.mark.tier2
    def test_positive_proxy_option(
        self, default_org, default_location, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify http_proxy option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id""

        :id: e1b00b46-d5e6-40d5-a955-a45a75a5cfad

        :expectedresults: http_proxy/https_proxy and no_proxy option can be updated.

        :CaseImportance: Medium

        :BZ: 1902199
        """
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=default_org.label
        )
        # Check default NO_PROXY option
        assert get_configure_option('no_proxy', ETC_VIRTWHO_CONFIG) == '*'
        # Check HTTTP Proxy and No_PROXY option
        http_proxy_url, http_proxy_name, http_proxy_id = create_http_proxy(
            http_type='http', org=default_org, location=default_location
        )
        no_proxy = 'test.satellite.com'
        virtwho_config_api.http_proxy_id = http_proxy_id
        virtwho_config_api.no_proxy = no_proxy
        virtwho_config_api.update(['http_proxy_id', 'no_proxy'])
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=default_org.label
        )
        assert get_configure_option('http_proxy', ETC_VIRTWHO_CONFIG) == http_proxy_url
        assert get_configure_option('no_proxy', ETC_VIRTWHO_CONFIG) == no_proxy
        # Check HTTTPs Proxy option
        https_proxy_url, https_proxy_name, https_proxy_id = create_http_proxy(
            org=default_org, location=default_location
        )
        virtwho_config_api.http_proxy_id = https_proxy_id
        virtwho_config_api.update(['http_proxy_id'])
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=default_org.label
        )
        assert get_configure_option('https_proxy', ETC_VIRTWHO_CONFIG) == https_proxy_url

    @pytest.mark.tier2
    def test_positive_configure_organization_list(
        self, default_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify "GET /foreman_virt_who_configure/

        api/v2/organizations/:organization_id/configs"

        :id: 5bf34bef-bf68-4557-978d-419bd4df0ba1

        :expectedresults: Config can be searched in org list

        :CaseImportance: Medium
        """
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=default_org.label
        )
        search_result = virtwho_config_api.get_organization_configs(data={'per_page': '1000'})
        assert [item for item in search_result['results'] if item['name'] == form_data_api['name']]

    @pytest.mark.tier2
    def test_positive_deploy_configure_hypervisor_password_with_special_characters(
        self, default_org, form_data_api, target_sat
    ):
        """Verify " hammer virt-who-config deploy hypervisor with special characters"

        :id: 3a79d65a-e206-4693-a5ba-59f6c44c984e

        :expectedresults: Config can be created and deployed without any error

        :CaseImportance: High

        :BZ: 1870816,1959136

        :customerscenario: true
        """
        # check the hypervisor password contains single quotes
        form_data_api['hypervisor_password'] = "Tes't"
        virtwho_config_api = target_sat.api.VirtWhoConfig(**form_data_api).create()
        assert virtwho_config_api.status == 'unknown'
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_status = deploy_configure_by_command_check(command)
        assert deploy_status == 'Finished successfully'
        config_file = get_configure_file(virtwho_config_api.id)
        assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
        assert (
            get_configure_option('username', config_file)
            == settings.virtwho.esx.hypervisor_username
        )
        virtwho_config_api.delete()
        assert not target_sat.api.VirtWhoConfig().search(
            query={'search': f"name={form_data_api['name']}"}
        )
        # check the hypervisor password contains backtick
        form_data_api['hypervisor_password'] = "my`password"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
        assert virtwho_config.status == 'unknown'
        command = get_configure_command(virtwho_config.id, default_org.name)
        deploy_status = deploy_configure_by_command_check(command)
        assert deploy_status == 'Finished successfully'
        config_file = get_configure_file(virtwho_config.id)
        assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
        assert (
            get_configure_option('username', config_file)
            == settings.virtwho.esx.hypervisor_username
        )
        virtwho_config.delete()
        assert not target_sat.api.VirtWhoConfig().search(
            query={'search': f"name={form_data_api['name']}"}
        )

    @pytest.mark.tier2
    def test_positive_remove_env_option(
        self, default_org, form_data_api, virtwho_config_api, target_sat
    ):
        """remove option 'env=' from the virt-who configuration file and without any error

        :id: 981b6828-a7ed-46d9-9c6c-9fb22af4011e

        :expectedresults:
            the option "env=" should be removed from etc/virt-who.d/virt-who.conf
            /var/log/messages should not display warning message

        :customerscenario: true

        :CaseImportance: Medium

        :BZ: 1834897

        """
        command = get_configure_command(virtwho_config_api.id, default_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], debug=True, org=default_org.label
        )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config_api.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'
        # Check the option "env=" should be removed from etc/virt-who.d/virt-who.conf
        option = "env"
        config_file = get_configure_file(virtwho_config_api.id)
        env_error = f"option {{'{option}'}} is not exist or not be enabled in {{'{config_file}'}}"
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - TODO determine better exception
            get_configure_option({option}, {config_file})
        assert str(exc_info.value) == env_error
        # Check /var/log/messages should not display warning message
        env_warning = f"Ignoring unknown configuration option \"{option}\""
        result = target_sat.execute(f'grep "{env_warning}" /var/log/messages')
        assert result.status == 1
