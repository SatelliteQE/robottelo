import os
import logging
from collections import Sequence
from six import string_types
from jinja2 import Template
from robottelo.config import settings

logger = logging.getLogger(__name__)


def render_single(data, context):
    """Gets a single entity description and perform inplace template
    rendering or reference evaluation for single data sets."""
    for k, v in data.items():
        if isinstance(v, dict):
            if 'from_registry' in v:
                try:
                    data[k] = eval(v['from_registry'], None, context)
                except NameError as e:
                    logger.error(str(e))
                    raise NameError(
                        "{0}: Please check if the reference "
                        "was added to the registry".format(str(e)))
            else:
                render_single(v, context)
        elif isinstance(v, string_types):
            if '{{' in v and '}}' in v:
                data[k] = Template(v).render(**context)


def render(raw_entity, context):
    """Takes an entity description and strips 'data' out to
    perform single rendering and also handle repetitions"""
    if 'data' not in raw_entity:
        raise ValueError('entity misses `data` key')

    items = raw_entity.get('with_items')
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
        items = [None, ]

    for loop_index, item in enumerate(items):
        new_context = {}
        new_context.update(context)
        new_context['item'] = item
        new_context['loop_index'] = loop_index
        new_entity_data = raw_entity['data'].copy()
        # loop index should be removed before creation
        # that is performed in render_search_data
        new_entity_data['loop_index'] = loop_index

        render_single(
            new_entity_data,
            new_context
        )

        entities.append(new_entity_data)

    return entities


class BasePopulator(object):
    """Base class for API and CLI populator"""

    def __init__(self, data):
        self.logger = logger
        self.vars = data.get('vars', {})
        self.entities = data['entities']
        self.registry = {}
        self.validation_errors = []
        self.total_created = 0
        self.total_existing = 0

        if not settings.configured:
            settings.configure()

        self.admin_username = self.vars.get(
            'admin_username', settings.server.admin_username)
        self.admin_password = self.vars.get(
            'admin_password', settings.server.admin_password)

        self.context = {
            'settings': settings,
            'env': os.environ
        }
        self.context.update(self.vars)

        self.context.update(
            {'admin_username': self.admin_username,
             'admin_password': self.admin_password}
        )

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
        return render(entity, context=self.context)

    def render_search_data(self, entity_data, raw_entity):
        """Creates a dictionary for Nailgun search mixin as in the example:
        `{'query': {'search':'name=Orgcompanyone,label=Orgcompanyone,id=28'}}`
        By default that dict will use all fields provided in entity_data
        if `validate_fields` is available then use that provided fields/values
        """
        # if with_items, get current loop_index reference or 0
        loop_index = entity_data.pop('loop_index', 0)

        if 'validate_fields' not in raw_entity:
            data = {
                key: value for key, value in entity_data.items()
                if isinstance(value, string_types) and
                key not in ['password']
            }
        else:
            if isinstance(raw_entity['validate_fields'], dict):
                items = raw_entity.get('with_items')

                if items and isinstance(items, list):
                    items = [
                        Template(item).render(**self.context)
                        for item in items
                    ]
                elif items and isinstance(items, string_types):
                    items = eval(items, None, self.context)
                    if not isinstance(items, Sequence):
                        raise AttributeError(
                            "with_items must be sequence type")
                else:
                    # as there is no with_items, a single item list will
                    # ensure the addition of a single one.
                    items = [None, ]

                new_context = {}
                new_context.update(self.context)
                new_context['item'] = items[loop_index]
                new_context['loop_index'] = loop_index

                data = {
                    key: Template(value).render(**new_context)
                    for key, value in raw_entity['validate_fields'].items()
                }

            elif isinstance(raw_entity['validate_fields'], Sequence):
                data = {
                    key: entity_data[key]
                    for key in raw_entity['validate_fields']
                }
            else:
                raise ValueError("validate_fields bad formatted")

        search_query = ",".join(
            ["{0}={1}".format(key, value) for key, value in data.items()]
        )
        search_query = Template(search_query).render(**self.context)
        return {'query': {'search': search_query}}

    def execute(self, mode='populate'):
        """Iterates the entities property described in YAML file
        and parses its values, variables and substitutions
        depending on `mode` execute `populate` or `validate`

        """

        for raw_entity in self.entities:
            entities_list = self.render_entities(raw_entity)
            for entity_data in entities_list:
                model_name = raw_entity['model'].lower()
                method = getattr(
                    self, '{0}_{1}'.format(mode, model_name), None
                )
                search_data = self.render_search_data(entity_data, raw_entity)
                if method:
                    method(entity_data, raw_entity, search_data)
                else:
                    # execute self.populate or self.validate
                    getattr(self, mode)(entity_data, raw_entity, search_data)

                # ensure context is updated with latest created entities
                self.context.update(self.registry)

    def populate(self, entity_data, raw_entity, search_data):
        """Should be implemented in sub classes"""
        raise NotImplementedError()

    def validate(self, entity_data, raw_entity, search_data):
        """Should be implemented in sub classes"""
        raise NotImplementedError()

    def populate_modelname(self, entity_data, raw_entity, search_data):
        """Example on how to implement custom populate methods
           e.g: `def populate_organization`
        This method should take care of all validations and errors.
        """

        result = (
            "Implement your own populate method here,"
            "This method should take care of `validate_fields`"
            "to check the existence of entity before creation"
            "and should return a valid Nailgun entity object"
            "containing a valid `id`"
        )

        # always add the result to registry to allow references
        self.add_to_registry(raw_entity, result)

    def validate_modelname(self, entity_data, raw_entity, search_data):
        """Example on how to implement custom validate methods
           e.g: `def validate_organization`
        This method should take care of all validations and errors.
        """

        result = (
            "Implement your own validate method here,"
            "This method should use `validate_fields`"
            "to check the existence of entities"
            "and should add valid Nailgun entity object to self.registry"
            "and errors to self.validation_errors"
        )

        # always add the result to registry to allow references
        self.add_to_registry(raw_entity, result)

        self.validation_errors.append("message")