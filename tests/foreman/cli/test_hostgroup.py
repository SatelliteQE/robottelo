# -*- encoding: utf-8 -*-
"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI.

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: HostGroup

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_integer

from robottelo.cleanup import capsule_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.environment import Environment
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_architecture
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_domain
from robottelo.cli.factory import make_environment
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_os
from robottelo.cli.factory import make_partition_table
from robottelo.cli.factory import make_proxy
from robottelo.cli.factory import make_subnet
from robottelo.cli.factory import publish_puppet_module
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.proxy import Proxy
from robottelo.cli.puppet import Puppet
from robottelo.config import settings
from robottelo.constants import (
    CUSTOM_PUPPET_REPO,
)
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_hostgroups_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class HostGroupTestCase(CLITestCase):
    """Test class for Host Group CLI"""

    @classmethod
    def setUpClass(cls):
        super(HostGroupTestCase, cls).setUpClass()
        cls.org = make_org()
        # Setup for puppet class related tests
        puppet_modules = [
            {'author': 'robottelo', 'name': 'generic_1'},
            {'author': 'robottelo', 'name': 'generic_2'},
        ]
        cls.cv = publish_puppet_module(
            puppet_modules, CUSTOM_PUPPET_REPO, cls.org['id'])
        cls.env = Environment.list({
            'search': u'content_view="{0}"'.format(cls.cv['name'])})[0]
        cls.puppet_classes = [
            Puppet.info({'name': mod['name'], 'puppet-environment': cls.env['name']})
            for mod in puppet_modules
        ]
        cls.content_source = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        cls.hostgroup = make_hostgroup({
            'content-source-id': cls.content_source['id'],
            'organization-ids': cls.org['id'],
        })

    @tier2
    def test_negative_create_with_name(self):
        """Don't create an HostGroup with invalid data.

        :id: 853a6d43-129a-497b-94f0-08dc622862f8

        :expectedresults: HostGroup is not created.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.create({'name': name})

    @tier1
    @upgrade
    def test_positive_create_with_multiple_entities_and_delete(self):
        """Check if hostgroup with multiple options can be created and deleted

        :id: a3ef4f0e-971d-4307-8d0a-35103dff6586

        :expectedresults: Hostgroup should be created, has all defined
            entities assigned and deleted

        :BZ: 1395254, 1313056

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # Common entities
        name = valid_hostgroups_list()[0]
        loc = make_location()
        org = make_org()
        orgs = [org, self.org]
        env = make_environment({
            'location-ids': loc['id'],
            'organization-ids': org['id'],
        })
        lce = make_lifecycle_environment({'organization-id': org['id']})
        # Content View should be promoted to be used with LC Env
        cv = make_content_view({'organization-id': org['id']})
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        ContentView.version_promote({
            'id': cv['versions'][0]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        # Network
        domain = make_domain({
            'location-ids': loc['id'],
            'organization-ids': org['id'],
        })
        subnet = make_subnet({
            'domain-ids': domain['id'],
            'organization-ids': org['id'],
        })
        # Operating System
        arch = make_architecture()
        ptable = make_partition_table({
            'location-ids': loc['id'],
            'organization-ids': org['id'],
        })
        os = make_os({
            'architecture-ids': arch['id'],
            'partition-table-ids': ptable['id'],
        })
        os_full_name = "{0} {1}.{2}".format(
            os['name'],
            os['major-version'],
            os['minor-version']
        )
        media = make_medium({
            'operatingsystem-ids': os['id'],
            'location-ids': loc['id'],
            'organization-ids': org['id'],
        })
        # Note: in the current hammer version there is no content source name
        # option
        make_hostgroup_params = {
            'name': name,
            'organization-ids': [org['id'] for org in orgs],
            'locations': loc['name'],
            'environment': env['name'],
            'lifecycle-environment': lce['name'],
            'puppet-proxy': self.content_source['name'],
            'puppet-ca-proxy': self.content_source['name'],
            'content-source-id': self.content_source['id'],
            'content-view': cv['name'],
            'domain': domain['name'],
            'subnet': subnet['name'],
            'architecture': arch['name'],
            'partition-table': ptable['name'],
            'medium': media['name'],
            'operatingsystem':  os_full_name,
            'puppet-classes': self.puppet_classes[0]['name'],
            'query-organization': org['name']
        }
        hostgroup = make_hostgroup(make_hostgroup_params)
        self.assertEqual(hostgroup['name'], name)
        self.assertEqual(
            set(org['name'] for org in orgs),
            set(hostgroup['organizations'])
        )
        self.assertIn(loc['name'], hostgroup['locations'])
        self.assertEqual(env['name'], hostgroup['puppet-environment'])
        self.assertEqual(self.content_source['name'], hostgroup['puppet-master-proxy'])
        self.assertEqual(self.content_source['name'], hostgroup['puppet-ca-proxy'])
        self.assertEqual(domain['name'], hostgroup['network']['domain'])
        self.assertEqual(subnet['name'], hostgroup['network']['subnet-ipv4'])
        self.assertEqual(
            arch['name'],
            hostgroup['operating-system']['architecture']
        )
        self.assertEqual(
            ptable['name'],
            hostgroup['operating-system']['partition-table']
        )
        self.assertEqual(
            media['name'],
            hostgroup['operating-system']['medium']
        )
        self.assertEqual(
            os_full_name,
            hostgroup['operating-system']['operating-system']
        )
        self.assertEqual(
            cv['name'],
            hostgroup['content-view']['name'])
        self.assertEqual(
            lce['name'], hostgroup['lifecycle-environment']['name'])
        self.assertEqual(self.content_source['name'], hostgroup['content-source']['name'])
        self.assertIn(
            self.puppet_classes[0]['name'], hostgroup['puppetclasses'])
        # delete hostgroup
        HostGroup.delete({'id': hostgroup['id']})
        with self.assertRaises(CLIReturnCodeError):
            HostGroup.info({'id': hostgroup['id']})

    @tier2
    def test_negative_create_with_content_source(self):
        """Attempt to create a hostgroup with invalid content source specified

        :id: 9fc1b777-36a3-4940-a9c8-aed7ff725371

        :BZ: 1260697

        :expectedresults: Hostgroup was not created

        :CaseLevel: Integration
        """
        with self.assertRaises(CLIFactoryError):
            make_hostgroup({
                'content-source-id': gen_integer(10000, 99999),
                'organization-ids': self.org['id'],
            })

    @run_in_one_thread
    @tier2
    def test_positive_update_hostgroup(self):
        """Update hostgroup's content source, name and puppet classes

        :id: c22218a1-4d86-4ac1-ad4b-79b10c9adcde

        :customerscenario: true

        :BZ: 1260697, 1313056

        :expectedresults: Hostgroup was successfully updated with new content
            source, name and puppet classes

        :CaseLevel: Integration
        """
        hostgroup = make_hostgroup({
            'content-source-id': self.content_source['id'],
            'organization-ids': self.org['id'],
            'environment-id': self.env['id'],
            'content-view-id': self.cv['id'],
            'query-organization-id': self.org['id'],
        })
        new_content_source = make_proxy()
        self.addCleanup(capsule_cleanup, new_content_source['id'])
        self.addCleanup(HostGroup.delete, {'id': hostgroup['id']})
        self.assertEqual(len(hostgroup['puppetclasses']), 0)
        new_name = valid_hostgroups_list()[0]
        puppet_classes = [puppet['name'] for puppet in self.puppet_classes]
        HostGroup.update({
            'new-name': new_name,
            'id': hostgroup['id'],
            'content-source-id': new_content_source['id'],
            'puppet-classes': puppet_classes,
        })
        hostgroup = HostGroup.info({'id': hostgroup['id']})
        self.assertEqual(hostgroup['name'], new_name)
        self.assertEqual(
            hostgroup['content-source']['name'], new_content_source['name'])
        self.assertEqual(set(puppet_classes), set(hostgroup['puppetclasses']))

    @tier2
    def test_negative_update_content_source(self):
        """Attempt to update hostgroup's content source with invalid value

        :id: 4ffe6d18-3899-4bf1-acb2-d55ea09b7a26

        :BZ: 1260697, 1313056

        :expectedresults: Host group was not updated. Content source remains
            the same as it was before update

        :CaseLevel: Integration
        """
        with self.assertRaises(CLIReturnCodeError):
            HostGroup.update({
                'id': self.hostgroup['id'],
                'content-source-id': gen_integer(10000, 99999),
            })
        hostgroup = HostGroup.info({'id': self.hostgroup['id']})
        self.assertEqual(
            hostgroup['content-source']['name'], self.content_source['name'])

    @tier2
    def test_negative_update_name(self):
        """Create HostGroup then fail to update its name

        :id: 42d208a4-f518-4ff2-9b7a-311adb460abd

        :expectedresults: HostGroup name is not updated
        """
        new_name = invalid_values_list()[0]
        with self.assertRaises(CLIReturnCodeError):
            HostGroup.update({
                'id': self.hostgroup['id'],
                'new-name': new_name,
            })
        result = HostGroup.info({'id': self.hostgroup['id']})
        self.assertEqual(self.hostgroup['name'], result['name'])

    @tier2
    def test_negative_delete_by_id(self):
        """Create HostGroup then delete it by wrong ID

        :id: 047c9f1a-4dd6-4fdc-b7ed-37cc725c68d3

        :expectedresults: HostGroup is not deleted

        :CaseLevel: Integration
        """
        entity_id = invalid_id_list()[0]
        with self.assertRaises(CLIReturnCodeError):
            HostGroup.delete({'id': entity_id})
