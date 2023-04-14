"""
It is not meant to be used directly, but as part of a robottelo.hosts.Satellite instance
example: my_satellite.api_factory.api_method()
"""
from contextlib import contextmanager

from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_string
from nailgun import entity_mixins
from nailgun.entity_mixins import call_entity_method_with_timeout
from requests import HTTPError

from robottelo.config import settings
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DEFAULT_PXE_TEMPLATE
from robottelo.constants import DEFAULT_TEMPLATE
from robottelo.constants import REPO_TYPE
from robottelo.exceptions import ImproperlyConfigured
from robottelo.host_helpers.repository_mixins import initiate_repo_helpers


class APIFactory:
    """This class is part of a mixin and not to be used directly. See robottelo.hosts.Satellite"""

    def __init__(self, satellite):
        self._satellite = satellite
        self.__dict__.update(initiate_repo_helpers(self._satellite))

    def make_http_proxy(self, org, http_proxy_type):
        """
        Creates HTTP proxy.
        :param str org: Organization
        :param str http_proxy_type: None, False, True
        """
        if http_proxy_type is False:
            return self._satellite.api.HTTPProxy(
                name=gen_string('alpha', 15),
                url=settings.http_proxy.un_auth_proxy_url,
                organization=[org.id],
            ).create()
        if http_proxy_type:
            return self._satellite.api.HTTPProxy(
                name=gen_string('alpha', 15),
                url=settings.http_proxy.auth_proxy_url,
                username=settings.http_proxy.username,
                password=settings.http_proxy.password,
                organization=[org.id],
            ).create()

    def cv_publish_promote(self, name=None, env_name=None, repo_id=None, org_id=None):
        """Create, publish and promote CV to selected environment"""
        if org_id is None:
            org_id = self._satellite.api.Organization().create().id
        # Create Life-Cycle content environment
        kwargs = {'name': env_name} if env_name is not None else {}
        lce = self._satellite.api.LifecycleEnvironment(organization=org_id, **kwargs).create()
        # Create content view(CV)
        kwargs = {'name': name} if name is not None else {}
        content_view = self._satellite.api.ContentView(organization=org_id, **kwargs).create()
        # Associate YUM repo to created CV
        if repo_id is not None:
            content_view.repository = [self._satellite.api.Repository(id=repo_id)]
            content_view = content_view.update(['repository'])
        # Publish content view
        content_view.publish()
        # Promote the content view version.
        content_view_version = content_view.read().version[0]
        content_view_version.promote(data={'environment_ids': lce.id})
        return content_view.read()

    def enable_rhrepo_and_fetchid(
        self, basearch, org_id, product, repo, reposet, releasever=None, strict=False
    ):
        """Enable a RedHat Repository and fetches it's Id.

        :param str org_id: The organization Id.
        :param str product: The product name in which repository exists.
        :param str reposet: The reposet name in which repository exists.
        :param str repo: The repository name who's Id is to be fetched.
        :param str basearch: The architecture of the repository.
        :param str optional releasever: The releasever of the repository.
        :param bool optional strict: Raise exception if the reposet was already enabled.
        :return: Returns the repository Id.
        :rtype: str

        """
        product = self._satellite.api.Product(name=product, organization=org_id).search()[0]
        r_set = self._satellite.api.RepositorySet(name=reposet, product=product).search()[0]
        payload = {}
        if basearch is not None:
            payload['basearch'] = basearch
        if releasever is not None:
            payload['releasever'] = releasever
        payload['product_id'] = product.id
        try:
            r_set.enable(data=payload)
        except HTTPError as e:
            if (
                not strict
                and e.response.status_code == 409
                and 'repository is already enabled' in e.response.json()['displayMessage']
            ):
                pass
            else:
                raise
        result = self._satellite.api.Repository(name=repo).search(query={'organization_id': org_id})
        return result[0].id

    def create_sync_custom_repo(
        self,
        org_id=None,
        product_name=None,
        repo_name=None,
        repo_url=None,
        repo_type=None,
        repo_unprotected=True,
        docker_upstream_name=None,
    ):
        """Create product/repo, sync it and returns repo_id"""
        if org_id is None:
            org_id = self._satellite.api.Organization().create().id
        product_name = product_name or gen_string('alpha')
        repo_name = repo_name or gen_string('alpha')
        # Creates new product and repository via API's
        product = self._satellite.api.Product(name=product_name, organization=org_id).create()
        repo = self._satellite.api.Repository(
            name=repo_name,
            url=repo_url or settings.repos.yum_1.url,
            content_type=repo_type or REPO_TYPE['yum'],
            product=product,
            unprotected=repo_unprotected,
            docker_upstream_name=docker_upstream_name,
        ).create()
        # Sync repository
        self._satellite.api.Repository(id=repo.id).sync()
        return repo.id

    def enable_sync_redhat_repo(self, rh_repo, org_id, timeout=1500):
        """Enable the RedHat repo, sync it and returns repo_id"""
        # Enable RH repo and fetch repository_id
        repo_id = self.enable_rhrepo_and_fetchid(
            basearch=rh_repo['basearch'],
            org_id=org_id,
            product=rh_repo['product'],
            repo=rh_repo['name'],
            reposet=rh_repo['reposet'],
            releasever=rh_repo['releasever'],
        )
        # Sync repository
        call_entity_method_with_timeout(
            self._satellite.api.Repository(id=repo_id).sync, timeout=timeout
        )
        return repo_id

    def one_to_one_names(self, name):
        """Generate the names Satellite might use for a one to one field.

        Example of usage::

            >>> one_to_one_names('person') == {'person_name', 'person_id'}
            True

        :param name: A field name.
        :returns: A set including both ``name`` and variations on ``name``.

        """
        return {f'{name}_name', f'{name}_id'}

    def configure_provisioning(self, org=None, loc=None, compute=False, os=None):
        """Create and configure org, loc, product, repo, cv, env. Update proxy,
        domain, subnet, compute resource, provision templates and medium with
        previously created entities and create a hostgroup using all mentioned
        entities.

        :param str org: Default Organization that should be used in both host
            discovering and host provisioning procedures
        :param str loc: Default Location that should be used in both host
            discovering and host provisioning procedures
        :param bool compute: If False creates a default Libvirt compute resource
        :param str os: Specify the os to be used while provisioning and to
            associate related entities to the specified os.
        :return: List of created entities that can be re-used further in
            provisioning or validation procedure (e.g. hostgroup or domain)
        """
        # Create new organization and location in case they were not passed
        if org is None:
            org = self._satellite.api.Organization().create()
        if loc is None:
            loc = self._satellite.api.Location(organization=[org]).create()
        if settings.repos.rhel7_os is None:
            raise ImproperlyConfigured('settings file is not configured for rhel os')
        # Create a new Life-Cycle environment
        lc_env = self._satellite.api.LifecycleEnvironment(organization=org).create()
        # Create a Product, Repository for custom RHEL7 contents
        product = self._satellite.api.Product(organization=org).create()
        repo = self._satellite.api.Repository(
            product=product, url=settings.repos.rhel7_os, download_policy='immediate'
        ).create()

        # Increased timeout value for repo sync and CV publishing and promotion
        try:
            old_task_timeout = entity_mixins.TASK_TIMEOUT
            entity_mixins.TASK_TIMEOUT = 3600
            repo.sync()
            # Create, Publish and promote CV
            content_view = self._satellite.api.ContentView(organization=org).create()
            content_view.repository = [repo]
            content_view = content_view.update(['repository'])
            content_view.publish()
            content_view = content_view.read()
            content_view.read().version[0].promote(data={'environment_ids': lc_env.id})
        finally:
            entity_mixins.TASK_TIMEOUT = old_task_timeout
        # Search for existing organization puppet environment, otherwise create a
        # new one, associate organization and location where it is appropriate.
        environments = self._satellite.api.Environment().search(
            query=dict(search=f'organization_id={org.id}')
        )
        if len(environments) > 0:
            environment = environments[0].read()
            environment.location.append(loc)
            environment = environment.update(['location'])
        else:
            environment = self._satellite.api.Environment(
                organization=[org], location=[loc]
            ).create()

        # Search for SmartProxy, and associate location
        proxy = self._satellite.api.SmartProxy().search(
            query={'search': f'name={settings.server.hostname}'}
        )
        proxy = proxy[0].read()
        if loc.id not in [location.id for location in proxy.location]:
            proxy.location.append(loc)
        if org.id not in [organization.id for organization in proxy.organization]:
            proxy.organization.append(org)
        proxy = proxy.update(['location', 'organization'])

        # Search for existing domain or create new otherwise. Associate org,
        # location and dns to it
        _, _, domain = settings.server.hostname.partition('.')
        domain = self._satellite.api.Domain().search(query={'search': f'name="{domain}"'})
        if len(domain) == 1:
            domain = domain[0].read()
            domain.location.append(loc)
            domain.organization.append(org)
            domain.dns = proxy
            domain = domain.update(['dns', 'location', 'organization'])
        else:
            domain = self._satellite.api.Domain(
                dns=proxy, location=[loc], organization=[org]
            ).create()

        # Search if subnet is defined with given network.
        # If so, just update its relevant fields otherwise,
        # Create new subnet
        network = settings.vlan_networking.subnet
        subnet = self._satellite.api.Subnet().search(query={'search': f'network={network}'})
        if len(subnet) == 1:
            subnet = subnet[0].read()
            subnet.domain = [domain]
            subnet.location.append(loc)
            subnet.organization.append(org)
            subnet.dns = proxy
            subnet.dhcp = proxy
            subnet.tftp = proxy
            subnet.discovery = proxy
            subnet.ipam = 'DHCP'
            subnet = subnet.update(
                ['domain', 'discovery', 'dhcp', 'dns', 'location', 'organization', 'tftp', 'ipam']
            )
        else:
            # Create new subnet
            subnet = self._satellite.api.Subnet(
                network=network,
                mask=settings.vlan_networking.netmask,
                domain=[domain],
                location=[loc],
                organization=[org],
                dns=proxy,
                dhcp=proxy,
                tftp=proxy,
                discovery=proxy,
                ipam='DHCP',
            ).create()

        # Search if Libvirt compute-resource already exists
        # If so, just update its relevant fields otherwise,
        # Create new compute-resource with 'libvirt' provider.
        # compute boolean is added to not block existing test's that depend on
        # Libvirt resource and use this same functionality to all CR's.
        if compute is False:
            resource_url = f'qemu+ssh://root@{settings.libvirt.libvirt_hostname}/system'
            comp_res = [
                res
                for res in self._satellite.api.LibvirtComputeResource().search()
                if res.provider == 'Libvirt' and res.url == resource_url
            ]
            if len(comp_res) > 0:
                computeresource = self._satellite.api.LibvirtComputeResource(
                    id=comp_res[0].id
                ).read()
                computeresource.location.append(loc)
                computeresource.organization.append(org)
                computeresource.update(['location', 'organization'])
            else:
                # Create Libvirt compute-resource
                self._satellite.api.LibvirtComputeResource(
                    provider='libvirt',
                    url=resource_url,
                    set_console_password=False,
                    display_type='VNC',
                    location=[loc.id],
                    organization=[org.id],
                ).create()

        # Get the Partition table ID
        ptable = (
            self._satellite.api.PartitionTable()
            .search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0]
            .read()
        )
        if loc.id not in [location.id for location in ptable.location]:
            ptable.location.append(loc)
        if org.id not in [organization.id for organization in ptable.organization]:
            ptable.organization.append(org)
        ptable = ptable.update(['location', 'organization'])

        # Get the OS ID
        if os is None:
            os = (
                self._satellite.api.OperatingSystem()
                .search(query={'search': 'name="RedHat" AND (major="6" OR major="7")'})[0]
                .read()
            )
        else:
            os_ver = os.split(' ')[1].split('.')
            os = (
                self._satellite.api.OperatingSystem()
                .search(
                    query={
                        'search': f'family="Redhat" AND major="{os_ver[0]}" '
                        f'AND minor="{os_ver[1]}")'
                    }
                )[0]
                .read()
            )

        # Get the Provisioning template_ID and update with OS, Org, Location
        provisioning_template = self._satellite.api.ProvisioningTemplate().search(
            query={'search': f'name="{DEFAULT_TEMPLATE}"'}
        )
        provisioning_template = provisioning_template[0].read()
        provisioning_template.operatingsystem.append(os)
        if org.id not in [organization.id for organization in provisioning_template.organization]:
            provisioning_template.organization.append(org)
        if loc.id not in [location.id for location in provisioning_template.location]:
            provisioning_template.location.append(loc)
        provisioning_template = provisioning_template.update(
            ['location', 'operatingsystem', 'organization']
        )

        # Get the PXE template ID and update with OS, Org, location
        pxe_template = self._satellite.api.ProvisioningTemplate().search(
            query={'search': f'name="{DEFAULT_PXE_TEMPLATE}"'}
        )
        pxe_template = pxe_template[0].read()
        pxe_template.operatingsystem.append(os)
        if org.id not in [organization.id for organization in pxe_template.organization]:
            pxe_template.organization.append(org)
        if loc.id not in [location.id for location in pxe_template.location]:
            pxe_template.location.append(loc)
        pxe_template = pxe_template.update(['location', 'operatingsystem', 'organization'])

        # Get the arch ID
        arch = (
            self._satellite.api.Architecture()
            .search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0]
            .read()
        )

        # Update the OS to associate arch, ptable, templates
        os.architecture.append(arch)
        os.ptable.append(ptable)
        os.provisioning_template.append(provisioning_template)
        os.provisioning_template.append(pxe_template)
        os = os.update(['architecture', 'provisioning_template', 'ptable'])
        # kickstart_repository is the content view and lce bind repo
        kickstart_repository = self._satellite.api.Repository().search(
            query=dict(content_view_id=content_view.id, environment_id=lc_env.id, name=repo.name)
        )[0]
        # Create Hostgroup
        host_group = self._satellite.api.HostGroup(
            architecture=arch,
            domain=domain.id,
            subnet=subnet.id,
            lifecycle_environment=lc_env.id,
            content_view=content_view.id,
            location=[loc.id],
            environment=environment.id,
            puppet_proxy=proxy,
            puppet_ca_proxy=proxy,
            content_source=proxy,
            kickstart_repository=kickstart_repository,
            root_pass=gen_string('alphanumeric'),
            operatingsystem=os.id,
            organization=[org.id],
            ptable=ptable.id,
        ).create()

        return {
            'host_group': host_group.name,
            'domain': domain.name,
            'environment': environment.name,
            'ptable': ptable.name,
            'subnet': subnet.name,
            'os': os.title,
        }

    def create_role_permissions(
        self, role, permissions_types_names, search=None
    ):  # pragma: no cover
        """Create role permissions found in dict permissions_types_names.

        :param role: nailgun.entities.Role
        :param permissions_types_names: a dict containing resource types
            and permission names to add to the role.
        :param search: string that contains search criteria that should be applied
            to the filter

              example usage::

               permissions_types_names = {
                   None: ['access_dashboard'],
                   'Organization': ['view_organizations'],
                   'Location': ['view_locations'],
                   'Katello::KTEnvironment': [
                       'view_lifecycle_environments',
                       'edit_lifecycle_environments',
                       'promote_or_remove_content_views_to_environments'
                   ]
               }
               role = entities.Role(name='example_role_name').create()
               create_role_permissions(
                   role,
                   permissions_types_names,
                   'name = {0}'.format(lce.name)
               )
        """
        for resource_type, permissions_name in permissions_types_names.items():
            if resource_type is None:
                permissions_entities = []
                for name in permissions_name:
                    result = self._satellite.api.Permission().search(
                        query={'search': f'name="{name}"'}
                    )
                    if not result:
                        raise self._satellite.api.APIResponseError(f'permission "{name}" not found')
                    if len(result) > 1:
                        raise self._satellite.api.APIResponseError(
                            f'found more than one entity for permission "{name}"'
                        )
                    entity_permission = result[0]
                    if entity_permission.name != name:
                        raise self._satellite.api.APIResponseError(
                            'the returned permission is different from the'
                            ' requested one "{} != {}"'.format(entity_permission.name, name)
                        )
                    permissions_entities.append(entity_permission)
            else:
                if not permissions_name:
                    raise ValueError(
                        'resource type "{}" empty. You must select at'
                        ' least one permission'.format(resource_type)
                    )

                resource_type_permissions_entities = self._satellite.api.Permission().search(
                    query={'per_page': '350', 'search': f'resource_type="{resource_type}"'}
                )
                if not resource_type_permissions_entities:
                    raise self._satellite.api.APIResponseError(
                        f'resource type "{resource_type}" permissions not found'
                    )

                permissions_entities = [
                    entity
                    for entity in resource_type_permissions_entities
                    if entity.name in permissions_name
                ]
                # ensure that all the requested permissions entities where
                # retrieved
                permissions_entities_names = {entity.name for entity in permissions_entities}
                not_found_names = set(permissions_name).difference(permissions_entities_names)
                if not_found_names:
                    raise self._satellite.api.APIResponseError(
                        f'permissions names entities not found "{not_found_names}"'
                    )
            self._satellite.api.Filter(
                permission=permissions_entities, role=role, search=search
            ).create()

    def create_discovered_host(self, name=None, ip_address=None, mac_address=None, options=None):
        """Creates a discovered host.

        :param str name: Name of discovered host.
        :param str ip_address: A valid ip address.
        :param str mac_address: A valid mac address.
        :param dict options: additional facts to add to discovered host
        :return: dict of ``entities.DiscoveredHost`` facts.
        """
        if name is None:
            name = gen_string('alpha')
        if ip_address is None:
            ip_address = gen_ipaddr()
        if mac_address is None:
            mac_address = gen_mac(multicast=False)
        if options is None:
            options = {}
        facts = {
            'name': name,
            'discovery_bootip': ip_address,
            'discovery_bootif': mac_address,
            'interfaces': 'eth0',
            'ipaddress': ip_address,
            'ipaddress_eth0': ip_address,
            'macaddress': mac_address,
            'macaddress_eth0': mac_address,
        }
        facts.update(options)
        return self._satellite.api.DiscoveredHost().facts(json={'facts': facts})

    def update_vm_host_location(self, vm_client, location_id):
        """Update vm client host location.

        :param vm_client: A subscribed Virtual Machine client instance.
        :param location_id: The location id to update the vm_client host with.
        """
        self._satellite.api.Host(
            id=vm_client.nailgun_host.id, location=self._satellite.api.Location(id=location_id)
        ).update(['location'])

    def check_create_os_with_title(self, os_title):
        """Check if the OS is present, if not create the required OS

        :param os_title: OS title to check, and create (like: RedHat 7.5)
        :return: Created or found OS
        """
        # Check if OS that image needs is present or no, If not create the OS
        result = self._satellite.api.OperatingSystem().search(
            query={'search': f'title="{os_title}"'}
        )
        if result:
            os = result[0]
        else:
            os_name, _, os_version = os_title.partition(' ')
            os_version_major, os_version_minor = os_version.split('.')
            os = self._satellite.api.OperatingSystem(
                name=os_name, major=os_version_major, minor=os_version_minor
            ).create()
        return os

    @contextmanager
    def satellite_setting(self, key_val: str):
        """Context Manager to update the satellite setting and revert on exit

        :param key_val: The setting name and value in format `setting_name=new_value`
        """
        try:
            name, value = key_val.split('=')
            try:
                setting = self._satellite.api.Setting().search(
                    query={'search': f'name={name.strip()}'}
                )[0]
            except IndexError:
                raise KeyError(f'The setting {name} in not available in satellite.')
            old_value = setting.value
            setting.value = value.strip()
            setting.update({'value'})
            yield
        except Exception:
            raise
        finally:
            setting.value = old_value
            setting.update({'value'})

    def update_provisioning_template(self, name=None, old=None, new=None):
        """Update provisioning template content

        :param str name: template provisioning name
        :param str old: current content
        :param str new: replace content

        :return bool: True/False
        """
        self.temp = (
            self._satellite.api.ProvisioningTemplate()
            .search(query={'per_page': '1000', 'search': f'name="{name}"'})[0]
            .read()
        )
        if old in self.temp.template:
            with self.template_update(self.temp):
                self.temp.template = self.temp.template.replace(old, new, 1)
                update = self.temp.update(['template'])
            return new in update.template
        elif new in self.temp.template:
            return True
        else:
            raise ValueError(f'{old} does not exists in template {name}')

    def disable_syncplan(self, sync_plan):
        """
        Disable sync plans after a test to reduce distracting task events, logs,
        and load on Satellite.
        Note that only a Sync Plan with a repo would create a noticeable load.
        You can also create sync plans in a disabled state where it is unlikely to impact the test.
        """
        sync_plan.enabled = False
        sync_plan = sync_plan.update(['enabled'])
        assert sync_plan.enabled is False

    @contextmanager
    def template_update(self, temp):
        template = temp
        if template.locked:
            template.locked = False
            template.update(['locked'])
        yield
        if not template.locked:
            template.locked = True
            template.update(['locked'])
