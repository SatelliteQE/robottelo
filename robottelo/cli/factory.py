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
    gen_alphanumeric, gen_integer, gen_ipaddr,
    gen_mac, gen_netmask, gen_string
)
from os import chmod
from robottelo import manifests, ssh
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.architecture import Architecture
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.contenthost import ContentHost
from robottelo.cli.contentview import ContentView
from robottelo.cli.docker import DockerContainer
from robottelo.cli.domain import Domain
from robottelo.cli.environment import Environment
from robottelo.cli.gpgkey import GPGKey
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.location import Location
from robottelo.cli.medium import Medium
from robottelo.cli.model import Model
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.org import Org
from robottelo.cli.partitiontable import PartitionTable
from robottelo.cli.product import Product
from robottelo.cli.proxy import Proxy, SSHTunnelError, default_url_on_new_port
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.role import Role
from robottelo.cli.subnet import Subnet
from robottelo.cli.subscription import Subscription
from robottelo.cli.syncplan import SyncPlan
from robottelo.cli.template import Template
from robottelo.cli.user import User
from robottelo.constants import (
    DEFAULT_SUBSCRIPTION_NAME,
    FAKE_1_YUM_REPO,
    FOREMAN_PROVIDERS,
    OPERATING_SYSTEMS,
    SYNC_INTERVAL,
    TEMPLATE_TYPES,
)
from robottelo.decorators import cacheable
from robottelo.helpers import update_dictionary
from robottelo.ssh import upload_file
from tempfile import mkstemp

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
    update_dictionary(options, values)
    try:
        result = cli_object.create(options)
    except CLIReturnCodeError as err:
        # If the object is not created, raise exception, stop the show.
        raise CLIFactoryError(
            'Failed to create {0} with data:\n{1}\n{2}'.format(
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
        --max-content-hosts MAX_CONTENT_HOSTS maximum number of registered
                                              content hosts
        --name NAME                   name
        --organization ORGANIZATION_NAME Organization name to search by
        --organization-id ORGANIZATION_ID
        --organization-label ORGANIZATION_LABEL Organization label to search by
        --unlimited-content-hosts UNLIMITED_CONTENT_HOSTS can the activation
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
        u'max-content-hosts': None,
        u'name': gen_alphanumeric(),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'unlimited-content-hosts': 'true',
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
    # Organization ID is a required field.
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
        os.chmod(key_filename, 0700)
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

        hammer partition-table update [OPTIONS]

    Options::

        --file LAYOUT         Path to a file that contains the partition layout
        --id ID
        --name NAME           Partition table name
        --new-name NEW_NAME
        --os-family OS_FAMILY
        -h, --help            print help

    Usage::

        hammer partition-table create [OPTIONS]

    Options::

        --file LAYOUT         Path to a file that contains the partition layout
        --name NAME
        --os-family OS_FAMILY
    """
    if options is None:
        options = {}
    (_, layout) = mkstemp(text=True)
    os.chmod(layout, 0700)
    with open(layout, 'w') as ptable:
        ptable.write(options.get('content', 'default ptable content'))

    args = {
        u'file': '/tmp/{0}'.format(gen_alphanumeric()),
        u'name': gen_alphanumeric(),
        u'os-family': random.choice(OPERATING_SYSTEMS)
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
        newport = random.randint(9191, 49090)
        try:
            with default_url_on_new_port(9090, newport) as url:
                args['url'] = url
                return create_object(Proxy, args, options)
        except SSHTunnelError as err:
            raise CLIFactoryError(
                'Failed to create ssh tunnel: {0}'.format(err))

    return create_object(Proxy, args, options)


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
                                                'puppet' or 'docker', defaults
                                                to 'yum')
        --docker-upstream-name DOCKER_UPSTREAM_NAME name of the upstream docker
                                                repository
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
    """
    Usage::

        hammer content-host create [OPTIONS]

    Options::

        --content-view CONTENT_VIEW_NAME                    Content view name
        --content-view-id CONTENT_VIEW_ID                   content view
                                                            numeric identifier
        --description DESCRIPTION                           Description of the
                                                            content host
        --guest-ids GUEST_IDS                               IDs of the virtual
                                                            guests running on
                                                            this content host
                                                            Comma separated
                                                            list of values.
        --host-collection-ids HOST_COLLECTION_IDS           Specify the host
                                                            collections as an
                                                            array
                                                            Comma separated
                                                            list of values.
        --last-checkin LAST_CHECKIN                         Last check-in time
                                                            of this content
                                                            host
        --lifecycle-environment LIFECYCLE_ENVIRONMENT_NAME  Name to search by
        --lifecycle-environment-id LIFECYCLE_ENVIRONMENT_ID
        --location LOCATION                                 Physical location
                                                            of the content host
        --name NAME                                         Name of the content
                                                            host
        --organization ORGANIZATION_NAME                    Organization name
                                                            to search by
        --organization-id ORGANIZATION_ID                   organization ID
        --organization-label ORGANIZATION_LABEL             Organization label
                                                            to search by
        --release-ver RELEASE_VER                           Release version of
                                                            the content host
        --service-level SERVICE_LEVEL                       A service level for
                                                            auto-healing
                                                            process, e.g.
                                                            SELF-SUPPORT
        -h, --help                                          print help

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
        u'description': None,
        u'guest-ids': None,
        u'host-collection-ids': None,
        u'last-checkin': None,
        u'lifecycle-environment': None,
        u'lifecycle-environment-id': None,
        u'location': None,
        u'name': gen_string('alpha', 20),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'release-ver': None,
        u'service-level': None,
    }

    return create_object(ContentHost, args, options)


@cacheable
def make_host(options=None):
    """
    Usage::

        hammer host create [OPTIONS]

    Options::

        --architecture ARCHITECTURE_NAME Architecture name
        --architecture-id ARCHITECTURE_ID
        --ask-root-password ASK_ROOT_PW One of true/false, yes/no, 1/0.
        --build BUILD                 One of true/false, yes/no, 1/0.
                                      Default: 'true'
        --compute-attributes COMPUTE_ATTRS Compute resource attributes.
                                      Comma-separated list of key=value.
        --compute-profile COMPUTE_PROFILE_NAME Name to search by
        --compute-profile-id COMPUTE_PROFILE_ID
        --compute-resource COMPUTE_RESOURCE_NAME Compute resource name
        --compute-resource-id COMPUTE_RESOURCE
        --domain DOMAIN_NAME          Domain name
        --domain-id DOMAIN_ID
        --enabled ENABLED             One of true/false, yes/no, 1/0.
                                      Default: 'true'
        --environment ENVIRONMENT_NAME Environment name
        --environment-id ENVIRONMENT_ID
        --hostgroup HOSTGROUP_NAME    Hostgroup name
        --hostgroup-id HOSTGROUP_ID
        --image-id IMAGE_ID
        --interface INTERFACE         Interface parameters.
                                      Comma-separated list of key=value.
                                      Can be specified multiple times.
        --ip IP                       not required if using a subnet with dhcp
                                      proxy
        --location LOCATION_NAME      Location name
        --location-id LOCATION_ID
        --mac MAC                     not required if its a virtual machine
        --managed MANAGED             One of true/false, yes/no, 1/0.
                                      Default: 'true'
        --medium MEDIUM_NAME          Medium name
        --medium-id MEDIUM_ID
        --model MODEL_NAME            Model name
        --model-id MODEL_ID
        --name NAME
        --operatingsystem OPERATINGSYSTEM_TITLE  Operating system title
        --operatingsystem-id OPERATINGSYSTEM_ID
        --organization ORGANIZATION_NAME Organization name
        --organization-id ORGANIZATION_ID
        --owner-id OWNER_ID
        --parameters PARAMS           Host parameters.
                                    Comma-separated list of key=value.
        --partition-table-id PARTITION_TABLE_ID
        --progress-report-id PROGRESS_REPORT_ID UUID to track orchestration
                                    tasks status, GET
                                    /api/orchestration/:UUID/tasks
        --provision-method METHOD     One of 'build', 'image'
        --ptable PTABLE_NAME          Partition table name
        --ptable-id PTABLE_ID
        --puppet-ca-proxy-id PUPPET_CA_PROXY_ID
        --puppet-proxy-id PUPPET_PROXY_ID
        --puppetclass-ids PUPPETCLASS_IDS Comma separated list of values.
        --realm REALM_NAME            Name to search by
        --realm-id REALM_ID           May be numerical id or realm name
        --root-password ROOT_PW
        --sp-subnet-id SP_SUBNET_ID
        --subnet SUBNET_NAME          Subnet name
        --subnet-id SUBNET_ID
        --volume VOLUME               Volume parameters
                                    Comma-separated list of key=value.
                                    Can be specified multiple times.
    """
    # Check for required options
    required_options = (
        'architecture-id',
        'domain-id',
        'environment-id',
        'medium-id',
        'operatingsystem-id',
        'partition-table-id',
        'puppet-proxy-id',
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
        u'build': None,
        u'compute-attributes': None,
        u'compute-profile': None,
        u'compute-profile-id': None,
        u'compute-resource': None,
        u'compute-resource-id': None,
        u'domain': None,
        u'domain-id': None,
        u'enabled': None,
        u'environment': None,
        u'environment-id': None,
        u'hostgroup': None,
        u'hostgroup-id': None,
        u'image-id': None,
        u'interface': None,
        u'ip': gen_ipaddr(),
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
        u'owner-id': None,
        u'parameters': None,
        u'partition-table-id': None,
        u'progress-report-id': None,
        u'provision-method': None,
        u'ptable': None,
        u'ptable-id': None,
        u'puppet-ca-proxy-id': None,
        u'puppet-proxy-id': None,
        u'puppetclass-ids': None,
        u'realm': None,
        u'realm-id': None,
        u'root-password': gen_string('alpha', 8),
        u'sp-subnet-id': None,
        u'subnet': None,
        u'subnet-id': None,
        u'volume': None,
    }

    return create_object(Host, args, options)


@cacheable
def make_host_collection(options=None):
    """
    Usage::

         host-collection create [OPTIONS]

    Options::

        --content-host-ids CONTENT_HOST_IDS  List of content host uuids to be
                                             in the host collection
        --description DESCRIPTION
        --host-collection-ids HOST_COLLECTION_IDS  Array of content host ids to
                                                   replace the content hosts in
                                                   host collection
                                                   Comma separated list of vals

        --max-content-hosts MAX_CONTENT_HOSTS Maximum number of content hosts
                                              in the host collection
        --name NAME                           Host Collection name
        --organization ORGANIZATION_NAME
        --organization-id ORGANIZATION_ID     organization identifier
        --organization-label ORGANIZATION_LABEL
        --unlimited-content-hosts UNLIMITED_CONTENT_HOSTS Whether or not the
                                                          host collection may
                                                          have unlimited
                                                          content hosts
                                                          One of true/false,
                                                          yes/no, 1/0.
         -h, --help                                       print help

    """
    # Organization ID is required
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORGANIZATION_ID.')

    # Assigning default values for attributes
    args = {
        u'content-host-ids': None,
        u'description': None,
        u'host-collection-ids': None,
        u'max-content-hosts': None,
        u'name': gen_string('alpha', 15),
        u'organization': None,
        u'organization-id': None,
        u'organization-label': None,
        u'unlimited-content-hosts': None,
    }

    return create_object(HostCollection, args, options)


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
        --name NAME                   The full DNS Domain name
        --organization-ids ORGANIZATION_IDS REPLACE organizations with
                                            given ids.
                                            Comma separated list of values.
        -h, --help                          print help

    """
    # Assigning default values for attributes
    args = {
        u'description': None,
        u'dns-id': None,
        u'location-ids': None,
        u'name': gen_alphanumeric().lower(),
        u'organization-ids': None,
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
        --domain DOMAIN_NAME          Domain name
        --domain-id DOMAIN_ID         May be numerical id or domain name
        --environment ENVIRONMENT_NAME Environment name
        --environment-id ENVIRONMENT_ID
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
        --puppet-proxy PUPPET_CA_PROXY_NAME     Name of puppet proxy
        --puppet-proxy-id PUPPET_PROXY_ID
        --puppetclass-ids PUPPETCLASS_IDS  Comma separated list of values.
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
        u'domain': None,
        u'domain-id': None,
        u'environment': None,
        u'environment-id': None,
        u'location-ids': None,
        u'medium': None,
        u'medium-id': None,
        u'name': gen_alphanumeric(6),
        u'operatingsystem': None,
        u'operatingsystem-id': None,
        u'organization-ids': None,
        u'parent-id': None,
        u'ptable': None,
        u'ptable-id': None,
        u'puppet-ca-proxy': None,
        u'puppet-ca-proxy-id': None,
        u'puppet-proxy': None,
        u'puppet-proxy-id': None,
        u'puppetclass-ids': None,
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
        --name NAME             Name of media
        --operatingsystem-ids OPERATINGSYSTEM_IDS REPLACE organizations with
                                                          given ids.
                                                          Comma separated list
                                                          of values.
        --organization-ids ORGANIZATION_IDS               Comma separated list
                                                          of values.
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
        u'name': gen_alphanumeric(6),
        u'operatingsystem-ids': None,
        u'organization-ids': None,
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
    chmod(layout, 0700)
    with open(layout, 'w') as ptable:
        ptable.write(content)
    # Upload file to server
    ssh.upload_file(local_file=layout, remote_file=args['file'])
    # End - Special handling for template factory

    return create_object(Template, args, options)


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
    for subscription in subscriptions:
        if subscription['name'] == options['subscription']:
            if int(subscription['quantity']) == 0:
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
                    'Failed to add subscription to activation key\n{0}'
                    .format(err.msg)
                )


def setup_org_for_a_custom_repo(options=None):
    """
    Sets up Org for the given custom repo by:

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

    Args::

        url - URL to custom repository
        organization-id (optional) - ID of organization to use (or create a new
                                    one if empty)
        lifecycle-environment-id (optional) - ID of lifecycle environment to
                                             use (or create a new one if empty)
        content-view-id (optional) - ID of content view to use (or create a new
                                    one if empty)
        activationkey-id (optional) - ID of activation key (or create a new one
                                    if empty)

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
            'Failed to synchronize repository\n{0}'.format(err.msg))
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
            'Failed to add repository to content view\n{0}'.format(err.msg))
    # Publish a new version of CV
    try:
        ContentView.publish({u'id': cv_id})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            'Failed to publish new version of content view\n{0}'
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
            'Failed to promote version to next environment\n{0}'
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
                'Failed to associate activation-key with CV\n{0}'
                .format(err.msg)
            )
    # Add subscription to activation-key
    activationkey_add_subscription_to_repo({
        u'activationkey-id': activationkey_id,
        u'organization-id': org_id,
        u'subscription': custom_product['name'],
    })


def setup_org_for_a_rh_repo(options=None):
    """
    Sets up Org for the given Red Hat repository by:

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

    Args::

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
    manifest = manifests.clone()
    upload_file(manifest, remote_file=manifest)
    try:
        Subscription.upload({
            u'file': manifest,
            u'organization-id': org_id,
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError('Failed to upload manifest\n{0}'.format(err.msg))
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
            'Failed to enable repository set\n{0}'.format(err.msg))
    # Fetch repository info
    try:
        rhel_repo = Repository.info({
            u'name': options['repository'],
            u'organization-id': org_id,
            u'product': options['product'],
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            'Failed to fetch repository info\n{0}'.format(err.msg))
    # Synchronize the RH repository
    try:
        Repository.synchronize({
            u'name': options['repository'],
            u'organization-id': org_id,
            u'product': options['product'],
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            'Failed to synchronize repository\n{0}'.format(err.msg))
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
            'Failed to add repository to content view\n{0}'.format(err.msg))
    # Publish a new version of CV
    try:
        ContentView.publish({u'id': cv_id})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            'Failed to publish new version of content view\n{0}'
            .format(err.msg)
        )
    # Get the version id
    try:
        cvv = ContentView.info({u'id': cv_id})['versions'][-1]
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            'Failed to fetch content view info\n{0}'.format(err.msg))
    # Promote version1 to next env
    try:
        ContentView.version_promote({
            u'id': cvv['id'],
            u'organization-id': org_id,
            u'to-lifecycle-environment-id': env_id,
        })
    except CLIReturnCodeError as err:
        raise CLIFactoryError(
            'Failed to promote version to next environment\n{0}'
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
                'Failed to associate activation-key with CV\n{0}'
                .format(err.msg)
            )
    # Add subscription to activation-key
    activationkey_add_subscription_to_repo({
        u'organization-id': org_id,
        u'activationkey-id': activationkey_id,
        u'subscription': DEFAULT_SUBSCRIPTION_NAME,
    })
