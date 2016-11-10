# -*- encoding: utf-8 -*-
"""
Factory object creation for all CLI methods
"""

import datetime
import json
import logging
import os
import random

from fauxfactory import (
    gen_alphanumeric,
    gen_integer,
    gen_ipaddr,
    gen_mac,
    gen_netmask,
    gen_string,
)
from os import chmod
from robottelo import manifests, ssh
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.architecture import Architecture
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.contenthost import ContentHost
from robottelo.cli.contentview import (
    ContentView,
    ContentViewFilter,
    ContentViewFilterRule,
)
from robottelo.cli.discoveryrule import DiscoveryRule
from robottelo.cli.docker import DockerContainer, DockerRegistry
from robottelo.cli.domain import Domain
from robottelo.cli.environment import Environment
from robottelo.cli.filter import Filter
from robottelo.cli.gpgkey import GPGKey
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.job_template import JobTemplate
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.location import Location
from robottelo.cli.medium import Medium
from robottelo.cli.model import Model
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.org import Org
from robottelo.cli.partitiontable import PartitionTable
from robottelo.cli.product import Product
from robottelo.cli.proxy import CapsuleTunnelError, Proxy
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.role import Role
from robottelo.cli.subnet import Subnet
from robottelo.cli.subscription import Subscription
from robottelo.cli.syncplan import SyncPlan
from robottelo.cli.template import Template
from robottelo.cli.user import User
from robottelo.cli.usergroup import UserGroup, UserGroupExternal
from robottelo.cli.smart_variable import SmartVariable
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_LOC,
    DEFAULT_ORG,
    DEFAULT_SUBSCRIPTION_NAME,
    FAKE_1_YUM_REPO,
    FOREMAN_PROVIDERS,
    OPERATING_SYSTEMS,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
    SYNC_INTERVAL,
    TEMPLATE_TYPES,
)
from robottelo.decorators import bz_bug_is_open, cacheable
from robottelo.helpers import (
    update_dictionary, default_url_on_new_port, get_available_capsule_port
)
from robottelo.ssh import upload_file
from tempfile import mkstemp
from time import sleep

logger = logging.getLogger(__name__)

ORG_KEYS = ['organization', 'organization-id', 'organization-label']
CONTENT_VIEW_KEYS = ['content-view', 'content-view-id']
LIFECYCLE_KEYS = ['lifecycle-environment', 'lifecycle-environment-id']


class CLIFactoryError(Exception):
    """Indicates an error occurred while creating an entity using hammer"""


def create_object(cli_object, options, values):
    """
    Creates <object> with dictionary of arguments.

    :param cli_object: A valid CLI object.
    :param dict options: The default options accepted by the cli_object
        create
    :param dict values: Custom values to override default ones.
    :raise robottelo.cli.factory.CLIFactoryError: Raise an exception if object
        cannot be created.
    :rtype: dict
    :return: A dictionary representing the newly created resource.

    """
    if values:
        diff = set(values.keys()).difference(set(options.keys()))
        if diff:
            logger.debug(
                "Option(s) {0} not supported by CLI factory. Please check for "
                "a typo or update default options".format(diff)
            )
    update_dictionary(options, values)
    try:
        result = cli_object.create(options)
    except CLIReturnCodeError as err:
        # If the object is not created, raise exception, stop the show.
        raise CLIFactoryError(
            u'Failed to create {0} with data:\n{1}\n{2}'.format(
                cli_object.__name__,
                json.dumps(options, indent=2, sort_keys=True),
                err.msg,
            )
        )

    # Sometimes we get a list with a dictionary and not
    # a dictionary.
    if type(result) is list and len(result) > 0:
        result = result[0]

    return result


@cacheable
def make_activation_key(options=None):
    """
    Usage::

        hammer activation-key create [OPTIONS]

    Options::

        --content-view CONTENT_VIEW_NAME Content view name to search by
        --content-view-id CONTENT_VIEW_ID content view numeric identifier
        --description DESCRIPTION     description
        --lifecycle-environment LIFECYCLE_ENVIRONMENT_NAME Name to search by
        --lifecycle-environment-id LIFECYCLE_ENVIRONMENT_ID
        --max-hosts MAX_CONTENT_HOSTS maximum number of registered
                                              content hosts
        --name NAME                   name
        --organization ORGANIZATION_NAME Organization name to search by
        --organization-id ORGANIZATION_ID
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --unlimited-hosts UNLIMITED_CONTENT_HOSTS can the activation
                                                          key have unlimited
                                                          content hosts
    """
    # Organization Name, Label or ID is a required field.
    if (
            not options or
            not options.get('organization') and
            not options.get('organization-label') and
            not options.get('organization-id')):
        raise CLIFactoryError('Please provide a valid Organization.')

    args = {
        u'content-view': None,
        u'content-view-id': None,
        u'description': None,
        u'lifecycle-environment': None,
        u'lifecycle-environment-id': None,
        u'max-hosts': None,
        u'name': gen_alphanumeric(),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'unlimited-hosts': None,
    }

    return create_object(ActivationKey, args, options)


@cacheable
def make_architecture(options=None):
    """
    Usage::

        hammer architecture create [OPTIONS]

    Options::

        --name NAME
        --operatingsystem-ids OPERATINGSYSTEM_IDS Operatingsystem ID’s
                                      Comma separated list of values.
    """
    args = {
        u'name': gen_alphanumeric(),
        u'operatingsystem-ids': None,
    }

    return create_object(Architecture, args, options)


def make_container(options=None):
    """Creates a docker container

    Usage::

        hammer docker container create [OPTIONS]

    Options::

        --attach-stderr ATTACH_STDERR             One of true/false, yes/no,
                                                  1/0.
        --attach-stdin ATTACH_STDIN               One of true/false, yes/no,
                                                  1/0.
        --attach-stdout ATTACH_STDOUT             One of true/false, yes/no,
                                                  1/0.
        --capsule CAPSULE_NAME                    Name to search by
        --capsule-id CAPSULE_ID                   Id of the capsule
        --command COMMAND
        --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
        --compute-resource-id COMPUTE_RESOURCE_ID
        --cpu-sets CPU_SETS
        --cpu-shares CPU_SHARES
        --entrypoint ENTRYPOINT
        --location-ids LOCATION_IDS               REPLACE locations with given
        ids. Comma separated list of values.
        --locations LOCATION_NAMES                Comma separated list of
                                                  values.
        --memory MEMORY
        --name NAME
        --organization-ids ORGANIZATION_IDS       REPLACE organizations with
                                                  given ids.  Comma separated
                                                  list of values.
        --organizations ORGANIZATION_NAMES        Comma separated list of
                                                  values.
        --registry-id REGISTRY_ID                 Registry this container will
                                                  have to use to get the image
        --repository-name REPOSITORY_NAME         Name of the repository to use
                                                  to create the container. e.g:
                                                  centos
        --tag TAG                                 Tag to use to create the
                                                  container. e.g: latest
        --tty TTY                                 One of true/false, yes/no,
                                                  1/0.

    """
    # Compute resource ID is a required field.
    if (not options or (
            u'compute-resource' not in options and
            u'compute-resource-id' not in options
    )):
        raise CLIFactoryError(
            'Please provide at least compute-resource or compute-resource-id '
            'options.'
        )

    args = {
        u'attach-stderr': None,
        u'attach-stdin': None,
        u'attach-stdout': None,
        u'capsule': None,
        u'capsule-id': None,
        u'command': 'top',
        u'compute-resource': None,
        u'compute-resource-id': None,
        u'cpu-sets': None,
        u'cpu-shares': None,
        u'entrypoint': None,
        u'location-ids': None,
        u'locations': None,
        u'memory': None,
        u'name': gen_string('alphanumeric'),
        u'organization-ids': None,
        u'organizations': None,
        u'registry-id': None,
        u'repository-name': 'busybox',
        u'tag': 'latest',
        u'tty': None,
    }

    return create_object(DockerContainer, args, options)


@cacheable
def make_content_view(options=None):
    """
    Usage::

        hammer content-view create [OPTIONS]

    Options::

        --component-ids COMPONENT_IDS List of component content view
        version ids for composite views
                                      Comma separated list of values.
        --composite                   Create a composite content view
        --description DESCRIPTION     Description for the content view
        --label LABEL                 Content view label
        --name NAME                   Name of the content view
        --organization ORGANIZATION_NAME  Organization name to search by
        --organization-id ORGANIZATION_ID Organization identifier
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --repository-ids REPOSITORY_IDS List of repository ids
                                      Comma separated list of values.
        -h, --help                    print help

    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')

    args = {
        u'component-ids': None,
        u'composite': False,
        u'description': None,
        u'label': None,
        u'name': gen_string('alpha', 10),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'repository-ids': None
    }

    return create_object(ContentView, args, options)


@cacheable
def make_content_view_filter(options=None):
    """
    Usage::

        content-view filter create [OPTIONS]

    Options::

        --content-view CONTENT_VIEW_NAME        Content view name to search by
        --content-view-id CONTENT_VIEW_ID       content view numeric identifier
        --description DESCRIPTION               description of the filter
        --inclusion INCLUSION                   specifies if content should be
                                                included or excluded, default:
                                                 inclusion=false
                                                One of true/false, yes/no, 1/0.
        --name NAME                             name of the filter
        --organization ORGANIZATION_NAME        Organization name to search by
        --organization-id ORGANIZATION_ID       Organization ID to search by
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --original-packages ORIGINAL_PACKAGES   add all packages without errata
                                                to the included/ excluded list.
                                                (package filter only)
                                                One of true/false, yes/no, 1/0.
        --repositories REPOSITORY_NAMES         Comma separated list of values.
        --repository-ids REPOSITORY_IDS         list of repository ids
                                                Comma separated list of values.
        --type TYPE                             type of filter (e.g. rpm,
                                                package_group, erratum)
        -h, --help                              print help

    """

    args = {
        u'content-view': None,
        u'content-view-id': None,
        u'description': None,
        u'inclusion': None,
        u'name': gen_string('alpha', 10),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'original-packages': None,
        u'repositories': None,
        u'repository-ids': None,
        u'type': None,
    }

    return create_object(ContentViewFilter, args, options)


@cacheable
def make_content_view_filter_rule(options=None):
    """
    Usage::

        content-view filter rule create [OPTIONS]

    Options::

        --content-view CONTENT_VIEW_NAME        Content view name to search by
        --content-view-filter CONTENT_VIEW_FILTER_NAME  Name to search by
        --content-view-filter-id CONTENT_VIEW_FILTER_ID filter identifier
        --content-view-id CONTENT_VIEW_ID       content view numeric identifier
        --date-type DATE_TYPE                   erratum: search using the
                                                'Issued On' or 'Updated On'
                                                column of the errata.
                                                Values are 'issued'/'updated'
        --end-date END_DATE                     erratum: end date (YYYY-MM-DD)
        --errata-id ERRATA_ID                   erratum: id
        --errata-ids ERRATA_IDS                 erratum: IDs or a select all
                                                object
                                                Comma separated list of values.
        --max-version MAX_VERSION               package: maximum version
        --min-version MIN_VERSION               package: minimum version
        --name NAME                             package and package group names
                                                Comma separated list of values.
        --names NAMES                           Package and package group names
        --start-date START_DATE                 erratum: start date
                                                (YYYY-MM-DD)
        --types TYPES                           erratum: types (enhancement,
                                                bugfix, security)
                                                Comma separated list of values.
        --version VERSION                       package: version
        -h, --help                              print help

    """

    args = {
        u'content-view': None,
        u'content-view-filter': None,
        u'content-view-filter-id': None,
        u'content-view-id': None,
        u'date-type': None,
        u'end-date': None,
        u'errata-id': None,
        u'errata-ids': None,
        u'max-version': None,
        u'min-version': None,
        u'name': None,
        u'names': None,
        u'start-date': None,
        u'types': None,
        u'version': None,
    }

    return create_object(ContentViewFilterRule, args, options)


@cacheable
def make_discoveryrule(options=None):
    """
    Usage::

        hammer discovery_rule create [OPTIONS]

    Options::

        --enabled ENABLED                   flag is used for temporary shutdown
                                            of rules
                                            One of true/false, yes/no, 1/0.
        --hostgroup HOSTGROUP_NAME          Hostgroup name
        --hostgroup-id HOSTGROUP_ID
        --hostgroup-title HOSTGROUP_TITLE   Hostgroup title
        --hostname HOSTNAME                 defines a pattern to assign
                                            human-readable hostnames to the
                                            matching hosts
        --hosts-limit HOSTS_LIMIT
        --location-ids LOCATION_IDS         REPLACE locations with given ids
                                            Comma separated list of values.
        --locations LOCATION_NAMES          Comma separated list of values.
        --max-count MAX_COUNT               enables to limit maximum amount of
                                            provisioned hosts per rule
        --name NAME                         represents rule name shown to the
                                            users
        --organization-ids ORGANIZATION_IDS REPLACE organizations with given
                                            ids.
                                            Comma separated list of values.
        --organizations ORGANIZATION_NAMES  Comma separated list of values.
        --priority PRIORITY                 puts the rules in order, low
                                            numbers go first. Must be greater
                                            then zero
        --search SEARCH                     query to match discovered hosts for
                                            the particular rule
        -h, --help                          print help
    """

    # Organizations, Locations, search query, hostgroup are required fields.
    if not options:
        raise CLIFactoryError('Please provide required parameters')
    # Organizations fields is required
    if not any(options.get(key) for key in [
        'organizations', 'organization-ids'
    ]):
        raise CLIFactoryError('Please provide a valid organization field.')
    # Locations field is required
    if not any(options.get(key) for key in ['locations', 'location-ids']):
        raise CLIFactoryError('Please provide a valid location field.')
    # search query is required
    if not options.get('search'):
        raise CLIFactoryError('Please provider a valid search query')
    # hostgroup is required
    if not any(options.get(key) for key in ['hostgroup', 'hostgroup-id']):
        raise CLIFactoryError('Please provider a valid hostgroup')

    args = {
        u'enabled': None,
        u'hostgroup': None,
        u'hostgroup-id': None,
        u'hostgroup-title': None,
        u'hostname': None,
        u'hosts-limit': None,
        u'location-ids': None,
        u'locations': None,
        u'max-count': None,
        u'name': gen_alphanumeric(),
        u'organizations': None,
        u'organization-ids': None,
        u'priority': None,
        u'search': None,
    }

    return create_object(DiscoveryRule, args, options)


@cacheable
def make_gpg_key(options=None):
    """
    Usage::

        hammer gpg create [OPTIONS]

    Options::

        --key GPG_KEY_FILE            GPG Key file
        --name NAME                   identifier of the GPG Key
        --organization ORGANIZATION_NAME  Organization name to search by
        --organization-id ORGANIZATION_ID organization identifier
        --organization-label ORGANIZATION_LABEL Organization label to search by
        -h, --help                    print help
    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')

    # Create a fake gpg key file if none was provided
    if not options.get('key'):
        (_, key_filename) = mkstemp(text=True)
        os.chmod(key_filename, 0o700)
        with open(key_filename, 'w') as gpg_key_file:
            gpg_key_file.write(gen_alphanumeric(gen_integer(20, 50)))
    else:
        # If the key is provided get its local path and remove it from options
        # to not override the remote path
        key_filename = options.pop('key')

    args = {
        u'key': '/tmp/{0}'.format(gen_alphanumeric()),
        u'name': gen_alphanumeric(),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
    }

    # Upload file to server
    ssh.upload_file(local_file=key_filename, remote_file=args['key'])

    return create_object(GPGKey, args, options)


@cacheable
def make_location(options=None):
    """Location CLI factory

    Usage::

        hammer location create [OPTIONS]

    Options::

        --compute-resource-ids COMPUTE_RESOURCE_IDS Compute resource IDs
                                                    Comma separated list of
                                                    values.
        --compute-resources COMPUTE_RESOURCE_NAMES  Compute resource names
                                                    Comma separated list of
                                                    values.
        --config-template-ids CONFIG_TEMPLATE_IDS   Provisioning template IDs
                                                    Comma separated list of
                                                    values.
        --config-templates CONFIG_TEMPLATE_NAMES    Provisioning template names
                                                    Comma separated list of
                                                    values.
        --description DESCRIPTION                   Location description
        --domain-ids DOMAIN_IDS                     Domain IDs
                                                    Comma separated list of
                                                    values.
        --domains DOMAIN_NAMES                      Domain names
                                                    Comma separated list of
                                                    values.
        --environment-ids ENVIRONMENT_IDS           Environment IDs
                                                    Comma separated list of
                                                    values.
        --environments ENVIRONMENT_NAMES            Environment names
                                                    Comma separated list of
                                                    values.
        --hostgroup-ids HOSTGROUP_IDS               Host group IDs
                                                    Comma separated list of
                                                    values.
        --hostgroups HOSTGROUP_NAMES                Host group names
                                                    Comma separated list of
                                                    values.
        --medium-ids MEDIUM_IDS                     Media IDs
                                                    Comma separated list of
                                                    values.
        --name NAME
        --realm-ids REALM_IDS                       Realm IDs
                                                    Comma separated list of
                                                    values.
        --realms REALM_NAMES                        Realm names
                                                    Comma separated list of
                                                    values.
        --smart-proxy-ids SMART_PROXY_IDS           Smart proxy IDs
                                                    Comma separated list of
                                                    values.
        --smart-proxies SMART_PROXY_NAMES           Smart proxy names
                                                    Comma separated list of
                                                    values.
        --subnet-ids SUBNET_IDS                     Subnet IDs
                                                    Comma separated list of
                                                    values.
        --subnets SUBNET_NAMES                      Subnet names
                                                    Comma separated list of
        --user-ids USER_IDS                         User IDs
                                                    Comma separated list of
                                                    values.
        --users USER_LOGINS                         User names
                                                    Comma separated list of
                                                    values.
    """
    args = {
        u'compute-resource-ids': None,
        u'compute-resources': None,
        u'config-template-ids': None,
        u'config-templates': None,
        u'description': None,
        u'domain-ids': None,
        u'domains': None,
        u'environment-ids': None,
        u'environments': None,
        u'hostgroup-ids': None,
        u'hostgroups': None,
        u'medium-ids': None,
        u'name': gen_alphanumeric(),
        u'realm-ids': None,
        u'realms': None,
        u'smart-proxy-ids': None,
        u'smart-proxies': None,
        u'subnet-ids': None,
        u'subnets': None,
        u'user-ids': None,
        u'users': None,
    }

    return create_object(Location, args, options)


@cacheable
def make_model(options=None):
    """
    Usage::

        hammer model create [OPTIONS]

    Options::

        --hardware-model HARDWARE_MODEL
        --info INFO
        --name NAME
        --vendor-class VENDOR_CLASS
    """
    args = {
        u'hardware-model': None,
        u'info': None,
        u'name': gen_alphanumeric(),
        u'vendor-class': None,
    }

    return create_object(Model, args, options)


@cacheable
def make_partition_table(options=None):
    """
    Usage::

        hammer partition-table create [OPTIONS]

    Options::

        --file LAYOUT                         Path to a file that contains the
                                              partition layout
        --location-ids LOCATION_IDS           REPLACE locations with given ids
                                              Comma separated list of values.
        --locations LOCATION_NAMES            Comma separated list of values.
        --name NAME
        --organization-ids ORGANIZATION_IDS   REPLACE organizations with given
                                              ids.
                                              Comma separated list of values.
        --organizations ORGANIZATION_NAMES    Comma separated list of values.
        --os-family OS_FAMILY
    """
    if options is None:
        options = {}
    (_, layout) = mkstemp(text=True)
    os.chmod(layout, 0o700)
    with open(layout, 'w') as ptable:
        ptable.write(options.get('content', 'default ptable content'))

    args = {
        u'file': '/tmp/{0}'.format(gen_alphanumeric()),
        u'location-ids': None,
        u'locations': None,
        u'name': gen_alphanumeric(),
        u'organization-ids': None,
        u'organizations': None,
        u'os-family': random.choice(OPERATING_SYSTEMS),
    }

    # Upload file to server
    ssh.upload_file(local_file=layout, remote_file=args['file'])

    return create_object(PartitionTable, args, options)


@cacheable
def make_product(options=None):
    """
    Usage::

        hammer product create [OPTIONS]

    Options::

        --description DESCRIPTION     Product description
        --gpg-key GPG_KEY_NAME        Name to search by
        --gpg-key-id GPG_KEY_ID       Identifier of the GPG key
        --label LABEL
        --name NAME
        --organization ORGANIZATION_NAME        Organization name to search by
        --organization-id ORGANIZATION_ID       ID of the organization
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --sync-plan SYNC_PLAN_NAME              Sync plan name to search by
        --sync-plan-id SYNC_PLAN_ID             Plan numeric identifier
        -h, --help                              print help
    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')

    args = {
        u'description': gen_string('alpha', 20),
        u'gpg-key': None,
        u'gpg-key-id': None,
        u'label': gen_string('alpha', 20),
        u'name': gen_string('alpha', 20),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'sync-plan': None,
        u'sync-plan-id': None,
    }

    return create_object(Product, args, options)


def make_product_wait(options=None, wait_for=5):
    """Wrapper function for make_product to make it wait before erroring out.

    This is a temporary workaround for BZ#1332650: Sometimes cli product
    create errors for no reason when there are multiple product creation
    requests at the sametime although the product entities are created.  This
    workaround will attempt to wait for 5 seconds and query the
    product again to make sure it is actually created.  If it is not found,
    it will fail and stop.

    Note: This wrapper method is created instead of patching make_product
    because this issue does not happen for all entities and this workaround
    should be removed once the root cause is identified/fixed.
    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')
    options['name'] = options.get('name', gen_string('alpha'))
    try:
        product = make_product(options)
    except CLIFactoryError as err:
        if not bz_bug_is_open(1332650):
            raise err
        sleep(wait_for)
        try:
            product = Product.info({
                'name': options.get('name'),
                'organization-id': options.get('organization-id'),
            })
        except CLIReturnCodeError:
            raise err
        if not product:
            raise err
    return product


@cacheable
def make_proxy(options=None):
    """
    Usage::

        hammer proxy create [OPTIONS]

    Options::

        --location-ids LOCATION_IDS     REPLACE locations with given ids
                                        Comma separated list of values.
        --name NAME
        --organization-ids              ORGANIZATION_IDS REPLACE organizations
                                        with given ids.
                                        Comma separated list of values.
        -h, --help                      print help

    """
    args = {
        u'name': gen_alphanumeric(),
    }

    if options is None or 'url' not in options:
        newport = get_available_capsule_port()
        try:
            with default_url_on_new_port(9090, newport) as url:
                args['url'] = url
                return create_object(Proxy, args, options)
        except CapsuleTunnelError as err:
            raise CLIFactoryError(
                'Failed to create ssh tunnel: {0}'.format(err))
    args['url'] = options['url']
    return create_object(Proxy, args, options)


def make_registry(options=None):
    """Creates a docker registry

        Usage::

            hammer docker registry create [OPTIONS]

        Options::

            --description DESCRIPTION
            --name NAME
            --password PASSWORD
            --url URL
            --username USERNAME

    """
    args = {
        u'description': None,
        u'name': gen_string('alphanumeric'),
        u'password': None,
        u'url': settings.docker.external_registry_1,
        u'username': None,
    }

    return create_object(DockerRegistry, args, options)


@cacheable
def make_repository(options=None):
    """
    Usage::

        hammer repository create [OPTIONS]

    Options::

        --checksum-type CHECKSUM_TYPE           checksum of the repository,
                                                currently 'sha1' &amp; 'sha256'
                                                are supported.'
        --content-type CONTENT_TYPE             type of repo (either 'yum',
                                                'puppet', 'docker' or 'ostree',
                                                defaults to 'yum')
        --docker-upstream-name DOCKER_UPSTREAM_NAME name of the upstream docker
                                                repository
        --download-policy DOWNLOAD_POLICY       download policy for yum repos
                                                (either 'immediate','on_demand'
                                                or 'background')
        --gpg-key GPG_KEY_NAME                  Name to search by
        --gpg-key-id GPG_KEY_ID                 gpg key numeric identifier
        --label LABEL
        --name NAME
        --organization ORGANIZATION_NAME        Organization name to search by
        --organization-id ORGANIZATION_ID       organization ID
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --product PRODUCT_NAME                  Product name to search by
        --product-id PRODUCT_ID                 product numeric identifier
        --publish-via-http ENABLE               Publish Via HTTP
                                                One of true/false, yes/no, 1/0.
        --url URL                               repository source url
        -h, --help                              print help

    """
    # Product ID is a required field.
    if not options or not options.get('product-id'):
        raise CLIFactoryError('Please provide a valid Product ID.')

    args = {
        u'checksum-type': None,
        u'content-type': u'yum',
        u'docker-upstream-name': None,
        u'download-policy': None,
        u'gpg-key': None,
        u'gpg-key-id': None,
        u'label': None,
        u'name': gen_string('alpha', 15),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'product': None,
        u'product-id': None,
        u'publish-via-http': u'true',
        u'url': FAKE_1_YUM_REPO,
    }

    return create_object(Repository, args, options)


@cacheable
def make_role(options=None):
    """Usage::

        hammer role create [OPTIONS]

    Options::

        --name NAME
    """
    # Assigning default values for attributes
    args = {u'name': gen_alphanumeric(6)}

    return create_object(Role, args, options)


@cacheable
def make_filter(options=None):
    """
    Usage::

        hammer filter create [OPTIONS]

    Options::

        --location-ids LOCATION_IDS         Comma separated list of values.
        --locations LOCATION_NAMES          Comma separated list of values.
        --organization-ids ORGANIZATION_IDS Comma separated list of values.
        --organizations ORGANIZATION_NAMES  Comma separated list of values.
        --permission-ids PERMISSION_IDS     Comma separated list of values.
        --permissions PERMISSION_NAMES      Comma separated list of values.
        --role ROLE_NAME                    User role name
        --role-id ROLE_ID
        --search SEARCH
        -h, --help                          print help
    """
    args = {
        u'location-ids': None,
        u'locations': None,
        u'organization-ids': None,
        u'organizations': None,
        u'permission-ids': None,
        u'permissions': None,
        u'role': None,
        u'role-id': None,
        u'search': None,
    }

    # Role and permissions are required fields.
    if not options:
        raise CLIFactoryError('Please provide required parameters')

    # Do we have at least one role field?
    if not any(options.get(key) for key in ['role', 'role-id']):
        raise CLIFactoryError('Please provide a valid role field.')

    # Do we have at least one permissions field?
    if not any(options.get(key) for key in ['permissions', 'permission-ids']):
        raise CLIFactoryError('Please provide a valid permissions field.')

    return create_object(Filter, args, options)


@cacheable
def make_subnet(options=None):
    """
    Usage::

        hammer subnet create [OPTIONS]

    Options::

        --boot-mode BOOT_MODE         Default boot mode for interfaces assigned
                                      to this subnet, valid values are
                                      "Static", "DHCP"
        --dhcp-id DHCP_ID             DHCP Proxy to use within this subnet
        --dns-id DNS_ID               DNS Proxy to use within this subnet
        --dns-primary DNS_PRIMARY     Primary DNS for this subnet
        --dns-secondary DNS_SECONDARY Secondary DNS for this subnet
        --domain-ids DOMAIN_IDS       Numerical ID or domain name
        --domains DOMAIN_NAMES        Comma separated list of values.
        --from FROM                   Starting IP Address for IP auto
                                      suggestion
        --gateway GATEWAY             Primary DNS for this subnet
        --ipam IPAM                   IP Address auto suggestion mode for this
                                      subnet, valid values are
                                      'DHCP', 'Internal DB', 'None'
        --location-ids LOCATION_IDS
        --locations LOCATION_NAMES    Comma separated list of values.
        --mask MASK                   Netmask for this subnet
        --name NAME                   Subnet name
        --network NETWORK             Subnet network
        --organization-ids ORGANIZATION_IDS organization ID
        --organizations ORGANIZATION_NAMES Comma separated list of values.
        --tftp-id TFTP_ID             TFTP Proxy to use within this subnet
        --to TO                       Ending IP Address for IP auto suggestion
        --vlanid VLANID               VLAN ID for this subnet
        -h, --help                    print help

    """
    args = {
        u'boot-mode': None,
        u'dhcp-id': None,
        u'dns-id': None,
        u'dns-primary': None,
        u'dns-secondary': None,
        u'domain-ids': None,
        u'domains': None,
        u'from': None,
        u'gateway': None,
        u'ipam': None,
        u'location-ids': None,
        u'locations': None,
        u'mask': gen_netmask(),
        u'name': gen_alphanumeric(8),
        u'network': gen_ipaddr(ip3=True),
        u'organization-ids': None,
        u'organizations': None,
        u'tftp-id': None,
        u'to': None,
        u'vlanid': None,
    }

    return create_object(Subnet, args, options)


@cacheable
def make_sync_plan(options=None):
    """
    Usage::

        hammer sync-plan create [OPTIONS]

    Options::

        --description DESCRIPTION               sync plan description
        --enabled ENABLED                       enables or disables
                                                synchronization. One of
                                                true/false, yes/no, 1/0.
        --interval INTERVAL                     how often synchronization
                                                should run. One of 'none',
                                                'hourly', 'daily', 'weekly'.
                                                Default: ""none""
        --name NAME                             sync plan name
        --organization ORGANIZATION_NAME        Organization name to search by
        --organization-id ORGANIZATION_ID       organization ID
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --sync-date SYNC_DATE                   start date and time of the
                                                synchronization defaults to now
                                                Date and time in YYYY-MM-DD
                                                HH:MM:SS or ISO 8601 format
                                                Default: "2014-10-07 08:50:35"
        -h, --help                              print help

    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')

    args = {
        u'description': gen_string('alpha', 20),
        u'enabled': 'true',
        u'interval': random.choice(SYNC_INTERVAL.values()),
        u'name': gen_string('alpha', 20),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'sync-date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    return create_object(SyncPlan, args, options)


@cacheable
def make_content_host(options=None):
    """Register a content host by running ``hammer host subscription
    register``.

    Return the information about the created content host by running ``hammer
    content-host info``.
    """
    # Organization ID is a required field.
    if not options:
        raise CLIFactoryError('Please provide required parameters')

    # Do we have at least one organization field?
    if not any(options.get(key) for key in ORG_KEYS):
        raise CLIFactoryError('Please provide a valid organization field.')

    # Do we have at least one content view field?
    if not any(options.get(key) for key in CONTENT_VIEW_KEYS):
        raise CLIFactoryError(
            'Please provide one of {0}.'.format(', '.join(CONTENT_VIEW_KEYS)))

    # Do we have at least one lifecycle-environment field?
    if not any(options.get(key) for key in LIFECYCLE_KEYS):
        raise CLIFactoryError(
            'Please provide one of {0}.'.format(', '.join(LIFECYCLE_KEYS)))

    args = {
        u'content-view': None,
        u'content-view-id': None,
        u'hypervisor-guest-uuids': None,
        u'lifecycle-environment': None,
        u'lifecycle-environment-id': None,
        u'name': gen_string('alpha', 20),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'release-version': None,
        u'service-level': None,
        u'uuid': None,
    }
    return create_object(ContentHost, args, options)


@cacheable
def make_host(options=None):
    """
    Usage::

        hammer host create [OPTIONS]

    Options::

        --architecture ARCHITECTURE_NAME Architecture name
        --architecture ARCHITECTURE_NAME            Architecture name
        --architecture-id ARCHITECTURE_ID
        --ask-root-password ASK_ROOT_PW             One of true/false, yes/no,
                                                    1/0.
        --autoheal AUTOHEAL                         Sets whether the Host will
                                                    autoheal subscriptions upon
                                                    checkin
                                                    One of true/false, yes/no,
                                                    1/0.
        --build BUILD                               One of true/false, yes/no,
                                                    1/0.
                                                    Default: "true"
        --comment COMMENT                           Additional information
                                                    about this host
        --compute-attributes COMPUTE_ATTRS          Compute resource attributes
                                                    Comma-separated list of
                                                    key=value.
        --compute-profile COMPUTE_PROFILE_NAME      Name to search by
        --compute-profile-id COMPUTE_PROFILE_ID
        --compute-resource COMPUTE_RESOURCE_NAME    Compute resource name
        --compute-resource-id COMPUTE_RESOURCE_ID
        --content-view CONTENT_VIEW_NAME            Name to search by
        --content-view-id CONTENT_VIEW_ID           content view numeric
                                                    identifier
        --domain DOMAIN_NAME                        Domain name
        --domain-id DOMAIN_ID                       Numerical ID or domain name
        --enabled ENABLED                           One of true/false, yes/no,
                                                    1/0.
                                                    Default: "true"
        --environment ENVIRONMENT_NAME              Environment name
        --environment-id ENVIRONMENT_ID
        --hostgroup HOSTGROUP_NAME                  Hostgroup name
        --hostgroup-id HOSTGROUP_ID
        --hostgroup-title HOSTGROUP_TITLE           Hostgroup title
        --hypervisor-guest-uuids HYPERVISOR_GUEST_UUIDS     List of hypervisor
                                                            guest uuids
                                                            Comma separated
                                                            list of values.
        --image IMAGE_NAME                          Name to search by
        --image-id IMAGE_ID
        --interface INTERFACE                       Interface parameters.
                                                    Comma-separated list of
                                                    key=value.
                                                    Can be specified multiple
                                                    times.
        --ip IP                                     not required if using a
                                                    subnet with DHCP Capsule
        --kickstart-repository-id KICKSTART_REPOSITORY_ID   Repository Id
                                                            associated with the
                                                            kickstart repo used
                                                            for provisioning
        --lifecycle-environment LIFECYCLE_ENVIRONMENT_NAME  Name to search by
        --lifecycle-environment-id LIFECYCLE_ENVIRONMENT_ID ID of the
                                                            environment
        --location LOCATION_NAME                    Location name
        --location-id LOCATION_ID
        --mac MAC                                   required for managed host
                                                    that is bare metal, not
                                                    required if it's a virtual
                                                    machine
        --managed MANAGED                           One of true/false, yes/no,
                                                    1/0.
                                                    Default: "true"
        --medium MEDIUM_NAME                        Medium name
        --medium-id MEDIUM_ID
        --model MODEL_NAME                          Model name
        --model-id MODEL_ID
        --name NAME
        --operatingsystem OPERATINGSYSTEM_TITLE     Operating system title
        --operatingsystem-id OPERATINGSYSTEM_ID
        --organization ORGANIZATION_NAME            Organization name
        --organization-id ORGANIZATION_ID           organization ID
        --overwrite OVERWRITE                       One of true/false, yes/no,
                                                    1/0.
                                                    Default: "true"
        --owner OWNER_LOGIN                         Login of the owner
        --owner-id OWNER_ID                         ID of the owner
        --owner-type OWNER_TYPE                     Host's owner type
                                                    Possible value(s): 'User',
                                                    'Usergroup'
        --parameters PARAMS                         Host parameters.
                                                    Comma-separated list of
                                                    key=value.
        --partition-table PARTITION_TABLE_NAME      Partition table name
        --partition-table-id PARTITION_TABLE_ID
        --progress-report-id PROGRESS_REPORT_ID     UUID to track orchestration
                                                    tasks status, GET
                                                    /api/orchestration/:UUID
                                                    /tasks
        --provision-method METHOD                   Possible value(s): 'build',
                                                    'image'
        --puppet-ca-proxy PUPPET_CA_PROXY_NAME
        --puppet-ca-proxy-id PUPPET_CA_PROXY_ID
        --puppet-class-ids PUPPET_CLASS_IDS         Comma separated list of
                                                    values.
        --puppet-classes PUPPET_CLASS_NAMES         Comma separated list of
                                                    values.
        --puppet-proxy PUPPET_PROXY_NAME
        --puppet-proxy-id PUPPET_PROXY_ID
        --pxe-loader PXE_LOADER                     DHCP filename option
                                                    (Grub2/PXELinux by default)
                                                    Possible value(s): 'None',
                                                    'PXELinux BIOS',
                                                    'PXELinux UEFI',
                                                    'Grub UEFI',
                                                    'Grub UEFI SecureBoot',
                                                    'Grub2 UEFI',
                                                    'Grub2 UEFI SecureBoot'
        --realm REALM_NAME                          Name to search by
        --realm-id REALM_ID                         Numerical ID or realm name
        --release-version RELEASE_VERSION           Release version for this
                                                    Host to use (7Server, 7.1,
                                                    etc)
        --root-pass ROOT_PASS                       required if host is managed
                                                    and value is not inherited
                                                    from host group or default
                                                    password in settings
        --root-password ROOT_PW
        --service-level SERVICE_LEVEL               Service level to be used
                                                    for autoheal.
        --subnet SUBNET_NAME                        Subnet name
        --subnet-id SUBNET_ID
        --volume VOLUME                             Volume parameters
                                                    Comma-separated list of
                                                    key=value.
                                                    Can be specified multiple
                                                    times.
    """
    # Check for required options
    required_options = (
        'architecture-id',
        'domain-id',
        'medium-id',
        'operatingsystem-id',
        'partition-table-id',
    )

    if options is None:
        raise CLIFactoryError(
            'Options {0} are required'.format(', '.join(required_options))
        )

    missing_options = [
        option for option in required_options if options.get(option) is None
    ]

    if missing_options:
        raise CLIFactoryError(
            'Options {0} are required'.format(', '.join(missing_options))
        )

    args = {
        u'architecture': None,
        u'architecture-id': None,
        u'ask-root-password': None,
        u'autoheal': None,
        u'build': None,
        u'comment': None,
        u'compute-attributes': None,
        u'compute-profile': None,
        u'compute-profile-id': None,
        u'compute-resource': None,
        u'compute-resource-id': None,
        u'content-view': None,
        u'content-view-id': None,
        u'domain': None,
        u'domain-id': None,
        u'enabled': None,
        u'environment': None,
        u'environment-id': None,
        u'hostgroup': None,
        u'hostgroup-id': None,
        u'hostgroup-title': None,
        u'hypervisor-guest-uuids': None,
        u'image': None,
        u'image-id': None,
        u'interface': None,
        u'ip': gen_ipaddr(),
        u'kickstart-repository-id': None,
        u'lifecycle-environment': None,
        u'lifecycle-environment-id': None,
        u'location': None,
        u'location-id': None,
        u'mac': gen_mac(),
        u'managed': None,
        u'medium': None,
        u'medium-id': None,
        u'model': None,
        u'model-id': None,
        u'name': gen_string('alpha', 10),
        u'operatingsystem': None,
        u'operatingsystem-id': None,
        u'organization': None,
        u'organization-id': None,
        u'overwrite': None,
        u'owner': None,
        u'owner-id': None,
        u'owner-type': None,
        u'parameters': None,
        u'partition-table': None,
        u'partition-table-id': None,
        u'progress-report-id': None,
        u'provision-method': None,
        u'puppet-ca-proxy': None,
        u'puppet-ca-proxy-id': None,
        u'puppet-class-ids': None,
        u'puppet-classes': None,
        u'puppet-proxy': None,
        u'puppet-proxy-id': None,
        u'pxe-loader': None,
        u'realm': None,
        u'realm-id': None,
        u'root-pass': None,
        u'root-password': gen_string('alpha', 8),
        u'service-level': None,
        u'subnet': None,
        u'subnet-id': None,
        u'volume': None,
    }

    return create_object(Host, args, options)


@cacheable
def make_fake_host(options=None):
    """Wrapper function for make_host to pass all required options for creation
    of a fake host
    """
    if options is None:
        options = {}

    # Try to use default Satellite entities, otherwise create them if they were
    # not passed or defined previously
    if not options.get('organization') and not options.get('organization-id'):
        try:
            options['organization-id'] = Org.info({'name': DEFAULT_ORG})['id']
        except CLIReturnCodeError:
            options['organization-id'] = make_org()['id']
    if not options.get('location') and not options.get('location-id'):
        try:
            options['location-id'] = Location.info({'name': DEFAULT_LOC})['id']
        except CLIReturnCodeError:
            options['location-id'] = make_location()['id']
    if not options.get('domain') and not options.get('domain-id'):
        try:
            options['domain-id'] = Domain.info({
                'name': settings.server.hostname.partition('.')[-1]})['id']
        except CLIReturnCodeError:
            options['domain-id'] = make_domain({
                'location-ids': options.get('location-id'),
                'locations': options.get('location'),
                'organization-ids': options.get('organization-id'),
                'organizations': options.get('organization'),
            })['id']
    if not options.get('architecture') and not options.get('architecture-id'):
        try:
            options['architecture-id'] = Architecture.info({
                'name': DEFAULT_ARCHITECTURE})['id']
        except CLIReturnCodeError:
            options['architecture-id'] = make_architecture()['id']
    if (not options.get('operatingsystem') and
            not options.get('operatingsystem-id')):
        try:
            options['operatingsystem-id'] = OperatingSys.list({
                    'search': 'name="RedHat" AND major="{0}" OR major="{1}"'
                              .format(
                                   RHEL_6_MAJOR_VERSION,
                                   RHEL_7_MAJOR_VERSION
                              )
            })[0]['id']
        except IndexError:
            options['operatingsystem-id'] = make_os({
                'architecture-ids': options.get('architecture-id'),
                'architectures': options.get('architecture'),
                'partition-table-ids': options.get('partition-table-id'),
                'partition-tables': options.get('partition-table'),
            })['id']
    if (not options.get('partition-table') and
            not options.get('partition-table-id')):
        try:
            options['partition-table-id'] = PartitionTable.list({
                'operatingsystem': options.get('operatingsystem'),
                'operatingsystem-id': options.get('operatingsystem-id'),
            })[0]['id']
        except IndexError:
            options['partition-table-id'] = make_partition_table({
                'location-ids': options.get('location-id'),
                'locations': options.get('location'),
                'operatingsystem-ids': options.get('operatingsystem-id'),
                'organization-ids': options.get('organization-id'),
                'organizations': options.get('organization'),
            })['id']

    # Finally, create a new medium (if none was passed)
    if not options.get('medium') and not options.get('medium-id'):
        options['medium-id'] = make_medium({
            'location-ids': options.get('location-id'),
            'locations': options.get('location'),
            'operatingsystems': options.get('operatingsystem'),
            'operatingsystem-ids': options.get('operatingsystem-id'),
            'organization-ids': options.get('organization-id'),
            'organizations': options.get('organization'),
        })['id']

    return make_host(options)


@cacheable
def make_host_collection(options=None):
    """
    Usage::

         host-collection create [OPTIONS]

    Options::

        --description DESCRIPTION
        --host-collection-ids HOST_COLLECTION_IDS  Array of content host ids to
                                                   replace the content hosts in
                                                   host collection
                                                   Comma separated list of
                                                   values
        --hosts HOST_NAMES                         Comma separated list of
                                                   values
        --max-hosts MAX_CONTENT_HOSTS              Maximum number of content
                                                   hosts in the host collection
        --name NAME                                Host Collection name
        --organization ORGANIZATION_NAME
        --organization-id ORGANIZATION_ID          Organization identifier
        --organization-label ORGANIZATION_LABEL
        --unlimited-hosts UNLIMITED_CONTENT_HOSTS  Whether or not the host
                                                   collection may have
                                                   unlimited content hosts
                                                   One of true/false, yes/no,
                                                   1/0.
         -h, --help                                print help

    """
    # Organization ID is required
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORGANIZATION_ID.')

    # Assigning default values for attributes
    args = {
        u'description': None,
        u'host-collection-ids': None,
        u'hosts': None,
        u'max-hosts': None,
        u'name': gen_string('alpha', 15),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'unlimited-hosts': None,
    }

    return create_object(HostCollection, args, options)


@cacheable
def make_job_invocation(options=None):
    """
    Usage::

        hammer job-invocation create

    Options::

         --async                                  Do not wait for the task
         --bookmark BOOKMARK_NAME                 Name to search by
         --bookmark-id BOOKMARK_ID
         --concurrency-level CONCURRENCY_LEVEL    Run at most N tasks at a time
         --cron-line CRONLINE                     Create a recurring execution
         --description-format DESCRIPTION_FORMAT  Override the description
                                                  format from the template for
                                                  this invocation only
         --dynamic                                Dynamic search queries are
                                                  evaluated at run time
         --effective-user EFFECTIVE_USER          What user should be used to
                                                  run the script (using
                                                  sudo-like mechanisms).
         --end-time DATETIME                      Perform no more executions
                                                  after this time, used with
                                                  --cron-line (YYYY-MM-DD
                                                  HH:MM:SS or ISO 8601 format)
         --input-files INPUT FILES                Read input values from files
                                                  Comma-separated list of
                                                  key=file, where file is a
                                                  path to a text file
         --inputs INPUTS                          Inputs from command line
                                                  Comma-separated list of
                                                  key=value.
         --job-template JOB_TEMPLATE_NAME         Name to search by
         --job-template-id JOB_TEMPLATE_ID
         --max-iteration MAX_ITERATION            Repeat a maximum of N times
         --search-query SEARCH_QUERY
         --start-at DATETIME                      Schedule the execution for
                                                  a later time in
                                                  YYYY-MM-DD HH:MM:SS
                                                  or ISO 8601
         --start-before DATETIME                  Execution should be cancelled
                                                  if it cannot be started
                                                  before specified datetime
         --time-span TIME_SPAN                    Distribute tasks over
                                                  N seconds
    """

    args = {
        u'async': None,
        u'bookmark': None,
        u'bookmark-id': None,
        u'concurrency-level': None,
        u'cron-line': None,
        u'description-format': None,
        u'dynamic': None,
        u'effective-user': None,
        u'end-time': None,
        u'input-files': None,
        u'inputs': None,
        u'job-template': None,
        u'job-template-id': None,
        u'max-iteration': None,
        u'search-query': None,
        u'start-at': None,
        u'start-before': None,
        u'time-span': None,
    }

    return create_object(JobInvocation, args, options)


@cacheable
def make_job_template(options=None):
    """
    Usage::

        hammer job-template create

    Options::

       --audit-comment AUDIT_COMMENT
       --current-user CURRENT_USER              Whether the current user login
                                                should be used as the effective
                                                user.
       --description-format DESCRIPTION_FORMAT  This template is used to
                                                generate the description.
       --file TEMPLATE                          Path to a file that contains
                                                the template.
       --job-category JOB_CATEGORY              Job category.
       --location-ids LOCATION_IDS              Comma separated list of values.
       --locations LOCATION_NAMES               Comma separated list of values.
       --locked LOCKED                          Whether or not the template is
                                                locked for editing.
       --name NAME                              Template name
       --organization-ids ORGANIZATION_IDS      Comma separated list of values.
       --organizations ORGANIZATION_NAMES       Comma separated list of values.
       --overridable OVERRIDABLE                Whether it should be allowed to
                                                override the effective user
                                                from the invocation form.
       --provider-type PROVIDER_TYPE            Possible value(s): 'SSH'
       --snippet SNIPPET                        One of true/false, yes/no, 1/0.
       --value VALUE                            What user should be used to run
                                                the script (using sudo-like
                                                mechanisms).

    """
    args = {
        u'audit-comment': None,
        u'current-user': None,
        u'description-format': None,
        u'file': None,
        u'job-category': u'Miscellaneous',
        u'location-ids': None,
        u'locations': None,
        u'name': None,
        u'organization-ids': None,
        u'organizations': None,
        u'overridable': None,
        u'provider-type': u'SSH',
        u'snippet': None,
        u'value': None,
    }

    return create_object(JobTemplate, args, options)


@cacheable
def make_user(options=None):
    """
    Usage::

        hammer user create [OPTIONS]

    Options::

        --admin ADMIN                       Is an admin account?
        --auth-source-id AUTH_SOURCE_ID
        --default-location-id DEFAULT_LOCATION_ID
        --default-organization-id DEFAULT_ORGANIZATION_ID
        --firstname FIRSTNAME
        --lastname LASTNAME
        --location-ids LOCATION_IDS         REPLACE locations with given ids
                                            Comma separated list of values.
        --login LOGIN
        --mail MAIL
        --organization-ids ORGANIZATION_IDS REPLACE organizations with
                                            given ids.
                                            Comma separated list of values.
        --password PASSWORD
        -h, --help                          print help

    """
    login = gen_alphanumeric(6)

    # Assigning default values for attributes
    args = {
        u'admin': None,
        u'auth-source-id': 1,
        u'default-location-id': None,
        u'default-organization-id': None,
        u'firstname': gen_alphanumeric(),
        u'lastname': gen_alphanumeric(),
        u'location-ids': None,
        u'login': login,
        u'mail': '{0}@example.com'.format(login),
        u'organization-ids': None,
        u'password': gen_alphanumeric(),
    }
    logger.debug(
        'User "{0}" password not provided {1} was generated'
        .format(args['login'], args['password'])
    )

    return create_object(User, args, options)


@cacheable
def make_usergroup(options=None):
    """
    Usage:
        hammer user-group create [OPTIONS]

    Options:
        --name NAME
        --role-ids ROLE_IDS                              Comma separated list
        --roles ROLE_NAMES                               Comma separated list
        --user-group-ids, --usergroup-ids USER_GROUP_IDS Comma separated list
        --user-groups, --usergroups USER_GROUP_NAMES     Comma separated list
        --user-ids USER_IDS                              Comma separated list
        --users USER_LOGINS                              Comma separated list
    """
    # Assigning default values for attributes
    args = {
        u'name': gen_alphanumeric(),
        u'role-ids': None,
        u'roles': None,
        u'user-group-ids': None,
        u'user-groups': None,
        u'user-ids': None,
        u'users': None,
    }

    return create_object(UserGroup, args, options)


@cacheable
def make_usergroup_external(options=None):
    """
    Usage::

        hammer user-group external create [OPTIONS]

    Options::

        --auth-source-id AUTH_SOURCE_ID           ID of linked auth source
        --name NAME                               External user group name
        --user-group, --usergroup USER_GROUP_NAME Name to search by
        --user-group-id, --usergroup-id USER_GROUP_ID
    """
    # UserGroup Name or ID is a required field.
    if (
        not options or
        not options.get('user-group') and
        not options.get('user-group-id')
    ):
        raise CLIFactoryError('Please provide a valid UserGroup.')

    # Assigning default values for attributes
    args = {
        u'auth-source-id': 1,
        u'name': gen_alphanumeric(8),
        u'user-group': None,
        u'user-group-id': None,
    }

    return create_object(UserGroupExternal, args, options)


@cacheable
def make_compute_resource(options=None):
    """
    Usage::

        hammer compute-resource create [OPTIONS]

    Options::

        --description DESCRIPTION
        --location-ids LOCATION_IDS   Comma separated list of values.
        --locations LOCATION_NAMES    Comma separated list of values.
        --name NAME
        --organization-ids ORGANIZATION_IDS  Comma separated list of values.
        --organizations ORGANIZATION_NAMES   Comma separated list of values.
        --password PASSWORD           Password for Ovirt, EC2, Vmware,
                                      Openstack. Access Key for EC2.
        --provider PROVIDER           Providers include Libvirt, Ovirt, EC2,
                                      Vmware, Openstack, Rackspace, GCE
        --region REGION               for EC2 only
        --server SERVER               for Vmware
        --set-console-password SET_CONSOLE_PASSWORD for Libvirt and Vmware only
                                                    One of true/false,
                                                    yes/no, 1/0.
        --tenant TENANT               for Openstack only
        --url URL                     URL for Libvirt, Ovirt, and Openstack
        --user USER                   Username for Ovirt, EC2, Vmware,
                                      Openstack. Secret key for EC2
        --uuid UUID                   for Ovirt, Vmware Datacenter
        -h, --help                    print help

    """
    args = {
        u'description': None,
        u'location-ids': None,
        u'locations': None,
        u'name': gen_alphanumeric(8),
        u'organization-ids': None,
        u'organizations': None,
        u'password': None,
        u'provider': None,
        u'region': None,
        u'server': None,
        u'set-console-password': None,
        u'tenant': None,
        u'url': None,
        u'user': None,
        u'uuid': None,
    }

    if options is None:
        options = {}

    if options.get('provider') is None:
        options['provider'] = FOREMAN_PROVIDERS['libvirt']
        if options.get('url') is None:
            options['url'] = 'qemu+tcp://localhost:16509/system'

    return create_object(ComputeResource, args, options)


@cacheable
def make_org(options=None):
    """
    Usage::

        hammer organization create [OPTIONS]

    Options::

        --compute-resource-ids COMPUTE_RESOURCE_IDS Compute resource IDs
                                                    Comma separated list
                                                    of values.
        --compute-resources COMPUTE_RESOURCE_NAMES  Compute resource Names
                                                    Comma separated list
                                                    of values.
        --config-template-ids CONFIG_TEMPLATE_IDS   Provisioning template IDs
                                                    Comma separated list
                                                    of values.
        --config-templates CONFIG_TEMPLATE_NAMES    Provisioning template Names
                                                    Comma separated list
                                                    of values.
        --description DESCRIPTION                   description
        --domain-ids DOMAIN_IDS                     Domain IDs
                                                    Comma separated list
                                                    of values.
        --environment-ids ENVIRONMENT_IDS           Environment IDs
                                                    Comma separated list
                                                    of values.
        --environments ENVIRONMENT_NAMES            Environment Names
                                                    Comma separated list
                                                    of values.
        --hostgroup-ids HOSTGROUP_IDS               Host group IDs
                                                    Comma separated list
                                                    of values.
        --hostgroups HOSTGROUP_NAMES                Host group Names
                                                    Comma separated list
                                                    of values.
        --label LABEL                               unique label
        --media MEDIUM_NAMES                        Media Names
                                                    Comma separated list
                                                    of values.
        --media-ids MEDIA_IDS                       Media IDs
                                                    Comma separated list
                                                    of values.
        --name NAME                                 name
        --realms REALM_NAMES                        Realm Names
                                                    Comma separated list
                                                    of values.
        --realm-ids REALM_IDS                       Realm IDs
                                                    Comma separated list
                                                    of values.
        --smart-proxies SMART_PROXY_NAMES           Smart proxy Names
                                                    Comma separated list
                                                    of values.
        --smart-proxy-ids SMART_PROXY_IDS           Smart proxy IDs
                                                    Comma separated list
                                                    of values.
        --subnet-ids SUBNET_IDS                     Subnet IDs
                                                    Comma separated list
                                                    of values.
        --subnets SUBNET_NAMES                      Subnet Names
                                                    Comma separated list
                                                    of values.
        --user-ids USER_IDS                         User IDs
                                                    Comma separated list
                                                    of values.
        --users USER_NAMES                          User Names
                                                    Comma separated list
                                                    of values.
        -h, --help                                  print help

    """
    # Assigning default values for attributes
    args = {
        u'compute-resource-ids': None,
        u'compute-resources': None,
        u'config-template-ids': None,
        u'config-templates': None,
        u'description': None,
        u'domain-ids': None,
        u'environment-ids': None,
        u'environments': None,
        u'hostgroup-ids': None,
        u'hostgroups': None,
        u'label': None,
        u'media-ids': None,
        u'media': None,
        u'name': gen_alphanumeric(6),
        u'realm-ids': None,
        u'realms': None,
        u'smart-proxy-ids': None,
        u'smart-proxies': None,
        u'subnet-ids': None,
        u'subnets': None,
        u'user-ids': None,
        u'users': None,
    }

    return create_object(Org, args, options)


@cacheable
def make_os(options=None):
    """
    Usage::

        hammer os create [OPTIONS]

    Options::

        --architecture-ids ARCHITECTURE_IDS       IDs of associated
                                                  architectures. Comma
                                                  separated list of values.
        --architectures ARCHITECTURE_NAMES        Comma separated list of
                                                  values.
        --config-template-ids CONFIG_TEMPLATE_IDS IDs of associated
                                                  provisioning templates. Comma
                                                  separated list of values.
        --config-templates CONFIG_TEMPLATE_NAMES  Comma separated list of
                                                  values.
        --description DESCRIPTION
        --family FAMILY
        --major MAJOR
        --media MEDIUM_NAMES                      Comma separated list of
                                                  values.
        --medium-ids MEDIUM_IDS                   IDs of associated media.
                                                  Comma separated list of
                                                  values.
        --minor MINOR
        --name NAME
        --partition-table-ids PARTITION_TABLE_IDS IDs of associated partition
                                                  tables. Comma separated list
                                                  of values.
        --partition-tables PARTITION_TABLE_NAMES  Comma separated list of
                                                  values.
        --password-hash PASSWORD_HASH             Root password hash function
                                                  to use, one of MD5, SHA256,
                                                  SHA512
        --release-name RELEASE_NAME
        -h, --help                    print help

    """
    # Assigning default values for attributes
    args = {
        u'architecture-ids': None,
        u'architectures': None,
        u'config-template-ids': None,
        u'config-templates': None,
        u'description': None,
        u'family': None,
        u'major': random.randint(0, 10),
        u'media': None,
        u'medium-ids': None,
        u'minor': random.randint(0, 10),
        u'name': gen_alphanumeric(6),
        u'partition-table-ids': None,
        u'partition-tables': None,
        u'password-hash': None,
        u'release-name': None,
    }

    return create_object(OperatingSys, args, options)


@cacheable
def make_domain(options=None):
    """
    Usage::

        hammer domain create [OPTIONS]

    Options::

        --description DESC            Full name describing the domain
        --dns-id DNS_ID               DNS Proxy to use within this domain
        --location-ids LOCATION_IDS   REPLACE locations with given ids
                                      Comma separated list of values.
        --locations LOCATION_NAMES    Comma separated list of values.
        --name NAME                   The full DNS Domain name
        --organization-ids ORGANIZATION_IDS REPLACE organizations with
                                            given ids.
                                            Comma separated list of values.
        --organizations ORGANIZATION_NAMES  Comma separated list of values.
        -h, --help                          print help

    """
    # Assigning default values for attributes
    args = {
        u'description': None,
        u'dns-id': None,
        u'location-ids': None,
        u'locations': None,
        u'name': gen_alphanumeric().lower(),
        u'organization-ids': None,
        u'organizations': None,
    }

    return create_object(Domain, args, options)


@cacheable
def make_hostgroup(options=None):
    """
    Usage::

        hammer hostgroup create [OPTIONS]

    Options::

        --architecture ARCHITECTURE_NAME Architecture name
        --architecture-id ARCHITECTURE_ID
        --ask-root-pass ASK_ROOT_PW  One of true/false, yes/no, 1/0.
        --content-source-id CONTENT_SOURCE_ID
        --content-view CONTENT_VIEW_NAME Name to search by
        --content-view-id CONTENT_VIEW_ID content view numeric identifier

        --domain DOMAIN_NAME          Domain name
        --domain-id DOMAIN_ID         May be numerical id or domain name
        --environment ENVIRONMENT_NAME Environment name
        --environment-id ENVIRONMENT_ID
        --lifecycle-environment LIFECYCLE_ENVIRONMENT_NAME   Name to search by
        --lifecycle-environment-id LIFECYCLE_ENVIRONMENT_ID

        --location-ids LOCATION_IDS   REPLACE locations with given ids
                                      Comma separated list of values.
        --medium MEDIUM_NAME          Medium name
        --medium-id MEDIUM_ID
        --name NAME
        --operatingsystem OPERATINGSYSTEM_TITLE Operating system title
        --operatingsystem-id OPERATINGSYSTEM_ID
        --organization-ids ORGANIZATION_IDS     REPLACE organizations with
                                                given ids.
                                                Comma separated list of values.
        --parent-id PARENT_ID
        --ptable PTABLE_NAME                    Partition table name
        --ptable-id PTABLE_ID
        --puppet-ca-proxy PUPPET_CA_PROXY_NAME  Name of puppet CA proxy
        --puppet-ca-proxy-id PUPPET_CA_PROXY_ID
        --puppet-class-ids PUPPETCLASS_IDS      List of puppetclass ids
                                                Comma separated list of values.
        --puppet-classes PUPPET_CLASS_NAMES     Comma separated list of values.
        --puppet-proxy PUPPET_CA_PROXY_NAME     Name of puppet proxy
        --puppet-proxy-id PUPPET_PROXY_ID
        --realm REALM_NAME                 Name to search by
        --realm-id REALM_ID                May be numerical id or realm name
        --subnet SUBNET_NAME               Subnet name
        --subnet-id SUBNET_ID
        -h, --help                         print help

    """
    # Assigning default values for attributes
    args = {
        u'architecture': None,
        u'architecture-id': None,
        u'content-source-id': None,
        u'content-view': None,
        u'content-view-id': None,
        u'domain': None,
        u'domain-id': None,
        u'environment': None,
        u'environment-id': None,
        u'location-ids': None,
        u'lifecycle-environment': None,
        u'lifecycle-environment-id': None,
        u'lifecycle-environment-organization-id': None,
        u'medium': None,
        u'medium-id': None,
        u'name': gen_alphanumeric(6),
        u'operatingsystem': None,
        u'operatingsystem-id': None,
        u'organization-id': None,
        u'organization-ids': None,
        u'parent-id': None,
        u'partition-table': None,
        u'partition-table-id': None,
        u'puppet-ca-proxy': None,
        u'puppet-ca-proxy-id': None,
        u'puppet-class-ids': None,
        u'puppet-classes': None,
        u'puppet-proxy': None,
        u'puppet-proxy-id': None,
        u'realm': None,
        u'realm-id': None,
        u'subnet': None,
        u'subnet-id': None,
    }

    return create_object(HostGroup, args, options)


@cacheable
def make_medium(options=None):
    """
    Usage::

        hammer medium create [OPTIONS]

    Options::

        --location-ids LOCATION_IDS   REPLACE locations with given ids
                                      Comma separated list of values.
        --locations LOCATION_NAMES    Comma separated list of values.
        --name NAME             Name of media
        --operatingsystem-ids OPERATINGSYSTEM_IDS REPLACE organizations with
                                                  given ids.
                                                  Comma separated list of
                                                  values.
        --operatingsystems OPERATINGSYSTEM_TITLES Comma separated list of
                                                  values.
        --organization-ids ORGANIZATION_IDS       Comma separated list of
                                                  values.
        --organizations ORGANIZATION_NAMES        Comma separated list of
                                                  values.
        --os-family OS_FAMILY   The family that the operating system belongs
                                to. Available families:
                                Archlinux
                                Debian
                                Gentoo
                                Redhat
                                Solaris
                                Suse
                                Windows
        --path PATH             The path to the medium, can be a URL or a valid
                                NFS server (exclusive of the architecture)
                                for example http://mirror.centos.org/centos/
                                $version/os/$arch where $arch will be
                                substituted for the host’s actual OS
                                architecture and $version, $major and $minor
                                will be substituted for the version of the
                                operating system.
                                Solaris and Debian media may also use $release.
        -h, --help                         print help

    """
    # Assigning default values for attributes
    args = {
        u'location-ids': None,
        u'locations': None,
        u'name': gen_alphanumeric(6),
        u'operatingsystem-ids': None,
        u'operatingsystems': None,
        u'organization-ids': None,
        u'organizations': None,
        u'os-family': None,
        u'path': 'http://{0}'.format((gen_string('alpha', 6))),
    }

    return create_object(Medium, args, options)


@cacheable
def make_environment(options=None):
    """
    Usage::

        hammer environment create [OPTIONS]

    Options::

        --location-ids LOCATION_IDS   REPLACE locations with given ids
                                      Comma separated list of values.
        --name NAME
        --organization-ids ORGANIZATION_IDS   REPLACE organizations with
                                              given ids.
                                              Comma separated list of values.
        -h, --help                            print help

    """
    # Assigning default values for attributes
    args = {
        u'location-ids': None,
        u'name': gen_alphanumeric(6),
        u'organization-ids': None,
    }

    return create_object(Environment, args, options)


@cacheable
def make_lifecycle_environment(options=None):
    """
    Usage::

        hammer lifecycle-environment create [OPTIONS]

    Options::

        --description DESCRIPTION   description of the environment
        --label LABEL               label of the environment
        --name NAME                 name of the environment
        --organization ORGANIZATION_NAME        Organization name to search by
        --organization-id ORGANIZATION_ID       organization ID
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --prior PRIOR               Name of an environment that is prior to
                                    the new environment in the chain. It has to
                                    be either ‘Library’ or an environment at
                                    the end of a chain.
        -h, --help                  print help

    """
    # Organization Name, Label or ID is a required field.
    if (
            not options or
            'organization' not in options and
            'organization-label' not in options and
            'organization-id' not in options):
        raise CLIFactoryError('Please provide a valid Organization.')

    if not options.get('prior'):
        options['prior'] = 'Library'

    # Assigning default values for attributes
    args = {
        u'description': None,
        u'label': None,
        u'name': gen_alphanumeric(6),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'prior': None,
    }

    return create_object(LifecycleEnvironment, args, options)


@cacheable
def make_template(options=None):
    """
    Usage::

        hammer template create [OPTIONS]

    Options::

        --audit-comment AUDIT_COMMENT
        --file TEMPLATE     Path to a file that contains the template
        --location-ids LOCATION_IDS   REPLACE locations with given ids
                                      Comma separated list of values.
        --locked LOCKED               Whether or not the template is locked
                                      for editing
                                      One of true/false, yes/no, 1/0.
        --name NAME         template name
        --operatingsystem-ids OPERATINGSYSTEM_IDS
                            Array of operating systems ID to associate the
                            template with Comma separated list of values.
        --organization-ids ORGANIZATION_IDS REPLACE organizations with
                                            given ids.
                                            Comma separated list of values.
        --type TYPE         Template type. Eg. snippet, script, provision
        -h, --help                  print help

    """
    # Assigning default values for attribute
    args = {
        u'audit-comment': None,
        u'file': '/tmp/{0}'.format(gen_alphanumeric()),
        u'location-ids': None,
        u'locked': None,
        u'name': gen_alphanumeric(6),
        u'operatingsystem-ids': None,
        u'organization-ids': None,
        u'type': random.choice(TEMPLATE_TYPES),
    }

    # Write content to file or random text
    if options is not None and 'content' in options.keys():
        content = options.pop('content')
    else:
        content = gen_alphanumeric()

    # Special handling for template factory
    (_, layout) = mkstemp(text=True)
    chmod(layout, 0o700)
    with open(layout, 'w') as ptable:
        ptable.write(content)
    # Upload file to server
    ssh.upload_file(local_file=layout, remote_file=args['file'])
    # End - Special handling for template factory

    return create_object(Template, args, options)


@cacheable
def make_smart_variable(options=None):
    """
    Usage::

        hammer smart-variable create [OPTIONS]

    Options::

        --avoid-duplicates AVOID_DUPLICATES         Remove duplicate values (
                                                    only array type)
                                                    One of true/false, yes/no,
                                                    1/0.
        --default-value DEFAULT_VALUE               Default value of variable
        --description DESCRIPTION                   Description of variable
        --hidden-value HIDDEN_VALUE                 When enabled the parameter
                                                    is hidden in the UI
                                                    One of true/false, yes/no,
                                                    1/0.
        --merge-default MERGE_DEFAULT               Include default value when
                                                    merging all matching values
                                                    One of true/false, yes/no,
                                                    1/0.
        --merge-overrides MERGE_OVERRIDES           Merge all matching values(
                                                    only array/hash type)
                                                    One of true/false, yes/no,
                                                    1/0.
        --override-value-order OVERRIDE_VALUE_ORDER The order in which values
                                                    are resolved
        --puppet-class PUPPET_CLASS_NAME            Puppet class name
        --puppet-class-id PUPPET_CLASS_ID           ID of Puppet class
        --validator-rule VALIDATOR_RULE             Used to enforce certain
                                                    values for the parameter
                                                    values
        --validator-type VALIDATOR_TYPE             Type of the validator.
                                                    Possible value(s):
                                                    'regexp', 'list', ''
        --variable VARIABLE                         Name of variable
        --variable-type VARIABLE_TYPE               Type of the variable.
                                                    Possible value(s):
                                                    'string', 'boolean',
                                                    'integer', 'real', 'array',
                                                    'hash', 'yaml', 'json'
         -h, --help                                 print help

    """
    # Puppet class name or ID is a required field.
    if (
            not options or
            'puppet-class' not in options and
            'puppet-class-id' not in options):
        raise CLIFactoryError('Please provide a valid Puppet class')

    # Assigning default values for attributes
    args = {
        u'avoid-duplicates': None,
        u'default-value': None,
        u'description': None,
        u'hidden-value': None,
        u'merge-default': None,
        u'merge-overrides': None,
        u'override-value-order': None,
        u'puppet-class': None,
        u'puppet-class-id': None,
        u'validator-rule': None,
        u'validator-type': None,
        u'variable': gen_alphanumeric(),
        u'variable-type': None,
    }

    return create_object(SmartVariable, args, options)


def activationkey_add_subscription_to_repo(options=None):
    """
    Adds subscription to activation key.

    Args::

        organization-id - ID of organization
        activationkey-id - ID of activation key
        subscription - subscription name

    """
    if(
            not options or
            not options.get('organization-id') or
            not options.get('activationkey-id') or
            not options.get('subscription')):
        raise CLIFactoryError(
            'Please provide valid organization, activation key and '
            'subscription.'
        )
    # List the subscriptions in given org
    subscriptions = Subscription.list(
        {u'organization-id': options['organization-id']},
        per_page=False
    )
    # Add subscription to activation-key
    if options['subscription'] not in (sub['name'] for sub in subscriptions):
        raise CLIFactoryError(
            u'Subscription {0} not found in the given org'
            .format(options['subscription'])
        )
    for subscription in subscriptions:
        if subscription['name'] == options['subscription']:
            if (
                    subscription['quantity'] != 'Unlimited' and
                    int(subscription['quantity']) == 0):
                raise CLIFactoryError(
                    'All the subscriptions are already consumed')
            try:
                ActivationKey.add_subscription({
                    u'id': options['activationkey-id'],
                    u'subscription-id': subscription['id'],
                    u'quantity': 1,
                })
            except CLIReturnCodeError as err:
                raise CLIFactoryError(
                    u'Failed to add subscription to activation key\n{0}'
                    .format(err.msg)
                )


def setup_org_for_a_custom_repo(options=None):
    """Sets up Org for the given custom repo by:

    1. Checks if organization and lifecycle environment were given, otherwise
        creates new ones.
    2. Creates a new product with the custom repo. Synchronizes the repo.
    3. Checks if content view was given, otherwise creates a new one and
        - adds the RH repo
        - publishes
        - promotes to the lifecycle environment
    4. Checks if activation key was given, otherwise creates a new one and
        associates it with the content view.
    5. Adds the custom repo subscription to the activation key

    Options::

        url - URL to custom repository
        organization-id (optional) - ID of organization to use (or create a new
                                    one if empty)
        lifecycle-environment-id (optional) - ID of lifecycle environment to
                                             use (or create a new one if empty)
        content-view-id (optional) - ID of content view to use (or create a new
                                    one if empty)
        activationkey-id (optional) - ID of activation key (or create a new one
                                    if empty)

    :return: A dictionary with the entity ids of Activation key, Content view,
        Lifecycle Environment, Organization, Product and Repository

    """
    if(
            not options or
            not options.get('url')):
        raise CLIFactoryError('Please provide valid custom repo URL.')
    # Create new organization and lifecycle environment if needed
    if options.get('organization-id') is None:
        org_id = make_org()['id']
    else:
        org_id = options['organization-id']
    if options.get('lifecycle-environment-id') is None:
        env_id = make_lifecycle_environment({u'organization-id': org_id})['id']
    else:
        env_id = options['lifecycle-environment-id']
    # Create custom product and repository
    custom_product = make_product({u'organization-id': org_id})
    custom_repo = make_repository({
        u'content-type': 'yum',
        u'product-id': custom_product['id'],
        u'url': options.get('url'),
    })
    # Synchronize custom repository
    try:
        Repository.synchronize({'id': custom_repo['id']})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to synchronize repository\n{0}'.format(err.msg))
    # Create CV if needed and associate repo with it
    if options.get('content-view-id') is None:
        cv_id = make_content_view({u'organization-id': org_id})['id']
    else:
        cv_id = options['content-view-id']
    try:
        ContentView.add_repository({
            u'id': cv_id,
            u'organization-id': org_id,
            u'repository-id': custom_repo['id'],
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to add repository to content view\n{0}'.format(err.msg))
    # Publish a new version of CV
    try:
        ContentView.publish({u'id': cv_id})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to publish new version of content view\n{0}'
            .format(err.msg)
        )
    # Get the version id
    cvv = ContentView.info({u'id': cv_id})['versions'][-1]
    # Promote version to next env
    try:
        ContentView.version_promote({
            u'id': cvv['id'],
            u'organization-id': org_id,
            u'to-lifecycle-environment-id': env_id,
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to promote version to next environment\n{0}'
            .format(err.msg)
        )
    # Create activation key if needed and associate content view with it
    if options.get('activationkey-id') is None:
        activationkey_id = make_activation_key({
            u'content-view-id': cv_id,
            u'lifecycle-environment-id': env_id,
            u'organization-id': org_id,
        })['id']
    else:
        activationkey_id = options['activationkey-id']
        # Given activation key may have no (or different) CV associated.
        # Associate activation key with CV just to be sure
        try:
            ActivationKey.update({
                u'content-view-id': cv_id,
                u'id': activationkey_id,
                u'organization-id': org_id,
            })
        except CLIReturnCodeError as err:
            raise CLIFactoryError(
                u'Failed to associate activation-key with CV\n{0}'
                .format(err.msg)
            )
    # Add subscription to activation-key
    activationkey_add_subscription_to_repo({
        u'activationkey-id': activationkey_id,
        u'organization-id': org_id,
        u'subscription': custom_product['name'],
    })
    return {
        u'activationkey-id': activationkey_id,
        u'content-view-id': cv_id,
        u'lifecycle-environment-id': env_id,
        u'organization-id': org_id,
        u'product-id': custom_product['id'],
        u'repository-id': custom_repo['id'],
    }


def setup_org_for_a_rh_repo(options=None):
    """Sets up Org for the given Red Hat repository by:

    1. Checks if organization and lifecycle environment were given, otherwise
        creates new ones.
    2. Clones and uploads manifest.
    3. Enables RH repo and synchronizes it.
    4. Checks if content view was given, otherwise creates a new one and
        - adds the RH repo
        - publishes
        - promotes to the lifecycle environment
    5. Checks if activation key was given, otherwise creates a new one and
        associates it with the content view.
    6. Adds the RH repo subscription to the activation key

    Options::

        product - RH product name
        repository-set - RH repository set name
        repository - RH repository name
        releasever (optional) - Repository set release version, don't specify
                                it if enabling the Satellite 6 Tools repo.
        organization-id (optional) - ID of organization to use (or create a new
                                    one if empty)
        lifecycle-environment-id (optional) - ID of lifecycle environment to
                                             use (or create a new one if empty)
        content-view-id (optional) - ID of content view to use (or create a new
                                    one if empty)
        activationkey-id (optional) - ID of activation key (or create a new one
                                    if empty)

    :return: A dictionary with the entity ids of Activation key, Content view,
        Lifecycle Environment, Organization and Repository

    """
    if (
            not options or
            not options.get('product') or
            not options.get('repository-set') or
            not options.get('repository')):
        raise CLIFactoryError(
            'Please provide valid product, repository-set and repo.')
    # Create new organization and lifecycle environment if needed
    if options.get('organization-id') is None:
        org_id = make_org()['id']
    else:
        org_id = options['organization-id']
    if options.get('lifecycle-environment-id') is None:
        env_id = make_lifecycle_environment({u'organization-id': org_id})['id']
    else:
        env_id = options['lifecycle-environment-id']
    # Clone manifest and upload it
    with manifests.clone() as manifest:
        upload_file(manifest.content, manifest.filename)
    try:
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': org_id,
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to upload manifest\n{0}'.format(err.msg))
    # Enable repo from Repository Set
    try:
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'name': options['repository-set'],
            u'organization-id': org_id,
            u'product': options['product'],
            u'releasever': options.get('releasever'),
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to enable repository set\n{0}'.format(err.msg))
    # Fetch repository info
    try:
        rhel_repo = Repository.info({
            u'name': options['repository'],
            u'organization-id': org_id,
            u'product': options['product'],
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to fetch repository info\n{0}'.format(err.msg))
    # Synchronize the RH repository
    try:
        Repository.synchronize({
            u'name': options['repository'],
            u'organization-id': org_id,
            u'product': options['product'],
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to synchronize repository\n{0}'.format(err.msg))
    # Create CV if needed and associate repo with it
    if options.get('content-view-id') is None:
        cv_id = make_content_view({u'organization-id': org_id})['id']
    else:
        cv_id = options['content-view-id']
    try:
        ContentView.add_repository({
            u'id': cv_id,
            u'organization-id': org_id,
            u'repository-id': rhel_repo['id'],
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to add repository to content view\n{0}'.format(err.msg))
    # Publish a new version of CV
    try:
        ContentView.publish({u'id': cv_id})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to publish new version of content view\n{0}'
            .format(err.msg)
        )
    # Get the version id
    try:
        cvv = ContentView.info({u'id': cv_id})['versions'][-1]
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to fetch content view info\n{0}'.format(err.msg))
    # Promote version1 to next env
    try:
        ContentView.version_promote({
            u'id': cvv['id'],
            u'organization-id': org_id,
            u'to-lifecycle-environment-id': env_id,
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            u'Failed to promote version to next environment\n{0}'
            .format(err.msg)
        )
    # Create activation key if needed and associate content view with it
    if options.get('activationkey-id') is None:
        activationkey_id = make_activation_key({
            u'content-view-id': cv_id,
            u'lifecycle-environment-id': env_id,
            u'organization-id': org_id,
        })['id']
    else:
        activationkey_id = options['activationkey-id']
        # Given activation key may have no (or different) CV associated.
        # Associate activation key with CV just to be sure
        try:
            ActivationKey.update({
                u'id': activationkey_id,
                u'organization-id': org_id,
                u'content-view-id': cv_id,
            })
        except CLIReturnCodeError as err:
            raise CLIFactoryError(
                u'Failed to associate activation-key with CV\n{0}'
                .format(err.msg)
            )
    # Add subscription to activation-key
    activationkey_add_subscription_to_repo({
        u'organization-id': org_id,
        u'activationkey-id': activationkey_id,
        u'subscription': DEFAULT_SUBSCRIPTION_NAME,
    })
    return {
        u'activationkey-id': activationkey_id,
        u'content-view-id': cv_id,
        u'lifecycle-environment-id': env_id,
        u'organization-id': org_id,
        u'repository-id': rhel_repo['id'],
    }
