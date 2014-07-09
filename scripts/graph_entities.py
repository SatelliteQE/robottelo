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
from robottelo import entities, orm
import inspect


# Compile a dict of `orm.Entity` subclasses.
entities_ = {}
for name, klass in inspect.getmembers(entities, inspect.isclass):
    if issubclass(klass, orm.Entity):
        entities_[name] = klass

# Generate DOT-formatted output.
print('digraph dependencies {')  # (superfluous-parens) pylint:disable=C0325
for entity_name, entity in entities_.items():
    for field_name, field in entity.get_fields().items():
        if (isinstance(field, orm.OneToOneField)
                or isinstance(field, orm.OneToManyField)):
            print('{0} -> {1} [label="{2}"{3}]'.format(
                entity_name,
                field.model,
                field_name,
                ' color=red' if field.options.get('required', False) else ''
            ))
print('}')  # (superfluous-parens) pylint:disable=C0325
