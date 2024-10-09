"""Test class for Ansible-ConfigurationManagement and Ansible-RemoteExecution components

:Requirement: Ansible

:CaseAutomation: Automated

:Team: Rocket

:CaseImportance: Critical
"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for
import yaml

from robottelo import constants
from robottelo.config import (
    admin_nailgun_config,
    robottelo_tmp_dir,
    settings,
    user_nailgun_config,
)
from robottelo.utils.issue_handlers import is_open


class TestAnsibleCfgMgmt:
    """Test class for Configuration Management with Ansible

    :CaseComponent: Ansible-ConfigurationManagement
    """

    @pytest.mark.tier3
    @pytest.mark.parametrize('auth_type', ['admin', 'non-admin'])
    def test_positive_create_delete_variable_with_overrides(
        self, request, function_org, target_sat, auth_type
    ):
        """Create an Ansible variable with all values populated.

        :id: 90acea37-4c2f-42e5-92a6-0c88148f4fb6

        :customerscenario: true

        :Verifies: SAT-19619

        :steps:
            1. Import Ansible roles if none have been imported yet.
            2. Create an Anible variable, populating all fields on the creation form.
            3. Verify that the Ansible variable was created successfully.
            4. Delete the Ansible variable.
            5. Verify that the Ansible Variable has been deleted.

        :expectedresults: The variable is successfully created.
        """
        user_cfg = admin_nailgun_config()
        password = settings.server.admin_password
        key = gen_string('alpha')
        param_type = 'integer'
        if auth_type == 'non-admin':
            ansible_manager_role = target_sat.api.Role().search(
                query={'search': 'name="Ansible Roles Manager"'}
            )
            user = target_sat.api.User(
                role=ansible_manager_role,
                admin=False,
                login=gen_string('alphanumeric'),
                password=password,
                organization=[function_org],
            ).create()
            request.addfinalizer(user.delete)
            user_cfg = user_nailgun_config(user.login, password)

        SELECTED_ROLE = 'redhat.satellite.activation_keys'
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles(server_config=user_cfg).sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
        with target_sat.ui_session(user=user_cfg.auth[0], password=password) as session:
            session.organization.select(function_org.name)
            session.ansiblevariables.create_with_overrides(
                {
                    'key': key,
                    'description': gen_string(str_type='alpha'),
                    'ansible_role': SELECTED_ROLE,
                    'parameter_type': param_type,
                    'default_value': '11',
                    'validator_type': 'list',
                    'validator_rule': '11, 12, 13',
                    'attribute_order': 'domain \n fqdn \n hostgroup \n os',
                    'matcher_section.params': [
                        {
                            'attribute_type': {'matcher_key': 'os', 'matcher_value': 'fedora'},
                            'value': '13',
                        }
                    ],
                }
            )
            result = session.ansiblevariables.search(key)[0]
            assert result['Name'] == key
            assert result['Role'] == SELECTED_ROLE
            assert result['Type'] == param_type
            assert result['Imported?'] == ''

            session.ansiblevariables.delete(key)
            assert not session.ansiblevariables.search(key)

    @pytest.mark.tier2
    def test_positive_host_role_information(self, target_sat, function_host):
        """Assign Ansible Role to a Host and verify that the information
        in the new UI is displayed correctly

        :id: 7da913ef-3b43-4bfa-9a45-d895431c8b56

        :steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Assign one role to the RHEL host.
            4. Navigate to the new UI for the given Host.
            5. Select the 'Ansible' tab, then the 'Inventory' sub-tab.

        :expectedresults: Roles assigned directly to the Host are visible on the subtab.
        """
        SELECTED_ROLE = 'RedHatInsights.insights-client'

        location = function_host.location.read()
        organization = function_host.organization.read()
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles().sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
        target_sat.cli.Host.ansible_roles_assign(
            {'id': function_host.id, 'ansible-roles': SELECTED_ROLE}
        )
        host_roles = function_host.list_ansible_roles()
        assert host_roles[0]['name'] == SELECTED_ROLE
        with target_sat.ui_session() as session:
            session.organization.select(organization.name)
            session.location.select(location.name)
            ansible_roles_table = session.host_new.get_ansible_roles(function_host.name)
            assert ansible_roles_table[0]['Name'] == SELECTED_ROLE
            all_assigned_roles_table = session.host_new.get_ansible_roles_modal(function_host.name)
            assert all_assigned_roles_table[0]['Name'] == SELECTED_ROLE

    @pytest.mark.rhel_ver_match('8')
    def test_positive_assign_ansible_role_variable_on_host(
        self,
        request,
        target_sat,
        rhel_contenthost,
        module_activation_key,
        module_org,
        module_location,
    ):
        """Verify ansible variable is added to the role and attached to the host.

        :id: 7ec4fe19-5a08-4b10-bb4e-7327dd68699a

        :BZ: 2170727

        :customerscenario: true

        :steps:
            1. Create an Ansible variable with array type and set the default value.
            2. Enable both 'Merge Overrides' and 'Merge Default'.
            3. Add the variable to a role and attach the role to the host.
            4. Verify that ansible role and variable is added to the host.

        :expectedresults: The role and variable is successfully added to the host.
        """

        @request.addfinalizer
        def _finalize():
            result = target_sat.cli.Ansible.variables_delete({'name': key})
            assert f'Ansible variable [{key}] was deleted.' in result[0]['message']
            for role in SELECTED_ROLE:
                result = target_sat.cli.Ansible.roles_delete({'name': role})
                assert f'Ansible role [{role}] was deleted.' in result[0]['message']

        key = gen_string('alpha')
        SELECTED_ROLE = ['redhat.satellite.activation_keys', 'RedHatInsights.insights-client']
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles().sync(data={'proxy_id': proxy_id, 'role_names': SELECTED_ROLE})
        result = rhel_contenthost.api_register(
            target_sat,
            organization=module_org,
            activation_keys=[module_activation_key.name],
            location=module_location,
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'

        target_host = rhel_contenthost.nailgun_host
        default_value = '[\"test\"]'  # fmt: skip
        parameter_type = 'array'
        with target_sat.ui_session() as session:
            session.organization.select(org_name=module_org.name)
            session.location.select(loc_name=module_location.name)
            session.ansiblevariables.create_with_overrides(
                {
                    'key': key,
                    'ansible_role': SELECTED_ROLE[0],
                    'override': 'true',
                    'parameter_type': parameter_type,
                    'default_value': default_value,
                    'validator_type': None,
                    'attribute_order': 'domain \n fqdn \n hostgroup \n os',
                    'merge_default': 'true',
                    'merge_overrides': 'true',
                    'matcher_section.params': [
                        {
                            'attribute_type': {'matcher_key': 'os', 'matcher_value': 'fedora'},
                            'value': '[\'13\']',
                        }
                    ],
                }
            )
            result = target_sat.cli.Host.ansible_roles_assign(
                {'id': target_host.id, 'ansible-roles': ','.join(SELECTED_ROLE)}
            )
            assert 'Ansible roles were assigned' in result[0]['message']

            values = session.host_new.get_details(rhel_contenthost.hostname, 'ansible')['ansible']
            roles_table = values['roles']['table']
            variable_table = values['variables']['table']
            for role in SELECTED_ROLE:
                var_count = str(len([v for v in variable_table if v['Ansible role'] == role]))
                assert (role, var_count) in [(r['Name'], r['Variables']) for r in roles_table]

            assert (key, SELECTED_ROLE[0], parameter_type, default_value) in [
                (v['Name'], v['Ansible role'], v['Type'], v['Value']) for v in variable_table
            ]

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_ansible_roles_ignore_list(self):
        """Verify that the ignore list setting prevents selected roles from being available for import

        :id: 6fa1d8f0-b583-4a07-88eb-c9ae7fcd0219

        :steps:
            1. Add roles to the ignore list in Administer > Settings > Ansible
            2. Navigate to Configure > Roles

        :expectedresults: Verify that any roles on the ignore list are not available for import

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_set_ansible_role_order_per_host(self):
        """Verify that role run order can be set and this order is respected when roles are run

        :id: 24fbcd60-7cd1-46ff-86ac-16d6b436202c

        :steps:
            1. Enable a host for remote execution
            2. Navigate to Hosts > All Hosts > $hostname > Edit > Ansible Roles
            3. Assign more than one role to the host
            4. Use the drag-and-drop mechanism to change the order of the roles
            5. Run Ansible roles on the host

        :expectedresults: The roles are run in the specified order

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_set_ansible_role_order_per_hostgroup(self):
        """Verify that role run order can be set and that this order is respected when roles are run

        :id: 9eb5bc8e-081a-45b9-8751-f4220c944da6

        :steps:
            1. Enable a host for remote execution
            2. Create a host group
            3. Navigate to Configure > Host Groups > $hostgroup > Ansible Roles
            4. Assign more than one role to the host group
            5. Use the drag-and-drop mechanism to change the order of the roles
            6. Add the host to the host group
            7. Run Ansible roles on the host group

        :expectedresults: The roles are run in the specified order

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.tier2
    def test_positive_assign_and_remove_ansible_role_to_host(self, target_sat, function_host):
        """Add and remove the role(s) of a Host

        :id: a61b4c05-1395-47c2-b6d9-fcff8b094e0e

        :setup: Used pre-defined function_host (component/host) registerd with satellite.

        :steps:
            1. Import all roles available by default.
            2. Assign a role to the host.
            3. Navigate to the new UI for the given Host.
            4. Select the 'Ansible' tab
            5. Click the 'Edit Ansible roles' button.
            6. Using the popup, remove the assigned role from the Host.

        :expectedresults: The Role is successfully aaded and removed from the Host, and no longer shows
            up on the UI
        """
        SELECTED_ROLE = 'RedHatInsights.insights-client'

        location = function_host.location.read()
        organization = function_host.organization.read()
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles().sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
        with target_sat.ui_session() as session:
            session.location.select(location.name)
            session.organization.select(organization.name)
            # add ansible role
            session.host_new.add_single_ansible_role(function_host.name, SELECTED_ROLE)
            wait_for(lambda: session.browser.refresh(), timeout=5)
            # verify ansible role assigned to new UI for the given Host
            ansible_roles_table = session.host_new.get_ansible_roles(function_host.name)
            assert ansible_roles_table[0]['Name'] == SELECTED_ROLE
            # remove ansible role
            session.host_new.remove_single_ansible_role(function_host.name)
            # verify ansible role removed
            result = session.host_new.get_details(
                function_host.name, widget_names='ansible.roles.noRoleAssign'
            )
            assert (
                result['ansible']['roles']['noRoleAssign']
                == 'No roles assigned directly to the host'
            )

    @pytest.mark.tier2
    def test_positive_assign_and_remove_ansible_role_to_hostgroup(
        self,
        target_sat,
        module_org,
        module_location,
    ):
        """Add and remove functionality for ansible roles in hostgroup

        :id: 5d94a484-92c1-4387-ab92-0649e4c4f907

        :steps:
            1. Import all roles available by default.
            2. Assign ansible role while creating the hostgroup
            3. Assign ansible role after creating the hostgroup
            4. Remove previously added ansible roles from the hostgroup

        :expectedresults: The Ansible Role is successfully added and removed from the hostgroup
        """
        SELECTED_ROLE = [
            'RedHatInsights.insights-client',
            'redhat.satellite.hostgroups',
            'redhat.satellite.compute_profiles',
        ]
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles().sync(data={'proxy_id': proxy_id, 'role_names': SELECTED_ROLE})
        name = gen_string('alpha').lower()
        with target_sat.ui_session() as session:
            session.location.select(module_location.name)
            session.organization.select(module_org.name)
            # Assign Ansible role(s) while creating the hostgroup.
            session.hostgroup.create(
                {
                    'host_group.name': name,
                    'ansible_roles.resources': SELECTED_ROLE[:2],
                }
            )
            # verify ansible role(s) assigned properly while creating a host group.
            assert session.hostgroup.read_role(name, SELECTED_ROLE) == SELECTED_ROLE[:2]

            session.hostgroup.assign_role_to_hostgroup(
                name, {'ansible_roles.resources': SELECTED_ROLE[2]}
            )
            # verify ansible role(s) assigned properly after creating the hostgroup.
            assert SELECTED_ROLE[2] in session.hostgroup.read_role(name, SELECTED_ROLE)

            session.hostgroup.remove_hostgroup_role(
                name, {'ansible_roles.resources': SELECTED_ROLE[0]}
            )
            # verify ansible role(s) removed properly from the host group.
            assert SELECTED_ROLE[0] not in session.hostgroup.read_role(name, SELECTED_ROLE)
            assert SELECTED_ROLE[1:] == session.hostgroup.read_role(name, SELECTED_ROLE)

            # Delete host group
            session.hostgroup.delete(name)
            assert not target_sat.api.HostGroup().search(query={'search': f'name={name}'})

    @pytest.mark.tier3
    def test_positive_non_admin_user_access_with_usergroup(
        self,
        request,
        module_org,
        module_location,
        target_sat,
        test_name,
    ):
        """Verify non-admin user can access the ansible page on WebUI

        :id: 82d30664-1b74-457c-92e2-31a5ba89e826

        :steps:
            1. Create user with non-admin
            2. Create usergroup with administrator role
            3. Log in as a user and try to access WebUI -> Hosts -> select host -> Ansible
            4. Assign ansible role to the host

        :expectedresults: The user is able to view the Ansible page and assign roles because they are an administrator due to user group

        :BZ: 2158508

        :Verifies: SAT-15826

        :customerscenario: true
        """
        SELECTED_ROLE = 'RedHatInsights.insights-client'
        name = gen_string('alpha')
        password = gen_string('alpha')
        host = target_sat.api.Host(organization=module_org, location=module_location).create()
        user = target_sat.api.User(
            login=name,
            password=password,
            location=[module_location],
            organization=[module_org],
            admin=False,
        ).create()
        request.addfinalizer(user.delete)
        user_gp = target_sat.api.UserGroup(
            name=gen_string('alpha'), user=[user], admin=True
        ).create()
        assert user.login in [u.read().login for u in user_gp.user]
        id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles().sync(data={'proxy_id': id, 'role_names': [SELECTED_ROLE]})
        with target_sat.ui_session(test_name, user=user.login, password=password) as session:
            session.location.select(module_location.name)
            session.organization.select(module_org.name)
            session.host_new.add_single_ansible_role(host.name, SELECTED_ROLE)
            wait_for(lambda: session.browser.refresh(), timeout=5)
            ansible_roles_table = session.host_new.get_ansible_roles(host.name)
            assert ansible_roles_table[0]['Name'] == SELECTED_ROLE

    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    def test_positive_ansible_config_report_changes_notice_and_failed_tasks_errors(
        self,
        rhel_contenthost,
        module_target_sat,
        module_org,
        module_location,
        module_activation_key,
    ):
        """Check that Ansible tasks that make changes on a host show as notice in the config report and
        failed Ansible tasks show as errors in the config report

        :id: 286048f8-0f4f-4a3c-b5c7-fe9c7af8a780

        :steps:
            1. Import Ansible Roles
            2. Assign and Run Ansible roles to a host
            3. Run Ansible Roles on a host
            4. Check Config Report

        :expectedresults:
            1. Verify that any tasks that make changes on the host are listed as notice in the config report
            2. Verify that any task failures are listed as errors in the config report
        """
        SELECTED_ROLE = 'theforeman.foreman_scap_client'
        nc = module_target_sat.nailgun_smart_proxy
        nc.location = [module_location]
        nc.organization = [module_org]
        nc.update(['organization', 'location'])
        module_target_sat.api.AnsibleRoles().sync(
            data={'proxy_id': nc.id, 'role_names': SELECTED_ROLE}
        )
        rhel_ver = rhel_contenthost.os_version.major
        rhel_repo_urls = getattr(settings.repos, f'rhel{rhel_ver}_os', None)
        rhel_contenthost.create_custom_repos(**rhel_repo_urls)
        result = rhel_contenthost.register(
            module_org, module_location, module_activation_key.name, module_target_sat
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        with module_target_sat.ui_session() as session:
            session.location.select(module_location.name)
            session.organization.select(module_org.name)
            session.host_new.add_single_ansible_role(rhel_contenthost.hostname, SELECTED_ROLE)
            ansible_roles_table = session.host_new.get_ansible_roles(rhel_contenthost.hostname)
            assert ansible_roles_table[0]['Name'] == SELECTED_ROLE
            # Verify error log for config report after ansible role is executed
            session.host_new.run_job(rhel_contenthost.hostname)
            session.jobinvocation.wait_job_invocation_state(
                entity_name='Run ansible roles',
                host_name=rhel_contenthost.hostname,
                expected_state='failed',
            )
            err_log = session.configreport.search(rhel_contenthost.hostname)
            package_name = SELECTED_ROLE.split('.')[1]
            assert f'err Install the {package_name} package' in err_log['permission_denied']
            assert (
                'Execution error: Failed to install some of the specified packages'
                in err_log['permission_denied']
            )

            # Verify notice log for config report after ansible role is successfully executed
            rhel_contenthost.create_custom_repos(
                client_repo=settings.repos.satclient_repo[f'rhel{rhel_ver}']
            )
            result = rhel_contenthost.register(
                module_org,
                module_location,
                module_activation_key.name,
                module_target_sat,
                force=True,
            )
            assert result.status == 0, f'Failed to register host: {result.stderr}'
            session.host_new.run_job(rhel_contenthost.hostname)
            session.jobinvocation.wait_job_invocation_state(
                entity_name='Run ansible roles', host_name=rhel_contenthost.hostname
            )
            notice_log = session.configreport.search(rhel_contenthost.hostname)
            assert f'notice Install the {package_name} package' in notice_log['permission_denied']
            assert f'Installed: rubygem-{package_name}' in notice_log['permission_denied']


class TestAnsibleREX:
    """Test class for remote execution via Ansible

    :CaseComponent: Ansible-RemoteExecution
    """

    @pytest.mark.tier2
    @pytest.mark.pit_server
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_match('[^6]')
    def test_positive_config_report_ansible(
        self, target_sat, module_org, module_ak_with_cv, rhel_contenthost
    ):
        """Test Config Report generation with Ansible Jobs.

        :id: 118e25e5-409e-44ba-b908-217da9722576

        :steps:
            1. Register a content host with satellite
            2. Import a role into satellite
            3. Assign that role to a host
            4. Assert that the role was assigned to the host successfully
            5. Run the Ansible playbook associated with that role
            6. Check if the report is created successfully

        :expectedresults:
            1. Host should be assigned the proper role.
            2. Job report should be created.
        """
        SELECTED_ROLE = 'RedHatInsights.insights-client'
        if rhel_contenthost.os_version.major <= 7:
            rhel_contenthost.create_custom_repos(rhel7=settings.repos.rhel7_os)
            assert rhel_contenthost.execute('yum install -y insights-client').status == 0
        result = rhel_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        id = target_sat.nailgun_smart_proxy.id
        target_host = rhel_contenthost.nailgun_host
        target_sat.api.AnsibleRoles().sync(data={'proxy_id': id, 'role_names': [SELECTED_ROLE]})
        target_sat.cli.Host.ansible_roles_assign(
            {'id': target_host.id, 'ansible-roles': SELECTED_ROLE}
        )
        host_roles = target_host.list_ansible_roles()
        assert host_roles[0]['name'] == SELECTED_ROLE
        template_id = (
            target_sat.api.JobTemplate()
            .search(query={'search': 'name="Ansible Roles - Ansible Default"'})[0]
            .id
        )
        job = target_sat.api.JobInvocation().run(
            synchronous=False,
            data={
                'job_template_id': template_id,
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel_contenthost.hostname}',
            },
        )
        target_sat.wait_for_tasks(
            f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1000
        )
        result = target_sat.api.JobInvocation(id=job['id']).read()
        assert result.succeeded == 1
        with target_sat.ui_session() as session:
            session.organization.select(module_org.name)
            session.location.select(constants.DEFAULT_LOC)
            assert session.host.search(target_host.name)[0]['Name'] == rhel_contenthost.hostname
            session.configreport.search(rhel_contenthost.hostname)
            session.configreport.delete(rhel_contenthost.hostname)
            assert len(session.configreport.read()['table']) == 0

    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_match('9')
    @pytest.mark.parametrize('auth_type', ['admin', 'non-admin'])
    def test_positive_ansible_custom_role(
        self,
        auth_type,
        target_sat,
        module_org,
        module_ak_with_cv,
        rhel_contenthost,
        request,
    ):
        """
        Test Config report generation with Custom Ansible Role

        :id: 3551068a-ccfc-481c-b7ec-8fe2b8a802bf

        :steps:
            1. Register a content host with satellite
            2. Create a  custom role and import  into satellite
            3. Assign that role to a host
            4. Assert that the role was assigned to the host successfully
            5. Run the Ansible playbook associated with that role
            6. Check if the report is created successfully

        :expectedresults:
            1. Config report should be generated for a custom role run.

        :BZ: 2155392

        :customerscenario: true
        """
        user_cfg = admin_nailgun_config()
        password = settings.server.admin_password
        if auth_type == 'non-admin':
            ansible_manager_role = target_sat.api.Role().search(
                query={'search': 'name="Ansible Roles Manager"'}
            )
            username = gen_string('alphanumeric')
            target_sat.api.User(
                role=ansible_manager_role,
                admin=True,
                login=username,
                password=password,
                organization=[module_org],
            ).create()
            user_cfg = user_nailgun_config(username, password)

        @request.addfinalizer
        def _finalize():
            result = target_sat.cli.Ansible.roles_delete({'name': SELECTED_ROLE})
            assert f'Ansible role [{SELECTED_ROLE}] was deleted.' in result[0]['message']
            target_sat.execute(f'rm -rvf /etc/ansible/roles/{SELECTED_ROLE}')

        SELECTED_ROLE = gen_string('alphanumeric')
        playbook = f'{robottelo_tmp_dir}/playbook.yml'
        data = {
            'name': 'Copy ssh keys',
            'copy': {
                'src': '/var/lib/foreman-proxy/ssh/{{ item }}',
                'dest': '/root/.ssh',
                'owner': 'root',
                "group": 'root',
                'mode': '0400',
            },
            'with_items': ['id_rsa_foreman_proxy.pub', 'id_rsa_foreman_proxy'],
        }

        with open(playbook, 'w') as f:
            yaml.dump(data, f, sort_keys=False, default_flow_style=False)
        target_sat.execute(f'mkdir /etc/ansible/roles/{SELECTED_ROLE}')
        target_sat.put(playbook, f'/etc/ansible/roles/{SELECTED_ROLE}/playbook.yaml')

        result = rhel_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_host = rhel_contenthost.nailgun_host
        target_sat.api.AnsibleRoles(server_config=user_cfg).sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
        ROLE_ID = [
            target_sat.api.AnsibleRoles().search(query={'search': f'name={SELECTED_ROLE}'})[0].id
        ]
        # Assign first 2 roles to HG and verify it
        target_sat.api.Host(server_config=user_cfg, id=target_host.id).assign_ansible_roles(
            data={'ansible_role_ids': ROLE_ID}
        )
        host_roles = target_sat.api.Host(
            server_config=user_cfg, id=target_host.id
        ).list_ansible_roles()
        assert host_roles[0]['name'] == SELECTED_ROLE

        template_id = (
            target_sat.api.JobTemplate(server_config=user_cfg)
            .search(query={'search': 'name="Ansible Roles - Ansible Default"'})[0]
            .id
        )
        job = target_sat.api.JobInvocation(server_config=user_cfg).run(
            synchronous=False,
            data={
                'job_template_id': template_id,
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel_contenthost.hostname}',
            },
        )
        target_sat.wait_for_tasks(
            f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1000
        )
        result = target_sat.api.JobInvocation(server_config=user_cfg, id=job['id']).read()
        assert result.succeeded == 1

        with target_sat.ui_session(user=user_cfg.auth[0], password=password) as session:
            session.organization.select(module_org.name)
            session.location.select(constants.DEFAULT_LOC)
            assert session.host.search(target_host.name)[0]['Name'] == rhel_contenthost.hostname
            session.configreport.search(rhel_contenthost.hostname)
            session.configreport.delete(rhel_contenthost.hostname)
            assert len(session.configreport.read()['table']) == 0

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_ansible_job_check_mode(self):
        """Run a job on a host with enable_roles_check_mode parameter enabled

        :id: 7aeb7253-e555-4e28-977f-71f16d3c32e2

        :steps:
            1. Set the value of the ansible_roles_check_mode parameter to true on a host
            2. Associate one or more Ansible roles with the host
            3. Run Ansible roles against the host

        :expectedresults: Verify that the roles were run in check mode
                        (i.e. no changes were made on the host)

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    def test_positive_install_ansible_collection(
        self, rhel_contenthost, target_sat, module_org, module_ak_with_cv
    ):
        """Verify that Ansible collections can be installed on hosts via job invocations

        :id: d4096aef-f6fc-41b6-ae56-d19b1f49cd42

        :steps:
            1. Enable a host for remote execution
            2. Navigate to Hosts > Schedule Remote Job
            3. Select "Ansible Galaxy" as the job category
            4. Select "Ansible Collection - Install from Galaxy" as the job template
            5. Enter a collection in the ansible_collections_list field
            6. Click "Submit"

        :expectedresults: The Ansible collection is successfully installed on the host
        """
        client = rhel_contenthost
        # Enable Ansible repository and Install ansible or ansible-core package
        client.register(module_org, None, module_ak_with_cv.name, target_sat)
        rhel_repo_urls = getattr(settings.repos, f'rhel{client.os_version.major}_os', None)
        rhel_contenthost.create_custom_repos(**rhel_repo_urls)
        assert client.execute('dnf -y install ansible-core').status == 0

        with target_sat.ui_session() as session:
            session.organization.select(module_org.name)
            collections_names = 'oasis_roles.system'
            session.jobinvocation.run(
                {
                    'category_and_template.job_category': 'Ansible Galaxy',
                    'category_and_template.job_template': 'Ansible Collection - Install from Galaxy',
                    'target_hosts_and_inputs.targetting_type': 'Hosts',
                    'target_hosts_and_inputs.targets': client.hostname,
                    'target_hosts_and_inputs.ansible_collections_list': collections_names,
                    'advanced_fields.ansible_collections_path': '~/',
                }
            )
            job_description = f'Install collections \'{collections_names}\' from galaxy'
            session.jobinvocation.wait_job_invocation_state(
                entity_name=job_description, host_name=client.hostname
            )
            status = session.jobinvocation.read(
                entity_name=job_description, host_name=client.hostname
            )
            assert status['overview']['hosts_table'][0]['Status'] == 'success'

            collection_path = client.execute('ls ~/ansible_collections').stdout
            assert 'oasis_roles' in collection_path

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_schedule_recurring_host_job(self):
        """Using the new Host UI, schedule a recurring job on a Host

        :id: 5052be04-28ab-4349-8bee-851ef76e4ffa

        :steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Assign a role to host.
            4. Navigate to the new UI for the given Host.
            5. Select the Jobs subtab.
            6. Click the Schedule Recurring Job button, and using the popup, schedule a
                recurring Job.
            7. Navigate to Job Invocations.

        :expectedresults: Scheduled Job appears in the Job Invocation list at the appointed time
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_schedule_recurring_hostgroup_job(self):
        """Using the new recurring job scheduler, schedule a recurring job on a Hostgroup

        :id: c65db99b-11fe-4a32-89d0-0a4692b07efe

        :steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Assign a role to host.
            4. Navigate to the Host Group page.
            5. Select the "Configure Ansible Job" action.
            6. Click the Schedule Recurring Job button, and using the popup, schedule a
                recurring Job.
            7. Navigate to Job Invocations.

        :expectedresults: Scheduled Job appears in the Job Invocation list at the appointed time
        """

    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    @pytest.mark.parametrize('setting_update', ['ansible_verbosity'], indirect=True)
    def test_positive_ansible_job_with_verbose_stdout(
        self,
        request,
        target_sat,
        module_org,
        module_location,
        module_ak_with_cv,
        setting_update,
        registered_hosts,
    ):
        """Verify ansible_verbosity setting and dynflow console output for expected hosts

        :id: 06e0a95c-530b-11ef-a28c-36dcd2c0c415

        :steps:
            1. Select two or more hosts
            2. Run ansible roles on those hosts
            3. Check the Ansible job execution logs

        :expectedresults: Ansible job console stdout should mention the verbose logs for expected host instead of the all host present in the inventory.

        :BZ: 1912941

        :Verifies: SAT-12267, SAT-27757

        :customerscenario: true
        """
        if not is_open('SAT-27757'):
            setting_update.value = '3'
            setting_update.update({'value'})

            @request.addfinalizer
            def _finalize():
                setting_update.value = '0'
                setting_update.update({'value'})

        SELECTED_ROLE = 'RedHatInsights.insights-client'
        nc = target_sat.nailgun_smart_proxy
        nc.location = [module_location]
        nc.organization = [module_org]
        nc.update(['organization', 'location'])
        target_sat.api.AnsibleRoles().sync(data={'proxy_id': nc.id, 'role_names': SELECTED_ROLE})
        vm_hostnames = []
        for vm in registered_hosts:
            rhel_ver = vm.os_version.major
            rhel_repo_urls = getattr(settings.repos, f'rhel{rhel_ver}_os', None)
            vm.create_custom_repos(**rhel_repo_urls)
            result = vm.register(
                module_org, module_location, module_ak_with_cv.name, target_sat, force=True
            )
            assert result.status == 0, f'Failed to register host: {result.stderr}'
            vm_hostnames.append(vm.hostname)
        with target_sat.ui_session() as session:
            session.organization.select(module_org.name)
            session.location.select(module_location.name)
            session.host.play_ansible_roles('All')
            session.jobinvocation.wait_job_invocation_state(
                entity_name='Run ansible roles', host_name=vm_hostnames[0]
            )
            output = session.jobinvocation.read_dynflow_output('Run ansible roles', vm_hostnames[0])
            assert vm_hostnames[0] in output
            assert vm_hostnames[1] not in output
