"""This module defines all entities which Foreman exposes.

Each class in this module corresponds to a certain type of Foreman entity. For
example, the ``Host`` class corresponds to the "Host" Foreman entity.
Similarly, each class attribute corresponds to a Foreman entity attribute. For
example, the ``Host.name`` class attribute corresponds to the "name" attribute
of a "Host" entity.

"""
from robottelo import orm
# (too-few-public-methods) pylint:disable=R0903


class Host(orm.Entity):
    """A representation of a Host entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        '''Alternate names for this entity's fields.'''
        api_names = {'name': 'host[name]'}


class Model(orm.Entity):
    """A representation of a Model entity."""
    name = orm.StringField(required=True)
    info = orm.StringField()
    vendor_class = orm.StringField()
    hardware_model = orm.StringField()

    class Meta(object):
        '''Alternate names for this entity's fields.'''
        api_names = {
            'name': 'model[name]',
            'info': 'model[info]',
            'vendor_class': 'model[vendor_class]',
            'hardware_model': 'model[hardware_model]',
        }


class Organization(orm.Entity):
    """A representation of an Organization entity."""
    name = orm.StringField(required=True)
    label = orm.StringField()
    description = orm.StringField()


class Product(orm.Entity):
    """A representation of a Product entity."""
    organization_id = orm.OneToOneField(Organization, required=True)
    description = orm.StringField()
    gpg_key_id = orm.IntegerField()
    #sync_plan_id = orm.OneToOneField(SyncPlan)  # FIXME: implement SyncPlan
    name = orm.StringField(required=True)
    label = orm.StringField()
