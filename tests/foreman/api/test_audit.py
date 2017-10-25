"""Unit tests for the ``audit`` paths.

:Requirement: Audit

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from robottelo.datafactory import gen_string
from robottelo.decorators import run_in_one_thread, tier1
from robottelo.test import APITestCase


@run_in_one_thread
class AuditTestCase(APITestCase):
    """Tests for audit functionality"""

    @tier1
    def test_positive_create_by_type(self):
        """Create entities of different types and check audit logs for these
        events using entity type as search criteria

        :id: 6c7ea7fc-6728-447f-9655-26fe0a2881bc

        :expectedresults: Audit logs contain corresponding entries per each
            create event

        :BZ: 1426742, 1492668, 1492696

        :CaseImportance: Critical
        """
        for entity_item in [
            {'entity': entities.Architecture()},
            {
                'entity': entities.AuthSourceLDAP(),
                'entity_type': 'auth_source',
                'value_template': 'LDAP-{entity.name}'
            },
            {
                'entity': entities.ComputeProfile(),
                'entity_type': 'compute_profile'
            },
            {
                'entity': entities.LibvirtComputeResource(),
                'entity_type': 'compute_resource',
                'value_template': '{entity.name} (Libvirt)'
            },
            {'entity': entities.ConfigGroup(), 'entity_type': 'config_group'},
            {'entity': entities.Domain()},
            {'entity': entities.Host()},
            {'entity': entities.HostGroup()},
            {'entity': entities.Image(
                compute_resource=entities.LibvirtComputeResource().create())},
            {'entity': entities.Location()},
            {'entity': entities.Media(), 'entity_type': 'medium'},
            {'entity': entities.Organization()},
            {
                'entity': entities.OperatingSystem(),
                'entity_type': 'os',
                'value_template': '{entity.name} {entity.major}'
            },
            {
                'entity': entities.PartitionTable(),
                'entity_type': 'ptable',
            },
            {'entity': entities.PuppetClass()},
            {'entity': entities.Role()},
            {
                'entity': entities.Subnet(),
                'value_template': '{entity.name} '
                                  '({entity.network}/{entity.cidr})'
            },
            {
                'entity': entities.ProvisioningTemplate(),
                'entity_type': 'template',
            },
            {'entity': entities.User(), 'value_template': '{entity.login}'},
            {'entity': entities.UserGroup()},
        ]:
            created_entity = entity_item['entity'].create()
            entity_type = entity_item.get(
                'entity_type', created_entity.__class__.__name__.lower())
            value_template = entity_item.get('value_template', '{entity.name}')
            entity_value = value_template.format(entity=created_entity)
            audit = entities.Audit().search(
                query={'search': 'type={0}'.format(entity_type)})[0]
            self.assertEqual(audit.auditable_name, entity_value)
            self.assertEqual(audit.auditable_id, created_entity.id)
            self.assertEqual(audit.action, 'create')
            self.assertEqual(audit.version, 1)

    @tier1
    def test_positive_update_by_type(self):
        """Update some entities of different types and check audit logs for
        these events using entity type as search criteria

        :id: 43e73a11-b241-4b91-bdf6-e966366014e8

        :expectedresults: Audit logs contain corresponding entries per each
            update event
        """
        for entity in [
            entities.Architecture(),
            entities.Domain(),
            entities.HostGroup(),
            entities.Location(),
            entities.Organization(),
            entities.Role(),
            entities.UserGroup(),
        ]:
            created_entity = entity.create()
            name = created_entity.name
            new_name = gen_string('alpha')
            created_entity.name = new_name
            created_entity = created_entity.update(['name'])
            audit = entities.Audit().search(
                query={'search': 'type={0}'.format(
                    created_entity.__class__.__name__.lower())
                }
            )[0]
            self.assertEqual(audit.auditable_name, name)
            self.assertEqual(audit.auditable_id, created_entity.id)
            self.assertEqual(
                audit.audited_changes['name'], [name, new_name])
            self.assertEqual(audit.action, 'update')
            self.assertEqual(audit.version, 2)

    @tier1
    def test_positive_delete_by_type(self):
        """Delete some entities of different types and check audit logs for
        these events using entity type as search criteria

        :id: de9b056f-10da-485a-87ce-b02a9efff15c

        :expectedresults: Audit logs contain corresponding entries per each
            delete event
        """
        for entity in [
            entities.Architecture(),
            entities.Domain(),
            entities.Host(),
            entities.HostGroup(),
            entities.Location(),
            entities.Organization(),
            entities.Role(),
            entities.UserGroup(),
        ]:
            created_entity = entity.create()
            created_entity.delete()
            audit = entities.Audit().search(
                query={'search': 'type={0}'.format(
                    created_entity.__class__.__name__.lower())
                }
            )[0]
            self.assertEqual(audit.auditable_name, created_entity.name)
            self.assertEqual(audit.auditable_id, created_entity.id)
            self.assertEqual(audit.action, 'destroy')
            self.assertEqual(audit.version, 2)
