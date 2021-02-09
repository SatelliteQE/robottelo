"""Module containing convenience functions for working with the API."""
import time

from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_string
from inflector import Inflector
from nailgun import entities
from nailgun import entity_mixins
from nailgun.client import request

from robottelo import ssh
from robottelo.config import settings
from robottelo.config.base import ImproperlyConfigured
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DEFAULT_PXE_TEMPLATE
from robottelo.constants import DEFAULT_TEMPLATE
from robottelo.constants import REPO_TYPE
from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.constants.repos import FAKE_1_YUM_REPO


def call_entity_method_with_timeout(entity_callable, timeout=300, **kwargs):
    """Call Entity callable with a custom timeout

    :param entity_callable, the entity method object to call
    :param timeout: the time to wait for the method call to finish
    :param kwargs: the kwargs to pass to the entity callable

    Usage:
        call_entity_method_with_timeout(
            entities.Repository(id=repo_id).sync, timeout=1500)
    """
    original_task_timeout = entity_mixins.TASK_TIMEOUT
    entity_mixins.TASK_TIMEOUT = timeout
    try:
        entity_callable(**kwargs)
    finally:
        entity_mixins.TASK_TIMEOUT = original_task_timeout


def enable_rhrepo_and_fetchid(basearch, org_id, product, repo, reposet, releasever):
    """Enable a RedHat Repository and fetches it's Id.

    :param str org_id: The organization Id.
    :param str product: The product name in which repository exists.
    :param str reposet: The reposet name in which repository exists.
    :param str repo: The repository name who's Id is to be fetched.
    :param str basearch: The architecture of the repository.
    :param str optional releasever: The releasever of the repository.
    :return: Returns the repository Id.
    :rtype: str

    """
    product = entities.Product(name=product, organization=org_id).search()[0]
    r_set = entities.RepositorySet(name=reposet, product=product).search()[0]
    payload = {}
    if basearch is not None:
        payload['basearch'] = basearch
    if releasever is not None:
        payload['releasever'] = releasever
    payload['product_id'] = product.id
    r_set.enable(data=payload)
    result = entities.Repository(name=repo).search(query={'organization_id': org_id})
    return result[0].id


def promote(content_view_version, environment_id, force=False):
    """Call ``content_view_version.promote(…)``.

    :param content_view_version: A ``nailgun.entities.ContentViewVersion``
        object.
    :param environment_id: An environment ID.
    :param force: Whether to force the promotion or not. Only needed if
        promoting to a lifecycle environment that is not the next in order
        of sequence.
    :returns: Whatever ``nailgun.entities.ContentViewVersion.promote`` returns.

    """
    data = {'environment_ids': [environment_id], 'force': True if force else False}
    return content_view_version.promote(data=data)


def upload_manifest(organization_id, manifest):
    """Call ``nailgun.entities.Subscription.upload``.

    :param organization_id: An organization ID.
    :param manifest: A file object referencing a Red Hat Satellite 6 manifest.
    :returns: Whatever ``nailgun.entities.Subscription.upload`` returns.

    """
    return entities.Subscription().upload(
        data={'organization_id': organization_id}, files={'content': manifest}
    )


def publish_puppet_module(puppet_modules, repo_url, organization_id=None):
    """Creates puppet repo, sync it via provided url and publish using
    Content View publishing mechanism. It makes puppet class available
    via Puppet Environment created by Content View and returns Content
    View entity.

    :param puppet_modules: List of dictionaries with module 'author' and
        module 'name' fields.
    :param str repo_url: Url of the repo that can be synced using pulp:
        pulp repo or puppet forge.
    :param organization_id: Organization id that is shared between
        created entities.
    :return: `nailgun.entities.ContentView` entity.
    """
    if not organization_id:
        organization_id = entities.Organization().create().id
    # Create product and puppet modules repository
    product = entities.Product(organization=organization_id).create()
    repo = entities.Repository(product=product, content_type='puppet', url=repo_url).create()
    # Synchronize repo via provided URL
    repo.sync()
    # Add selected module to Content View
    cv = entities.ContentView(organization=organization_id).create()
    for module in puppet_modules:
        entities.ContentViewPuppetModule(
            author=module['author'], name=module['name'], content_view=cv
        ).create()
    # CV publishing will automatically create Environment and
    # Puppet Class entities
    cv.publish()
    return cv.read()


def delete_puppet_class(
    puppetclass_name, puppet_module=None, proxy_hostname=None, environment_name=None
):
    """Removes puppet class entity and uninstall puppet module from Capsule if
    puppet module name and Capsule details provided.

    :param str puppetclass_name: Name of the puppet class entity that should be
        removed.
    :param str puppet_module: Name of the module that should be
        uninstalled via puppet.
    :param str proxy_hostname: Hostname of the Capsule from which puppet module
        should be removed.
    :param str environment_name: Name of environment where puppet module was
        imported.
    """
    # Find puppet class
    puppet_classes = entities.PuppetClass().search(
        query={'search': f'name = "{puppetclass_name}"'}
    )
    # And all subclasses
    puppet_classes.extend(
        entities.PuppetClass().search(query={'search': f'name ~ "{puppetclass_name}::"'})
    )
    for puppet_class in puppet_classes:
        # Search and remove puppet class from affected hostgroups
        for hostgroup in puppet_class.read().hostgroup:
            hostgroup.delete_puppetclass(data={'puppetclass_id': puppet_class.id})
        # Search and remove puppet class from affected hosts
        for host in entities.Host().search(query={'search': f'class={puppet_class.name}'}):
            host.delete_puppetclass(data={'puppetclass_id': puppet_class.id})
        # Remove puppet class entity
        puppet_class.delete()
    # And remove puppet module from the system if puppet_module name provided
    if puppet_module and proxy_hostname and environment_name:
        ssh.command(f'puppet module uninstall --force {puppet_module}')
        env = entities.Environment().search(query={'search': f'name="{environment_name}"'})[0]
        proxy = entities.SmartProxy(name=proxy_hostname).search()[0]
        proxy.import_puppetclasses(environment=env)


def create_sync_custom_repo(
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
        org_id = entities.Organization().create().id
    product_name = product_name or gen_string('alpha')
    repo_name = repo_name or gen_string('alpha')
    # Creates new product and repository via API's
    product = entities.Product(name=product_name, organization=org_id).create()
    repo = entities.Repository(
        name=repo_name,
        url=repo_url or FAKE_1_YUM_REPO,
        content_type=repo_type or REPO_TYPE['yum'],
        product=product,
        unprotected=repo_unprotected,
        docker_upstream_name=docker_upstream_name,
    ).create()
    # Sync repository
    entities.Repository(id=repo.id).sync()
    return repo.id


def enable_sync_redhat_repo(rh_repo, org_id, timeout=1500):
    """Enable the RedHat repo, sync it and returns repo_id"""
    # Enable RH repo and fetch repository_id
    repo_id = enable_rhrepo_and_fetchid(
        basearch=rh_repo['basearch'],
        org_id=org_id,
        product=rh_repo['product'],
        repo=rh_repo['name'],
        reposet=rh_repo['reposet'],
        releasever=rh_repo['releasever'],
    )
    # Sync repository
    call_entity_method_with_timeout(entities.Repository(id=repo_id).sync, timeout=timeout)
    return repo_id


def cv_publish_promote(name=None, env_name=None, repo_id=None, org_id=None):
    """Create, publish and promote CV to selected environment"""
    if org_id is None:
        org_id = entities.Organization().create().id
    # Create Life-Cycle content environment
    kwargs = {'name': env_name} if env_name is not None else {}
    lce = entities.LifecycleEnvironment(organization=org_id, **kwargs).create()
    # Create content view(CV)
    kwargs = {'name': name} if name is not None else {}
    content_view = entities.ContentView(organization=org_id, **kwargs).create()
    # Associate YUM repo to created CV
    if repo_id is not None:
        content_view.repository = [entities.Repository(id=repo_id)]
        content_view = content_view.update(['repository'])
    # Publish content view
    content_view.publish()
    # Promote the content view version.
    promote(content_view.read().version[0], lce.id)
    return content_view.read()


def one_to_one_names(name):
    """Generate the names Satellite might use for a one to one field.

    Example of usage::

        >>> one_to_many_names('person') == {'person_name', 'person_id'}
        True

    :param name: A field name.
    :returns: A set including both ``name`` and variations on ``name``.

    """
    return {name + '_name', name + '_id'}


def one_to_many_names(name):
    """Generate the names Satellite might use for a one to many field.

    Example of usage::

        >>> one_to_many_names('person') == {'person', 'person_ids', 'people'}
        True

    :param name: A field name.
    :returns: A set including both ``name`` and variations on ``name``.

    """
    return {name, name + '_ids', Inflector().pluralize(name)}


def configure_provisioning(org=None, loc=None, compute=False, os=None):
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
        org = entities.Organization().create()
    if loc is None:
        loc = entities.Location(organization=[org]).create()
    if settings.rhel7_os is None:
        raise ImproperlyConfigured('settings file is not configured for rhel os')
    # Create a new Life-Cycle environment
    lc_env = entities.LifecycleEnvironment(organization=org).create()
    # Create a Product, Repository for custom RHEL6 contents
    product = entities.Product(organization=org).create()
    repo = entities.Repository(
        product=product, url=settings.rhel7_os, download_policy='immediate'
    ).create()

    # Increased timeout value for repo sync and CV publishing and promotion
    try:
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        entity_mixins.TASK_TIMEOUT = 3600
        repo.sync()
        # Create, Publish and promote CV
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], lc_env.id)
    finally:
        entity_mixins.TASK_TIMEOUT = old_task_timeout
    # Search for existing organization puppet environment, otherwise create a
    # new one, associate organization and location where it is appropriate.
    environments = entities.Environment().search(query=dict(search=f'organization_id={org.id}'))
    if len(environments) > 0:
        environment = environments[0].read()
        environment.location.append(loc)
        environment = environment.update(['location'])
    else:
        environment = entities.Environment(organization=[org], location=[loc]).create()

    # Search for SmartProxy, and associate location
    proxy = entities.SmartProxy().search(query={'search': f'name={settings.server.hostname}'})
    proxy = proxy[0].read()
    if loc.id not in [location.id for location in proxy.location]:
        proxy.location.append(loc)
    if org.id not in [organization.id for organization in proxy.organization]:
        proxy.organization.append(org)
    proxy = proxy.update(['location', 'organization'])

    # Search for existing domain or create new otherwise. Associate org,
    # location and dns to it
    _, _, domain = settings.server.hostname.partition('.')
    domain = entities.Domain().search(query={'search': f'name="{domain}"'})
    if len(domain) == 1:
        domain = domain[0].read()
        domain.location.append(loc)
        domain.organization.append(org)
        domain.dns = proxy
        domain = domain.update(['dns', 'location', 'organization'])
    else:
        domain = entities.Domain(dns=proxy, location=[loc], organization=[org]).create()

    # Search if subnet is defined with given network.
    # If so, just update its relevant fields otherwise,
    # Create new subnet
    network = settings.vlan_networking.subnet
    subnet = entities.Subnet().search(query={'search': f'network={network}'})
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
        subnet = entities.Subnet(
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
        resource_url = 'qemu+ssh://root@{}/system'.format(
            settings.compute_resources.libvirt_hostname
        )
        comp_res = [
            res
            for res in entities.LibvirtComputeResource().search()
            if res.provider == 'Libvirt' and res.url == resource_url
        ]
        if len(comp_res) > 0:
            computeresource = entities.LibvirtComputeResource(id=comp_res[0].id).read()
            computeresource.location.append(loc)
            computeresource.organization.append(org)
            computeresource.update(['location', 'organization'])
        else:
            # Create Libvirt compute-resource
            entities.LibvirtComputeResource(
                provider='libvirt',
                url=resource_url,
                set_console_password=False,
                display_type='VNC',
                location=[loc.id],
                organization=[org.id],
            ).create()

    # Get the Partition table ID
    ptable = (
        entities.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0].read()
    )
    if loc.id not in [location.id for location in ptable.location]:
        ptable.location.append(loc)
    if org.id not in [organization.id for organization in ptable.organization]:
        ptable.organization.append(org)
    ptable = ptable.update(['location', 'organization'])

    # Get the OS ID
    if os is None:
        os = (
            entities.OperatingSystem()
            .search(
                query={
                    'search': 'name="RedHat" AND (major="{}" OR major="{}")'.format(
                        RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION
                    )
                }
            )[0]
            .read()
        )
    else:
        os_ver = os.split(' ')[1].split('.')
        os = (
            entities.OperatingSystem()
            .search(
                query={
                    'search': f'family="Redhat" AND major="{os_ver[0]}" AND minor="{os_ver[1]}")'
                }
            )[0]
            .read()
        )

    # Get the Provisioning template_ID and update with OS, Org, Location
    provisioning_template = entities.ProvisioningTemplate().search(
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
    pxe_template = entities.ProvisioningTemplate().search(
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
        entities.Architecture()
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
    kickstart_repository = entities.Repository().search(
        query=dict(content_view_id=content_view.id, environment_id=lc_env.id, name=repo.name)
    )[0]
    # Create Hostgroup
    host_group = entities.HostGroup(
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


def create_role_permissions(role, permissions_types_names, search=None):  # pragma: no cover
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
                result = entities.Permission().search(query={'search': f'name="{name}"'})
                if not result:
                    raise entities.APIResponseError(f'permission "{name}" not found')
                if len(result) > 1:
                    raise entities.APIResponseError(
                        f'found more than one entity for permission "{name}"'
                    )
                entity_permission = result[0]
                if entity_permission.name != name:
                    raise entities.APIResponseError(
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

            resource_type_permissions_entities = entities.Permission().search(
                query={'per_page': '350', 'search': f'resource_type="{resource_type}"'}
            )
            if not resource_type_permissions_entities:
                raise entities.APIResponseError(
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
                raise entities.APIResponseError(
                    f'permissions names entities not found "{not_found_names}"'
                )
        entities.Filter(permission=permissions_entities, role=role, search=search).create()


def wait_for_tasks(search_query, search_rate=1, max_tries=10, poll_rate=None, poll_timeout=None):
    """Search for tasks by specified search query and poll them to ensure that
    task has finished.

    :param search_query: Search query that will be passed to API call.
    :param search_rate: Delay between searches.
    :param max_tries: How many times search should be executed.
    :param poll_rate: Delay between the end of one task check-up and
            the start of the next check-up. Parameter for
            ``nailgun.entities.ForemanTask.poll()`` method.
    :param poll_timeout: Maximum number of seconds to wait until timing out.
            Parameter for ``nailgun.entities.ForemanTask.poll()`` method.
    :return: List of ``nailgun.entities.ForemanTasks`` entities.
    :raises: ``AssertionError``. If not tasks were found until timeout.
    """
    for _ in range(max_tries):
        tasks = entities.ForemanTask().search(query={'search': search_query})
        if len(tasks) > 0:
            for task in tasks:
                task.poll(poll_rate=poll_rate, timeout=poll_timeout)
            break
        else:
            time.sleep(search_rate)
    else:
        raise AssertionError(f"No task was found using query '{search_query}'")
    return tasks


def wait_for_syncplan_tasks(repo_backend_id=None, timeout=10, repo_name=None):
    """Search the pulp tasks and identify repositories sync tasks with
    specified name or backend_identifier

    :param repo_backend_id: The Backend ID for the repository to identify the
        repo in Pulp environment
    :param timeout: Value to decided how long to check for the Sync task
    :param repo_name: If repo_backend_id can not be passed, pass the repo_name
    """
    if repo_name:
        repo_backend_id = (
            entities.Repository()
            .search(query={'search': f'name="{repo_name}"', 'per_page': '1000'})[0]
            .backend_identifier
        )
    # Fetch the Pulp password
    pulp_pass = ssh.command(
        'grep "^default_password" /etc/pulp/server.conf | awk \'{print $2}\''
    ).stdout[0]
    # Set the Timeout value
    timeup = time.time() + int(timeout) * 60
    # Search Filter to filter out the task based on backend-id and sync action
    filtered_req = {
        'criteria': {
            'filters': {
                'tags': {'$in': [f"pulp:repository:{repo_backend_id}"]},
                'task_type': {'$in': ["pulp.server.managers.repo.sync.sync"]},
            }
        }
    }
    while True:
        if time.time() > timeup:
            raise entities.APIResponseError(f'Pulp task with repo_id {repo_backend_id} not found')
        # Send request to pulp API to get the task info
        req = request(
            'POST',
            f'{settings.server.get_url()}/pulp/api/v2/tasks/search/',
            verify=False,
            auth=('admin', f'{pulp_pass}'),
            headers={'content-type': 'application/json'},
            data=filtered_req,
        )
        # Check Status code of response
        if req.status_code != 200:
            raise entities.APIResponseError(f'Pulp task with repo_id {repo_backend_id} not found')
        # Check content of response
        # It is '[]' string for empty content when backend_identifier is wrong
        if len(req.content) > 2:
            if req.json()[0].get('state') in ['finished']:
                return True
            elif req.json()[0].get('error'):
                raise AssertionError(
                    f"Pulp task with repo_id {repo_backend_id} error or not found: "
                    f"'{req.json().get('error')}'"
                )
        time.sleep(2)


def wait_for_errata_applicability_task(
    host_id, from_when, search_rate=1, max_tries=10, poll_rate=None, poll_timeout=15
):
    """Search the generate applicability task for given host and make sure it finishes

    :param int host_id: Content host ID of the host where we are regenerating applicability.
    :param int from_when: Timestamp (in UTC) to limit number of returned tasks to investigate.
    :param int search_rate: Delay between searches.
    :param int max_tries: How many times search should be executed.
    :param int poll_rate: Delay between the end of one task check-up and
            the start of the next check-up. Parameter for
            ``nailgun.entities.ForemanTask.poll()`` method.
    :param int poll_timeout: Maximum number of seconds to wait until timing out.
            Parameter for ``nailgun.entities.ForemanTask.poll()`` method.
    :return: Relevant errata applicability task.
    :raises: ``AssertionError``. If not tasks were found for given host until timeout.
    """
    assert isinstance(host_id, int), 'Param host_id have to be int'
    assert isinstance(from_when, int), 'Param from_when have to be int'
    now = int(time.time())
    assert from_when <= now, 'Param from_when have to be timestamp in the past'
    for _ in range(max_tries):
        now = int(time.time())
        max_age = now - from_when + 1
        search_query = (
            '( label = Actions::Katello::Host::GenerateApplicability OR label = '
            'Actions::Katello::Host::UploadPackageProfile ) AND started_at > "%s seconds ago"'
            % max_age
        )
        tasks = entities.ForemanTask().search(query={'search': search_query})
        tasks_finished = 0
        for task in tasks:
            if (
                task.label == 'Actions::Katello::Host::GenerateApplicability'
                and host_id in task.input['host_ids']
            ):
                task.poll(poll_rate=poll_rate, timeout=poll_timeout)
                tasks_finished += 1
            elif (
                task.label == 'Actions::Katello::Host::UploadPackageProfile'
                and host_id == task.input['host']['id']
            ):
                task.poll(poll_rate=poll_rate, timeout=poll_timeout)
                tasks_finished += 1
        if tasks_finished > 0:
            break
        time.sleep(search_rate)
    else:
        raise AssertionError(
            f"No task was found using query '{search_query}' for host '{host_id}'"
        )


def create_discovered_host(name=None, ip_address=None, mac_address=None, options=None):
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
    return entities.DiscoveredHost().facts(json={'facts': facts})


def update_vm_host_location(vm_client, location_id):
    """Update vm client host location.

    :param vm_client: A subscribed Virtual Machine client instance.
    :param location_id: The location id to update the vm_client host with.
    """
    host = entities.Host().search(query={'search': f'name={vm_client.hostname}'})[0]
    host.location = entities.Location(id=location_id)
    host.update(['location'])


def check_create_os_with_title(os_title):
    """Check if the OS is present, if not create the required OS

    :param os_title: OS title to check, and create (like: RedHat 7.5)
    :return: Created or found OS
    """
    # Check if OS that image needs is present or no, If not create the OS
    result = entities.OperatingSystem().search(query={'search': f'title="{os_title}"'})
    if result:
        os = result[0]
    else:
        os_name, _, os_version = os_title.partition(' ')
        os_version_major, os_version_minor = os_version.split('.')
        os = entities.OperatingSystem(
            name=os_name, major=os_version_major, minor=os_version_minor
        ).create()
    return os


def attach_custom_product_subscription(prod_name=None, host_name=None):
    """Attach custom product subscription to client host
    :param str prod_name: custom product name
    :param str host_name: client host name
    """
    host = entities.Host().search(query={'search': f'{host_name}'})[0]
    product_subscription = entities.Subscription().search(query={'search': f'name={prod_name}'})[0]
    entities.HostSubscription(host=host.id).add_subscriptions(
        data={'subscriptions': [{'id': product_subscription.id, 'quantity': 1}]}
    )


class templateupdate:
    """Context Manager to unlock lock template for updating"""

    def __init__(self, temp):
        """Context manager that takes entities.ProvisioningTemplate's object

        :param entities.ProvisioningTemplate temp: entities.ProvisioningTemplate's object
        """
        self.temp = temp
        if not isinstance(self.temp, entities.ProvisioningTemplate):
            raise TypeError(
                'The template should be of type entities.ProvisioningTemplate, {} given'.format(
                    type(temp)
                )
            )

    def __enter__(self):
        """Unlocks template for update"""
        if self.temp.locked:
            self.temp.locked = False
            self.temp.update(['locked'])

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Locks template after update"""
        if not self.temp.locked:
            self.temp.locked = True
            self.temp.update(['locked'])


def update_provisioning_template(name=None, old=None, new=None):
    """Update provisioning template content

    :param str name: template provisioning name
    :param str old: current content
    :param str new: replace content

    :return bool: True/False
    """
    temp = (
        entities.ProvisioningTemplate()
        .search(query={'per_page': '1000', 'search': f'name="{name}"'})[0]
        .read()
    )
    if old in temp.template:
        with templateupdate(temp):
            temp.template = temp.template.replace(old, new, 1)
            update = temp.update(['template'])
        return new in update.template
    elif new in temp.template:
        return True
    else:
        raise ValueError(f'{old} does not exists in template {name}')


def apply_package_filter(content_view, repo, package, inclusion=True):
    """Apply package filter on content view

    :param content_view: entity content view
    :param repo: entity repository
    :param str package: package name to filter
    :param bool inclusion: True/False based on include or exclude filter

    :return list : list of content view versions
    """
    cv_filter = entities.RPMContentViewFilter(
        content_view=content_view, inclusion=inclusion, repository=[repo]
    ).create()
    cv_filter_rule = entities.ContentViewFilterRule(
        content_view_filter=cv_filter, name=package
    ).create()
    assert cv_filter.id == cv_filter_rule.content_view_filter.id
    content_view.publish()
    content_view = content_view.read()
    content_view_version_info = content_view.version[0].read()
    return content_view_version_info


def create_org_admin_role(orgs, locs, name=None):
    """Helper function to create org admin role for particular
    organizations and locations by cloning 'Organization admin' role.

    :param list orgs: The list of organizations for which the org admin is
        being created
    :param list locs: The list of locations for which the org admin is
        being created
    :param str name: The name of cloned Org Admin role, autogenerates if None provided
    :return dict: The object of ```nailgun.Role``` of Org Admin role.
    """
    name = gen_string('alpha') if not name else name
    default_org_admin = entities.Role().search(query={'search': 'name="Organization admin"'})
    org_admin = entities.Role(id=default_org_admin[0].id).clone(
        data={'role': {'name': name, 'organization_ids': orgs or [], 'location_ids': locs or []}}
    )
    return entities.Role(id=org_admin['id']).read()


def create_org_admin_user(orgs, locs):
    """Helper function to create an Org Admin user by assigning org admin role and assign
    taxonomies to Role and User

    The taxonomies for role and user will be assigned based on parameters of this function

    :return User: Returns the ```nailgun.entities.User``` object with passwd attr
    """
    # Create Org Admin Role
    org_admin = create_org_admin_role(orgs=orgs, locs=locs)
    # Create Org Admin User
    user_login = gen_string('alpha')
    user_passwd = gen_string('alphanumeric')
    user = entities.User(
        login=user_login,
        password=user_passwd,
        organization=orgs,
        location=locs,
        role=[org_admin.id],
    ).create()
    user.passwd = user_passwd
    return user


def skip_yum_update_during_provisioning(template=None, reverse=False):
    """Hides the yum update command with echo text

    :param str template: The template name where the yum update will be hidden
    :param bool reverse: Reverses the echo text to yum update
    :return: Boolean True on success else exception
    """
    old = 'yum -t -y update'
    new = 'echo "Yum update skipped for faster automation testing"'
    if not reverse:
        return update_provisioning_template(name=template, old=old, new=new)
    else:
        return update_provisioning_template(name=template, old=new, new=old)


def set_hammer_api_timeout(timeout=-1, reverse=False):
    """Set hammer API request timeout on Satellite

    :param int timeout: request timeout in seconds
    :param bool reverse: Reverses the request timeout
    :return: ssh.command
    """
    default_timeout = f':request_timeout: {120}'
    new_timeout = f':request_timeout: {timeout}'
    if not reverse:
        return ssh.command(
            "sed -ie 's/{}/{}/' ~/.hammer/cli.modules.d/foreman.yml".format(
                default_timeout, new_timeout
            )
        )
    else:
        return ssh.command(
            "sed -ie 's/{}/{}/' ~/.hammer/cli.modules.d/foreman.yml".format(
                new_timeout, default_timeout
            )
        )


def update_rhsso_settings_in_satellite(revert=False):
    """Update or Revert the RH-SSO settings in satellite"""
    rhhso_settings = {
        'authorize_login_delegation': True,
        'authorize_login_delegation_auth_source_user_autocreate': 'External',
        'login_delegation_logout_url': f'https://{settings.server.hostname}/users/extlogout',
        'oidc_algorithm': 'RS256',
        'oidc_audience': [f'{settings.server.hostname}-foreman-openidc'],
        'oidc_issuer': f'{settings.rhsso.host_url}/auth/realms/{settings.rhsso.realm}',
        'oidc_jwks_url': f'{settings.rhsso.host_url}/auth/realms'
        f'/{settings.rhsso.realm}/protocol/openid-connect/certs',
    }
    if revert:
        setting_entity = entities.Setting().search(
            query={'search': 'name=authorize_login_delegation'}
        )[0]
        setting_entity.value = False
        setting_entity.update({'value'})
    else:
        for setting_name, setting_value in rhhso_settings.items():
            setting_entity = entities.Setting().search(query={'search': f'name={setting_name}'})[0]
            setting_entity.value = setting_value
            setting_entity.update({'value'})
