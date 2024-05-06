"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

"""

from datetime import datetime

from airgun.session import Session
from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.utils.datafactory import valid_emails_list
from robottelo.utils.virtwho import (
    ETC_VIRTWHO_CONFIG,
    add_configure_option,
    delete_configure_option,
    deploy_configure_by_command,
    deploy_configure_by_command_check,
    get_configure_command,
    get_configure_file,
    get_configure_id,
    get_configure_option,
    get_virtwho_status,
    restart_virtwho_service,
    update_configure_option,
)


@pytest.mark.usefixtures('delete_host')
class TestVirtwhoConfigforEsx:
    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize('deploy_type_ui', ['id', 'script'], indirect=True)
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, org_session, form_data_ui, deploy_type_ui
    ):
        """Verify configure created and deployed with id.

        :id: 867e109f-3ecc-4631-b6fb-085a1142473a

        :expectedresults:
            1. Config can be created and deployed by command or script
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseImportance: High
        """
        assert org_session.virtwho_configure.search(form_data_ui['name'])[0]['Status'] == 'ok'

    @pytest.mark.tier2
    def test_positive_debug_option(
        self, module_sca_manifest_org, virtwho_config_ui, org_session, form_data_ui
    ):
        """Verify debug checkbox and the value changes of VIRTWHO_DEBUG

        :id: 71e675b5-16ae-423a-9162-cd10a7a6a5eb

        :expectedresults:
            1. if debug is checked, VIRTWHO_DEBUG=1 in /etc/sysconfig/virt-who
            2. if debug is unchecked, VIRTWHO_DEBUG=0 in /etc/sysconfig/virt-who

        :CaseImportance: Medium
        """
        name = form_data_ui['name']
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            config_command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option('debug', ETC_VIRTWHO_CONFIG) == '1'
        org_session.virtwho_configure.edit(name, {'debug': False})
        results = org_session.virtwho_configure.read(name)
        assert results['overview']['debug'] is False
        deploy_configure_by_command(
            config_command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option('debug', ETC_VIRTWHO_CONFIG) == '0'

    @pytest.mark.tier2
    def test_positive_interval_option(
        self, module_sca_manifest_org, virtwho_config_ui, org_session, form_data_ui
    ):
        """Verify interval dropdown options and the value changes of VIRTWHO_INTERVAL.

        :id: 22fe4e66-5a73-4fa5-866e-c5664aabfa23

        :expectedresults:
            VIRTWHO_INTERVAL can be changed in /etc/sysconfig/virt-who if the
            dropdown option is selected to Every 2/4/8/12/24 hours, Every 2/3 days.

        :CaseImportance: Medium
        """
        name = form_data_ui['name']
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, module_sca_manifest_org.name)
        intervals = {
            'Every hour': '3600',
            'Every 2 hours': '7200',
            'Every 4 hours': '14400',
            'Every 8 hours': '28800',
            'Every 12 hours': '43200',
            'Every 24 hours': '86400',
            'Every 2 days': '172800',
            'Every 3 days': '259200',
        }
        for option, value in intervals.items():
            org_session.virtwho_configure.edit(name, {'interval': option})
            results = org_session.virtwho_configure.read(name)
            assert results['overview']['interval'] == option
            deploy_configure_by_command(
                config_command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('interval', ETC_VIRTWHO_CONFIG) == value

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, virtwho_config_ui, org_session, form_data_ui
    ):
        """Verify Hypervisor ID dropdown options.

        :id: b9767319-ab81-425c-bebe-0701d5e91332

        :expectedresults:
            hypervisor_id can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to uuid/hwuuid/hostname.

        :CaseImportance: Medium
        """
        name = form_data_ui['name']
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, module_sca_manifest_org.name)
        config_file = get_configure_file(config_id)
        # esx and rhevm support hwuuid option
        for value in ['uuid', 'hostname', 'hwuuid']:
            org_session.virtwho_configure.edit(name, {'hypervisor_id': value})
            results = org_session.virtwho_configure.read(name)
            assert results['overview']['hypervisor_id'] == value
            deploy_configure_by_command(
                config_command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('filter_type', ['whitelist', 'blacklist'])
    @pytest.mark.parametrize('option_type', ['edit', 'create'])
    def test_positive_filtering_option(
        self, module_sca_manifest_org, org_session, form_data_ui, filter_type, option_type
    ):
        """Verify Filtering dropdown options.

        :id: 8e5fa139-8e79-4dd4-85f2-5565ec4b39f1

        :expectedresults:
            1. Edit virtwho config if filtering is selected to Whitelist,
            'Filter hosts' can be set.
            2. Edit virtwho config if filtering is selected to Blacklist,
            'Exclude hosts' can be set.
            3. Create virtwho config if filtering is selected to Whitelist,
            'Filter hosts' can be set.
            4. Create virtwho config if filtering is selected to Blacklist,
            'Exclude hosts' can be set.

        :CaseImportance: Medium

        :BZ: 1735670

        :customerscenario: true
        """
        name = gen_string('alpha')
        form_data_ui['name'] = name
        regex = '.*redhat.com'
        with org_session:
            if option_type == "edit":
                org_session.virtwho_configure.create(form_data_ui)
                config_id = get_configure_id(name)
                config_command = get_configure_command(config_id, module_sca_manifest_org.name)
                config_file = get_configure_file(config_id)
                if filter_type == "whitelist":
                    whitelist = {'filtering': 'Whitelist', 'filtering_content.filter_hosts': regex}
                    # esx support filter-host-parents and exclude-host-parents options
                    whitelist['filtering_content.filter_host_parents'] = regex
                    # Update Whitelist and check the result
                    org_session.virtwho_configure.edit(name, whitelist)
                    results = org_session.virtwho_configure.read(name)
                    assert results['overview']['filter_hosts'] == regex
                    assert results['overview']['filter_host_parents'] == regex
                elif filter_type == "blacklist":
                    blacklist = {'filtering': 'Blacklist', 'filtering_content.exclude_hosts': regex}
                    blacklist['filtering_content.exclude_host_parents'] = regex
                    org_session.virtwho_configure.edit(name, blacklist)
                    results = org_session.virtwho_configure.read(name)
                    assert results['overview']['exclude_hosts'] == regex
                    assert results['overview']['exclude_host_parents'] == regex
                deploy_configure_by_command(
                    config_command,
                    form_data_ui['hypervisor_type'],
                    org=module_sca_manifest_org.label,
                )
                if filter_type == "whitelist":
                    assert regex == get_configure_option('filter_hosts', config_file)
                    assert regex == get_configure_option('filter_host_parents', config_file)
                elif filter_type == "blacklist":
                    assert regex == get_configure_option('exclude_hosts', config_file)
                    assert regex == get_configure_option('exclude_host_parents', config_file)
                org_session.virtwho_configure.delete(name)
                assert not org_session.virtwho_configure.search(name)
            elif option_type == "create":
                if filter_type == "whitelist":
                    form_data_ui['filtering'] = "Whitelist"
                    form_data_ui['filtering_content.filter_hosts'] = regex
                    form_data_ui['filtering_content.filter_host_parents'] = regex
                elif filter_type == "blacklist":
                    form_data_ui['filtering'] = "Blacklist"
                    form_data_ui['filtering_content.exclude_hosts'] = regex
                    form_data_ui['filtering_content.exclude_host_parents'] = regex
                org_session.virtwho_configure.create(form_data_ui)
                config_id = get_configure_id(name)
                command = get_configure_command(config_id, module_sca_manifest_org.name)
                deploy_configure_by_command(
                    command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
                )
                config_file = get_configure_file(config_id)
                results = org_session.virtwho_configure.read(name)
                if filter_type == "whitelist":
                    assert results['overview']['filter_hosts'] == regex
                    assert results['overview']['filter_host_parents'] == regex
                    assert regex == get_configure_option('filter_hosts', config_file)
                    assert regex == get_configure_option('filter_host_parents', config_file)
                elif filter_type == "blacklist":
                    assert results['overview']['exclude_hosts'] == regex
                    assert results['overview']['exclude_host_parents'] == regex
                    assert regex == get_configure_option('exclude_hosts', config_file)
                    assert regex == get_configure_option('exclude_host_parents', config_file)

    @pytest.mark.tier2
    def test_positive_last_checkin_status(
        self,
        module_sca_manifest_org,
        virtwho_config_ui,
        form_data_ui,
        org_session,
        default_location,
    ):
        """Verify the Last Checkin status on Content Hosts Page.

        :id: 4b76b79b-df9b-453e-9e72-0f33f35b8d29

        :expectedresults: The Last Checkin time on Content Hosts Page is client date time

        :BZ: 1652323

        :customerscenario: true

        :CaseImportance: Medium
        """
        name = form_data_ui['name']
        values = org_session.virtwho_configure.read(name, widget_names='deploy.command')
        command = values['deploy']['command']
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data_ui['hypervisor_type'], debug=True, org=module_sca_manifest_org.label
        )
        time_now = org_session.browser.get_client_datetime()
        assert org_session.virtwho_configure.search(name)[0]['Status'] == 'ok'
        org_session.location.select(default_location.name)
        checkin_time = org_session.contenthost.search(hypervisor_name)[0]['Last Checkin']
        # 10 mins margin to check the Last Checkin time
        assert (
            abs(
                datetime.strptime(checkin_time, "%B %d, %Y at %I:%M %p")
                .replace(year=datetime.utcnow().year)
                .timestamp()
                - time_now.timestamp()
            )
            <= 300
        )

    @pytest.mark.tier2
    def test_positive_remove_env_option(
        self, module_sca_manifest_org, virtwho_config_ui, form_data_ui, target_sat, org_session
    ):
        """remove option 'env=' from the virt-who configuration file and without any error

        :id: 779a37fb-1245-4b01-920f-7c28a96a5fe0

        :expectedresults:
            1. the option "env=" should be removed from etc/virt-who.d/virt-who.conf
            2. /var/log/messages should not display warning message

        :CaseImportance: Medium

        :BZ: 1834897

        :customerscenario: true
        """
        name = form_data_ui['name']
        values = org_session.virtwho_configure.read(name)
        command = values['deploy']['command']
        deploy_configure_by_command(
            command, form_data_ui['hypervisor_type'], debug=True, org=module_sca_manifest_org.label
        )
        assert org_session.virtwho_configure.search(name)[0]['Status'] == 'ok'
        # Check the option "env=" should be removed from etc/virt-who.d/virt-who.conf
        option = "env"
        config_id = get_configure_id(name)
        config_file = get_configure_file(config_id)
        env_error = f"option {{'{option}'}} is not exist or not be enabled in {{'{config_file}'}}"
        with pytest.raises(Exception) as exc_info:  # noqa: PT011 - TODO determine better exception
            get_configure_option({option}, {config_file})
        assert str(exc_info.value) == env_error
        # Check /var/log/messages should not display warning message
        env_warning = f"Ignoring unknown configuration option \"{option}\""
        result = target_sat.execute(f'grep "{env_warning}" /var/log/messages')
        assert result.status == 1

    @pytest.mark.tier2
    def test_positive_virtwho_roles(self, org_session):
        """Verify the default roles for virtwho configure

        :id: 3c2501d5-c122-49f0-baa4-4c0d678cb6fc

        :expectedresults:
            'Virt-who Manager', 'Virt-who Reporter', 'Virt-who Viewer' existing

        :CaseImportance: Low
        """
        roles = {
            'Virt-who Manager': {
                'Satellite virt who configure/config': [
                    'view_virt_who_config',
                    'create_virt_who_config',
                    'edit_virt_who_config',
                    'destroy_virt_who_config',
                ]
            },
            'Virt-who Reporter': {
                'Host': ['create_hosts', 'edit_hosts'],
                'Lifecycle Environment': ['view_lifecycle_environments'],
                '(Miscellaneous)': ['my_organizations'],
            },
            'Virt-who Viewer': {'Satellite virt who configure/config': ['view_virt_who_config']},
        }
        with org_session:
            for role_name, role_filters in roles.items():
                assert org_session.role.search(role_name)[0]['Name'] == role_name
                assigned_permissions = org_session.filter.read_permissions(role_name)
                assert sorted(assigned_permissions) == sorted(role_filters)

    @pytest.mark.tier2
    def test_positive_delete_configure(self, module_sca_manifest_org, org_session, form_data_ui):
        """Verify when a config is deleted the associated user is deleted.

        :id: efc7253d-f455-4dc3-ae03-3ed5e215bd11

        :steps:
            1. Create a virt-who configuration and deploy it to a
               virt-who server.
            2. Delete the configuration on the Satellite.

        :expectedresults:
            1. Verify the virt-who server can no longer connect to the
               Satellite.

        :CaseImportance: Low
        """
        name = gen_string('alpha')
        form_data_ui['name'] = name
        with org_session:
            org_session.virtwho_configure.create(form_data_ui)
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                config_command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert org_session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            org_session.virtwho_configure.delete(name)
            assert not org_session.virtwho_configure.search(name)
            restart_virtwho_service()
            assert get_virtwho_status() == 'logerror'

    @pytest.mark.tier2
    def test_positive_virtwho_reporter_role(
        self, module_sca_manifest_org, org_session, test_name, form_data_ui
    ):
        """Verify the virt-who reporter role can TRULY work.

        :id: eacb6efc-7bcb-4837-9d88-e242cfb3eaae

        :expectedresults:
            Virt-who Reporter Role granting minimal set of permissions for virt-who
            to upload the report, it can be used if you configure virt-who manually
            and want to use user that has locked down account.

        :CaseImportance: Low
        """
        username = gen_string('alpha')
        password = gen_string('alpha')
        config_name = gen_string('alpha')
        with org_session:
            # Create an user
            org_session.user.create(
                {
                    'user.login': username,
                    'user.mail': valid_emails_list()[0],
                    'user.auth': 'INTERNAL',
                    'user.password': password,
                    'user.confirm': password,
                }
            )
            # Create a virt-who config plugin
            form_data_ui['name'] = config_name
            org_session.virtwho_configure.create(form_data_ui)
            values = org_session.virtwho_configure.read(config_name)
            command = values['deploy']['command']
            deploy_configure_by_command(
                command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert org_session.virtwho_configure.search(config_name)[0]['Status'] == 'ok'
            # Update the virt-who config file
            config_id = get_configure_id(config_name)
            config_file = get_configure_file(config_id)
            update_configure_option('rhsm_username', username, config_file)
            delete_configure_option('rhsm_encrypted_password', config_file)
            add_configure_option('rhsm_password', password, config_file)
            restart_virtwho_service()
            assert get_virtwho_status() == 'logerror'
            # Check the permissioin of Virt-who Reporter
            org_session.user.update(username, {'roles.resources.assigned': ['Virt-who Reporter']})
            assert org_session.user.search(username)[0]['Username'] == username
            user = org_session.user.read(username)
            assert user['roles']['resources']['assigned'] == ['Virt-who Reporter']
            restart_virtwho_service()
            assert get_virtwho_status() == 'running'
            with Session(test_name, username, password) as newsession:
                assert not newsession.virtwho_configure.check_create_permission()['can_view']
            org_session.user.delete(username)
            assert not org_session.user.search(username)

    @pytest.mark.tier2
    def test_positive_virtwho_viewer_role(
        self, module_sca_manifest_org, org_session, test_name, form_data_ui
    ):
        """Verify the virt-who viewer role can TRULY work.

        :id: 6619a1e8-5cd4-4fe8-a318-95499aeb7552

        :expectedresults:
            Virt-who Viewer Role granting permissions to see all configurations
            including their configuration scripts, which means viewers could still
            deploy the virt-who instances for existing virt-who configurations.

        :CaseImportance: Low
        """
        username = gen_string('alpha')
        password = gen_string('alpha')
        config_name = gen_string('alpha')
        with org_session:
            # Create an user
            org_session.user.create(
                {
                    'user.login': username,
                    'user.mail': valid_emails_list()[0],
                    'user.auth': 'INTERNAL',
                    'user.password': password,
                    'user.confirm': password,
                }
            )
            # Create a virt-who config plugin
            form_data_ui['name'] = config_name
            org_session.virtwho_configure.create(form_data_ui)
            values = org_session.virtwho_configure.read(config_name)
            command = values['deploy']['command']
            deploy_configure_by_command(
                command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert org_session.virtwho_configure.search(config_name)[0]['Status'] == 'ok'
            # Check the permissioin of Virt-who Viewer
            org_session.user.update(username, {'roles.resources.assigned': ['Virt-who Viewer']})
            user = org_session.user.read(username)
            assert user['roles']['resources']['assigned'] == ['Virt-who Viewer']
            # Update the virt-who config file
            config_id = get_configure_id(config_name)
            config_file = get_configure_file(config_id)
            update_configure_option('rhsm_username', username, config_file)
            delete_configure_option('rhsm_encrypted_password', config_file)
            add_configure_option('rhsm_password', password, config_file)
            restart_virtwho_service()
            assert get_virtwho_status() == 'logerror'
            with Session(test_name, username, password) as newsession:
                create_permission = newsession.virtwho_configure.check_create_permission()
                update_permission = newsession.virtwho_configure.check_update_permission(
                    config_name
                )
                assert create_permission['can_view']
                assert not create_permission['can_create']
                assert not update_permission['can_delete']
                assert not update_permission['can_edit']
                newsession.virtwho_configure.read(config_name)
            # Delete the created user
            org_session.user.delete(username)
            assert not org_session.user.search(username)

    @pytest.mark.tier2
    def test_positive_virtwho_manager_role(
        self, module_sca_manifest_org, org_session, test_name, form_data_ui
    ):
        """Verify the virt-who manager role can TRULY work.

        :id: ddaf44cc-10fb-402a-9b97-fe8692404031

        :expectedresults:
            Virt-who Manager Role granting all permissions to manage virt-who configurations,
            user needs this role to create, delete or update configurations.

        :CaseImportance: Low
        """
        username = gen_string('alpha')
        password = gen_string('alpha')
        config_name = gen_string('alpha')
        with org_session:
            # Create an user
            org_session.user.create(
                {
                    'user.login': username,
                    'user.mail': valid_emails_list()[0],
                    'user.auth': 'INTERNAL',
                    'user.password': password,
                    'user.confirm': password,
                }
            )
            # Create a virt-who config plugin
            form_data_ui['name'] = config_name
            org_session.virtwho_configure.create(form_data_ui)
            values = org_session.virtwho_configure.read(config_name)
            command = values['deploy']['command']
            deploy_configure_by_command(
                command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert org_session.virtwho_configure.search(config_name)[0]['Status'] == 'ok'
            # Check the permissioin of Virt-who Manager
            org_session.user.update(username, {'roles.resources.assigned': ['Virt-who Manager']})
            user = org_session.user.read(username)
            assert user['roles']['resources']['assigned'] == ['Virt-who Manager']
            with Session(test_name, username, password) as newsession:
                # create_virt_who_config
                new_virt_who_name = gen_string('alpha')
                form_data_ui['name'] = new_virt_who_name
                newsession.virtwho_configure.create(form_data_ui)
                # view_virt_who_config
                values = newsession.virtwho_configure.read(new_virt_who_name)
                command = values['deploy']['command']
                deploy_configure_by_command(
                    command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
                )
                assert newsession.virtwho_configure.search(new_virt_who_name)[0]['Status'] == 'ok'
                # edit_virt_who_config
                modify_name = gen_string('alpha')
                newsession.virtwho_configure.edit(new_virt_who_name, {'name': modify_name})
                newsession.virtwho_configure.search(modify_name)
                # destroy_virt_who_config
                newsession.virtwho_configure.delete(modify_name)
                assert not newsession.virtwho_configure.search(modify_name)
            # Delete the created user
            org_session.user.delete(username)
            assert not org_session.user.search(username)

    @pytest.mark.tier2
    def test_positive_deploy_configure_hypervisor_password_with_special_characters(
        self, module_sca_manifest_org, form_data_ui, target_sat, org_session
    ):
        """Verify " hammer virt-who-config deploy hypervisor with special characters"

        :id: 0cefdbb3-fc23-49c4-b1fb-78004db1c7bc

        :expectedresults: Config can be created and deployed without any error

        :CaseImportance: High

        :BZ: 1870816,1959136

        :customerscenario: true
        """
        name = gen_string('alpha')
        form_data_ui['name'] = name
        with org_session:
            # check the hypervisor password contains single quotes
            form_data_ui['hypervisor_content.password'] = "Tes't"
            org_session.virtwho_configure.create(form_data_ui)
            values = org_session.virtwho_configure.read(name)
            command = values['deploy']['command']
            config_id = get_configure_id(name)
            deploy_status = deploy_configure_by_command_check(command)
            assert deploy_status == 'Finished successfully'
            config_file = get_configure_file(config_id)
            assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
            assert (
                get_configure_option('username', config_file)
                == settings.virtwho.esx.hypervisor_username
            )
            org_session.virtwho_configure.delete(name)
            assert not org_session.virtwho_configure.search(name)
            # check the hypervisor password contains backtick
            form_data_ui['hypervisor_content.password'] = "my`password"
            org_session.virtwho_configure.create(form_data_ui)
            values = org_session.virtwho_configure.read(name)
            command = values['deploy']['command']
            config_id = get_configure_id(name)
            deploy_status = deploy_configure_by_command_check(command)
            assert deploy_status == 'Finished successfully'
            config_file = get_configure_file(config_id)
            assert get_configure_option('rhsm_hostname', config_file) == target_sat.hostname
            assert (
                get_configure_option('username', config_file)
                == settings.virtwho.esx.hypervisor_username
            )
            org_session.virtwho_configure.delete(name)
            assert not org_session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_hypervisor_password_option(
        self, module_sca_manifest_org, virtwho_config_ui, org_session, form_data_ui
    ):
        """Verify Hypervisor password.

        :id: 8362955a-4daa-4332-9559-b526d9095a61

        :expectedresults:
            hypervisor_password has been set in virt-who-config-{}.conf
            hypervisor_password has been encrypted in satellite WEB UI Edit page
            hypervisor_password has been encrypted in satellite WEB UI Details page

        :CaseImportance: Medium

        :BZ: 2256927
        """
        name = form_data_ui['name']
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            config_command, form_data_ui['hypervisor_type'], org=module_sca_manifest_org.label
        )
        config_file = get_configure_file(config_id)
        assert get_configure_option('encrypted_password', config_file)
        res = org_session.virtwho_configure.read_edit(name)
        assert 'encrypted-' in res['hypervisor_content']['password']
        org_session.virtwho_configure.edit(name, {'hypervisor_password': gen_string('alpha')})
        results = org_session.virtwho_configure.read(name)
        assert 'encrypted_password=$cr_password' in results['deploy']['script']
