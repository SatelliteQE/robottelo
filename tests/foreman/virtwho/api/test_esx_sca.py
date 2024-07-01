"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:Team: Phoenix

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


class TestVirtWhoConfigforEsx:
    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize('deploy_type_api', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, target_sat, virtwho_config_api, deploy_type_api
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: 26b37372-390f-45b8-accd-ff006a8b0ccf

        :expectedresults: Config can be created and deployed

        :CaseImportance: High
        """
        assert virtwho_config_api.status == 'unknown'
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config_api.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'

    @pytest.mark.tier2
    def test_positive_debug_option(
        self, module_sca_manifest_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify debug option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 61eeef42-12a0-4b92-9b87-c409b2507052

        :expectedresults: debug option can be updated.

        :CaseImportance: Medium
        """
        options = {'0': '0', '1': '1', 'false': '0', 'true': '1'}
        for key, value in options.items():
            virtwho_config_api.debug = key
            virtwho_config_api.update(['debug'])
            command = get_configure_command(virtwho_config_api.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('debug', ETC_VIRTWHO_CONFIG) == value

    @pytest.mark.tier2
    def test_positive_interval_option(
        self, module_sca_manifest_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify interval option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: aa9c7f19-c402-4197-9d3a-1379d9126620

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
        for key, value in options.items():
            virtwho_config_api.interval = key
            virtwho_config_api.update(['interval'])
            command = get_configure_command(virtwho_config_api.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('interval', ETC_VIRTWHO_CONFIG) == value

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: fb1ebabe-7522-45a3-8e27-05101c50aabe

        :expectedresults: hypervisor_id option can be updated.

        :CaseImportance: Medium
        """
        for value in ['uuid', 'hostname']:
            virtwho_config_api.hypervisor_id = value
            virtwho_config_api.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config_api.id)
            command = get_configure_command(virtwho_config_api.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('filter_type', ['whitelist', 'blacklist'])
    @pytest.mark.parametrize('option_type', ['edit', 'create'])
    def test_positive_filter_option(
        self, module_sca_manifest_org, form_data_api, target_sat, filter_type, option_type
    ):
        """Verify filter option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 443d534a-0eb0-42fb-abcf-15081371a5a9

        :expectedresults:
            1. filter and filter_hosts can be updated.
            2. create virt-who config with filter and filter_hosts options work well.

        :CaseImportance: Medium
        """
        regex = '.*redhat.com'
        whitelist = {'filtering_mode': '1', 'whitelist': regex}
        blacklist = {'filtering_mode': '2', 'blacklist': regex}
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
        if option_type == "edit":
            if filter_type == "whitelist":
                whitelist['filter_host_parents'] = regex
                virtwho_config.filtering_mode = whitelist['filtering_mode']
                virtwho_config.whitelist = whitelist['whitelist']
                virtwho_config.filter_host_parents = whitelist['filter_host_parents']
                virtwho_config.update(whitelist.keys())
            elif filter_type == "blacklist":
                blacklist['exclude_host_parents'] = regex
                virtwho_config.filtering_mode = blacklist['filtering_mode']
                virtwho_config.blacklist = blacklist['blacklist']
                virtwho_config.exclude_host_parents = blacklist['exclude_host_parents']
                virtwho_config.update(blacklist.keys())
            command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
            )
            config_file = get_configure_file(virtwho_config.id)
            result = target_sat.api.VirtWhoConfig().search(
                query={'search': f'name={virtwho_config.name}'}
            )[0]
            if filter_type == "whitelist":
                assert get_configure_option('filter_hosts', config_file) == whitelist['whitelist']
                assert (
                    get_configure_option('filter_host_parents', config_file)
                    == whitelist['filter_host_parents']
                )
                assert result.whitelist == regex
                assert result.filter_host_parents == regex
            elif filter_type == "blacklist":
                assert get_configure_option('exclude_hosts', config_file) == blacklist['blacklist']
                assert (
                    get_configure_option('exclude_host_parents', config_file)
                    == blacklist['exclude_host_parents']
                )
                assert result.blacklist == regex
                assert result.exclude_host_parents == regex
        elif option_type == "create":
            virtwho_config.delete()
            assert not target_sat.api.VirtWhoConfig().search(
                query={'search': f"name={form_data_api['name']}"}
            )
            if filter_type == "whitelist":
                form_data_api['filtering_mode'] = 1
                form_data_api['whitelist'] = regex
                form_data_api['filter_host_parents'] = regex
            elif filter_type == "blacklist":
                form_data_api['filtering_mode'] = 2
                form_data_api['blacklist'] = regex
                form_data_api['exclude_host_parents'] = regex
            virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
            command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
            )
            config_file = get_configure_file(virtwho_config.id)
            result = target_sat.api.VirtWhoConfig().search(
                query={'search': f'name={virtwho_config.name}'}
            )[0]
            if filter_type == "whitelist":
                assert get_configure_option('filter_hosts', config_file) == regex
                assert (
                    get_configure_option('filter_host_parents', config_file)
                    == whitelist['whitelist']
                )
                assert result.whitelist == regex
                assert result.filter_host_parents == regex

            elif filter_type == "blacklist":
                assert get_configure_option('exclude_hosts', config_file) == regex
                assert (
                    get_configure_option('exclude_host_parents', config_file)
                    == blacklist['blacklist']
                )
                assert result.blacklist == regex
                assert result.exclude_host_parents == regex

    @pytest.mark.tier2
    def test_positive_proxy_option(
        self, module_sca_manifest_org, default_location, form_data_api, target_sat
    ):
        """Verify http_proxy option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id""

        :id: cd08dc14-faa2-4d06-a00a-900b16a6195a

        :expectedresults:
            1. http_proxy and no_proxy option can be updated.
            2. create virt-who config with http_proxy and no_proxy options work well.

        :CaseImportance: Medium

        :BZ: 1902199
        """
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
        command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
        )
        # Check default NO_PROXY option
        assert get_configure_option('no_proxy', ETC_VIRTWHO_CONFIG) == '*'
        # Check HTTTP Proxy and No_PROXY option
        http_proxy_url, http_proxy_name, http_proxy_id = create_http_proxy(
            http_type='http', org=module_sca_manifest_org, location=default_location
        )
        no_proxy = 'test.satellite.com'
        virtwho_config.http_proxy_id = http_proxy_id
        virtwho_config.no_proxy = no_proxy
        virtwho_config.update(['http_proxy_id', 'no_proxy'])
        command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option('http_proxy', ETC_VIRTWHO_CONFIG) == http_proxy_url
        assert get_configure_option('no_proxy', ETC_VIRTWHO_CONFIG) == no_proxy
        result = target_sat.api.VirtWhoConfig().search(
            query={'search': f'name={virtwho_config.name}'}
        )[0]
        assert result.no_proxy == no_proxy
        # Check HTTTPs Proxy option
        https_proxy_url, https_proxy_name, https_proxy_id = create_http_proxy(
            org=module_sca_manifest_org, location=default_location
        )
        virtwho_config.http_proxy_id = https_proxy_id
        virtwho_config.update(['http_proxy_id'])
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option('https_proxy', ETC_VIRTWHO_CONFIG) == https_proxy_url
        virtwho_config.delete()
        assert not target_sat.api.VirtWhoConfig().search(
            query={'search': f"name={form_data_api['name']}"}
        )

        # Check the http proxy option, create virt-who config via http proxy id
        form_data_api['http_proxy_id'] = http_proxy_id
        form_data_api['no_proxy'] = no_proxy
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
        command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option('http_proxy', ETC_VIRTWHO_CONFIG) == http_proxy_url
        assert get_configure_option('no_proxy', ETC_VIRTWHO_CONFIG) == no_proxy
        result = target_sat.api.VirtWhoConfig().search(
            query={'search': f'name={virtwho_config.name}'}
        )[0]
        assert result.no_proxy == no_proxy
        virtwho_config.delete()
        assert not target_sat.api.VirtWhoConfig().search(
            query={'search': f"name={form_data_api['name']}"}
        )

    @pytest.mark.tier2
    def test_positive_configure_organization_list(
        self, module_sca_manifest_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify "GET /foreman_virt_who_configure/

        api/v2/organizations/:organization_id/configs"

        :id: 6d6736cd-6a85-40f5-b195-54be8db92571

        :expectedresults: Config can be searched in org list

        :CaseImportance: Medium
        """
        command = get_configure_command(virtwho_config_api.id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], org=module_sca_manifest_org.label
        )
        search_result = virtwho_config_api.get_organization_configs(data={'per_page': '1000'})
        assert [item for item in search_result['results'] if item['name'] == form_data_api['name']]

    @pytest.mark.tier2
    def test_positive_deploy_configure_hypervisor_password_with_special_characters(
        self, module_sca_manifest_org, form_data_api, target_sat
    ):
        """Verify "hammer virt-who-config deploy hypervisor with special characters"

        :id: 7d957371-ae2e-440d-8e19-22eb34922b36

        :expectedresults: Config can be created and deployed without any error

        :CaseImportance: High

        :BZ: 1870816,1959136

        :customerscenario: true
        """
        # check the hypervisor password contains single quotes
        form_data_api['hypervisor_password'] = "Tes't"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
        assert virtwho_config.status == 'unknown'
        command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
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
        # check the hypervisor password contains backtick
        form_data_api['hypervisor_password'] = "my`password"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data_api).create()
        assert virtwho_config.status == 'unknown'
        command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
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
        self, module_sca_manifest_org, form_data_api, virtwho_config_api, target_sat
    ):
        """remove option 'env=' from the virt-who configuration file and without any error

        :id: c6b4ae5a-4369-4a1d-9fa5-e17b7a729027

        :expectedresults:
            1. the option "env=" should be removed from etc/virt-who.d/virt-who.conf
            2. /var/log/messages should not display warning message

        :customerscenario: true

        :CaseImportance: Medium

        :BZ: 1834897

        """
        command = get_configure_command(virtwho_config_api.id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], debug=True, org=module_sca_manifest_org.label
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
