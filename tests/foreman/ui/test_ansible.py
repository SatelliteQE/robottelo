"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Ansible

:Assignee: dsynk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.datafactory import gen_string


def test_positive_import_all_roles(target_sat):
    """Import all Ansible roles available by default.

    :id: 53fe3857-a08f-493d-93c7-3fed331ed391

    :Steps:

        1. Navigate to the Configure > Roles page.
        2. Click the `Import from [hostname]` button.
        3. Get totally number of importable roles from pagination?
        4. Fill the `Select All` checkbox.
        5. Click the `Submit` button.
        6. Verify that number of imported roles == number of importable roles from step 3.
        7. Verify that Ansible variables have been imported along with roles.

    :expectedresults: All roles are imported successfully.
    """
    with target_sat.ui_session as session:
        available_roles_count = session.ansibleroles.import_all_roles()
        imported_roles_count = session.ansibleroles.imported_roles_count
        assert available_roles_count == imported_roles_count
        ansible_variables_count = int(session.ansiblevariables.read_total_variables())
        assert ansible_variables_count > 0
        delete_role = 'theforeman.foreman_scap_client'
        session.ansibleroles.delete(delete_role)
        assert not session.ansibleroles.search(delete_role)


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
    with target_sat.ui_session as session:
        preimport_check = session.ansibleroles.preimport_check()
        if preimport_check is False:
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
    with target_sat.ui_session as session:
        preimport_check = session.ansibleroles.preimport_check()
        if preimport_check is False:
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
