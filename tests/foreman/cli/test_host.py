"""CLI tests for ``hammer host``.

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

from fauxfactory import gen_integer, gen_ipaddr, gen_mac, gen_string
from nailgun import entities
import yaml

from robottelo import ssh
from robottelo.cleanup import capsule_cleanup, vm_cleanup
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIBaseError, CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.environment import Environment
from robottelo.cli.factory import (
    add_role_permissions,
    CLIFactoryError,
    make_activation_key,
    make_architecture,
    make_content_view,
    make_domain,
    make_environment,
    make_fake_host,
    make_host,
    make_host_collection,
    make_hostgroup,
    make_lifecycle_environment,
    make_medium,
    make_org,
    make_os,
    make_proxy,
    make_role,
    make_smart_variable,
    make_user,
    publish_puppet_module,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.host import Host, HostInterface
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.medium import Medium
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.org import Org
from robottelo.cli.package import Package
from robottelo.cli.proxy import Proxy
from robottelo.cli.puppet import Puppet
from robottelo.cli.scparams import SmartClassParameter
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import (
    CUSTOM_PUPPET_REPO,
    DEFAULT_CV,
    DISTRO_RHEL7,
    ENVIRONMENT,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_GROUP,
    FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE_NAME,
    FAKE_1_ERRATA_ID,
    FAKE_1_YUM_REPO,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
    SATELLITE_SUBSCRIPTION_NAME,
)
from robottelo.datafactory import (
    invalid_values_list,
    valid_data_list,
    valid_hosts_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade,
)
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine, VirtualMachineError


class HostCreateTestCase(CLITestCase):
    """Tests for creating the hosts via CLI."""

    @classmethod
    def setUpClass(cls):
        """Create organization, lifecycle environment, content view, publish
        and promote new version to re-use in tests.
        """
        super(HostCreateTestCase, cls).setUpClass()
        cls.new_org = make_org()
        cls.new_lce = make_lifecycle_environment({
            'organization-id': cls.new_org['id']})
        cls.LIBRARY = LifecycleEnvironment.info({
            'organization-id': cls.new_org['id'],
            'name': ENVIRONMENT,
        })
        cls.DEFAULT_CV = ContentView.info({
            'organization-id': cls.new_org['id'],
            'name': DEFAULT_CV,
        })
        cls.new_cv = make_content_view({'organization-id': cls.new_org['id']})
        ContentView.publish({'id': cls.new_cv['id']})
        version_id = ContentView.version_list({
            'content-view-id': cls.new_cv['id'],
        })[0]['id']
        ContentView.version_promote({
            'id': version_id,
            'to-lifecycle-environment-id': cls.new_lce['id'],
            'organization-id': cls.new_org['id'],
        })
        cls.promoted_cv = cls.new_cv
        # Setup for puppet class related tests
        puppet_modules = [
            {'author': 'robottelo', 'name': 'generic_1'},
        ]
        cls.puppet_cv = publish_puppet_module(
            puppet_modules, CUSTOM_PUPPET_REPO, cls.new_org['id'])
        cls.puppet_env = Environment.list({
            'search': u'content_view="{0}"'.format(cls.puppet_cv['name'])})[0]
        cls.puppet_class = Puppet.info({
            'name': puppet_modules[0]['name'],
            'environment': cls.puppet_env['name'],
        })
        # adding org to a puppet env
        Org.set_parameter({
            'name': 'Environment',
            'value': cls.puppet_env["name"],
            'organization': cls.new_org["name"],
        })

    def setUp(self):
        """Find an existing puppet proxy.

        Record information about this puppet proxy as ``self.puppet_proxy``.
        """
        super(HostCreateTestCase, self).setUp()
        # Use the default installation smart proxy
        self.puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]

    @tier1
    def test_positive_create_with_name(self):
        """A host can be created with a random name

        :id: 2e8dd25d-47ed-4131-bba6-1ff024808d05

        :expectedresults: A host is created and the name matches

        :CaseImportance: Critical
        """
        for name in valid_hosts_list():
            with self.subTest(name):
                host = entities.Host()
                host.create_missing()
                result = make_host({
                    u'architecture-id': host.architecture.id,
                    u'domain-id': host.domain.id,
                    u'environment-id': host.environment.id,
                    u'location-id': host.location.id,
                    u'mac': host.mac,
                    u'medium-id': host.medium.id,
                    u'name': name,
                    u'operatingsystem-id': host.operatingsystem.id,
                    u'organization-id': host.organization.id,
                    u'partition-table-id': host.ptable.id,
                    u'puppet-proxy-id': self.puppet_proxy['id'],
                    u'root-password': host.root_pass,
                })
                self.assertEqual(
                    '{0}.{1}'.format(name, host.domain.read().name),
                    result['name'],
                )

    @tier1
    def test_positive_add_interface_by_id(self):
        """New network interface can be added to existing host

        :id: e97dba92-61eb-47ad-a7d7-5f989292b12a

        :expectedresults: Interface added to host correctly and has proper
            domain and mac address

        :CaseImportance: Critical
        """
        domain = make_domain({
            u'organizations': u'Default Organization',
            u'locations': u'Default Location'
        })
        mac = gen_mac(multicast=False)
        host = make_fake_host({
            u'domain-id': domain['id'],
        })
        HostInterface.create({
            u'host-id': host['id'],
            u'domain-id': domain['id'],
            u'mac': mac,
            u'type': u'interface'
        })
        host = Host.info({u'id': host['id']})
        host_interface = HostInterface.info({
            u'host-id': host['id'],
            u'id': [ni for ni in host['network-interfaces']
                    if ni['mac-address'] == mac][0]['id']
        })
        self.assertEqual(host_interface['domain'], domain['name'])
        self.assertEqual(host_interface['mac-address'], mac)

    @tier2
    @upgrade
    def test_positive_create_with_interface_by_id(self):
        """A host with defined interface can be created. Use domain id as one
        of the interface keys

        :id: 5455632c-ec87-4b45-ad88-cc8b4b1167c2

        :expectedresults: A host is created and has proper name. Assigned
            interface has correct domain name

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        name = gen_string('alpha').lower()
        hostgroup = make_hostgroup({
            'content-view-id': self.new_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-ids': self.new_org['id'],
        })
        host = entities.Host(
            organization=entities.Organization(id=self.new_org['id']).read()
            )
        host.create_missing()
        interface = (
            "type=interface,mac={0},identifier=eth0,name={1},domain_id={2},"
            "ip={3},primary=true,provision=true"
        ).format(host.mac, gen_string('alpha'), host.domain.id, gen_ipaddr())
        result = make_host({
            u'architecture-id': host.architecture.id,
            u'hostgroup-id': hostgroup['id'],
            u'location-id': host.location.id,
            u'medium-id': host.medium.id,
            u'name': name,
            u'operatingsystem-id': host.operatingsystem.id,
            u'organization-id': host.organization.id,
            u'partition-table-id': host.ptable.id,
            u'root-password': host.root_pass,
            u'interface': interface,
        })
        self.assertEqual(
            '{0}.{1}'.format(name, host.domain.read().name),
            result['name'],
        )
        host_interface = HostInterface.info({
            u'host-id': result['id'],
            u'id': result['network-interfaces'][0]['id']
        })
        self.assertEqual(host_interface['domain'], host.domain.read().name)

    @tier2
    def test_positive_create_with_interface_by_name(self):
        """A host with defined interface can be created. Use domain name as one
        of the interface keys

        :id: 6185f8d7-fdb5-4749-ad82-91ff471f91b8

        :expectedresults: A host is created and has proper name. Assigned
            interface has correct domain name

        :BZ: 1384497

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        name = gen_string('alpha').lower()
        hostgroup = make_hostgroup({
            'content-view-id': self.new_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-ids': self.new_org['id'],
        })
        host = entities.Host(
            organization=entities.Organization(id=self.new_org['id']).read()
        )
        host.create_missing()
        interface = (
            "type=interface,mac={0},identifier=eth0,name={1},domain={2},"
            "ip={3},primary=true,provision=true"
        ).format(host.mac, gen_string('alpha'), host.domain.name, gen_ipaddr())
        result = make_host({
            u'architecture-id': host.architecture.id,
            u'hostgroup-id': hostgroup['id'],
            u'location-id': host.location.id,
            u'medium-id': host.medium.id,
            u'name': name,
            u'operatingsystem-id': host.operatingsystem.id,
            u'organization-id': host.organization.id,
            u'partition-table-id': host.ptable.id,
            u'root-password': host.root_pass,
            u'interface': interface,
        })
        self.assertEqual(
            '{0}.{1}'.format(name, host.domain.read().name),
            result['name'],
        )
        host_interface = HostInterface.info({
            u'host-id': result['id'],
            u'id': result['network-interfaces'][0]['id']
        })
        self.assertEqual(host_interface['domain'], host.domain.read().name)

    @tier1
    def test_positive_create_with_org_name(self):
        """Check if host can be created with organization name

        :id: c08b0dac-9820-4261-bb0b-8a78f5c78a74

        :expectedresults: Host is created using organization name

        :CaseImportance: Critical
        """
        new_host = make_fake_host({
            'content-view-id': self.DEFAULT_CV['id'],
            'lifecycle-environment-id': self.LIBRARY['id'],
            'organization': self.new_org['name'],
        })
        self.assertEqual(new_host['organization'], self.new_org['name'])

    @skip_if_bug_open('bugzilla', 1483252)
    @tier1
    def test_positive_create_with_content_source(self):
        """Create a host with content source specified

        :id: 6068bd4d-18d8-47a2-99f4-3e0ee9208104

        :customerscenario: true

        :BZ: 1260697, 1483252, 1313056

        :expectedresults: A host is created with expected content source
            assigned

        :CaseImportance: High
        """
        content_source = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        host = make_fake_host({
            'content-source-id': content_source['id'],
            'content-view-id': self.DEFAULT_CV['id'],
            'lifecycle-environment-id': self.LIBRARY['id'],
            'organization': self.new_org['name'],
        })
        self.assertEqual(host['content-information']['content-source']['name'],
                         content_source['name'])

    @tier1
    def test_negative_create_with_content_source(self):
        """Attempt to create a host with invalid content source specified

        :id: d92d6aff-4ad3-467c-88a8-5a5e56614f58

        :BZ: 1260697

        :expectedresults: Host was not created

        :CaseImportance: Medium
        """
        with self.assertRaises(CLIFactoryError):
            make_fake_host({
                'content-source-id': gen_integer(10000, 99999),
                'content-view-id': self.DEFAULT_CV['id'],
                'lifecycle-environment-id': self.LIBRARY['id'],
                'organization': self.new_org['name'],
            })

    @run_in_one_thread
    @skip_if_bug_open('bugzilla', 1483252)
    @skip_if_bug_open('bugzilla', 1488465)
    @tier1
    def test_positive_update_content_source(self):
        """Update host's content source

        :id: 2364dbb7-2ccd-46c0-baf1-5e179a157027

        :customerscenario: true

        :BZ: 1260697, 1483252, 1488465

        :expectedresults: Content source was successfully updated

        :CaseImportance: High
        """
        content_source = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        host = make_fake_host({
            'content-source-id': content_source['id'],
            'content-view-id': self.DEFAULT_CV['id'],
            'lifecycle-environment-id': self.LIBRARY['id'],
            'organization': self.new_org['name'],
        })
        new_content_source = make_proxy()
        self.addCleanup(capsule_cleanup, new_content_source['id'])
        self.addCleanup(Host.delete, {'id': host['id']})
        Host.update({
            'id': host['id'],
            'content-source-id': new_content_source['id'],
        })
        host = Host.info({'id': host['id']})
        self.assertEqual(host['content-information']['content-source']['name'],
                         new_content_source['name'])

    @skip_if_bug_open('bugzilla', 1483252)
    @tier1
    def test_negative_update_content_source(self):
        """Attempt to update host's content source with invalid value

        :id: 03243c56-3835-4b15-94df-15d436bbda87

        :BZ: 1260697, 1483252, 1313056

        :expectedresults: Host was not updated. Content source remains the same
            as it was before update

        :CaseImportance: Medium
        """
        content_source = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        host = make_fake_host({
            'content-source-id': content_source['id'],
            'content-view-id': self.DEFAULT_CV['id'],
            'lifecycle-environment-id': self.LIBRARY['id'],
            'organization': self.new_org['name'],
        })
        with self.assertRaises(CLIBaseError):
            Host.update({
                'id': host['id'],
                'content-source-id': gen_integer(10000, 99999),
            })
        host = Host.info({'id': host['id']})
        self.assertEqual(host['content-information']['content-source']['name'],
                         content_source['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_cv_default(self):
        """Check if host can be created with default content view ('Default
        Organization View')

        :id: bb69a70e-17f9-4639-802d-90e6a4520afa

        :expectedresults: Host is created, default content view is associated

        :BZ: 1313056

        :CaseImportance: Critical
        """
        new_host = make_fake_host({
            'content-view-id': self.DEFAULT_CV['id'],
            'lifecycle-environment-id': self.LIBRARY['id'],
            'organization-id': self.new_org['id'],
        })
        self.assertEqual(
            new_host['content-information']['content-view']['name'],
            self.DEFAULT_CV['name'],
        )

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_lce_library(self):
        """Check if host can be created with default lifecycle environment
        ('Library')

        :id: 0093be1c-3664-448e-87f5-758bab34958a

        :expectedresults: Host is created, default lifecycle environment is
            associated

        :BZ: 1313056

        :CaseImportance: Critical
        """
        new_host = make_fake_host({
            'content-view-id': self.DEFAULT_CV['id'],
            'lifecycle-environment-id': self.LIBRARY['id'],
            'organization-id': self.new_org['id'],
        })
        self.assertEqual(
            new_host['content-information']['lifecycle-environment']['name'],
            self.LIBRARY['name'],
        )

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_lce(self):
        """Check if host can be created with new lifecycle

        :id: e102b034-0011-471d-ba21-5ef8d129a61f

        :expectedresults: Host is created using new lifecycle

        :BZ: 1313056

        :CaseImportance: Critical
        """
        new_host = make_fake_host({
            'content-view-id': self.promoted_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-id': self.new_org['id'],
        })
        self.assertEqual(
            new_host['content-information']['lifecycle-environment']['name'],
            self.new_lce['name'],
        )

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_cv(self):
        """Check if host can be created with new content view

        :id: f90873b9-fb3a-4c93-8647-4b1aea0a2c35

        :expectedresults: Host is created using new published, promoted cv

        :BZ: 1313056

        :CaseImportance: Critical
        """
        new_host = make_fake_host({
            'content-view-id': self.promoted_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-id': self.new_org['id'],
        })
        self.assertEqual(
            new_host['content-information']['content-view']['name'],
            self.promoted_cv['name'],
        )

    @tier1
    def test_positive_create_with_puppet_class_id(self):
        """Check if host can be created with puppet class id

        :id: 6bb1bbdc-23fd-4493-9283-fbb70d72b2eb

        :expectedresults: Host is created and has puppet class assigned

        :CaseImportance: Critical
        """
        host = make_fake_host({
            'puppet-class-ids': self.puppet_class['id'],
            'environment-id': self.puppet_env['id'],
            'organization-id': self.new_org['id'],
        })
        host_classes = Host.puppetclasses({'host-id': host['id']})
        self.assertIn(
            self.puppet_class['id'],
            [puppet['id'] for puppet in host_classes]
        )

    @tier1
    def test_positive_create_with_puppet_class_name(self):
        """Check if host can be created with puppet class name

        :id: a65df36e-db4b-48d2-b0e1-5ccfbefd1e7a

        :expectedresults: Host is created and has puppet class assigned

        :CaseImportance: Critical
        """
        host = make_fake_host({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.puppet_env['name'],
            'organization-id': self.new_org['id'],
        })
        host_classes = Host.puppetclasses({'host': host['name']})
        self.assertIn(
            self.puppet_class['name'],
            [puppet['name'] for puppet in host_classes]
        )

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
                    make_fake_host({
                        'name': name,
                        'organization-id': self.new_org['id'],
                        'content-view-id': self.DEFAULT_CV['id'],
                        'lifecycle-environment-id': self.LIBRARY['id'],
                    })

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_unpublished_cv(self):
        """Check if host can be created using unpublished cv

        :id: 9997383d-3c27-4f14-94f9-4b8b51180eb6

        :expectedresults: Host is not created using new unpublished cv

        :CaseImportance: Critical
        """
        cv = make_content_view({'organization-id': self.new_org['id']})
        env = self.new_lce['id']
        with self.assertRaises(CLIFactoryError):
            make_fake_host({
                'content-view-id': cv['id'],
                'lifecycle-environment-id': env,
                'organization-id': self.new_org['id'],
            })

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
                lce='{}/{}'.format(
                    self.new_lce['label'], self.promoted_cv['label']),
            )
            self.assertTrue(client.subscribed)

    @tier3
    def test_negative_register_twice(self):
        """Attempt to register a host twice to Satellite

        :id: 0af81129-cd69-4fa7-a128-9e8fcf2d03b1

        :expectedresults: host cannot be registered twice

        :CaseLevel: System
        """
        activation_key = make_activation_key({
            'content-view-id': self.promoted_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-id': self.new_org['id'],
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.new_org['label'],
                activation_key['name'],
            )
            self.assertTrue(client.subscribed)
            result = client.register_contenthost(
                self.new_org['label'],
                activation_key['name'],
                force=False,
            )
            # Depending on distro version, successful return_code may be 0 or
            # 1, so we can't verify host wasn't registered by return_code != 0
            # check. Verifying return_code == 64 here, which stands for content
            # host being already registered.
            self.assertEqual(result.return_code, 64)

    def test_positive_register_twice_with_uppercase_chars_in_hostname(self):
        """Register twice a client host that contain upper case chars in
        hostname.

        :id: 59c20379-b878-46ce-ad3e-ed6969ea6a5f

        :customerscenario: true

        :steps:
            1. Create a client host with upper case chars in hostname
            2. register the host with command "subscription-manager register"
            3. register the host a second time with command
                "subscription-manager register --force"

        :expectedresults: host registered the second time, without error

        :BZ: 1361309

        :CaseLevel: System
        """
        activation_key = make_activation_key({
            'content-view-id': self.promoted_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-id': self.new_org['id'],
        })
        name = gen_string('alpha')
        # make all the odd chars as upper case and the even one lower case
        # to have a name like OpQrSTuVw
        name_chars = list(name.lower())
        for i in range(len(name_chars)):
            if i % 2 == 0:
                name_chars[i] = name_chars[i].upper()
        target_image = ''.join(name_chars)
        with VirtualMachine(
                distro=DISTRO_RHEL7, target_image=target_image) as client:
            self.assertIn(target_image, client.hostname)
            result = client.run('hostname')
            self.assertIn(target_image, '\n'.join(result.stdout))
            client.install_katello_ca()
            client.register_contenthost(
                self.new_org['label'],
                activation_key['name'],
                force=False,
            )
            self.assertTrue(client.subscribed)
            result = client.register_contenthost(
                    self.new_org['label'],
                    activation_key['name'],
                    force=True,
                )
            self.assertFalse(result.stderr)
            self.assertIn(
                'The system has been registered with ID',
                '\n'.join(result.stdout)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_list_scparams_by_id(self):
        """List all smart class parameters using host id

        :id: 596322f6-9fdc-441a-a36d-ae2f22132b38

        :expectedresults: Overridden sc-param from puppet class is listed

        :CaseLevel: Integration
        """
        # Create hostgroup with associated puppet class
        host = make_fake_host({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.puppet_env['name'],
            'organization-id': self.new_org['id'],
        })
        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list({
            'environment': self.puppet_env['name'],
            'search': u'puppetclass="{0}"'.format(self.puppet_class['name'])
        })
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        host_scparams = Host.sc_params({'host': host['name']})
        self.assertIn(scp_id, [scp['id'] for scp in host_scparams])

    @run_only_on('sat')
    @tier2
    def test_positive_list_scparams_by_name(self):
        """List all smart class parameters using host name

        :id: 26e406ea-56f5-4813-bb93-e908c9015ee3

        :expectedresults: Overridden sc-param from puppet class is listed

        :CaseLevel: Integration
        """
        # Create hostgroup with associated puppet class
        host = make_fake_host({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.puppet_env['name'],
            'organization-id': self.new_org['id'],
        })
        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list({
            'environment': self.puppet_env['name'],
            'search': u'puppetclass="{0}"'.format(self.puppet_class['name'])
        })
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        host_scparams = Host.sc_params({'host': host['name']})
        self.assertIn(scp_id, [scp['id'] for scp in host_scparams])

    @run_only_on('sat')
    @tier2
    def test_positive_list_smartvariables_by_id(self):
        """List all smart variables using host id

        :id: 22d85dea-0fc0-47c2-8f38-c6f6712dad7e

        :expectedresults: Smart variable from puppet class is listed

        :CaseLevel: Integration
        """
        # Create hostgroup with associated puppet class
        host = make_fake_host({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.puppet_env['name'],
            'organization-id': self.new_org['id'],
        })
        # Create smart variable
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name']})
        # Verify that affected sc-param is listed
        host_variables = Host.smart_variables({'host-id': host['id']})
        self.assertIn(
            smart_variable['id'], [sv['id'] for sv in host_variables])

    @run_only_on('sat')
    @tier2
    def test_positive_list_smartvariables_by_name(self):
        """List all smart variables using host name

        :id: a254d3a6-cf7f-4847-acb6-9813d23369d4

        :expectedresults: Smart variable from puppet class is listed

        :CaseLevel: Integration
        """
        # Create hostgroup with associated puppet class
        host = make_fake_host({
            'puppet-classes': self.puppet_class['name'],
            'environment': self.puppet_env['name'],
            'organization-id': self.new_org['id'],
        })
        # Create smart variable
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name']})
        # Verify that affected sc-param is listed
        host_variables = Host.smart_variables({'host': host['name']})
        self.assertIn(
            smart_variable['id'], [sv['id'] for sv in host_variables])

    @tier3
    def test_positive_list(self):
        """List hosts for a given org

        :id: b9c056cd-11ca-4870-bac4-0ebc4a782cb0

        :expectedresults: Hosts are listed for the given org

        :CaseLevel: System
        """
        activation_key = make_activation_key({
            'content-view-id': self.promoted_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-id': self.new_org['id'],
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.new_org['label'],
                activation_key['name'],
            )
            self.assertTrue(client.subscribed)
            hosts = Host.list({
                'organization-id': self.new_org['id'],
                'environment-id': self.new_lce['id'],
            })
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
                lce='{}/{}'.format(
                    self.new_lce['label'], self.promoted_cv['label']),
            )
            self.assertTrue(client.subscribed)
            hosts = Host.list({
                'search': 'last_checkin = "Today" or '
                          'last_checkin = "Yesterday"'
            })
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
        activation_key = make_activation_key({
            'content-view-id': self.promoted_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-id': self.new_org['id'],
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.new_org['label'],
                activation_key['name'],
            )
            self.assertTrue(client.subscribed)
            hosts = Host.list({
                'organization-id': self.new_org['id'],
                'environment-id': self.new_lce['id'],
            })
            self.assertGreaterEqual(len(hosts), 1)
            self.assertIn(client.hostname, [host['name'] for host in hosts])
            result = client.run('subscription-manager unregister')
            self.assertEqual(result.return_code, 0)
            hosts = Host.list({
                'organization-id': self.new_org['id'],
                'environment-id': self.new_lce['id'],
            })
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
            url='qemu+ssh://root@{0}/system'.format(
                settings.compute_resources.libvirt_hostname
            )
        ).create()
        host = entities.Host()
        host.create_missing()
        result = make_host({
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
        })
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
        hostgroup = make_hostgroup({
            'content-view-id': self.new_cv['id'],
            'lifecycle-environment-id': self.new_lce['id'],
            'organization-ids': self.new_org['id'],
        })
        host = make_fake_host({
            'hostgroup-id': hostgroup['id'],
            'organization-id': self.new_org['id'],
        })
        self.assertEqual(
            host['content-information']['lifecycle-environment']['name'],
            hostgroup['lifecycle-environment']['name'],
        )
        self.assertEqual(
            host['content-information']['content-view']['name'],
            hostgroup['content-view']['name'],
        )

    @skip_if_bug_open('bugzilla', '1436162')
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
        lce = make_lifecycle_environment({
            'organization-id': options.organization.id})
        cv = make_content_view({'organization-id': options.organization.id})
        ContentView.publish({'id': cv['id']})
        version_id = ContentView.version_list({
            'content-view-id': cv['id'],
        })[0]['id']
        ContentView.version_promote({
            'id': version_id,
            'to-lifecycle-environment-id': lce['id'],
        })
        host_name = gen_string('alpha').lower()
        nested_hg_name = gen_string('alpha')
        parent_hostgroups = []
        nested_hostgroups = []
        for _ in range(2):
            parent_hg_name = gen_string('alpha')
            parent_hostgroups.append(make_hostgroup({
                'name': parent_hg_name,
                'organization-ids': options.organization.id,
            }))
            nested_hostgroups.append(make_hostgroup({
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
            }))

        host = make_host({
            'hostgroup-title': nested_hostgroups[0]['title'],
            'location-id': options.location.id,
            'organization-id': options.organization.id,
            'name': host_name,
        })
        self.assertEqual(
            '{0}.{1}'.format(host_name, options.domain.read().name),
            host['name'],
        )

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
        lce = make_lifecycle_environment({
            'organization-id': options.organization.id})
        cv = make_content_view({'organization-id': options.organization.id})
        ContentView.publish({'id': cv['id']})
        version_id = ContentView.version_list({
            'content-view-id': cv['id'],
        })[0]['id']
        ContentView.version_promote({
            'id': version_id,
            'to-lifecycle-environment-id': lce['id'],
        })
        make_hostgroup({
            'name': parent_hg_name,
            'organization-ids': options.organization.id,
        })
        nested_hostgroup = make_hostgroup({
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
        })
        make_host({
            'hostgroup-id': nested_hostgroup['id'],
            'location-id': options.location.id,
            'organization-id': options.organization.id,
            'name': host_name,
        })
        hosts = Host.list({'organization-id': options.organization.id})
        self.assertEqual(
            '{0}/{1}'.format(parent_hg_name, nested_hg_name),
            hosts[0]['host-group'],
        )

    @run_only_on('sat')
    @stubbed()
    @tier2
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

        :caseautomation: notautomated

        :CaseLevel: System
        """


class HostDeleteTestCase(CLITestCase):
    """Tests for deleting the hosts via CLI."""

    def setUp(self):
        """Create a host to use in tests"""
        super(HostDeleteTestCase, self).setUp()
        # Use the default installation smart proxy
        self.puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        self.host = entities.Host()
        self.host.create_missing()
        self.host = make_host({
            u'architecture-id': self.host.architecture.id,
            u'domain-id': self.host.domain.id,
            u'environment-id': self.host.environment.id,
            # pylint:disable=no-member
            u'location-id': self.host.location.id,
            u'mac': self.host.mac,
            u'medium-id': self.host.medium.id,
            u'name': gen_string('alphanumeric'),
            u'operatingsystem-id': self.host.operatingsystem.id,
            # pylint:disable=no-member
            u'organization-id': self.host.organization.id,
            u'partition-table-id': self.host.ptable.id,
            u'puppet-proxy-id': self.puppet_proxy['id'],
            u'root-password': self.host.root_pass,
        })

    @tier1
    def test_positive_delete_by_id(self):
        """Create a host and then delete it by id.

        :id: e687a685-ab8b-4c5f-97f9-e14d3ab52f29

        :expectedresults: Host is deleted

        :CaseImportance: Critical
        """
        Host.delete({'id': self.host['id']})
        with self.assertRaises(CLIReturnCodeError):
            Host.info({'id': self.host['id']})

    @tier1
    def test_positive_delete_by_name(self):
        """Create a host and then delete it by name.

        :id: 93f7504d-9a63-491f-8fdb-ed8017aefab9

        :expectedresults: Host is deleted

        :CaseImportance: Critical
        """
        Host.delete({'name': self.host['name']})
        with self.assertRaises(CLIReturnCodeError):
            Host.info({'name': self.host['name']})


class HostUpdateTestCase(CLITestCase):
    """Tests for updating the hosts."""

    def setUp(self):
        """Create a host to reuse later"""
        super(HostUpdateTestCase, self).setUp()
        self.puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        # using nailgun to create dependencies
        self.host_args = entities.Host()
        self.host_args.create_missing()
        # using CLI to create host
        self.host = make_host({
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
        })

    @skip_if_bug_open('bugzilla', '1343392')
    @tier1
    def test_positive_update_name_by_id(self):
        """A host can be updated with a new random name. Use id to
        access the host

        :id: 058dbcbf-d543-483d-b755-be0602588464

        :expectedresults: A host is updated and the name matches

        :CaseImportance: Critical
        """
        for new_name in valid_hosts_list():
            with self.subTest(new_name):
                Host.update({
                    'id': self.host['id'],
                    'new-name': new_name,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertEqual(
                    u'{0}.{1}'.format(
                        new_name, self.host['network']['domain']),
                    self.host['name']
                )

    @skip_if_bug_open('bugzilla', '1343392')
    @tier1
    def test_positive_update_name_by_name(self):
        """A host can be updated with a new random name. Use name to
        access the host

        :id: f95a5952-17bd-49da-b2a7-c79f0614f1c7

        :expectedresults: A host is updated and the name matches

        :CaseImportance: Critical
        """
        for new_name in valid_hosts_list():
            with self.subTest(new_name):
                Host.update({
                    'name': self.host['name'],
                    'new-name': new_name,
                })
                self.host = Host.info({
                    'name': u'{0}.{1}'.format(
                        new_name, self.host['network']['domain'])})
                self.assertEqual(
                    u'{0}.{1}'.format(
                        new_name, self.host['network']['domain']),
                    self.host['name'],
                )

    @tier1
    def test_positive_update_mac_by_id(self):
        """A host can be updated with a new random MAC address. Use id
        to access the host

        :id: 72ed9ae8-989a-46d1-8b7d-46f5db106e75

        :expectedresults: A host is updated and the MAC address matches

        :CaseImportance: Critical
        """
        new_mac = gen_mac(multicast=False)
        Host.update({
            'id': self.host['id'],
            'mac': new_mac,
        })
        self.host = Host.info({'id': self.host['id']})
        self.assertEqual(self.host['network']['mac'], new_mac)

    @tier1
    def test_positive_update_mac_by_name(self):
        """A host can be updated with a new random MAC address. Use name
        to access the host

        :id: a422788d-5473-4846-a86b-90d8f236285a

        :expectedresults: A host is updated and the MAC address matches

        :CaseImportance: Critical
        """
        new_mac = gen_mac(multicast=False)
        Host.update({
            'mac': new_mac,
            'name': self.host['name'],
        })
        self.host = Host.info({'name': self.host['name']})
        self.assertEqual(self.host['network']['mac'], new_mac)

    @tier2
    def test_positive_update_domain_by_id(self):
        """A host can be updated with a new domain. Use entities ids for
        association

        :id: 3aac0896-d16a-46ee-afe9-2d3ecea6ca9b

        :expectedresults: A host is updated and the domain matches

        :CaseLevel: Integration
        """
        new_domain = make_domain({
            'location-id': self.host_args.location.id,
            'organization-id': self.host_args.organization.id,
        })
        Host.update({
            'domain-id': new_domain['id'],
            'id': self.host['id'],
        })
        self.host = Host.info({'id': self.host['id']})
        self.assertEqual(self.host['network']['domain'], new_domain['name'])

    @tier2
    def test_positive_update_domain_by_name(self):
        """A host can be updated with a new domain. Use entities names
        for association

        :id: 9b4fb1b9-a226-4b8a-bfaf-1121de7df5bc

        :expectedresults: A host is updated and the domain matches

        :CaseLevel: Integration
        """
        new_domain = make_domain({
            'location': self.host_args.location.name,
            'organization': self.host_args.organization.name,
        })
        Host.update({
            'domain': new_domain['name'],
            'name': self.host['name'],
        })
        self.host = Host.info({
            'name': '{0}.{1}'.format(
                self.host['name'].split('.')[0],
                new_domain['name'],
            )
        })
        self.assertEqual(self.host['network']['domain'], new_domain['name'])

    @tier2
    def test_positive_update_env_by_id(self):
        """A host can be updated with a new environment. Use entities
        ids for association

        :id: 4e1d1e31-fa84-43e4-9e66-7fb953767ee5

        :expectedresults: A host is updated and the environment matches

        :CaseLevel: Integration
        """
        new_env = make_environment({
            'location-id': self.host_args.location.id,
            'organization-id': self.host_args.organization.id,
        })
        Host.update({
            'environment-id': new_env['id'],
            'id': self.host['id'],
        })
        self.host = Host.info({'id': self.host['id']})
        self.assertEqual(self.host['puppet-environment'], new_env['name'])

    @tier2
    def test_positive_update_env_by_name(self):
        """A host can be updated with a new environment. Use entities
        names for association

        :id: f0ec469a-7550-4f05-b39c-e68b9267247d

        :expectedresults: A host is updated and the environment matches

        :CaseLevel: Integration
        """
        new_env = make_environment({
            'location': self.host_args.location.name,
            'organization': self.host_args.organization.name,
        })
        Host.update({
            'environment': new_env['name'],
            'name': self.host['name'],
        })
        self.host = Host.info({'name': self.host['name']})
        self.assertEqual(self.host['puppet-environment'], new_env['name'])

    @tier2
    def test_positive_update_arch_by_id(self):
        """A host can be updated with a new architecture. Use entities
        ids for association

        :id: a4546fd6-997a-44e4-853a-eac235ea87b0

        :expectedresults: A host is updated and the architecture matches

        :CaseLevel: Integration
        """
        new_arch = make_architecture({
            'location-id': self.host_args.location.id,
            'organization-id': self.host_args.organization.id,
        })
        OperatingSys.add_architecture({
            'architecture-id': new_arch['id'],
            'id': self.host_args.operatingsystem.id,
        })
        Host.update({
            'architecture-id': new_arch['id'],
            'id': self.host['id'],
        })
        self.host = Host.info({'id': self.host['id']})
        self.assertEqual(
            self.host['operating-system']['architecture'], new_arch['name'])

    @tier2
    def test_positive_update_arch_by_name(self):
        """A host can be updated with a new architecture. Use entities
        names for association

        :id: 92da3782-47db-4701-aaab-3ea974043d20

        :expectedresults: A host is updated and the architecture matches

        :CaseLevel: Integration
        """
        new_arch = make_architecture({
            'location': self.host_args.location.name,
            'organization': self.host_args.organization.name,
        })
        OperatingSys.add_architecture({
            'architecture': new_arch['name'],
            'title': self.host_args.operatingsystem.title,
        })
        Host.update({
            'architecture': new_arch['name'],
            'name': self.host['name'],
        })
        self.host = Host.info({'name': self.host['name']})
        self.assertEqual(
            self.host['operating-system']['architecture'], new_arch['name'])

    @tier2
    def test_positive_update_os_by_id(self):
        """A host can be updated with a new operating system. Use
        entities ids for association

        :id: 9ea88634-9c14-4519-be6e-fb163897efb7

        :expectedresults: A host is updated and the operating system matches

        :CaseLevel: Integration
        """
        new_os = make_os({
            'architecture-ids': self.host_args.architecture.id,
            'partition-table-ids': self.host_args.ptable.id,
        })
        Medium.add_operating_system({
            'id': self.host_args.medium.id,
            'operatingsystem-id': new_os['id'],
        })
        Host.update({
            'id': self.host['id'],
            'operatingsystem-id': new_os['id'],
        })
        self.host = Host.info({'id': self.host['id']})
        self.assertEqual(
            self.host['operating-system']['operating-system'], new_os['title'])

    @tier2
    def test_positive_update_os_by_name(self):
        """A host can be updated with a new operating system. Use
        entities names for association

        :id: bd48887f-3db3-47b0-8231-de58884efe57

        :expectedresults: A host is updated and the operating system matches

        :CaseLevel: Integration
        """
        new_os = make_os({
            'architectures': self.host_args.architecture.name,
            'partition-tables': self.host[
                'operating-system']['partition-table'],
        })
        Medium.add_operating_system({
            'name': self.host_args.medium.name,
            'operatingsystem': new_os['title'],
        })
        Host.update({
            'name': self.host['name'],
            'operatingsystem': new_os['title'],
        })
        self.host = Host.info({'name': self.host['name']})
        self.assertEqual(
            self.host['operating-system']['operating-system'], new_os['title'])

    @tier2
    def test_positive_update_medium_by_id(self):
        """A host can be updated with a new medium. Use entities ids for
        association

        :id: 899f1eef-07a9-4227-848a-92e377a8d55c

        :expectedresults: A host is updated and the medium matches

        :CaseLevel: Integration
        """
        new_medium = make_medium({
            'location-id': self.host_args.location.id,
            'organization-id': self.host_args.organization.id,
        })
        Medium.add_operating_system({
            'id': new_medium['id'],
            'operatingsystem-id': self.host_args.operatingsystem.id,
        })
        new_medium = Medium.info({'id': new_medium['id']})
        Host.update({
            'id': self.host['id'],
            'medium-id': new_medium['id'],
        })
        self.host = Host.info({'id': self.host['id']})
        self.assertEqual(
            self.host['operating-system']['medium'], new_medium['name'])

    @tier2
    def test_positive_update_medium_by_name(self):
        """A host can be updated with a new medium. Use entities names
        for association

        :id: f47edb02-d649-4ca8-94b2-0637ebdac2e8

        :expectedresults: A host is updated and the medium matches

        :CaseLevel: Integration
        """
        new_medium = make_medium({
            'location': self.host_args.location.name,
            'organization': self.host_args.organization.name,
        })
        Medium.add_operating_system({
            'name': new_medium['name'],
            'operatingsystem': self.host_args.operatingsystem.title,
        })
        new_medium = Medium.info({'name': new_medium['name']})
        Host.update({
            'medium': new_medium['name'],
            'name': self.host['name'],
        })
        self.host = Host.info({'name': self.host['name']})
        self.assertEqual(
            self.host['operating-system']['medium'], new_medium['name'])

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
                    Host.update({
                        'id': self.host['id'],
                        'new-name': new_name,
                    })
                self.host = Host.info({'id': self.host['id']})
                self.assertNotEqual(
                    u'{0}.{1}'.format(
                        new_name,
                        self.host['network']['domain'],
                    ).lower(),
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
                    Host.update({
                        'id': self.host['id'],
                        'mac': new_mac,
                    })
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
        new_arch = make_architecture({
            'location': self.host_args.location.name,
            'organization': self.host_args.organization.name,
        })
        with self.assertRaises(CLIReturnCodeError):
            Host.update({
                'architecture': new_arch['name'],
                'id': self.host['id'],
            })
        self.host = Host.info({'id': self.host['id']})
        self.assertNotEqual(
            self.host['operating-system']['architecture'], new_arch['name'])

    @tier2
    def test_negative_update_os(self):
        """A host can not be updated with a operating system, which is
        not associated with host's medium

        :id: ff13d2af-e54a-4daf-a24d-7ec930b4fbbe

        :expectedresults: A host is not updated

        :CaseLevel: Integration
        """
        new_arch = make_architecture({
            'location': self.host_args.location.name,
            'organization': self.host_args.organization.name,
        })
        new_os = make_os({
            'architectures': new_arch['name'],
            'partition-tables': self.host[
                'operating-system']['partition-table'],
        })
        with self.assertRaises(CLIReturnCodeError):
            Host.update({
                'architecture': new_arch['name'],
                'id': self.host['id'],
                'operatingsystem': new_os['title'],
            })
        self.host = Host.info({'id': self.host['id']})
        self.assertNotEqual(
            self.host['operating-system']['operating-system'], new_os['title'])


class HostParameterTestCase(CLITestCase):
    """Tests targeting host parameters"""

    @classmethod
    def setUpClass(cls):
        """Create host to tests parameters for"""
        super(HostParameterTestCase, cls).setUpClass()
        cls.puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        # using nailgun to create dependencies
        cls.host = entities.Host()
        cls.host.create_missing()
        cls.org_id = cls.host.organization.id
        cls.loc_id = cls.host.location.id
        # using CLI to create host
        cls.host = make_host({
            u'architecture-id': cls.host.architecture.id,
            u'domain-id': cls.host.domain.id,
            u'environment-id': cls.host.environment.id,
            u'location-id': cls.loc_id,
            u'mac': cls.host.mac,
            u'medium-id': cls.host.medium.id,
            u'name': cls.host.name,
            u'operatingsystem-id': cls.host.operatingsystem.id,
            u'organization-id': cls.org_id,
            u'partition-table-id': cls.host.ptable.id,
            u'puppet-proxy-id': cls.puppet_proxy['id'],
            u'root-password': cls.host.root_pass,
        })

    @tier1
    def test_positive_add_parameter_with_name(self):
        """Add host parameter with different valid names.

        :id: 67b1c496-8f33-4a34-aebb-7339bc33ce77

        :expectedresults: Host parameter was successfully added with correct
            name.


        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                name = name.lower()
                Host.set_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                    'value': gen_string('alphanumeric'),
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertIn(name, self.host['parameters'].keys())

    @tier1
    def test_positive_add_parameter_with_value(self):
        """Add host parameter with different valid values.

        :id: 1932b61d-8be4-4f58-9760-dc588cbca1d7

        :expectedresults: Host parameter was successfully added with value.


        :CaseImportance: Critical
        """
        for value in valid_data_list():
            with self.subTest(value):
                name = gen_string('alphanumeric').lower()
                Host.set_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                    'value': value,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertIn(name, self.host['parameters'].keys())
                self.assertEqual(value, self.host['parameters'][name])

    @tier1
    def test_positive_add_parameter_by_host_name(self):
        """Add host parameter by specifying host name.

        :id: 32b09b07-39de-4706-ac5e-75a54255df17

        :expectedresults: Host parameter was successfully added with correct
            name and value.

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric').lower()
        value = gen_string('alphanumeric')
        Host.set_parameter({
            'host': self.host['name'],
            'name': name,
            'value': value,
        })
        self.host = Host.info({'id': self.host['id']})
        self.assertIn(name, self.host['parameters'].keys())
        self.assertEqual(value, self.host['parameters'][name])

    @tier1
    def test_positive_update_parameter_by_host_id(self):
        """Update existing host parameter by specifying host ID.

        :id: 56c43ab4-7fb0-44f5-9d54-107d3c1011bf

        :expectedresults: Host parameter was successfully updated with new
            value.


        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric').lower()
        old_value = gen_string('alphanumeric')
        Host.set_parameter({
            'host-id': self.host['id'],
            'name': name,
            'value': old_value,
        })
        for new_value in valid_data_list():
            with self.subTest(new_value):
                Host.set_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                    'value': new_value,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertIn(name, self.host['parameters'].keys())
                self.assertEqual(new_value, self.host['parameters'][name])

    @tier1
    def test_positive_update_parameter_by_host_name(self):
        """Update existing host parameter by specifying host name.

        :id: 24bcc8a4-7787-4fa8-9bf8-dfc5e697684f

        :expectedresults: Host parameter was successfully updated with new
            value.


        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric').lower()
        old_value = gen_string('alphanumeric')
        Host.set_parameter({
            'host': self.host['name'],
            'name': name,
            'value': old_value,
        })
        for new_value in valid_data_list():
            with self.subTest(new_value):
                Host.set_parameter({
                    'host': self.host['name'],
                    'name': name,
                    'value': new_value,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertIn(name, self.host['parameters'].keys())
                self.assertEqual(new_value, self.host['parameters'][name])

    @tier1
    def test_positive_delete_parameter_by_host_id(self):
        """Delete existing host parameter by specifying host ID.

        :id: a52da845-0403-4b66-9e83-6065f7d4551d

        :expectedresults: Host parameter was successfully deleted.


        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                name = name.lower()
                Host.set_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                    'value': gen_string('alphanumeric'),
                })
                Host.delete_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertNotIn(name, self.host['parameters'].keys())

    @tier1
    def test_posistive_delete_parameter_by_host_name(self):
        """Delete existing host parameter by specifying host name.

        :id: d28cbbba-d296-49c7-91f5-8fb63a80d82c

        :expectedresults: Host parameter was successfully deleted.


        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                name = name.lower()
                Host.set_parameter({
                    'host': self.host['name'],
                    'name': name,
                    'value': gen_string('alphanumeric'),
                })
                Host.delete_parameter({
                    'host': self.host['name'],
                    'name': name,
                })
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
                    Host.set_parameter({
                        'host-id': self.host['id'],
                        'name': name,
                        'value': gen_string('alphanumeric'),
                    })
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

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha').lower()
        param_value = gen_string('alphanumeric')
        user_name = gen_string('alphanumeric')
        user_password = gen_string('alphanumeric')
        Host.set_parameter({
            'host-id': self.host['id'],
            'name': param_name,
            'value': param_value,
        })
        host = Host.info({'id': self.host['id']})
        self.assertEqual(host['parameters'][param_name], param_value)
        role = make_role()
        add_role_permissions(
            role['id'],
            resource_permissions={
                'Host': {'permissions': ['view_hosts']},
                'Organization': {'permissions': ['view_organizations']},
            }
        )
        user = make_user({
            'admin': False,
            'default-organization-id': self.org_id,
            'organization-ids': [self.org_id],
            'default-location-id': self.loc_id,
            'location-ids': [self.loc_id],
            'login': user_name,
            'password': user_password,
        })
        User.add_role({'id': user['id'], 'role-id': role['id']})
        host = Host.with_user(
            username=user_name,
            password=user_password
        ).info({'id': self.host['id']})
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

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha').lower()
        param_value = gen_string('alphanumeric')
        user_name = gen_string('alphanumeric')
        user_password = gen_string('alphanumeric')
        Host.set_parameter({
            'host-id': self.host['id'],
            'name': param_name,
            'value': param_value,
        })
        host = Host.info({'id': self.host['id']})
        self.assertEqual(host['parameters'][param_name], param_value)
        role = make_role()
        add_role_permissions(
            role['id'],
            resource_permissions={
                'Host': {'permissions': ['view_hosts']},
                'Organization': {'permissions': ['view_organizations']},
                'Parameter': {'permissions': ['view_params']},
            }
        )
        user = make_user({
            'admin': False,
            'default-organization-id': self.org_id,
            'organization-ids': [self.org_id],
            'default-location-id': self.loc_id,
            'location-ids': [self.loc_id],
            'login': user_name,
            'password': user_password,
        })
        User.add_role({'id': user['id'], 'role-id': role['id']})
        host = Host.with_user(
            username=user_name,
            password=user_password
        ).info({'id': self.host['id']})
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

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha').lower()
        param_value = gen_string('alphanumeric')
        user_name = gen_string('alphanumeric')
        user_password = gen_string('alphanumeric')
        Host.set_parameter({
            'host-id': self.host['id'],
            'name': param_name,
            'value': param_value,
        })
        host = Host.info({'id': self.host['id']})
        self.assertEqual(host['parameters'][param_name], param_value)
        role = make_role()
        add_role_permissions(
            role['id'],
            resource_permissions={
                'Host': {'permissions': ['view_hosts']},
                'Organization': {'permissions': ['view_organizations']},
                'Parameter': {'permissions': ['view_params']},
            }
        )
        user = make_user({
            'admin': False,
            'default-organization-id': self.org_id,
            'organization-ids': [self.org_id],
            'default-location-id': self.loc_id,
            'location-ids': [self.loc_id],
            'login': user_name,
            'password': user_password,
        })
        User.add_role({'id': user['id'], 'role-id': role['id']})
        param_new_value = gen_string('alphanumeric')
        with self.assertRaises(CLIReturnCodeError):
            Host.with_user(
                username=user_name,
                password=user_password
            ).set_parameter({
                'host-id': self.host['id'],
                'name': param_name,
                'value': param_new_value,
            })
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

        :CaseLevel: System
        """
        param_name = gen_string('alpha').lower()
        # long string that should be escaped and affected by line break with
        # yaml dump by default
        param_value = (
            u'auth                          include              '
            u'password-auth\r\n'
            u'account     include                  password-auth'
        )
        host = self.host
        # count parameters of a host
        response = Host.info(
            {'id': host['id']}, output_format='yaml', return_raw_response=True)
        self.assertEqual(response.return_code, 0)
        yaml_content = yaml.load('\n'.join(response.stdout))
        host_initial_params = yaml_content.get('Parameters')
        # set parameter
        Host.set_parameter({
            'host-id': host['id'],
            'name': param_name,
            'value': param_value,
        })
        response = Host.info(
            {'id': host['id']}, output_format='yaml', return_raw_response=True)
        self.assertEqual(response.return_code, 0)
        yaml_content = yaml.load('\n'.join(response.stdout))
        host_parameters = yaml_content.get('Parameters')
        # check that number of params increased by one
        self.assertEqual(len(host_parameters), 1 + len(host_initial_params))
        self.assertEqual(host_parameters[0]['name'], param_name)
        self.assertEqual(host_parameters[0]['value'], param_value)


class HostProvisionTestCase(CLITestCase):
    """Provisioning-related tests"""

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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


        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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


        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

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
        KatelloAgentTestCase.env = make_lifecycle_environment({
            u'organization-id': KatelloAgentTestCase.org['id'],
        })
        KatelloAgentTestCase.content_view = make_content_view({
            u'organization-id': KatelloAgentTestCase.org['id'],
        })
        KatelloAgentTestCase.activation_key = make_activation_key({
            u'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
            u'organization-id': KatelloAgentTestCase.org['id'],
        })
        # Add subscription to Satellite Tools repo to activation key
        setup_org_for_a_rh_repo({
            u'product': PRDS['rhel'],
            u'repository-set': REPOSET['rhst7'],
            u'repository': REPOS['rhst7']['name'],
            u'organization-id': KatelloAgentTestCase.org['id'],
            u'content-view-id': KatelloAgentTestCase.content_view['id'],
            u'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
            u'activationkey-id': KatelloAgentTestCase.activation_key['id'],
        })
        # Create custom repo, add subscription to activation key
        setup_org_for_a_custom_repo({
            u'url': FAKE_1_YUM_REPO,
            u'organization-id': KatelloAgentTestCase.org['id'],
            u'content-view-id': KatelloAgentTestCase.content_view['id'],
            u'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
            u'activationkey-id': KatelloAgentTestCase.activation_key['id'],
        })

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
            KatelloAgentTestCase.org['label'],
            KatelloAgentTestCase.activation_key['name'],
        )
        self.assertTrue(self.client.subscribed)
        self.host = Host.info({'name': self.client.hostname})
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_agent()

    @tier3
    @run_only_on('sat')
    def test_positive_get_errata_info(self):
        """Get errata info

        :id: afb5ab34-1703-49dc-8ddc-5e032c1b86d7

        :expectedresults: Errata info was displayed


        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        result = Host.errata_info({
            u'host-id': self.host['id'],
            u'id': FAKE_1_ERRATA_ID,
        })
        self.assertEqual(result[0]['errata-id'], FAKE_1_ERRATA_ID)
        self.assertIn(FAKE_2_CUSTOM_PACKAGE, result[0]['packages'])

    @tier3
    @run_only_on('sat')
    @upgrade
    def test_positive_apply_errata(self):
        """Apply errata to a host

        :id: 8d0e5c93-f9fd-4ec0-9a61-aa93082a30c5

        :expectedresults: Errata is scheduled for installation


        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        Host.errata_apply({
            u'errata-ids': FAKE_1_ERRATA_ID,
            u'host-id': self.host['id'],
        })

    @tier3
    @run_only_on('sat')
    def test_positive_apply_security_erratum(self):
        """Apply security erratum to a host

        :id: 4d1095c8-d354-42ac-af44-adf6dbb46deb

        :expectedresults: erratum is recognized by the
            `yum update --security` command on client

        :CaseLevel: System

        :BZ: 1420671
        """
        self.client.download_install_rpm(
            FAKE_1_YUM_REPO,
            FAKE_2_CUSTOM_PACKAGE
        )
        # Check the system is up to date
        result = self.client.run(
            'yum update --security | grep "No packages needed for security"'
        )
        self.assertEqual(result.return_code, 0)
        # Downgrade walrus package
        self.client.run('yum downgrade -y {0}'.format(
            FAKE_2_CUSTOM_PACKAGE_NAME))
        # Check that host has applicable errata
        host_errata = Host.errata_list({u'host-id': self.host['id']})
        self.assertEqual(host_errata[0]['erratum-id'], FAKE_1_ERRATA_ID)
        self.assertEqual(host_errata[0]['installable'], 'true')
        # Check the erratum becomes available
        result = self.client.run(
            'yum update --assumeno --security '
            '| grep "No packages needed for security"'
        )
        self.assertEqual(result.return_code, 1)

    @tier3
    @run_only_on('sat')
    @upgrade
    def test_positive_install_package(self):
        """Install a package to a host remotely

        :id: b1009bba-0c7e-4b00-8ac4-256e5cfe4a78

        :expectedresults: Package was successfully installed


        :CaseLevel: System
        """
        Host.package_install({
            u'host-id': self.host['id'],
            u'packages': FAKE_0_CUSTOM_PACKAGE_NAME,
        })
        result = self.client.run(
            'rpm -q {0}'.format(FAKE_0_CUSTOM_PACKAGE_NAME)
        )
        self.assertEqual(result.return_code, 0)

    @tier3
    @run_only_on('sat')
    def test_positive_remove_package(self):
        """Remove a package from a host remotely

        :id: 573dec11-8f14-411f-9e41-84426b0f23b5

        :expectedresults: Package was successfully removed


        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        Host.package_remove({
            u'host-id': self.host['id'],
            u'packages': FAKE_1_CUSTOM_PACKAGE_NAME,
        })
        result = self.client.run(
            'rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE_NAME)
        )
        self.assertNotEqual(result.return_code, 0)

    @tier3
    @run_only_on('sat')
    def test_positive_upgrade_package(self):
        """Upgrade a host package remotely

        :id: ad751c63-7175-40ae-8bc4-800462cd9c29

        :expectedresults: Package was successfully upgraded


        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        Host.package_upgrade({
            u'host-id': self.host['id'],
            u'packages': FAKE_1_CUSTOM_PACKAGE_NAME,
        })
        result = self.client.run('rpm -q {0}'.format(FAKE_2_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)

    @tier3
    @run_only_on('sat')
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
    @run_only_on('sat')
    @upgrade
    def test_positive_install_package_group(self):
        """Install a package group to a host remotely

        :id: 8c28c188-2903-44d1-ab1e-b74f6d6affcf

        :expectedresults: Package group was successfully installed


        :CaseLevel: System
        """
        Host.package_group_install({
            u'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            u'host-id': self.host['id'],
        })
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.client.run('rpm -q {0}'.format(package))
            self.assertEqual(result.return_code, 0)

    @tier3
    @run_only_on('sat')
    def test_positive_remove_package_group(self):
        """Remove a package group from a host remotely

        :id: c80dbeff-93b4-4cd4-8fae-6a4d1bfc94f0

        :expectedresults: Package group was successfully removed


        :CaseLevel: System
        """
        hammer_args = {
            u'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            u'host-id': self.host['id'],
        }
        Host.package_group_install(hammer_args)
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
        result = self.client.run(
            'yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
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
        activation_key = make_activation_key({
            u'lifecycle-environment-id': self.env['id'],
            u'organization-id': self.org['id'],
            u'content-view-id': self.content_view['id'],
        })
        hc = make_host_collection({u'organization-id': self.org['id']})
        ActivationKey.add_host_collection({
            'id': activation_key['id'],
            'organization-id': self.org['id'],
            'host-collection-id': hc['id']
        })
        # add the registered instance host to collection
        HostCollection.add_host({
            'id': hc['id'],
            'organization-id': self.org['id'],
            'host-ids': self.host['id']
        })
        with VirtualMachine() as client:
            client.create()
            client.install_katello_ca()
            # register the client host with the current activation key
            client.register_contenthost(
                self.org['name'], activation_key=activation_key['name'])
            self.assertTrue(client.subscribed)
            # note: when registering the host, it should be automatically added
            # to the host collection
            client_host = Host.info({'name': client.hostname})
            hosts = HostCollection.hosts({
                'id': hc['id'],
                'organization-id': self.org['id'],
            })
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
        cls.env = make_lifecycle_environment({
            u'organization-id': cls.org['id'],
        })
        cls.content_view = make_content_view({
            u'organization-id': cls.org['id'],
        })
        cls.activation_key = make_activation_key({
            u'lifecycle-environment-id': cls.env['id'],
            u'organization-id': cls.org['id'],
        })
        # setup rh satellite tools repository content
        setup_org_for_a_rh_repo({
            u'product': PRDS['rhel'],
            u'repository-set': REPOSET['rhst7'],
            u'repository': REPOS['rhst7']['name'],
            u'organization-id': cls.org['id'],
            u'content-view-id': cls.content_view['id'],
            u'lifecycle-environment-id': cls.env['id'],
            u'activationkey-id': cls.activation_key['id'],
        })
        # Create custom repository content
        setup_org_for_a_custom_repo({
            u'url': FAKE_6_YUM_REPO,
            u'organization-id': cls.org['id'],
            u'content-view-id': cls.content_view['id'],
            u'lifecycle-environment-id': cls.env['id'],
            u'activationkey-id': cls.activation_key['id'],
        })

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
        self.client.register_contenthost(
            self.org['label'],
            self.activation_key['name'],
        )
        self.assertTrue(self.client.subscribed)
        self.host_info = Host.info({'name': self.client.hostname})
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_host_tools()

    @run_only_on('sat')
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
        result = self.client.run(
            'rpm -q {0}'.format(FAKE_0_CUSTOM_PACKAGE)
        )
        self.assertEqual(result.return_code, 0)
        installed_packages = Host.package_list({
            'host-id': self.host_info['id'],
            'search': 'name={0}'.format(FAKE_0_CUSTOM_PACKAGE_NAME)
        })
        self.assertEqual(len(installed_packages), 1)
        self.assertEqual(installed_packages[0]['nvra'], FAKE_0_CUSTOM_PACKAGE)
        result = self.client.run(
            'yum remove -y {0}'.format(FAKE_0_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        installed_packages = Host.package_list({
            'host-id': self.host_info['id'],
            'search': 'name={0}'.format(FAKE_0_CUSTOM_PACKAGE_NAME)
        })
        self.assertEqual(len(installed_packages), 0)

    @run_only_on('sat')
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
        result = self.client.run(
            'rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE)
        )
        self.assertEqual(result.return_code, 0)
        applicable_packages = Package.list({
            'host-id': self.host_info['id'],
            'packages-restrict-applicable': 'true',
            'search': 'name={0}'.format(FAKE_1_CUSTOM_PACKAGE_NAME)
        })
        self.assertEqual(len(applicable_packages), 1)
        self.assertIn(
            FAKE_2_CUSTOM_PACKAGE, applicable_packages[0]['filename'])
        # install package update
        self.client.run('yum install -y {0}'.format(FAKE_2_CUSTOM_PACKAGE))
        result = self.client.run(
            'rpm -q {0}'.format(FAKE_2_CUSTOM_PACKAGE)
        )
        self.assertEqual(result.return_code, 0)
        applicable_packages = Package.list({
            'host-id': self.host_info['id'],
            'packages-restrict-applicable': 'true',
            'search': 'name={0}'.format(FAKE_1_CUSTOM_PACKAGE_NAME)
        })
        self.assertEqual(len(applicable_packages), 0)

    @run_only_on('sat')
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

        :BZ: 1463809

        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        result = self.client.run(
            'rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE)
        )
        self.assertEqual(result.return_code, 0)
        applicable_erratum = Host.errata_list({
            'host-id': self.host_info['id'],
        })
        applicable_erratum_ids = [
            errata['erratum-id']
            for errata in applicable_erratum
            if errata['installable'] == 'true'
        ]
        self.assertIn(FAKE_2_ERRATA_ID, applicable_erratum_ids)
        # apply errata
        result = self.client.run(
            'yum update -y --advisory {0}'.format(FAKE_2_ERRATA_ID))
        self.assertEqual(result.return_code, 0)
        applicable_erratum = Host.errata_list({
            'host-id': self.host_info['id'],
        })
        applicable_erratum_ids = [
            errata['erratum-id']
            for errata in applicable_erratum
            if errata['installable'] == 'true'
        ]
        self.assertNotIn(FAKE_2_ERRATA_ID, applicable_erratum_ids)

    def test_negative_install_package(self):
        """Attempt to install a package to a host remotely

        :id: 751c05b4-d7a3-48a2-8860-f0d15fdce204

        :expectedresults: Package was not installed

        :CaseLevel: System
        """
        with self.assertRaises(CLIReturnCodeError) as context:
            Host.package_install({
                u'host-id': self.host_info['id'],
                u'packages': FAKE_1_CUSTOM_PACKAGE,
            })
        self.assertIn(
            ('The task has been cancelled. Is katello-agent installed and '
             'goferd running on the Host?'),
            str(context.exception)
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
    @skip_if_bug_open('bugzilla', 1444886)
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key"""
        super(HostSubscriptionTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.env = make_lifecycle_environment({
            u'organization-id': cls.org['id'],
        })
        cls.content_view = make_content_view({
            u'organization-id': cls.org['id'],
        })
        cls.activation_key = make_activation_key({
            u'lifecycle-environment-id': cls.env['id'],
            u'organization-id': cls.org['id'],
        })

        cls.subscription_name = SATELLITE_SUBSCRIPTION_NAME
        # create a rh capsule content
        setup_org_for_a_rh_repo({
            u'product': PRDS['rhsc'],
            u'repository-set': REPOSET['rhsc7'],
            u'repository': REPOS['rhsc7']['name'],
            u'organization-id': cls.org['id'],
            u'content-view-id': cls.content_view['id'],
            u'lifecycle-environment-id': cls.env['id'],
            u'activationkey-id': cls.activation_key['id'],
            u'subscription': cls.subscription_name,
        }, force_use_cdn=True)
        org_subscriptions = Subscription.list(
            {'organization-id': cls.org['id']})
        cls.default_subscription_id = None
        cls.repository_id = REPOS['rhsc7']['id']
        for org_subscription in org_subscriptions:
            if org_subscription['name'] == cls.subscription_name:
                cls.default_subscription_id = org_subscription['id']
                break
        # create a new lce for hosts subscription
        cls.hosts_env = make_lifecycle_environment({
            u'organization-id': cls.org['id'],
        })
        # refresh content view data
        cls.content_view = ContentView.info({'id': cls.content_view['id']})
        content_view_version = cls.content_view['versions'][-1]
        ContentView.version_promote({
            u'id': content_view_version['id'],
            u'organization-id': cls.org['id'],
            u'to-lifecycle-environment-id': cls.hosts_env['id'],
        })

    def setUp(self):
        """Create  a virtual machine without registration"""
        super(HostSubscriptionTestCase, self).setUp()
        self.client = VirtualMachine(distro=DISTRO_RHEL7)
        self.client.create()
        self.addCleanup(vm_cleanup, self.client)
        self.client.install_katello_ca()

    def _register_client(self, activation_key=None, lce=False,
                         enable_repo=False, auto_attach=False):
        """Register the client as a content host consumer

        :param activation_key: activation key if registration with activation
            key
        :param lce: boolean to indicate whether the registration should be made
            by environment
        :param enable_repo: boolean to indicate whether to enable repository
        :param auto_attach: boolean to indicate whether to register with
            auto-attach option, in case of registration with activation key a
            command is launched
        :return: the registration result
        """
        if activation_key is None:
            activation_key = self.activation_key

        if lce:
            result = self.client.register_contenthost(
                self.org['name'],
                lce='{0}/{1}'.format(
                    self.hosts_env['name'], self.content_view['name']),
                auto_attach=auto_attach
            )
        else:
            result = self.client.register_contenthost(
                self.org['name'],
                activation_key=activation_key['name'],
            )
            if auto_attach and self.client.subscribed:
                result = self.client.run('subscription-manager attach --auto')

        if self.client.subscribed and enable_repo:
            self.client.enable_repo(self.repository_id)

        return result

    def _client_enable_repo(self):
        """Enable the client default repository"""
        result = self.client.run(
            'subscription-manager repos --enable {0}'
            .format(self.repository_id)
        )
        return result

    def _make_activation_key(self, add_subscription=False):
        """Create a new activation key

        :param add_subscription: boolean to indicate whether to add the default
            subscription to the created activation key
        :return: the created activation key
        """
        activation_key = make_activation_key({
            'organization-id': self.org['id'],
            'content-view-id': self.content_view['id'],
            'lifecycle-environment-id': self.hosts_env['id'],
        })
        ActivationKey.update({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
            'auto-attach': 0,
        })
        if add_subscription:
            ActivationKey.add_subscription({
                'organization-id': self.org['id'],
                'id': activation_key['id'],
                'subscription-id': self.default_subscription_id
            })
        return activation_key

    def _host_subscription_register(self):
        """Register the subscription of client as a content host consumer"""
        Host.subscription_register({
            u'organization-id': self.org['id'],
            u'content-view-id': self.content_view['id'],
            u'lifecycle-environment-id': self.hosts_env['id'],
            u'name': self.client.hostname,
        })

    @tier3
    def test_positive_register(self):
        """Attempt to register a host

        :id: b1c601ee-4def-42ce-b353-fc2657237533

        :expectedresults: host successfully registered

        :CaseLevel: System
        """
        activation_key = self._make_activation_key(add_subscription=False)
        hosts = Host.list({
            'organization-id': self.org['id'],
            'search': self.client.hostname
        })
        self.assertEqual(len(hosts), 0)
        self._host_subscription_register()
        hosts = Host.list({
            'organization-id': self.org['id'],
            'search': self.client.hostname
        })
        self.assertGreater(len(hosts), 0)
        host = Host.info({'id': hosts[0]['id']})
        self.assertEqual(host['name'], self.client.hostname)
        # note: when not registered the following command lead to exception,
        # see unregister
        host_subscriptions = ActivationKey.subscriptions({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
            'host-id': host['id'],
        }, output_format='json')
        self.assertEqual(len(host_subscriptions), 0)

    @skip_if_bug_open('bugzilla', '1199515')
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
        Host.subscription_attach({
            'host-id': host['id'],
            'subscription-id': self.default_subscription_id
        })
        result = self._client_enable_repo()
        self.assertEqual(result.return_code, 0)
        # ensure that katello agent can be installed
        with self.assertNotRaises(VirtualMachineError):
            self.client.install_katello_agent()

    @skip_if_bug_open('bugzilla', '1199515')
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
        Host.subscription_attach({
            'host-id': host['id'],
            'subscription-id': self.default_subscription_id
        })
        result = self._client_enable_repo()
        self.assertEqual(result.return_code, 0)
        # ensure that katello agent can be installed
        with self.assertNotRaises(VirtualMachineError):
            self.client.install_katello_agent()

    @tier3
    def test_negative_without_attach(self):
        """Attempt to enable a repository of a subscription that was not
        attached to a host

        :id: 54a2c95f-be08-4353-a96c-4bc4d96ad03d

        :expectedresults: repository not enabled on host

        :CaseLevel: System
        """
        activation_key = self._make_activation_key(add_subscription=False)
        self._host_subscription_register()
        self._register_client(activation_key=activation_key, auto_attach=True)
        self.assertTrue(self.client.subscribed)
        result = self._client_enable_repo()
        self.assertNotEqual(result.return_code, 0)

    @tier3
    def test_negative_without_attach_with_lce(self):
        """Attempt to enable a repository of a subscription that was not
        attached to a host

        :id: fc469e70-a7cb-4fca-b0ea-3c9e3dfff849

        :expectedresults: repository not enabled on host

        :CaseLevel: System
        """
        self._register_client(lce=True, auto_attach=True)
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
        host_subscriptions = ActivationKey.subscriptions({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
            'host-id': host['id'],
        }, output_format='json')
        self.assertNotIn(self.subscription_name,
                         [sub['name'] for sub in host_subscriptions])
        self._register_client(activation_key=activation_key)
        Host.subscription_attach({
            'host-id': host['id'],
            'subscription-id': self.default_subscription_id
        })
        host_subscriptions = ActivationKey.subscriptions({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
            'host-id': host['id'],
        }, output_format='json')
        self.assertIn(self.subscription_name,
                      [sub['name'] for sub in host_subscriptions])
        Host.subscription_remove({
            'host-id': host['id'],
            'subscription-id': self.default_subscription_id
        })
        host_subscriptions = ActivationKey.subscriptions({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
            'host-id': host['id'],
        }, output_format='json')
        self.assertNotIn(self.subscription_name,
                         [sub['name'] for sub in host_subscriptions])

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
        self._register_client(
            activation_key=activation_key, enable_repo=True, auto_attach=True)
        self.assertTrue(self.client.subscribed)
        host = Host.info({'name': self.client.hostname})
        host_subscriptions = ActivationKey.subscriptions({
            'organization-id': self.org['id'],
            'id': activation_key['id'],
            'host-id': host['id'],
        }, output_format='json')
        self.assertGreater(len(host_subscriptions), 0)
        Host.subscription_unregister({'host': self.client.hostname})
        with self.assertRaises(CLIReturnCodeError):
            # raise error that the host was not registered by
            # subscription-manager register
            ActivationKey.subscriptions({
                'organization-id': self.org['id'],
                'id': activation_key['id'],
                'host-id': host['id'],
            })


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
