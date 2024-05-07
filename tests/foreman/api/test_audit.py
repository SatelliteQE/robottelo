"""Tests for audit functionality.

:Requirement: AuditLog

:CaseAutomation: Automated

:CaseComponent: AuditLog

:Team: Endeavour

:CaseImportance: High

"""

import pytest

from robottelo.utils.datafactory import gen_string


@pytest.mark.e2e
@pytest.mark.tier1
def test_positive_create_by_type(target_sat):
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
        {'entity': target_sat.api.Architecture(), 'entity_type': 'architecture'},
        {
            'entity': target_sat.api.AuthSourceLDAP(),
            'entity_type': 'auth_source',
            'value_template': 'LDAP-{entity.name}',
        },
        {'entity': target_sat.api.ComputeProfile(), 'entity_type': 'compute_profile'},
        {
            'entity': target_sat.api.LibvirtComputeResource(),
            'entity_type': 'compute_resource',
            'value_template': '{entity.name} (Libvirt)',
        },
        {'entity': target_sat.api.Domain(), 'entity_type': 'domain'},
        {'entity': target_sat.api.Host(), 'entity_type': 'host'},
        {'entity': target_sat.api.HostGroup(), 'entity_type': 'hostgroup'},
        {
            'entity': target_sat.api.Image(
                compute_resource=target_sat.api.LibvirtComputeResource().create()
            ),
            'entity_type': 'image',
        },
        {'entity': target_sat.api.Location(), 'entity_type': 'location'},
        {'entity': target_sat.api.Media(), 'entity_type': 'medium'},
        {
            'entity': target_sat.api.OperatingSystem(),
            'entity_type': 'os',
            'value_template': '{entity.name} {entity.major}',
        },
        {'entity': target_sat.api.PartitionTable(), 'entity_type': 'ptable'},
        {'entity': target_sat.api.Role(), 'entity_type': 'role'},
        {
            'entity': target_sat.api.Subnet(),
            'entity_type': 'subnet',
            'value_template': '{entity.name} ({entity.network}/{entity.cidr})',
        },
        {'entity': target_sat.api.ProvisioningTemplate(), 'entity_type': 'provisioning_template'},
        {
            'entity': target_sat.api.User(),
            'value_template': '{entity.login}',
            'entity_type': 'user',
        },
        {'entity': target_sat.api.UserGroup(), 'entity_type': 'usergroup'},
        {'entity': target_sat.api.ContentView(), 'entity_type': 'katello/content_view'},
        {'entity': target_sat.api.LifecycleEnvironment(), 'entity_type': 'katello/kt_environment'},
        {'entity': target_sat.api.ActivationKey(), 'entity_type': 'katello/activation_key'},
        {'entity': target_sat.api.HostCollection(), 'entity_type': 'katello/host_collection'},
        {'entity': target_sat.api.Product(), 'entity_type': 'katello/product'},
        {
            'entity': target_sat.api.SyncPlan(organization=target_sat.api.Organization(id=1)),
            'entity_type': 'katello/sync_plan',
        },
    ]:
        created_entity = entity_item['entity'].create()
        value_template = entity_item.get('value_template', '{entity.name}')
        entity_value = value_template.format(entity=created_entity)
        audits = target_sat.api.Audit().search(
            query={'search': f'type={entity_item["entity_type"]}'}
        )
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
def test_positive_update_by_type(target_sat):
    """Update some entities of different types and check audit logs for
    these events using entity type as search criteria

    :id: 43e73a11-b241-4b91-bdf6-e966366014e8

    :expectedresults: Audit logs contain corresponding entries per each
        update event

    :CaseImportance: Medium
    """
    for entity in [
        {'entity': target_sat.api.Architecture(), 'entity_type': 'architecture'},
        {'entity': target_sat.api.Domain(), 'entity_type': 'domain'},
        {'entity': target_sat.api.HostGroup(), 'entity_type': 'hostgroup'},
        {'entity': target_sat.api.Location(), 'entity_type': 'location'},
        {'entity': target_sat.api.Role(), 'entity_type': 'role'},
        {'entity': target_sat.api.UserGroup(), 'entity_type': 'usergroup'},
    ]:
        created_entity = entity['entity'].create()
        name = created_entity.name
        new_name = gen_string('alpha')
        created_entity.name = new_name
        created_entity = created_entity.update(['name'])
        audits = target_sat.api.Audit().search(query={'search': f'type={entity["entity_type"]}'})
        entity_audits = [entry for entry in audits if entry.auditable_name == name]
        assert entity_audits, f'audit not found by name "{name}"'
        audit = entity_audits[0]
        assert audit.auditable_id == created_entity.id
        assert audit.audited_changes['name'] == [name, new_name]
        assert audit.action == 'update'
        assert audit.version == 2


@pytest.mark.tier1
def test_positive_delete_by_type(target_sat):
    """Delete some entities of different types and check audit logs for
    these events using entity type as search criteria

    :id: de9b056f-10da-485a-87ce-b02a9efff15c

    :expectedresults: Audit logs contain corresponding entries per each
        delete event

    :CaseImportance: Medium
    """
    for entity in [
        {'entity': target_sat.api.Architecture(), 'entity_type': 'architecture'},
        {'entity': target_sat.api.Domain(), 'entity_type': 'domain'},
        {'entity': target_sat.api.HostGroup(), 'entity_type': 'hostgroup'},
        {'entity': target_sat.api.Location(), 'entity_type': 'location'},
        {'entity': target_sat.api.Role(), 'entity_type': 'role'},
        {'entity': target_sat.api.UserGroup(), 'entity_type': 'usergroup'},
    ]:
        created_entity = entity['entity'].create()
        created_entity.delete()
        audits = target_sat.api.Audit().search(query={'search': f'type={entity["entity_type"]}'})
        entity_audits = [entry for entry in audits if entry.auditable_name == created_entity.name]
        assert entity_audits, f'audit not found by name "{created_entity.name}"'
        audit = entity_audits[0]
        assert audit.auditable_id == created_entity.id
        assert audit.action == 'destroy'
        assert audit.version == 2
