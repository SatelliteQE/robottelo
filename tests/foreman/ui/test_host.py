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
    call_entity_method_with_timeout,
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo import manifests
from robottelo.cleanup import host_cleanup
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ATOMIC_TEMPLATE,
    DEFAULT_PTABLE,
    DEFAULT_PXE_TEMPLATE,
    FOREMAN_PROVIDERS,
    PRDS,
    REPOS,
    REPOSET,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
)
from robottelo.decorators import (
    run_in_one_thread,
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
    set_context,
)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


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
        })[0].read()

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
            )[0].read()
            template.operatingsystem.append(cls.os)
            template.organization.append(cls.org_)
            template.location.append(cls.loc)
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
        )[0].read()
        cls.proxy.location.append(cls.loc)
        cls.proxy.organization.append(cls.org_)
        cls.proxy = cls.proxy.update(['location', 'organization'])

        # Search for existing domain or create new otherwise. Associate org,
        # location and dns to it
        _, _, domain = settings.server.hostname.partition('.')
        domain = entities.Domain().search(
            query={
                u'search': u'name="{0}"'.format(domain)
            }
        )
        if len(domain) > 0:
            cls.domain = domain[0].read()
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
        subnet = entities.Subnet().search(
            query={u'search': u'network={0}'.format(network)}
        )
        if len(subnet) > 0:
            cls.subnet = subnet[0].read()
            cls.subnet.domain.append(cls.domain)
            cls.subnet.location.append(cls.loc)
            cls.subnet.organization.append(cls.org_)
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
            if (res.provider == FOREMAN_PROVIDERS['libvirt']
                and res.url == resource_url)
        ]
        if len(comp_res) > 0:
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
                provider=FOREMAN_PROVIDERS['libvirt'],
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
                loc=self.loc_name,
                force_context=True,
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

        :customerscenario: true

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
                loc=self.loc_name,
                force_context=True,
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
    @tier2
    def test_positive_sort_by_name(self):
        """Create some Host entities and sort them by name ascendingly and then
        descendingly

        :id: 12f75ef9-23e6-48be-80ed-b354e8ac212b

        :customerscenario: true

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

        :customerscenario: true

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

        :customerscenario: true

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

        :customerscenario: true

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

        :customerscenario: true

        :expectedresults: Host entities are sorted properly

        :CaseImportance: High

        :BZ: 1268085

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], environment_id=lce.id)
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
                content_facet_attributes={
                    'content_view_id': content_view.id,
                    'lifecycle_environment_id': lce.id,
                },
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


@run_in_one_thread
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
        # Sync repository with custom timeout
        call_entity_method_with_timeout(
            entities.Repository(id=cls.repo_id).sync, timeout=1500)
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
        )[0].read()
        cls.proxy.location.append(cls.loc)
        cls.proxy.organization.append(cls.org)
        cls.proxy = cls.proxy.update(['organization', 'location'])

        # Search for existing domain or create new otherwise. Associate org,
        # location and dns to it
        _, _, domain = settings.server.hostname.partition('.')
        cls.domain = entities.Domain().search(
            query={
                u'search': u'name="{0}"'.format(domain)
            }
        )
        if len(cls.domain) > 0:
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
        subnet = entities.Subnet().search(
            query={u'search': u'network={0}'.format(network)}
        )
        if len(subnet) > 0:
            cls.subnet = subnet[0].read()
            cls.subnet.domain.append(cls.domain)
            cls.subnet.location.append(cls.loc)
            cls.subnet.organization.append(cls.org)
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
                location=[cls.loc],
                organization=[cls.org],
                dns=cls.proxy,
                dhcp=cls.proxy,
                ipam='DHCP',
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
        if len(comp_res) > 0:
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
        )[0].read()
        cls.ptable.location.append(cls.loc)
        cls.ptable.organization.append(cls.org)
        cls.ptable = cls.ptable.update(['location', 'organization'])

        # Get the OS ID
        os = entities.OperatingSystem().search(query={
            u'search': u'name="RedHat_Enterprise_Linux_Atomic_Host"'
        })
        if len(os) > 0:
            cls.os = os[0].read()
        else:
            cls.os = entities.OperatingSystem(
                name='RedHat_Enterprise_Linux_Atomic_Host',
                family='Redhat',
                major=RHEL_7_MAJOR_VERSION,
            ).create()

        # update the provisioning templates with OS, Org and Location
        cls.templates = []
        for template_name in [DEFAULT_ATOMIC_TEMPLATE, DEFAULT_PXE_TEMPLATE]:
            template = entities.ConfigTemplate().search(
                query={
                    u'search': u'name="{0}"'.format(template_name)
                }
            )[0].read()
            template.operatingsystem.append(cls.os)
            template.organization.append(cls.org)
            template.location.append(cls.loc)
            template = template.update(
                ['location', 'operatingsystem', 'organization']
            )
            cls.templates.append(template)

        # Get the arch ID
        cls.arch = entities.Architecture().search(
            query={u'search': u'name="x86_64"'}
        )[0]
        # Get the ostree installer URL
        ostree_path = settings.ostree.ostree_installer
        # Get the Media
        media = entities.Media().search(query={
            u'search': u'path={0}'.format(ostree_path)
        })
        if len(media) > 0:
            cls.media = media[0].read()
            cls.media.location.append(cls.loc)
            cls.media.organization.append(cls.org)
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
        cls.os.config_template = cls.templates
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
        hosts = entities.Host().search(
            query={u'search': u'organization={0}'.format(self.org_name)})
        for host in hosts:
            host.delete()
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
                loc=self.loc_name,
                force_context=True,
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
                loc=self.loc_name,
                force_context=True,
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
