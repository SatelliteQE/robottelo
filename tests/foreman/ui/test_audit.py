"""Test class for Audit UI

:Requirement: Audit

:CaseAutomation: Automated

:CaseLevel: Medium

:CaseComponent: AuditLog

:Assignee: sbible

:TestType: Functional

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import create_role_permissions
from robottelo.constants import ANY_CONTEXT
from robottelo.constants import ENVIRONMENT


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


pytestmark = [pytest.mark.run_in_one_thread]


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_create_event(session, module_org, module_location):
    """When new host is created, corresponding audit entry appear in the application

    :id: d0595705-f4b2-4f06-888b-ee93edd4acf8

    :expectedresults: Audit entry for created host contains valid data

    :CaseAutomation: Automated

    :CaseLevel: Integration

    :CaseImportance: Medium

    :BZ: 1730360
    """
    host = entities.Host(organization=module_org, location=module_location).create()
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


@pytest.mark.tier2
def test_positive_audit_comment(session, module_org):
    """When new partition table with audit comment is created, that message can be seen in
    corresponding audit entry

    :id: 52249010-ab3f-4467-8a96-d125a69f4524

    :expectedresults: Audit entry for created partition table contains proper audit comment

    :CaseAutomation: Automated

    :CaseLevel: Component

    :CaseImportance: Low
    """
    name = gen_string('alpha')
    audit_comment = gen_string('alpha')
    with session:
        session.partitiontable.create(
            {
                'template.name': name,
                'template.template_editor': gen_string('alpha'),
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


@pytest.mark.tier2
def test_positive_update_event(session, module_org):
    """When existing content view is updated, corresponding audit entry appear
    in the application

    :id: 6b869f66-9430-4bbd-b8a0-9aebde45e45c

    :expectedresults: Audit entry for updated content view contains valid data

    :CaseAutomation: Automated

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    cv = entities.ContentView(name=name, organization=module_org).create()
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


@pytest.mark.tier2
def test_positive_delete_event(session, module_org):
    """When existing architecture is deleted, corresponding audit entry appear
    in the application

    :id: 30f2dc85-f6be-410a-9ed5-b2ea00278f49

    :expectedresults: Audit entry for deleted architecture contains valid data

    :CaseAutomation: Automated

    :CaseLevel: Component

    :CaseImportance: Medium
    """
    architecture = entities.Architecture().create()
    architecture.delete()
    with session:
        values = session.audit.search('type=architecture and action=destroy')
        assert values['action_type'] == 'destroy'
        assert values['resource_type'] == 'ARCHITECTURE'
        assert values['resource_name'] == architecture.name
        assert len(values['action_summary']) == 1
        assert values['action_summary'][0]['column0'] == 'Name'
        assert values['action_summary'][0]['column1'] == architecture.name


@pytest.mark.tier2
def test_positive_add_event(session, module_org):
    """When content view is published and proper lifecycle environment added to it,
    corresponding audit entry appear in the application

    :id: 8e24b1e1-fde0-4715-ad1d-053db58fee66

    :expectedresults: Audit entry for added environment contains valid data

    :CaseAutomation: Automated

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    cv = entities.ContentView(organization=module_org).create()
    cv.publish()
    with session:
        values = session.audit.search(
            f'type=katello/content_view_environment and organization={module_org.name}'
        )
        assert values['action_type'] == 'add'
        assert values['resource_type'] == 'KATELLO/CONTENT VIEW ENVIRONMENT'
        assert values['resource_name'] == f'{ENVIRONMENT}/{cv.name} / {cv.name}'
        assert len(values['action_summary']) == 1
        assert values['action_summary'][0]['column0'] == 'Added {}/{} to {}'.format(
            ENVIRONMENT, cv.name, cv.name
        )


@pytest.mark.skip_if_open("BZ:1701118")
@pytest.mark.skip_if_open("BZ:1701132")
@pytest.mark.tier2
def test_positive_create_role_filter(session, module_org):
    """Update a role with new filter and check that corresponding event
    appeared in the audit log

    :id: 74679c0d-7ef1-4ab1-8282-9377c6cabb9f

    :customerscenario: true

    :expectedresults: audit log has an entry for a new filter that was
        added to the role

    :BZ: 1425977, 1701118, 1701132

    :CaseAutomation: Automated

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    role = entities.Role(organization=[module_org]).create()
    with session:
        session.organization.select(org_name=ANY_CONTEXT['org'])
        values = session.audit.search(f'type=role and organization={module_org.name}')
        assert values['action_type'] == 'create'
        assert values['resource_type'] == 'ROLE'
        assert values['resource_name'] == role.name
        create_role_permissions(
            role, {'Architecture': ['view_architectures', 'edit_architectures']}
        )
        values = session.audit.search('type=filter')
        assert values['action_type'] == 'added'
        assert values['resource_type'] == 'Filter'
        assert values['resource_name'] == '{} and {} / {}'.format(
            'view_architectures', 'edit_architectures', role.name
        )
        assert len(values['action_summary']) == 1
        assert values['action_summary'][0]['column0'] == 'Added {} and {} to {}'.format(
            'view_architectures', 'edit_architectures', role.name
        )
