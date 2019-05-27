# -*- encoding: utf-8 -*-
"""Cleanup module for different entities"""
import logging
from collections import deque, defaultdict
from nailgun import entities, signals
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.proxy import Proxy
from robottelo.constants import DEFAULT_ORG
from robottelo.decorators import bz_bug_is_open


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


class EntitiesCleaner(object):
    """Register and clean entities for cleanup using signals"""

    def __init__(self, *types_to_cleanup):
        self.cleanup_queue = defaultdict(deque)
        self.deleted_entities = defaultdict(set)
        self.types_to_cleanup = types_to_cleanup
        self.logger = logging.getLogger('robottelo')
        self.connect_cleanup_signals()

    def connect_cleanup_signals(self):
        """Connect signals to entity types specified for cleanup"""
        for entity_type in self.types_to_cleanup:
            self.logger.info('Registering %s signal for cleanup', entity_type)
            signals.post_create.connect(self.register_entity_for_cleanup,
                                        sender=entity_type)

    def register_entity_for_cleanup(self, sender, entity, **kwargs):
        """Put a new entity in the queue to be cleaned"""
        self.logger.info(
            'Adding {0}:{1} for cleanup_queue'.format(sender, entity.id))
        self.cleanup_queue[entity.__class__.__name__].appendleft(entity)

    def clean(self):
        """This method is called in TearDownClass only when cleanup=true"""
        default_org_id = entities.Organization().search(
            query={'search': 'name="{}"'.format(DEFAULT_ORG)})[0].id
        default_org = entities.Organization(id=default_org_id)
        # reassign created hosts to default org
        self.update_entities(
            self.cleanup_queue.get(entities.Host.__name__, []),
            hostgroup=None,
            managed=False,
            organization=default_org
        )
        # reassign created host groups to default org
        self.update_entities(
            self.cleanup_queue.get(entities.HostGroup.__name__, []),
            lifecycle_environment=None,
            content_view=None,
            organization=[default_org]
        )
        # delete organizations
        self.delete_entities(
            self.cleanup_queue.get(entities.Organization.__name__, []),
            synchronous=False
        )

        self.logger.debug(
            'Cleanup deleted %s entities', len(self.deleted_entities))

    def delete_entities(self, entity_list, **kwargs):
        self.logger.debug(
            'Cleanup got %s entities to delete', len(entity_list))
        for entity in entity_list:
            entity_type = entity.__class__.__name__
            if entity.id in self.deleted_entities[entity_type]:
                # skip already deleted entities
                continue
            try:
                if isinstance(entity, entities.Organization):
                    query = {'search': 'organization_id={0}'.format(entity.id)}
                    org_hosts = entities.Host().search(query=query)
                    if org_hosts:  # Do not delete organizations with hosts
                        self.logger.debug(
                            'Org %s can\'t be deleted as it has %s hosts',
                            entity.id,
                            len(org_hosts)
                        )
                        return
                entity.delete(**kwargs)
            except Exception as e:
                self.logger.warn('Error deleting entity %s', str(e))
            else:
                self.deleted_entities[entity_type].add(entity.id)

    def update_entities(self, entity_list, **kwargs):
        self.logger.debug(
            'Cleanup got %s entities to update', len(entity_list))
        for entity in entity_list:
            try:
                for key, value in kwargs.items():
                    setattr(entity, key, value)
                entity.update(fields=kwargs.keys())
            except Exception as e:
                self.logger.warn('Error updating entity %s', str(e))
