"""DEPRECATED UI FUNCTIONALITY"""

# import six

# from fauxfactory import gen_string
# from nailgun import entities

# from robottelo.api.utils import (
#     call_entity_method_with_timeout,
#     enable_rhrepo_and_fetchid,
#     promote,
#     upload_manifest,
# )
# from robottelo import manifests
# from robottelo.config import settings
# from robottelo.constants import (
#     DEFAULT_ATOMIC_TEMPLATE,
#     DEFAULT_PTABLE,
#     DEFAULT_PXE_TEMPLATE,
#     PRDS,
#     REPOS,
#     REPOSET,
#     RHEL_7_MAJOR_VERSION,
# )
# from robottelo.decorators import (
#     run_in_one_thread,
#     skip_if_bug_open,
#     skip_if_not_set,
#     stubbed,
#     tier2,
#     tier3,
#     upgrade,
# )
# from robottelo.decorators.host import skip_if_os
# from robottelo.test import UITestCase
# from robottelo.ui.factory import (
#     make_host,
#     set_context,
# )
# from robottelo.ui.session import Session


# @run_in_one_thread
# class AtomicHostTestCase(UITestCase):
#     """Implements Atomic Host tests in UI"""

#     hostname = gen_string('numeric')

#     @classmethod
#     @skip_if_bug_open('bugzilla', 1414134)
#     @skip_if_os('RHEL6')
#     @skip_if_not_set('vlan_networking', 'compute_resources', 'ostree')
#     def setUpClass(cls):
#         """Steps required to create a Atomic host on libvirt

#         1. Creates new Organization and Location.
#         2. Creates new life-cycle environment.
#         3. Creates new product and sync RH Atomic OSTree repository.
#         4. Creates new content-view by associating RH Atomic repository.
#         5. Publish and promote the content-view to next environment.
#         6. Search for smart-proxy and associate location.
#         7. Search for existing domain or create new otherwise. Associate org,
#            location and dns proxy.
#         8. Search for '192.168.100.0' network and associate org, location,
#            dns/dhcp/tftp proxy, and if its not there then creates new.
#         9. Search for existing compute-resource with 'libvirt' provider and
#             associate org.location, and if its not there then creates
#             new.
#         10. Search 'Kickstart default' partition table and RH Atomic OS along
#             with PXE templates.
#         11. Associates org, location and OS with provisioning and PXE templates
#         12. Search for x86_64 architecture
#         13. Associate arch, partition table, provisioning/PXE templates with OS
#         14. Search for existing Atomic media or create new otherwise and
#             associate org/location
#         15. Create new host group with all required entities
#         """
#         super(AtomicHostTestCase, cls).setUpClass()
#         # Create a new Organization and Location
#         cls.org = entities.Organization().create()
#         cls.org_name = cls.org.name
#         cls.loc = entities.Location(organization=[cls.org]).create()
#         cls.loc_name = cls.loc.name
#         # Create a new Life-Cycle environment
#         cls.lc_env = entities.LifecycleEnvironment(
#             organization=cls.org
#         ).create()
#         cls.rh_ah_repo = {
#             'name': REPOS['rhaht']['name'],
#             'product': PRDS['rhah'],
#             'reposet': REPOSET['rhaht'],
#             'basearch': None,
#             'releasever': None,
#         }
#         with manifests.clone() as manifest:
#             upload_manifest(cls.org.id, manifest.content)
#         # Enables the RedHat repo and fetches it's Id.
#         cls.repo_id = enable_rhrepo_and_fetchid(
#             basearch=cls.rh_ah_repo['basearch'],
#             # OrgId is passed as data in API hence str
#             org_id=str(cls.org.id),
#             product=cls.rh_ah_repo['product'],
#             repo=cls.rh_ah_repo['name'],
#             reposet=cls.rh_ah_repo['reposet'],
#             releasever=cls.rh_ah_repo['releasever'],
#         )
#         # Sync repository with custom timeout
#         call_entity_method_with_timeout(
#             entities.Repository(id=cls.repo_id).sync, timeout=1500)
#         cls.cv = entities.ContentView(organization=cls.org).create()
#         cls.cv.repository = [entities.Repository(id=cls.repo_id)]
#         cls.cv = cls.cv.update(['repository'])
#         cls.cv.publish()
#         cls.cv = cls.cv.read()
#         promote(cls.cv.version[0], cls.lc_env.id)
#         # Search for SmartProxy, and associate location
#         cls.proxy = entities.SmartProxy().search(
#             query={
#                 u'search': u'name={0}'.format(
#                     settings.server.hostname
#                 )
#             }
#         )[0].read()
#         cls.proxy.location.append(cls.loc)
#         cls.proxy.organization.append(cls.org)
#         cls.proxy = cls.proxy.update(['organization', 'location'])

#         # Search for existing domain or create new otherwise. Associate org,
#         # location and dns to it
#         _, _, domain = settings.server.hostname.partition('.')
#         cls.domain = entities.Domain().search(
#             query={
#                 u'search': u'name="{0}"'.format(domain)
#             }
#         )
#         if len(cls.domain) > 0:
#             cls.domain = cls.domain[0].read()
#             cls.domain.location.append(cls.loc)
#             cls.domain.organization.append(cls.org)
#             cls.domain.dns = cls.proxy
#             cls.domain = cls.domain.update(['dns', 'location', 'organization'])
#         else:
#             cls.domain = entities.Domain(
#                 dns=cls.proxy,
#                 location=[cls.loc],
#                 organization=[cls.org],
#             ).create()
#         cls.domain_name = cls.domain.name

#         # Search if subnet is defined with given network.
#         # If so, just update its relevant fields otherwise,
#         # Create new subnet
#         network = settings.vlan_networking.subnet
#         subnet = entities.Subnet().search(
#             query={u'search': u'network={0}'.format(network)}
#         )
#         if len(subnet) > 0:
#             cls.subnet = subnet[0].read()
#             cls.subnet.domain.append(cls.domain)
#             cls.subnet.location.append(cls.loc)
#             cls.subnet.organization.append(cls.org)
#             cls.subnet.dns = cls.proxy
#             cls.subnet.dhcp = cls.proxy
#             cls.subnet.ipam = 'DHCP'
#             cls.subnet.tftp = cls.proxy
#             cls.subnet.discovery = cls.proxy
#             cls.subnet = cls.subnet.update([
#                 'domain',
#                 'discovery',
#                 'dhcp',
#                 'dns',
#                 'ipam',
#                 'location',
#                 'organization',
#                 'tftp',
#             ])
#         else:
#             # Create new subnet
#             cls.subnet = entities.Subnet(
#                 name=gen_string('alpha'),
#                 network=network,
#                 mask=settings.vlan_networking.netmask,
#                 domain=[cls.domain],
#                 location=[cls.loc],
#                 organization=[cls.org],
#                 dns=cls.proxy,
#                 dhcp=cls.proxy,
#                 ipam='DHCP',
#                 tftp=cls.proxy,
#                 discovery=cls.proxy
#             ).create()

#         # Search if Libvirt compute-resource already exists
#         # If so, just update its relevant fields otherwise,
#         # Create new compute-resource with 'libvirt' provider.
#         resource_url = u'qemu+ssh://root@{0}/system'.format(
#             settings.compute_resources.libvirt_hostname
#         )
#         comp_res = [
#             res for res in entities.LibvirtComputeResource().search()
#             if res.provider == 'Libvirt' and res.url == resource_url
#         ]
#         if len(comp_res) > 0:
#             cls.computeresource = entities.LibvirtComputeResource(
#                 id=comp_res[0].id).read()
#             cls.computeresource.location.append(cls.loc)
#             cls.computeresource.organization.append(cls.org)
#             cls.computeresource = cls.computeresource.update([
#                 'location', 'organization'])
#         else:
#             # Create Libvirt compute-resource
#             cls.computeresource = entities.LibvirtComputeResource(
#                 name=gen_string('alpha'),
#                 provider=u'libvirt',
#                 url=resource_url,
#                 set_console_password=False,
#                 display_type=u'VNC',
#                 location=[cls.loc.id],
#                 organization=[cls.org.id],
#             ).create()

#         # Get the Partition table ID
#         cls.ptable = entities.PartitionTable().search(
#             query={
#                 u'search': u'name="{0}"'.format(DEFAULT_PTABLE)
#             }
#         )[0].read()
#         cls.ptable.location.append(cls.loc)
#         cls.ptable.organization.append(cls.org)
#         cls.ptable = cls.ptable.update(['location', 'organization'])

#         # Get the OS ID
#         os = entities.OperatingSystem().search(query={
#             u'search': u'name="RedHat_Enterprise_Linux_Atomic_Host"'
#         })
#         if len(os) > 0:
#             cls.os = os[0].read()
#         else:
#             cls.os = entities.OperatingSystem(
#                 name='RedHat_Enterprise_Linux_Atomic_Host',
#                 family='Redhat',
#                 major=RHEL_7_MAJOR_VERSION,
#             ).create()

#         # update the provisioning templates with OS, Org and Location
#         cls.templates = []
#         for template_name in [DEFAULT_ATOMIC_TEMPLATE, DEFAULT_PXE_TEMPLATE]:
#             template = entities.ConfigTemplate().search(
#                 query={
#                     u'search': u'name="{0}"'.format(template_name)
#                 }
#             )[0].read()
#             template.operatingsystem.append(cls.os)
#             template.organization.append(cls.org)
#             template.location.append(cls.loc)
#             template = template.update(
#                 ['location', 'operatingsystem', 'organization']
#             )
#             cls.templates.append(template)

#         # Get the arch ID
#         cls.arch = entities.Architecture().search(
#             query={u'search': u'name="x86_64"'}
#         )[0]
#         # Get the ostree installer URL
#         ostree_path = settings.ostree.ostree_installer
#         # Get the Media
#         media = entities.Media().search(query={
#             u'search': u'path={0}'.format(ostree_path)
#         })
#         if len(media) > 0:
#             cls.media = media[0].read()
#             cls.media.location.append(cls.loc)
#             cls.media.organization.append(cls.org)
#             cls.media = cls.media.update(['location', 'organization'])
#         else:
#             cls.media = entities.Media(
#                 organization=[cls.org],
#                 location=[cls.loc],
#                 os_family='Redhat',
#                 path_=ostree_path
#             ).create()
#         # Update the OS to associate arch, ptable, templates
#         cls.os.architecture = [cls.arch]
#         cls.os.ptable = [cls.ptable]
#         cls.os.config_template = cls.templates
#         cls.os.medium = [cls.media]
#         cls.os = cls.os.update([
#             'architecture',
#             'config_template',
#             'ptable',
#             'medium',
#         ])

#         # Create Hostgroup
#         cls.host_group = entities.HostGroup(
#             architecture=cls.arch,
#             domain=cls.domain.id,
#             subnet=cls.subnet.id,
#             lifecycle_environment=cls.lc_env.id,
#             content_view=cls.cv.id,
#             location=[cls.loc.id],
#             name=gen_string('alpha'),
#             medium=cls.media,
#             operatingsystem=cls.os.id,
#             organization=[cls.org.id],
#             ptable=cls.ptable.id,
#         ).create()

#     def tearDown(self):
#         """Delete the host to free the resources"""
#         hosts = entities.Host().search(
#             query={u'search': u'organization={0}'.format(self.org_name)})
#         for host in hosts:
#             host.delete()
#         super(AtomicHostTestCase, self).tearDown()

#     @tier3
#     def test_positive_provision_atomic_host(self):
#         """Provision an atomic host on libvirt and register it with satellite

#         :id: 5ddf2f7f-f7aa-4321-8717-372c7b6e99b6

#         :expectedresults: Atomic host should be provisioned and listed under
#             content-hosts/Hosts

#         :CaseLevel: System
#         """
#         resource = u'{0} (Libvirt)'.format(self.computeresource.name)
#         root_pwd = gen_string('alpha', 15)
#         with Session(self) as session:
#             make_host(
#                 session,
#                 name=self.hostname,
#                 org=self.org_name,
#                 loc=self.loc_name,
#                 force_context=True,
#                 parameters_list=[
#                     ['Host', 'Organization', self.org_name],
#                     ['Host', 'Location', self.loc_name],
#                     ['Host', 'Host group', self.host_group.name],
#                     ['Host', 'Deploy on', resource],
#                     ['Virtual Machine', 'Memory', '1 GB'],
#                     ['Operating System', 'Media', self.media.name],
#                     ['Operating System', 'Partition table', DEFAULT_PTABLE],
#                     ['Operating System', 'Root password', root_pwd],
#                 ],
#                 interface_parameters=[
#                     ['Network type', 'Physical (Bridge)'],
#                     ['Network', settings.vlan_networking.bridge],
#                 ],
#             )
#             search = self.hosts.search(
#                 u'{0}.{1}'.format(self.hostname, self.domain_name)
#             )
#             self.assertIsNotNone(search)

#     @stubbed()
#     @tier3
#     def test_positive_register_pre_installed_atomic_host(self):
#         """Register a pre-installed atomic host with satellite using admin
#         credentials

#         :id: 09729944-b60b-4742-8f1b-e8859e2e36d3

#         :expectedresults: Atomic host should be registered successfully and
#             listed under content-hosts/Hosts

#         :CaseAutomation: notautomated

#         :CaseLevel: System
#         """

#     @stubbed()
#     @tier3
#     def test_positive_register_pre_installed_atomic_host_using_ak(self):
#         """Register a pre-installed atomic host with satellite using activation
#         key

#         :id: 31e5ffcf-2e3c-474a-a6a3-6d8e2f392abe

#         :expectedresults: Atomic host should be registered successfully and
#             listed under content-hosts/Hosts

#         :CaseAutomation: notautomated

#         :CaseLevel: System
#         """

#     @tier3
#     @upgrade
#     def test_positive_delete_atomic_host(self):
#         """Delete a provisioned atomic host

#         :id: c0bcf753-8ddf-4e95-b214-42d1e077a6cf

#         :expectedresults: Atomic host should be deleted successfully and
#             shouldn't be listed under hosts/content-hosts

#         :CaseLevel: System
#         """
#         resource = u'{0} (Libvirt)'.format(self.computeresource.name)
#         root_pwd = gen_string('alpha', 15)
#         with Session(self) as session:
#             make_host(
#                 session,
#                 name=self.hostname,
#                 org=self.org_name,
#                 loc=self.loc_name,
#                 force_context=True,
#                 parameters_list=[
#                     ['Host', 'Organization', self.org_name],
#                     ['Host', 'Location', self.loc_name],
#                     ['Host', 'Host group', self.host_group.name],
#                     ['Host', 'Deploy on', resource],
#                     ['Virtual Machine', 'Memory', '1 GB'],
#                     ['Operating System', 'Media', self.media.name],
#                     ['Operating System', 'Partition table', DEFAULT_PTABLE],
#                     ['Operating System', 'Root password', root_pwd],
#                 ],
#                 interface_parameters=[
#                     ['Network type', 'Physical (Bridge)'],
#                     ['Network', settings.vlan_networking.bridge],
#                 ],
#             )
#             # Delete host
#             self.hosts.delete(
#                 u'{0}.{1}'.format(self.hostname, self.domain_name),
#                 dropdown_present=True,
#             )

#     @stubbed()
#     @tier3
#     def test_positive_update_atomic_host_cv(self):
#         """Update atomic-host with a new environment and content-view

#         :id: 2ddd3bb7-ef58-42c0-908c-ae4d4bd0bff9

#         :expectedresults: Atomic host should be updated with new content-view

#         :CaseAutomation: notautomated

#         :CaseLevel: System
#         """

#     @stubbed()
#     @tier3
#     def test_positive_execute_cmd_on_atomic_host_with_job_templates(self):
#         """Execute ostree/atomic commands on provisioned atomic host with job
#         templates

#         :id: 56a46a1e-9e24-4ad7-9cea-3d78c7310b14

#         :expectedresults: Ostree/atomic commands should be executed
#             successfully via job templates

#         :CaseAutomation: notautomated

#         :CaseLevel: System
#         """


# class BulkHostTestCase(UITestCase):
#     """Implements tests for Bulk Hosts actions in UI"""

#     @stubbed()
#     @tier3
#     def test_positive_bulk_delete_atomic_host(self):
#         """Delete a multiple atomic hosts

#         :id: 7740e7c2-db54-4f6a-b5d4-6005fccb4c61

#         :expectedresults: All selected atomic hosts should be deleted
#             successfully

#         :CaseAutomation: notautomated

#         :CaseLevel: System
#         """
