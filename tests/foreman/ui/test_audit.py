"""Test class for Audit UI

:Requirement: AuditLog

:CaseAutomation: Automated

:CaseComponent: AuditLog

:Team: Endeavour

"""

from fauxfactory import gen_string
import pytest

from robottelo.constants import ENVIRONMENT


@pytest.fixture(scope='module')
def module_org(module_target_sat):
    return module_target_sat.api.Organization().create()


pytestmark = [pytest.mark.run_in_one_thread]


@pytest.mark.upgrade
def test_positive_create_event(session, module_org, module_location, module_target_sat):
    """When new host is created, corresponding audit entry appear in the application

    :id: d0595705-f4b2-4f06-888b-ee93edd4acf8

    :expectedresults: Audit entry for created host contains valid data

    :CaseAutomation: Automated

    :CaseImportance: Medium

    :BZ: 1730360
    """
    host = module_target_sat.api.Host(organization=module_org, location=module_location).create()
    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        values = session.audit.search('type=host')
        assert values.get('action_type') == 'create'
        assert values.get('resource_type') == 'HOST'
        assert values.get('resource_name') == host.name
        assert values.get('created_at')
        assert values.get('affected_organization') == module_org.name
        assert values.get('affected_location') == module_location.name
        summary = {
            prop['column0']: prop['column1']
            for prop in values.get('action_summary')
            if prop.get('column1')
        }
        assert summary.get('Name') == host.name
        assert summary.get('Architecture') == host.architecture.read().name
        os = host.operatingsystem.read()
        assert summary.get('Operatingsystem') == f'{os.name} {os.major}'
        assert summary.get('Ptable') == host.ptable.read().name
        assert summary.get('Medium') == host.medium.read().name
        assert summary.get('Build') == 'false'
        assert summary.get('Owner type') == 'User'
        assert summary.get('Managed') == 'true'
        assert summary.get('Enabled') == 'true'
        assert summary.get('Organization') == module_org.name
        assert summary.get('Location') == module_location.name


def test_positive_audit_comment(session, module_org):
    """When new partition table with audit comment is created, that message can be seen in
    corresponding audit entry

    :id: 52249010-ab3f-4467-8a96-d125a69f4524

    :expectedresults: Audit entry for created partition table contains proper audit comment

    :CaseAutomation: Automated

    :CaseImportance: Low
    """
    name = gen_string('alpha')
    audit_comment = gen_string('alpha')
    with session:
        session.partitiontable.create(
            {
                'template.name': name,
                'template.template_editor.editor': gen_string('alpha'),
                'template.audit_comment': audit_comment,
            }
        )
        assert session.partitiontable.search(name)[0]['Name'] == name
        current_user = session.partitiontable.read(name, 'current_user')['current_user']
        values = session.audit.search(f'type=ptable and username={current_user}')
        assert values['user'] == current_user
        assert values['action_type'] == 'create'
        assert values['resource_type'] == 'PARTITION TABLE'
        assert values['resource_name'] == name
        assert values['comment'] == audit_comment


def test_positive_update_event(session, module_org, module_target_sat):
    """When existing content view is updated, corresponding audit entry appear
    in the application

    :id: 6b869f66-9430-4bbd-b8a0-9aebde45e45c

    :expectedresults: Audit entry for updated content view contains valid data

    :CaseAutomation: Automated

    :CaseImportance: Medium

    :bz: 2222890
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    cv = module_target_sat.api.ContentView(name=name, organization=module_org).create()
    cv.name = new_name
    cv.update(['name'])
    with session:
        values = session.audit.search('type=katello/content_view and action=update')
        assert values['action_type'] == 'update'
        assert values['resource_type'] == 'KATELLO/CONTENT VIEW'
        assert values['resource_name'] == name
        assert values['affected_organization'] == module_org.name
        assert len(values['action_summary']) == 1
        assert values['action_summary'][0]['column0'] == 'Name'
        assert values['action_summary'][0]['column1'] == name
        assert values['action_summary'][0]['column2'] == new_name


def test_positive_delete_event(session, module_org, module_target_sat):
    """When existing architecture is deleted, corresponding audit entry appear
    in the application

    :id: 30f2dc85-f6be-410a-9ed5-b2ea00278f49

    :expectedresults: Audit entry for deleted architecture contains valid data

    :CaseAutomation: Automated

    :CaseImportance: Medium
    """
    architecture = module_target_sat.api.Architecture().create()
    architecture.delete()
    with session:
        values = session.audit.search('type=architecture and action=destroy')
        assert values['action_type'] == 'destroy'
        assert values['resource_type'] == 'ARCHITECTURE'
        assert values['resource_name'] == architecture.name
        assert len(values['action_summary']) == 1
        assert values['action_summary'][0]['column0'] == 'Name'
        assert values['action_summary'][0]['column1'] == architecture.name


def test_positive_add_event(session, module_org, module_target_sat):
    """When content view is published and proper lifecycle environment added to it,
    corresponding audit entry appear in the application

    :id: 8e24b1e1-fde0-4715-ad1d-053db58fee66

    :expectedresults: Audit entry for added environment contains valid data

    :CaseAutomation: Automated

    :CaseImportance: Medium
    """
    cv = module_target_sat.api.ContentView(organization=module_org).create()
    cv.publish()
    with session:
        values = session.audit.search(
            f'type=katello/content_view_environment and organization={module_org.name}'
        )
        assert values['action_type'] == 'add'
        assert values['resource_type'] == 'KATELLO/CONTENT VIEW ENVIRONMENT'
        assert values['resource_name'] == f'{ENVIRONMENT}/{cv.name} / {cv.name}'
        assert len(values['action_summary']) == 1
        assert (
            values['action_summary'][0]['column0'] == f'Added {ENVIRONMENT}/{cv.name} to {cv.name}'
        )


@pytest.mark.usefixtures('import_ansible_roles')
def test_positive_add_remove_ansible_host_role_event(request, module_org, module_target_sat):
    """When an Ansible role is assigned/unassigned to/from a host, each event is logged in Audit.

    :id: a316038a-ea50-11ef-97f3-000c29a0e355

    :Verifies: SAT-29715

    :setup:
        1. Import Ansible roles to Satellite.

    :steps:
        1. Create a host.
        2. Assign a role to the host.
        3. Unassign the role from the host.

    :expectedresults:
        2. & 3. Audit entry for added/removed host role is generated and contains information
            like the action, host name and Ansible role name.

    :CaseImportance: Medium
    """
    host = module_target_sat.api.Host(organization=module_org).create()
    request.addfinalizer(module_target_sat.api.Host(id=host.id).delete)
    role_name = 'theforeman.foreman_scap_client'
    role_id = (
        module_target_sat.api.AnsibleRoles().search(query={'search': f'name={role_name}'})[0].id
    )
    module_target_sat.api.Host(id=host.id).assign_ansible_roles(
        data={'ansible_role_ids': [role_id]}
    )
    module_target_sat.api.Host(id=host.id).remove_ansible_role(data={'ansible_role_id': role_id})

    with module_target_sat.ui_session() as session:
        values = session.audit.search(
            f'type=host_ansible_role and action=create and organization={module_org.name}'
        )
        assert values['action_type'] == 'add'
        assert values['resource_type'] == 'HOST ANSIBLE ROLE'
        assert values['resource_name'] == f'{role_name} / {host.name}'
        assert len(values['action_summary']) == 1
        assert values['action_summary'][0]['column0'] == f'Added {role_name} to {host.name}'

        values = session.audit.search(
            f'type=host_ansible_role and action=destroy and organization={module_org.name}'
        )
        assert values['action_type'] == 'remove'
        assert values['resource_type'] == 'HOST ANSIBLE ROLE'
        assert values['resource_name'] == f'{role_name} / {host.name}'
        assert len(values['action_summary']) == 1
        assert values['action_summary'][0]['column0'] == f'Removed {role_name} from {host.name}'
