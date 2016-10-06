# -*- encoding: utf-8 -*-
"""Test class for Hosts UI

@Requirement: Host

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities, entity_mixins
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo import manifests
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_CV,
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
    skip_if_not_set,
    stubbed,
    tier3,
)
from robottelo.decorators.host import skip_if_os
from robottelo.test import UITestCase
from robottelo.ui.factory import make_host
from robottelo.ui.session import Session


class HostTestCase(UITestCase):
    """Implements Host tests in UI"""

    hostname = gen_string('numeric')

    @classmethod
    @skip_if_not_set('vlan_networking', 'compute_resources')
    def setUpClass(cls):
        """Steps required to create a real host on libvirt

        1. Creates new Organization and Location.
        2. Creates new life-cycle environment.
        3. Creates new product and rhel67 custom repository.
        4. Creates new content-view by associating rhel67 repository.
        5. Publish and promote the content-view to next environment.
        6. Search for puppet environment and associate location.
        7. Search for smart-proxy and associate location.
        8. Search for existing domain or create new otherwise. Associate org,
           location and dns proxy.
        9. Search for '192.168.100.0' network and associate org, location,
           dns/dhcp/tftp proxy, and if its not there then creates new.
        10. Search for existing compute-resource with 'libvirt' provider and
            associate org.location, and if its not there then creates
            new.
        11. Search 'Kickstart default' partition table and rhel67 OS along with
            provisioning/PXE templates.
        12. Associates org, location and OS with provisioning and PXE templates
        13. Search for x86_64 architecture
        14. Associate arch, partition table, provisioning/PXE templates with OS
        15. Search for media and associate org/location
        16. Create new host group with all required entities
        """
        super(HostTestCase, cls).setUpClass()
        # Create a new Organization and Location
        cls.org_ = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = cls.org_.name
        cls.loc = entities.Location(
            name=gen_string('alpha'),
            organization=[cls.org_]
        ).create()
        cls.loc_name = cls.loc.name

        # Create a new Life-Cycle environment
        cls.lc_env = entities.LifecycleEnvironment(
            name=gen_string('alpha'),
            organization=cls.org_
        ).create()

        # Create a Product, Repository for custom RHEL6 contents
        cls.product = entities.Product(
            name=gen_string('alpha'),
            organization=cls.org_
        ).create()
        cls.repo = entities.Repository(
            name=gen_string('alpha'),
            product=cls.product,
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

        # Search for SmartProxy, and associate location
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

        # Get the Provisioning template_ID and update with OS, Org, Location
        cls.provisioning_template = entities.ConfigTemplate().search(
            query={
                u'search': u'name="Satellite Kickstart Default"'
            }
        )[0]
        cls.provisioning_template.operatingsystem = [cls.os]
        cls.provisioning_template.organization = [cls.org_]
        cls.provisioning_template.location = [cls.loc]
        cls.provisioning_template = cls.provisioning_template.update([
            'location',
            'operatingsystem',
            'organization'
        ])

        # Get the PXE template ID and update with OS, Org, location
        cls.pxe_template = entities.ConfigTemplate().search(
            query={
                u'search': u'name="Kickstart default PXELinux"'
            }
        )[0]
        cls.pxe_template.operatingsystem = [cls.os]
        cls.pxe_template.organization = [cls.org_]
        cls.pxe_template.location = [cls.loc]
        cls.pxe_template = cls.pxe_template.update(
            ['location', 'operatingsystem', 'organization']
        )

        # Get the arch ID
        cls.arch = entities.Architecture().search(
            query={u'search': u'name="x86_64"'}
        )[0]

        # Get the media and update its location
        cls.media = entities.Media(organization=[cls.org_]).search()[0].read()
        cls.media.location.append(cls.loc)
        cls.media.organization.append(cls.org_)
        cls.media = cls.media.update(['location', 'organization'])
        # Update the OS to associate arch, ptable, templates
        cls.os.architecture = [cls.arch]
        cls.os.ptable = [cls.ptable]
        cls.os.config_template = [cls.provisioning_template]
        cls.os.config_template = [cls.pxe_template]
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
            content_view=cls.content_view.id,
            location=[cls.loc.id],
            name=gen_string('alpha'),
            environment=cls.environment.id,
            puppet_proxy=cls.proxy,
            puppet_ca_proxy=cls.proxy,
            content_source=cls.proxy,
            medium=cls.media,
            operatingsystem=cls.os.id,
            organization=[cls.org_.id],
            ptable=cls.ptable.id,
        ).create()

    def tearDown(self):
        """Delete the host to free the resources"""
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_hosts()
            host_name = u'{0}.{1}'.format(self.hostname, self.domain_name)
            if self.hosts.get_entity(host_name):
                self.hosts.delete(host_name, True)
        super(HostTestCase, self).tearDown()

    @run_only_on('sat')
    @tier3
    def test_positive_create_libvirt(self):
        """Create a new Host on libvirt compute resource

        @id: 2678f95f-0c0e-4b46-a3c1-3f9a954d3bde

        @Assert: Host is created

        @CaseLevel: System
        """
        resource = u'{0} (Libvirt)'.format(self.computeresource.name)
        root_pwd = gen_string('alpha', 15)
        environment = entities.Environment(
            location=[self.loc],
            organization=[self.org_],
        ).create(True)
        with Session(self.browser) as session:
            make_host(
                session,
                name=self.hostname,
                org=self.org_name,
                parameters_list=[
                    ['Host', 'Organization', self.org_name],
                    ['Host', 'Location', self.loc_name],
                    ['Host', 'Host group', self.host_group.name],
                    ['Host', 'Deploy on', resource],
                    ['Host', 'Puppet Environment', environment.name],
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
            search = self.hosts.get_entity(
                u'{0}.{1}'.format(self.hostname, self.domain_name)
            )
            self.assertIsNotNone(search)

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_create_baremetal_with_bios(self):
        """Create a new Host from provided MAC address

        @id: 2cedc634-7761-4326-b77a-b999098f5c00

        @setup:

        1. Create a PXE-based VM with BIOS boot mode (outside of Satellite).

        @steps:

        1. Create a new host using 'BareMetal' option and MAC address of the
        pre-created VM

        @assert: Host is created

        @caseautomation: notautomated

        @caselevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_create_baremetal_with_uefi(self):
        """Create a new Host from provided MAC address

        @id: ec62e90b-1b2a-4eac-8b15-7e36c8179086

        @setup:

        1. Create a PXE-based VM with UEFI boot mode (outside of Satellite).

        @steps:

        1. Create a new host using 'BareMetal' option and MAC address of the
        pre-created VM

        @assert: Host is created

        @caseautomation: notautomated

        @caselevel: System

        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_verify_files_with_pxegrub_uefi(self):
        """Provision a new Host and verify the tftp and dhcpd file
        structure is correct

        @id: e3dd2334-6e82-4272-a099-6f4214b77151

        @steps:

        1. Associate a pxegrub-type provisioning template with the os
        2. Create new host (can be fictive bare metal) with the above OS and
        PXE loader set to Grub UEFI
        3. Build the host

        @assert:
        Verify [/var/lib/tftpboot/] contains the following dir/file structure:
            grub/bootia32.efi
            grub/bootx64.efi
            grub/01-AA-BB-CC-DD-EE-FF
            grub/efidefault
            grub/shim.efi
        and record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

        @caseautomation: notautomated

        @caselevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_verify_files_with_pxegrub_uefi_secureboot(self):
        """Provision a new Host and verify the tftp and dhcpd file
        structure is correct

        @id: fc97dfcc-15d0-4eab-a778-fa1bcf82be22

        @steps:

        1. Associate a pxegrub-type provisioning template with the os
        2. Create new host (can be fictive bare metal) with the above OS and
        PXE loader set to Grub UEFI SecureBoot
        3. Build the host

        @assert:
        Verify [/var/lib/tftpboot/] contains the following dir/file structure:
            grub/bootia32.efi
            grub/bootx64.efi
            grub/01-AA-BB-CC-DD-EE-FF
            grub/efidefault
            grub/shim.efi
        and record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

        @caseautomation: notautomated

        @caselevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_verify_files_with_pxegrub2_uefi(self):
        """Provision a new UEFI Host and verify the and dhcpd file
        structure is correct

        @id: eec31881-eb20-4fb3-8d19-e3a4012ba4a0

        @steps:

        1. Associate a pxegrub-type provisioning template with the os
        2. Create new host (can be fictive bare metal) with the above OS and
        PXE loader set to Grub2 UEFI
        3. Build the host

        @assert:
        Verify [/var/lib/tftpboot/] contains the following dir/file structure:
            pxegrub2
            grub2/grub.cfg-01-aa-bb-cc-dd-ee-ff
            grub2/grub.cfg
            grub2/grubx32.efi
            grub2/grubx64.efi
            grub/shim.efi
        and record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

        @caseautomation: notautomated

        @caselevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier3
    def test_positive_verify_files_with_pxegrub2_uefi_secureboot(self):
        """Provision a new UEFI Host and verify the tftp and dhcpd file
        structure is correct

        @id: fdbb3617-74f2-46c4-930f-028dd4edcf9e

        @steps:

        1. Associate a pxegrub-type provisioning template with the os
        2. Create new host (can be fictive bare metal) with the above OS and
        PXE loader set to Grub2 UEFI SecureBoot
        3. Build the host

        @assert:
        Verify [/var/lib/tftpboot/] contains the following dir/file structure:
            pxegrub2
            grub2/grub.cfg-01-aa-bb-cc-dd-ee-ff
            grub2/grub.cfg
            grub2/grubx32.efi
            grub2/grubx64.efi
            grub/shim.efi
        and record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

        @caseautomation: notautomated

        @caselevel: System
        """

    @run_only_on('sat')
    @tier3
    def test_positive_create(self):
        """Create a new Host

        @id: 4821444d-3c86-4f93-849b-60460e025ba0

        @Assert: Host is created

        @CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self.browser) as session:
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
            search = self.hosts.get_entity(
                u'{0}.{1}'.format(host.name, host.domain.name)
            )
            self.assertIsNotNone(search)

    @run_only_on('sat')
    @tier3
    def test_positive_update_name(self):
        """Create a new Host and update its name to valid one

        @id: f1c19599-f613-431d-bf09-62addec1e60b

        @Assert: Host is updated successfully

        @CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        host_name = host.name
        with Session(self.browser) as session:
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
            search = self.hosts.get_entity(
                u'{0}.{1}'.format(host_name, host.domain.name)
            )
            self.assertIsNotNone(search)
            new_name = gen_string('alpha')
            self.hosts.update(host_name, host.domain.name, new_name)
            new_host_name = (
                u'{0}.{1}'.format(new_name, host.domain.name)).lower()
            self.assertIsNotNone(self.hosts.get_entity(new_host_name))
            self.hostname = new_name

    @run_only_on('sat')
    @tier3
    def test_positive_delete(self):
        """Delete a Host

        @id: 13735af1-f1c7-466e-a969-80618a1d854d

        @Assert: Host is delete

        @CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self.browser) as session:
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
                u'{0}.{1}'.format(host.name, host.domain.name))

    @stubbed()
    @tier3
    def test_positive_create_with_user(self):
        """Create Host with new user specified

        @id: b97d6fe5-b0a1-4ddc-8d7f-cbf7b17c823d

        @Assert: Host is created

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_update_with_user(self):
        """Update Host with new user specified

        @id: 4c030cf5-b89c-4dec-bb3e-0cb3215a2315

        @Assert: Host is updated

        @caseautomation: notautomated

        @CaseLevel: System
        """


class AtomicHostTestCase(UITestCase):
    """Implements Atomic Host tests in UI"""

    hostname = gen_string('numeric')

    @classmethod
    @skip_if_os('RHEL6')
    @skip_if_not_set('vlan_networking', 'compute_resources')
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
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_hosts()
            host_name = u'{0}.{1}'.format(self.hostname, self.domain_name)
            if self.hosts.get_entity(host_name):
                self.hosts.delete(host_name, True)
        super(AtomicHostTestCase, self).tearDown()

    @tier3
    def test_positive_provision_atomic_host(self):
        """Provision an atomic host on libvirt and register it with satellite

        @id: 5ddf2f7f-f7aa-4321-8717-372c7b6e99b6

        @Assert: Atomic host should be provisioned and listed under
        content-hosts/Hosts

        @CaseLevel: System
        """
        resource = u'{0} (Libvirt)'.format(self.computeresource.name)
        root_pwd = gen_string('alpha', 15)
        with Session(self.browser) as session:
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
            search = self.hosts.get_entity(
                u'{0}.{1}'.format(self.hostname, self.domain_name)
            )
            self.assertIsNotNone(search)

    @stubbed()
    @tier3
    def test_positive_register_pre_installed_atomic_host(self):
        """Register a pre-installed atomic host with satellite using admin
        credentials

        @id: 09729944-b60b-4742-8f1b-e8859e2e36d3

        @Assert: Atomic host should be registered successfully and listed under
        content-hosts/Hosts

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_register_pre_installed_atomic_host_using_ak(self):
        """Register a pre-installed atomic host with satellite using activation
        key

        @id: 31e5ffcf-2e3c-474a-a6a3-6d8e2f392abe

        @Assert: Atomic host should be registered successfully and listed under
        content-hosts/Hosts

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @tier3
    def test_positive_delete_atomic_host(self):
        """Delete a provisioned atomic host

        @id: c0bcf753-8ddf-4e95-b214-42d1e077a6cf

        @Assert: Atomic host should be deleted successfully and shouldn't be
        listed under hosts/content-hosts

        @CaseLevel: System
        """
        resource = u'{0} (Libvirt)'.format(self.computeresource.name)
        root_pwd = gen_string('alpha', 15)
        with Session(self.browser) as session:
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
                u'{0}.{1}'.format(self.hostname, self.domain_name))

    @stubbed()
    @tier3
    def test_positive_bulk_delete_atomic_host(self):
        """Delete a multiple atomic hosts

        @id: 7740e7c2-db54-4f6a-b5d4-6005fccb4c61

        @Assert: All selected atomic hosts should be deleted successfully

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_update_atomic_host_cv(self):
        """Update atomic-host with a new environment and content-view

        @id: 2ddd3bb7-ef58-42c0-908c-ae4d4bd0bff9

        @Assert: Atomic host should be updated with new content-view

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_execute_cmd_on_atomic_host_with_job_templates(self):
        """Execute ostree/atomic commands on provisioned atomic host with job
        templates

        @id: 56a46a1e-9e24-4ad7-9cea-3d78c7310b14

        @Assert: Ostree/atomic commands should be executed successfully via job
        templates

        @caseautomation: notautomated

        @CaseLevel: System
        """
