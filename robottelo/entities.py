"""This module define all entities from Satellite

Each entity is mapped with its required and optional fields.

"""
from robottelo import models


class Host(models.Entity):
    """Entity that represents a Host on a Satellite system"""
    name = models.StringField(required=True)
