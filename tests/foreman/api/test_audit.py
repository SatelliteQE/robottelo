"""Tests for audit functionality.

:Requirement: Audit

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: AuditLog

:Assignee: sbible

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.datafactory import gen_string


@pytest.mark.tier1
def test_positive_create_by_type():
    """Create entities of different types and check audit logs for these
    events using entity type as search criteria

    :id: 6c7ea7fc-6728-447f-9655-26fe0a2881bc

    :customerscenario: true

    :expectedresults: Audit logs contain corresponding entries per each
        create event

    :BZ: 1426742, 1492668, 1492696

    :CaseImportance: Medium
    """
    for entity_item in [
        {'entity': entities.Architecture()},
        {
            'entity': entities.AuthSourceLDAP(),
            'entity_type': 'auth_source',
            'value_template': 'LDAP-{entity.name}',
        },
        {'entity': entities.ComputeProfile(), 'entity_type': 'compute_profile'},
        {
            'entity': entities.LibvirtComputeResource(),
            'entity_type': 'compute_resource',
            'value_template': '{entity.name} (Libvirt)',
        },
        {'entity': entities.Domain()},
        {'entity': entities.Host()},
        {'entity': entities.HostGroup()},
        {'entity': entities.Image(compute_resource=entities.LibvirtComputeResource().create())},
        {'entity': entities.Location()},
        {'entity': entities.Media(), 'entity_type': 'medium'},
        {
            'entity': entities.OperatingSystem(),
            'entity_type': 'os',
            'value_template': '{entity.name} {entity.major}',
        },
        {'entity': entities.PartitionTable(), 'entity_type': 'ptable'},
        {'entity': entities.Role()},
        {
            'entity': entities.Subnet(),
            'value_template': '{entity.name} ({entity.network}/{entity.cidr})',
        },
        {'entity': entities.ProvisioningTemplate(), 'entity_type': 'provisioning_template'},
        {'entity': entities.User(), 'value_template': '{entity.login}'},
        {'entity': entities.UserGroup()},
        {'entity': entities.ContentView(), 'entity_type': 'katello/content_view'},
        {'entity': entities.LifecycleEnvironment(), 'entity_type': 'katello/kt_environment'},
        {'entity': entities.ActivationKey(), 'entity_type': 'katello/activation_key'},
        {'entity': entities.HostCollection(), 'entity_type': 'katello/host_collection'},
        {'entity': entities.Product(), 'entity_type': 'katello/product'},
        {
            'entity': entities.SyncPlan(organization=entities.Organization(id=1)),
            'entity_type': 'katello/sync_plan',
        },
    ]:
        created_entity = entity_item['entity'].create()
        entity_type = entity_item.get('entity_type', created_entity.__class__.__name__.lower())
        value_template = entity_item.get('value_template', '{entity.name}')
        entity_value = value_template.format(entity=created_entity)
        audits = entities.Audit().search(query={'search': f'type={entity_type}'})
        entity_audits = [entry for entry in audits if entry.auditable_name == entity_value]
        assert entity_audits, (
            f'audit not found by name "{entity_value}" for entity: '
            f'{created_entity.__class__.__name__.lower()}'
        )
        audit = entity_audits[0]
        assert audit.auditable_id == created_entity.id
        assert audit.action == 'create'
        assert audit.version == 1


@pytest.mark.tier1
def test_positive_update_by_type():
    """Update some entities of different types and check audit logs for
    these events using entity type as search criteria

    :id: 43e73a11-b241-4b91-bdf6-e966366014e8

    :expectedresults: Audit logs contain corresponding entries per each
        update event

    :CaseImportance: Medium
    """
    for entity in [
        entities.Architecture(),
        entities.Domain(),
        entities.HostGroup(),
        entities.Location(),
        entities.Role(),
        entities.UserGroup(),
    ]:
        created_entity = entity.create()
        name = created_entity.name
        new_name = gen_string('alpha')
        created_entity.name = new_name
        created_entity = created_entity.update(['name'])
        audits = entities.Audit().search(
            query={'search': f'type={created_entity.__class__.__name__.lower()}'}
        )
        entity_audits = [entry for entry in audits if entry.auditable_name == name]
        assert entity_audits, f'audit not found by name "{name}"'
        audit = entity_audits[0]
        assert audit.auditable_id == created_entity.id
        assert audit.audited_changes['name'] == [name, new_name]
        assert audit.action == 'update'
        assert audit.version == 2


@pytest.mark.tier1
def test_positive_delete_by_type():
    """Delete some entities of different types and check audit logs for
    these events using entity type as search criteria

    :id: de9b056f-10da-485a-87ce-b02a9efff15c

    :expectedresults: Audit logs contain corresponding entries per each
        delete event

    :CaseImportance: Medium
    """
    for entity in [
        entities.Architecture(),
        entities.Domain(),
        entities.Host(),
        entities.HostGroup(),
        entities.Location(),
        entities.Role(),
        entities.UserGroup(),
    ]:
        created_entity = entity.create()
        created_entity.delete()
        audits = entities.Audit().search(
            query={'search': f'type={created_entity.__class__.__name__.lower()}'}
        )
        entity_audits = [entry for entry in audits if entry.auditable_name == created_entity.name]
        assert entity_audits, f'audit not found by name "{created_entity.name}"'
        audit = entity_audits[0]
        assert audit.auditable_id == created_entity.id
        assert audit.action == 'destroy'
        assert audit.version == 2
