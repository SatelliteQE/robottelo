#!/usr/bin/env python2
"""Graph relationships between entities.

For each entity in :mod:`robottelo.entities`, determine which entities it
depends on. Print this dependency information to stdout in DOT format. To run
this script and generate an image all in one go, use the ``graph-entities``
command provided by the make file in the parent directory.

"""
# Append parent dir to sys.path if not already present.
import os
import sys
ROBOTTELO_PATH = os.path.realpath(os.path.join(
    os.path.dirname(__file__),
    os.path.pardir
))
if ROBOTTELO_PATH not in sys.path:
    sys.path.append(ROBOTTELO_PATH)

# Proceed with normal imports.
import inspect  # noqa
from robottelo import entities, orm  # noqa


def graph():
    """Read through ``robottelo/entities.py`` and graph their relationships."""
    # Compile a dict of `orm.Entity` subclasses.
    entities_ = {}
    for name, klass in inspect.getmembers(entities, inspect.isclass):
        if issubclass(klass, orm.Entity):
            entities_[name] = klass
    # Generate DOT-formatted output.
    #
    # Ignore superfluous parentheses, as Python 3 requires them for print().
    # (superfluous-parens) pylint:disable=C0325
    print('digraph dependencies {')
    for entity_name, entity in entities_.items():
        # Graph out which entities this entity depends on.
        for field_name, field in entity.get_fields().items():
            if (isinstance(field, orm.OneToOneField) or
                    isinstance(field, orm.OneToManyField)):
                print('{0} -> {1} [label="{2}"{3}]'.format(
                    entity_name,
                    field.entity,
                    field_name,
                    ' color=red' if field.required else ''
                ))
        # Make entities that cannot be created less visible.
        if not issubclass(entity, orm.EntityCreateMixin):
            print('{0} [style=dotted]'.format(entity_name))
    print('}')

if __name__ == '__main__':
    graph()
