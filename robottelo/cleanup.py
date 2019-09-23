# -*- encoding: utf-8 -*-
"""Cleanup module for different entities"""
import logging

from nailgun import entities
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.proxy import Proxy
from robottelo.decorators import bz_bug_is_open
from robottelo.vm import VirtualMachine

LOGGER = logging.getLogger(__name__)


def capsule_cleanup(proxy_id=None):
    """Deletes the capsule with the given id"""
    if bz_bug_is_open(1398695):
        try:
            Proxy.delete({'id': proxy_id})
        except CLIReturnCodeError as err:
            if err.return_code != 70:
                raise err
    else:
        Proxy.delete({'id': proxy_id})


def realm_cleanup(realm_id=None):
    """Deletes the realm with the given id"""
    entities.Realm(id=realm_id).delete()


def location_cleanup(loc_id=None):
    """Deletes the location with the given id"""
    entities.Location(id=loc_id).delete()


def org_cleanup(org_id=None):
    """Deletes the Org with the given id"""
    entities.Organization(id=org_id).delete()


def host_cleanup(host_id=None):
    """Deletes the Host with the given id"""
    entities.Host(id=host_id).delete()


def setting_cleanup(setting_name=None, setting_value=None):
    """Put necessary value for a specified setting"""
    setting_entity = entities.Setting().search(
        query={'search': 'name={}'.format(setting_name)})[0]
    setting_entity.value = setting_value
    setting_entity.update({'value'})


def vm_cleanup(vm):
    """Destroys virtual machine

    :param robottelo.vm.VirtualMachine vm: virtual machine to destroy
    """
    vm.destroy()


def cleanup_of_provisioned_server(hostname=None, provisioning_server=None,
                                  distro=None):
    """ Cleanup the VM from provisioning server

    :param: str hostname: The content host hostname
    :param: str provisioning_server: provision server name
    :param: str distro: distro type
    """
    if hostname:
        vm = VirtualMachine(
            hostname=hostname,
            target_image=hostname,
            provisioning_server=provisioning_server,
            distro=distro,
        )
        vm._created = True
        vm.destroy()
