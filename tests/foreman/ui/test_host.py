# -*- encoding: utf-8 -*-
from fauxfactory import gen_string
from nailgun import entities, entity_mixins
from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import ENVIRONMENT
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.base import Base
from robottelo.ui.factory import make_host
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
class Host(UITestCase, Base):

    hostname = gen_string('numeric')

    @classmethod
    def setUpClass(cls):
        """Steps required to create a real host on libvirt

        1. Creates new Organization and Location.
        2. Creates new life-cycle environment.
        3. Creates new product and rhel67 custom repository.
        4. Creates new content-view by associating rhel67 repository.
        5. Publish and promote the content-view to next environment.
        6. Search for puppet environment and associate location.
        7. Search for smart-proxy and associate location.
        8. Search for domain and associate org, location and dns proxy.
        9. Search for '192.168.100.0' network and associate org, location,
        dns/dhcp/tftp proxy, and if its not there then creates new.
        10. Search for existing compute-resource with 'libvirt' provider and
        associate org.location, and if its not there then creates new.
        11. Search 'Kickstart default' partition table and rhel67 OS along with
        provisioning/PXE templates.
        12. Associates org, location and OS with provisioning and PXE templates
        13. Search for x86_64 architecture
        14. Associate arch, partition table, provisioning/PXE templates with OS
        15. Search for media and associate org/location
        16. Create new host group with all required entities

        """
        # Create a new Organization and Location
        cls.org = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = cls.org.name
        cls.loc = entities.Location(
            name=gen_string('alpha'),
            organization=[cls.org]
        ).create()
        cls.loc_name = cls.loc.name

        # Create a new Life-Cycle environment
        cls.lc_env = entities.LifecycleEnvironment(
            name=gen_string('alpha'),
            organization=cls.org
        ).create()

        # Create a Product, Repository for custom RHEL6 contents
        cls.product = entities.Product(
            name=gen_string('alpha'),
            organization=cls.org
        ).create()
        cls.repo = entities.Repository(
            name=gen_string('alpha'),
            product=cls.product,
            url=settings.rhel6_repo
        ).create()

        # Increased timeout value for repo sync
        cls.old_task_timeout = entity_mixins.TASK_TIMEOUT
        entity_mixins.TASK_TIMEOUT = 3600
        cls.repo.sync()

        # Create, Publish and promote CV
        cls.content_view = entities.ContentView(
            name=gen_string('alpha'),
            organization=cls.org
        ).create()
        cls.content_view.repository = [cls.repo]
        cls.content_view = cls.content_view.update(['repository'])
        cls.content_view.publish()
        cls.content_view = cls.content_view.read()
        promote(cls.content_view.version[0], cls.lc_env.id)
        entity_mixins.TASK_TIMEOUT = cls.old_task_timeout
        # Search for puppet environment and associate location
        cls.environment = entities.Environment().search(
            query={'organization_id': [cls.org.id]}
        )[0]
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

        # Search for domain and associate org, location
        cls.domain = entities.Domain().search(
            query={
                u'search': u'name="usersys.redhat.com"'
            }
        )[0]
        cls.domain_name = cls.domain.name
        cls.domain.location = [cls.loc]
        cls.domain.organization = [cls.org]
        cls.domain.dns = cls.proxy
        cls.domain = cls.domain.update(['dns', 'location', 'organization'])

        # Search if subnet is defined with given network.
        # If so, just update its relevant fields otherwise,
        # Create new subnet
        network = '192.168.100.0'
        cls.subnet = entities.Subnet().search(
            query={u'search': u'network={0}'.format(network)}
        )
        if (len(cls.subnet) == 1):
            cls.subnet = cls.subnet[0]
            cls.subnet.domain = [cls.domain]
            cls.subnet.location = [cls.loc]
            cls.subnet.organization = [cls.org]
            cls.subnet.dns = cls.proxy
            cls.subnet.dhcp = cls.proxy
            cls.subnet.tftp = cls.proxy
            cls.subnet.discovery = cls.proxy
            cls.subnet = cls.subnet.update(
                ['domain',
                 'discovery',
                 'dhcp',
                 'dns',
                 'location',
                 'organization',
                 'tftp']
            )
        else:
            # Create new subnet
            cls.subnet = entities.Subnet(
                name=gen_string('alpha'),
                network=network,
                mask=u'255.255.255.0',
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
        resource_url = u'qemu+tcp://{0}:16509/system'.format(
            settings.server.hostname
        )
        cls.computeresource = entities.LibvirtComputeResource(
            provider='libvirt',
            url=resource_url
        ).search()
        if (len(cls.computeresource) >= 1):
            cls.computeresource = cls.computeresource[0]
            cls.computeresource.location = [cls.loc]
            cls.computeresource.organization = [cls.org]
            cls.computeresource = cls.computeresource.update(
                ['location',
                 'organization']
            )
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
                u'search': u'name="Kickstart default"'
            }
        )[0]

        # Get the OS ID
        cls.os = entities.OperatingSystem().search(
            query={u'search': u'name="RedHat" AND major="6" AND minor="7"'}
        )[0]

        # Get the Provisioning template_ID and update with OS, Org, Location
        cls.provisioning_template = entities.ConfigTemplate().search(
            query={
                u'search': u'name="Satellite Kickstart Default"'
            }
        )[0]
        cls.provisioning_template.operatingsystem = [cls.os]
        cls.provisioning_template.organization = [cls.org]
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
        cls.pxe_template.organization = [cls.org]
        cls.pxe_template.location = [cls.loc]
        cls.pxe_template = cls.pxe_template.update(
            ['location', 'operatingsystem', 'organization']
        )

        # Get the arch ID
        cls.arch = entities.Architecture().search(
            query={u'search': u'name="x86_64"'}
        )[0]
        # Update the OS to associate arch, ptable, templates
        cls.os.architecture = [cls.arch]
        cls.os.ptable = [cls.ptable]
        cls.os.config_template = [cls.provisioning_template]
        cls.os.config_template = [cls.pxe_template]
        cls.os = cls.os.update(['architecture', 'config_template', 'ptable'])

        # Get the media and update its location
        cls.media = entities.Media().search(
            query={'organization_id': [cls.org.id]}
        )[0]
        cls.media.location = [cls.loc]
        cls.media = cls.media.update(['location'])
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
            organization=[cls.org.id],
            ptable=cls.ptable.id,
        ).create()
        super(Host, cls).setUpClass()

    def tearDown(self):
        """Delete the host to free the resources"""
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_hosts()
            host_name = u'{0}.{1}'.format(self.hostname, self.domain_name)
            if self.hosts.search(host_name):
                self.hosts.delete(host_name, True)
                self.assertIsNotNone(
                    self.hosts.wait_until_element(
                        common_locators['notif.success']))
        super(Host, self).tearDown()

    def test_create_host_on_libvirt(self):
        """@Test: Create a new Host on libvirt compute resource

        @Feature: Host - Positive create

        @Assert: Host is created

        """
        resource = u'{0} (Libvirt)'.format(self.computeresource.name)
        root_pwd = gen_string("alpha", 15)
        with Session(self.browser) as session:
            make_host(
                session,
                org=self.org_name,
                loc=self.loc_name,
                name=self.hostname,
                host_group=self.host_group.name,
                resource=resource,
                root_pwd=root_pwd,
                memory="1 GB",
                network_type="Virtual (NAT)",
            )
            self.scroll_page()
            self.navigator.go_to_hosts()
            search = self.hosts.search(
                u'{0}.{1}'.format(self.hostname, self.domain_name)
            )
            self.assertIsNotNone(search)

    def test_create_host(self):
        """@Test: Create a new Host

        @Feature: Host - Positive create

        @Assert: Host is created

        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(host.organization.name)
            self.navigator.go_to_hosts()
            self.hosts.create(
                arch=host.architecture.name,
                domain=host.domain.name,
                env=host.environment.name,
                loc=host.location.name,
                lifecycle_env=ENVIRONMENT,
                mac=host.mac,
                media=host.medium.name,
                name=host.name,
                org=host.organization.name,
                os=os_name,
                ptable=host.ptable.name,
                root_pwd=host.root_pass,
            )
            self.navigator.go_to_dashboard()
            self.navigator.go_to_hosts()
            # confirm the Host appears in the UI
            search = self.hosts.search(
                u'{0}.{1}'.format(host.name, host.domain.name)
            )
            self.assertIsNotNone(search)

    def test_delete_host(self):
        """@Test: Delete a Host

        @Feature: Host - Positive Delete

        @Assert: Host is deleted

        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(host.organization.name)
            self.navigator.go_to_hosts()
            self.hosts.create(
                arch=host.architecture.name,
                domain=host.domain.name,
                env=host.environment.name,
                loc=host.location.name,
                lifecycle_env=ENVIRONMENT,
                mac=host.mac,
                media=host.medium.name,
                name=host.name,
                org=host.organization.name,
                os=os_name,
                ptable=host.ptable.name,
                root_pwd=host.root_pass,
            )
            self.navigator.go_to_dashboard()
            self.navigator.go_to_hosts()
            # Delete host
            self.hosts.delete(
                u'{0}.{1}'.format(host.name, host.domain.name))
