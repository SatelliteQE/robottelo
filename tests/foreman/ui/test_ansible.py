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
from robottelo.config import robottelo_tmp_dir, settings


class TestAnsibleCfgMgmt:
    """Test class for Configuration Management with Ansible

    :CaseComponent: Ansible-ConfigurationManagement
    """

    @pytest.mark.tier2
    def test_positive_create_and_delete_variable(self, target_sat):
        """Create an Ansible variable with the minimum required values, then delete the variable.

        :id: 7006d7c7-788a-4447-a564-d6b03ec06aaf

        :steps:
            1. Import Ansible roles if none have been imported yet.
            2. Create an Ansible variable with only a name and an assigned Ansible role.
            3. Verify that the Ansible variable has been created.
            4. Delete the Ansible variable.
            5. Verify that the Ansible Variable has been deleted.

        :expectedresults: The variable is successfully created and deleted.
        """
        key = gen_string('alpha')
        SELECTED_ROLE = 'redhat.satellite.activation_keys'
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles().sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
        with target_sat.ui_session() as session:
            session.ansiblevariables.create(
                {
                    'key': key,
                    'ansible_role': SELECTED_ROLE,
                }
            )
            assert session.ansiblevariables.search(key)[0]['Name'] == key
            session.ansiblevariables.delete(key)
            assert not session.ansiblevariables.search(key)

    @pytest.mark.tier3
    def test_positive_create_variable_with_overrides(self, target_sat):
        """Create an Ansible variable with all values populated.

        :id: 90acea37-4c2f-42e5-92a6-0c88148f4fb6

        :steps:
            1. Import Ansible roles if none have been imported yet.
            2. Create an Anible variable, populating all fields on the creation form.
            3. Verify that the Ansible variable was created successfully.
            4. Delete the Ansible variable.
            5. Verify that the Ansible Variable has been deleted.

        :expectedresults: The variable is successfully created.
        """
        key = gen_string('alpha')
        SELECTED_ROLE = 'redhat.satellite.activation_keys'
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles().sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
        with target_sat.ui_session() as session:
            session.ansiblevariables.create_with_overrides(
                {
                    'key': key,
                    'description': 'this is a description',
                    'ansible_role': SELECTED_ROLE,
                    'parameter_type': 'integer',
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
            assert session.ansiblevariables.search(key)[0]['Name'] == key
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
            result = target_sat.cli.Ansible.roles_delete({'name': SELECTED_ROLE})
            assert f'Ansible role [{SELECTED_ROLE}] was deleted.' in result[0]['message']

        key = gen_string('alpha')
        SELECTED_ROLE = 'redhat.satellite.activation_keys'
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_sat.api.AnsibleRoles().sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
        command = target_sat.api.RegistrationCommand(
            organization=module_org,
            location=module_location,
            activation_keys=[module_activation_key.name],
        ).create()
        result = rhel_contenthost.execute(command)
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
                    'ansible_role': SELECTED_ROLE,
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
                {'id': target_host.id, 'ansible-roles': SELECTED_ROLE}
            )
            assert 'Ansible roles were assigned' in result[0]['message']
            values = session.host_new.get_details(rhel_contenthost.hostname, 'ansible')['ansible'][
                'variables'
            ]['table']
            assert (key, SELECTED_ROLE, default_value, parameter_type) in [
                (var['Name'], var['Ansible role'], var['Value'], var['Type']) for var in values
            ]

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_role_variable_information(self):
        """Create and assign variables to an Ansible Role and verify that the information in
        the new UI is displayed correctly

        :id: 4ab2813a-6b83-4907-b104-0473465814f5

        :steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Create a host group and assign one of the Ansible roles to the host group.
            4. Assign the host to the host group.
            5. Assign one roles to the RHEL host.
            6. Create a variable and associate it with the role assigned to the Host.
            7. Create a variable and associate it with the role assigned to the Hostgroup.
            8. Navigate to the new UI for the given Host.
            9. Select the 'Ansible' tab, then the 'Variables' sub-tab.

        :expectedresults: The variables information for the given Host is visible.
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_assign_role_in_new_ui(self):
        """Using the new Host UI, assign a role to a Host

        :id: 044f38b4-cff2-4ddc-b93c-7e9f2826d00d

        :steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Navigate to the new UI for the given Host.
            4. Select the 'Ansible' tab
            5. Click the 'Assign Ansible Roles' button.
            6. Using the popup, assign a role to the Host.

        :expectedresults: The Role is successfully assigned to the Host, and visible on the UI
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_remove_role_in_new_ui(self):
        """Using the new Host UI, remove the role(s) of a Host

        :id: d6de5130-45f6-4349-b490-fbde2aed082c

        :steps:
            1. Register a RHEL host to Satellite.
            2. Import all roles available by default.
            3. Assign a role to the host.
            4. Navigate to the new UI for the given Host.
            5. Select the 'Ansible' tab
            6. Click the 'Edit Ansible roles' button.
            7. Using the popup, remove the assigned role from the Host.

        :expectedresults: Role is successfully removed from the Host, and not visible on the UI
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_ansible_config_report_failed_tasks_errors(self):
        """Check that failed Ansible tasks show as errors in the config report

        :id: 1a91e534-143f-4f35-953a-7ad8b7d2ddf3

        :steps:
            1. Import Ansible roles
            2. Assign Ansible roles to a host
            3. Run Ansible roles on host

        :expectedresults: Verify that any task failures are listed as errors in the config report

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_ansible_config_report_changes_notice(self):
        """Check that Ansible tasks that make changes on a host show as notice in the config report

        :id: 8c90f179-8b70-4932-a477-75dc3566c437

        :steps:
            1. Import Ansible Roles
            2. Assign Ansible roles to a host
            3. Run Ansible Roles on a host

        :expectedresults: Verify that any tasks that make changes on the host
                        are listed as notice in the config report

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_ansible_variables_imported_with_roles(self):
        """Verify that, when Ansible roles are imported, their variables are imported simultaneously

        :id: 107c53e8-5a8a-4291-bbde-fbd66a0bb85e

        :steps:
            1. Import Ansible roles
            2. Navigate to Configure > Variables

        :expectedresults: Verify that any variables in the role were also imported to Satellite

        :CaseAutomation: NotAutomated
        """

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
    def test_positive_ansible_variables_installed_with_collection(self):
        """Verify that installing an Ansible collection also imports
        any variables associated with the collection

        :id: 7ff88022-fe9b-482f-a6bb-3922036a1e1c

        :steps:
            1. Install an Ansible collection
            2. Navigate to Configure > Variables

        :expectedresults: Verify that any variables associated with the collection
            are present on Configure > Variables

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
            session.host_new.add_single_ansible_role(function_host.name)
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
    def test_positive_ansible_custom_role(
        self, target_sat, module_org, module_ak_with_cv, rhel_contenthost, request
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

        @request.addfinalizer
        def _finalize():
            result = target_sat.cli.Ansible.roles_delete({'name': SELECTED_ROLE})
            assert f'Ansible role [{SELECTED_ROLE}] was deleted.' in result[0]['message']
            target_sat.execute('rm -rvf /etc/ansible/roles/custom_role')

        SELECTED_ROLE = 'custom_role'
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
        target_sat.execute('mkdir /etc/ansible/roles/custom_role')
        target_sat.put(playbook, '/etc/ansible/roles/custom_role/playbook.yaml')

        result = rhel_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_host = rhel_contenthost.nailgun_host
        target_sat.api.AnsibleRoles().sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
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

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_install_ansible_collection_via_job_invocation(self):
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

        :CaseAutomation: NotAutomated
        """

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
