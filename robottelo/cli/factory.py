#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging

from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.model import Model
from robottelo.cli.proxy import Proxy
from robottelo.cli.subnet import Subnet
from robottelo.cli.user import User
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
    options = options or {}
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
    create_object(ComputeResource, args)

    return args
