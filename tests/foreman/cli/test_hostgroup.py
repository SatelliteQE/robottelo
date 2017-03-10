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

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
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
    make_smart_variable,
    make_subnet,
    publish_puppet_module,
)
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.proxy import Proxy
from robottelo.cli.puppet import Puppet
from robottelo.cli.scparams import SmartClassParameter
from robottelo.config import settings
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.datafactory import (
    invalid_id_list,
    invalid_values_list,
    valid_hostgroups_list,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_only_on,
    skip_if_bug_open,
    tier1,
    tier2,
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

        :Assert: HostGroup is created.
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                self.assertEqual(hostgroup['name'], name)

    @tier1
    def test_negative_create_with_name(self):
        """Don't create an HostGroup with invalid data.

        :id: 853a6d43-129a-497b-94f0-08dc622862f8

        :Assert: HostGroup is not created.
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

        :Assert: Hostgroup is created and has new environment assigned

        """
        environment = make_environment()
        hostgroup = make_hostgroup({'environment-id': environment['id']})
        self.assertEqual(environment['name'], hostgroup['environment'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_loc(self):
        """Check if hostgroup with location can be created

        :id: 84ae02a4-ea7e-43ce-87bd-7bbde3766b14

        :Assert: Hostgroup is created and has new location assigned

        """
        location = make_location()
        hostgroup = make_hostgroup({'location-ids': location['id']})
        self.assertIn(location['name'], hostgroup['locations'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_os(self):
        """Check if hostgroup with operating system can be created

        :id: d12c5939-1aac-44f5-8aa3-a04a824f4e83

        :Assert: Hostgroup is created and has operating system assigned

        """
        os = make_os()
        hostgroup = make_hostgroup({'operatingsystem-id': os['id']})
        self.assertEqual(hostgroup['operating-system'], os['title'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_org(self):
        """Check if hostgroup with organization can be created

        :id: 780d4b93-f35a-4c5b-a645-4053aed4c37b

        :Assert: Hostgroup is created and has new organization assigned

        """
        org = make_org()
        hostgroup = make_hostgroup({'organization-ids': org['id']})
        self.assertIn(org['name'], hostgroup['organizations'])

    @tier1
    def test_positive_create_with_orgs(self):
        """Check if hostgroup with multiple organizations can be created

        :id: 32be4630-0032-4f5f-89d4-44f8d05fe585

        :Assert: Hostgroup is created and has both new organizations assigned
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

        :Assert: Hostgroup is created and has puppet CA proxy server assigned

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

        :Assert: Hostgroup is created and has puppet proxy server assigned
        """
        puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = make_hostgroup({'puppet-proxy': puppet_proxy['name']})
        self.assertEqual(
            puppet_proxy['id'],
            hostgroup['puppet-master-proxy-id'],
        )

    @tier1
    def test_positive_create_with_puppet_class_id(self):
        """Check if hostgroup with puppet class id can be created

        :id: 0a07856d-4432-4b72-a636-460ec12f1b65

        :Assert: Hostgroup is created and has puppet class assigned
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

        :Assert: Hostgroup is created and has puppet class assigned
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

        :Assert: Hostgroup should be created and has architecture assigned

        :BZ: 1354544
        """
        arch = 'x86_64'
        hostgroup = make_hostgroup({'architecture': arch})
        self.assertEqual(arch, hostgroup['architecture'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_domain(self):
        """Check if hostgroup with domain can be created

        :id: c468fcac-9e42-4ee6-a431-abe29b6848ce

        :Assert: Hostgroup should be created and has domain assigned
        """
        domain = make_domain()
        hostgroup = make_hostgroup({'domain-id': domain['id']})
        self.assertEqual(domain['name'], hostgroup['domain'])

    @skip_if_bug_open('bugzilla', 1313056)
    @run_only_on('sat')
    @tier1
    def test_positive_create_with_lifecycle_environment(self):
        """Check if hostgroup with lifecyle environment can be created

        :id: 24bc3010-4e61-47d8-b8ae-0d66e1055aea

        :Assert: Hostgroup should be created and has lifecycle env assigned

        :BZ: 1359694
        """
        org = make_org()
        lc_env = make_lifecycle_environment({'organization-id': org['id']})
        hostgroup = make_hostgroup({
            'lifecycle-environment': lc_env['name'],
            'organization-id': org['id'],
        })
        self.assertEqual(
            lc_env['name'],
            hostgroup['lifecycle-environment'],
        )

    @tier1
    def test_positive_create_with_orgs_and_lce(self):
        """Check if hostgroup with multiple organizations can be created
        if one of them is associated with lifecycle environment

        :id: ca110a74-401d-48f9-9700-6c57f1c10f11

        :Assert: Hostgroup is created, has both new organizations assigned and
            has lifecycle env assigned
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
    def test_positive_create_with_multiple_entities(self):
        """Check if hostgroup with multiple options can be created

        :id: a3ef4f0e-971d-4307-8d0a-35103dff6586

        :Assert: Hostgroup should be created and has all defined entities
            assigned

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
        puppet_proxy = Proxy.list({
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
            'lifecycle-environment': lce['name'],
            'puppet-proxy-id': puppet_proxy['id'],
            'puppet-ca-proxy-id': puppet_proxy['id'],
            'content-view-id': cv['id'],
            'domain-id': domain['id'],
            'subnet-id': subnet['id'],
            'organization-ids': org['id'],
            'architecture-id': arch['id'],
            'partition-table-id': ptable['id'],
            'medium-id': media['id'],
            'operatingsystem-id': os['id'],
        }
        # If bug is open provide LCE id as parameter
        # because LCE name cause errors
        if bz_bug_is_open(1395254):
            make_hostgroup_params.pop('lifecycle-environment')
            make_hostgroup_params['lifecycle-environment-id'] = lce['id']

        hostgroup = make_hostgroup(make_hostgroup_params)
        self.assertIn(org['name'], hostgroup['organizations'])
        self.assertIn(loc['name'], hostgroup['locations'])
        self.assertEqual(env['name'], hostgroup['environment'])
        self.assertEqual(
            puppet_proxy['id'], hostgroup['puppet-master-proxy-id']
        )
        self.assertEqual(puppet_proxy['id'], hostgroup['puppet-ca-proxy-id'])
        self.assertEqual(domain['name'], hostgroup['domain'])
        self.assertEqual(subnet['name'], hostgroup['subnet'])
        self.assertEqual(arch['name'], hostgroup['architecture'])
        self.assertEqual(ptable['name'], hostgroup['partition-table'])
        self.assertEqual(media['name'], hostgroup['medium'])
        self.assertEqual(
            "{0} {1}.{2}".format(
                os['name'],
                os['major-version'],
                os['minor-version']
            ),
            hostgroup['operating-system']
        )
        if not bz_bug_is_open('1313056'):
            self.assertEqual(cv['name'], hostgroup['content-view'])
            self.assertEqual(
                lce['name'], hostgroup['lifecycle-environment']
            )

    @skip_if_bug_open('bugzilla', 1354568)
    @run_only_on('sat')
    @tier1
    def test_negative_create_with_subnet_id(self):
        """Check if hostgroup with invalid subnet id raises proper error

        :id: c352d7ea-4fc6-4b78-863d-d3ee4c0ad439

        :Assert: Proper error should be raised

        :BZ: 1354568
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

        :Assert: Proper error should be raised

        :BZ: 1354568
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

        :Assert: Proper error should be raised

        :BZ: 1354568
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
    def test_positive_update_name(self):
        """Successfully update an HostGroup.

        :id: a36e3cbe-83d9-44ce-b8f7-5fab2a2cadf9

        :Assert: HostGroup is updated.
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

        :assert: HostGroup name is not updated
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

        :Assert: Puppet class is associated with hostgroup
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

        :Assert: Puppet class is associated with hostgroup
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

        :Assert: All puppet classes are associated with hostgroup

        :BZ: 1264163
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
    def test_positive_delete_by_id(self):
        """Create HostGroup with valid values then delete it
        by ID

        :id: fe7dedd4-d7c3-4c70-b70d-c2deff357b76

        :assert: HostGroup is deleted
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

        :assert: HostGroup is not deleted
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.delete({'id': entity_id})

    @tier2
    def test_positive_list_scparams_by_id(self):
        """List all overridden smart class parameters using hostgroup id

        :id: 42a24060-2ed7-427e-8396-86d73bbe5f69

        :Assert: Overridden sc-param from puppet class is listed

        :Caselevel: Integration
        """
        # Create hostgroup with associated puppet class
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list({
            'environment': self.env['name'],
            'search': u'puppetclass="{0}"'.format(self.puppet_class['name'])
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

        :Assert: Overridden sc-param from puppet class is listed

        :Caselevel: Integration
        """
        # Create hostgroup with associated puppet class
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list({
            'environment': self.env['name'],
            'search': u'puppetclass="{0}"'.format(self.puppet_class['name'])
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

        :Assert: Smart variable from puppet class is listed

        :Caselevel: Integration
        """
        # Create hostgroup with associated puppet class
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        # Create smart variable
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name']})
        # Verify that affected sc-param is listed
        hg_variables = HostGroup.smart_variables(
            {'hostgroup-id': hostgroup['id']})
        self.assertIn(smart_variable['id'], [sv['id'] for sv in hg_variables])

    @tier2
    def test_positive_list_smartvariables_by_name(self):
        """List all smart variables using hostgroup name

        :id: 2b0da695-57fa-4f91-b164-e1ff60076c26

        :Assert: Smart variable from puppet class is listed

        :Caselevel: Integration
        """
        # Create hostgroup with associated puppet class
        hostgroup = make_hostgroup({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.env['name'],
            'content-view': self.cv['name'],
            'query-organization': self.org['name'],
        })
        # Create smart variable
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name']})
        # Verify that affected sc-param is listed
        hg_variables = HostGroup.smart_variables(
            {'hostgroup': hostgroup['name']})
        self.assertIn(smart_variable['id'], [sv['id'] for sv in hg_variables])
