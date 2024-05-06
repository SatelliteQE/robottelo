"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:CaseComponent: Ansible-ConfigurationManagement

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

pytestmark = [pytest.mark.destructive, pytest.mark.upgrade]


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


def test_positive_import_all_roles(target_sat):
    """Import all Ansible roles available by default.

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
    with target_sat.ui_session() as session:
        assert session.ansibleroles.import_all_roles() == session.ansibleroles.imported_roles_count
        assert int(session.ansiblevariables.read_total_variables()) > 0
        # The choice of role to be deleted is arbitrary; any of the roles present on Satellite
        # by default should work here.
        session.ansibleroles.delete('theforeman.foreman_scap_client')
        assert not session.ansibleroles.search('theforeman.foreman_scap_client')


@pytest.mark.parametrize('setting_update', ['entries_per_page=12'], indirect=True)
def test_positive_hostgroup_ansible_roles_tab_pagination(target_sat, setting_update):
    """Import all Ansible roles available by default.

    :id: 53fe3857-a08f-493d-93c7-3fed331ed392

    :steps:
        1. Navigate to the Configure > Roles page, and click the `Import from [hostname]` button
        2. Get total number of importable roles from pagination.
        3. Fill the `Select All` checkbox and click the `Submit` button
        4. Verify that number of imported roles == number of importable roles from step 2
        5. Navigate to Administer > Settings > General tab and update the entries_per_page setting
        6. Navigate to `Ansible Roles` tab in Hostgroup create and edit page
        7. Verify the new per page entry is updated in pagination list

    :expectedresults: All imported roles should be available on the webUI and properly paginated
        as per entries_per_page setting on create and edit hostgroup page.

    :BZ: 2166466, 2242915

    :customerscenario: true
    """
    setting_value = str(
        target_sat.api.Setting().search(query={'search': 'name=entries_per_page'})[0].value
    )
    with target_sat.ui_session() as session:
        imported_roles = session.ansibleroles.import_all_roles()
        total_role_count = str(session.ansibleroles.imported_roles_count)
        assert imported_roles == int(total_role_count)
        assert total_role_count > setting_value

        create_page = session.hostgroup.helper.read_filled_view(
            'New', read_widget_names=['ansible_roles.pagination']
        )
        assert create_page['ansible_roles']['pagination']['_items'].split()[2] == setting_value
        assert create_page['ansible_roles']['pagination']['_items'].split()[-2] == total_role_count

        hg = target_sat.api.HostGroup(name=gen_string('alpha')).create()
        edit_page = session.hostgroup.helper.read_filled_view(
            'Edit',
            navigation_kwargs={'entity_name': hg.name},
            read_widget_names=['ansible_roles.pagination'],
        )
        assert edit_page['ansible_roles']['pagination']['_items'].split()[2] == setting_value
        assert edit_page['ansible_roles']['pagination']['_items'].split()[-2] == total_role_count
