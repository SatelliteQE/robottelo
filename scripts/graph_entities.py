#!/usr/bin/env python2
"""Graph relationships between entities.

For each entity in module ``nailgun.entities``, determine which entities it
depends on. Print this dependency information to stdout in DOT format. To run
this script and generate an image all in one go, use the ``graph-entities``
command provided by the make file in the parent directory.

"""

import inspect

from nailgun import entities, entity_mixins


def graph():
    """Graph the relationships between the entity classes."""
    # Compile a dict of `entity_mixins.Entity` subclasses.
    entities_ = {}
    for name, klass in inspect.getmembers(entities, inspect.isclass):
        if issubclass(klass, entity_mixins.Entity):
            entities_[name] = klass
    # Generate DOT-formatted output.
    print('digraph dependencies {')
    for entity_name, entity in entities_.items():
        # Graph out which entities this entity depends on.
        for field_name, field in entity.get_fields().items():
            if isinstance(field, (entity_mixins.OneToOneField | entity_mixins.OneToManyField)):
                print(
                    '{} -> {} [label="{}"{}]'.format(
                        entity_name,
                        field.entity,
                        field_name,
                        ' color=red' if field.required else '',
                    )
                )
        # Make entities that cannot be created less visible.
        if not issubclass(entity, entity_mixins.EntityCreateMixin):
            print(f'{entity_name} [style=dotted]')
    print('}')


if __name__ == '__main__':
    graph()
