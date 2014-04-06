# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Factory object creation for all CLI methods
"""

import datetime
import logging
import os
import random

from os import chmod
from robottelo.cli.architecture import Architecture
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.domain import Domain
from robottelo.cli.environment import Environment
from robottelo.cli.gpgkey import GPGKey
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.medium import Medium
from robottelo.cli.model import Model
from robottelo.cli.org import Org
from robottelo.cli.partitiontable import PartitionTable
from robottelo.cli.product import Product
from robottelo.cli.proxy import Proxy
from robottelo.cli.repository import Repository
from robottelo.cli.subnet import Subnet
from robottelo.cli.syncplan import SyncPlan
from robottelo.cli.systemgroup import SystemGroup
from robottelo.cli.template import Template
from robottelo.cli.user import User
from robottelo.cli.operatingsys import OperatingSys
from robottelo.common import ssh
from robottelo.common.constants import (FOREMAN_PROVIDERS, OPERATING_SYSTEMS,
                                        SYNC_INTERVAL, TEMPLATE_TYPES)
from robottelo.common.helpers import (generate_ipaddr, generate_name,
                                      generate_string, sleep_for_seconds,
                                      update_dictionary)
from tempfile import mkstemp

logger = logging.getLogger("robottelo")


def create_object(cli_object, args, organization_id=None):
    """
    Creates <object> with dictionary of arguments.

    @param cli_object: A valid CLI object.
    @param args: A python dictionary containing all valid
    attributes for creating a new object.
    @param organization_id: A Katello organization id
    @raise Exception: Raise an exception if object cannot be
    created.

    @rtype: dict
    @return: A dictionary representing the newly created resource.
    """

    result = cli_object.create(args, organization_id)
    # Some methods require a bit of waiting
    sleep_for_seconds(5)

    # If the object is not created, raise exception, stop the show.
    if result.return_code != 0:
        logger.debug(result.stderr)  # Show why creation failed.
        raise Exception(
            'Failed to create %s with %r data.' % (cli_object.__name__, args))

    # Sometimes we get a list with a dictionary and not
    # a dictionary.
    if type(result.stdout) is list and len(result.stdout) > 0:
        result.stdout = result.stdout[0]

    return result.stdout


def make_architecture(options=None):
    """
    Usage:
        hammer architecture create [OPTIONS]

    Options:
        --name NAME
        --operatingsystem-ids OPERATINGSYSTEM_IDS Operatingsystem ID’s
                                      Comma separated list of values.
    """

    args = {
        'name': generate_name(),
        'operatingsystem-ids': None,
    }

    # Override default dictionary with updated one
    args = update_dictionary(args, options)
    args.update(create_object(Architecture, args))

    return args


def make_gpg_key(options=None):
    """
    Usage:
        hammer gpg create [OPTIONS]

    Options:
        --organization-id ORGANIZATION_ID organization identifier
        --name NAME                   identifier of the GPG Key
        --key GPG_KEY_FILE            GPG Key file
        -h, --help                    print help
    """

    # Organization ID is a required field.
    if not options or not options.get('organization-id', None):
        raise Exception("Please provide a valid ORG ID.")

    # Create a fake gpg key file if none was provided
    if not options.get('key', None):
        (file_handle, key_filename) = mkstemp(text=True)
        os.chmod(key_filename, 0700)
        with open(key_filename, "w") as gpg_key_file:
            gpg_key_file.write(generate_name(minimum=20, maximum=50))
    else:
        # If the key is provided get its local path and remove it from options
        # to not override the remote path
        key_filename = options.pop('key')

    args = {
        'name': generate_name(),
        'key': "/tmp/%s" % generate_name(),
        'organization-id': None,
    }

    # Upload file to server
    ssh.upload_file(local_file=key_filename, remote_file=args['key'])

    args = update_dictionary(args, options)

    # gpg create returns a dict inside a list
    new_obj = create_object(GPGKey, args)
    args.update(new_obj)

    return args


def make_model(options=None):
    """
    Usage:
        hammer model create [OPTIONS]

    Options:
        --name NAME
        --info INFO
        --vendor-class VENDOR_CLASS
        --hardware-model HARDWARE_MODEL
    """

    args = {
        'name': generate_name(),
        'info': None,
        'vendor-class': None,
        'hardware-model': None,
    }

    # Override default dictionary with updated one
    args = update_dictionary(args, options)
    args.update(create_object(Model, args))

    return args


def make_partition_table(options=None):
    """
    Usage:
        hammer partition_table update [OPTIONS]

    Options:
        --file LAYOUT                 Path to a file that contains
                                      the partition layout
        --os-family OS_FAMILY
        --id ID                       resource id
        --name NAME                   resource name
        --new-name NEW_NAME           new name for the resource
        -h, --help                    print help
    [root@qe-blade-04 ~]# hammer partition_table create --help
    Usage:
        hammer partition_table create [OPTIONS]

    Options:
        --file LAYOUT                 Path to a file that contains
                                      the partition layout
        --name NAME
        --os-family OS_FAMILY
    """
    if options is None:
        options = {}
    (file_handle, layout) = mkstemp(text=True)
    os.chmod(layout, 0700)
    with open(layout, "w") as ptable:
        ptable.write(options.get('content', 'default ptable content'))

    args = {
        'name': generate_name(),
        'file': "/tmp/%s" % generate_name(),
        'os-family': random.choice(OPERATING_SYSTEMS)
    }

    # Upload file to server
    ssh.upload_file(local_file=layout, remote_file=args['file'])

    args = update_dictionary(args, options)
    args.update(create_object(PartitionTable, args))

    return args


def make_product(options=None):
    """
    Usage:
        hammer product create [OPTIONS]

    Options:
        --description DESCRIPTION     Product description
        --gpg-key-id GPG_KEY_ID       Identifier of the GPG key
        --label LABEL
        --name NAME
        --organization-id ORGANIZATION_ID ID of the organization
        --sync-plan-id SYNC_PLAN_ID   Plan numeric identifier
        -h, --help                    print help
    """

    # Organization ID is a required field.
    if not options or not options.get('organization-id', None):
        raise Exception("Please provide a valid ORG ID.")

    args = {
        'name': generate_string('alpha', 20),
        'label': generate_string('alpha', 20),
        'description': generate_string('alpha', 20),
        'organization-id': None,
        'gpg-key-id': None,
        'sync-plan-id': None,
    }

    args = update_dictionary(args, options)
    args.update(create_object(Product, args))

    return args


def make_proxy(options=None):
    """
    Usage:
        hammer proxy create [OPTIONS]

    Options:
        --name NAME
        --url URL
    """

    args = {
        'name': generate_name(),
        'url': 'http://%s:%s' % (generate_string('alpha', 6),
                                 generate_string('numeric', 4)),
    }

    args = update_dictionary(args, options)
    args.update(create_object(Proxy, args))

    return args


def make_repository(options=None):
    """
    Usage:
        hammer repository create [OPTIONS]

    Options:
        --content-type CONTENT_TYPE   type of repo (either 'yum' or 'puppet',
                                      defaults to 'yum')
        --enabled ENABLED             flag that enables/disables the repository
        --url FEED_URL               repository source url
        --gpg-key-name GPG_KEY_NAME   name of a gpg key that will be assigned
                                      to the new repository
        --label LABEL
        --name NAME
        --product-id PRODUCT_ID       Product the repository belongs to
        --publish-via-http ENABLE     Publish Via HTTP
                                      One of true/false, yes/no, 1/0.
    """

    # Product ID is a required field.
    if not options or not options.get('product-id', None):
        raise Exception("Please provide a valid Product ID.")

    args = {
        'name': generate_string('alpha', 15),
        'label': None,
        'content-type': u'yum',
        'product-id': None,
        'publish-via-http': u'true',
        'url': u'http://omaciel.fedorapeople.org/fakerepo01/',
        'gpg-key-name': None,
    }

    args = update_dictionary(args, options)
    args.update(create_object(Repository, args))

    return args


def make_subnet(options=None):
    """
    Usage:
        hammer subnet create [OPTIONS]

    Options:
        --name NAME                   Subnet name
        --network NETWORK             Subnet network
        --mask MASK                   Netmask for this subnet
        --gateway GATEWAY             Primary DNS for this subnet
        --dns-primary DNS_PRIMARY     Primary DNS for this subnet
        --dns-secondary DNS_SECONDARY Secondary DNS for this subnet
        --from FROM                   Starting IP Address for IP auto
                                      suggestion
        --to TO                       Ending IP Address for IP auto suggestion
        --vlanid VLANID               VLAN ID for this subnet
        --domain-ids DOMAIN_IDS       Domains in which this subnet is part
                                      Comma separated list of values.
        --dhcp-id DHCP_ID             DHCP Proxy to use within this subnet
        --tftp-id TFTP_ID             TFTP Proxy to use within this subnet
        --dns-id DNS_ID               DNS Proxy to use within this subnet
    """

    args = {
        'name': generate_name(8, 8),
        'network': generate_ipaddr(ip3=True),
        'mask': u'255.255.255.0',
        'gateway': None,
        'dns-primary': None,
        'dns-secondary': None,
        'from': None,
        'to': None,
        'vlanid': None,
        'domain-ids': None,
        'dhcp-id': None,
        'tftp-id': None,
        'dns-id': None,
    }

    args = update_dictionary(args, options)
    args.update(create_object(Subnet, args))

    return args


def make_sync_plan(options=None):
    """
    Usage:
        hammer sync-plan create [OPTIONS]

    Options:
        --description DESCRIPTION     sync plan description
        --interval INTERVAL           how often synchronization should run
                                      One of ''none',', ''hourly',',
                                      ''daily',', ''weekly''
                                      Default: "none"
        --name NAME                   sync plan name
        --organization-id ORGANIZATION_ID Filter products by organization
                                      name or label
        --sync-date SYNC_DATE         start date and time of the
                                      synchronization Date and time
                                      in YYYY-MM-DD HH:MM:SS or ISO 8601 format
    """

    # Organization ID is a required field.
    if not options or not options.get('organization-id', None):
        raise Exception("Please provide a valid ORG ID.")

    args = {
        'name': generate_string('alpha', 20),
        'description': generate_string('alpha', 20),
        'organization-id': None,
        'sync-date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'interval': random.choice(SYNC_INTERVAL.values()),
    }

    args = update_dictionary(args, options)
    args.update(create_object(SyncPlan, args, args['organization-id']))

    return args


def make_system_group(options=None):
    """
    Usage:
        hammer systemgroup create [OPTIONS]

    Options:
        --description DESCRIPTION
        --max-systems MAX_SYSTEMS      Maximum number of systems in the group
        --name NAME                    System group name
        --organization-id ORGANIZATION_ID organization identifier
         --system-ids SYSTEM_IDS       List of system uuids to be in the group
                                       Comma separated list of values.
    """

    # Organization ID is required
    if not options or not options.get('organization-id', None):
        raise Exception("Please provide a valid ORGANIZATION_ID.")

    # Assigning default values for attributes
    args = {
        'description': None,
        'max-systems': None,
        'name': generate_string('alpha', 15),
        'organization-id': None,
        'system-ids': None,
    }

    args = update_dictionary(args, options)
    args.update(create_object(SystemGroup, args))

    return args


def make_user(options=None):
    """
    Usage:
        hammer user create [OPTIONS]

    Options:
        --login LOGIN
        --firstname FIRSTNAME
        --lastname LASTNAME
        --mail MAIL
        --admin ADMIN                 Is an admin account?
        --password PASSWORD
        --auth-source-id AUTH_SOURCE_ID
    """

    login = generate_name(6)

    # Assigning default values for attributes
    args = {
        'login': login,
        'firstname': generate_name(),
        'lastname': generate_name(),
        'mail': "%s@example.com" % login,
        'admin': None,
        'password': generate_name(),
        'auth-source-id': 1,
    }

    args = update_dictionary(args, options)
    args.update(create_object(User, args))

    return args


def make_compute_resource(options=None):
    """
    Usage:
        hammer compute_resource create [OPTIONS]

    Options:
        --name NAME
        --provider PROVIDER           Providers include Libvirt, Ovirt, EC2,
            Vmware, Openstack, Rackspace, GCE
        --url URL                     URL for Libvirt, Ovirt, and Openstack
        --description DESCRIPTION
        --user USER                   Username for Ovirt, EC2, Vmware,
            Openstack. Access Key for EC2.
        --password PASSWORD           Password for Ovirt, EC2, Vmware,
            Openstack. Secret key for EC2
        --uuid UUID                   for Ovirt, Vmware Datacenter
        --region REGION               for EC2 only
        --tenant TENANT               for Openstack only
        --server SERVER               for Vmware
        -h, --help                    print help
    """
    args = {
        'name': generate_name(8, 8),
        'provider': None,
        'url': None,
        'description': None,
        'user': None,
        'password': None,
        'uuid': None,
        'region': None,
        'tenant': None,
        'server': None
    }

    args = update_dictionary(args, options)
    if args['provider'] is None:
        options['provider'] = FOREMAN_PROVIDERS['libvirt']
        if args['url'] is None:
            options['url'] = "qemu+tcp://localhost:16509/system"
    args.update(create_object(ComputeResource, args))

    return args


def make_org(options=None):
    """
    Usage:
        hammer organization create [OPTIONS]

    Options:
        --name NAME                   name
        --label LABEL                 unique label
        --description DESCRIPTION     description
    """

    # Assigning default values for attributes
    args = {
        'name': generate_name(6),
        'label': None,
        'description': None,
    }

    args = update_dictionary(args, options)
    args.update(create_object(Org, args))

    return args


def make_os(options=None):
    """
        Creates the operating system
        """
    # Assigning default values for attributes
    args = {
        'name': generate_name(6),
        'major': random.randint(0, 10),
        'minor': random.randint(0, 10),
    }

    args = update_dictionary(args, options)
    args.update(create_object(OperatingSys, args))

    return args


def make_domain(options=None):
    """
    Usage:
        hammer domain create [OPTIONS]

    Options:
        --name NAME                   The full DNS Domain name
        --dns-id DNS_ID               DNS Proxy to use within this domain
        --description DESC            Full name describing the domain
    """
    # Assigning default values for attributes
    args = {
        'name': generate_name(6),
        'dns-id': None,
        'description': None,
    }

    args = update_dictionary(args, options)
    args.update(create_object(Domain, args))

    return args


def make_hostgroup(options=None):
    """
    Usage:
    hammer hostgroup create [OPTIONS]

    Options:
        --name NAME
        --parent-id PARENT_ID
        --environment-id ENVIRONMENT_ID
        --operatingsystem-id OPERATINGSYSTEM_ID
        --architecture-id ARCHITECTURE_ID
        --medium-id MEDIUM_ID
        --ptable-id PTABLE_ID
        --puppet-ca-proxy-id PUPPET_CA_PROXY_ID
        --subnet-id SUBNET_ID
        --domain-id DOMAIN_ID
        --puppet-proxy-id PUPPET_PROXY_ID

    """
    # Assigning default values for attributes
    args = {
        'name': generate_name(6),
        'parent-id': None,
        'environment-id': None,
        'operatingsystem-id': None,
        'architecture-id': None,
        'medium-id': None,
        'ptable-id': None,
        'puppet-ca-proxy-id': None,
        'subnet-id': None,
        'domain-id': None,
        'puppet-proxy-id': None,
    }
    args = update_dictionary(args, options)
    args.update(create_object(HostGroup, args))

    return args


def make_medium(options=None):
    """
    Usage:
    hammer medium create [OPTIONS]

    Options:
    --name NAME                Name of media
    --path PATH                The path to the medium, can be a URL or a valid
                               NFS server (exclusive of the architecture)
                               for example http://mirror.centos.org/centos/
                               $version/os/$arch where $arch will be
                               substituted for the host’s actual OS
                               architecture and $version, $major and $minor
                               will be substituted for the version of the
                               operating system.
                               Solaris and Debian media may also use $release.
    --os-family OS_FAMILY      The family that the operating system belongs to.
                               Available families:
                               Archlinux
                               Debian
                               Gentoo
                               Redhat
                               Solaris
                               Suse
                               Windows
    --operatingsystem-ids OPERATINGSYSTEM_IDS Comma separated list of values.
    --operatingsystem-ids OSIDS   os ids
                                  Comma separated list of values.

    """
    # Assigning default values for attributes
    args = {
        'name': generate_name(6),
        'path': 'http://%s' % (generate_string('alpha', 6)),
        'os-family': None,
        'operatingsystem-ids': None,
    }

    args = update_dictionary(args, options)
    args.update(create_object(Medium, args))

    return args


def make_environment(options=None):
    """
    Usage:
    hammer environment create [OPTIONS]

    Options:
    --name NAME
    """
    # Assigning default values for attributes
    args = {
        'name': generate_name(6),
    }

    args = update_dictionary(args, options)
    args.update(create_object(Environment, args))

    return args


def make_lifecycle_environment(options=None):
    """
    Usage:
    hammer lifecycle-environment create [OPTIONS]

    Options:
        --organization-id ORGANIZATION_ID name of organization
        --name NAME                   name of the environment
        --description DESCRIPTION     description of the environment
        --prior PRIOR                 Name of an environment that is prior to
    the new environment in the chain. It has to be either ‘Library’ or an
    environment at the end of a chain.


    """

    # Organization ID is required
    if not options or not options.get('organization-id', None):
        raise Exception("Please provide a valid ORG ID.")
    if not options.get('prior', None):
        options['prior'] = 'Library'

    # Assigning default values for attributes
    args = {
        'organization-id': None,
        'name': generate_name(6),
        'description': None,
        'prior': None,
    }

    args = update_dictionary(args, options)
    args.update(create_object(LifecycleEnvironment, args))

    return args


def make_template(options=None):
    """
    Usage:
    hammer template create [OPTIONS]

    Options:
    --file TEMPLATE             Path to a file that contains the template
    --type TYPE                 Template type. Eg. snippet, script, provision
    --name NAME                 template name
    --audit-comment AUDIT_COMMENT
    --operatingsystem-ids OPERATINGSYSTEM_IDS
                                Array of operating systems ID
                                to associate the template with
                                Comma separated list of values.

    """
    # Assigning default values for attribute
    args = {
        'file': "/tmp/%s" % generate_name(),
        'type': random.choice(TEMPLATE_TYPES),
        'name': generate_name(6),
        'audit-comment': None,
        'operatingsystem-ids': None,
        }

    # Write content to file or random text
    if options is not None and 'content' in options.keys():
        content = options.pop('content')
    else:
        content = generate_name()

    # Special handling for template factory
    (file_handle, layout) = mkstemp(text=True)
    chmod(layout, 0700)
    with open(layout, "w") as ptable:
        ptable.write(content)
    # Upload file to server
    ssh.upload_file(local_file=layout, remote_file=args['file'])
    # End - Special handling for template factory

    args = update_dictionary(args, options)
    args.update(create_object(Template, args))

    return args
