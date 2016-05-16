# -*- encoding: utf-8 -*-
"""Cleanup module for different entities"""
from nailgun import entities
from robottelo.cli.proxy import Proxy


def capsule_cleanup(proxy_id=None):
    """Deletes the capsule with the given id"""
    Proxy.delete({'id': proxy_id})


def location_cleanup(loc_id=None):
    """Deletes the location with the given id"""
    entities.Location(id=loc_id).delete()


def org_cleanup(org_id=None):
    """Deletes the Org with the given id"""
    entities.Organization(id=org_id).delete()
