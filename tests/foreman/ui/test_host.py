# -*- encoding: utf-8 -*-
"""Test class for Hosts UI

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import six

from fauxfactory import gen_string
from nailgun import entities, entity_mixins
from time import sleep

from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo import manifests
from robottelo.cleanup import host_cleanup
from robottelo.cli.contentview import ContentView as cli_ContentView
from robottelo.cli.proxy import Proxy as cli_Proxy
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    DEFAULT_CV,
    DEFAULT_LOC,
    DEFAULT_PTABLE,
    ENVIRONMENT,
    PRDS,
    REPOS,
    REPOSET,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
)
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier2,
    tier3,
    upgrade,
)
from robottelo.decorators.host import skip_if_os
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_host,
    make_hostgroup,
    make_loc,
    make_org,
    set_context,
)
from robottelo.ui.base import UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session

import robottelo.cli.factory as cli_factory


class LibvirtHostTestCase(UITestCase):
    """Implements Libvirt Host tests in UI"""

    @classmethod
    @skip_if_not_set('vlan_networking', 'compute_resources')
    def setUpClass(cls):
        """Steps required to create a real host on libvirt

        1. Creates new Organization and Location.
        2. Search 'Kickstart default' partition table and OS along with
            provisioning/PXE templates.
        3. Associates org, location and OS with provisioning and PXE templates
        4. Search for x86_64 architecture
        5. Associate arch, partition table, provisioning/PXE templates with OS
        6. Find and specify proper Repo URL for OS distribution folder
        7. Creates new life-cycle environment.
        8. Creates new product and OS custom repository.
        9. Creates new content-view and associate with created repository.
        10. Publish and promote the content-view to next environment.
        11. Search for puppet environment and associate location.
        12. Search for smart-proxy and associate organization/location.
        13. Search for existing domain or create new otherwise. Associate org,
            location and dns proxy.
        14. Search for '192.168.100.0' network and associate org, location,
            dns/dhcp/tftp proxy, and if its not there then creates new.
        15. Search for existing compute-resource with 'libvirt' provider and
            associate org.location, and if its not there then creates new.
        16. Create new host group with all required entities

        """
        super(LibvirtHostTestCase, cls).setUpClass()
        # Create a new Organization and Location
        cls.org_ = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = cls.org_.name
        cls.loc = entities.Location(
            name=gen_string('alpha'),
            organization=[cls.org_]
        ).create()
        cls.loc_name = cls.loc.name

        # Get the Partition table ID
        cls.ptable = entities.PartitionTable().search(
            query={
                u'search': u'name="{0}"'.format(DEFAULT_PTABLE)
            }
        )[0]

        # Get the OS ID
        cls.os = entities.OperatingSystem().search(query={
            u'search': u'name="RedHat" AND (major="{0}" OR major="{1}")'
                       .format(RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
        })[0]

        # Get the templates and update with OS, Org, Location
        cls.templates = []
        for template_name in [
            'Kickstart default PXELinux',
            'Discovery Red Hat kexec',
            'Kickstart default iPXE',
            'Satellite Kickstart Default',
            'Satellite Kickstart Default Finish',
            'Satellite Kickstart Default User Data'
        ]:
            template = entities.ConfigTemplate().search(
                query={
                    u'search': u'name="{}"'.format(template_name)
                }
            )[0]
            template.operatingsystem = [cls.os]
            template.organization = [cls.org_]
            template.location = [cls.loc]
            template = template.update([
                'location',
                'operatingsystem',
                'organization'
            ])
            cls.templates.append(template)

        # Get the arch ID
        cls.arch = entities.Architecture().search(
            query={u'search': u'name="x86_64"'}
        )[0]

        # Update the OS to associate arch, ptable, templates
        cls.os.architecture = [cls.arch]
        cls.os.ptable = [cls.ptable]
        cls.os.config_template = cls.templates
        cls.os = cls.os.update([
            'architecture',
            'config_template',
            'ptable',
        ])

        # Check what OS was found to use correct media
        if cls.os.major == str(RHEL_6_MAJOR_VERSION):
            os_distr_url = settings.rhel6_os
        elif cls.os.major == str(RHEL_7_MAJOR_VERSION):
            os_distr_url = settings.rhel7_os
        else:
            raise ValueError('Proposed RHEL version is not supported')

        # Create a new Life-Cycle environment
        cls.lc_env = entities.LifecycleEnvironment(
            name=gen_string('alpha'),
            organization=cls.org_
        ).create()

        # Create a Product and Repository for OS distribution content
        cls.product = entities.Product(
            name=gen_string('alpha'),
            organization=cls.org_
        ).create()
        cls.repo = entities.Repository(
            name=gen_string('alpha'),
            product=cls.product,
            url=os_distr_url
        ).create()

        # Increased timeout value for repo sync
        cls.old_task_timeout = entity_mixins.TASK_TIMEOUT
        entity_mixins.TASK_TIMEOUT = 3600
        cls.repo.sync()

        # Create, Publish and promote CV
        cls.content_view = entities.ContentView(
            name=gen_string('alpha'),
            organization=cls.org_
        ).create()
        cls.content_view.repository = [cls.repo]
        cls.content_view = cls.content_view.update(['repository'])
        cls.content_view.publish()
        cls.content_view = cls.content_view.read()
        promote(cls.content_view.version[0], cls.lc_env.id)
        entity_mixins.TASK_TIMEOUT = cls.old_task_timeout
        # Search for puppet environment and associate location
        cls.environment = entities.Environment(
            organization=[cls.org_.id]).search()[0]
        cls.environment.location = [cls.loc]
        cls.environment = cls.environment.update(['location'])

        # Search for SmartProxy, and associate organization/location
        cls.proxy = entities.SmartProxy().search(
            query={
                u'search': u'name={0}'.format(
                    settings.server.hostname
                )
            }
        )[0]
        cls.proxy.location = [cls.loc]
        cls.proxy = cls.proxy.update(['location'])
        cls.proxy.organization = [cls.org_]
        cls.proxy = cls.proxy.update(['organization'])

        # Search for existing domain or create new otherwise. Associate org,
        # location and dns to it
        _, _, domain = settings.server.hostname.partition('.')
        cls.domain = entities.Domain().search(
            query={
                u'search': u'name="{0}"'.format(domain)
            }
        )
        if len(cls.domain) == 1:
            cls.domain = cls.domain[0].read()
            cls.domain.location.append(cls.loc)
            cls.domain.organization.append(cls.org_)
            cls.domain.dns = cls.proxy
            cls.domain = cls.domain.update(['dns', 'location', 'organization'])
        else:
            cls.domain = entities.Domain(
                dns=cls.proxy,
                location=[cls.loc],
                organization=[cls.org_],
            ).create()
        cls.domain_name = cls.domain.name

        # Search if subnet is defined with given network.
        # If so, just update its relevant fields otherwise,
        # Create new subnet
        network = settings.vlan_networking.subnet
        cls.subnet = entities.Subnet().search(
            query={u'search': u'network={0}'.format(network)}
        )
        if len(cls.subnet) == 1:
            cls.subnet = cls.subnet[0]
            cls.subnet.domain = [cls.domain]
            cls.subnet.location = [cls.loc]
            cls.subnet.organization = [cls.org_]
            cls.subnet.dns = cls.proxy
            cls.subnet.dhcp = cls.proxy
            cls.subnet.ipam = 'DHCP'
            cls.subnet.tftp = cls.proxy
            cls.subnet.discovery = cls.proxy
            cls.subnet = cls.subnet.update([
                'domain',
                'discovery',
                'dhcp',
                'dns',
                'ipam',
                'location',
                'organization',
                'tftp',
            ])
        else:
            # Create new subnet
            cls.subnet = entities.Subnet(
                name=gen_string('alpha'),
                network=network,
                mask=settings.vlan_networking.netmask,
                domain=[cls.domain],
                ipam='DHCP',
                location=[cls.loc],
                organization=[cls.org_],
                dns=cls.proxy,
                dhcp=cls.proxy,
                tftp=cls.proxy,
                discovery=cls.proxy
            ).create()

        # Search if Libvirt compute-resource already exists
        # If so, just update its relevant fields otherwise,
        # Create new compute-resource with 'libvirt' provider.
        resource_url = u'qemu+ssh://root@{0}/system'.format(
            settings.compute_resources.libvirt_hostname
        )
        comp_res = [
            res for res in entities.LibvirtComputeResource().search()
            if res.provider == 'Libvirt' and res.url == resource_url
        ]
        if len(comp_res) >= 1:
            cls.computeresource = entities.LibvirtComputeResource(
                id=comp_res[0].id).read()
            cls.computeresource.location.append(cls.loc)
            cls.computeresource.organization.append(cls.org_)
            cls.computeresource = cls.computeresource.update([
                'location', 'organization'])
        else:
            # Create Libvirt compute-resource
            cls.computeresource = entities.LibvirtComputeResource(
                name=gen_string('alpha'),
                provider=u'libvirt',
                url=resource_url,
                set_console_password=False,
                display_type=u'VNC',
                location=[cls.loc.id],
                organization=[cls.org_.id],
            ).create()

        cls.resource = u'{0} (Libvirt)'.format(cls.computeresource.name)

        cls.puppet_env = entities.Environment(
            location=[cls.loc],
            organization=[cls.org_],
        ).create(True)

        cls.root_pwd = gen_string('alpha', 15)

        # Create Hostgroup
        cls.host_group = entities.HostGroup(
            architecture=cls.arch,
            domain=cls.domain.id,
            subnet=cls.subnet.id,
            lifecycle_environment=cls.lc_env.id,
            content_view=cls.content_view.id,
            location=[cls.loc.id],
            name=gen_string('alpha'),
            environment=cls.environment.id,
            puppet_proxy=cls.proxy,
            puppet_ca_proxy=cls.proxy,
            content_source=cls.proxy,
            operatingsystem=cls.os.id,
            organization=[cls.org_.id],
            ptable=cls.ptable.id,
        ).create()

    @run_only_on('sat')
    @tier3
    def test_positive_provision_end_to_end(self):
        """Provision Host on libvirt compute resource

        :id: 2678f95f-0c0e-4b46-a3c1-3f9a954d3bde

        :expectedresults: Host is provisioned successfully

        :CaseLevel: System
        """
        hostname = gen_string('numeric')
        with Session(self) as session:
            make_host(
                session,
                name=hostname,
                org=self.org_name,
                parameters_list=[
                    ['Host', 'Organization', self.org_name],
                    ['Host', 'Location', self.loc_name],
                    ['Host', 'Host group', self.host_group.name],
                    ['Host', 'Deploy on', self.resource],
                    ['Host', 'Puppet Environment', self.puppet_env.name],
                    ['Virtual Machine', 'Memory', '1 GB'],
                    ['Operating System', 'Root password', self.root_pwd],
                ],
                interface_parameters=[
                    ['Network type', 'Physical (Bridge)'],
                    ['Network', settings.vlan_networking.bridge],
                ],
            )
            name = u'{0}.{1}'.format(hostname, self.domain_name)
            self.assertIsNotNone(self.hosts.search(name))
            self.addCleanup(host_cleanup, entities.Host().search(
                query={'search': 'name={}'.format(name)})[0].id)
            for _ in range(25):
                result = self.hosts.get_host_properties(name, ['Build'])
                if result['Build'] == 'Pending installation':
                    sleep(30)
                else:
                    break
            self.assertEqual(result['Build'], 'Installed')

    @run_only_on('sat')
    @tier3
    def test_positive_delete_libvirt(self):
        """Create a new Host on libvirt compute resource and delete it
        afterwards

        :id: 6a9175e7-bb96-4de3-bc45-ba6c10dd14a4

        :expectedresults: Proper warning message is displayed on delete attempt
            and host deleted successfully afterwards

        :BZ: 1243223

        :CaseLevel: System
        """
        hostname = gen_string('alpha').lower()
        with Session(self) as session:
            make_host(
                session,
                name=hostname,
                org=self.org_name,
                parameters_list=[
                    ['Host', 'Organization', self.org_name],
                    ['Host', 'Location', self.loc_name],
                    ['Host', 'Host group', self.host_group.name],
                    ['Host', 'Deploy on', self.resource],
                    ['Host', 'Puppet Environment', self.puppet_env.name],
                    ['Virtual Machine', 'Memory', '1 GB'],
                    ['Operating System', 'Root password', self.root_pwd],
                ],
                interface_parameters=[
                    ['Network type', 'Physical (Bridge)'],
                    ['Network', settings.vlan_networking.bridge],
                ],
            )
            name = u'{0}.{1}'.format(hostname, self.domain_name)
            self.assertIsNotNone(self.hosts.search(name))
            self.hosts.click(common_locators['select_action_dropdown'] % name)
            self.hosts.click(
                common_locators['delete_button'] % name,
                wait_for_ajax=False
            )
            text = self.hosts.get_alert_text()
            self.assertIn(
                'This will delete the virtual machine and its disks, and is '
                'irreversible.',
                text
            )
            self.hosts.handle_alert(True)
            self.hosts.wait_for_ajax()
            self.assertIsNone(self.hosts.search(name))


class HostTestCase(UITestCase):
    """Implements Host tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_baremetal_with_bios(self):
        """Create a new Host AR from provided MAC address

        :id: 2cedc634-7761-4326-b77a-b999098f5c00

        :setup: Create a PXE-based VM with BIOS boot mode (outside of
            Satellite).

        :steps: Create a new host using 'BareMetal' option and MAC address of
            the pre-created VM

        :expectedresults: Host AR is created, TFTP files are deployed

        :caseautomation: notautomated

        :caselevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    @upgrade
    def test_positive_create_baremetal_with_uefi(self):
        """Create a new Host AR from provided MAC address

        :id: ec62e90b-1b2a-4eac-8b15-7e36c8179086

        :setup: Create a PXE-based VM with UEFI boot mode (outside of
            Satellite).

        :steps: Create a new host using 'BareMetal' option and MAC address of
            the pre-created VM

        :expectedresults: Host AR is created, TFTP files are deployed

        :caseautomation: notautomated

        :caselevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_create_with_incompatible_pxe_loader(self):
        """Try to create host with a known OS and incompatible PXE loader

        :id: c45391d2-c244-4b64-a956-4a329f687a4b

        :Setup:
          1. Synchronize RHEL[5,6,7] kickstart repos

        :Steps:
          1. create a new RHEL host using 'BareMetal' option and the following
             OS-PXE_loader combinations:

            1.1 RHEL5,6 - GRUB2_UEFI
            1.2 RHEL5,6 - GRUB2_UEFI_SB
            1.3 RHEL7 - GRUB_UEFI
            1.4 RHEL7 - GRUB_UEFI_SB

        :expectedresults:
          1. Warning message appears
          2. Files not deployed on TFTP
          3. Host not created

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier3
    def test_positive_create(self):
        """Create a new Host

        :id: 4821444d-3c86-4f93-849b-60460e025ba0

        :expectedresults: Host is created

        :CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self) as session:
            make_host(
                session,
                name=host.name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name
                    ],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            # confirm the Host appears in the UI
            search = self.hosts.search(
                u'{0}.{1}'.format(host.name, host.domain.name)
            )
            self.assertIsNotNone(search)

    @tier3
    def test_positive_create_with_inherited_params(self):
        """Create a new Host in organization and location with parameters

        :BZ: 1287223

        :id: 628122f2-bda9-4aa1-8833-55debbd99072

        :expectedresults: Host has inherited parameters from organization and
            location

        :CaseImportance: High
        """
        org_name = gen_string('alphanumeric')
        loc_name = gen_string('alphanumeric')
        org_param_name = gen_string('alphanumeric')
        loc_param_name = gen_string('alphanumeric')
        org_param_value = gen_string('alphanumeric')
        loc_param_value = gen_string('alphanumeric')
        with Session(self) as session:
            make_org(
                session,
                org_name=org_name,
                params=[(org_param_name, org_param_value)],
            )
            session.nav.go_to_select_org(org_name)
            make_loc(
                session,
                name=loc_name,
                params=[(loc_param_name, loc_param_value)],
            )
            session.nav.go_to_select_loc(loc_name)
            org = entities.Organization().search(
                query={'search': 'name={}'.format(org_name)})[0]
            loc = entities.Location().search(
                query={'search': 'name={}'.format(loc_name)})[0]
            host = entities.Host(
                location=loc,
                organization=org,
            )
            host.create_missing()
            os_name = u'{0} {1}'.format(
                host.operatingsystem.name, host.operatingsystem.major)
            make_host(
                session,
                name=host.name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name
                    ],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            actual_params = self.hosts.fetch_global_parameters(
                host.name, host.domain.name)
            self.assertEqual(len(actual_params), 2)
            self.assertEqual(
                {(org_param_name, org_param_value),
                 (loc_param_name, loc_param_value)},
                set(actual_params)
            )

    @run_only_on('sat')
    @tier3
    def test_negative_delete_primary_interface(self):
        """Attempt to delete primary interface of a host

        :id: bc747e2c-38d9-4920-b4ae-6010851f704e

        :BZ: 1417119

        :expectedresults: Interface was not deleted

        :CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        interface_id = gen_string('alpha')
        with Session(self) as session:
            make_host(
                session,
                name=host.name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name
                    ],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['Device Identifier', interface_id],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            host_el = self.hosts.search(
                u'{0}.{1}'.format(host.name, host.domain.name)
            )
            self.assertIsNotNone(host_el)
            self.hosts.click(host_el)
            self.hosts.click(locators['host.edit'])
            self.hosts.click(tab_locators['host.tab_interfaces'])
            delete_button = self.hosts.wait_until_element(
                locators['host.delete_interface'] % interface_id)
            # Verify the button is disabled
            self.assertFalse(delete_button.is_enabled())
            self.assertEqual(delete_button.get_attribute('disabled'), 'true')
            # Attempt to delete the interface
            self.hosts.delete_interface(
                host.name, host.domain.name, interface_id)
            # Verify interface wasn't deleted by fetching one of its parameters
            # (e.g., MAC address)
            results = self.hosts.fetch_host_parameters(
                host.name,
                host.domain.name,
                [['Interfaces', 'Primary Interface MAC']],
            )
            self.assertEqual(results['Primary Interface MAC'], host.mac)

    @tier3
    def test_positive_remove_parameter_non_admin_user(self):
        """Remove a host parameter as a non-admin user with enough permissions

        :id: 598111c1-fdb6-42e9-8c28-fae999b5d112

        :expectedresults: user with sufficient permissions may remove host
            parameter

        :CaseLevel: System
        """
        user_login = gen_string('alpha')
        user_password = gen_string('alpha')
        param_name = gen_string('alpha')
        default_loc = entities.Location().search(
            query={'search': 'name="{0}"'.format(DEFAULT_LOC)})[0]
        role = entities.Role().create()
        entities.Filter(
            permission=entities.Permission(resource_type='Parameter').search(),
            role=role,
        ).create()
        entities.Filter(
            permission=entities.Permission(resource_type='Host').search(),
            role=role,
        ).create()
        entities.User(
            role=[role],
            admin=False,
            login=user_login,
            password=user_password,
            organization=[self.session_org],
            location=[default_loc],
            default_organization=self.session_org,
        ).create()
        host = entities.Host(
            location=default_loc,
            organization=self.session_org,
            host_parameters_attributes=[
                {'name': param_name, 'value': gen_string('alpha')}
            ],
        ).create()
        with Session(self, user=user_login, password=user_password):
            self.hosts.search_and_click(host.name)
            self.hosts.click(locators['host.edit'])
            self.hosts.remove_parameter(param_name)
            self.hosts.click(locators['host.edit'])
            self.assertIsNone(self.hosts.get_parameter(param_name))

    @tier3
    def test_negative_remove_parameter_non_admin_user(self):
        """Attempt to remove host parameter as a non-admin user with
        insufficient permissions

        :BZ: 1317868

        :id: 78fd230e-2ec4-4158-823b-ddbadd5e232f

        :expectedresults: user with insufficient permissions is unable to
            remove host parameter, 'Remove' link is not visible for him

        :CaseLevel: System
        """
        user_login = gen_string('alpha')
        user_password = gen_string('alpha')
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        default_loc = entities.Location().search(
            query={'search': 'name="{0}"'.format(DEFAULT_LOC)})[0]
        role = entities.Role().create()
        entities.Filter(
            permission=entities.Permission(name='view_params').search(),
            role=role,
        ).create()
        entities.Filter(
            permission=entities.Permission(resource_type='Host').search(),
            role=role,
        ).create()
        entities.User(
            role=[role],
            admin=False,
            login=user_login,
            password=user_password,
            organization=[self.session_org],
            location=[default_loc],
            default_organization=self.session_org,
        ).create()
        host = entities.Host(
            location=default_loc,
            organization=self.session_org,
            host_parameters_attributes=[
                {'name': param_name, 'value': param_value}
            ],
        ).create()
        with Session(self, user=user_login, password=user_password):
            self.hosts.search_and_click(host.name)
            self.hosts.click(locators['host.edit'])
            self.assertEqual(self.hosts.get_parameter(param_name), param_value)
            with self.assertRaises(UINoSuchElementError):
                self.hosts.remove_parameter(param_name)

    @run_only_on('sat')
    @tier3
    def test_positive_update_name(self):
        """Create a new Host and update its name to valid one

        :id: f1c19599-f613-431d-bf09-62addec1e60b

        :expectedresults: Host is updated successfully

        :CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        host_name = host.name
        with Session(self) as session:
            make_host(
                session,
                name=host_name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            # confirm the Host appears in the UI
            search = self.hosts.search(
                u'{0}.{1}'.format(host_name, host.domain.name)
            )
            self.assertIsNotNone(search)
            new_name = gen_string('alpha')
            self.hosts.update(host_name, host.domain.name, new_name)
            new_host_name = (
                u'{0}.{1}'.format(new_name, host.domain.name)).lower()
            self.assertIsNotNone(self.hosts.search(new_host_name))
            self.hostname = new_name

    @run_only_on('sat')
    @tier3
    def test_positive_update_name_with_prefix(self):
        """Create a new Host and update its name to valid one. Host should
        contain word 'new' in its name

        :id: b08cb5c9-bd2c-4dc7-97b1-d1f20d1373d7

        :expectedresults: Host is updated successfully

        :BZ: 1419161

        :CaseLevel: System
        """
        current_name = 'new{0}'.format(gen_string('alpha'), 6).lower()
        new_name = 'new{0}'.format(gen_string('alpha')).lower()
        host = entities.Host(name=current_name)
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self) as session:
            make_host(
                session,
                name=current_name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            # confirm the Host appears in the UI
            search = self.hosts.search(
                u'{0}.{1}'.format(current_name, host.domain.name)
            )
            self.assertIsNotNone(search)
            self.hosts.update(current_name, host.domain.name, new_name)
            new_host_name = (
                u'{0}.{1}'.format(new_name, host.domain.name)).lower()
            self.assertIsNotNone(self.hosts.search(new_host_name))

    @run_only_on('sat')
    @tier3
    @upgrade
    def test_positive_delete(self):
        """Delete a Host

        :id: 13735af1-f1c7-466e-a969-80618a1d854d

        :expectedresults: Host is delete

        :CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self) as session:
            make_host(
                session,
                name=host.name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name
                    ],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            # Delete host
            self.hosts.delete(
                u'{0}.{1}'.format(host.name, host.domain.name),
                dropdown_present=True
            )

    @run_only_on('sat')
    @tier2
    def test_positive_search_by_parameter(self):
        """Search for the host by global parameter assigned to it

        :id: 8e61127c-d0a0-4a46-a3c6-22d3b2c5457c

        :expectedresults: Only one specific host is returned by search

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        parameters = [{'name': param_name, 'value': param_value}]
        param_host = entities.Host(
            organization=org,
            host_parameters_attributes=parameters,
        ).create()
        additional_host = entities.Host(organization=org).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            # Check that hosts present in the system
            for host in [param_host, additional_host]:
                self.assertIsNotNone(self.hosts.search(host.name))
            # Check that search by parameter returns only one host in the list
            self.assertIsNotNone(
                self.hosts.search(
                    param_host.name,
                    _raw_query='params.{0} = {1}'.format(
                        param_name, param_value)
                )
            )
            strategy, value = locators['host.select_name']
            self.assertIsNone(self.hosts.wait_until_element(
                (strategy, value % additional_host.name)))

    @run_only_on('sat')
    @tier2
    def test_positive_search_by_parameter_with_different_values(self):
        """Search for the host by global parameter assigned to it by its value

        :id: c3a4551e-d759-4a9d-ba90-8db4cab3db2c

        :expectedresults: Only one specific host is returned by search

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        name = gen_string('alpha')
        param_values = [gen_string('alpha'), gen_string('alphanumeric')]
        hosts = [
            entities.Host(
                organization=org,
                host_parameters_attributes=[{'name': name, 'value': value}]
            ).create()
            for value in param_values
        ]
        with Session(self) as session:
            set_context(session, org=org.name)
            # Check that hosts present in the system
            for host in hosts:
                self.assertIsNotNone(self.hosts.search(host.name))
            # Check that search by parameter returns only one host in the list
            strategy, value = locators['host.select_name']
            for i in range(2):
                self.assertIsNotNone(
                    self.hosts.search(
                        hosts[i].name,
                        _raw_query='params.{0} = {1}'.format(
                            name, param_values[i])
                    )
                )
                self.assertIsNone(self.hosts.wait_until_element(
                    (strategy, value % hosts[-i-1])))

    @run_only_on('sat')
    @tier2
    def test_positive_search_by_parameter_with_prefix(self):
        """Search by global parameter assigned to host using prefix 'not' and
        any random string as parameter value to make sure that all hosts will
        be present in the list

        :id: a4affb90-1222-4d9a-94be-213f9e5be573

        :expectedresults: All assigned hosts to organization are returned by
            search

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        parameters = [{'name': param_name, 'value': param_value}]
        param_host = entities.Host(
            organization=org,
            host_parameters_attributes=parameters,
        ).create()
        additional_host = entities.Host(organization=org).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            # Check that hosts present in the system
            for host in [param_host, additional_host]:
                self.assertIsNotNone(self.hosts.search(host.name))
            # Check that search by parameter with 'not' prefix returns both
            # hosts in the list
            self.assertIsNotNone(
                self.hosts.search(
                    param_host.name,
                    _raw_query='not params.{0} = {1}'.format(
                        param_name, gen_string('alphanumeric'))
                )
            )
            strategy, value = locators['host.select_name']
            self.assertIsNotNone(self.hosts.wait_until_element(
                (strategy, value % additional_host.name)))

    @run_only_on('sat')
    @tier2
    def test_positive_search_by_parameter_with_operator(self):
        """Search by global parameter assigned to host using operator '<>' and
        any random string as parameter value to make sure that all hosts will
        be present in the list

        :id: 264065b7-0d04-467d-887a-0aba0d871b7c

        :expectedresults: All assigned hosts to organization are returned by
            search

        :BZ: 1463806

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        param_global_value = gen_string('numeric')
        entities.CommonParameter(
            name=param_name,
            value=param_global_value
        ).create()
        parameters = [{'name': param_name, 'value': param_value}]
        param_host = entities.Host(
            organization=org,
            host_parameters_attributes=parameters,
        ).create()
        additional_host = entities.Host(organization=org).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            # Check that hosts present in the system
            for host in [param_host, additional_host]:
                self.assertIsNotNone(self.hosts.search(host.name))
            # Check that search by parameter with '<>' operator returns both
            # hosts in the list
            self.assertIsNotNone(
                self.hosts.search(
                    param_host.name,
                    _raw_query='params.{0} <> {1}'.format(
                        param_name, gen_string('alphanumeric'))
                )
            )
            strategy, value = locators['host.select_name']
            self.assertIsNotNone(self.hosts.wait_until_element(
                (strategy, value % additional_host.name)))

    @run_only_on('sat')
    @tier2
    def test_positive_search_with_org_and_loc_context(self):
        """Perform usual search for host, but organization and location used
        for host create procedure should have 'All capsules' checkbox selected

        :id: 2ce50df0-2b30-42cc-a40b-0e1f4fde3c6f

        :expectedresults: Search functionality works as expected and correct
            result is returned

        :BZ: 1405496

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        loc = entities.Location().create()
        host = entities.Host(organization=org, location=loc).create()
        with Session(self) as session:
            self.org.update(org.name, all_capsules=True)
            self.location.update(loc.name, all_capsules=True)
            set_context(session, org=org.name, loc=loc.name)
            # Check that host present in the system
            self.assertIsNotNone(self.hosts.search(host.name))
            self.assertIsNotNone(
                self.hosts.search(host.name, _raw_query=host.name))

    @tier2
    def test_positive_search_by_org(self):
        """Search for host by specifying host's organization name

        :id: a3bb5bc5-cb9c-4b56-b383-f3e4d3d4d222

        :expectedresults: Search functionality works as expected and correct
            result is returned

        :BZ: 1447958

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        with Session(self) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            self.assertIsNotNone(
                self.hosts.search(
                    host.name,
                    _raw_query='organization = {}'.format(
                        host.organization.read().name)
                )
            )

    @run_only_on('sat')
    @tier2
    def test_positive_sort_by_name(self):
        """Create some Host entities and sort them by name ascendingly and then
        descendingly

        :id: 12f75ef9-23e6-48be-80ed-b354e8ac212b

        :expectedresults: Host entities are sorted properly

        :CaseImportance: High

        :BZ: 1268085

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        name_list = [gen_string('alpha', 20).lower() for _ in range(5)]
        host = entities.Host(organization=org)
        host.create_missing()
        for name in name_list:
            entities.Host(
                name=name,
                organization=org,
                architecture=host.architecture,
                domain=host.domain,
                environment=host.environment,
                location=host.location,
                mac=host.mac,
                medium=host.medium,
                operatingsystem=host.operatingsystem,
                ptable=host.ptable,
                root_pass=host.root_pass,
            ).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.hosts.navigate_to_entity()
            sorted_list_asc = self.hosts.sort_table_by_column('Name')
            self.assertEqual(
                [el.split('.', 1)[0] for el in sorted_list_asc],
                sorted(name_list)
            )
            sorted_list_desc = self.hosts.sort_table_by_column('Name')
            self.assertEqual(
                [el.split('.', 1)[0] for el in sorted_list_desc],
                sorted(name_list, reverse=True)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_sort_by_os(self):
        """Create some Host entities and sort them by operation system
        ascendingly and then descendingly

        :id: 617e812d-258e-4ba4-8a9a-d7d02f2fb405

        :expectedresults: Host entities are sorted properly

        :CaseImportance: High

        :BZ: 1268085

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        name_list = [gen_string('alpha', 20) for _ in range(5)]
        host = entities.Host(organization=org)
        host.create_missing()
        for name in name_list:
            os = entities.OperatingSystem(name=name).create()
            entities.Host(
                organization=org,
                architecture=host.architecture,
                domain=host.domain,
                environment=host.environment,
                location=host.location,
                mac=host.mac,
                medium=host.medium,
                operatingsystem=os,
                ptable=host.ptable,
                root_pass=host.root_pass,
            ).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.hosts.navigate_to_entity()
            sorted_list_asc = self.hosts.sort_table_by_column(
                'Operating system')
            self.assertEqual(
                [el.split(' ', 1)[0] for el in sorted_list_asc],
                sorted(name_list, key=six.text_type.lower)
            )
            sorted_list_desc = self.hosts.sort_table_by_column(
                'Operating system')
            self.assertEqual(
                [el.split(' ', 1)[0] for el in sorted_list_desc],
                sorted(name_list, key=six.text_type.lower, reverse=True)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_sort_by_env(self):
        """Create some Host entities and sort them by environment
        ascendingly and then descendingly

        :id: 8a1e8d6d-dc5f-4b78-9844-80355452c979

        :expectedresults: Host entities are sorted properly

        :CaseImportance: High

        :BZ: 1268085

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        name_list = [gen_string('alpha', 20) for _ in range(5)]
        host = entities.Host(organization=org)
        host.create_missing()
        for name in name_list:
            env = entities.Environment(name=name).create()
            entities.Host(
                organization=org,
                architecture=host.architecture,
                domain=host.domain,
                environment=env,
                location=host.location,
                mac=host.mac,
                medium=host.medium,
                operatingsystem=host.operatingsystem,
                ptable=host.ptable,
                root_pass=host.root_pass,
            ).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.hosts.navigate_to_entity()
            self.assertEqual(
                self.hosts.sort_table_by_column('Environment'),
                sorted(name_list, key=six.text_type.lower)
            )
            self.assertEqual(
                self.hosts.sort_table_by_column('Environment'),
                sorted(name_list, key=six.text_type.lower, reverse=True)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_sort_by_model(self):
        """Create some Host entities and sort them by hardware model
        ascendingly and then descendingly

        :id: 56853ffb-47b2-47ce-89c5-d295c16200c8

        :expectedresults: Host entities are sorted properly

        :CaseImportance: High

        :BZ: 1268085

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        name_list = [gen_string('alpha', 20) for _ in range(5)]
        host = entities.Host(organization=org)
        host.create_missing()
        for name in name_list:
            model = entities.Model(name=name).create()
            entities.Host(
                organization=org,
                architecture=host.architecture,
                domain=host.domain,
                environment=host.environment,
                location=host.location,
                mac=host.mac,
                medium=host.medium,
                operatingsystem=host.operatingsystem,
                ptable=host.ptable,
                root_pass=host.root_pass,
                model=model
            ).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.hosts.navigate_to_entity()
            self.assertEqual(
                self.hosts.sort_table_by_column('Model'),
                sorted(name_list, key=six.text_type.lower)
            )
            self.assertEqual(
                self.hosts.sort_table_by_column('Model'),
                sorted(name_list, key=six.text_type.lower, reverse=True)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_sort_by_hostgroup(self):
        """Create some Host entities and sort them by host group ascendingly
        and then descendingly

        :id: d1ac744a-ff76-4afe-84a1-3a7e4b3ca3f1

        :expectedresults: Host entities are sorted properly

        :CaseImportance: High

        :BZ: 1268085

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        name_list = [gen_string('alpha', 20) for _ in range(5)]
        host = entities.Host(organization=org)
        host.create_missing()
        for name in name_list:
            hg = entities.HostGroup(name=name, organization=[org]).create()
            entities.Host(
                hostgroup=hg,
                organization=org,
                architecture=host.architecture,
                domain=host.domain,
                environment=host.environment,
                location=host.location,
                mac=host.mac,
                medium=host.medium,
                operatingsystem=host.operatingsystem,
                ptable=host.ptable,
                root_pass=host.root_pass,
            ).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.hosts.navigate_to_entity()
            self.assertEqual(
                self.hosts.sort_table_by_column('Host group'),
                sorted(name_list, key=six.text_type.lower)
            )
            self.assertEqual(
                self.hosts.sort_table_by_column('Host group'),
                sorted(name_list, key=six.text_type.lower, reverse=True)
            )

    @tier2
    def test_positive_validate_inherited_cv_lce(self):
        """Create a host with hostgroup specified via CLI. Make sure host
        inherited hostgroup's lifecycle environment, content view and both
        fields are properly reflected via WebUI

        :id: c83f6819-2649-4a8b-bb1d-ce93b2243765

        :expectedresults: Host's lifecycle environment and content view match
            the ones specified in hostgroup

        :CaseLevel: Integration

        :BZ: 1391656
        """
        host = entities.Host()
        host.create_missing()

        new_lce = cli_factory.make_lifecycle_environment({
            'organization-id': host.organization.id})
        new_cv = cli_factory.make_content_view({
            'organization-id': host.organization.id})
        cli_ContentView.publish({'id': new_cv['id']})
        version_id = cli_ContentView.version_list({
            'content-view-id': new_cv['id'],
        })[0]['id']
        cli_ContentView.version_promote({
            'id': version_id,
            'to-lifecycle-environment-id': new_lce['id'],
            'organization-id': host.organization.id,
        })
        hostgroup = cli_factory.make_hostgroup({
            'content-view-id': new_cv['id'],
            'lifecycle-environment-id': new_lce['id'],
            'organization-ids': host.organization.id,
        })
        puppet_proxy = cli_Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]

        cli_factory.make_host({
            'architecture-id': host.architecture.id,
            'domain-id': host.domain.id,
            'environment-id': host.environment.id,
            'hostgroup-id': hostgroup['id'],
            'location-id': host.location.id,
            'medium-id': host.medium.id,
            'name': host.name,
            'operatingsystem-id': host.operatingsystem.id,
            'organization-id': host.organization.id,
            'partition-table-id': host.ptable.id,
            'puppet-proxy-id': puppet_proxy['id'],
        })
        with Session(self) as session:
            set_context(session, host.organization.name, host.location.name)
            result = self.hosts.fetch_host_parameters(
                host.name,
                host.domain.name,
                [['Host', 'Lifecycle Environment'],
                 ['Host', 'Content View']],
            )
            self.assertEqual(result['Lifecycle Environment'], new_lce['name'])
            self.assertEqual(result['Content View'], new_cv['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_inherit_puppet_env_from_host_group_when_create(self):
        """Host group puppet environment is inherited to host in create
        procedure

        :id: 05831ecc-3132-4eb7-ad90-155470f331b6

        :expectedresults: Expected puppet environment is inherited to the form

        :BZ: 1414914

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        hg_name = gen_string('alpha')
        env = entities.Environment(
            name=gen_string('alpha'), organization=[org]).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            make_hostgroup(
                session,
                name=hg_name,
                parameters_list=[
                    ['Host Group', 'Puppet Environment', env.name],
                ],
            )
            self.assertIsNotNone(self.hostgroup.search(hg_name))
            self.hosts.navigate_to_entity()
            self.hosts.click(locators['host.new'])
            self.hosts.assign_value(locators['host.host_group'], hg_name)
            self.assertEqual(
                self.hosts.wait_until_element(
                    locators['host.fetch_puppet_environment']).text,
                env.name
            )
            self.hosts.click(locators['host.inherit_puppet_environment'])
            self.assertEqual(
                self.hosts.wait_until_element(
                    locators['host.fetch_puppet_environment']).text,
                env.name
            )

    @run_only_on('sat')
    @tier2
    def test_positive_inherit_puppet_env_from_host_group_when_action(self):
        """Host group puppet environment is inherited to already created
        host when corresponding action is applied to that host

        :id: 3f5af54e-e259-46ad-a2af-7dc1850891f5

        :expectedresults: Expected puppet environment is inherited to the host

        :BZ: 1414914

        :CaseLevel: Integration
        """
        host_name = gen_string('alpha').lower()
        org = entities.Organization().create()
        host = entities.Host(organization=org, name=host_name).create()
        env = entities.Environment(
            name=gen_string('alpha'), organization=[org]).create()
        hostgroup = entities.HostGroup(
            environment=env, organization=[org]).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.hosts.update_host_bulkactions(
                [host_name],
                action='Change Environment',
                parameters_list=[{
                    'puppet_env_name': '*Clear environment*',
                }],
            )
            self.assertEqual(
                self.hosts.wait_until_element(
                    common_locators['table_cell_value'] %
                    (host_name, 'Environment')).text,
                ''
            )
            self.hosts.update_host_bulkactions(
                [host_name],
                action='Change Group',
                parameters_list=[{'host_group_name': hostgroup.name}],
            )
            self.hosts.update_host_bulkactions(
                [host_name],
                action='Change Environment',
                parameters_list=[{
                    'puppet_env_name': '*Inherit from host group*',
                }],
            )
            self.assertEqual(
                self.hosts.wait_until_element(
                    common_locators['table_cell_value'] %
                    (host_name, 'Environment')).text,
                env.name
            )
            result = self.hosts.fetch_host_parameters(
                host_name,
                host.domain.read().name,
                [['Host', 'Puppet Environment']],
            )
            self.assertEqual(result['Puppet Environment'], env.name)

    @run_only_on('sat')
    @tier2
    def test_positive_reset_puppet_env_from_cv(self):
        """Content View puppet environment is inherited to host in create
        procedure and can be rolled back to its value at any moment using
        'Reset Puppet Environment to match selected Content View' button

        :id: f8f35bd9-9e7c-418f-837a-ccec21c05d59

        :expectedresults: Expected puppet environment is inherited to the field

        :BZ: 1336802

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        puppet_env = entities.Environment(
            name=gen_string('alpha'), organization=[org]).create()
        cv = entities.ContentView(organization=org).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.content_views.update(name=cv.name, force_puppet=True)
            self.content_views.publish(cv.name)
            published_puppet_env = [
                env
                for env in entities.Environment(organization=[org]).search()
                if cv.name in env.name
            ][0]
            self.hosts.navigate_to_entity()
            self.hosts.click(locators['host.new'])
            self.hosts.assign_value(
                locators['host.lifecycle_environment'], ENVIRONMENT)
            self.hosts.assign_value(locators['host.content_view'], cv.name)
            self.assertEqual(
                self.hosts.wait_until_element(
                    locators['host.fetch_puppet_environment']).text,
                published_puppet_env.name
            )
            self.hosts.assign_value(
                locators['host.puppet_environment'],
                puppet_env.name
            )
            self.hosts.click(locators['host.reset_puppet_environment'])
            self.assertEqual(
                self.hosts.wait_until_element(
                    locators['host.fetch_puppet_environment']).text,
                published_puppet_env.name
            )

    @stubbed()
    @tier3
    def test_positive_create_with_user(self):
        """Create Host with new user specified

        :id: b97d6fe5-b0a1-4ddc-8d7f-cbf7b17c823d

        :expectedresults: Host is created

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_update_with_user(self):
        """Update Host with new user specified

        :id: 4c030cf5-b89c-4dec-bb3e-0cb3215a2315

        :expectedresults: Host is updated

        :caseautomation: notautomated

        :CaseLevel: System
        """


class AtomicHostTestCase(UITestCase):
    """Implements Atomic Host tests in UI"""

    hostname = gen_string('numeric')

    @classmethod
    @skip_if_bug_open('bugzilla', 1414134)
    @skip_if_os('RHEL6')
    @skip_if_not_set('vlan_networking', 'compute_resources', 'ostree')
    def setUpClass(cls):
        """Steps required to create a Atomic host on libvirt

        1. Creates new Organization and Location.
        2. Creates new life-cycle environment.
        3. Creates new product and sync RH Atomic OSTree repository.
        4. Creates new content-view by associating RH Atomic repository.
        5. Publish and promote the content-view to next environment.
        6. Search for smart-proxy and associate location.
        7. Search for existing domain or create new otherwise. Associate org,
           location and dns proxy.
        8. Search for '192.168.100.0' network and associate org, location,
           dns/dhcp/tftp proxy, and if its not there then creates new.
        9. Search for existing compute-resource with 'libvirt' provider and
            associate org.location, and if its not there then creates
            new.
        10. Search 'Kickstart default' partition table and RH Atomic OS along
            with PXE templates.
        11. Associates org, location and OS with provisioning and PXE templates
        12. Search for x86_64 architecture
        13. Associate arch, partition table, provisioning/PXE templates with OS
        14. Search for existing Atomic media or create new otherwise and
            associate org/location
        15. Create new host group with all required entities
        """
        super(AtomicHostTestCase, cls).setUpClass()
        # Create a new Organization and Location
        cls.org = entities.Organization().create()
        cls.org_name = cls.org.name
        cls.loc = entities.Location(organization=[cls.org]).create()
        cls.loc_name = cls.loc.name
        # Create a new Life-Cycle environment
        cls.lc_env = entities.LifecycleEnvironment(
            organization=cls.org
        ).create()
        cls.rh_ah_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        with manifests.clone() as manifest:
            upload_manifest(cls.org.id, manifest.content)
        # Enables the RedHat repo and fetches it's Id.
        cls.repo_id = enable_rhrepo_and_fetchid(
            basearch=cls.rh_ah_repo['basearch'],
            # OrgId is passed as data in API hence str
            org_id=str(cls.org.id),
            product=cls.rh_ah_repo['product'],
            repo=cls.rh_ah_repo['name'],
            reposet=cls.rh_ah_repo['reposet'],
            releasever=cls.rh_ah_repo['releasever'],
        )
        # Increased timeout value for repo sync
        cls.old_task_timeout = entity_mixins.TASK_TIMEOUT
        entity_mixins.TASK_TIMEOUT = 600
        # Sync repository
        entities.Repository(id=cls.repo_id).sync()
        entity_mixins.TASK_TIMEOUT = cls.old_task_timeout
        cls.cv = entities.ContentView(organization=cls.org).create()
        cls.cv.repository = [entities.Repository(id=cls.repo_id)]
        cls.cv = cls.cv.update(['repository'])
        cls.cv.publish()
        cls.cv = cls.cv.read()
        promote(cls.cv.version[0], cls.lc_env.id)
        # Search for SmartProxy, and associate location
        cls.proxy = entities.SmartProxy().search(
            query={
                u'search': u'name={0}'.format(
                    settings.server.hostname
                )
            }
        )[0]
        cls.proxy.location = [cls.loc]
        cls.proxy.organization = [cls.org]
        cls.proxy = cls.proxy.update(['organization', 'location'])

        # Search for existing domain or create new otherwise. Associate org,
        # location and dns to it
        _, _, domain = settings.server.hostname.partition('.')
        cls.domain = entities.Domain().search(
            query={
                u'search': u'name="{0}"'.format(domain)
            }
        )
        if len(cls.domain) == 1:
            cls.domain = cls.domain[0].read()
            cls.domain.location.append(cls.loc)
            cls.domain.organization.append(cls.org)
            cls.domain.dns = cls.proxy
            cls.domain = cls.domain.update(['dns', 'location', 'organization'])
        else:
            cls.domain = entities.Domain(
                dns=cls.proxy,
                location=[cls.loc],
                organization=[cls.org],
            ).create()
        cls.domain_name = cls.domain.name

        # Search if subnet is defined with given network.
        # If so, just update its relevant fields otherwise,
        # Create new subnet
        network = settings.vlan_networking.subnet
        cls.subnet = entities.Subnet().search(
            query={u'search': u'network={0}'.format(network)}
        )
        if len(cls.subnet) == 1:
            cls.subnet = cls.subnet[0]
            cls.subnet.domain = [cls.domain]
            cls.subnet.location = [cls.loc]
            cls.subnet.organization = [cls.org]
            cls.subnet.dns = cls.proxy
            cls.subnet.dhcp = cls.proxy
            cls.subnet.tftp = cls.proxy
            cls.subnet.discovery = cls.proxy
            cls.subnet = cls.subnet.update([
                'domain',
                'discovery',
                'dhcp',
                'dns',
                'location',
                'organization',
                'tftp',
            ])
        else:
            # Create new subnet
            cls.subnet = entities.Subnet(
                name=gen_string('alpha'),
                network=network,
                mask=settings.vlan_networking.netmask,
                domain=[cls.domain],
                location=[cls.loc],
                organization=[cls.org],
                dns=cls.proxy,
                dhcp=cls.proxy,
                tftp=cls.proxy,
                discovery=cls.proxy
            ).create()

        # Search if Libvirt compute-resource already exists
        # If so, just update its relevant fields otherwise,
        # Create new compute-resource with 'libvirt' provider.
        resource_url = u'qemu+ssh://root@{0}/system'.format(
            settings.compute_resources.libvirt_hostname
        )
        comp_res = [
            res for res in entities.LibvirtComputeResource().search()
            if res.provider == 'Libvirt' and res.url == resource_url
        ]
        if len(comp_res) >= 1:
            cls.computeresource = entities.LibvirtComputeResource(
                id=comp_res[0].id).read()
            cls.computeresource.location.append(cls.loc)
            cls.computeresource.organization.append(cls.org)
            cls.computeresource = cls.computeresource.update([
                'location', 'organization'])
        else:
            # Create Libvirt compute-resource
            cls.computeresource = entities.LibvirtComputeResource(
                name=gen_string('alpha'),
                provider=u'libvirt',
                url=resource_url,
                set_console_password=False,
                display_type=u'VNC',
                location=[cls.loc.id],
                organization=[cls.org.id],
            ).create()

        # Get the Partition table ID
        cls.ptable = entities.PartitionTable().search(
            query={
                u'search': u'name="{0}"'.format(DEFAULT_PTABLE)
            }
        )[0]

        # Get the OS ID
        cls.os = entities.OperatingSystem().search(query={
            u'search': u'name="RedHat_Enterprise_Linux_Atomic_Host"'
        })[0]

        # Get the Provisioning template_ID and update with OS, Org, Location
        cls.provisioning_template = entities.ConfigTemplate().search(
            query={
                u'search': u'name="Satellite Atomic Kickstart Default"'
            }
        )[0]
        cls.provisioning_template.operatingsystem = [cls.os]
        cls.provisioning_template.organization = [cls.org]
        cls.provisioning_template.location = [cls.loc]
        cls.provisioning_template = cls.provisioning_template.update(
            ['location', 'operatingsystem', 'organization']
        )

        # Get the PXE template ID and update with OS, Org, location
        cls.pxe_template = entities.ConfigTemplate().search(
            query={
                u'search': u'name="Kickstart default PXELinux"'
            }
        )[0]
        cls.pxe_template.operatingsystem = [cls.os]
        cls.pxe_template.organization = [cls.org]
        cls.pxe_template.location = [cls.loc]
        cls.pxe_template = cls.pxe_template.update(
            ['location', 'operatingsystem', 'organization']
        )
        # Get the arch ID
        cls.arch = entities.Architecture().search(
            query={u'search': u'name="x86_64"'}
        )[0]
        # Get the ostree installer URL
        ostree_path = settings.ostree.ostree_installer
        # Get the Media
        cls.media = entities.Media().search(query={
            u'search': u'path={0}'.format(ostree_path)
        })
        if len(cls.media) == 1:
            cls.media = cls.media[0]
            cls.media.location = [cls.loc]
            cls.media.organization = [cls.org]
            cls.media = cls.media.update(['location', 'organization'])
        else:
            cls.media = entities.Media(
                organization=[cls.org],
                location=[cls.loc],
                os_family='Redhat',
                path_=ostree_path
            ).create()
        # Update the OS to associate arch, ptable, templates
        cls.os.architecture = [cls.arch]
        cls.os.ptable = [cls.ptable]
        cls.os.config_template = [cls.pxe_template, cls.provisioning_template]
        cls.os.medium = [cls.media]
        cls.os = cls.os.update([
            'architecture',
            'config_template',
            'ptable',
            'medium',
        ])

        # Create Hostgroup
        cls.host_group = entities.HostGroup(
            architecture=cls.arch,
            domain=cls.domain.id,
            subnet=cls.subnet.id,
            lifecycle_environment=cls.lc_env.id,
            content_view=cls.cv.id,
            location=[cls.loc.id],
            name=gen_string('alpha'),
            medium=cls.media,
            operatingsystem=cls.os.id,
            organization=[cls.org.id],
            ptable=cls.ptable.id,
        ).create()

    def tearDown(self):
        """Delete the host to free the resources"""
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            host_name = u'{0}.{1}'.format(self.hostname, self.domain_name)
            if self.hosts.search(host_name):
                self.hosts.delete(host_name, dropdown_present=True)
        super(AtomicHostTestCase, self).tearDown()

    @tier3
    def test_positive_provision_atomic_host(self):
        """Provision an atomic host on libvirt and register it with satellite

        :id: 5ddf2f7f-f7aa-4321-8717-372c7b6e99b6

        :expectedresults: Atomic host should be provisioned and listed under
            content-hosts/Hosts

        :CaseLevel: System
        """
        resource = u'{0} (Libvirt)'.format(self.computeresource.name)
        root_pwd = gen_string('alpha', 15)
        with Session(self) as session:
            make_host(
                session,
                name=self.hostname,
                org=self.org_name,
                parameters_list=[
                    ['Host', 'Organization', self.org_name],
                    ['Host', 'Location', self.loc_name],
                    ['Host', 'Host group', self.host_group.name],
                    ['Host', 'Deploy on', resource],
                    ['Virtual Machine', 'Memory', '1 GB'],
                    ['Operating System', 'Media', self.media.name],
                    ['Operating System', 'Partition table', DEFAULT_PTABLE],
                    ['Operating System', 'Root password', root_pwd],
                ],
                interface_parameters=[
                    ['Network type', 'Physical (Bridge)'],
                    ['Network', settings.vlan_networking.bridge],
                ],
            )
            search = self.hosts.search(
                u'{0}.{1}'.format(self.hostname, self.domain_name)
            )
            self.assertIsNotNone(search)

    @stubbed()
    @tier3
    def test_positive_register_pre_installed_atomic_host(self):
        """Register a pre-installed atomic host with satellite using admin
        credentials

        :id: 09729944-b60b-4742-8f1b-e8859e2e36d3

        :expectedresults: Atomic host should be registered successfully and
            listed under content-hosts/Hosts

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_register_pre_installed_atomic_host_using_ak(self):
        """Register a pre-installed atomic host with satellite using activation
        key

        :id: 31e5ffcf-2e3c-474a-a6a3-6d8e2f392abe

        :expectedresults: Atomic host should be registered successfully and
            listed under content-hosts/Hosts

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @tier3
    @upgrade
    def test_positive_delete_atomic_host(self):
        """Delete a provisioned atomic host

        :id: c0bcf753-8ddf-4e95-b214-42d1e077a6cf

        :expectedresults: Atomic host should be deleted successfully and
            shouldn't be listed under hosts/content-hosts

        :CaseLevel: System
        """
        resource = u'{0} (Libvirt)'.format(self.computeresource.name)
        root_pwd = gen_string('alpha', 15)
        with Session(self) as session:
            make_host(
                session,
                name=self.hostname,
                org=self.org_name,
                parameters_list=[
                    ['Host', 'Organization', self.org_name],
                    ['Host', 'Location', self.loc_name],
                    ['Host', 'Host group', self.host_group.name],
                    ['Host', 'Deploy on', resource],
                    ['Virtual Machine', 'Memory', '1 GB'],
                    ['Operating System', 'Media', self.media.name],
                    ['Operating System', 'Partition table', DEFAULT_PTABLE],
                    ['Operating System', 'Root password', root_pwd],
                ],
                interface_parameters=[
                    ['Network type', 'Physical (Bridge)'],
                    ['Network', settings.vlan_networking.bridge],
                ],
            )
            # Delete host
            self.hosts.delete(
                u'{0}.{1}'.format(self.hostname, self.domain_name),
                dropdown_present=True,
            )

    @stubbed()
    @tier3
    def test_positive_update_atomic_host_cv(self):
        """Update atomic-host with a new environment and content-view

        :id: 2ddd3bb7-ef58-42c0-908c-ae4d4bd0bff9

        :expectedresults: Atomic host should be updated with new content-view

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_execute_cmd_on_atomic_host_with_job_templates(self):
        """Execute ostree/atomic commands on provisioned atomic host with job
        templates

        :id: 56a46a1e-9e24-4ad7-9cea-3d78c7310b14

        :expectedresults: Ostree/atomic commands should be executed
            successfully via job templates

        :caseautomation: notautomated

        :CaseLevel: System
        """


class BulkHostTestCase(UITestCase):
    """Implements tests for Bulk Hosts actions in UI"""

    @tier3
    @upgrade
    def test_positive_bulk_delete_host(self):
        """Delete a multiple hosts from the list

        :id: 8da2084a-8b50-46dc-b305-18eeb80d01e0

        :expectedresults: All selected hosts should be deleted successfully

        :BZ: 1368026

        :CaseLevel: System
        """
        org = entities.Organization().create()
        hosts_names = [
            entities.Host(
                organization=org
            ).create().name
            for _ in range(18)
        ]
        with Session(self) as session:
            set_context(session, org=org.name)
            self.assertIsNotNone(self.hosts.update_host_bulkactions(
                hosts_names,
                action='Delete Hosts',
                parameters_list=[{'timeout': 300}],
            ))

    @stubbed()
    @tier3
    def test_positive_bulk_delete_atomic_host(self):
        """Delete a multiple atomic hosts

        :id: 7740e7c2-db54-4f6a-b5d4-6005fccb4c61

        :expectedresults: All selected atomic hosts should be deleted
            successfully

        :caseautomation: notautomated

        :CaseLevel: System
        """
