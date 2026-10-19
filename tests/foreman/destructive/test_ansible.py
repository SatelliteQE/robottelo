"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:CaseComponent: Ansible-ConfigurationManagement

:Team: Endeavour

:CaseImportance: High

"""

from datetime import UTC, datetime

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import TIMESTAMP_FMT

pytestmark = [pytest.mark.destructive, pytest.mark.upgrade]


@pytest.mark.foreman_installer
def test_positive_persistent_ansible_cfg_change(target_sat):
    """Check if changes in ansible.cfg are persistent after running satellite-installer

    :id: c22fcd47-8627-4230-aa1f-7d4fc8517a0e

    :steps:
        1. Update value in ansible.cfg.
        2. Verify value is updated in the file.
        3. Run "satellite-installer".
        4. Verify the changes are persistent in the file.

    :expectedresults: Changes in ansible.cfg are persistent after running
        "satellite-installer".

    :BZ: 1786358

    :customerscenario: true
    """
    ansible_cfg = '/etc/ansible/ansible.cfg'
    param = 'local_tmp = /tmp'
    command = f'''echo "{param}" >> {ansible_cfg}'''
    target_sat.execute(command)
    assert param in target_sat.execute(f'cat {ansible_cfg}').stdout.splitlines()
    target_sat.execute('satellite-installer')
    assert param in target_sat.execute(f'cat {ansible_cfg}').stdout.splitlines()


@pytest.mark.parametrize('auth_type', ['admin', 'non-admin'])
def test_positive_import_all_roles(request, target_sat, function_org, auth_type):
    """Import all available Ansible roles.

    :id: 53fe3857-a08f-493d-93c7-3fed331ed391

    :steps:
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
    target_sat.install_ansible_roles(['theforeman.foreman_scap_client'])
    proxy = target_sat.nailgun_smart_proxy.read()
    proxy.organization.append(function_org)
    proxy.update(['organization'])
    username = settings.server.admin_username
    password = settings.server.admin_password
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
            location=proxy.location,
        ).create()
        request.addfinalizer(user.delete)
        username = user.login
    with target_sat.ui_session(user=username, password=password) as session:
        session.organization.select(function_org.name)
        import_started_at = datetime.now(UTC).strftime(TIMESTAMP_FMT)
        available_roles_count = session.ansibleroles.import_all_roles()
        target_sat.wait_for_tasks(
            f'label = SyncRolesAndVariables and started_at >= "{import_started_at}"',
            poll_timeout=600,
        )
        session.browser.refresh()
        assert available_roles_count == session.ansibleroles.imported_roles_count
        assert int(session.ansiblevariables.read_total_variables()) > 0
        # Delete the standalone role installed for this scenario.
        session.ansibleroles.delete('theforeman.foreman_scap_client')
        assert not session.ansibleroles.search('theforeman.foreman_scap_client')


@pytest.mark.parametrize('setting_update', ['entries_per_page=12'], indirect=True)
def test_positive_hostgroup_ansible_roles_not_limited_by_page_size(
    target_sat, setting_update, function_org
):
    """All imported roles are available in hostgroup forms despite the default page size.

    :id: 53fe3857-a08f-493d-93c7-3fed331ed392

    :steps:
        1. Set entries_per_page to 12 and import more than 12 Ansible roles.
        2. Read the available roles on the hostgroup create form.
        3. Create a hostgroup and read the available roles on its edit form.

    :expectedresults: Both forms offer every imported role rather than only the first page.

    :BZ: 2166466, 2242915

    :customerscenario: true
    """
    proxy = target_sat.nailgun_smart_proxy.read()
    proxy.organization.append(function_org)
    proxy.update(['organization'])
    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        import_started_at = datetime.now(UTC).strftime(TIMESTAMP_FMT)
        session.ansibleroles.import_all_roles()
        target_sat.wait_for_tasks(
            f'label = SyncRolesAndVariables and started_at >= "{import_started_at}"',
            poll_timeout=600,
        )
        roles = target_sat.api.AnsibleRoles().search_json(query={'per_page': 'all'})['results']
        expected_roles = {role['name'] for role in roles}
        assert len(expected_roles) > int(setting_update.value)

        assert set(session.hostgroup.read_ansible_roles('New')) == expected_roles

        hg = target_sat.api.HostGroup(
            name=gen_string('alpha'), organization=[function_org]
        ).create()
        assert (
            set(session.hostgroup.read_ansible_roles('Edit', entity_name=hg.name)) == expected_roles
        )
