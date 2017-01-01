import os
import logging
import fauxfactory
import import_string
from collections import Sequence
from six import string_types
from jinja2 import Template
from nailgun import entities
from nailgun.entity_mixins import Entity, EntitySearchMixin
from robottelo.config import settings

logger = logging.getLogger(__name__)

INVALID_FOR_SEARCH = {
    'user': ['password', 'default_organization']
}
APPEND_ID = ['organization']
SPECIAL_ACTIONS = ('register', 'unregister', 'assertion')
CRUD_ACTIONS = ('create', 'update', 'delete')


def parse_field_name(key):
    """transform field name for search, appending _id when necessary
    example: organization turns to organization_id
    """
    if key in APPEND_ID:
        return "{0}_id".format(key)
    return key


def parse_field_value(value):
    """Turn objects in to IDS for search"""
    if isinstance(value, Entity):
        return value.id
    return value


class BasePopulator(object):
    """Base class for API and CLI populator"""

    def __init__(self, data):
        self.logger = logger
        self.vars = data.get('vars', {})
        self.actions = data['actions']
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
            'env': os.environ,
            'fauxfactory': fauxfactory
        }
        self.context.update(self.vars)

        self.context.update(
            {'admin_username': self.admin_username,
             'admin_password': self.admin_password}
        )

    def add_to_registry(self, action_data, result):
        """Once an entity is created this method adds it to the registry"""
        if not action_data.get('register'):
            return

        registry_key = action_data['register']

        if action_data.get('with_items'):
            if registry_key in self.registry:
                self.registry[registry_key].append(result)
            else:
                self.registry[registry_key] = [result]
        else:
            self.registry[registry_key] = result

        self.logger.info("register: %s added to registry", registry_key)

    def search_entity(self, action_data, context):
        """Gets fields and perform a search to return Entity object
        used when 'from_search' directive is used in YAML file"""

        model_name = action_data['model']
        options = action_data.get('options', {})
        get_all = action_data.get('all', False)

        model = getattr(entities, model_name)
        if not issubclass(model, EntitySearchMixin):
            raise TypeError("{0} not searchable".format(model))

        if 'data' in action_data:
            rendered_data = action_data['data'].copy()
            self.render_single(rendered_data, context)

            query_data = {
                parse_field_name(key): parse_field_value(value)
                for key, value in rendered_data.items()
                if key not in INVALID_FOR_SEARCH.get(model_name.lower(), [])
                and isinstance(value, (string_types, Entity))
            }

            search_query = ",".join(
                ["{0}={1}".format(key, value)
                 for key, value in query_data.items()]
            )

            query = {'query': {'search': search_query}}
            query['query'].update(options)
            if 'organization' in rendered_data:
               if isinstance(rendered_data['organization'], Entity):
                   org_id = rendered_data['organization'].id
                   query['query']['organization_id'] = org_id

            if 'filters' in action_data:
                query['filters'] = action_data['filters']
            search_result = model().search(**query)
        else:
            # empty search
            query = {'query': options}
            if 'filters' in action_data:
                query['filters'] = action_data['filters']
            search_result = model().search(**query)

        silent_errors = action_data.get('silent_errors', False)

        if not search_result:
            if silent_errors:
                return None
            raise RuntimeError("Search returned no objects")

        if get_all:
            self.add_to_registry(action_data, search_result)
            return search_result
        else:
            self.add_to_registry(action_data, search_result[0])
            return search_result[0]


    def render_single(self, data, context):
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
                elif 'from_object' in v:
                    try:
                        data[k] = import_string(v['from_object'])
                    except ImportError as e:
                        logger.error(str(e))
                        raise
                elif 'from_search' in v:
                    try:
                        data[k] = self.search_entity(v['from_search'], context)
                    except Exception as e:
                        logger.error(str(e))
                        raise
                else:
                    self.render_single(v, context)
            elif isinstance(v, string_types):
                if '{{' in v and '}}' in v:
                    data[k] = Template(v).render(**context)

    def render(self, action_data, action):
        """Takes an entity description and strips 'data' out to
        perform single rendering and also handle repetitions"""
        if 'data' not in action_data:
            raise ValueError('entity misses `data` key')

        items = action_data.get('with_items')
        context = self.context
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

            # data can be dict on CRUD or list on SPECIAL_ACTIONS
            data = action_data['data']
            if isinstance(data, dict):
                entity_data = data.copy()
            else:
                entity_data = {'values': data}

            # loop index should be removed before creation
            # that is performed in build_search_query
            entity_data['loop_index'] = loop_index

            self.render_single(
                entity_data,
                new_context
            )

            entities.append(entity_data)

        return entities

    def build_search_query(self, entity_data, action_data):
        """Creates a dictionary for Nailgun search mixin as in the example:
        `{'query': {'search':'name=Orgcompanyone,label=Orgcompanyone,id=28'}}`
        By default that dict will use all fields provided in entity_data
        if `validate_fields` is available then use that provided fields/values
        """
        # if with_items, get current loop_index reference or 0
        loop_index = entity_data.pop('loop_index', 0)
        model_name = action_data['model'].lower()
        if 'validate_fields' not in action_data:
            data = {
                parse_field_name(key): parse_field_value(value)
                for key, value in entity_data.items()
                if key not in INVALID_FOR_SEARCH.get(model_name, []) and
                isinstance(value, (string_types, Entity))
            }
        else:
            if isinstance(action_data['validate_fields'], dict):
                items = action_data.get('with_items')

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
                    for key, value in action_data['validate_fields'].items()
                }

            elif isinstance(action_data['validate_fields'], Sequence):
                data = {
                    key: entity_data[key]
                    for key in action_data['validate_fields']
                }
            else:
                raise ValueError("validate_fields bad formatted")

        search_query = ",".join(
            ["{0}={1}".format(key, value) for key, value in data.items()]
        )
        search_query = Template(search_query).render(**self.context)
        query = {'query': {'search': search_query}}
        if 'organization' in entity_data:
            if isinstance(entity_data['organization'], Entity):
                org_id = entity_data['organization'].id
                query['query']['organization_id'] = org_id
        return query

    def execute(self, mode='populate'):
        """Iterates the entities property described in YAML file
        and parses its values, variables and substitutions
        depending on `mode` execute `populate` or `validate`

        """

        for action_data in self.actions:
            action = action_data.get('action', 'create')
            entities_list = self.render(action_data, action)
            for entity_data in entities_list:

                if action in SPECIAL_ACTIONS:
                    # find the method named as action name
                    getattr(self, action)(
                        entity_data, action_data, action
                    )

                    # execute above method and continue to next item
                    continue

                # Executed only for create, update, delete actions
                model_name = action_data['model'].lower()
                method = getattr(
                    self, '{0}_{1}'.format(mode, model_name), None
                )
                search_query = self.build_search_query(
                    entity_data, action_data
                )
                if method:
                    method(entity_data, action_data, search_query, action)
                else:
                    # execute self.populate or self.validate
                    getattr(self, mode)(
                        entity_data, action_data, search_query, action
                    )

                # ensure context is updated with latest created entities
                self.context.update(self.registry)

    def unregister(self, entity_data, action_data, action):
        """Remove data from registry"""
        for value in entity_data['values']:
            if self.registry.pop(value, None):
                self.logger.info("unregister: %s unregistered", value)
            else:
                self.logger.info("unregister: %s not was registered", value)

    def register(self, entity_data, action_data, action):
        """Should be implemented in sub classes"""
        loop_index = entity_data.pop('loop_index', 0)
        for key, value in entity_data.items():
            data = action_data.copy()
            data['register'] = key
            self.add_to_registry(data, value)

    def populate(self, entity_data, raw_entity, search_query, action):
        """Should be implemented in sub classes"""
        raise NotImplementedError()

    def validate(self, entity_data, raw_entity, search_query, action):
        """Should be implemented in sub classes"""
        raise NotImplementedError()

    def assertion(self, entity_data, action_data, action):
        """Should be implemented in sub classes"""
        raise NotImplementedError

    def populate_modelname(self, entity_data, action_data, search_query, action):
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
        self.add_to_registry(action_data, result)

    def validate_modelname(self, entity_data, action_data, search_query, action):
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
        self.add_to_registry(action_data, result)

        # add errors to validation_errors
        self.validation_errors.append({
            'search_query': search_query,
            'message': 'entity does not validate in the system',
            'entity_data':  entity_data,
            'action_data': action_data
        })