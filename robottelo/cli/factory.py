# -*- encoding: utf-8 -*-
"""
Factory object creation for all CLI methods
"""

import datetime
import json
import logging
import os
import random
import time

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
from robottelo.cli.ldapauthsource import LDAPAuthSource
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.location import Location
from robottelo.cli.medium import Medium
from robottelo.cli.model import Model
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.org import Org
from robottelo.cli.partitiontable import PartitionTable
from robottelo.cli.product import Product
from robottelo.cli.proxy import CapsuleTunnelError, Proxy
from robottelo.cli.realm import Realm
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.role import Role
from robottelo.cli.scapcontent import Scapcontent
from robottelo.cli.subnet import Subnet
from robottelo.cli.subscription import Subscription
from robottelo.cli.syncplan import SyncPlan
from robottelo.cli.scap_policy import Scappolicy
from robottelo.cli.scap_tailoring_files import TailoringFiles
from robottelo.cli.template import Template
from robottelo.cli.user import User
from robottelo.cli.usergroup import UserGroup, UserGroupExternal
from robottelo.cli.smart_variable import SmartVariable
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_LOC,
    DEFAULT_ORG,
    DEFAULT_PTABLE,
    DEFAULT_PXE_TEMPLATE,
    DEFAULT_SUBSCRIPTION_NAME,
    DEFAULT_TEMPLATE,
    DISTRO_RHEL7,
    FAKE_1_YUM_REPO,
    FOREMAN_PROVIDERS,
    OPERATING_SYSTEMS,
    PRDS,
    REPOS,
    REPOSET,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
    SYNC_INTERVAL,
    TEMPLATE_TYPES,
)
from robottelo.decorators import bz_bug_is_open, cacheable
from robottelo.helpers import (
    update_dictionary, default_url_on_new_port, get_available_capsule_port
)
from robottelo.ssh import download_file, upload_file
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


def _entity_with_credentials(credentials, cli_entity_cls):
    """Create entity class using credentials. If credentials is None will
    return cli_entity_cls itself

    :param credentials: tuple (login, password)
    :param cli_entity_cls: Cli Entity Class
    :return: Cli Entity Class
    """
    if credentials is not None:
        cli_entity_cls = cli_entity_cls.with_user(*credentials)
    return cli_entity_cls


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
        --organization-label ORGANIZATION_LABEL Organization label to
        search by
        --product PRODUCT_NAME          Product name to search by
        --product-id PRODUCT_ID         product numeric identifier
        --repositories REPOSITORY_NAMES Comma separated list of values.
        --repository-ids REPOSITORY_IDS List of repository ids
                                        Comma separated list of values.
        -h, --help                    print help

    """
    return make_content_view_with_credentials(options)


def make_content_view_with_credentials(options=None, credentials=None):
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
        --product PRODUCT_NAME          Product name to search by
        --product-id PRODUCT_ID         product numeric identifier
        --repositories REPOSITORY_NAMES Comma separated list of values.
        --repository-ids REPOSITORY_IDS List of repository ids
                                        Comma separated list of values.
        -h, --help                    print help

    If credentials is None default credentials present on
    robottelo.properties will be used.

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
        u'product': None,
        u'product-id': None,
        u'repositories': None,
        u'repository-ids': None
    }

    cv_cls = _entity_with_credentials(credentials, ContentView)
    return create_object(cv_cls, args, options)


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
        u'parent-id': None,
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
        --operatingsystem-ids OPERATINGSYSTEM_IDS Array of operating system IDs
            to associate with the partition table Comma separated list of
            values. Values containing comma should be double quoted
        --operatingsystems OPERATINGSYSTEM_TITLES Comma separated list of
            values. Values containing comma should be double quoted
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
        u'operatingsystem-ids': None,
        u'operatingsystems': None,
        u'organization-ids': None,
        u'organizations': None,
        u'os-family': random.choice(OPERATING_SYSTEMS),
    }

    # Upload file to server
    ssh.upload_file(local_file=layout, remote_file=args['file'])

    return create_object(PartitionTable, args, options)


@cacheable
def make_product(options=None):
    return make_product_with_credentials(options)


def make_product_with_credentials(options=None, credentials=None):
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
    product_cls = _entity_with_credentials(credentials, Product)
    return create_object(product_cls, args, options)


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
    return make_repository_with_credentials(options)


def make_repository_with_credentials(options=None, credentials=None):
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
        --ignorable-content IGNORABLE_CONTENT   List of content units to ignore
                                                while syncing a yum repository.
                                                Subset of rpm, drpm, srpm,
                                                distribution, erratum
        --label LABEL
        --mirror-on-sync MIRROR_ON_SYNC         true if this repository when
                                                synced has to be mirrored from
                                                the source and stale rpms
                                                removed.
        --name NAME
        --organization ORGANIZATION_NAME        Organization name to search by
        --organization-id ORGANIZATION_ID       organization ID
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --ostree-upstream-sync-depth OSTREE_UPSTREAM_SYNC_DEPTH if a custom
                                                sync policy is chosen for
                                                ostree repositories then a
                                                'depth' value must be provided.
        --ostree-upstream-sync-policy OSTREE_UPSTREAM_SYNC_POLICY policies for
                                                syncing upstream ostree
                                                repositories. Possible
                                                value(s): 'latest', 'all',
                                                'custom'
        --product PRODUCT_NAME                  Product name to search by
        --product-id PRODUCT_ID                 product numeric identifier
        --publish-via-http ENABLE               Publish Via HTTP
                                                One of true/false, yes/no, 1/0.
        --upstream-password UPSTREAM_PASSWORD   Password of the upstream
                                                repository user used for
                                                authentication
        --upstream-username UPSTREAM_USERNAME   Username of the upstream
                                                repository user used for
                                                authentication
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
        u'ignorable-content': None,
        u'label': None,
        u'mirror-on-sync': None,
        u'name': gen_string('alpha', 15),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'product': None,
        u'product-id': None,
        u'publish-via-http': u'true',
        u'url': FAKE_1_YUM_REPO,
    }
    repo_cls = _entity_with_credentials(credentials, Repository)
    return create_object(repo_cls, args, options)


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
        --override OVERRIDE                 One of true/false, yes/no, 1/0.
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
        u'override': None,
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
def make_scap_policy(options=None):
    """
    Usage::

        policy create [OPTIONS]

    Options::

         --cron-line CRON_LINE                                 Policy schedule
                                                               cron line
         --day-of-month DAY_OF_MONTH                           Policy schedule
                                                               day of month
                                                               (only if period
                                                               == “monthly”)
         --description DESCRIPTION                             Policy
                                                               description
         --hostgroup-ids HOSTGROUP_IDS                         Apply policy to
                                                               host groups
                                                               Comma separated
                                                               Values list of
                                                               values.
                                                               containing comma
                                                               or should be
                                                               quoted escaped
                                                               with backslash
         --hostgroups HOSTGROUP_NAMES                          Comma separated
                                                               list of values.
                                                               Values
                                                               containing
                                                               comma should be
                                                               quoted or
                                                               escaped with
                                                               backslash
         --location-ids LOCATION_IDS                           REPLACE
                                                               locations
                                                               with given ids
                                                               Comma separated
                                                               list of values.
                                                               containing comma
                                                               should be quoted
                                                               escaped with
                                                               backslash
         --locations LOCATION_NAMES                            Comma separated
                                                               list of values.
                                                               containing comma
                                                               should be quoted
                                                               escaped with
                                                               backslash
         --name NAME                                           Policy name
         --organization-ids ORGANIZATION_IDS                   REPLACE
                                                               organizations
                                                               with given ids.
                                                               Comma separated
                                                               list of values.
                                                               containing comma
                                                               should be quoted
                                                               escaped with
                                                               backslash
         --organizations ORGANIZATION_NAMES                    Comma separated
                                                               list of values.
                                                               containing comma
                                                               should be quoted
                                                               escaped with
                                                               backslash
         --period PERIOD                                       Policy schedule
                                                               period (weekly,
                                                               monthly, custom)
         --scap-content SCAP_CONTENT_TITLE                     SCAP content
                                                               title
         --scap-content-id SCAP_CONTENT_ID
         --scap-content-profile-id SCAP_CONTENT_PROFILE_ID     Policy SCAP
                                                               content
                                                               profile ID
         --tailoring-file TAILORING_FILE_NAME                  Tailoring file
                                                               name
         --tailoring-file-id TAILORING_FILE_ID
         --tailoring-file-profile-id TAILORING_FILE_PROFILE_ID Tailoring file
                                                               profile ID
         --weekday WEEKDAY                                     Policy schedule
                                                               weekday (only if
                                                               period
                                                               == “weekly”)
         -h, --help                                            print help

    """
    # Assigning default values for attributes
    # SCAP ID and SCAP profile ID is a required field.
    if not options and not options.get('scap-content-id') and not options.get(
            'scap-content-profile-id') and not options.get('period'):
        raise CLIFactoryError('Please provide a valid SCAP ID or'
                              ' SCAP Profile ID or Period')
    args = {
        u'description': None,
        u'scap-content-id': None,
        u'scap-content-profile-id': None,
        u'period': None,
        u'weekday': None,
        u'day-of-month': None,
        u'cron-line': None,
        u'hostgroup-ids': None,
        u'hostgroups': None,
        u'locations': None,
        u'organizations:': None,
        u'tailoring-file': None,
        u'tailoring-file-id': None,
        u'tailoring-file-profile-id': None,
        u'location-ids': None,
        u'name': gen_alphanumeric().lower(),
        u'organization-ids': None,
    }

    return create_object(Scappolicy, args, options)


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
        u'interval': random.choice(list(SYNC_INTERVAL.values())),
        u'name': gen_string('alpha', 20),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'sync-date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    return create_object(SyncPlan, args, options)


@cacheable
def make_host(options=None):
    """
    Usage::

        hammer host create [OPTIONS]

    Options::

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
        --config-group-ids CONFIG_GROUP_IDS         IDs of associated config
                                                    groups. Comma separated
                                                    list of values
        --config-groups CONFIG_GROUP_NAMES          Comma separated list of
                                                    values.
        --content-source-id CONTENT_SOURCE_ID
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
        --root-password ROOT_PW                     required if host is managed
                                                    and value is not inherited
                                                    from host group or default
                                                    password in settings
        --service-level SERVICE_LEVEL               Service level to be used
                                                    for autoheal.
        --subnet SUBNET_NAME                        Subnet name
        --subnet-id SUBNET_ID
        --volume VOLUME                             Volume parameters
                                                    Comma-separated list of
                                                    key=value.
                                                    Can be specified multiple
                                                    times.

    Available keys for --interface::

        mac
        ip
        type                                        Possible values: interface,
                                                    bmc, bond, bridge
        name
        subnet_id
        domain_id
        identifier
        managed                                     true/false
        primary                                     true/false, each managed
                                                    hosts needs to have one
                                                    primary interface.
        provision                                   true/false
        virtual                                     true/false
    """
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
        u'content-source-id': None,
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
        u'mac': gen_mac(multicast=False),
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
        --description DESCRIPTION
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
        u'description': None,
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
def make_ldap_auth_source(options=None):
    """
    Usage::

        hammer auth-source ldap create [OPTIONS]

    Options::

        --account ACCOUNT
        --account-password ACCOUNT_PASSWORD       required if onthefly_register
                                                  is true
        --attr-firstname ATTR_FIRSTNAME           required if onthefly_register
                                                  is true
        --attr-lastname ATTR_LASTNAME             required if onthefly_register
                                                  is true
        --attr-login ATTR_LOGIN                   required if onthefly_register
                                                  is true
        --attr-mail ATTR_MAIL                     required if onthefly_register
                                                  is true
        --attr-photo ATTR_PHOTO
        --base-dn BASE_DN
        --groups-base GROUPS_BASE                 groups base DN
        --host HOST
        --ldap-filter LDAP_FILTER                 LDAP filter
        --location-ids LOCATION_IDS               REPLACE locations with given
                                                  ids
                                                  Comma separated list of
                                                  values. Values containing
                                                  comma should be double quoted
        --locations LOCATION_NAMES                Comma separated list of
                                                  values. Values containing
                                                  comma should be double quoted
        --name NAME
        --onthefly-register                       ONTHEFLY_REGISTER One of
                                                  true/false, yes/no, 1/0.
        --organization-ids ORGANIZATION_IDS       REPLACE organizations with
                                                  given ids.
                                                  Comma separated list of
                                                  values. Values containing
                                                  comma should be double quoted
        --organizations ORGANIZATION_NAMES        Comma separated list of
                                                  values. Values containing
                                                  comma should be double quoted
        --port PORT                               defaults to 389
        --server-type SERVER_TYPE                 type of the LDAP server
                                                  Possible value(s):
                                                  'free_ipa',
                                                  'active_directory', 'posix'
        --tls TLS                                 One of true/false, yes/no,
                                                  1/0.
        --usergroup-sync USERGROUP_SYNC           sync external user groups on
                                                  login
                                                  One of true/false, yes/no,
                                                  1/0.
        -h, --help                                print help
    """
    # Assigning default values for attributes
    args = {
        u'account': None,
        u'account-password': None,
        u'attr-firstname': None,
        u'attr-lastname': None,
        u'attr-login': None,
        u'attr-mail': None,
        u'attr-photo': None,
        u'base-dn': None,
        u'groups-base': None,
        u'host': None,
        u'ldap-filter': None,
        u'location-ids': None,
        u'locations': None,
        u'name': gen_alphanumeric(),
        u'onthefly-register': None,
        u'organization-ids': None,
        u'organizations': None,
        u'port': None,
        u'server-type': None,
        u'tls': None,
        u'usergroup-sync': None,
    }

    return create_object(LDAPAuthSource, args, options)


@cacheable
def make_compute_resource(options=None):
    """
    Usage::

        hammer compute-resource create [OPTIONS]

    Options::

        --caching-enabled CACHING_ENABLED    enable caching, for VMware only
                                             One of true/false, yes/no, 1/0.
        --datacenter DATACENTER              for RHEV, VMware Datacenter
        --description DESCRIPTION
        --display-type DISPLAY_TYPE          for Libvirt only
                                             Possible value(s): 'VNC', 'SPICE'
        --location-ids LOCATION_IDS          REPLACE locations with given ids
                                             Comma separated list of values.
                                             Values containing comma should be
                                             quoted or escaped with backslash
        --location-titles LOCATION_TITLES    Comma separated list of values.
                                             Values containing comma should be
                                             quoted or escaped with backslash
        --locations LOCATION_NAMES           Comma separated list of values.
                                             Values containing comma should be
                                             quoted or escaped with backslash
        --name NAME
        --organization-ids ORGANIZATION_IDS  REPLACE organizations with given
                                             ids.
                                             Comma separated list of values.
                                             Values containing comma should be
                                             quoted or escaped with backslash
        --organization-titles ORGANIZATION_TITLES   Comma separated list of
                                                    values. Values containing
                                                    comma should be quoted or
                                                    escaped with backslash
        --organizations ORGANIZATION_NAMES   Comma separated list of values.
                                             Values containing comma should be
                                             quoted or escaped with backslash
        --password PASSWORD                  Password for RHEV, EC2, VMware,
                                             OpenStack. Secret key for EC2
        --provider PROVIDER                  Providers include Libvirt, Ovirt,
                                             EC2, Vmware, Openstack, Rackspace,
                                             GCE, Docker
        --region REGION                      for EC2 only
        --server SERVER                      for VMware
        --set-console-password SET_CONSOLE_PASSWORD for Libvirt and VMware only
                                                    One of true/false, yes/no,
                                                    1/0.
        --tenant TENANT                       for RHEL OpenStack Platform  only
        --url URL                             URL for Docker, Libvirt, RHEV,
                                              OpenStack and Rackspace
        --user USER                           Username for RHEV, EC2, VMware,
                                              OpenStack. Access Key for EC2.
        --uuid UUID                           Deprecated, please use datacenter
        -h, --help                            print help
    """
    args = {
        u'caching-enabled': None,
        u'datacenter': None,
        u'description': None,
        u'display-type': None,
        u'location-ids': None,
        u'location-titles': None,
        u'locations': None,
        u'name': gen_alphanumeric(8),
        u'organization-ids': None,
        u'organization-titles': None,
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
    return make_org_with_credentials(options)


def make_org_with_credentials(options=None, credentials=None):
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
    org_cls = _entity_with_credentials(credentials, Org)
    return create_object(org_cls, args, options)


@cacheable
def make_realm(options=None):
    """
    Usage::

        hammer realm create [OPTIONS]

    Options::

        --location-ids LOCATION_IDS         REPLACE locations with given ids
                                            Comma separated list of values.
                                            Values containing comma should
                                            be double quoted
        --locations LOCATION_NAMES          Comma separated list of values.
                                            Values containing comma should
                                            be double quoted
        --name NAME                         The realm name, e.g. EXAMPLE.COM
        --organization-ids ORGANIZATION_IDS REPLACE organizations with
                                            given ids.
                                            Comma separated list of values.
                                            Values containing comma should
                                            be double quoted
        --organizations ORGANIZATION_NAMES  Comma separated list of values.
                                            Values containing comma should
                                            be double quoted
        --realm-proxy-id REALM_PROXY_ID     Capsule ID to use within this realm
        --realm-type REALM_TYPE             Realm type, e.g.
                                            Red Hat Identity Management
                                            or Active Directory

        -h, --help                          print help

    """
    # Assigning default values for attributes
    args = {
        u'location-ids': None,
        u'locations': None,
        u'name': gen_alphanumeric(6),
        u'organization-ids': None,
        u'organizations': None,
        u'realm-proxy-id': None,
        u'realm-type': None,
    }

    return create_object(Realm, args, options)


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
def make_scapcontent(options=None):
    """
    Usage::

         scap-content create [OPTIONS]

    Options::

         --location-ids LOCATION_IDS           REPLACE locations with given ids
                                               Comma separated list of values.
                                               Values containing comma should
                                               be double quoted
         --locations LOCATION_NAMES            Comma separated list of values.
                                               Values containing comma should
                                               be double quoted
         --organization-ids ORGANIZATION_IDS   REPLACE organizations with given
                                               ids.
                                               Comma separated list of values.
                                               Values containing comma should
                                               be double quoted
         --organizations ORGANIZATION_NAMES    Comma separated list of values.
                                               Values containing comma should
                                               be double quoted
         --original-filename ORIGINAL_FILENAME Original file name of the XML
                                               file
         --scap-file SCAP_FILE                 Scap content file
         --title TITLE                         SCAP content name
         -h, --help                            print help
    """
    # Assigning default values for attributes
    args = {
        u'scap-file': None,
        u'original-filename': None,
        u'location-ids': None,
        u'locations': None,
        u'title': gen_alphanumeric().lower(),
        u'organization-ids': None,
        u'organizations': None,
    }

    return create_object(Scapcontent, args, options)


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

        --architecture ARCHITECTURE_NAME        Architecture name
        --architecture-id ARCHITECTURE_ID
        --ask-root-pass ASK_ROOT_PW             One of true/false, yes/no, 1/0.
        --compute-profile COMPUTE_PROFILE_NAME  Name to search by
        --compute-profile-id COMPUTE_PROFILE_ID
        --config-group-ids CONFIG_GROUP_IDS     IDs of associated config groups
        --config-groups CONFIG_GROUP_NAMES
        --content-source-id CONTENT_SOURCE_ID
        --content-view CONTENT_VIEW_NAME        Name to search by
        --content-view-id CONTENT_VIEW_ID       content view numeric identifier

        --domain DOMAIN_NAME                    Domain name
        --domain-id DOMAIN_ID                   Numerical ID or domain name
        --environment ENVIRONMENT_NAME          Environment name
        --environment-id ENVIRONMENT_ID
        --group-parameters-attributes GROUP_PARAMETERS_ATTRIBUTES    Array of
                                                                     parameters
        --kickstart-repository-id KICKSTART_REPOSITORY_ID    Kickstart
                                                             repository ID
        --lifecycle-environment LIFECYCLE_ENVIRONMENT_NAME    Name to search by
        --lifecycle-environment-id LIFECYCLE_ENVIRONMENT_ID    ID of the
                                                               environment
        --locations LOCATION_NAMES  Comma separated list of values
        --location-titles LOCATION_TITLES
        --location-ids LOCATION_IDS   REPLACE locations with given ids
                                      Comma separated list of values.
        --medium MEDIUM_NAME          Medium name
        --medium-id MEDIUM_ID
        --name NAME
        --openscap-proxy-id OPENSCAP_PROXY_ID      ID of OpenSCAP Capsule
        --operatingsystem OPERATINGSYSTEM_TITLE    Operating system title
        --operatingsystem-id OPERATINGSYSTEM_ID
        --organizations ORGANIZATION_NAMES   Comma separated list of values
        --organization-titles ORGANIZATION_TITLES
        --organization-ids ORGANIZATION_IDS     REPLACE organizations with
                                                given ids.
                                                Comma separated list of values.
        --parent PARENT_NAME                    Name of parent hostgroup
        --parent-id PARENT_ID
        --partition-table PTABLE_NAME           Partition table name
        --partition-table-id PTABLE_ID
        --puppet-ca-proxy PUPPET_CA_PROXY_NAME  Name of puppet CA proxy
        --puppet-ca-proxy-id PUPPET_CA_PROXY_ID
        --puppet-class-ids PUPPETCLASS_IDS      List of puppetclass ids
                                                Comma separated list of values.
        --puppet-classes PUPPET_CLASS_NAMES     Comma separated list of values.
        --puppet-proxy PUPPET_CA_PROXY_NAME     Name of puppet proxy
        --puppet-proxy-id PUPPET_PROXY_ID
        --pxe-loader PXE_LOADER                 DHCP filename option (
                                                Grub2/PXELinux by default)
        --query-organization ORGANIZATION_NAME  Organization name to search by
        --query-organization-id ORGANIZATION_ID Organization ID to search by
        --query-organization-label ORGANIZATION_LABEL    Organization label to
                                                         search by
        --realm REALM_NAME                 Name to search by
        --realm-id REALM_ID                Numerical ID or realm name
        --root-pass ROOT_PASSWORD
        --subnet SUBNET_NAME               Subnet name
        --subnet-id SUBNET_ID
        -h, --help                         print help

    """
    # Assigning default values for attributes
    args = {
        u'architecture': None,
        u'architecture-id': None,
        u'compute-profile': None,
        u'compute-profile-id': None,
        u'config-group-ids': None,
        u'config-groups': None,
        u'content-source-id': None,
        u'content-view': None,
        u'content-view-id': None,
        u'domain': None,
        u'domain-id': None,
        u'environment': None,
        u'environment-id': None,
        u'locations': None,
        u'location-ids': None,
        u'kickstart-repository-id': None,
        u'lifecycle-environment': None,
        u'lifecycle-environment-id': None,
        u'lifecycle-environment-organization-id': None,
        u'medium': None,
        u'medium-id': None,
        u'name': gen_alphanumeric(6),
        u'operatingsystem': None,
        u'operatingsystem-id': None,
        u'organizations': None,
        u'organization-titles': None,
        u'organization-ids': None,
        u'parent': None,
        u'parent-id': None,
        u'partition-table': None,
        u'partition-table-id': None,
        u'puppet-ca-proxy': None,
        u'puppet-ca-proxy-id': None,
        u'puppet-class-ids': None,
        u'puppet-classes': None,
        u'puppet-proxy': None,
        u'puppet-proxy-id': None,
        u'pxe-loader': None,
        u'query-organization': None,
        u'query-organization-id': None,
        u'query-organization-label': None,
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

         --location-ids LOCATION_IDS         REPLACE locations with given ids
                                             Comma separated list of values.
         --locations LOCATION_NAMES          Comma separated list of values.
         --name NAME
         --organization-ids ORGANIZATION_IDS REPLACE organizations with given
                                             ids.
                                             Comma separated list of values.
         --organizations ORGANIZATION_NAMES  Comma separated list of values.

    """
    # Assigning default values for attributes
    args = {
        u'location-ids': None,
        u'locations': None,
        u'name': gen_alphanumeric(6),
        u'organization-ids': None,
        u'organizations': None,
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
def make_tailoringfile(options=None):
    """
   Usage::

        tailoring-file create [OPTIONS]

   Options::

         --location-ids LOCATION_IDS           REPLACE locations with given ids
                                               Comma separated list of values.
                                               Values containing comma should
                                               be double quoted.
         --locations LOCATION_NAMES            Comma separated list of values.
                                               Values containing comma should
                                               be double quoted
         --name NAME                           Tailoring file name
         --organization-ids ORGANIZATION_IDS   REPLACE organizations with given
                                               ids.
                                               Comma separated list of values.
                                               Values containing comma should
                                               be double quoted
         --organizations ORGANIZATION_NAMES    Comma separated list of values.
                                               Values containing comma should
                                               be double quoted
         --original-filename ORIGINAL_FILENAME Original file name of the XML
                                               file
         --scap-file SCAP_FILE                 Tailoring file content
         -h, --help                            print help
    """
    # Assigning default values for attributes
    args = {
        u'scap-file': None,
        u'original-filename': None,
        u'location-ids': None,
        u'locations': None,
        u'name': gen_alphanumeric().lower(),
        u'organization-ids': None,
        u'organizations': None,
    }

    return create_object(TailoringFiles, args, options)


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


@cacheable
def make_virt_who_config(options=None):
    """
    Usage::

        hammer virt-who-config create [OPTIONS]

    Options::

        --blacklist BLACKLIST    Hypervisor blacklist, applicable only when
                                 filtering mode is set to 2.
                                 Wildcards and regular expressions are
                                 supported, multiple records must be
                                 separated by comma.
        --debug DEBUG            Enable debugging output
                                 One of true/false, yes/no, 1/0.
        --filtering-mode MODE    Hypervisor filtering mode
                                 Possible value(s): 'none', 'whitelist',
                                 'blacklist'
        --hypervisor-id HYPERVISOR_ID  Specifies how the hypervisor will be
                                       identified.
                                       Possible value(s): 'hostname', 'uuid',
                                       'hwuuid'
        --hypervisor-password HYPERVISOR_PASSWORD Hypervisor password, required
                                                  for all hypervisor types
                                                  except for libvirt
        --hypervisor-server HYPERVISOR_SERVER     Fully qualified host name or
                                                  IP address of the hypervisor
        --hypervisor-type HYPERVISOR_TYPE         Hypervisor type
                                                  Possible value(s): 'esx',
                                                  'rhevm', 'hyperv', 'xen',
                                                  'libvirt'
        --hypervisor-username HYPERVISOR_USERNAME Account name by which
                                                  virt-who is to connect to the
                                                  hypervisor.
        --interval INTERVAL   Configuration interval in minutes
                              Possible value(s): '60', '120', '240', '480',
                              '720'
        --name NAME           Configuration name
        --no-proxy NO_PROXY   Ignore Proxy. A comma-separated list of hostnames
                              or domains or ip addresses to ignore proxy
                              settings for. Optionally this may be set to * to
                              bypass proxy settings for all hostnames domains
                              or ip addresses.
        --organization ORGANIZATION_NAME          Organization name
        --organization-id ORGANIZATION_ID         organization ID
        --organization-title ORGANIZATION_TITLE   Organization title
        --proxy PROXY         HTTP Proxy that should be used for communication
                              between the server on which virt-who is running
                              and the hypervisors and virtualization managers.
        --satellite-url SATELLITE_URL   Satellite server FQDN
        --whitelist WHITELIST Hypervisor whitelist, applicable only when
                              filtering mode is set to 1.
                              Wildcards and regular expressions are supported,
                              multiple records must be separated by comma.
        -h, --help            print help
    """
    args = {
        u'blacklist': None,
        u'debug': None,
        u'filtering-mode': 'none',
        u'hypervisor-id': 'hostname',
        u'hypervisor-password': None,
        u'hypervisor-server': None,
        u'hypervisor-type': None,
        u'hypervisor-username': None,
        u'interval': '60',
        u'name': gen_alphanumeric(6),
        u'no-proxy': None,
        u'organization': None,
        u'organization-id': None,
        u'organization-title': None,
        u'proxy': None,
        u'satellite-url': settings.server.hostname,
        u'whitelist': None
     }
    return create_object(VirtWhoConfig, args, options)


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


def _setup_org_for_a_rh_repo(options=None):
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

    Note that in most cases you should use ``setup_org_for_a_rh_repo`` instead
    as it's more flexible.

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
        subscription (optional) - subscription name (or use the default one
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
        u'subscription': options.get(
            u'subscription', DEFAULT_SUBSCRIPTION_NAME),
    })
    return {
        u'activationkey-id': activationkey_id,
        u'content-view-id': cv_id,
        u'lifecycle-environment-id': env_id,
        u'organization-id': org_id,
        u'repository-id': rhel_repo['id'],
    }


def setup_org_for_a_rh_repo(options=None, force_manifest_upload=False,
                            force_use_cdn=False):
    """Wrapper above ``_setup_org_for_a_rh_repo`` to use custom downstream repo
    instead of CDN's 'Satellite Capsule' and 'Satellite Tools' if
    ``settings.cdn == 0`` and URL for custom repositories is set in properties.

    :param options: a dict with options to pass to function
        ``_setup_org_for_a_rh_repo``. See its docstring for more details
    :param force_use_cdn: bool flag whether to use CDN even if there's
        downstream repo available and ``settings.cdn == 0``.
    :param force_manifest_upload: bool flag whether to upload a manifest to
        organization even if downstream custom repo is used instead of CDN.
        Useful when test relies on organization with manifest (e.g. uses some
        other RH repo afterwards). Defaults to False.
    :return: a dict with entity ids (see ``_setup_org_for_a_rh_repo`` and
        ``setup_org_for_a_custom_repo``).
    """
    custom_repo_url = None
    if options.get('repository') == REPOS['rhst6']['name']:
        custom_repo_url = settings.sattools_repo['rhel6']
    elif options.get('repository') == REPOS['rhst7']['name']:
        custom_repo_url = settings.sattools_repo['rhel7']
    elif 'Satellite Capsule' in options.get('repository'):
        custom_repo_url = settings.capsule_repo
    if force_use_cdn or settings.cdn or not custom_repo_url:
        return _setup_org_for_a_rh_repo(options)
    else:
        options['url'] = custom_repo_url
        result = setup_org_for_a_custom_repo(options)
        if force_manifest_upload:
            with manifests.clone() as manifest:
                upload_file(manifest.content, manifest.filename)
            try:
                Subscription.upload({
                    u'file': manifest.filename,
                    u'organization-id': result.get('organization-id'),
                })
            except CLIReturnCodeError as err:
                raise CLIFactoryError(
                    u'Failed to upload manifest\n{0}'.format(err.msg))
            # attach the default subscription to activation key
            activationkey_add_subscription_to_repo({
                'activationkey-id': result[u'activationkey-id'],
                'organization-id': result[u'organization-id'],
                'subscription': DEFAULT_SUBSCRIPTION_NAME,
            })
        return result


def configure_env_for_provision(org=None, loc=None):
    """Create and configure org, loc, product, repo, env. Update proxy,
    domain, subnet, compute resource, provision templates and medium with
    previously created entities and create a hostgroup using all mentioned
    entities.

    :param org: Default Organization that should be used in both host
        discovering and host provisioning procedures
    :param loc: Default Location that should be used in both host
        discovering and host provisioning procedures
    :return: List of created entities that can be re-used further in
        provisioning or validation procedure (e.g. hostgroup or subnet)
    """
    # Create new organization and location in case they were not passed
    if org is None:
        org = make_org()
    if loc is None:
        loc = make_location()

    # Get a Library Lifecycle environment and the default CV for the org
    lce = LifecycleEnvironment.info(
        {u'name': u'Library', 'organization-id': org['id']}
    )
    cv = ContentView.info(
        {u'name': u'Default Organization View', u'organization-id': org['id']}
    )

    # Create puppet environment and associate organization and location
    env = make_environment({
        'location-ids': loc['id'],
        'organization-ids': org['id'],
    })

    # Get default capsule and associate location
    puppet_proxy = Proxy.info({'id': Proxy.list({
        u'search': settings.server.hostname
    })[0]['id']})
    Proxy.update({
        'id': puppet_proxy['id'],
        'locations': list(
            set(puppet_proxy.get('locations') or []) | {loc['name']}),
    })

    # Network
    # Search for existing domain or create new otherwise. Associate org,
    # location and dns to it
    _, _, domain_name = settings.server.hostname.partition('.')
    domain = Domain.list({'search': 'name={0}'.format(domain_name)})
    if len(domain) == 1:
        domain = Domain.info({'id': domain[0]['id']})
        Domain.update({
            'name': domain_name,
            'locations': list(
                set(domain.get('locations') or []) | {loc['name']}),
            'organizations': list(
                set(domain.get('organizations') or []) | {org['name']}),
            'dns-id': puppet_proxy['id'],
        })
    else:
        # Create new domain
        domain = make_domain({
            'name': domain_name,
            'location-ids': loc['id'],
            'organization-ids': org['id'],
            'dns-id': puppet_proxy['id'],
        })
    # Search if subnet is defined with given network. If so, just update its
    # relevant fields otherwise create new subnet
    network = settings.vlan_networking.subnet
    subnet = Subnet.list({'search': 'network={0}'.format(network)})
    if len(subnet) >= 1:
        subnet = Subnet.info({'id': subnet[0]['id']})
        Subnet.update({
            'name': subnet['name'],
            'domains': list(
                      set(subnet.get('domains') or []) | {domain['name']}),
            'locations': list(
                set(subnet.get('locations') or []) | {loc['name']}),
            'organizations': list(
                set(subnet.get('organizations') or []) | {org['name']}),
            'dhcp-id': puppet_proxy['id'],
            'dns-id': puppet_proxy['id'],
            'tftp-id': puppet_proxy['id'],
        })
    else:
        # Create new subnet
        subnet = make_subnet({
            'name': gen_string('alpha'),
            'network': network,
            'mask': settings.vlan_networking.netmask,
            'domain-ids': domain['id'],
            'location-ids': loc['id'],
            'organization-ids': org['id'],
            'dhcp-id': puppet_proxy['id'],
            'dns-id': puppet_proxy['id'],
            'tftp-id': puppet_proxy['id'],
        })

    # Get the Partition table entity
    ptable = PartitionTable.info({'name': DEFAULT_PTABLE})

    # Get the OS entity
    os = OperatingSys.list({
        'search': 'name="RedHat" AND major="{0}" OR major="{1}"'.format(
            RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
    })[0]

    # Get proper Provisioning templates and update with OS, Org, Location
    provisioning_template = Template.info({'name': DEFAULT_TEMPLATE})
    pxe_template = Template.info({'name': DEFAULT_PXE_TEMPLATE})
    for template in provisioning_template, pxe_template:
        if os['title'] not in template['operating-systems']:
            Template.update({
                'id': template['id'],
                'locations': list(
                    set(template.get('locations') or []) | {loc['name']}),
                'operatingsystems': list(set(
                    template.get('operating-systems') or []) | {os['title']}),
                'organizations': list(
                    set(template.get('organizations') or []) | {org['name']}),
            })

    # Get the architecture entity
    arch = Architecture.list(
        {'search': 'name={0}'.format(DEFAULT_ARCHITECTURE)})[0]

    os = OperatingSys.info({'id': os['id']})
    # Get the media and update its location
    medium = Medium.list({'search': 'path={0}'.format(settings.rhel7_os)})
    if medium:
        media = Medium.info({'id': medium[0]['id']})
        Medium.update({
            'id': media['id'],
            'operatingsystems': list(
                set(media.get('operating-systems') or []) | {os['title']}),
            'locations': list(
                set(media.get('locations') or []) | {loc['name']}),
            'organizations': list(
                set(media.get('organizations') or []) | {org['name']}),
        })
    else:
        media = make_medium({
            'location-ids': loc['id'],
            'operatingsystem-ids': os['id'],
            'organization-ids': org['id'],
            'path': settings.rhel7_os
        })

    # Update the OS with found arch, ptable, templates and media
    OperatingSys.update({
        'id': os['id'],
        'architectures': list(
            set(os.get('architectures') or []) | {arch['name']}),
        'media': list(
            set(os.get('installation-media') or []) | {media['name']}),
        'partition-tables': list(
            set(os.get('partition-tables') or []) | {ptable['name']}),
    })
    for template in (provisioning_template, pxe_template):
        if '{} ({})'.format(template['name'], template['type']) not in os[
                'templates']:
            OperatingSys.update({
                'id': os['id'],
                'config-templates': list(
                    set(os['templates']) | {template['name']}),
            })

    # Create new hostgroup using proper entities
    hostgroup = make_hostgroup({
        'location-ids': loc['id'],
        'environment-id': env['id'],
        'lifecycle-environment-id': lce['id'],
        'puppet-proxy-id': puppet_proxy['id'],
        'puppet-ca-proxy-id': puppet_proxy['id'],
        'content-view-id': cv['id'],
        'domain-id': domain['id'],
        'subnet-id': subnet['id'],
        'organization-ids': org['id'],
        'architecture-id': arch['id'],
        'partition-table-id': ptable['id'],
        'medium-id': media['id'],
        'operatingsystem-id': os['id'],
        'content-source-id': puppet_proxy['id'],
    })

    return {
        'hostgroup': hostgroup,
        'subnet': subnet,
        'domain': domain,
        'ptable': ptable,
        'os': os
    }


def publish_puppet_module(puppet_modules, repo_url, organization_id=None):
    """Creates puppet repo, sync it via provided url and publish using
    Content View publishing mechanism. It makes puppet class available
    via Puppet Environment created by Content View and returns Content
    View entity.

    :param puppet_modules: List of dictionaries with module 'author'
        and module 'name' fields.
    :param str repo_url: Url of the repo that can be synced using pulp:
        pulp repo or puppet forge.
    :param organization_id: Organization id that is shared between created
        entities.
    :return: Content View entity.
    """
    if not organization_id:
        organization_id = make_org()['id']
    product = make_product({u'organization-id': organization_id})
    repo = make_repository({
        u'product-id': product['id'],
        u'content-type': 'puppet',
        u'url': repo_url,
    })
    # Synchronize repo via provided URL
    Repository.synchronize({'id': repo['id']})
    # Add selected module to Content View
    cv = make_content_view({u'organization-id': organization_id})
    for module in puppet_modules:
        ContentView.puppet_module_add({
            u'author': module['author'],
            u'name': module['name'],
            u'content-view-id': cv['id'],
        })
    # CV publishing will automatically create Environment and
    # Puppet Class entities
    ContentView.publish({u'id': cv['id']})
    return ContentView.info({u'id': cv['id']})


def setup_virtual_machine(
        vm, org_label, rh_repos_id=None, repos_label=None, product_label=None,
        lce=None, activation_key=None, patch_os_release_distro=None,
        install_katello_agent=True):
    """
    Setup a Virtual machine with basic components and tasks.

    :param robottelo.vm.VirtualMachine vm: The Virtual machine to setup.
    :param str org_label: The Organization label.
    :param list rh_repos_id: a list of RH repositories ids to enable.
    :param list repos_label: a list of custom repositories labels to enable.
    :param str product_label: product label if repos_label is applicable.
    :param str lce: Lifecycle environment label if applicable.
    :param str activation_key: Activation key name if applicable.
    :param str patch_os_release_distro: distro name, to patch the VM with os
        version.
    :param bool install_katello_agent: whether to install katello agent.
    """
    if rh_repos_id is None:
        rh_repos_id = []
    if repos_label is None:
        repos_label = []
    vm.install_katello_ca()
    vm.register_contenthost(org_label, activation_key=activation_key, lce=lce)
    if not vm.subscribed:
        raise CLIFactoryError('Virtual machine failed subscription')
    if patch_os_release_distro:
        vm.patch_os_release_version(distro=patch_os_release_distro)
    # Enable RH repositories
    for repo_id in rh_repos_id:
        vm.enable_repo(repo_id, force=True)
    if product_label:
        # Enable custom repositories
        for repo_label in repos_label:
            result = vm.run(
                'yum-config-manager --enable {0}_{1}_{2}'.format(
                    org_label,
                    product_label,
                    repo_label,
                )
            )
            if result.return_code != 0:
                raise CLIFactoryError(
                    'Failed to enable custom repository "{0}"\n{1}'.format(
                        repos_label, result.stderr)
                )
    if install_katello_agent:
        vm.install_katello_agent()


def _get_capsule_vm_distro_repos(distro):
    """Return the right RH repos info for the capsule setup"""
    rh_repos = []
    if distro == DISTRO_RHEL7:
        # Red Hat Enterprise Linux 7 Server
        rh_product_arch = REPOS['rhel7']['arch']
        rh_product_releasever = REPOS['rhel7']['releasever']
        rh_repos.append({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhel7'],
            'repository': REPOS['rhel7']['name'],
            'repository-id': REPOS['rhel7']['id'],
            'releasever': rh_product_releasever,
            'arch': rh_product_arch,
            'cdn': True,
        })
        # Red Hat Software Collections (for 7 Server)
        rh_repos.append({
            'product': PRDS['rhscl'],
            'repository-set': REPOSET['rhscl7'],
            'repository': REPOS['rhscl7']['name'],
            'repository-id': REPOS['rhscl7']['id'],
            'releasever': rh_product_releasever,
            'arch': rh_product_arch,
            'cdn': True,
        })
        # Red Hat Satellite Capsule 6.2 (for RHEL 7 Server)
        rh_repos.append({
            'product': PRDS['rhsc'],
            'repository-set': REPOSET['rhsc7'],
            'repository': REPOS['rhsc7']['name'],
            'repository-id': REPOS['rhsc7']['id'],
            'url': settings.capsule_repo,
            'cdn': bool(settings.cdn or not settings.capsule_repo),
        })
    else:
        raise CLIFactoryError('distro "{}" not supported'.format(distro))

    return rh_product_arch, rh_product_releasever, rh_repos


def add_role_permissions(role_id, resource_permissions):
    """Create role permissions found in resource permissions dict

    :param role_id: The role id
    :param resource_permissions: a dict containing resources with permission
        names and other Filter options

    Usage::

        role = make_role({'organization-id': org['id']})
        resource_permissions = {
            'Katello::ActivationKey': {
                'permissions': [
                    'view_activation_keys',
                    'create_activation_keys',
                    'edit_activation_keys',
                    'destroy_activation_keys'
                ],
                'search': "name ~ {}".format(ak_name_like)
            },
        }
        add_role_permissions(role['id'], resource_permissions)
    """
    available_permissions = Filter.available_permissions()
    # group the available permissions by resource type
    available_rc_permissions = {}
    for permission in available_permissions:
        permission_resource = permission['resource']
        if permission_resource not in available_rc_permissions:
            available_rc_permissions[permission_resource] = []
        available_rc_permissions[permission_resource].append(permission)
    # create only the required role permissions per resource type
    for resource_type, permission_data in resource_permissions.items():
        permission_names = permission_data.get('permissions')
        if permission_names is None:
            raise CLIFactoryError(
                'Permissions not provided for resource: {0}'
                .format(resource_type)
            )
        # ensure  that the required resource type is available
        if resource_type not in available_rc_permissions:
            raise CLIFactoryError(
                'Resource "{0}" not in the list of available resources'
                .format(resource_type)
            )
        available_permission_names = [
            permission['name']
            for permission in available_rc_permissions[resource_type]
            if permission['name'] in permission_names
            ]
        # ensure that all the required permissions are available
        missing_permissions = set(
            permission_names).difference(set(available_permission_names))
        if missing_permissions:
            raise CLIFactoryError(
                'Permissions "{0}" are not available in Resource "{1}"'
                .format(list(missing_permissions), resource_type)
            )
        # Create the current resource type role permissions
        options = {'role-id': role_id}
        options.update(permission_data)
        make_filter(options=options)


def setup_cdn_and_custom_repositories(
        org_id, repos, download_policy='on_demand', synchronize=True):
    """Setup cdn and custom repositories

    :param int org_id: The organization id
    :param list repos: a list of dict repositories options
    :param str download_policy: update the repositories with this download
        policy
    :param bool synchronize: Whether to synchronize the repositories.
    :return: a dict containing the content view and repos info
    """
    custom_product = None
    repos_info = []
    for repo in repos:
        custom_repo_url = repo.get('url')
        cdn = repo.get('cdn', False)
        if not cdn and not custom_repo_url:
            raise CLIFactoryError(u'Custom repository with url not supplied')
        if cdn:
            RepositorySet.enable({
                u'organization-id': org_id,
                u'product': repo['product'],
                u'name': repo['repository-set'],
                u'basearch': repo.get('arch', DEFAULT_ARCHITECTURE),
                u'releasever': repo.get('releasever'),
            })
            repo_info = Repository.info({
                u'organization-id': org_id,
                u'name': repo['repository'],
                u'product': repo['product'],
            })
        else:
            if custom_product is None:
                custom_product = make_product_wait({
                    'organization-id': org_id,
                })
            repo_info = make_repository({
                'product-id': custom_product['id'],
                'organization-id': org_id,
                'url': custom_repo_url,
            })
        if download_policy:
            # Set download policy
            Repository.update({
                'download-policy': download_policy,
                'id': repo_info['id'],
            })
        repos_info.append(repo_info)
    if synchronize:
        # Synchronize the repositories
        for repo_info in repos_info:
            Repository.synchronize({'id': repo_info['id']}, timeout=4800)
    return custom_product, repos_info


def setup_cdn_and_custom_repos_content(
        org_id, lce_id=None, repos=None, upload_manifest=True,
        download_policy='on_demand', rh_subscriptions=None, default_cv=False):
    """Setup cdn and custom repositories, content view and activations key

    :param int org_id: The organization id
    :param int lce_id: the lifecycle environment id
    :param list repos: a list of dict repositories options
    :param bool default_cv: whether to use the Default Organization CV
    :param bool upload_manifest: whether to upload the organization manifest
    :param str download_policy: update the repositories with this download
        policy
    :param list rh_subscriptions: a list of RH subscription to attach to
        activation key
    :return: a dict containing the activation key, content view and repos info
    """
    if lce_id is None and not default_cv:
        raise TypeError(u'lce_id must be specified')
    if repos is None:
        repos = []
    if rh_subscriptions is None:
        rh_subscriptions = []

    if upload_manifest:
        # Upload the organization manifest
        try:
            manifests.upload_manifest_locked(org_id, manifests.clone(),
                                             interface=manifests.INTERFACE_CLI)
        except CLIReturnCodeError as err:
            raise CLIFactoryError(
                u'Failed to upload manifest\n{0}'.format(err.msg))

    custom_product, repos_info = setup_cdn_and_custom_repositories(
        org_id=org_id,
        repos=repos,
        download_policy=download_policy
    )
    if default_cv:
        activation_key = make_activation_key({
            u'organization-id': org_id,
            u'lifecycle-environment': 'Library',
        })
        content_view = ContentView.info({
            u'organization-id': org_id,
            u'name': u'Default Organization View'
        })
    else:
        # Create a content view
        content_view = make_content_view({u'organization-id': org_id})
        # Add repositories to content view
        for repo_info in repos_info:
            ContentView.add_repository({
                u'id': content_view['id'],
                u'organization-id': org_id,
                u'repository-id': repo_info['id'],
            })
        # Publish the content view
        ContentView.publish({u'id': content_view['id']})
        # Get the latest content view version id
        content_view_version = ContentView.info({
            u'id': content_view['id']
         })['versions'][-1]
        # Promote content view version to lifecycle environment
        ContentView.version_promote({
            u'id': content_view_version['id'],
            u'organization-id': org_id,
            u'to-lifecycle-environment-id': lce_id,
        })
        content_view = ContentView.info({u'id': content_view['id']})
        activation_key = make_activation_key({
            u'organization-id': org_id,
            u'lifecycle-environment-id': lce_id,
            u'content-view-id': content_view['id'],
        })
    # Get organization subscriptions
    subscriptions = Subscription.list({
        u'organization-id': org_id},
        per_page=False
    )
    # Add subscriptions to activation-key
    needed_subscription_names = list(rh_subscriptions)
    if custom_product:
        needed_subscription_names.append(custom_product['name'])
    added_subscription_names = []
    for subscription in subscriptions:
        if subscription['name'] in needed_subscription_names:
            ActivationKey.add_subscription({
                u'id': activation_key['id'],
                u'subscription-id': subscription['id'],
                u'quantity': 1,
            })
            added_subscription_names.append(subscription['name'])
            if (len(added_subscription_names)
                    == len(needed_subscription_names)):
                break
    missing_subscription_names = set(
        needed_subscription_names).difference(set(added_subscription_names))
    if missing_subscription_names:
        raise CLIFactoryError(
            u'Missing subscriptions: {0}'.format(missing_subscription_names))

    return dict(
        activation_key=activation_key,
        content_view=content_view,
        product=custom_product,
        repos=repos_info,
    )


def vm_setup_ssh_config(vm, ssh_key_name, host, user=None):
    """Create host entry in vm ssh config and know_hosts files to allow vm
    to access host via ssh without password prompt

    :param robottelo.vm.VirtualMachine vm: Virtual machine instance
    :param str ssh_key_name: The ssh key file name to use to access host,
        the file must already exist in /root/.ssh directory
    :param str host: the hostname to setup that will be accessed from vm
    :param str user: the user that will access the host
    """
    if user is None:
        user = 'root'
    ssh_path = '/root/.ssh'
    ssh_key_file_path = '{0}/{1}'.format(ssh_path, ssh_key_name)
    # setup the config file
    ssh_config_file_path = '{0}/config'.format(ssh_path)
    result = vm.run('touch {0}'.format(ssh_config_file_path))
    if result.return_code != 0:
        raise CLIFactoryError(
            u'Failed to create ssh config file:\n{}'
            .format(result.stderr)
        )
    result = vm.run(
        'echo "\nHost {0}\n\tHostname {0}\n\tUser {1}\n'
        '\tIdentityFile {2}\n" >> {3}'
        .format(host, user, ssh_key_file_path, ssh_config_file_path)
    )
    if result.return_code != 0:
        raise CLIFactoryError(
            u'Failed to write to ssh config file:\n{}'.format(result.stderr))
    # add host entry to ssh known_hosts
    result = vm.run(
        'ssh-keyscan {0} >> {1}/known_hosts'.format(host, ssh_path))
    if result.return_code != 0:
        raise CLIFactoryError(
            u'Failed to put hostname in ssh known_hosts files:\n{}'
            .format(result.stderr)
        )


def vm_upload_ssh_key(vm, source_key_path, destination_key_name):
    """Copy ssh key to virtual machine ssh path and ensure proper permission is
    set

    :param robottelo.vm.VirtualMachine vm: Virtual machine instance
    :param source_key_path: The ssh key file path to copy to vm
    :param destination_key_name: The ssh key file name when copied to vm
    """
    destination_key_path = '/root/.ssh/{0}'.format(destination_key_name)
    upload_file(
        local_file=source_key_path,
        remote_file=destination_key_path,
        hostname=vm.ip_addr
    )
    result = vm.run('chmod 600 {0}'.format(destination_key_path))
    if result.return_code != 0:
        raise CLIFactoryError(
            u'Failed to chmod ssh key file:\n{}'.format(result.stderr))


def virt_who_hypervisor_config(
        config_id, virt_who_vm, org_id=None, lce_id=None,
        hypervisor_hostname=None, configure_ssh=False, hypervisor_user=None,
        subscription_name=None, exec_one_shot=False, upload_manifest=True):
    """
    Configure virtual machine as hypervisor virt-who service

    :param int config_id: virt-who config id
    :param robottelo.vm.VirtualMachine virt_who_vm: the Virtual machine
        instance to use for configuration
    :param int org_id: the organization id
    :param int lce_id: the lifecycle environment id to use
    :param str hypervisor_hostname: the hypervisor hostname
    :param str hypervisor_user: hypervisor user that connect with the ssh key
    :param bool configure_ssh: whether to configure the ssh key to allow this
        virtual machine to connect to hypervisor
    :param str subscription_name: the subscription name to assign to virt-who
        hypervisor guests
    :param bool exec_one_shot: whether to run the virt-who one-shot command
        after startup
    :param bool upload_manifest: whether to upload the organization manifest
    """
    if org_id is None:
        org = make_org()
    else:
        org = Org.info({'id': org_id})

    if lce_id is None:
        lce = make_lifecycle_environment({'organization-id': org['id']})
    else:
        lce = LifecycleEnvironment.info({
            'id': lce_id,
            'organization-id': org['id']
        })
    rh_product_arch = REPOS['rhel7']['arch']
    rh_product_releasever = REPOS['rhel7']['releasever']
    repos = [
        # Red Hat Enterprise Linux 7
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhel7'],
            'repository': REPOS['rhel7']['name'],
            'repository-id': REPOS['rhel7']['id'],
            'releasever': rh_product_releasever,
            'arch': rh_product_arch,
            'cdn': True,
        },
        # Red Hat Satellite Tools
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'repository-id': REPOS['rhst7']['id'],
            'url': settings.sattools_repo['rhel7'],
            'cdn': bool(settings.cdn or not settings.sattools_repo['rhel7']),
        },
    ]
    content_setup_data = setup_cdn_and_custom_repos_content(
        org['id'],
        lce['id'],
        repos,
        upload_manifest=upload_manifest,
        rh_subscriptions=[DEFAULT_SUBSCRIPTION_NAME],
    )
    activation_key = content_setup_data['activation_key']
    content_view = content_setup_data['content_view']
    setup_virtual_machine(
        virt_who_vm,
        org['label'],
        activation_key=activation_key['name'],
        patch_os_release_distro=DISTRO_RHEL7,
        rh_repos_id=[
            repo['repository-id']
            for repo in repos if repo['cdn']
        ],
        install_katello_agent=False,
    )
    if hypervisor_hostname and configure_ssh:
        # configure ssh access of hypervisor from virt_who_vm
        hypervisor_ssh_key_name = 'hypervisor-{0}.key'.format(
            gen_string('alpha').lower())
        # upload the ssh key
        vm_upload_ssh_key(
            virt_who_vm, settings.server.ssh_key, hypervisor_ssh_key_name)
        # setup the ssh config and known_hosts files
        vm_setup_ssh_config(virt_who_vm, hypervisor_ssh_key_name,
                            hypervisor_hostname, user=hypervisor_user)

    # upload the virt-who config deployment script
    _, temp_virt_who_deploy_file_path = mkstemp(
        suffix='-virt_who_deploy-{0}'.format(config_id))
    VirtWhoConfig.fetch({
        'id': config_id,
        'output': temp_virt_who_deploy_file_path
    })
    download_file(
        remote_file=temp_virt_who_deploy_file_path,
        local_file=temp_virt_who_deploy_file_path,
        hostname=settings.server.hostname
    )
    upload_file(
        local_file=temp_virt_who_deploy_file_path,
        remote_file=temp_virt_who_deploy_file_path,
        hostname=virt_who_vm.ip_addr
    )
    # ensure the virt-who config deploy script is executable
    result = virt_who_vm.run('chmod +x {0}'.format(
        temp_virt_who_deploy_file_path))
    if result.return_code != 0:
        raise CLIFactoryError(
            u'Failed to set deployment script as executable:\n{}'
            .format(result.stderr)
        )
    # execute the deployment script
    result = virt_who_vm.run('{0}'.format(temp_virt_who_deploy_file_path))
    if result.return_code != 0:
        raise CLIFactoryError(
            u'Deployment script failure:\n{}'.format(result.stderr))
    # after this step, we should have virt-who service installed and started
    if exec_one_shot:
        # usually to be sure that the virt-who generated the report we need
        # to force a one shot report, for this we have to stop the virt-who
        # service
        result = virt_who_vm.run('service virt-who stop')
        if result.return_code != 0:
            raise CLIFactoryError(
                u'Failed to stop the virt-who service:\n{}'
                .format(result.stderr)
            )
        result = virt_who_vm.run('virt-who --one-shot', timeout=900)
        if result.return_code != 0:
            raise CLIFactoryError(
                u'Failed when executing virt-who --one-shot:\n{}'
                .format(result.stderr)
            )
        result = virt_who_vm.run('service virt-who start')
        if result.return_code != 0:
            raise CLIFactoryError(
                u'Failed to start the virt-who service:\n{}'
                .format(result.stderr)
            )
    # after this step the hypervisor as a content host should be created
    # do not confuse virt-who host with hypervisor host as they can be
    # diffrent hosts and as per this setup we have only registered the virt-who
    # host, the hypervisor host should registered after virt-who send the
    # first report when started or with one shot command
    # the virt-who hypervisor will be registered to satellite with host name
    # like "virt-who-{hypervisor_hostname}-{organization_id}"
    virt_who_hypervisor_hostname = (
        'virt-who-{0}-{1}'.format(hypervisor_hostname, org['id']))
    # find the registered virt-who hypervisor host
    org_hosts = Host.list({
        'organization-id': org['id'],
        'search': 'name={0}'.format(virt_who_hypervisor_hostname)
    })
    # Note: if one shot command was executed the report is immediately
    # generated, and the server must have already registered the virt-who
    # hypervisor host
    if not org_hosts and not exec_one_shot:
        # we have to wait until the first report was sent.
        # the report is generated after the virt-who service startup, but some
        # small delay can occur.
        max_time = time.time() + 60
        while time.time() <= max_time:
            time.sleep(5)
            org_hosts = Host.list({
                'organization-id': org['id'],
                'search': 'name={0}'.format(virt_who_hypervisor_hostname)
            })
            if org_hosts:
                break

    if len(org_hosts) == 0:
        raise CLIFactoryError(
            u'Failed to find hypervisor host:\n{}'.format(result.stderr))
    virt_who_hypervisor_host = org_hosts[0]
    subscription_id = None
    if hypervisor_hostname and subscription_name:
        subscriptions = Subscription.list({
            u'organization-id': org_id},
            per_page=False
        )
        for subscription in subscriptions:
            if subscription['name'] == subscription_name:
                subscription_id = subscription['id']
                Host.subscription_attach({
                    'host': virt_who_hypervisor_hostname,
                    'subscription-id': subscription_id
                })
                break
    return {
        'subscription_id': subscription_id,
        'subscription_name': subscription_name,
        'activation_key_id': activation_key['id'],
        'organization_id': org['id'],
        'content_view_id': content_view['id'],
        'lifecycle_environment_id': lce['id'],
        'virt_who_hypervisor_host': virt_who_hypervisor_host,
    }
