# -*- encoding: utf-8 -*-
"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI.

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

from fauxfactory import gen_integer, gen_string
from robottelo.cleanup import capsule_cleanup
from robottelo.cli.base import CLIBaseError, CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.environment import Environment
from robottelo.cli.factory import (
    make_architecture,
    make_content_view,
    make_domain,
    make_environment,
    make_hostgroup,
    make_lifecycle_environment,
    make_location,
    make_medium,
    make_org,
    make_os,
    make_partition_table,
    make_product,
    make_proxy,
    make_repository,
    make_smart_variable,
    make_subnet,
    publish_puppet_module,
)
from robottelo.cli.architecture import Architecture
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.partitiontable import PartitionTable
from robottelo.cli.proxy import Proxy
from robottelo.cli.puppet import Puppet
from robottelo.cli.repository import Repository
from robottelo.cli.scparams import SmartClassParameter
from robottelo.config import settings
from robottelo.constants import (
    CUSTOM_PUPPET_REPO,
    DEFAULT_ARCHITECTURE,
    DEFAULT_PTABLE,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
)
from robottelo.datafactory import (
    invalid_id_list,
    invalid_values_list,
    valid_hostgroups_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    tier1,
    tier2,
    upgrade,
)
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
            Puppet.info({'name': mod['name'], 'environment': cls.env['name']})
            for mod in puppet_modules
        ]

    @tier1
    def test_positive_create_with_name(self):
        """Successfully creates an HostGroup.

        :id: f5f2056f-d090-4e0d-8fb9-d29255a47908

        :expectedresults: HostGroup is created.

        :CaseImportance: Critical
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                self.assertEqual(hostgroup['name'], name)

    @tier1
    def test_negative_create_with_name(self):
        """Don't create an HostGroup with invalid data.

        :id: 853a6d43-129a-497b-94f0-08dc622862f8

        :expectedresults: HostGroup is not created.

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.create({'name': name})

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_env(self):
        """Check if hostgroup with environment can be created

        :id: f1bfb333-90cf-4a9f-b183-cf77c1773247

        :expectedresults: Hostgroup is created and has new environment assigned


        :CaseImportance: Critical
        """
        environment = make_environment()
        hostgroup = make_hostgroup({'environment-id': environment['id']})
        self.assertEqual(environment['name'], hostgroup['puppet-environment'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_loc(self):
        """Check if hostgroup with location can be created

        :id: 84ae02a4-ea7e-43ce-87bd-7bbde3766b14

        :expectedresults: Hostgroup is created and has new location assigned


        :CaseImportance: Critical
        """
        location = make_location()
        hostgroup = make_hostgroup({'location-ids': location['id']})
        self.assertIn(location['name'], hostgroup['locations'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_os(self):
        """Check if hostgroup with operating system can be created

        :id: d12c5939-1aac-44f5-8aa3-a04a824f4e83

        :expectedresults: Hostgroup is created and has operating system
            assigned


        :CaseImportance: Critical
        """
        os = make_os()
        hostgroup = make_hostgroup({'operatingsystem-id': os['id']})
        self.assertEqual(hostgroup['operating-system']['operating-system'],
            os['title'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_org(self):
        """Check if hostgroup with organization can be created

        :id: 780d4b93-f35a-4c5b-a645-4053aed4c37b

        :expectedresults: Hostgroup is created and has new organization
            assigned


        :CaseImportance: Critical
        """
        org = make_org()
        hostgroup = make_hostgroup({'organization-ids': org['id']})
        self.assertIn(org['name'], hostgroup['organizations'])

    @tier1
    def test_positive_create_with_orgs(self):
        """Check if hostgroup with multiple organizations can be created

        :id: 32be4630-0032-4f5f-89d4-44f8d05fe585

        :expectedresults: Hostgroup is created and has both new organizations
            assigned

        :CaseImportance: Critical
        """
        orgs = [make_org() for _ in range(2)]
        hostgroup = make_hostgroup({
            'organization-ids': [org['id'] for org in orgs],
        })
        self.assertEqual(
            set(org['name'] for org in orgs),
            set(hostgroup['organizations'])
        )

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_puppet_ca_proxy(self):
        """Check if hostgroup with puppet CA proxy server can be created

        :id: f7ea1c94-8a0e-4500-98b3-0ecd63b3ce3c

        :expectedresults: Hostgroup is created and has puppet CA proxy server
            assigned


        :CaseImportance: Critical
        """
        puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = make_hostgroup({'puppet-ca-proxy': puppet_proxy['name']})
        self.assertEqual(puppet_proxy['id'], hostgroup['puppet-ca-proxy-id'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_puppet_proxy(self):
        """Check if hostgroup with puppet proxy server can be created

        :id: 3a922d9f-7466-4565-b279-c1481f63a4ce

        :expectedresults: Hostgroup is created and has puppet proxy server
            assigned

        :CaseImportance: Critical
        """
        puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = make_hostgroup({'puppet-proxy': puppet_proxy['name']})
        self.assertEqual(
            puppet_proxy['name'],
            hostgroup['puppet-master-proxy'],
        )

    @tier1
    def test_positive_create_with_puppet_class_id(self):
        """Check if hostgroup with puppet class id can be created

        :id: 0a07856d-4432-4b72-a636-460ec12f1b65

        :expectedresults: Hostgroup is created and has puppet class assigned

        :CaseImportance: Critical
        """
        hostgroup = make_hostgroup({
            'puppet-class-ids': self.puppet_classes[0]['id'],
            'environment-id': self.env['id'],
            'content-view-id': self.cv['id'],
            'query-organization-id': self.org['id'],
        })
        self.assertIn(
            self.puppet_classes[0]['name'], hostgroup['puppetclasses'])

    @tier1
    def test_positive_create_with_puppet_class_name(self):
        """Check if hostgroup with puppet class name can be created

        :id: 78545a14-742f-4db6-abce-49fbeccd836e

        :expectedresults: Hostgroup is created and has puppet class assigned

        :CaseImportance: Critical
        """
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_classes[0]['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        self.assertIn(
            self.puppet_classes[0]['name'], hostgroup['puppetclasses'])

    @skip_if_bug_open('bugzilla', 1354544)
    @run_only_on('sat')
    @tier1
    def test_positive_create_with_architecture(self):
        """Check if hostgroup with architecture can be created

        :id: 21c619f4-7339-4fb0-9e29-e12dae65f943

        :expectedresults: Hostgroup should be created and has architecture
            assigned

        :BZ: 1354544

        :CaseImportance: Critical
        """
        arch = 'x86_64'
        hostgroup = make_hostgroup({'architecture': arch})
        self.assertEqual(arch, hostgroup['architecture'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_domain(self):
        """Check if hostgroup with domain can be created

        :id: c468fcac-9e42-4ee6-a431-abe29b6848ce

        :expectedresults: Hostgroup should be created and has domain assigned

        :CaseImportance: Critical
        """
        domain = make_domain()
        hostgroup = make_hostgroup({'domain-id': domain['id']})
        self.assertEqual(domain['name'], hostgroup['network']['domain'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_lifecycle_environment(self):
        """Check if hostgroup with lifecyle environment can be created

        :id: 24bc3010-4e61-47d8-b8ae-0d66e1055aea

        :expectedresults: Hostgroup should be created and has lifecycle env
            assigned

        :BZ: 1359694, 1313056

        :CaseImportance: Critical
        """
        org = make_org()
        lc_env = make_lifecycle_environment({'organization-id': org['id']})
        hostgroup = make_hostgroup({
            'lifecycle-environment': lc_env['name'],
            'organization-ids': org['id'],
            'query-organization-id': org['id'],
        })
        self.assertEqual(
            lc_env['name'],
            hostgroup['lifecycle-environment']['name'],
        )

    @tier1
    def test_positive_create_with_orgs_and_lce(self):
        """Check if hostgroup with multiple organizations can be created
        if one of them is associated with lifecycle environment

        :id: ca110a74-401d-48f9-9700-6c57f1c10f11

        :expectedresults: Hostgroup is created, has both new organizations
            assigned and has lifecycle env assigned

        :CaseImportance: Critical
        """
        orgs = [make_org() for _ in range(2)]
        lce = make_lifecycle_environment({'organization-id': orgs[0]['id']})
        hostgroup = make_hostgroup({
            'organization-ids': [org['id'] for org in orgs],
            'lifecycle-environment-id': lce['id'],
        })
        self.assertEqual(
            set(org['name'] for org in orgs),
            set(hostgroup['organizations'])
        )

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_multiple_entities_name(self):
        """Check if hostgroup with multiple options name can be created

        :id: a3ef4f0e-971d-4307-8d0a-35103dff6586

        :expectedresults: Hostgroup should be created and has all defined
            entities assigned

        :BZ: 1395254, 1313056

        :CaseLevel: Integration
        """
        # Common entities
        loc = make_location()
        org = make_org()
        env = make_environment({
            'location-ids': loc['id'],
            'organization-ids': org['id'],
        })
        lce = make_lifecycle_environment({'organization-id': org['id']})
        proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
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
            'organizations': org['name'],
            'locations': loc['name'],
            'environment': env['name'],
            'lifecycle-environment': lce['name'],
            'puppet-proxy': proxy['name'],
            'puppet-ca-proxy': proxy['name'],
            'content-source-id': proxy['id'],
            'content-view': cv['name'],
            'domain': domain['name'],
            'subnet': subnet['name'],
            'architecture': arch['name'],
            'partition-table': ptable['name'],
            'medium': media['name'],
            'operatingsystem':  os_full_name,
            'query-organization': org['name']
        }
        hostgroup = make_hostgroup(make_hostgroup_params)
        self.assertIn(org['name'], hostgroup['organizations'])
        self.assertIn(loc['name'], hostgroup['locations'])
        self.assertEqual(env['name'], hostgroup['puppet-environment'])
        self.assertEqual(proxy['name'], hostgroup['puppet-master-proxy'])
        self.assertEqual(proxy['name'], hostgroup['puppet-ca-proxy'])
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
        self.assertEqual(proxy['name'], hostgroup['content-source']['name'])

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_create_with_multiple_entities_ids(self):
        """Check if hostgroup with multiple options ids can be created

        :id: 6277613b-0ece-4dee-b9d8-504f8299ac38

        :expectedresults: Hostgroup should be created and has all defined
            entities assigned

        :BZ: 1395254, 1313056

        :CaseLevel: Integration
        """
        # Common entities
        loc = make_location()
        org = make_org()
        env = make_environment({
            'location-ids': loc['id'],
            'organization-ids': org['id'],
        })
        lce = make_lifecycle_environment({'organization-id': org['id']})
        proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
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
        media = make_medium({
            'operatingsystem-ids': os['id'],
            'location-ids': loc['id'],
            'organization-ids': org['id'],
        })
        make_hostgroup_params = {
            'location-ids': loc['id'],
            'environment-id': env['id'],
            'lifecycle-environment-id': lce['id'],
            'puppet-proxy-id': proxy['id'],
            'puppet-ca-proxy-id': proxy['id'],
            'content-source-id': proxy['id'],
            'content-view-id': cv['id'],
            'domain-id': domain['id'],
            'subnet-id': subnet['id'],
            'organization-ids': org['id'],
            'architecture-id': arch['id'],
            'partition-table-id': ptable['id'],
            'medium-id': media['id'],
            'operatingsystem-id': os['id'],
        }
        hostgroup = make_hostgroup(make_hostgroup_params)
        self.assertEqual(cv['id'], hostgroup['content-view']['id'])
        self.assertEqual(lce['id'], hostgroup['lifecycle-environment']['id'])
        self.assertEqual(proxy['id'], hostgroup['content-source']['id'])
        # get the json output format
        hostgroup = HostGroup.info(
            {'id': hostgroup['id']}, output_format='json')
        self.assertIn(org['id'], hostgroup['organizations'][0]['id'])
        self.assertIn(loc['id'], hostgroup['locations'][0]['id'])
        self.assertEqual(
            env['id'], hostgroup['puppet-environment']['environment_id'])
        self.assertEqual(
            proxy['id'],
            hostgroup['puppet-master-proxy']['puppet_proxy_id']
        )
        self.assertEqual(
            proxy['id'],
            hostgroup['puppet-master-proxy']['puppet_ca_proxy_id']
        )
        self.assertEqual(
            domain['id'],
            hostgroup['network']['domain']['domain_id']
        )
        self.assertEqual(
                subnet['id'],
                hostgroup['network']['domain']['subnet_id'])
        self.assertEqual(
            arch['id'], hostgroup['network']['domain']['architecture_id'])
        self.assertEqual(
            ptable['id'], hostgroup['network']['domain']['ptable_id'])
        self.assertEqual(
            media['id'],
            hostgroup['network']['domain']['medium_id']
        )
        self.assertEqual(
            os['id'], hostgroup['network']['domain']['operatingsystem_id'])

    @skip_if_bug_open('bugzilla', 1354568)
    @run_only_on('sat')
    @tier1
    def test_negative_create_with_subnet_id(self):
        """Check if hostgroup with invalid subnet id raises proper error

        :id: c352d7ea-4fc6-4b78-863d-d3ee4c0ad439

        :expectedresults: Proper error should be raised

        :BZ: 1354568

        :CaseImportance: Critical
        """
        subnet_id = gen_string('numeric', 4)
        with self.assertRaises(CLIReturnCodeError) as exception:
            HostGroup.create({
                'name': gen_string('alpha'),
                'subnet-id': subnet_id
            })
        self.assertIs(
            exception.exception.stderr,
            'Could not find subnet {0}'.format(subnet_id)
        )

    @skip_if_bug_open('bugzilla', 1354568)
    @run_only_on('sat')
    @tier1
    def test_negative_create_with_domain_id(self):
        """Check if hostgroup with invalid domain id raises proper error

        :id: b36c83d6-b27c-4f1a-ac45-6c4999005bf7

        :expectedresults: Proper error should be raised

        :BZ: 1354568

        :CaseImportance: Critical
        """
        domain_id = gen_string('numeric', 4)
        with self.assertRaises(CLIReturnCodeError) as exception:
            HostGroup.create({
                'name': gen_string('alpha'),
                'domain-id': domain_id
            })
        self.assertIs(
            exception.exception.stderr,
            'Could not find domain {0}'.format(domain_id)
        )

    @skip_if_bug_open('bugzilla', 1354568)
    @run_only_on('sat')
    @tier1
    def test_negative_create_with_architecture_id(self):
        """Check if hostgroup with invalid architecture id raises proper error

        :id: 7b7de0fa-aee9-4163-adc2-354c1e720d90

        :expectedresults: Proper error should be raised

        :BZ: 1354568

        :CaseImportance: Critical
        """
        arch_id = gen_string('numeric', 4)
        with self.assertRaises(CLIReturnCodeError) as exception:
            HostGroup.create({
                'name': gen_string('alpha'),
                'architecture-id': arch_id
            })
        self.assertIs(
            exception.exception.stderr,
            'Could not find architecture {0}'.format(arch_id)
        )

    @tier1
    def test_positive_create_with_content_source(self):
        """Create a hostgroup with content source specified

        :id: 49ba2e4e-7772-4e5f-ac49-33f3a4966110

        :customerscenario: true

        :BZ: 1260697, 1313056

        :expectedresults: A hostgroup is created with expected content source
            assigned

        :CaseImportance: High
        """
        content_source = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = make_hostgroup({
            'content-source-id': content_source['id'],
            'organization-ids': self.org['id'],
        })
        self.assertEqual(
            hostgroup['content-source']['name'], content_source['name'])

    @tier1
    def test_negative_create_with_content_source(self):
        """Attempt to create a hostgroup with invalid content source specified

        :id: 9fc1b777-36a3-4940-a9c8-aed7ff725371

        :BZ: 1260697

        :expectedresults: Hostgroup was not created

        :CaseImportance: Medium
        """
        with self.assertRaises(CLIBaseError):
            make_hostgroup({
                'content-source-id': gen_integer(10000, 99999),
                'organization-ids': self.org['id'],
            })

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_create_with_synced_content(self):
        """Check if hostgroup with synced kickstart repository can be created

        :id: 7c51ac72-359c-488a-8658-88b5a94d7e7a

        :customerscenario: true

        :expectedresults: Hostgroup should be created and has proper
            installation content id present

        :BZ: 1415707

        :CaseLevel: Integration
        """
        # Check whether path to kickstart media is set
        if settings.rhel6_os is None:
            raise ValueError(
                'Installation media path is not set in properties file')
        # Common entities
        org = make_org()
        lce = make_lifecycle_environment({'organization-id': org['id']})
        product = make_product({'organization-id': org['id']})
        repo = make_repository({
            u'url': settings.rhel6_os,
            u'product-id': product['id'],
            u'content-type': u'yum',
        })
        Repository.synchronize({'id': repo['id']})

        cv = make_content_view({
            'organization-id': org['id'],
            'repository-ids': [repo['id']],
        })
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        cvv = cv['versions'][0]
        ContentView.version_promote({
            'id': cvv['id'],
            'to-lifecycle-environment-id': lce['id'],
        })

        # Get the Partition table ID
        ptable = PartitionTable.info({'name': DEFAULT_PTABLE})

        # Get the arch ID
        arch = Architecture.list({
            'search': 'name={0}'.format(DEFAULT_ARCHITECTURE)})[0]

        # Get the OS ID
        os = OperatingSys.list({
            'search': 'name="RedHat" AND major="{0}" OR major="{1}"'.format(
                RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
        })[0]

        # Update the OS with found arch and ptable
        OperatingSys.update({
            'id': os['id'],
            'architectures': arch['name'],
            'partition-tables': ptable['name'],
        })
        proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]

        # Search for proper installation repository id
        synced_repo = Repository.list({
            'content-view-version-id': cvv['id'],
            'organization-id': org['id'],
            'environment-id': lce['id'],
        })[0]
        hostgroup = make_hostgroup({
            'lifecycle-environment-id': lce['id'],
            'puppet-proxy-id': proxy['id'],
            'puppet-ca-proxy-id': proxy['id'],
            'content-source-id': proxy['id'],
            'content-view-id': cv['id'],
            'organization-ids': org['id'],
            'architecture-id': arch['id'],
            'partition-table-id': ptable['id'],
            'operatingsystem-id': os['id'],
            'kickstart-repository-id': synced_repo['id'],
        })
        hg = HostGroup.info({'id': hostgroup['id']}, output_format='json')
        self.assertEqual(
            hg['kickstart-repository']['id'],
            synced_repo['id']
        )

    @run_in_one_thread
    @tier1
    def test_positive_update_content_source(self):
        """Update hostgroup's content source

        :id: c22218a1-4d86-4ac1-ad4b-79b10c9adcde

        :customerscenario: true

        :BZ: 1260697, 1313056

        :expectedresults: Hostgroup was successfully updated with new content
            source

        :CaseImportance: High
        """
        content_source = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = make_hostgroup({
            'content-source-id': content_source['id'],
            'organization-ids': self.org['id'],
        })
        new_content_source = make_proxy()
        self.addCleanup(capsule_cleanup, new_content_source['id'])
        self.addCleanup(HostGroup.delete, {'id': hostgroup['id']})
        HostGroup.update({
            'id': hostgroup['id'],
            'content-source-id': new_content_source['id'],
        })
        hostgroup = HostGroup.info({'id': hostgroup['id']})
        self.assertEqual(
            hostgroup['content-source']['name'], new_content_source['name'])

    @tier1
    def test_negative_update_content_source(self):
        """Attempt to update hostgroup's content source with invalid value

        :id: 4ffe6d18-3899-4bf1-acb2-d55ea09b7a26

        :BZ: 1260697, 1313056

        :expectedresults: Host group was not updated. Content source remains
            the same as it was before update

        :CaseImportance: Medium
        """
        content_source = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = make_hostgroup({
            'content-source-id': content_source['id'],
            'organization-ids': self.org['id'],
        })
        with self.assertRaises(CLIBaseError):
            HostGroup.update({
                'id': hostgroup['id'],
                'content-source-id': gen_integer(10000, 99999),
            })
        hostgroup = HostGroup.info({'id': hostgroup['id']})
        self.assertEqual(
            hostgroup['content-source']['name'], content_source['name'])

    @tier1
    def test_positive_update_name(self):
        """Successfully update an HostGroup.

        :id: a36e3cbe-83d9-44ce-b8f7-5fab2a2cadf9

        :expectedresults: HostGroup is updated.

        :CaseImportance: Critical
        """
        hostgroup = make_hostgroup()
        for new_name in valid_hostgroups_list():
            with self.subTest(new_name):
                HostGroup.update({
                    'id': hostgroup['id'],
                    'new-name': new_name,
                })
                hostgroup = HostGroup.info({'id': hostgroup['id']})
                self.assertEqual(hostgroup['name'], new_name)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Create HostGroup then fail to update its name

        :id: 42d208a4-f518-4ff2-9b7a-311adb460abd

        :expectedresults: HostGroup name is not updated

        :CaseImportance: Critical
        """
        hostgroup = make_hostgroup()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.update({
                        'id': hostgroup['id'],
                        'new-name': new_name,
                    })
                result = HostGroup.info({'id': hostgroup['id']})
                self.assertEqual(hostgroup['name'], result['name'])

    @tier1
    def test_positive_update_puppet_class_by_id(self):
        """Update hostgroup with puppet class by name by id

        :id: 4b044719-431d-4d72-8974-330cc62fd020

        :expectedresults: Puppet class is associated with hostgroup

        :CaseImportance: Critical
        """
        hostgroup = make_hostgroup({
            'environment-id': self.env['id'],
            'content-view-id': self.cv['id'],
            'query-organization-id': self.org['id'],
        })
        self.assertEqual(len(hostgroup['puppetclasses']), 0)
        HostGroup.update({
            'id': hostgroup['id'],
            'puppet-class-ids': self.puppet_classes[0]['id'],
        })
        hostgroup = HostGroup.info({'id': hostgroup['id']})
        self.assertIn(
            self.puppet_classes[0]['name'], hostgroup['puppetclasses'])

    @tier1
    def test_positive_update_puppet_class_by_name(self):
        """Update hostgroup with puppet class by name

        :id: 4c37354f-ef2d-4d54-98ac-906bc611d292

        :expectedresults: Puppet class is associated with hostgroup

        :CaseImportance: Critical
        """
        hostgroup = make_hostgroup({
            'environment-id': self.env['id'],
            'content-view-id': self.cv['id'],
            'query-organization-id': self.org['id'],
        })
        self.assertEqual(len(hostgroup['puppetclasses']), 0)
        HostGroup.update({
            'id': hostgroup['id'],
            'puppet-classes': self.puppet_classes[0]['name'],
        })
        hostgroup = HostGroup.info({'id': hostgroup['id']})
        self.assertIn(
            self.puppet_classes[0]['name'], hostgroup['puppetclasses'])

    @tier1
    def test_positive_update_multiple_puppet_classes(self):
        """Update hostgroup with multiple puppet classes by name

        :id: 2e977aed-c0d4-478e-9c84-f07deac912cd

        :expectedresults: All puppet classes are associated with hostgroup

        :BZ: 1264163

        :CaseImportance: Critical
        """
        puppet_classes = [puppet['name'] for puppet in self.puppet_classes]
        hostgroup = make_hostgroup({
            'environment-id': self.env['id'],
            'content-view-id': self.cv['id'],
            'query-organization-id': self.org['id'],
        })
        self.assertEqual(len(hostgroup['puppetclasses']), 0)
        HostGroup.update({
            'id': hostgroup['id'], 'puppet-classes': puppet_classes})
        hostgroup = HostGroup.info({'id': hostgroup['id']})
        self.assertEqual(set(puppet_classes), set(hostgroup['puppetclasses']))

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Create HostGroup with valid values then delete it
        by ID

        :id: fe7dedd4-d7c3-4c70-b70d-c2deff357b76

        :expectedresults: HostGroup is deleted

        :CaseImportance: Critical
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                HostGroup.delete({'id': hostgroup['id']})
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.info({'id': hostgroup['id']})

    @run_only_on('sat')
    @tier1
    def test_negative_delete_by_id(self):
        """Create HostGroup then delete it by wrong ID

        :id: 047c9f1a-4dd6-4fdc-b7ed-37cc725c68d3

        :expectedresults: HostGroup is not deleted

        :CaseImportance: Critical
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.delete({'id': entity_id})

    @tier2
    def test_positive_list_scparams_by_id(self):
        """List all overridden smart class parameters using hostgroup id

        :id: 42a24060-2ed7-427e-8396-86d73bbe5f69

        :expectedresults: Overridden sc-param from puppet class is listed

        :Caselevel: Integration
        """
        # Create hostgroup with associated puppet class
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_classes[0]['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list({
            'environment': self.env['name'],
            'search': u'puppetclass="{0}"'.format(
                self.puppet_classes[0]['name'])
        })
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        hg_scparams = HostGroup.sc_params({'hostgroup-id': hostgroup['id']})
        self.assertIn(scp_id, [scp['id'] for scp in hg_scparams])

    @tier2
    def test_positive_list_scparams_by_name(self):
        """List all smart class parameters using hostgroup name

        :id: 8e4fc561-2446-4a89-989b-e6814973aa56

        :expectedresults: Overridden sc-param from puppet class is listed

        :Caselevel: Integration
        """
        # Create hostgroup with associated puppet class
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_classes[0]['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list({
            'environment': self.env['name'],
            'search': u'puppetclass="{0}"'.format(
                self.puppet_classes[0]['name'])
        })
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        hg_scparams = HostGroup.sc_params({'hostgroup': hostgroup['name']})
        self.assertIn(scp_id, [scp['id'] for scp in hg_scparams])

    @tier2
    def test_positive_list_smartvariables_by_id(self):
        """List all smart variables using hostgroup id

        :id: 1d614441-7ef9-4fdb-a8e7-2f1c1054bf2f

        :expectedresults: Smart variable from puppet class is listed

        :Caselevel: Integration
        """
        # Create hostgroup with associated puppet class
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_classes[0]['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        # Create smart variable
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_classes[0]['name']})
        # Verify that affected sc-param is listed
        hg_variables = HostGroup.smart_variables(
            {'hostgroup-id': hostgroup['id']})
        self.assertIn(smart_variable['id'], [sv['id'] for sv in hg_variables])

    @tier2
    def test_positive_list_smartvariables_by_name(self):
        """List all smart variables using hostgroup name

        :id: 2b0da695-57fa-4f91-b164-e1ff60076c26

        :expectedresults: Smart variable from puppet class is listed

        :Caselevel: Integration
        """
        # Create hostgroup with associated puppet class
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_classes[0]['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        # Create smart variable
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_classes[0]['name']})
        # Verify that affected sc-param is listed
        hg_variables = HostGroup.smart_variables(
            {'hostgroup': hostgroup['name']})
        self.assertIn(smart_variable['id'], [sv['id'] for sv in hg_variables])
