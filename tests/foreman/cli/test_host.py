"""CLI tests for ``hammer host``.

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import time
from random import choice

import pytest
import yaml
from fauxfactory import gen_integer
from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_string
from nailgun import entities

from robottelo import ssh
from robottelo.api.utils import wait_for_errata_applicability_task
from robottelo.cleanup import capsule_cleanup
from robottelo.cleanup import vm_cleanup
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.environment import Environment
from robottelo.cli.factory import add_role_permissions
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_activation_key
from robottelo.cli.factory import make_architecture
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_domain
from robottelo.cli.factory import make_environment
from robottelo.cli.factory import make_fake_host
from robottelo.cli.factory import make_host
from robottelo.cli.factory import make_host_collection
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_os
from robottelo.cli.factory import make_proxy
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_smart_variable
from robottelo.cli.factory import make_user
from robottelo.cli.factory import publish_puppet_module
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.host import Host
from robottelo.cli.host import HostInterface
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.org import Org
from robottelo.cli.package import Package
from robottelo.cli.proxy import Proxy
from robottelo.cli.puppet import Puppet
from robottelo.cli.scparams import SmartClassParameter
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP_NAME
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_ERRATA_ID
from robottelo.constants import FAKE_1_YUM_REPO
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_2_ERRATA_ID
from robottelo.constants import FAKE_6_YUM_REPO
from robottelo.constants import NO_REPOS_AVAILABLE
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants import SATELLITE_SUBSCRIPTION_NAME
from robottelo.constants import SM_OVERALL_STATUS
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_hosts_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine
from robottelo.vm import VirtualMachineError


class HostCreateTestCase(CLITestCase):
    """Tests for creating the hosts via CLI."""

    @classmethod
    def setUpClass(cls):
        """Create organization, lifecycle environment, content view, publish
        and promote new version to re-use in tests.
        """
        super(HostCreateTestCase, cls).setUpClass()
        cls.new_org = make_org()
        cls.new_loc = make_location()
        cls.new_lce = make_lifecycle_environment({'organization-id': cls.new_org['id']})
        cls.LIBRARY = LifecycleEnvironment.info(
            {'organization-id': cls.new_org['id'], 'name': ENVIRONMENT}
        )
        cls.DEFAULT_CV = ContentView.info(
            {'organization-id': cls.new_org['id'], 'name': DEFAULT_CV}
        )
        cls.new_cv = make_content_view({'organization-id': cls.new_org['id']})
        ContentView.publish({'id': cls.new_cv['id']})
        version_id = ContentView.version_list({'content-view-id': cls.new_cv['id']})[0]['id']
        ContentView.version_promote(
            {
                'id': version_id,
                'to-lifecycle-environment-id': cls.new_lce['id'],
                'organization-id': cls.new_org['id'],
            }
        )
        cls.promoted_cv = cls.new_cv
        # Setup for puppet class related tests
        puppet_modules = [{'author': 'robottelo', 'name': 'generic_1'}]
        cls.puppet_cv = publish_puppet_module(
            puppet_modules, CUSTOM_PUPPET_REPO, cls.new_org['id']
        )
        cls.puppet_env = Environment.list(
            {'search': u'content_view="{0}"'.format(cls.puppet_cv['name'])}
        )[0]
        cls.puppet_class = Puppet.info(
            {'name': puppet_modules[0]['name'], 'puppet-environment': cls.puppet_env['name']}
        )
        # adding org to a puppet env
        Org.set_parameter(
            {
                'name': 'Environment',
                'value': cls.puppet_env["name"],
                'organization': cls.new_org["name"],
            }
        )

    def setUp(self):
        """Find an existing puppet proxy.

        Record information about this puppet proxy as ``self.puppet_proxy``.
        """
        super(HostCreateTestCase, self).setUp()
        # Use the default installation smart proxy
        self.puppet_proxy = Proxy.list(
            {'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]

    @tier1
    @upgrade
    def test_positive_create_and_delete(self):
        """A host can be created and deleted

        :id: 59fcbe50-9c6b-4c3c-87b3-272b4b584fb3

        :expectedresults: A host is created and deleted

        :BZ: 1260697, 1313056, 1361309

        :CaseImportance: Critical
        """
        name = valid_hosts_list()[0]
        host = entities.Host()
        host.create_missing()
        interface = (
            "type=interface,mac={0},identifier=eth0,name={1},domain_id={2},"
            "ip={3},primary=true,provision=true"
        ).format(host.mac, gen_string('alpha'), host.domain.id, gen_ipaddr())
        new_host = make_host(
            {
                u'architecture-id': host.architecture.id,
                u'content-view-id': self.DEFAULT_CV['id'],
                u'domain-id': host.domain.id,
                u'environment-id': host.environment.id,
                u'interface': interface,
                u'lifecycle-environment-id': self.LIBRARY['id'],
                u'location-id': host.location.id,
                u'mac': host.mac,
                u'medium-id': host.medium.id,
                u'name': name,
                u'operatingsystem-id': host.operatingsystem.id,
                u'organization-id': host.organization.id,
                u'partition-table-id': host.ptable.id,
                u'root-password': host.root_pass,
            }
        )
        self.assertEqual('{0}.{1}'.format(name, host.domain.read().name), new_host['name'])
        self.assertEqual(new_host['organization'], host.organization.name)
        self.assertEqual(
            new_host['content-information']['content-view']['name'], self.DEFAULT_CV['name']
        )
        self.assertEqual(
            new_host['content-information']['lifecycle-environment']['name'], self.LIBRARY['name']
        )
        host_interface = HostInterface.info(
            {u'host-id': new_host['id'], u'id': new_host['network-interfaces'][0]['id']}
        )
        self.assertEqual(host_interface['domain'], host.domain.read().name)

        Host.delete({'id': new_host['id']})
        with self.assertRaises(CLIReturnCodeError):
            Host.info({'id': new_host['id']})

    @tier1
    def test_positive_add_interface_by_id(self):
        """New network interface can be added to existing host

        :id: e97dba92-61eb-47ad-a7d7-5f989292b12a

        :expectedresults: Interface added to host correctly and has proper
            domain and mac address

        :CaseImportance: Critical
        """
        domain = make_domain(
            {u'organizations': u'Default Organization', u'locations': u'Default Location'}
        )
        mac = gen_mac(multicast=False)
        host = make_fake_host({u'domain-id': domain['id']})
        HostInterface.create(
            {
                u'host-id': host['id'],
                u'domain-id': domain['id'],
                u'mac': mac,
                u'type': u'interface',
            }
        )
        host = Host.info({u'id': host['id']})
        host_interface = HostInterface.info(
            {
                u'host-id': host['id'],
                u'id': [ni for ni in host['network-interfaces'] if ni['mac-address'] == mac][0][
                    'id'
                ],
            }
        )
        self.assertEqual(host_interface['domain'], domain['name'])
        self.assertEqual(host_interface['mac-address'], mac)

    @run_in_one_thread
    @tier2
    def test_positive_create_and_update_with_content_source(self):
        """Create a host with content source specified and update content
            source

        :id: 5712f4db-3610-447d-b1da-0fe461577d59

        :customerscenario: true

        :BZ: 1260697, 1483252, 1313056, 1488465

        :expectedresults: A host is created with expected content source
            assigned and then content source is successfully updated

        :CaseImportance: High
        """
        content_source = Proxy.list(
            {'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        host = make_fake_host(
            {
                'content-source-id': content_source['id'],
                'content-view-id': self.DEFAULT_CV['id'],
                'lifecycle-environment-id': self.LIBRARY['id'],
                'organization': self.new_org['name'],
            }
        )
        self.assertEqual(
            host['content-information']['content-source']['name'], content_source['name']
        )
        new_content_source = make_proxy()
        self.addCleanup(capsule_cleanup, new_content_source['id'])
        self.addCleanup(Host.delete, {'id': host['id']})
        Host.update({'id': host['id'], 'content-source-id': new_content_source['id']})
        host = Host.info({'id': host['id']})
        self.assertEqual(
            host['content-information']['content-source']['name'], new_content_source['name']
        )

    @tier2
    def test_negative_create_with_content_source(self):
        """Attempt to create a host with invalid content source specified

        :id: d92d6aff-4ad3-467c-88a8-5a5e56614f58

        :BZ: 1260697

        :expectedresults: Host was not created

        :CaseImportance: Medium
        """
        with self.assertRaises(CLIFactoryError):
            make_fake_host(
                {
                    'content-source-id': gen_integer(10000, 99999),
                    'content-view-id': self.DEFAULT_CV['id'],
                    'lifecycle-environment-id': self.LIBRARY['id'],
                    'organization': self.new_org['name'],
                }
            )

    @tier2
    def test_negative_update_content_source(self):
        """Attempt to update host's content source with invalid value

        :id: 03243c56-3835-4b15-94df-15d436bbda87

        :BZ: 1260697, 1483252, 1313056

        :expectedresults: Host was not updated. Content source remains the same
            as it was before update

        :CaseImportance: Medium
        """
        content_source = Proxy.list(
            {'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        host = make_fake_host(
            {
                'content-source-id': content_source['id'],
                'content-view-id': self.DEFAULT_CV['id'],
                'lifecycle-environment-id': self.LIBRARY['id'],
                'organization': self.new_org['name'],
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            Host.update({'id': host['id'], 'content-source-id': gen_integer(10000, 99999)})
        host = Host.info({'id': host['id']})
        self.assertEqual(
            host['content-information']['content-source']['name'], content_source['name']
        )

    @tier1
    def test_positive_create_with_lce_and_cv(self):
        """Check if host can be created with new lifecycle and
            new content view

        :id: c2075131-6b25-4af3-b1e9-a7a9190dd6f8

        :expectedresults: Host is created using new lifecycle and
            new content view

        :BZ: 1313056

        :CaseImportance: Critical
        """
        new_host = make_fake_host(
            {
                'content-view-id': self.promoted_cv['id'],
                'lifecycle-environment-id': self.new_lce['id'],
                'organization-id': self.new_org['id'],
            }
        )
        self.assertEqual(
            new_host['content-information']['lifecycle-environment']['name'], self.new_lce['name']
        )
        self.assertEqual(
            new_host['content-information']['content-view']['name'], self.promoted_cv['name']
        )

    @tier1
    def test_positive_create_with_puppet_class_name(self):
        """Check if host can be created with puppet class name

        :id: a65df36e-db4b-48d2-b0e1-5ccfbefd1e7a

        :expectedresults: Host is created and has puppet class assigned

        :CaseImportance: Critical
        """
        host = make_fake_host(
            {
                'puppet-classes': self.puppet_class['name'],
                'environment': self.puppet_env['name'],
                'organization-id': self.new_org['id'],
            }
        )
        host_classes = Host.puppetclasses({'host': host['name']})
        self.assertIn(self.puppet_class['name'], [puppet['name'] for puppet in host_classes])

    @tier2
    def test_positive_create_with_openscap_proxy_id(self):
        """Check if host can be created with OpenSCAP Proxy id

        :id: 3774ba08-3b18-4e64-b07f-53f6aa0504f3

        :expectedresults: Host is created and has OpenSCAP Proxy assigned

        :CaseImportance: Medium
        """
        openscap_proxy = Proxy.list(
            {'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]

        host = make_fake_host(
            {'organization-id': self.new_org['id'], 'openscap-proxy-id': openscap_proxy['id']}
        )
        assert host['openscap-proxy'] == openscap_proxy['id']

    @tier1
    def test_negative_create_with_name(self):
        """Check if host can be created with random long names

        :id: f92b6070-b2d1-4e3e-975c-39f1b1096697

        :expectedresults: Host is not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_fake_host(
                        {
                            'name': name,
                            'organization-id': self.new_org['id'],
                            'content-view-id': self.DEFAULT_CV['id'],
                            'lifecycle-environment-id': self.LIBRARY['id'],
                        }
                    )

    @tier1
    def test_negative_create_with_unpublished_cv(self):
        """Check if host can be created using unpublished cv

        :id: 9997383d-3c27-4f14-94f9-4b8b51180eb6

        :expectedresults: Host is not created using new unpublished cv

        :CaseImportance: Critical
        """
        cv = make_content_view({'organization-id': self.new_org['id']})
        env = self.new_lce['id']
        with self.assertRaises(CLIFactoryError):
            make_fake_host(
                {
                    'content-view-id': cv['id'],
                    'lifecycle-environment-id': env,
                    'organization-id': self.new_org['id'],
                }
            )

    @tier3
    @upgrade
    def test_positive_katello_and_openscap_loaded(self):
        """Verify that command line arguments from both Katello
        and foreman_openscap plugins are loaded and available
        at the same time

        :id: 5b5db1d4-50f9-45a0-bb92-4571fc8d729b

        :expectedresults: Command line arguments from both Katello
            and foreman_openscap are available in help message
            (note: help is generated dynamically based on apipie cache)

        :CaseLevel: System

        :CaseImportance: Medium

        :BZ: 1671148
        """
        help_output = Host.execute('host update --help')
        for arg in ['lifecycle-environment-id', 'openscap-proxy-id']:
            assert any(
                ('--{}'.format(arg) in line for line in help_output)
            ), "--{} not supported by update subcommand".format(arg)

    @tier3
    @upgrade
    def test_positive_register_with_no_ak(self):
        """Register host to satellite without activation key

        :id: 6a7cedd2-aa9c-4113-a83b-3f0eea43ecb4

        :expectedresults: Host successfully registered to appropriate org

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.new_org['label'],
                lce='{}/{}'.format(self.new_lce['label'], self.promoted_cv['label']),
            )
            self.assertTrue(client.subscribed)

    @tier3
    def test_negative_register_twice(self):
        """Attempt to register a host twice to Satellite

        :id: 0af81129-cd69-4fa7-a128-9e8fcf2d03b1

        :expectedresults: host cannot be registered twice

        :CaseLevel: System
        """
        activation_key = make_activation_key(
            {
                'content-view-id': self.promoted_cv['id'],
                'lifecycle-environment-id': self.new_lce['id'],
                'organization-id': self.new_org['id'],
            }
        )
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(self.new_org['label'], activation_key['name'])
            self.assertTrue(client.subscribed)
            result = client.register_contenthost(
                self.new_org['label'], activation_key['name'], force=False
            )
            # Depending on distro version, successful return_code may be 0 or
            # 1, so we can't verify host wasn't registered by return_code != 0
            # check. Verifying return_code == 64 here, which stands for content
            # host being already registered.
            self.assertEqual(result.return_code, 64)

    @tier2
    def test_positive_list_scparams_and_smartvariables(self):
        """List all smart class parameters and smart variables using host id

        :id: 61814875-5ccd-4c04-a06f-d36fe089d514

        :expectedresults: Overridden sc-param and smart variable from puppet
            class are listed

        :CaseLevel: Integration
        """
        # Create hostgroup with associated puppet class
        host = make_fake_host(
            {
                'puppet-classes': self.puppet_class['name'],
                'environment': self.puppet_env['name'],
                'organization-id': self.new_org['id'],
            }
        )
        # Create smart variable
        smart_variable = make_smart_variable({'puppet-class': self.puppet_class['name']})
        # Verify that affected sc-param is listed
        host_variables = Host.smart_variables({'host-id': host['id']})
        self.assertIn(smart_variable['id'], [sv['id'] for sv in host_variables])

        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list(
            {
                'environment': self.puppet_env['name'],
                'search': u'puppetclass="{0}"'.format(self.puppet_class['name']),
            }
        )
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        host_scparams = Host.sc_params({'host': host['name']})
        self.assertIn(scp_id, [scp['id'] for scp in host_scparams])

    @tier3
    def test_positive_list(self):
        """List hosts for a given org

        :id: b9c056cd-11ca-4870-bac4-0ebc4a782cb0

        :expectedresults: Hosts are listed for the given org

        :CaseLevel: System
        """
        activation_key = make_activation_key(
            {
                'content-view-id': self.promoted_cv['id'],
                'lifecycle-environment-id': self.new_lce['id'],
                'organization-id': self.new_org['id'],
            }
        )
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(self.new_org['label'], activation_key['name'])
            self.assertTrue(client.subscribed)
            hosts = Host.list(
                {'organization-id': self.new_org['id'], 'environment-id': self.new_lce['id']}
            )
            self.assertGreaterEqual(len(hosts), 1)
            self.assertIn(client.hostname, [host['name'] for host in hosts])

    @tier3
    def test_positive_list_by_last_checkin(self):
        """List all content hosts using last checkin criteria

        :id: e7d86b44-28c3-4525-afac-61a20e62daf8

        :customerscenario: true

        :expectedresults: Hosts are listed for the given time period

        :BZ: 1285992

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.new_org['label'],
                lce='{}/{}'.format(self.new_lce['label'], self.promoted_cv['label']),
            )
            self.assertTrue(client.subscribed)
            hosts = Host.list(
                {'search': 'last_checkin = "Today" or ' 'last_checkin = "Yesterday"'}
            )
            self.assertGreaterEqual(len(hosts), 1)
            self.assertIn(client.hostname, [host['name'] for host in hosts])

    @tier3
    @upgrade
    def test_positive_unregister(self):
        """Unregister a host

        :id: c5ce988d-d0ea-4958-9956-5a4b039b285c

        :expectedresults: Host is successfully unregistered. Unlike content
            host, host has not disappeared from list of hosts after
            unregistering.

        :CaseLevel: System
        """
        activation_key = make_activation_key(
            {
                'content-view-id': self.promoted_cv['id'],
                'lifecycle-environment-id': self.new_lce['id'],
                'organization-id': self.new_org['id'],
            }
        )
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(self.new_org['label'], activation_key['name'])
            self.assertTrue(client.subscribed)
            hosts = Host.list(
                {'organization-id': self.new_org['id'], 'environment-id': self.new_lce['id']}
            )
            self.assertGreaterEqual(len(hosts), 1)
            self.assertIn(client.hostname, [host['name'] for host in hosts])
            result = client.run('subscription-manager unregister')
            self.assertEqual(result.return_code, 0)
            hosts = Host.list(
                {'organization-id': self.new_org['id'], 'environment-id': self.new_lce['id']}
            )
            self.assertIn(client.hostname, [host['name'] for host in hosts])

    @skip_if_not_set('compute_resources')
    @tier1
    def test_positive_create_using_libvirt_without_mac(self):
        """Create a libvirt host and not specify a MAC address.

        :id: b003faa9-2810-4176-94d2-ea84bed248eb

        :expectedresults: Host is created

        :CaseImportance: Critical
        """
        compute_resource = entities.LibvirtComputeResource(
            url='qemu+ssh://root@{0}/system'.format(settings.compute_resources.libvirt_hostname),
            organization=[self.new_org['id']],
            location=[self.new_loc['id']],
        ).create()
        host = entities.Host(organization=self.new_org['id'], location=self.new_loc['id'])
        host.create_missing()
        result = make_host(
            {
                u'architecture-id': host.architecture.id,
                u'compute-resource-id': compute_resource.id,
                u'domain-id': host.domain.id,
                u'environment-id': host.environment.id,
                u'location-id': host.location.id,
                u'medium-id': host.medium.id,
                u'name': host.name,
                u'operatingsystem-id': host.operatingsystem.id,
                u'organization-id': host.organization.id,
                u'partition-table-id': host.ptable.id,
                u'puppet-proxy-id': self.puppet_proxy['id'],
                u'root-password': host.root_pass,
            }
        )
        self.assertEqual(result['name'], host.name + '.' + host.domain.name)
        Host.delete({'id': result['id']})

    @tier2
    def test_positive_create_inherit_lce_cv(self):
        """Create a host with hostgroup specified. Make sure host inherited
        hostgroup's lifecycle environment and content-view

        :id: ba73b8c8-3ce1-4fa8-a33b-89ded9ffef47

        :expectedresults: Host's lifecycle environment and content view match
            the ones specified in hostgroup

        :CaseLevel: Integration

        :BZ: 1391656
        """
        hostgroup = make_hostgroup(
            {
                'content-view-id': self.new_cv['id'],
                'lifecycle-environment-id': self.new_lce['id'],
                'organization-ids': self.new_org['id'],
            }
        )
        host = make_fake_host(
            {'hostgroup-id': hostgroup['id'], 'organization-id': self.new_org['id']}
        )
        self.assertEqual(
            host['content-information']['lifecycle-environment']['name'],
            hostgroup['lifecycle-environment']['name'],
        )
        self.assertEqual(
            host['content-information']['content-view']['name'], hostgroup['content-view']['name']
        )

    @tier3
    def test_positive_create_inherit_nested_hostgroup(self):
        """Create two nested host groups with the same name, but different
        parents. Then create host using any from these hostgroups title

        :id: 7bc95130-3f20-493d-b54c-04c444d97563

        :expectedresults: Host created successfully using host group title

        :CaseLevel: System

        :BZ: 1436162
        """
        options = entities.Host()
        options.create_missing()
        lce = make_lifecycle_environment({'organization-id': options.organization.id})
        cv = make_content_view({'organization-id': options.organization.id})
        ContentView.publish({'id': cv['id']})
        version_id = ContentView.version_list({'content-view-id': cv['id']})[0]['id']
        ContentView.version_promote({'id': version_id, 'to-lifecycle-environment-id': lce['id']})
        host_name = gen_string('alpha').lower()
        nested_hg_name = gen_string('alpha')
        parent_hostgroups = []
        nested_hostgroups = []
        for _ in range(2):
            parent_hg_name = gen_string('alpha')
            parent_hostgroups.append(
                make_hostgroup(
                    {'name': parent_hg_name, 'organization-ids': options.organization.id}
                )
            )
            nested_hostgroups.append(
                make_hostgroup(
                    {
                        'name': nested_hg_name,
                        'parent': parent_hg_name,
                        'organization-ids': options.organization.id,
                        'architecture-id': options.architecture.id,
                        'domain-id': options.domain.id,
                        'medium-id': options.medium.id,
                        'operatingsystem-id': options.operatingsystem.id,
                        'partition-table-id': options.ptable.id,
                        'location-ids': options.location.id,
                        'content-view-id': cv['id'],
                        'lifecycle-environment-id': lce['id'],
                    }
                )
            )

        host = make_host(
            {
                'hostgroup-title': nested_hostgroups[0]['title'],
                'location-id': options.location.id,
                'organization-id': options.organization.id,
                'name': host_name,
            }
        )
        self.assertEqual('{0}.{1}'.format(host_name, options.domain.read().name), host['name'])

    @tier3
    def test_positive_list_with_nested_hostgroup(self):
        """Create parent and nested host groups. Then create host using nested
        hostgroup and then find created host using list command

        :id: 50c964c3-d3d6-4832-a51c-62664d132229

        :customerscenario: true

        :expectedresults: Host is successfully listed and has both parent and
            nested host groups names in its hostgroup parameter

        :BZ: 1427554

        :CaseLevel: System
        """
        options = entities.Host()
        options.create_missing()
        host_name = gen_string('alpha').lower()
        parent_hg_name = gen_string('alpha')
        nested_hg_name = gen_string('alpha')
        lce = make_lifecycle_environment({'organization-id': options.organization.id})
        cv = make_content_view({'organization-id': options.organization.id})
        ContentView.publish({'id': cv['id']})
        version_id = ContentView.version_list({'content-view-id': cv['id']})[0]['id']
        ContentView.version_promote({'id': version_id, 'to-lifecycle-environment-id': lce['id']})
        make_hostgroup({'name': parent_hg_name, 'organization-ids': options.organization.id})
        nested_hostgroup = make_hostgroup(
            {
                'name': nested_hg_name,
                'parent': parent_hg_name,
                'organization-ids': options.organization.id,
                'architecture-id': options.architecture.id,
                'domain-id': options.domain.id,
                'medium-id': options.medium.id,
                'operatingsystem-id': options.operatingsystem.id,
                'partition-table-id': options.ptable.id,
                'location-ids': options.location.id,
                'content-view-id': cv['id'],
                'lifecycle-environment-id': lce['id'],
            }
        )
        make_host(
            {
                'hostgroup-id': nested_hostgroup['id'],
                'location-id': options.location.id,
                'organization-id': options.organization.id,
                'name': host_name,
            }
        )
        hosts = Host.list({'organization-id': options.organization.id})
        self.assertEqual('{0}/{1}'.format(parent_hg_name, nested_hg_name), hosts[0]['host-group'])

    @stubbed()
    @tier3
    def test_negative_create_with_incompatible_pxe_loader(self):
        """Try to create host with a known OS and incompatible PXE loader

        :id: 75d7ab06-2d23-4f85-a080-faadfe2b294a

        :setup:
          1. Synchronize RHEL[5,6,7] kickstart repos


        :steps:
          1. create a new RHEL host using 'BareMetal' option and the following
             OS-PXE_loader combinations:

             a RHEL5,6 - GRUB2_UEFI
             b RHEL5,6 - GRUB2_UEFI_SB
             c RHEL7 - GRUB_UEFI
             d RHEL7 - GRUB_UEFI_SB

        :expectedresults:
          1. Warning message appears
          2. Files not deployed on TFTP
          3. Host not created

        :CaseAutomation: notautomated

        :CaseLevel: System
        """


class HostUpdateTestCase(CLITestCase):
    """Tests for updating the hosts."""

    def setUp(self):
        """Create a host to reuse later"""
        super(HostUpdateTestCase, self).setUp()
        self.puppet_proxy = Proxy.list(
            {'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        # using nailgun to create dependencies
        self.host_args = entities.Host()
        self.host_args.create_missing()
        # using CLI to create host
        self.host = make_host(
            {
                u'architecture-id': self.host_args.architecture.id,
                u'domain-id': self.host_args.domain.id,
                u'environment-id': self.host_args.environment.id,
                u'location-id': self.host_args.location.id,
                u'mac': self.host_args.mac,
                u'medium-id': self.host_args.medium.id,
                u'name': self.host_args.name,
                u'operatingsystem-id': self.host_args.operatingsystem.id,
                u'organization-id': self.host_args.organization.id,
                u'partition-table-id': self.host_args.ptable.id,
                u'puppet-proxy-id': self.puppet_proxy['id'],
                u'root-password': self.host_args.root_pass,
            }
        )

    @tier1
    def test_positive_update_parameters_by_name(self):
        """A host can be updated with a new name, mac address, domain,
            location, environment, architecture, operating system and medium.
            Use id to access the host

        :id: 3a4c0b5a-5d87-477a-b80a-9af0ec3b4b6f

        :expectedresults: A host is updated and the name, mac address, domain,
            location, environment, architecture, operating system and medium
            matches

        :BZ: 1343392, 1679300

        :CaseImportance: Critical
        """
        new_name = valid_hosts_list()[0]
        new_mac = gen_mac(multicast=False)
        new_loc = make_location()
        new_domain = make_domain(
            {'locations': new_loc['name'], 'organizations': self.host_args.organization.name}
        )
        new_env = make_environment(
            {'locations': new_loc['name'], 'organizations': self.host_args.organization.name}
        )
        new_arch = make_architecture()
        new_os = make_os(
            {'architectures': new_arch['name'], 'partition-table-ids': self.host_args.ptable.id}
        )
        new_medium = make_medium(
            {
                'locations': new_loc['name'],
                'organizations': self.host_args.organization.name,
                'operatingsystems': new_os['title'],
            }
        )
        Host.update(
            {
                'architecture': new_arch['name'],
                'domain': new_domain['name'],
                'environment': new_env['name'],
                'name': self.host['name'],
                'mac': new_mac,
                'medium-id': new_medium['id'],
                'new-name': new_name,
                'operatingsystem': new_os['title'],
                'new-location-id': new_loc['id'],
            }
        )
        self.host = Host.info({'id': self.host['id']})
        self.assertEqual(
            u'{0}.{1}'.format(new_name, self.host['network']['domain']), self.host['name']
        )
        self.assertEqual(self.host['location'], new_loc['name'])
        self.assertEqual(self.host['network']['mac'], new_mac)
        self.assertEqual(self.host['network']['domain'], new_domain['name'])
        self.assertEqual(self.host['puppet-environment'], new_env['name'])
        self.assertEqual(self.host['operating-system']['architecture'], new_arch['name'])
        self.assertEqual(self.host['operating-system']['operating-system'], new_os['title'])
        self.assertEqual(self.host['operating-system']['medium'], new_medium['name'])

    @tier1
    def test_negative_update_name(self):
        """A host can not be updated with invalid or empty name

        :id: e8068d2a-6a51-4627-908b-60a516c67032

        :expectedresults: A host is not updated

        :CaseImportance: Critical
        """
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    Host.update({'id': self.host['id'], 'new-name': new_name})
                self.host = Host.info({'id': self.host['id']})
                self.assertNotEqual(
                    u'{0}.{1}'.format(new_name, self.host['network']['domain']).lower(),
                    self.host['name'],
                )

    @tier1
    def test_negative_update_mac(self):
        """A host can not be updated with invalid or empty MAC address

        :id: 2f03032d-789d-419f-9ff2-a6f3561444da

        :expectedresults: A host is not updated

        :CaseImportance: Critical
        """
        for new_mac in invalid_values_list():
            with self.subTest(new_mac):
                with self.assertRaises(CLIReturnCodeError):
                    Host.update({'id': self.host['id'], 'mac': new_mac})
                    self.host = Host.info({'id': self.host['id']})
                    self.assertEqual(self.host['network']['mac'], new_mac)

    @tier2
    def test_negative_update_arch(self):
        """A host can not be updated with a architecture, which does not
        belong to host's operating system

        :id: a86524da-8caf-472b-9a3d-17a4385c3a18

        :expectedresults: A host is not updated

        :CaseLevel: Integration
        """
        new_arch = make_architecture()
        with self.assertRaises(CLIReturnCodeError):
            Host.update({'architecture': new_arch['name'], 'id': self.host['id']})
        self.host = Host.info({'id': self.host['id']})
        self.assertNotEqual(self.host['operating-system']['architecture'], new_arch['name'])

    @tier2
    def test_negative_update_os(self):
        """A host can not be updated with a operating system, which is
        not associated with host's medium

        :id: ff13d2af-e54a-4daf-a24d-7ec930b4fbbe

        :expectedresults: A host is not updated

        :CaseLevel: Integration
        """
        new_arch = make_architecture()
        new_os = make_os(
            {
                'architectures': new_arch['name'],
                'partition-tables': self.host['operating-system']['partition-table'],
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            Host.update(
                {
                    'architecture': new_arch['name'],
                    'id': self.host['id'],
                    'operatingsystem': new_os['title'],
                }
            )
        self.host = Host.info({'id': self.host['id']})
        self.assertNotEqual(self.host['operating-system']['operating-system'], new_os['title'])


class HostParameterTestCase(CLITestCase):
    """Tests targeting host parameters"""

    @classmethod
    def setUpClass(cls):
        """Create host to tests parameters for"""
        super(HostParameterTestCase, cls).setUpClass()
        cls.puppet_proxy = Proxy.list(
            {'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        # using nailgun to create dependencies
        cls.host_template = entities.Host()
        cls.host_template.create_missing()
        cls.org_id = cls.host_template.organization.id
        cls.loc_id = cls.host_template.location.id
        # using CLI to create host
        cls.host = make_host(
            {
                u'architecture-id': cls.host_template.architecture.id,
                u'domain-id': cls.host_template.domain.id,
                u'environment-id': cls.host_template.environment.id,
                u'location-id': cls.loc_id,
                u'mac': cls.host_template.mac,
                u'medium-id': cls.host_template.medium.id,
                u'name': cls.host_template.name,
                u'operatingsystem-id': cls.host_template.operatingsystem.id,
                u'organization-id': cls.org_id,
                u'partition-table-id': cls.host_template.ptable.id,
                u'puppet-proxy-id': cls.puppet_proxy['id'],
                u'root-password': cls.host_template.root_pass,
            }
        )

    @tier1
    def test_positive_parameter_crud(self):
        """Add, update and remove host parameter with valid name.

        :id: 76034424-cf18-4ced-916b-ee9798c311bc

        :expectedresults: Host parameter was successfully added, updated and
            removed.

        :CaseImportance: Critical
        """
        name = valid_data_list()[0].lower()
        value = valid_data_list()[0]
        Host.set_parameter({'host-id': self.host['id'], 'name': name, 'value': value})
        self.host = Host.info({'id': self.host['id']})
        self.assertIn(name, self.host['parameters'].keys())
        self.assertEqual(value, self.host['parameters'][name])

        new_value = valid_data_list()[0]
        Host.set_parameter({'host-id': self.host['id'], 'name': name, 'value': new_value})
        self.host = Host.info({'id': self.host['id']})
        self.assertIn(name, self.host['parameters'].keys())
        self.assertEqual(new_value, self.host['parameters'][name])

        Host.delete_parameter({'host-id': self.host['id'], 'name': name})
        self.host = Host.info({'id': self.host['id']})
        self.assertNotIn(name, self.host['parameters'].keys())

    @tier1
    def test_negative_add_parameter(self):
        """Try to add host parameter with different invalid names.

        :id: 473f8c3f-b66e-4526-88af-e139cc3dabcb

        :expectedresults: Host parameter was not added.


        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                name = name.lower()
                with self.assertRaises(CLIReturnCodeError):
                    Host.set_parameter(
                        {
                            'host-id': self.host['id'],
                            'name': name,
                            'value': gen_string('alphanumeric'),
                        }
                    )
                self.host = Host.info({'id': self.host['id']})
                self.assertNotIn(name, self.host['parameters'].keys())

    @tier2
    def test_negative_view_parameter_by_non_admin_user(self):
        """Attempt to view parameters with non admin user without Parameter
         permissions

        :id: 65ba89f0-9bee-43d9-814b-9f5a194558f8

        :customerscenario: true

        :steps:
            1. As admin user create a host
            2. Set a host parameter name and value
            3. Create a non admin user with the following permissions:
                Host: [view_hosts],
                Organization: [view_organizations],
            4. Get the host info as the non admin user

        :expectedresults: The non admin user is not able to read the parameters

        :BZ: 1296662
        """
        param_name = gen_string('alpha').lower()
        param_value = gen_string('alphanumeric')
        user_name = gen_string('alphanumeric')
        user_password = gen_string('alphanumeric')
        Host.set_parameter({'host-id': self.host['id'], 'name': param_name, 'value': param_value})
        host = Host.info({'id': self.host['id']})
        self.assertEqual(host['parameters'][param_name], param_value)
        role = make_role()
        add_role_permissions(
            role['id'],
            resource_permissions={
                'Host': {'permissions': ['view_hosts']},
                'Organization': {'permissions': ['view_organizations']},
            },
        )
        user = make_user(
            {
                'admin': False,
                'default-organization-id': self.org_id,
                'organization-ids': [self.org_id],
                'default-location-id': self.loc_id,
                'location-ids': [self.loc_id],
                'login': user_name,
                'password': user_password,
            }
        )
        User.add_role({'id': user['id'], 'role-id': role['id']})
        host = Host.with_user(username=user_name, password=user_password).info(
            {'id': self.host['id']}
        )
        self.assertFalse(host.get('parameters'))

    @tier2
    def test_positive_view_parameter_by_non_admin_user(self):
        """Attempt to view parameters with non admin user that has
        Parameter::vew_params permission

        :id: 22d7d7cf-3d4f-4ae2-beaf-c11e41f2d439

        :customerscenario: true

        :steps:
            1. As admin user create a host
            2. Set a host parameter name and value
            3. Create a non admin user with the following permissions:
                Host: [view_hosts],
                Organization: [view_organizations],
                Parameter: [view_params]
            4. Get the host info as the non admin user

        :expectedresults: The non admin user is able to read the parameters

        :BZ: 1296662
        """
        param_name = gen_string('alpha').lower()
        param_value = gen_string('alphanumeric')
        user_name = gen_string('alphanumeric')
        user_password = gen_string('alphanumeric')
        Host.set_parameter({'host-id': self.host['id'], 'name': param_name, 'value': param_value})
        host = Host.info({'id': self.host['id']})
        self.assertEqual(host['parameters'][param_name], param_value)
        role = make_role()
        add_role_permissions(
            role['id'],
            resource_permissions={
                'Host': {'permissions': ['view_hosts']},
                'Organization': {'permissions': ['view_organizations']},
                'Parameter': {'permissions': ['view_params']},
            },
        )
        user = make_user(
            {
                'admin': False,
                'default-organization-id': self.org_id,
                'organization-ids': [self.org_id],
                'default-location-id': self.loc_id,
                'location-ids': [self.loc_id],
                'login': user_name,
                'password': user_password,
            }
        )
        User.add_role({'id': user['id'], 'role-id': role['id']})
        host = Host.with_user(username=user_name, password=user_password).info(
            {'id': self.host['id']}
        )
        self.assertIn(param_name, host['parameters'])
        self.assertEqual(host['parameters'][param_name], param_value)

    @tier2
    def test_negative_edit_parameter_by_non_admin_user(self):
        """Attempt to edit parameter with non admin user that has
        Parameter::vew_params permission

        :id: 2b40b3b9-42db-48c8-a9d7-7c308dc6add0

        :customerscenario: true

        :steps:
            1. As admin user create a host
            2. Set a host parameter name and value
            3. Create a non admin user with the following permissions:
                Host: [view_hosts],
                Organization: [view_organizations],
                Parameter: [view_params]
            4. Attempt to edit the parameter value as the non admin user

        :expectedresults: The non admin user is not able to edit the parameter

        :BZ: 1296662
        """
        param_name = gen_string('alpha').lower()
        param_value = gen_string('alphanumeric')
        user_name = gen_string('alphanumeric')
        user_password = gen_string('alphanumeric')
        Host.set_parameter({'host-id': self.host['id'], 'name': param_name, 'value': param_value})
        host = Host.info({'id': self.host['id']})
        self.assertEqual(host['parameters'][param_name], param_value)
        role = make_role()
        add_role_permissions(
            role['id'],
            resource_permissions={
                'Host': {'permissions': ['view_hosts']},
                'Organization': {'permissions': ['view_organizations']},
                'Parameter': {'permissions': ['view_params']},
            },
        )
        user = make_user(
            {
                'admin': False,
                'default-organization-id': self.org_id,
                'organization-ids': [self.org_id],
                'default-location-id': self.loc_id,
                'location-ids': [self.loc_id],
                'login': user_name,
                'password': user_password,
            }
        )
        User.add_role({'id': user['id'], 'role-id': role['id']})
        param_new_value = gen_string('alphanumeric')
        with self.assertRaises(CLIReturnCodeError):
            Host.with_user(username=user_name, password=user_password).set_parameter(
                {'host-id': self.host['id'], 'name': param_name, 'value': param_new_value}
            )
        host = Host.info({'id': self.host['id']})
        self.assertEqual(host['parameters'][param_name], param_value)

    @tier2
    def test_positive_set_multi_line_and_with_spaces_parameter_value(self):
        """Check that host parameter value with multi-line and spaces is
        correctly restored from yaml format

        :id: 776feffd-1b46-46e9-925d-4739194c15cc

        :customerscenario: true

        :expectedresults: host parameter value is the same when restored
            from yaml format

        :BZ: 1315282

        :CaseLevel: Integration
        """
        param_name = gen_string('alpha').lower()
        # long string that should be escaped and affected by line break with
        # yaml dump by default
        param_value = (
            u'auth                          include              '
            u'password-auth\r\n'
            u'account     include                  password-auth'
        )
        host = make_host(
            {
                u'architecture-id': self.host_template.architecture.id,
                u'domain-id': self.host_template.domain.id,
                u'environment-id': self.host_template.environment.id,
                u'location-id': self.loc_id,
                u'mac': self.host_template.mac,
                u'medium-id': self.host_template.medium.id,
                u'operatingsystem-id': self.host_template.operatingsystem.id,
                u'organization-id': self.org_id,
                u'partition-table-id': self.host_template.ptable.id,
                u'puppet-proxy-id': self.puppet_proxy['id'],
                u'root-password': self.host_template.root_pass,
            }
        )
        # count parameters of a host
        response = Host.info({'id': host['id']}, output_format='yaml', return_raw_response=True)
        self.assertEqual(response.return_code, 0)
        yaml_content = yaml.load('\n'.join(response.stdout))
        host_initial_params = yaml_content.get('Parameters')
        # set parameter
        Host.set_parameter({'host-id': host['id'], 'name': param_name, 'value': param_value})
        response = Host.info({'id': host['id']}, output_format='yaml', return_raw_response=True)
        self.assertEqual(response.return_code, 0)
        yaml_content = yaml.load('\n'.join(response.stdout))
        host_parameters = yaml_content.get('Parameters')
        # check that number of params increased by one
        self.assertEqual(len(host_parameters), 1 + len(host_initial_params))
        filtered_params = [param for param in host_parameters if param['name'] == param_name]
        self.assertEqual(len(filtered_params), 1)
        self.assertEqual(filtered_params[0]['value'], param_value)


class HostProvisionTestCase(CLITestCase):
    """Provisioning-related tests"""

    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_baremetal_with_bios_syslinux(self):
        """Provision RHEL system on a new BIOS BM Host with SYSLINUX loader
        from provided MAC address

        :id: 01509973-9f0b-4166-9fbd-59b753a7384b

        :setup:
          1. Create a PXE-based VM with BIOS boot mode (outside of
             Satellite).
          2. Synchronize a RHEL Kickstart repo

        :steps:
          1. create a new RHEL host using 'BareMetal' option,
             PXEGRUB loader and MAC address of the pre-created VM
          2. do the provisioning assertions (assertion steps #1-6)
          3. reboot the host

        :expectedresults:
          1. The loader files on TFTP are in the appropriate format and in the
             appropriate dirs.
          2. PXE handoff is successful (tcpdump shows the VM has requested
             the correct files)
          3. VM started to provision (might be tricky to automate console
             checks)
          4. VM accessible via SSH, shows correct OS version in
             ``/etc/*release``
          5. Host info command states 'built' in the status
          6. GRUB config changes the boot order (boot local first)
          7. Hosts boots straight to RHEL after reboot (step #4)

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_provision_baremetal_with_uefi_syslinux(self):
        """Provision RHEL system on a new UEFI BM Host with SYSLINUX loader
        from provided MAC address

        :id: a02e39a9-e04b-483f-8036-a5fe0348f615

        :setup:
          1. Create a PXE-based VM with UEFI boot mode (outside of
             Satellite).
          2. Synchronize a RHEL Kickstart repo

        :steps:
          1. create a new RHEL host using 'BareMetal' option,
             PXELINUX BIOS loader and MAC address of the pre-created VM
          2. do the provisioning assertions (assertion steps #1-6)
          3. reboot the host

        :expectedresults:
          1. The loader files on TFTP are in the appropriate format and in the
             appropriate dirs.
          2. PXE handoff is successful (tcpdump shows the VM has requested
             the correct files)
          3. VM started to provision (might be tricky to automate console
             checks)
          4. VM accessible via SSH, shows correct OS version in
             ``/etc/*release``
          5. Host info command states 'built' in the status
          6. GRUB config changes the boot order (boot local first)
          7. Hosts boots straight to RHEL after reboot (step #4)

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_provision_baremetal_with_uefi_grub(self):
        """Provision a RHEL system on a new UEFI BM Host with GRUB loader from
        a provided MAC address

        :id: 508b268b-244d-4bf0-a92a-fbee96e7e8ae

        :setup:
          1. Create a PXE-based VM with UEFI boot mode (outside of
             Satellite).
          2. Synchronize a RHEL6 Kickstart repo (el7 kernel is too new
             for GRUB v1)

        :steps:
          1. create a new RHEL6 host using 'BareMetal' option,
             PXEGRUB loader and MAC address of the pre-created VM
          2. reboot the VM (to ensure the NW boot is run)
          3. do the provisioning assertions (assertion steps #1-6)
          4. reboot the host

        :expectedresults:
          1. The loader files on TFTP are in the appropriate format and in the
             appropriate dirs.
          2. PXE handoff is successful (tcpdump shows the VM has requested
             the correct files)
          3. VM started to provision (might be tricky to automate console
             checks)
          4. VM accessible via SSH, shows correct OS version in
             ``/etc/*release``
          5. Host info command states 'built' in the status
          6. GRUB config changes the boot order (boot local first)
          7. Hosts boots straight to RHEL after reboot (step #4)


        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_baremetal_with_uefi_grub2(self):
        """Provision a RHEL7+ system on a new UEFI BM Host with GRUB2 loader
        from a provided MAC address

        :id: b944c1b4-8612-4299-ac2e-9f77487ba669

        :setup:
          1. Create a PXE-based VM with UEFI boot mode (outside of
             Satellite).
          2. Synchronize a RHEL7+ Kickstart repo
             (el6 kernel is too old for GRUB2)

        :steps:
          1. create a new RHEL7+ host using 'BareMetal' option,
             PXEGRUB2 loader and MAC address of the pre-created VM
          2. reboot the VM (to ensure the NW boot is run)
          3. do the provisioning assertions (assertion steps #1-6)
          4. reboot the host


        :expectedresults:
          1. The loader files on TFTP are in the appropriate format and in the
             appropriate dirs.
          2. PXE handoff is successful (tcpdump shows the VM has requested
             the correct files)
          3. VM started to provision (might be tricky to automate console
             checks)
          4. VM accessible via SSH, shows correct OS version in
             ``/etc/*release``
          5. Host info command states 'built' in the status
          6. GRUB config changes the boot order (boot local first)
          7. Hosts boots straight to RHEL after reboot (step #4)


        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_provision_baremetal_with_uefi_secureboot(self):
        """Provision RHEL7+ on a new SecureBoot-enabled UEFI BM Host from
        provided MAC address

        :id: f5a0fe7b-0899-42df-81ad-be3143785303

        :setup:
          1. Create a PXE-based VM with UEFI boot mode from
             a secureboot image (outside of Satellite).
          2. Synchronize a RHEL7+ Kickstart repo
             (el6 kernel is too old for GRUB2)

        :steps:
          1. The loader files on TFTP are in the appropriate format and in the
             appropriate dirs.
          2. PXE handoff is successful (tcpdump shows the VM has requested
             the correct files)
          3. VM started to provision (might be tricky to automate console
             checks)
          4. VM accessible via SSH, shows correct OS version in
             ``/etc/*release``
          5. Host info command states 'built' in the status
          6. GRUB config changes the boot order (boot local first)
          7. Hosts boots straight to RHEL after reboot (step #4)

        :expectedresults: Host is provisioned

        :CaseAutomation: notautomated

        :CaseLevel: System
        """


@run_in_one_thread
class KatelloAgentTestCase(CLITestCase):
    """Host tests, which require VM with installed katello-agent."""

    org = None
    env = None
    content_view = None
    activation_key = None

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key

        """
        super(KatelloAgentTestCase, cls).setUpClass()
        # Create new org, environment, CV and activation key
        KatelloAgentTestCase.org = make_org()
        KatelloAgentTestCase.env = make_lifecycle_environment(
            {u'organization-id': KatelloAgentTestCase.org['id']}
        )
        KatelloAgentTestCase.content_view = make_content_view(
            {u'organization-id': KatelloAgentTestCase.org['id']}
        )
        KatelloAgentTestCase.activation_key = make_activation_key(
            {
                u'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
                u'organization-id': KatelloAgentTestCase.org['id'],
            }
        )
        # Add subscription to Satellite Tools repo to activation key
        setup_org_for_a_rh_repo(
            {
                u'product': PRDS['rhel'],
                u'repository-set': REPOSET['rhst7'],
                u'repository': REPOS['rhst7']['name'],
                u'organization-id': KatelloAgentTestCase.org['id'],
                u'content-view-id': KatelloAgentTestCase.content_view['id'],
                u'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
                u'activationkey-id': KatelloAgentTestCase.activation_key['id'],
            }
        )
        # Create custom repo, add subscription to activation key
        setup_org_for_a_custom_repo(
            {
                u'url': FAKE_1_YUM_REPO,
                u'organization-id': KatelloAgentTestCase.org['id'],
                u'content-view-id': KatelloAgentTestCase.content_view['id'],
                u'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
                u'activationkey-id': KatelloAgentTestCase.activation_key['id'],
            }
        )

    def setUp(self):
        """Create VM, subscribe it to satellite-tools repo, install katello-ca
        and katello-agent packages

        """
        super(KatelloAgentTestCase, self).setUp()
        # Create VM and register content host
        self.client = VirtualMachine(distro=DISTRO_RHEL7)
        self.client.create()
        self.addCleanup(vm_cleanup, self.client)
        self.client.install_katello_ca()
        # Register content host, install katello-agent
        self.client.register_contenthost(
            KatelloAgentTestCase.org['label'], KatelloAgentTestCase.activation_key['name']
        )
        self.assertTrue(self.client.subscribed)
        self.host = Host.info({'name': self.client.hostname})
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_agent()

    @tier3
    def test_positive_get_errata_info(self):
        """Get errata info

        :id: afb5ab34-1703-49dc-8ddc-5e032c1b86d7

        :expectedresults: Errata info was displayed


        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        result = Host.errata_info({u'host-id': self.host['id'], u'id': FAKE_1_ERRATA_ID})
        self.assertEqual(result[0]['errata-id'], FAKE_1_ERRATA_ID)
        self.assertIn(FAKE_2_CUSTOM_PACKAGE, result[0]['packages'])

    @tier3
    @upgrade
    def test_positive_apply_errata(self):
        """Apply errata to a host

        :id: 8d0e5c93-f9fd-4ec0-9a61-aa93082a30c5

        :expectedresults: Errata is scheduled for installation


        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        Host.errata_apply({u'errata-ids': FAKE_1_ERRATA_ID, u'host-id': self.host['id']})

    @pytest.mark.skip_if_open("BZ:1740790")
    @tier3
    def test_positive_apply_security_erratum(self):
        """Apply security erratum to a host

        :id: 4d1095c8-d354-42ac-af44-adf6dbb46deb

        :expectedresults: erratum is recognized by the
            `yum update --security` command on client

        :CaseLevel: System

        :BZ: 1420671, 1740790
        """
        self.client.download_install_rpm(FAKE_1_YUM_REPO, FAKE_2_CUSTOM_PACKAGE)
        # Check the system is up to date
        result = self.client.run('yum update --security | grep "No packages needed for security"')
        self.assertEqual(result.return_code, 0)
        before_downgrade = int(time.time())
        # Downgrade walrus package
        self.client.run('yum downgrade -y {0}'.format(FAKE_2_CUSTOM_PACKAGE_NAME))
        # Wait for errata applicability cache is counted
        wait_for_errata_applicability_task(int(self.host['id']), before_downgrade)
        # Check that host has applicable errata
        host_errata = Host.errata_list({u'host-id': self.host['id']})
        self.assertEqual(host_errata[0]['erratum-id'], FAKE_1_ERRATA_ID)
        self.assertEqual(host_errata[0]['installable'], 'true')
        # Check the erratum becomes available
        result = self.client.run(
            'yum update --assumeno --security ' '| grep "No packages needed for security"'
        )
        self.assertEqual(result.return_code, 1)

    @tier3
    @upgrade
    def test_positive_install_package(self):
        """Install a package to a host remotely

        :id: b1009bba-0c7e-4b00-8ac4-256e5cfe4a78

        :expectedresults: Package was successfully installed


        :CaseLevel: System
        """
        Host.package_install(
            {u'host-id': self.host['id'], u'packages': FAKE_0_CUSTOM_PACKAGE_NAME}
        )
        result = self.client.run('rpm -q {0}'.format(FAKE_0_CUSTOM_PACKAGE_NAME))
        self.assertEqual(result.return_code, 0)

    @tier3
    def test_positive_remove_package(self):
        """Remove a package from a host remotely

        :id: 573dec11-8f14-411f-9e41-84426b0f23b5

        :expectedresults: Package was successfully removed


        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        Host.package_remove({u'host-id': self.host['id'], u'packages': FAKE_1_CUSTOM_PACKAGE_NAME})
        result = self.client.run('rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE_NAME))
        self.assertNotEqual(result.return_code, 0)

    @tier3
    def test_positive_upgrade_package(self):
        """Upgrade a host package remotely

        :id: ad751c63-7175-40ae-8bc4-800462cd9c29

        :expectedresults: Package was successfully upgraded


        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        Host.package_upgrade(
            {u'host-id': self.host['id'], u'packages': FAKE_1_CUSTOM_PACKAGE_NAME}
        )
        result = self.client.run('rpm -q {0}'.format(FAKE_2_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)

    @tier3
    def test_positive_upgrade_packages_all(self):
        """Upgrade all the host packages remotely

        :id: 003101c7-bb95-4e51-a598-57977b2858a9

        :expectedresults: Packages (at least 1 with newer version available)
            were successfully upgraded

        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        Host.package_upgrade_all({'host-id': self.host['id']})
        result = self.client.run('rpm -q {0}'.format(FAKE_2_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)

    @tier3
    @upgrade
    def test_positive_install_and_remove_package_group(self):
        """Install and remove a package group to a host remotely

        :id: ded20a89-cfd9-48d5-8829-739b1a4d4042

        :expectedresults: Package group was successfully installed
            and removed

        :CaseLevel: System
        """
        hammer_args = {u'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME, u'host-id': self.host['id']}
        Host.package_group_install(hammer_args)
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.client.run('rpm -q {0}'.format(package))
            self.assertEqual(result.return_code, 0)
        Host.package_group_remove(hammer_args)
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.client.run('rpm -q {0}'.format(package))
            self.assertNotEqual(result.return_code, 0)

    @tier3
    def test_negative_unregister_and_pull_content(self):
        """Attempt to retrieve content after host has been unregistered from
        Satellite

        :id: de0d0d91-b1e1-4f0e-8a41-c27df4d6b6fd

        :expectedresults: Host can no longer retrieve content from satellite

        :CaseLevel: System
        """
        result = self.client.run('subscription-manager unregister')
        self.assertEqual(result.return_code, 0)
        result = self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        self.assertNotEqual(result.return_code, 0)

    @tier3
    @upgrade
    def test_positive_register_host_ak_with_host_collection(self):
        """Attempt to register a host using activation key with host collection

        :id: 7daf4e40-3fa6-42af-b3f7-1ca1a5c9bfeb

        :BZ: 1385814

        :expectedresults: Host successfully registered and listed in host
            collection

        :CaseLevel: System
        """
        # create a new activation key
        activation_key = make_activation_key(
            {
                u'lifecycle-environment-id': self.env['id'],
                u'organization-id': self.org['id'],
                u'content-view-id': self.content_view['id'],
            }
        )
        hc = make_host_collection({u'organization-id': self.org['id']})
        ActivationKey.add_host_collection(
            {
                'id': activation_key['id'],
                'organization-id': self.org['id'],
                'host-collection-id': hc['id'],
            }
        )
        # add the registered instance host to collection
        HostCollection.add_host(
            {'id': hc['id'], 'organization-id': self.org['id'], 'host-ids': self.host['id']}
        )
        with VirtualMachine() as client:
            client.create()
            client.install_katello_ca()
            # register the client host with the current activation key
            client.register_contenthost(self.org['name'], activation_key=activation_key['name'])
            self.assertTrue(client.subscribed)
            # note: when registering the host, it should be automatically added
            # to the host collection
            client_host = Host.info({'name': client.hostname})
            hosts = HostCollection.hosts({'id': hc['id'], 'organization-id': self.org['id']})
            self.assertEqual(len(hosts), 2)
            expected_hosts_ids = {self.host['id'], client_host['id']}
            hosts_ids = {host['id'] for host in hosts}
            self.assertEqual(hosts_ids, expected_hosts_ids)


@run_in_one_thread
class KatelloHostToolsTestCase(CLITestCase):
    """Host tests, which require VM with installed katello-host-tools."""

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key"""
        super(KatelloHostToolsTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.env = make_lifecycle_environment({u'organization-id': cls.org['id']})
        cls.content_view = make_content_view({u'organization-id': cls.org['id']})
        cls.activation_key = make_activation_key(
            {u'lifecycle-environment-id': cls.env['id'], u'organization-id': cls.org['id']}
        )
        # setup rh satellite tools repository content
        setup_org_for_a_rh_repo(
            {
                u'product': PRDS['rhel'],
                u'repository-set': REPOSET['rhst7'],
                u'repository': REPOS['rhst7']['name'],
                u'organization-id': cls.org['id'],
                u'content-view-id': cls.content_view['id'],
                u'lifecycle-environment-id': cls.env['id'],
                u'activationkey-id': cls.activation_key['id'],
            }
        )
        # Create custom repository content
        setup_org_for_a_custom_repo(
            {
                u'url': FAKE_6_YUM_REPO,
                u'organization-id': cls.org['id'],
                u'content-view-id': cls.content_view['id'],
                u'lifecycle-environment-id': cls.env['id'],
                u'activationkey-id': cls.activation_key['id'],
            }
        )

    def setUp(self):
        """Create VM, install katello-ca package, subscribe vm host, enable
        satellite-tools repository, and install katello-host-tools package
        """
        super(KatelloHostToolsTestCase, self).setUp()
        # Create VM and register content host
        self.client = VirtualMachine()
        self.client.create()
        self.addCleanup(vm_cleanup, self.client)
        self.client.install_katello_ca()
        # Register content host and install katello-host-tools
        self.client.register_contenthost(self.org['label'], self.activation_key['name'])
        self.assertTrue(self.client.subscribed)
        self.host_info = Host.info({'name': self.client.hostname})
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_host_tools()

    @tier3
    def test_positive_report_package_installed_removed(self):
        """Ensure installed/removed package is reported to satellite

        :id: fa5dc238-74c3-4c8a-aa6f-e0a91ba543e3

        :customerscenario: true

        :steps:
            1. register a host to activation key with content view that contain
               packages
            2. install a package 1 from the available packages
            3. list the host installed packages with search for package 1 name
            4. remove the package 1
            5. list the host installed packages with search for package 1 name

        :expectedresults:
            1. after step3: package 1 is listed in installed packages
            2. after step5: installed packages list is empty

        :BZ: 1463809

        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_0_CUSTOM_PACKAGE))
        result = self.client.run('rpm -q {0}'.format(FAKE_0_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        installed_packages = Host.package_list(
            {
                'host-id': self.host_info['id'],
                'search': 'name={0}'.format(FAKE_0_CUSTOM_PACKAGE_NAME),
            }
        )
        self.assertEqual(len(installed_packages), 1)
        self.assertEqual(installed_packages[0]['nvra'], FAKE_0_CUSTOM_PACKAGE)
        result = self.client.run('yum remove -y {0}'.format(FAKE_0_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        installed_packages = Host.package_list(
            {
                'host-id': self.host_info['id'],
                'search': 'name={0}'.format(FAKE_0_CUSTOM_PACKAGE_NAME),
            }
        )
        self.assertEqual(len(installed_packages), 0)

    @tier3
    def test_positive_package_applicability(self):
        """Ensure packages applicability is functioning properly

        :id: d283b65b-19c1-4eba-87ea-f929b0ee4116

        :customerscenario: true

        :steps:
            1. register a host to activation key with content view that contain
               a minimum of 2 packages, package 1 and package 2,
               where package 2 is an upgrade/update of package 1
            2. install the package 1
            3. list the host applicable packages for package 1 name
            4. install the package 2
            5. list the host applicable packages for package 1 name

        :expectedresults:
            1. after step 3: package 2 is listed in applicable packages
            2. after step 5: applicable packages list is empty

        :BZ: 1463809

        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        result = self.client.run('rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        applicable_packages = Package.list(
            {
                'host-id': self.host_info['id'],
                'packages-restrict-applicable': 'true',
                'search': 'name={0}'.format(FAKE_1_CUSTOM_PACKAGE_NAME),
            }
        )
        self.assertEqual(len(applicable_packages), 1)
        self.assertIn(FAKE_2_CUSTOM_PACKAGE, applicable_packages[0]['filename'])
        # install package update
        self.client.run('yum install -y {0}'.format(FAKE_2_CUSTOM_PACKAGE))
        result = self.client.run('rpm -q {0}'.format(FAKE_2_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        applicable_packages = Package.list(
            {
                'host-id': self.host_info['id'],
                'packages-restrict-applicable': 'true',
                'search': 'name={0}'.format(FAKE_1_CUSTOM_PACKAGE_NAME),
            }
        )
        self.assertEqual(len(applicable_packages), 0)

    @pytest.mark.skip_if_open("BZ:1740790")
    @tier3
    def test_positive_erratum_applicability(self):
        """Ensure erratum applicability is functioning properly

        :id: 139de508-916e-4c91-88ad-b4973a6fa104

        :customerscenario: true

        :steps:
            1. register a host to activation key with content view that contain
               a package with errata
            2. install the package
            3. list the host applicable errata
            4. install the errata
            5. list the host applicable errata

        :expectedresults:
            1. after step 3: errata of package is in applicable errata list
            2. after step 5: errata of package is not in applicable errata list

        :BZ: 1463809,1740790

        :CaseLevel: System
        """
        before_install = int(time.time())
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        result = self.client.run('rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        wait_for_errata_applicability_task(int(self.host_info['id']), before_install)
        applicable_erratum = Host.errata_list({'host-id': self.host_info['id']})
        applicable_erratum_ids = [
            errata['erratum-id']
            for errata in applicable_erratum
            if errata['installable'] == 'true'
        ]
        self.assertIn(FAKE_2_ERRATA_ID, applicable_erratum_ids)
        before_upgrade = int(time.time())
        # apply errata
        result = self.client.run('yum update -y --advisory {0}'.format(FAKE_2_ERRATA_ID))
        self.assertEqual(result.return_code, 0)
        wait_for_errata_applicability_task(int(self.host_info['id']), before_upgrade)
        applicable_erratum = Host.errata_list({'host-id': self.host_info['id']})
        applicable_erratum_ids = [
            errata['erratum-id']
            for errata in applicable_erratum
            if errata['installable'] == 'true'
        ]
        self.assertNotIn(FAKE_2_ERRATA_ID, applicable_erratum_ids)

    @tier3
    def test_negative_install_package(self):
        """Attempt to install a package to a host remotely

        :id: 751c05b4-d7a3-48a2-8860-f0d15fdce204

        :expectedresults: Package was not installed

        :CaseLevel: System
        """
        with self.assertRaises(CLIReturnCodeError) as context:
            Host.package_install(
                {u'host-id': self.host_info['id'], u'packages': FAKE_1_CUSTOM_PACKAGE}
            )
        self.assertIn(
            (
                'The task has been cancelled. Is katello-agent installed and '
                'goferd running on the Host?'
            ),
            str(context.exception),
        )


@run_in_one_thread
class HostSubscriptionTestCase(CLITestCase):
    """Tests for host subscription sub command"""

    org = None
    env = None
    hosts_env = None
    content_view = None
    activation_key = None

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key

        :BZ: 1444886
        """
        super(HostSubscriptionTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.env = make_lifecycle_environment({u'organization-id': cls.org['id']})
        cls.content_view = make_content_view({u'organization-id': cls.org['id']})
        cls.activation_key = make_activation_key(
            {u'lifecycle-environment-id': cls.env['id'], u'organization-id': cls.org['id']}
        )

        cls.subscription_name = SATELLITE_SUBSCRIPTION_NAME
        # create a rh capsule content
        setup_org_for_a_rh_repo(
            {
                u'product': PRDS['rhsc'],
                u'repository-set': REPOSET['rhsc7'],
                u'repository': REPOS['rhsc7']['name'],
                u'organization-id': cls.org['id'],
                u'content-view-id': cls.content_view['id'],
                u'lifecycle-environment-id': cls.env['id'],
                u'activationkey-id': cls.activation_key['id'],
                u'subscription': cls.subscription_name,
            },
            force_use_cdn=True,
        )
        org_subscriptions = Subscription.list({'organization-id': cls.org['id']})
        cls.default_subscription_id = None
        cls.repository_id = REPOS['rhsc7']['id']
        for org_subscription in org_subscriptions:
            if org_subscription['name'] == cls.subscription_name:
                cls.default_subscription_id = org_subscription['id']
                break
        # create a new lce for hosts subscription
        cls.hosts_env = make_lifecycle_environment({u'organization-id': cls.org['id']})
        # refresh content view data
        cls.content_view = ContentView.info({'id': cls.content_view['id']})
        content_view_version = cls.content_view['versions'][-1]
        ContentView.version_promote(
            {
                u'id': content_view_version['id'],
                u'organization-id': cls.org['id'],
                u'to-lifecycle-environment-id': cls.hosts_env['id'],
            }
        )

    def setUp(self):
        """Create  a virtual machine without registration"""
        super(HostSubscriptionTestCase, self).setUp()
        self.client = VirtualMachine(distro=DISTRO_RHEL7)
        self.client.create()
        self.addCleanup(vm_cleanup, self.client)
        self.client.install_katello_ca()

    def _register_client(
        self,
        activation_key=None,
        lce=False,
        enable_repo=False,
        auto_attach=False,
        attach_to_default=False,
    ):
        """Register the client as a content host consumer

        :param activation_key: activation key if registration with activation
            key
        :param lce: boolean to indicate whether the registration should be made
            by environment
        :param enable_repo: boolean to indicate whether to enable repository
        :param auto_attach: boolean to indicate whether to register with
            auto-attach option, in case of registration with activation key a
            command is launched
        :param attach_to_default: boolean to indicate whether to attach to
            plain RHEL subsctiption
        :return: the registration result
        """
        assert (
            not auto_attach or not attach_to_default
        ), 'Only one of auto_attach or attach_to_default must be set'

        if activation_key is None:
            activation_key = self.activation_key

        if lce:
            result = self.client.register_contenthost(
                self.org['name'],
                lce='{0}/{1}'.format(self.hosts_env['name'], self.content_view['name']),
                auto_attach=auto_attach,
            )
        else:
            result = self.client.register_contenthost(
                self.org['name'], activation_key=activation_key['name']
            )
            if auto_attach and self.client.subscribed:
                result = self.client.run('subscription-manager attach --auto')

        if attach_to_default:
            result = self.client.run(
                'subscription-manager list --available --matches "%s" --pool-only'
                % DEFAULT_SUBSCRIPTION_NAME
            )
            pool_id = result.stdout[0]
            result = self.client.run('subscription-manager attach --pool "%s"' % pool_id)

        if self.client.subscribed and enable_repo:
            self.client.enable_repo(self.repository_id)

        return result

    def _client_enable_repo(self):
        """Enable the client default repository"""
        result = self.client.run(
            'subscription-manager repos --enable {0}'.format(self.repository_id)
        )
        return result

    def _make_activation_key(self, add_subscription=False):
        """Create a new activation key

        :param add_subscription: boolean to indicate whether to add the default
            subscription to the created activation key
        :return: the created activation key
        """
        activation_key = make_activation_key(
            {
                'organization-id': self.org['id'],
                'content-view-id': self.content_view['id'],
                'lifecycle-environment-id': self.hosts_env['id'],
            }
        )
        ActivationKey.update(
            {'organization-id': self.org['id'], 'id': activation_key['id'], 'auto-attach': 0}
        )
        if add_subscription:
            ActivationKey.add_subscription(
                {
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'subscription-id': self.default_subscription_id,
                }
            )
        return activation_key

    def _host_subscription_register(self):
        """Register the subscription of client as a content host consumer"""
        Host.subscription_register(
            {
                u'organization-id': self.org['id'],
                u'content-view-id': self.content_view['id'],
                u'lifecycle-environment-id': self.hosts_env['id'],
                u'name': self.client.hostname,
            }
        )

    @tier3
    def test_positive_register(self):
        """Attempt to register a host

        :id: b1c601ee-4def-42ce-b353-fc2657237533

        :expectedresults: host successfully registered

        :CaseLevel: System
        """
        activation_key = self._make_activation_key(add_subscription=False)
        hosts = Host.list({'organization-id': self.org['id'], 'search': self.client.hostname})
        self.assertEqual(len(hosts), 0)
        self._host_subscription_register()
        hosts = Host.list({'organization-id': self.org['id'], 'search': self.client.hostname})
        self.assertGreater(len(hosts), 0)
        host = Host.info({'id': hosts[0]['id']})
        self.assertEqual(host['name'], self.client.hostname)
        # note: when not registered the following command lead to exception,
        # see unregister
        host_subscriptions = ActivationKey.subscriptions(
            {'organization-id': self.org['id'], 'id': activation_key['id'], 'host-id': host['id']},
            output_format='json',
        )
        self.assertEqual(len(host_subscriptions), 0)

    @tier3
    def test_positive_attach(self):
        """Attempt to attach a subscription to host

        :id: d5825bfb-59e3-4d49-8df8-902cc7a9d66b

        :BZ: 1199515

        :expectedresults: host successfully subscribed, subscription repository
            enabled, and repository package installed

        :CaseLevel: System
        """
        # create an activation key without subscriptions
        activation_key = self._make_activation_key(add_subscription=False)
        # register the client host
        self._host_subscription_register()
        host = Host.info({'name': self.client.hostname})
        self._register_client(activation_key=activation_key)
        self.assertTrue(self.client.subscribed)
        # attach the subscription to host
        Host.subscription_attach(
            {'host-id': host['id'], 'subscription-id': self.default_subscription_id}
        )
        result = self._client_enable_repo()
        self.assertEqual(result.return_code, 0)
        # ensure that katello agent can be installed
        with self.assertNotRaises(VirtualMachineError):
            self.client.install_katello_agent()

    @tier3
    def test_positive_attach_with_lce(self):
        """Attempt to attach a subscription to host, registered by lce

        :id: a362b959-9dde-4d1b-ae62-136c6ef943ba

        :BZ: 1199515

        :expectedresults: host successfully subscribed, subscription
            repository enabled, and repository package installed

        :CaseLevel: System
        """
        self._register_client(lce=True, auto_attach=True)
        self.assertTrue(self.client.subscribed)
        host = Host.info({'name': self.client.hostname})
        Host.subscription_attach(
            {'host-id': host['id'], 'subscription-id': self.default_subscription_id}
        )
        result = self._client_enable_repo()
        self.assertEqual(result.return_code, 0)
        # ensure that katello agent can be installed
        with self.assertNotRaises(VirtualMachineError):
            self.client.install_katello_agent()

    @tier3
    def test_negative_without_attach(self):
        """ Register content host from satellite, register client to uuid
        of that content host, as there was no attach on the client,
        Test if the list of the repository subscriptions is empty

        :id: 54a2c95f-be08-4353-a96c-4bc4d96ad03d

        :expectedresults: repository list is empty

        :CaseLevel: System
        """
        self._host_subscription_register()
        host = Host.info({'name': self.client.hostname})
        self.client.register_contenthost(
            self.org['name'], consumerid=host['subscription-information']['uuid'], force=False,
        )
        client_status = self.client.subscription_manager_status()
        self.assertIn(SM_OVERALL_STATUS['current'], client_status.stdout)
        repo_list = self.client.subscription_manager_list_repos()
        self.assertIn(NO_REPOS_AVAILABLE, repo_list.stdout)

    @tier3
    def test_negative_without_attach_with_lce(self):
        """Attempt to enable a repository of a subscription that was not
        attached to a host

        :id: fc469e70-a7cb-4fca-b0ea-3c9e3dfff849

        :expectedresults: repository not enabled on host

        :CaseLevel: System
        """
        self._register_client(lce=True, attach_to_default=True)
        self.assertTrue(self.client.subscribed)
        result = self._client_enable_repo()
        self.assertNotEqual(result.return_code, 0)

    @tier3
    @upgrade
    def test_positive_remove(self):
        """Attempt to remove a subscription from content host

        :id: 3833c349-1f5b-41ac-bbac-2c1f33232d76

        :expectedresults: subscription successfully removed from host

        :CaseLevel: System
        """
        activation_key = self._make_activation_key(add_subscription=True)
        self._host_subscription_register()
        host = Host.info({'name': self.client.hostname})
        host_subscriptions = ActivationKey.subscriptions(
            {'organization-id': self.org['id'], 'id': activation_key['id'], 'host-id': host['id']},
            output_format='json',
        )
        self.assertNotIn(self.subscription_name, [sub['name'] for sub in host_subscriptions])
        self._register_client(activation_key=activation_key)
        Host.subscription_attach(
            {'host-id': host['id'], 'subscription-id': self.default_subscription_id}
        )
        host_subscriptions = ActivationKey.subscriptions(
            {'organization-id': self.org['id'], 'id': activation_key['id'], 'host-id': host['id']},
            output_format='json',
        )
        self.assertIn(self.subscription_name, [sub['name'] for sub in host_subscriptions])
        Host.subscription_remove(
            {'host-id': host['id'], 'subscription-id': self.default_subscription_id}
        )
        host_subscriptions = ActivationKey.subscriptions(
            {'organization-id': self.org['id'], 'id': activation_key['id'], 'host-id': host['id']},
            output_format='json',
        )
        self.assertNotIn(self.subscription_name, [sub['name'] for sub in host_subscriptions])

    @tier3
    def test_positive_auto_attach(self):
        """Attempt to auto attach a subscription to content host

        :id: e3eebf72-d512-4892-828b-70165ea4b129

        :expectedresults: host successfully subscribed, subscription
            repository enabled, and repository package installed

        :CaseLevel: System
        """
        activation_key = self._make_activation_key(add_subscription=True)
        self._host_subscription_register()
        host = Host.info({'name': self.client.hostname})
        self._register_client(activation_key=activation_key)
        Host.subscription_auto_attach({'host-id': host['id']})
        result = self._client_enable_repo()
        self.assertEqual(result.return_code, 0)
        # ensure that katello agent can be installed
        with self.assertNotRaises(VirtualMachineError):
            self.client.install_katello_agent()

    @tier3
    def test_positive_unregister(self):
        """Attempt to unregister host subscription

        :id: 608f5b6d-4688-478e-8be8-e946771d5247

        :expectedresults: host subscription is unregistered

        :CaseLevel: System
        """
        # register the host client
        activation_key = self._make_activation_key(add_subscription=True)
        self._register_client(activation_key=activation_key, enable_repo=True, auto_attach=True)
        self.assertTrue(self.client.subscribed)
        host = Host.info({'name': self.client.hostname})
        host_subscriptions = ActivationKey.subscriptions(
            {'organization-id': self.org['id'], 'id': activation_key['id'], 'host-id': host['id']},
            output_format='json',
        )
        self.assertGreater(len(host_subscriptions), 0)
        Host.subscription_unregister({'host': self.client.hostname})
        with self.assertRaises(CLIReturnCodeError):
            # raise error that the host was not registered by
            # subscription-manager register
            ActivationKey.subscriptions(
                {
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'host-id': host['id'],
                }
            )

    @tier3
    def test_syspurpose_end_to_end(self):
        """Create a host with system purpose values set by activation key.

        :id: b88e9b6c-2348-49ce-b5e9-a2b9f0abed3f

        :expectedresults: host is registered and system purpose values are correct.

        :CaseLevel: System
        """
        # Create an activation key with test values
        activation_key = make_activation_key(
            {
                u'purpose-addons': "test-addon1, test-addon2",
                u'purpose-role': "test-role",
                u'purpose-usage': "test-usage",
                u'service-level': "Self-Support",
                u'lifecycle-environment-id': self.env['id'],
                u'organization-id': self.org['id'],
                u'content-view-id': self.content_view['id'],
            }
        )
        # Register a host using the activation key
        self._register_client(activation_key=activation_key, enable_repo=True, auto_attach=True)
        self.assertTrue(self.client.subscribed)
        host = Host.info({'name': self.client.hostname})
        # Assert system purpose values are set in the host as expected
        self.assertCountEqual(
            host['subscription-information']['system-purpose']['purpose-addons'],
            "test-addon1, test-addon2",
        )
        self.assertEqual(
            host['subscription-information']['system-purpose']['purpose-role'], "test-role"
        )
        self.assertEqual(
            host['subscription-information']['system-purpose']['purpose-usage'], "test-usage"
        )
        self.assertEqual(
            host['subscription-information']['system-purpose']['service-level'], "Self-Support"
        )
        # Change system purpose values in the host
        Host.update(
            {
                u'purpose-addons': "test-addon3",
                u'purpose-role': "test-role2",
                u'purpose-usage': "test-usage2",
                u'service-level': "Self-Support2",
                u'id': host['id'],
            }
        )
        host = Host.info({'id': host['id']})
        # Assert system purpose values have been updated in the host as expected
        self.assertEqual(
            host['subscription-information']['system-purpose']['purpose-addons'], "test-addon3"
        )
        self.assertEqual(
            host['subscription-information']['system-purpose']['purpose-role'], "test-role2"
        )
        self.assertEqual(
            host['subscription-information']['system-purpose']['purpose-usage'], "test-usage2"
        )
        self.assertEqual(
            host['subscription-information']['system-purpose']['service-level'], "Self-Support2"
        )
        # Assert subscriptions present
        host_subscriptions = ActivationKey.subscriptions(
            {'organization-id': self.org['id'], 'id': activation_key['id'], 'host-id': host['id']},
            output_format='json',
        )
        self.assertGreater(len(host_subscriptions), 0)
        self.assertEqual(self.subscription_name, host_subscriptions[0]['name'])
        # Unregister host
        Host.subscription_unregister({'host': self.client.hostname})
        with self.assertRaises(CLIReturnCodeError):
            # raise error that the host was not registered by
            # subscription-manager register
            ActivationKey.subscriptions(
                {
                    'organization-id': self.org['id'],
                    'id': activation_key['id'],
                    'host-id': host['id'],
                }
            )


class HostErrataTestCase(CLITestCase):
    """Tests for errata's host sub command"""

    @tier1
    def test_positive_errata_list_of_sat_server(self):
        """Check if errata list doesn't raise exception. Check BZ for details.

        :id: 6b22f0c0-9c4b-11e6-ab93-68f72889dc7f

        :expectedresults: Satellite host errata list not failing

        :BZ: 1351040

        :CaseImportance: Critical
        """
        hostname = ssh.command('hostname').stdout[0]
        host = Host.info({'name': hostname})
        self.assertIsInstance(Host.errata_list({'host-id': host['id']}), list)


class EncDumpTestCase(CLITestCase):
    """Tests for Dump host's ENC YAML"""

    @tier1
    def test_positive_dump_enc_yaml(self):
        """Dump host's ENC YAML. Check BZ for details.

        :id: 50bf2530-788c-4710-a382-d034d73d5d4d

        :expectedresults: Ensure that enc-dump does not fail

        :customerscenario: true

        :BZ: 1372731

        :CaseImportance: Critical
        """
        hostname = ssh.command('hostname').stdout[0]
        self.assertIsInstance(Host.enc_dump({'name': hostname}), list)
