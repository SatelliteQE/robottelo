#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging

from robottelo.cli.model import Model
from robottelo.cli.proxy import Proxy
from robottelo.cli.subnet import Subnet
from robottelo.cli.user import User
from robottelo.cli.org import Org
from robottelo.cli.domain import Domain
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.medium import Medium
from robottelo.cli.environment import Environment
from robottelo.common.helpers import generate_ipaddr, generate_name, \
    generate_string


logger = logging.getLogger("robottelo")


def update_dictionary(default, updates):
    """
    Updates default dictionary with elements from
    optional dictionary.

    @param default: A python dictionary containing the minimal
    required arguments to create a CLI object.
    @param updates: A python dictionary containing attributes
    to overwrite on default dictionary.

    @return default: The modified default python dictionary.
    """

    if updates:
        for key in set(default.keys()).intersection(set(updates.keys())):
            default[key] = updates[key]

    return default


def create_object(cli_object, args):
    """
    Creates <object> with dictionary of arguments.

    @param cli_object: A valid CLI object.
    @param args: A python dictionary containing all valid
    attributes for creating a new object.
    @raise Exception: Raise an exception if object cannot be
    created.
    """

    result = cli_object().create(args)

    # If the object is not created, raise exception, stop the show.
    if result.return_code != 0 and not cli_object().exists(
            ('name', args['name'])):

        logger.debug(result.stderr)  # Show why creation failed.
        raise Exception("Failed to create object.")


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
    create_object(Model, args)

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
    create_object(Proxy, args)

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
        'mask': '255.255.255.0',
        'gateway': '',
        'dns-primary': '',
        'dns-secondary': '',
        'from': '',
        'to': '',
        'vlanid': '',
        'domain-ids': '',
        'dhcp-id': '',
        'tftp-id': '',
        'dns-id': '',
    }

    args = update_dictionary(args, options)
    create_object(Subnet, args)

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

    #Assigning default values for attributes
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
    create_object(User, args)

    return args


def make_org(options=None):
    """
    Usage:
        hammer organization create [OPTIONS]

    Options:
        --name NAME
    """
    #Assigning default values for attributes
    args = {
        'name': generate_name(6)
    }

    args = update_dictionary(args, options)
    create_object(Org, args)

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
    #Assigning default values for attributes
    args = {
        'name': generate_name(6),
        'dns-id': '',
        'description': '',
    }

    args = update_dictionary(args, options)
    create_object(Domain, args)

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
    #Assigning default values for attributes
    args = {
        'name': generate_name(6),
        'parent-id': '',
        'environment-id': '',
        'operatingsystem-id': '',
        'architecture-id': '',
        'medium-id': '',
        'ptable-id': '',
        'puppet-ca-proxy-id': '',
        'subnet-id': '',
        'domain-id': '',
        'puppet-proxy-id': '',
    }
    args = update_dictionary(args, options)
    create_object(HostGroup, args)

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
    #Assigning default values for attributes
    args = {
        'name': generate_name(6),
        'path': 'http://%s' % (generate_string('alpha', 6)),
        'os-family': '',
        'operatingsystem-ids': '',
    }

    args = update_dictionary(args, options)
    create_object(Medium, args)

    return args


def make_environment(options=None):
    """
    Usage:
    hammer environment create [OPTIONS]

    Options:
    --name NAME
    """
    #Assigning default values for attributes
    args = {
        'name': generate_name(6),
    }

    args = update_dictionary(args, options)
    create_object(Environment, args)

    return args
