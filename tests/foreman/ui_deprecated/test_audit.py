# -*- encoding: utf-8 -*-
"""Test class for Audit UI

:Requirement: Audit

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import run_in_one_thread, run_only_on, tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.session import Session


@run_in_one_thread
class AuditTestCase(UITestCase):
    """Implements Audit tests from UI"""

    @run_only_on('sat')
    @tier1
    def test_positive_create_by_type(self):
        """Create entities of different types and check audit logs for these
        events using entity type and performed action as search criteria

        :id: 26197b39-4d56-4aab-8df8-f0fcedbffdb7

        :expectedresults: Audit logs contain corresponding entries per each
            create event

        :CaseImportance: Critical
        """
        with Session(self):
            for entity_item in [
                {
                    'entity': entities.Architecture(),
                    'entity_type': 'architecture'
                },
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
                {
                    'entity': entities.ConfigGroup(),
                    'entity_type': 'config_group'
                },
                {'entity': entities.Domain(), 'entity_type': 'domain'},
                {'entity': entities.Host(), 'entity_type': 'host'},
                {'entity': entities.HostGroup(), 'entity_type': 'hostgroup'},
                {'entity': entities.Image(
                    compute_resource=entities.LibvirtComputeResource().create()
                ), 'entity_type': 'image'},
                {'entity': entities.Location(), 'entity_type': 'location'},
                {
                    'entity': entities.Media(),
                    'entity_type': 'medium',
                    'custom_operation': 'added',
                },
                {
                    'entity': entities.Organization(),
                    'entity_type': 'organization'
                },
                {
                    'entity': entities.OperatingSystem(),
                    'entity_type': 'os',
                    'value_template': '{entity.name} {entity.major}'
                },
                {
                    'entity': entities.PartitionTable(),
                    'entity_type': 'ptable',
                },
                {
                    'entity': entities.PuppetClass(),
                    'entity_type': 'puppetclass'
                },
                {'entity': entities.Role(), 'entity_type': 'role'},
                {
                    'entity': entities.Subnet(),
                    'entity_type': 'subnet',
                    'value_template': '{entity.name} '
                                      '({entity.network}/{entity.cidr})'
                },
                {
                    'entity': entities.ProvisioningTemplate(),
                    'entity_type': 'template',
                },
                {
                    'entity': entities.User(),
                    'value_template': '{entity.login}',
                    'entity_type': 'user',
                },
                {'entity': entities.UserGroup(), 'entity_type': 'usergroup'},
            ]:
                created_entity = entity_item['entity'].create()
                value_template = entity_item.get(
                    'value_template', '{entity.name}')
                operation_type = entity_item.get('custom_operation', 'created')
                entity_value = value_template.format(entity=created_entity)
                self.audit.filter(
                    'type={} and action=create'.format(
                        entity_item['entity_type']
                    )
                )
                result = self.audit.get_last_entry()
                self.assertIn(operation_type, result['full_statement'])
                self.assertEqual(entity_value, result['entity_name'])

    @run_only_on('sat')
    @tier1
    def test_positive_update_by_type(self):
        """Update entities of different types and check audit logs for these
        events using entity type and performed action as search criteria

        :id: fef54686-4c13-4f36-a616-51dc9b58be19

        :expectedresults: Audit logs contain corresponding entries per each
            update event
        """
        with Session(self):
            for entity_item in [
                {
                    'entity': entities.Architecture(),
                    'entity_type': 'architecture'
                },
                {
                    'entity': entities.ConfigGroup(),
                    'entity_type': 'config_group'
                },
                {'entity': entities.Domain(), 'entity_type': 'domain'},
                {'entity': entities.HostGroup(), 'entity_type': 'hostgroup'},
                {'entity': entities.Location(), 'entity_type': 'location'},
                {
                    'entity': entities.PartitionTable(),
                    'entity_type': 'ptable',
                },
                {'entity': entities.Role(), 'entity_type': 'role'},
                {
                    'entity': entities.ProvisioningTemplate(),
                    'entity_type': 'template',
                },
                {'entity': entities.UserGroup(), 'entity_type': 'usergroup'},
            ]:
                entity = entity_item['entity'].create()
                name = entity.name
                new_name = gen_string('alpha')
                entity.name = new_name
                entity.update(['name'])
                self.audit.filter(
                    'type={} and action=update'.format(
                        entity_item['entity_type']
                    )
                )
                result = self.audit.get_last_entry()
                self.assertIn('updated', result['full_statement'])
                self.assertEqual(result['entity_name'], name)
                self.assertEqual(
                    result['update_list'][0],
                    'Name changed from {} to {}'.format(name, new_name),
                )

    @tier1
    @upgrade
    def test_positive_delete_by_type(self):
        """Delete some entities of different types and check audit logs for
        these events using entity type and performed action as search criteria

        :id: 69dcd846-5cef-457f-ae75-c1cf76071d00

        :expectedresults: Audit logs contain corresponding entries per each
            delete event
        """
        with Session(self):
            for entity_item in [
                {
                    'entity': entities.Architecture(),
                    'entity_type': 'architecture'
                },
                {'entity': entities.Domain(), 'entity_type': 'domain'},
                {'entity': entities.HostGroup(), 'entity_type': 'hostgroup'},
                {'entity': entities.Location(), 'entity_type': 'location'},
                {
                    'entity': entities.PartitionTable(),
                    'entity_type': 'ptable',
                },
                {'entity': entities.Role(), 'entity_type': 'role'},
                {
                    'entity': entities.ProvisioningTemplate(),
                    'entity_type': 'template',
                },
                {'entity': entities.UserGroup(), 'entity_type': 'usergroup'},
            ]:
                entity = entity_item['entity'].create()
                entity.delete()
                self.audit.filter(
                    'type={} and action=delete'.format(
                        entity_item['entity_type']
                    )
                )
                result = self.audit.get_last_entry()
                self.assertIn('destroyed', result['full_statement'])
                self.assertEqual(result['entity_name'], entity.name)
