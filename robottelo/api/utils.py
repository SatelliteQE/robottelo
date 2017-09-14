# -*- encoding: utf-8 -*-
"""Module containing convenience functions for working with the API."""
import time

from fauxfactory import gen_string
from inflector import Inflector
from nailgun import entities, entity_mixins
from robottelo import manifests
from robottelo import ssh
from robottelo.cli.proxy import Proxy
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_LOC,
    DEFAULT_PTABLE,
    DEFAULT_PXE_TEMPLATE,
    DEFAULT_SUBSCRIPTION_NAME,
    DEFAULT_TEMPLATE,
    PERMISSIONS_WITH_BZ,
    PRDS,
    REPOS,
    REPOSET,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
)
from robottelo.decorators import bz_bug_is_open


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


def enable_rhrepo_and_fetchid(basearch, org_id, product, repo,
                              reposet, releasever):
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
    r_set.enable(data=payload)
    result = entities.Repository(name=repo).search(
        query={'organization_id': org_id})
    if bz_bug_is_open(1252101):
        for _ in range(5):
            if len(result) > 0:
                break
            time.sleep(5)
            result = entities.Repository(name=repo).search(
                query={'organization_id': org_id})
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
    data = {
        u'environment_id': environment_id,
        u'force': True if force else False,
    }
    return content_view_version.promote(data=data)


def upload_manifest(organization_id, manifest):
    """Call ``nailgun.entities.Subscription.upload``.

    :param organization_id: An organization ID.
    :param manifest: A file object referencing a Red Hat Satellite 6 manifest.
    :returns: Whatever ``nailgun.entities.Subscription.upload`` returns.

    """
    return entities.Subscription().upload(
        data={'organization_id': organization_id},
        files={'content': manifest},
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
    repo = entities.Repository(
        product=product,
        content_type='puppet',
        url=repo_url
    ).create()
    # Synchronize repo via provided URL
    repo.sync()
    # Add selected module to Content View
    cv = entities.ContentView(organization=organization_id).create()
    for module in puppet_modules:
        entities.ContentViewPuppetModule(
            author=module['author'],
            name=module['name'],
            content_view=cv,
        ).create()
    # CV publishing will automatically create Environment and
    # Puppet Class entities
    cv.publish()
    return cv.read()


def delete_puppet_class(puppetclass_name, puppet_module=None,
                        proxy_hostname=None, environment_name=None):
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
        query={'search': 'name = "{0}"'.format(puppetclass_name)}
    )
    # And all subclasses
    puppet_classes.extend(entities.PuppetClass().search(
        query={'search': 'name ~ "{0}::"'.format(puppetclass_name)})
    )
    for puppet_class in puppet_classes:
        # Search and remove puppet class from affected hostgroups
        for hostgroup in puppet_class.read().hostgroup:
            hostgroup.delete_puppetclass(
                data={'puppetclass_id': puppet_class.id}
            )
        # Search and remove puppet class from affected hosts
        for host in entities.Host().search(
                query={'search': 'class={0}'.format(puppet_class.name)}):
            host.delete_puppetclass(
                data={'puppetclass_id': puppet_class.id}
            )
        # Remove puppet class entity
        puppet_class.delete()
    # And remove puppet module from the system if puppet_module name provided
    if puppet_module and proxy_hostname and environment_name:
        ssh.command(
            'puppet module uninstall --force {0}'.format(puppet_module))
        env = entities.Environment().search(
            query={'search': 'name="{0}"'.format(environment_name)}
        )[0]
        proxy = entities.SmartProxy(name=proxy_hostname).search()[0]
        proxy.import_puppetclasses(environment=env)


def one_to_one_names(name):
    """Generate the names Satellite might use for a one to one field.

    Example of usage::

        >>> one_to_many_names('person') == {'person_name', 'person_id'}
        True

    :param name: A field name.
    :returns: A set including both ``name`` and variations on ``name``.

    """
    return set((name + '_name', name + '_id'))


def one_to_many_names(name):
    """Generate the names Satellite might use for a one to many field.

    Example of usage::

        >>> one_to_many_names('person') == {'person', 'person_ids', 'people'}
        True

    :param name: A field name.
    :returns: A set including both ``name`` and variations on ``name``.

    """
    return set((name, name + '_ids', Inflector().pluralize(name)))


def configure_provisioning(org=None, loc=None, compute=False):
    """Create and configure org, loc, product, repo, cv, env. Update proxy,
    domain, subnet, compute resource, provision templates and medium with
    previously created entities and create a hostgroup using all mentioned
    entities.

    :param org: Default Organization that should be used in both host
        discovering and host provisioning procedures
    :param loc: Default Location that should be used in both host
        discovering and host provisioning procedures
    :return: List of created entities that can be re-used further in
        provisioning or validation procedure (e.g. hostgroup or domain)
    """
    # Create new organization and location in case they were not passed
    if org is None:
        org = entities.Organization().create()
    if loc is None:
        loc = entities.Location(organization=[org]).create()
    # Create a new Life-Cycle environment
    lc_env = entities.LifecycleEnvironment(organization=org).create()
    # Create a Product, Repository for custom RHEL6 contents
    product = entities.Product(organization=org).create()
    repo = entities.Repository(
        product=product,
        url=settings.rhel7_os
    ).create()

    # Increased timeout value for repo sync
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
    # Search for puppet environment and associate location
    environment = entities.Environment(
        organization=[org.id]).search()[0].read()
    environment.location.append(loc)
    environment = environment.update(['location'])

    # Search for SmartProxy, and associate location
    proxy = entities.SmartProxy().search(
        query={
            u'search': u'name={0}'.format(
                settings.server.hostname)
        }
    )
    proxy = proxy[0].read()
    proxy.location.append(loc)
    proxy = proxy.update(['location'])
    proxy.organization.append(org)
    proxy = proxy.update(['organization'])

    # Search for existing domain or create new otherwise. Associate org,
    # location and dns to it
    _, _, domain = settings.server.hostname.partition('.')
    domain = entities.Domain().search(
        query={
            u'search': u'name="{0}"'.format(domain)
        }
    )
    if len(domain) == 1:
        domain = domain[0].read()
        domain.location.append(loc)
        domain.organization.append(org)
        domain.dns = proxy
        domain = domain.update(['dns', 'location', 'organization'])
    else:
        domain = entities.Domain(
            dns=proxy,
            location=[loc],
            organization=[org],
        ).create()

    # Search if subnet is defined with given network.
    # If so, just update its relevant fields otherwise,
    # Create new subnet
    network = settings.vlan_networking.subnet
    subnet = entities.Subnet().search(
        query={u'search': u'network={0}'.format(network)}
    )
    if len(subnet) == 1:
        subnet = subnet[0].read()
        subnet.domain = [domain]
        subnet.location.append(loc)
        subnet.organization.append(org)
        subnet.dns = proxy
        subnet.dhcp = proxy
        subnet.tftp = proxy
        subnet.discovery = proxy
        subnet = subnet.update([
            'domain',
            'dhcp',
            'tftp',
            'dns',
            'discovery',
            'location',
            'organization',
        ])
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
            discovery=proxy
        ).create()

    # Search if Libvirt compute-resource already exists
    # If so, just update its relevant fields otherwise,
    # Create new compute-resource with 'libvirt' provider.
    # compute boolean is added to not block existing test's that depend on
    # Libvirt resource and use this same functionality to all CR's.
    if compute is False:
        resource_url = u'qemu+ssh://root@{0}/system'.format(
            settings.compute_resources.libvirt_hostname
        )
        comp_res = [
            res for res in entities.LibvirtComputeResource().search()
            if res.provider == 'Libvirt' and res.url == resource_url
        ]
        if len(comp_res) > 0:
            computeresource = entities.LibvirtComputeResource(
                id=comp_res[0].id).read()
            computeresource.location.append(loc)
            computeresource.organization.append(org)
            computeresource = computeresource.update([
                'location', 'organization'])
        else:
            # Create Libvirt compute-resource
            computeresource = entities.LibvirtComputeResource(
                provider=u'libvirt',
                url=resource_url,
                set_console_password=False,
                display_type=u'VNC',
                location=[loc.id],
                organization=[org.id],
            ).create()
    # Get the Partition table ID
    ptable = entities.PartitionTable().search(
        query={
            u'search': u'name="{0}"'.format(DEFAULT_PTABLE)
        }
    )[0].read()

    # Get the OS ID
    os = entities.OperatingSystem().search(query={
        u'search': u'name="RedHat" AND (major="{0}" OR major="{1}")'
        .format(RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
        })[0].read()

    # Get the Provisioning template_ID and update with OS, Org, Location
    provisioning_template = entities.ConfigTemplate().search(
        query={
            u'search': u'name="{0}"'.format(DEFAULT_TEMPLATE)
        }
    )
    provisioning_template = provisioning_template[0].read()
    provisioning_template.operatingsystem.append(os)
    provisioning_template.organization.append(org)
    provisioning_template.location.append(loc)
    provisioning_template = provisioning_template.update([
        'location',
        'operatingsystem',
        'organization'
    ])

    # Get the PXE template ID and update with OS, Org, location
    pxe_template = entities.ConfigTemplate().search(
        query={
            u'search': u'name="{0}"'.format(DEFAULT_PXE_TEMPLATE)
        }
    )
    pxe_template = pxe_template[0].read()
    pxe_template.operatingsystem.append(os)
    pxe_template.organization.append(org)
    pxe_template.location.append(loc)
    pxe_template = pxe_template.update(
        ['location', 'operatingsystem', 'organization']
    )

    # Get the arch ID
    arch = entities.Architecture().search(
        query={u'search': u'name="x86_64"'}
    )[0].read()

    # Update the OS to associate arch, ptable, templates
    os.architecture.append(arch)
    os.ptable.append(ptable)
    os.config_template.append(provisioning_template)
    os.config_template.append(pxe_template)
    os = os.update([
        'architecture',
        'config_template',
        'ptable',
    ])

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
    }


def get_role_by_bz(bz_id):
    """Create and configure custom role entity for the testing of specific bugs
     This function will read the dictionary of permissions and their associated
     bugzilla id's from robottelo.constants "PERMISSIONS_WITH_BZ",
     these permissions will create filter and a single role will be created
     from all the filters.

     :param bz_id: This is the bugzilla id that is specified in the
        PERMISSIONS_WITH_BZ list, all the permissions associated with the bz_id
        will be fetched and filters will be created
     :return: A single role entity will be created from all the created filters
     """
    role = entities.Role().create()
    for perms in PERMISSIONS_WITH_BZ.values():
        perms_with_bz = [x for x in perms if bz_id in x.get('bz', [])]
        if perms_with_bz:
            permissions = [
                entities.Permission(name=perm['name']).search()[0]
                for perm in perms_with_bz
                ]
            entities.Filter(permission=permissions, role=role).create()
    return role.read()


def create_role_permissions(role, permissions_types_names):  # pragma: no cover
    """Create role permissions found in dict permissions_types_names.

    :param role: nailgun.entities.Role
    :param permissions_types_names: a dict containing resource types
        and permission names to add to the role, example usage.

          ::

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
           create_role_permissions(role, permissions_types_names)
    """
    for resource_type, permissions_name in permissions_types_names.items():
        if resource_type is None:
            permissions_entities = []
            for name in permissions_name:
                result = entities.Permission(name=name).search()
                if not result:
                    raise entities.APIResponseError(
                        'permission "{}" not found'.format(name))
                if len(result) > 1:
                    raise entities.APIResponseError(
                        'found more than one entity for permission'
                        ' "{}"'.format(name)
                    )
                entity_permission = result[0]
                if entity_permission.name != name:
                    raise entities.APIResponseError(
                        'the returned permission is different from the'
                        ' requested one "{0} != {1}"'.format(
                            entity_permission.name, name)
                    )
                permissions_entities.append(entity_permission)
        else:
            if not permissions_name:
                raise ValueError('resource type "{}" empty. You must select at'
                                 ' least one permission'.format(resource_type))

            resource_type_permissions_entities = entities.Permission(
                resource_type=resource_type).search()
            if not resource_type_permissions_entities:
                raise entities.APIResponseError(
                    'resource type "{}" permissions not found'.format(
                        resource_type)
                )

            permissions_entities = [
                entity
                for entity in resource_type_permissions_entities
                if entity.name in permissions_name
            ]
            # ensure that all the requested permissions entities where
            # retrieved
            permissions_entities_names = {
                entity.name for entity in permissions_entities
            }
            not_found_names = set(permissions_name).difference(
                permissions_entities_names)
            if not_found_names:
                raise entities.APIResponseError(
                    'permissions names entities not found'
                    ' "{}"'.format(not_found_names)
                )
        entities.Filter(
            permission=permissions_entities,
            role=role,
            search=None
        ).create()


def configure_puppet_test():
    sat6_hostname = settings.server.hostname
    repo_values = [
        {'repo': REPOS['rhst6']['name'], 'reposet': REPOSET['rhst6']},
        {'repo': REPOS['rhst7']['name'], 'reposet': REPOSET['rhst7']},
    ]

    # step 1: Create new organization and environment.
    org = entities.Organization(name=gen_string('alpha')).create()
    loc = entities.Location(name=DEFAULT_LOC).search()[0].read()
    puppet_env = entities.Environment(
        name='production').search()[0].read()
    puppet_env.location.append(loc)
    puppet_env.organization.append(org)
    puppet_env = puppet_env.update(['location', 'organization'])
    Proxy.import_classes({
        u'environment': puppet_env.name,
        u'name': sat6_hostname,
    })
    env = entities.LifecycleEnvironment(
        organization=org,
        name=gen_string('alpha')
    ).create()

    # step 2: Clone and Upload manifest
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)

    # step 3: Sync RedHat Sattools RHEL6 and RHEL7 repository
    repos = [
        entities.Repository(id=enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=PRDS['rhel'],
            repo=value['repo'],
            reposet=value['reposet'],
            releasever=None,
        ))
        for value in repo_values
        ]
    for repo in repos:
        repo.sync()

    # step 4: Create content view
    content_view = entities.ContentView(
        organization=org,
        name=gen_string('alpha')
    ).create()

    # step 5: Associate repository to new content view
    content_view.repository = repos
    content_view = content_view.update(['repository'])

    # step 6: Publish content view and promote to lifecycle env.
    content_view.publish()
    content_view = content_view.read()
    promote(content_view.version[0], env.id)

    # step 7: Create activation key
    ak_name = gen_string('alpha')
    activation_key = entities.ActivationKey(
        name=ak_name,
        environment=env,
        organization=org,
        content_view=content_view,
    ).create()

    # step 7.1: Walk through the list of subscriptions.
    # Find the "Employee SKU" and attach it to the
    # recently-created activation key.
    for sub in entities.Subscription(organization=org).search():
        if sub.read_json()['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
            # 'quantity' must be 1, not subscription['quantity']. Greater
            # values produce this error: "RuntimeError: Error: Only pools
            # with multi-entitlement product subscriptions can be added to
            # the activation key with a quantity greater than one."
            activation_key.add_subscriptions(data={
                'quantity': 1,
                'subscription_id': sub.id,
            })
            break
    for content_label in [REPOS['rhst6']['id'], REPOS['rhst7']['id']]:
        # step 7.2: Enable product content
        activation_key.content_override(data={'content_override': {
            u'content_label': content_label,
            u'value': u'1',
        }})

    return {
        'org_name': org.name,
        'cv_name': content_view.name,
        'sat6_hostname': settings.server.hostname,
        'ak_name': ak_name,
        'env_name': env.name,
    }


def wait_for_tasks(query, search_rate=1, max_tries=10):
    """Search for tasks by specified search query and poll them to ensure that
    task has finished.

    :param query: Search query that will be passed to API call.
    :param search_rate: Delay between searches.
    :param max_tries: How many times search should be executed.
    :raises: ``AssertionError``. If not tasks were found until timeout.
    :return: List of ``nailgun.entities.ForemanTasks`` entities.
    """
    for _ in range(max_tries):
        tasks = entities.ForemanTask().search(query={'search': query})
        if len(tasks) > 0:
            for task in tasks:
                task.poll()
            break
        else:
            time.sleep(search_rate)
    else:
        raise AssertionError(
            "No task was found using query '{}'".format(query))
    return tasks
