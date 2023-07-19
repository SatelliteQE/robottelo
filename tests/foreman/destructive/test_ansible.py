"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Ansible

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

pytestmark = pytest.mark.destructive


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
