import os
from collections import Sequence
from six import string_types
from jinja2 import Template
from robottelo.config import settings


def render_single(data, context):
    """Gets a single entity description and perform inplace template
    rendering or reference evaluation for single data sets."""
    for k, v in data.items():
        if isinstance(v, dict):
            if 'from_registry' in v:
                data[k] = eval(v['from_registry'], None, context)
            else:
                render_single(v, context)
        elif isinstance(v, string_types):
            if '{{' in v and '}}' in v:
                data[k] = Template(v).render(**context)


def render(entity, context):
    """Takes an entity description and strips 'data' out to
    perform single rendering and also handle repetitions"""
    if 'data' not in entity:
        raise ValueError('entity misses `data` key')

    items = entity.get('with_items')
    entities = []

    if items and isinstance(items, list):
        items = [Template(item).render(**context) for item in items]
    elif items and isinstance(items, string_types):
        items = eval(items, None, context)
        if not isinstance(items, Sequence):
            raise AttributeError("with_items must be sequence type")
    else:
        # as there is no with_items, a single item list will
        # ensure the addition of a single one.
        items = [None,]

    for loop_index, item in enumerate(items):
        new_context = {}
        new_context.update(context)
        new_context['item'] = item
        new_context['loop_index'] = loop_index
        new_entity_data = entity['data'].copy()
        render_single(
            new_entity_data,
            new_context
        )
        entities.append(new_entity_data)

    return entities


class BasePopulator(object):
    """Base class for API and CLI populator"""

    def __init__(self, data):
        self.vars = data.get('vars', {})
        self.entities = data['entities']
        self.registry = {}

        if not settings.configured:
            settings.configure()

        self.admin_user = self.vars.get(
            'admin_username', settings.server.admin_username)
        self.admin_password = self.vars.get(
            'admin_password', settings.server.admin_password)

    def add_to_registry(self, entity, result):
        """Once an entity is created this method adds it to the registry"""
        if not entity['register']:
            return

        registry_key = entity['register']

        if entity.get('with_items'):
            if registry_key in self.registry:
                self.registry[registry_key].append(result)
            else:
                self.registry[registry_key] = [result]
        else:
            self.registry[registry_key] = result

    def render_entities(self, entity):
        """Get an entity dict and render each string using jinja and
        assign relations from_registry"""

        context = {
            'settings': settings,
            'env': os.environ
        }
        context.update(self.vars)
        context.update(self.registry)
        return render(entity, context=context)
