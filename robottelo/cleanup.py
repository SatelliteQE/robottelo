"""Cleanup module for different entities"""
from nailgun import entities

from robottelo.cli.proxy import Proxy


def capsule_cleanup(proxy_id=None):
    """Deletes the capsule with the given id"""
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
    setting_entity = entities.Setting().search(query={'search': f'name={setting_name}'})[0]
    setting_entity.value = setting_value
    setting_entity.update({'value'})
