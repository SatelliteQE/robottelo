"""This module defines all entities which Foreman exposes.

Each class in this module corresponds to a certain type of Foreman entity. For
example, the ``Host`` class corresponds to the "Host" Foreman entity.
Similarly, each class attribute corresponds to a Foreman entity attribute. For
example, the ``Host.name`` class attribute corresponds to the "name" attribute
of a "Host" entity.

"""
from robottelo import orm


class Host(orm.Entity):
    """Entity representing a Host on a Foreman system."""
    name = orm.StringField(required=True)


class Model(orm.Entity):
    """Entity representing a Model on a Foreman system."""
    name = orm.StringField(required=True)
    info = orm.StringField()
    vendor_class = orm.StringField()
    hardware_model = orm.StringField()
