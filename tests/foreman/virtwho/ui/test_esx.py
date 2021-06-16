"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:Assignee: kuhuang

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime

import pytest
from airgun.session import Session
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.datafactory import valid_emails_list
from robottelo.virtwho_utils import add_configure_option
from robottelo.virtwho_utils import create_http_proxy
from robottelo.virtwho_utils import delete_configure_option
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_id
from robottelo.virtwho_utils import get_configure_option
from robottelo.virtwho_utils import get_virtwho_status
from robottelo.virtwho_utils import restart_virtwho_service
from robottelo.virtwho_utils import update_configure_option
from robottelo.virtwho_utils import VIRTWHO_SYSCONFIG


@pytest.fixture()
def form_data():
    form = {
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.esx.hypervisor_type,
        'hypervisor_content.server': settings.virtwho.esx.hypervisor_server,
        'hypervisor_content.username': settings.virtwho.esx.hypervisor_username,
        'hypervisor_content.password': settings.virtwho.esx.hypervisor_password,
    }
    return form


class TestVirtwhoConfigforEsx:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(self, session, form_data):
        """Verify configure created and deployed with id.

        :id: 44f93ec8-a59a-42a4-ab30-edc554b022b2

        :expectedresults:
            1. Config can be created and deployed by command
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(name)
            command = values['deploy']['command']
            hypervisor_name, guest_name = deploy_configure_by_command(
                command, form_data['hypervisor_type'], debug=True
            )
            assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            hypervisor_display_name = session.contenthost.search(hypervisor_name)[0]['Name']
            vdc_physical = f'product_id = {settings.virtwho.sku.vdc_physical} and type=NORMAL'
            vdc_virtual = f'product_id = {settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'
            session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
            assert session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
            session.contenthost.add_subscription(guest_name, vdc_virtual)
            assert session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_deploy_configure_by_script(self, session, form_data):
        """Verify configure created and deployed with script.

        :id: d64332fb-a6e0-4864-9f8b-2406223fcdcc

        :expectedresults:
            1. Config can be created and deployed by script
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(name)
            script = values['deploy']['script']
            hypervisor_name, guest_name = deploy_configure_by_script(
                script, form_data['hypervisor_type'], debug=True
            )
            assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            hypervisor_display_name = session.contenthost.search(hypervisor_name)[0]['Name']
            vdc_physical = f'product_id = {settings.virtwho.sku.vdc_physical} and type=NORMAL'
            vdc_virtual = f'product_id = {settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'
            session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
            assert session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
            session.contenthost.add_subscription(guest_name, vdc_virtual)
            assert session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_debug_option(self, session, form_data):
        """Verify debug checkbox and the value changes of VIRTWHO_DEBUG

        :id: adb435c4-d02b-47b6-89f5-dce9a4ff7939

        :expectedresults:
            1. if debug is checked, VIRTWHO_DEBUG=1 in /etc/sysconfig/virt-who
            2. if debug is unchecked, VIRTWHO_DEBUG=0 in /etc/sysconfig/virt-who

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id)
            deploy_configure_by_command(config_command, form_data['hypervisor_type'])
            assert get_configure_option('VIRTWHO_DEBUG', VIRTWHO_SYSCONFIG) == '1'
            session.virtwho_configure.edit(name, {'debug': False})
            results = session.virtwho_configure.read(name)
            assert results['overview']['debug'] is False
            deploy_configure_by_command(config_command, form_data['hypervisor_type'])
            assert get_configure_option('VIRTWHO_DEBUG', VIRTWHO_SYSCONFIG) == '0'
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_interval_option(self, session, form_data):
        """Verify interval dropdown options and the value changes of VIRTWHO_INTERVAL.

        :id: 731f8361-38d4-40b9-9530-8d785d61eaab

        :expectedresults:
            VIRTWHO_INTERVAL can be changed in /etc/sysconfig/virt-who if the
            dropdown option is selected to Every 2/4/8/12/24 hours, Every 2/3 days.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id)
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
            for option, value in sorted(intervals.items(), key=lambda item: int(item[1])):
                session.virtwho_configure.edit(name, {'interval': option})
                results = session.virtwho_configure.read(name)
                assert results['overview']['interval'] == option
                deploy_configure_by_command(config_command, form_data['hypervisor_type'])
                assert get_configure_option('VIRTWHO_INTERVAL', VIRTWHO_SYSCONFIG) == value
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(self, session, form_data):
        """Verify Hypervisor ID dropdown options.

        :id: cc494bd9-51d9-452a-bfa9-5cdcafef5197

        :expectedresults:
            hypervisor_id can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to uuid/hwuuid/hostname.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id)
            config_file = get_configure_file(config_id)
            # esx and rhevm support hwuuid option
            values = ['uuid', 'hostname', 'hwuuid']
            for value in values:
                session.virtwho_configure.edit(name, {'hypervisor_id': value})
                results = session.virtwho_configure.read(name)
                assert results['overview']['hypervisor_id'] == value
                deploy_configure_by_command(config_command, form_data['hypervisor_type'])
                assert get_configure_option('hypervisor_id', config_file) == value
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_filtering_option(self, session, form_data):
        """Verify Filtering dropdown options.

        :id: e17dda14-79cd-4cd2-8f29-60970b24a905

        :expectedresults:
            1. if filtering is selected to Whitelist, 'Filter hosts' can be set.
            2. if filtering is selected to Blacklist, 'Exclude hosts' can be set.

        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 1735670
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id)
            config_file = get_configure_file(config_id)
            regex = '.*redhat.com'
            whitelist = {'filtering': 'Whitelist', 'filtering_content.filter_hosts': regex}
            blacklist = {'filtering': 'Blacklist', 'filtering_content.exclude_hosts': regex}
            # esx support filter-host-parents and exclude-host-parents options
            whitelist['filtering_content.filter_host_parents'] = regex
            blacklist['filtering_content.exclude_host_parents'] = regex
            # Update Whitelist and check the result
            session.virtwho_configure.edit(name, whitelist)
            results = session.virtwho_configure.read(name)
            assert results['overview']['filter_hosts'] == regex
            assert results['overview']['filter_host_parents'] == regex
            deploy_configure_by_command(config_command, form_data['hypervisor_type'])
            assert regex == get_configure_option('filter_hosts', config_file)
            assert regex == get_configure_option('filter_host_parents', config_file)
            # Update Blacklist and check the result
            session.virtwho_configure.edit(name, blacklist)
            results = session.virtwho_configure.read(name)
            assert results['overview']['exclude_hosts'] == regex
            assert results['overview']['exclude_host_parents'] == regex
            deploy_configure_by_command(config_command, form_data['hypervisor_type'])
            assert regex == get_configure_option('exclude_hosts', config_file)
            assert regex == get_configure_option('exclude_host_parents', config_file)
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_proxy_option(self, session, form_data):
        """Verify 'HTTP Proxy' and 'Ignore Proxy' options.

        :id: 6659d577-0135-4bf0-81af-14b930011536

        :expectedresults:
            http_proxy/https_proxy and NO_PROXY will be setting in /etc/sysconfig/virt-who.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        https_proxy, https_proxy_name, https_proxy_id = create_http_proxy()
        http_proxy, http_proxy_name, http_proxy_id = create_http_proxy(type='http')
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id)
            no_proxy = 'test.satellite.com'
            # Check the https proxy and No_PROXY settings
            session.virtwho_configure.edit(name, {'proxy': https_proxy, 'no_proxy': no_proxy})
            results = session.virtwho_configure.read(name)
            assert results['overview']['proxy'] == https_proxy
            assert results['overview']['no_proxy'] == no_proxy
            deploy_configure_by_command(config_command, form_data['hypervisor_type'])
            assert get_configure_option('https_proxy', VIRTWHO_SYSCONFIG) == https_proxy
            assert get_configure_option('NO_PROXY', VIRTWHO_SYSCONFIG) == no_proxy
            # Check the http proxy setting
            session.virtwho_configure.edit(name, {'proxy': http_proxy})
            results = session.virtwho_configure.read(name)
            assert results['overview']['proxy'] == http_proxy
            deploy_configure_by_command(config_command, form_data['hypervisor_type'])
            assert get_configure_option('http_proxy', VIRTWHO_SYSCONFIG) == http_proxy
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_virtwho_roles(self, session):
        """Verify the default roles for virtwho configure

        :id: cd6a5363-f9ba-4b52-892c-905634168fc5

        :expectedresults:
            'Virt-who Manager', 'Virt-who Reporter', 'Virt-who Viewer' existing

        :CaseLevel: Integration

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
        with session:
            for role_name, role_filters in roles.items():
                assert session.role.search(role_name)[0]['Name'] == role_name
                assigned_permissions = session.filter.read_permissions(role_name)
                assert sorted(assigned_permissions) == sorted(role_filters)

    @pytest.mark.tier2
    def test_positive_virtwho_configs_widget(self, session, form_data):
        """Check if Virt-who Configurations Status Widget is working in the Dashboard UI

        :id: 5d61ce00-a640-4823-89d4-7b1d02b50ea6

        :Steps:

            1. Create a Virt-who Configuration
            2. Navigate Monitor -> Dashboard
            3. Review the Virt-who Configurations Status widget

        :expectedresults: The widget is updated with all details.

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        org_name = gen_string('alpha')
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.organization.create({'name': org_name})
            session.organization.select(org_name)
            session.virtwho_configure.create(form_data)
            expected_values = [
                {'Configuration Status': 'No Reports', 'Count': '1'},
                {'Configuration Status': 'No Change', 'Count': '0'},
                {'Configuration Status': 'OK', 'Count': '0'},
                {'Configuration Status': 'Total Configurations', 'Count': '1'},
            ]
            values = session.dashboard.read('VirtWhoConfigStatus')
            assert values['config_status'] == expected_values
            assert values['latest_config'] == 'No configuration found'
            # Check the 'Status' changed after deployed the virt-who config
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id, org_name)
            deploy_configure_by_command(config_command, form_data['hypervisor_type'])
            assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            expected_values = [
                {'Configuration Status': 'No Reports', 'Count': '0'},
                {'Configuration Status': 'No Change', 'Count': '0'},
                {'Configuration Status': 'OK', 'Count': '1'},
                {'Configuration Status': 'Total Configurations', 'Count': '1'},
            ]
            values = session.dashboard.read('VirtWhoConfigStatus')
            assert values['config_status'] == expected_values
            assert values['latest_config'] == 'No configuration found'
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)
            session.organization.select("Default Organization")
            session.organization.delete(org_name)

    @pytest.mark.tier2
    def test_positive_delete_configure(self, session, form_data):
        """Verify when a config is deleted the associated user is deleted.

        :id: 0e66dcf6-dc64-4fb2-b8a9-518f5adfa800

        :steps:
            1. Create a virt-who configuration and deploy it to a
               virt-who server.
            2. Delete the configuration on the Satellite.

        :expectedresults:
            1. Verify the virt-who server can no longer connect to the
               Satellite.

        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id)
            deploy_configure_by_command(config_command, form_data['hypervisor_type'])
            assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)
            restart_virtwho_service()
            assert get_virtwho_status() == 'logerror'

    @pytest.mark.tier2
    def test_positive_virtwho_reporter_role(self, session, test_name, form_data):
        """Verify the virt-who reporter role can TRULY work.

        :id: cd235ab0-d89c-464b-98d6-9d090ac40d8f

        :expectedresults:
            Virt-who Reporter Role granting minimal set of permissions for virt-who
            to upload the report, it can be used if you configure virt-who manually
            and want to use user that has locked down account.
        """
        username = gen_string('alpha')
        password = gen_string('alpha')
        config_name = gen_string('alpha')
        with session:
            # Create an user
            session.user.create(
                {
                    'user.login': username,
                    'user.mail': valid_emails_list()[0],
                    'user.auth': 'INTERNAL',
                    'user.password': password,
                    'user.confirm': password,
                }
            )
            # Create a virt-who config plugin
            form_data['name'] = config_name
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(config_name)
            command = values['deploy']['command']
            deploy_configure_by_command(command, form_data['hypervisor_type'])
            assert session.virtwho_configure.search(config_name)[0]['Status'] == 'ok'
            # Update the virt-who config file
            config_id = get_configure_id(config_name)
            config_file = get_configure_file(config_id)
            update_configure_option('rhsm_username', username, config_file)
            delete_configure_option('rhsm_encrypted_password', config_file)
            add_configure_option('rhsm_password', password, config_file)
            restart_virtwho_service()
            assert get_virtwho_status() == 'logerror'
            # Check the permissioin of Virt-who Reporter
            session.user.update(username, {'roles.resources.assigned': ['Virt-who Reporter']})
            assert session.user.search(username)[0]['Username'] == username
            user = session.user.read(username)
            assert user['roles']['resources']['assigned'] == ['Virt-who Reporter']
            restart_virtwho_service()
            assert get_virtwho_status() == 'running'
            with Session(test_name, username, password) as newsession:
                assert not newsession.virtwho_configure.check_create_permission()['can_view']
            session.user.delete(username)
            assert not session.user.search(username)

    @pytest.mark.tier2
    def test_positive_virtwho_viewer_role(self, session, test_name, form_data):
        """Verify the virt-who viewer role can TRULY work.

        :id: bf3be2e4-3853-41cc-9b3e-c8677f0b8c5f

        :expectedresults:
            Virt-who Viewer Role granting permissions to see all configurations
            including their configuration scripts, which means viewers could still
            deploy the virt-who instances for existing virt-who configurations.
        """
        username = gen_string('alpha')
        password = gen_string('alpha')
        config_name = gen_string('alpha')
        with session:
            # Create an user
            session.user.create(
                {
                    'user.login': username,
                    'user.mail': valid_emails_list()[0],
                    'user.auth': 'INTERNAL',
                    'user.password': password,
                    'user.confirm': password,
                }
            )
            # Create a virt-who config plugin
            form_data['name'] = config_name
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(config_name)
            command = values['deploy']['command']
            deploy_configure_by_command(command, form_data['hypervisor_type'])
            assert session.virtwho_configure.search(config_name)[0]['Status'] == 'ok'
            # Check the permissioin of Virt-who Viewer
            session.user.update(username, {'roles.resources.assigned': ['Virt-who Viewer']})
            user = session.user.read(username)
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
            session.user.delete(username)
            assert not session.user.search(username)

    @pytest.mark.tier2
    def test_positive_virtwho_manager_role(self, session, test_name, form_data):
        """Verify the virt-who manager role can TRULY work.

        :id: a72023fb-7b23-4582-9adc-c5227dc7859c

        :expectedresults:
            Virt-who Manager Role granting all permissions to manage virt-who configurations,
            user needs this role to create, delete or update configurations.
        """
        username = gen_string('alpha')
        password = gen_string('alpha')
        config_name = gen_string('alpha')
        with session:
            # Create an user
            session.user.create(
                {
                    'user.login': username,
                    'user.mail': valid_emails_list()[0],
                    'user.auth': 'INTERNAL',
                    'user.password': password,
                    'user.confirm': password,
                }
            )
            # Create a virt-who config plugin
            form_data['name'] = config_name
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(config_name)
            command = values['deploy']['command']
            deploy_configure_by_command(command, form_data['hypervisor_type'])
            assert session.virtwho_configure.search(config_name)[0]['Status'] == 'ok'
            # Check the permissioin of Virt-who Manager
            session.user.update(username, {'roles.resources.assigned': ['Virt-who Manager']})
            user = session.user.read(username)
            assert user['roles']['resources']['assigned'] == ['Virt-who Manager']
            with Session(test_name, username, password) as newsession:
                # create_virt_who_config
                new_virt_who_name = gen_string('alpha')
                form_data['name'] = new_virt_who_name
                newsession.virtwho_configure.create(form_data)
                # view_virt_who_config
                values = newsession.virtwho_configure.read(new_virt_who_name)
                command = values['deploy']['command']
                deploy_configure_by_command(command, form_data['hypervisor_type'])
                assert newsession.virtwho_configure.search(new_virt_who_name)[0]['Status'] == 'ok'
                # edit_virt_who_config
                modify_name = gen_string('alpha')
                newsession.virtwho_configure.edit(new_virt_who_name, {'name': modify_name})
                newsession.virtwho_configure.search(modify_name)
                # destroy_virt_who_config
                newsession.virtwho_configure.delete(modify_name)
                assert not newsession.virtwho_configure.search(modify_name)
            # Delete the created user
            session.user.delete(username)
            assert not session.user.search(username)

    @pytest.mark.tier2
    def test_positive_overview_label_name(self, form_data, session):
        """Verify the label name on virt-who config Overview Page.

        :id: 21df8175-bb41-422e-a263-8677bc3a9565

        :BZ: 1649928

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        form_data['name'] = name
        hypervisor_type = form_data['hypervisor_type']
        http_proxy_url, proxy_name, proxy_id = create_http_proxy()
        form_data['proxy'] = http_proxy_url
        form_data['no_proxy'] = 'test.satellite.com'
        regex = '.*redhat.com'
        whitelist = {'filtering': 'Whitelist', 'filtering_content.filter_hosts': regex}
        blacklist = {'filtering': 'Blacklist', 'filtering_content.exclude_hosts': regex}
        if hypervisor_type == 'esx':
            whitelist['filtering_content.filter_host_parents'] = regex
            blacklist['filtering_content.exclude_host_parents'] = regex
        form_data = dict(form_data, **whitelist)
        with session:
            session.virtwho_configure.create(form_data)
            fields = {
                'status_label': 'Status',
                'hypervisor_type_label': 'Hypervisor Type',
                'hypervisor_server_label': 'Hypervisor Server',
                'hypervisor_username_label': 'Hypervisor Username',
                'interval_label': 'Interval',
                'satellite_url_label': 'Satellite server FQDN',
                'hypervisor_id_label': 'Hypervisor ID',
                'debug_label': 'Enable debugging output?',
                'filtering_label': 'Filtering',
                'filter_hosts_label': 'Filter Hosts',
                'proxy_label': 'HTTP Proxy',
                'no_proxy_label': 'Ignore Proxy',
            }
            if hypervisor_type == 'kubevirt':
                del fields['hypervisor_username_label']
                del fields['hypervisor_server_label']
                fields['kubeconfig_path_label'] = 'Kubeconfig Path'
            if hypervisor_type == 'esx':
                fields['filter_host_parents_label'] = 'Filter Host Parents'
            results = session.virtwho_configure.read(name)
            for key, value in fields.items():
                assert results['overview'][key] == value
            session.virtwho_configure.edit(name, blacklist)
            results = session.virtwho_configure.read(name)
            del fields['filter_hosts_label']
            if hypervisor_type == 'esx':
                del fields['filter_host_parents_label']
                fields['exclude_host_parents_label'] = 'Exclude Host Parents'
            fields['exclude_hosts_label'] = 'Exclude Hosts'
            for key, value in fields.items():
                assert results['overview'][key] == value
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_last_checkin_status(self, form_data, session):
        """Verify the Last Checkin status on Content Hosts Page.

        :id: 7448d482-d05c-4727-8980-176586e9e4a7

        :expectedresults: The Last Checkin time on Content Hosts Page is client date time

        :BZ: 1652323

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(name, widget_names='deploy.command')
            command = values['deploy']['command']
            hypervisor_name, guest_name = deploy_configure_by_command(
                command, form_data['hypervisor_type'], debug=True
            )
            time_now = session.browser.get_client_datetime()
            assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            checkin_time = session.contenthost.search(hypervisor_name)[0]['Last Checkin']
            # 10 mins margin to check the Last Checkin time
            assert (
                abs(
                    datetime.strptime(checkin_time, "%B %d, %Y, %I:%M %p")
                    .replace(year=datetime.utcnow().year)
                    .timestamp()
                    - time_now.timestamp()
                )
                <= 300
            )
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)
