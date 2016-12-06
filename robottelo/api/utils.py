# -*- encoding: utf-8 -*-
"""Module containing convenience functions for working with the API."""
import time

from fauxfactory import gen_string
from inflector import Inflector
from nailgun import entities, entity_mixins
from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_PTABLE,
    DEFAULT_PXE_TEMPLATE,
    DEFAULT_TEMPLATE,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
)
from robottelo.decorators import bz_bug_is_open


def enable_rhrepo_and_fetchid(basearch, org_id, product, repo,
                              reposet, releasever):
    """Enable a RedHat Repository and fetches it's Id.

    :param str org_id: The organization Id.
    :param str product: The product name in which repository exists.
    :param str reposet: The reposet name in which repository exists.
    :param str repo: The repository name who's Id is to be fetched.
    :param str basearch: The architecture of the repository.
    :param str releasever: The releasever of the repository.
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


def configure_provisioning(org=None, loc=None):
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
        org = entities.Organization(name=gen_string('alpha')).create()
        # org_name = org.name
    if loc is None:
        loc = entities.Location(
            name=gen_string('alpha'),
            organization=[org],
        ).create()
        # loc_name = loc.name
    # Create a new Life-Cycle environment
    lc_env = entities.LifecycleEnvironment(
        name=gen_string('alpha'),
        organization=org
    ).create()
    # Create a Product, Repository for custom RHEL6 contents
    product = entities.Product(
        name=gen_string('alpha'),
        organization=org
    ).create()
    repo = entities.Repository(
        name=gen_string('alpha'),
        product=product,
        url=settings.rhel7_os
    ).create()

    # Increased timeout value for repo sync
    old_task_timeout = entity_mixins.TASK_TIMEOUT
    entity_mixins.TASK_TIMEOUT = 3600
    repo.sync()

    # Create, Publish and promote CV
    content_view = entities.ContentView(
        name=gen_string('alpha'),
        organization=org
    ).create()
    content_view.repository = [repo]
    content_view = content_view.update(['repository'])
    content_view.publish()
    content_view = content_view.read()
    promote(content_view.version[0], lc_env.id)
    entity_mixins.TASK_TIMEOUT = old_task_timeout
    # Search for puppet environment and associate location
    environment = entities.Environment(
        organization=[org.id]).search()[0]
    environment.location = [loc]
    environment = environment.update(['location'])

    # Search for SmartProxy, and associate location
    proxy = entities.SmartProxy().search(
        query={
            u'search': u'name={0}'.format(
                settings.server.hostname)
        }
    )[0]
    proxy.location = [loc]
    proxy = proxy.update(['location'])
    proxy.organization = [org]
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
        subnet = subnet[0]
        subnet.domain = [domain]
        subnet.location = [loc]
        subnet.organization = [org]
        subnet.dns = proxy
        subnet.dhcp = proxy
        subnet.tftp = proxy
        subnet.discovery = proxy
        subnet = subnet.update([
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
        subnet = entities.Subnet(
            name=gen_string('alpha'),
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
    resource_url = u'qemu+ssh://root@{0}/system'.format(
        settings.compute_resources.libvirt_hostname
    )
    comp_res = [
        res for res in entities.LibvirtComputeResource().search()
        if res.provider == 'Libvirt' and res.url == resource_url
    ]
    if len(comp_res) >= 1:
        computeresource = entities.LibvirtComputeResource(
            id=comp_res[0].id).read()
        computeresource.location.append(loc)
        computeresource.organization.append(org)
        computeresource = computeresource.update([
            'location', 'organization'])
    else:
        # Create Libvirt compute-resource
        computeresource = entities.LibvirtComputeResource(
            name=gen_string('alpha'),
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
    )[0]

    # Get the OS ID
    os = entities.OperatingSystem().search(query={
        u'search': u'name="RedHat" AND (major="{0}" OR major="{1}")'
        .format(RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
        })[0]

    # Get the Provisioning template_ID and update with OS, Org, Location
    provisioning_template = entities.ConfigTemplate().search(
        query={
            u'search': u'name="{0}"'.format(DEFAULT_TEMPLATE)
        }
    )[0]
    provisioning_template.operatingsystem = [os]
    provisioning_template.organization = [org]
    provisioning_template.location = [loc]
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
    )[0]
    pxe_template.operatingsystem = [os]
    pxe_template.organization = [org]
    pxe_template.location = [loc]
    pxe_template = pxe_template.update(
        ['location', 'operatingsystem', 'organization']
    )

    # Get the arch ID
    arch = entities.Architecture().search(
        query={u'search': u'name="x86_64"'}
    )[0]

    # Get the media and update its location
    media = entities.Media(organization=[org]).search()[0].read()
    media.location.append(loc)
    media.organization.append(org)
    media = media.update(['location', 'organization'])
    # Update the OS to associate arch, ptable, templates
    os.architecture = [arch]
    os.ptable = [ptable]
    os.config_template = [provisioning_template]
    os.config_template = [pxe_template]
    os.medium = [media]
    os = os.update([
        'architecture',
        'config_template',
        'ptable',
        'medium',
    ])

    # Create Hostgroup
    host_group = entities.HostGroup(
        architecture=arch,
        domain=domain.id,
        subnet=subnet.id,
        lifecycle_environment=lc_env.id,
        content_view=content_view.id,
        location=[loc.id],
        name=gen_string('alpha'),
        environment=environment.id,
        puppet_proxy=proxy,
        puppet_ca_proxy=proxy,
        content_source=proxy,
        medium=media,
        root_pass=gen_string('alphanumeric'),
        operatingsystem=os.id,
        organization=[org.id],
        ptable=ptable.id,
    ).create()

    return {
        'host_group': host_group.name,
        'domain': domain.name,
    }
