"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Ansible

:Assignee: sbible

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo import constants
from robottelo.config import settings


def test_positive_import_all_roles(target_sat):
    """Import all Ansible roles available by default.

    :id: 53fe3857-a08f-493d-93c7-3fed331ed391

    :Steps:

        1. Navigate to the Configure > Roles page.
        2. Click the `Import from [hostname]` button.
        3. Get total number of importable roles from pagination.
        4. Fill the `Select All` checkbox.
        5. Click the `Submit` button.
        6. Verify that number of imported roles == number of importable roles from step 3.
        7. Verify that Ansible variables have been imported along with roles.
        8. Delete an imported role.
        9. Verify that the role was successfully deleted.

    :expectedresults: All roles are imported successfully. One role is deleted successfully.
    """
    with target_sat.ui_session() as session:
        assert session.ansibleroles.import_all_roles() == session.ansibleroles.imported_roles_count
        assert int(session.ansiblevariables.read_total_variables()) > 0
        # The choice of role to be deleted is arbitrary; any of the roles present on Satellite
        # by default should work here.
        session.ansibleroles.delete('theforeman.foreman_scap_client')
        assert not session.ansibleroles.search('theforeman.foreman_scap_client')


def test_positive_create_and_delete_variable(target_sat):
    """Create an Ansible variable with the minimum required values, then delete the variable.

    :id: 7006d7c7-788a-4447-a564-d6b03ec06aaf

    :Steps:

        1. Import Ansible roles if none have been imported yet.
        2. Create an Ansible variable with only a name and an assigned Ansible role.
        3. Verify that the Ansible variable has been created.
        4. Delete the Ansible variable.
        5. Verify that the Ansible Variable has been deleted.

    :expectedresults: The variable is successfully created and deleted.
    """
    key = gen_string('alpha')
    role = 'redhat.satellite.activation_keys'
    with target_sat.ui_session() as session:
        if not session.ansibleroles.imported_roles_count:
            session.ansibleroles.import_all_roles()
        session.ansiblevariables.create(
            {
                'key': key,
                'ansible_role': role,
            }
        )
        assert session.ansiblevariables.search(key)[0]['Name'] == key
        session.ansiblevariables.delete(key)
        assert not session.ansiblevariables.search(key)


def test_positive_create_variable_with_overrides(target_sat):
    """Create an Ansible variable with all values populated.

    :id: 90acea37-4c2f-42e5-92a6-0c88148f4fb6

    :Steps:

        1. Import Ansible roles if none have been imported yet.
        2. Create an Anible variable, populating all fields on the creation form.
        3. Verify that the Ansible variable was created successfully.

    :expectedresults: The variable is successfully created.
    """
    key = gen_string('alpha')
    role = 'redhat.satellite.activation_keys'
    with target_sat.ui_session() as session:
        if not session.ansibleroles.imported_roles_count:
            session.ansibleroles.import_all_roles()
        session.ansiblevariables.create_with_overrides(
            {
                'key': key,
                'description': 'this is a description',
                'ansible_role': role,
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


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_config_report_ansible(session, target_sat, module_org, rhel_contenthost):
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
    rhel_contenthost.install_katello_ca(target_sat)
    rhel_contenthost.register_contenthost(module_org.label, force=True)
    assert rhel_contenthost.subscribed
    rhel_contenthost.add_rex_key(satellite=target_sat)
    id = target_sat.nailgun_smart_proxy.id
    target_host = rhel_contenthost.nailgun_host
    target_sat.api.AnsibleRoles().sync(data={'proxy_id': id, 'role_names': [SELECTED_ROLE]})
    target_host.assign_ansible_roles(data={'ansible_role_ids': [1]})
    host_roles = target_host.list_ansible_roles()
    assert host_roles[0]['name'] == SELECTED_ROLE
    with session:
        session.organization.select(module_org.name)
        session.location.select(constants.DEFAULT_LOC)
        assert session.host.search(target_host.name)[0]['Name'] == rhel_contenthost.hostname
        session.jobinvocation.run(
            {
                'job_category': 'Ansible Playbook',
                'job_template': 'Ansible Roles - Ansible Default',
                'search_query': f'name ^ {rhel_contenthost.hostname}',
            }
        )
        session.jobinvocation.wait_job_invocation_state(
            entity_name='Run ansible roles', host_name=rhel_contenthost.hostname
        )
        status = session.jobinvocation.read(
            entity_name='Run ansible roles', host_name=rhel_contenthost.hostname
        )
        assert status['overview']['hosts_table'][0]['Status'] == 'success'
        session.configreport.search(rhel_contenthost.hostname)
        session.configreport.delete(rhel_contenthost.hostname)
        assert len(session.configreport.read()['table']) == 0
