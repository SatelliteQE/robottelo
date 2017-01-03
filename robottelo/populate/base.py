# coding: utf-8
"""
Base module for robottelo.populate
reads the YAML definition and perform all the rendering and basic actions.
"""
import fauxfactory
import import_string
import logging
import os

from collections import Sequence
from jinja2 import Template
from nailgun import entities
from nailgun.entity_mixins import EntitySearchMixin, EntityReadMixin
from robottelo.config import settings
from robottelo.populate import assertion_operators
from robottelo.populate.constants import (
    FORCE_RAW_SEARCH,
    LOGGERS,
    RAW_SEARCH_RULES,
    ACTIONS_SPECIAL
)
from six import string_types

logger = logging.getLogger(__name__)


def set_logger(verbose):
    """Set logger verbosity used when client is called with -vvvv"""
    if verbose == 0:
        for logger_name in LOGGERS.values():
            logging.getLogger(logger_name).disabled = True
    elif verbose == 1:
        logging.getLogger(LOGGERS['nailgun']).disabled = True
        logging.getLogger(LOGGERS['ssh']).disabled = True
    elif verbose == 2:
        logging.getLogger(LOGGERS['ssh']).disabled = True


class BasePopulator(object):
    """Base class for API and CLI populators"""

    def __init__(self, data, verbose=None, mode='populate'):
        """Reads YAML and initialize populator"""
        self.logger = logger
        set_logger(verbose)

        self.mode = mode
        self.vars = data.get('vars', {})
        self.actions = data['actions']
        self.registry = {}
        self.validation_errors = []
        self.assertion_errors = []
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
            'fauxfactory': fauxfactory,
            'registry': self.registry
        }
        self.context.update(self.vars)

        self.context.update(
            {'admin_username': self.admin_username,
             'admin_password': self.admin_password}
        )

    def add_to_registry(self, action_data, result):
        """Add objects to the internal registry"""
        if not action_data.get('register'):
            return

        registry_key = Template(action_data['register']).render(**self.context)

        if action_data.get('with_items'):
            if registry_key in self.registry:
                self.registry[registry_key].append(result)
            else:
                self.registry[registry_key] = [result]
        else:
            self.registry[registry_key] = result

        self.logger.info("register: %s added to registry", registry_key)

    def from_search(self, action_data, context):
        """Gets fields and perform a search to return Entity object
        used when 'from_search' directive is used in YAML file
        """

        model_name = action_data['model']
        unique = action_data.get('unique', True)
        get_all = action_data.get('all', False)
        index = action_data.get('index', None)
        model = getattr(entities, model_name)

        if 'data' in action_data:
            data = action_data['data'].copy()
            self.render_action_data(data, context)
            search = self.build_search(data, action_data, context)
            search_result = self.get_search_result(
                model, search, unique=unique
            )
        else:
            # empty search returns all when used with filters={}
            options = self.build_search_options({}, action_data)
            search_result = model().search(**options)

        silent_errors = action_data.get('silent_errors', False)

        if not search_result:
            if silent_errors:
                return None
            raise RuntimeError("Search returned no objects")

        if unique or get_all:
            self.add_to_registry(action_data, search_result)
            return search_result

        self.add_to_registry(action_data, search_result[index or 0])
        return search_result[index or 0]

    def from_read(self, action_data, context):
        """Gets fields and perform a read to return Entity object
        used when 'from_read' directive is used in YAML file
        """

        if 'id' not in action_data['data']:
            raise RuntimeError("read operations demands an id")

        model_name = action_data['model']
        model = getattr(entities, model_name)
        if not issubclass(model, EntityReadMixin):
            raise TypeError("{0} not readable".format(model))

        entity_data = action_data['data'].copy()
        self.render_action_data(entity_data, context)

        entity = model(**entity_data).read()

        self.add_to_registry(action_data, entity)
        return entity

    def render_action_data(self, data, context):
        """Gets a single action_data and perform inplace template
        rendering or reference evaluation depending on directive being used.
        """
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
                        result = import_string(v['from_object']['name'])
                        self.resolve_result_attr(
                            data, 'from_object', k, v, result
                        )
                    except ImportError as e:
                        logger.error(str(e))
                        raise
                elif 'from_search' in v:
                    try:
                        result = self.from_search(
                            v['from_search'], context
                        )
                        self.resolve_result_attr(
                            data, 'from_search', k, v, result
                        )

                    except Exception as e:
                        logger.error(str(e))
                        raise
                elif 'from_read' in v:
                    try:
                        result = self.from_read(v['from_read'], context)
                        self.resolve_result_attr(
                            data, 'from_read', k, v, result
                        )
                    except Exception as e:
                        logger.error(str(e))
                        raise
                else:
                    self.render_action_data(v, context)
            elif isinstance(v, string_types):
                if '{{' in v and '}}' in v:
                    data[k] = Template(v).render(**context)

    def resolve_result_attr(self, data, from_where, k, v, result):
        """Used in `from_search` and `from_object` to get specific
         attribute from object e.g: name. Or to invoke a method when
         attr is a dictionary of parameters.
        """
        attr = v[from_where].get('attr')
        if not attr:
            data[k] = result
        elif isinstance(attr, string_types):
            data[k] = getattr(result, attr)
        elif isinstance(attr, dict):
            data[k] = getattr(result, attr.keys()[0])(**attr.values()[0])
        else:
            raise RuntimeError('attr must be string or dict')

    def render(self, action_data, action):
        """Takes an entity description and strips 'data' out to
        perform single rendering and also handle repetitions defined
        in `with_items`
        """
        if action not in ('delete', 'assertion') and 'data' not in action_data:
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
            data = action_data.get('data')
            if isinstance(data, dict):
                entity_data = data.copy()
            else:
                entity_data = {'_values': data}

            # loop index should be removed before creation
            # that is performed in build_search_query
            entity_data['loop_index'] = loop_index

            self.render_action_data(
                entity_data,
                new_context
            )

            entities.append(entity_data)

        return entities

    def build_search(self, entity_data, action_data, context=None):
        """Build search data and returns a dict containing elements

        data:
        Dictionary of parsed entity_data to be used to instantiate an object
        to searched without raw_query.

        options:
        if `search_options` are specified it is passed to .search(**options)

        searchable:
        Returns boolean True if model inherits from EntitySearchMixin, else
        alternative search must be implemented.

        if `search_query` is available in action_data it will be used instead
        od entity_data.
        """

        # if with_items, get current loop_index reference or 0
        loop_index = entity_data.pop('loop_index', 0)

        if 'search_query' not in action_data:
            data = entity_data
        else:
            search_data = action_data['search_query']
            if isinstance(search_data, dict):
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
                new_context.update(context or {})
                new_context['item'] = items[loop_index]
                new_context['loop_index'] = loop_index
                data = search_data.copy()
                self.render_action_data(data, new_context)

            elif isinstance(search_data, Sequence):
                data = {
                    key: entity_data[key]
                    for key in search_data
                }
            else:
                raise ValueError("search_query bad formatted")

        model_name = action_data['model']
        model = getattr(entities, model_name)
        options = self.build_search_options(data, action_data)

        return {
            'data': data,
            'options': options,
            'searchable': issubclass(model, EntitySearchMixin)
        }

    def build_raw_query(self, data, action_data):
        """Builds nailgun raw_query for search"""
        search_data = data.copy()

        rules = RAW_SEARCH_RULES.get(action_data['model'].lower())
        if rules:
            for field_name, rule in rules.items():
                if field_name not in search_data:
                    continue

                if rule.get('rename'):
                    value = search_data[field_name]

                    attr = rule.get('attr')
                    index = rule.get('index')
                    key = rule.get('key')

                    if index is not None:
                        value = value[index]

                    if key is not None:
                        value = value[key]

                    if attr:
                        search_data[rule['rename']] = getattr(value, attr)
                    else:
                        search_data[rule['rename']] = value

                if rule.get('remove') or rule.get('rename'):
                    del search_data[field_name]

        query_items = [
            "{0}={1}".format(k, v) for k, v in search_data.items()
        ]
        raw_query = ",".join(query_items)
        return {'search': raw_query}

    def build_search_options(self, data, action_data):
        """Builds nailgun options for search
        raw_query:
        Some API endpoints demands a raw_query, so build it as in example:
        `{'query': {'search':'name=name,label=label,id=28'}}`

        force_raw:
        Returns a boolean if action_data.force_raw is explicitly specified

        """
        options = action_data.get('search_options', {})

        force_raw = options.pop(
            'force_raw', False
        ) or action_data['model'].lower() in FORCE_RAW_SEARCH

        if force_raw:
            options['query'] = self.build_raw_query(data, action_data)

        per_page = options.pop('per_page', None)
        if per_page:
            if 'query' in options:
                options['query']['perpage'] = per_page
            else:
                options['query'] = {'per_page': per_page}

        return options

    def get_search_result(self, model, search, unique=False,
                          silent_errors=False):
        """Perform a search"""
        if not search['searchable']:
            if silent_errors:
                return
            raise TypeError("{0} not searchable".format(model))

        result = model(**search['data']).search(**search['options'])

        if not result:
            return

        if unique:
            if len(result) > 1 and not silent_errors:
                self.logger.info(result)
                raise RuntimeError(
                    "More than 1 item returned "
                    "search is not unique"
                )
            return result[0]

        return result

    def execute(self, mode=None):
        """Iterates the entities property described in YAML file
        and parses its values, variables and substitutions
        depending on `mode` execute `populate` or `validate`
        """
        mode = mode or self.mode
        for action_data in self.actions:
            action = action_data.get('action', 'create')
            if action_data.get('log'):
                self.logger.info("%s: %s", action, action_data['log'])
            else:
                self.logger.info('%s: Running...', action)
            entities_list = self.render(action_data, action)
            for entity_data in entities_list:

                if action in ACTIONS_SPECIAL:
                    # find the method named as action name
                    getattr(self, action)(entity_data, action_data)

                    # execute above method and continue to next item
                    continue

                # Executed only for create, update, delete actions
                model_name = action_data['model'].lower()
                method = getattr(
                    self, '{0}_{1}'.format(mode, model_name), None
                )
                search = self.build_search(
                    entity_data, action_data
                )
                if method:
                    method(entity_data, action_data, search, action)
                else:
                    # execute self.populate or self.validate
                    getattr(self, mode)(
                        entity_data, action_data, search, action
                    )

                # ensure context is updated with latest created entities
                self.context.update(self.registry)

    # special methods

    def unregister(self, entity_data, action_data):
        """Remove data from registry"""
        for value in entity_data['_values']:
            if self.registry.pop(value, None):
                self.logger.info("unregister: %s unregistered", value)
            else:
                self.logger.info("unregister: %s not was registered", value)

    def register(self, entity_data, action_data):
        """Register arbitrary items to the registry"""
        entity_data.pop('loop_index', 0)
        for key, value in entity_data.items():
            data = action_data.copy()
            data['register'] = key
            self.add_to_registry(data, value)

    def assertion(self, entity_data, action_data):
        """Run assert operations"""
        new_context = self.context.copy()
        new_context['loop_index'] = loop_index = entity_data.get('loop_index')
        new_context['item'] = action_data.get('with_items', [None])[loop_index]
        operator = action_data.get('operator', 'eq')
        assertion_function = getattr(assertion_operators, operator)
        data = {
            'value' if index == 0 else 'other': value
            for index, value in enumerate(action_data['data'])
        }
        self.render_action_data(data, new_context)

        if assertion_function(**data):
            self.logger.info(
                'assertion: %s is %s to %s',
                data['value'], operator, data['other']
            )
        else:
            self.assertion_errors.append({
                'data': data,
                'operator': operator,
                'action_data': action_data
            })

    # sub class methods

    def populate(self, entity_data, raw_entity, search_query, action):
        """Should be implemented in sub classes"""
        raise NotImplementedError()

    def validate(self, entity_data, raw_entity, search_query, action):
        """Should be implemented in sub classes"""
        raise NotImplementedError()

    def populate_modelname(self, entity_data, action_data,
                           search_query, action):
        """Example on how to implement custom populate methods
           e.g: `def populate_organization`
        This method should take care of all validations and errors.
        """

        result = (
            "Implement your own populate method here,"
            "This method should take care of `search_query`"
            "to check the existence of entity before creation"
            "and should return a valid Nailgun entity object"
            "containing a valid `id`"
        )

        # always add the result to registry to allow references
        self.add_to_registry(action_data, result)

    def validate_modelname(self, entity_data, action_data,
                           search_query, action):
        """Example on how to implement custom validate methods
           e.g: `def validate_organization`
        This method should take care of all validations and errors.
        """

        result = (
            "Implement your own validate method here,"
            "This method should use `search_query`"
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
