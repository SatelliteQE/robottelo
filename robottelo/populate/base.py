# coding: utf-8
"""
Base module for robottelo.populate
reads the YAML definition and perform all the rendering and basic actions.
"""
import import_string
import logging

from collections import Sequence
from jinja2 import Template
from nailgun import entities
from nailgun.entity_mixins import EntitySearchMixin, EntityReadMixin
from robottelo.config import settings
from robottelo.populate import assertion_operators
from robottelo.populate.constants import (
    DEFAULT_CONFIG,
    REQUIRED_MODULES,
    RAW_SEARCH_RULES
)
from robottelo.populate.utils import set_logger, SmartDict
from six import string_types

logger = logging.getLogger(__name__)


class BasePopulator(object):
    """Base class for API and CLI populators"""

    def __init__(self, data, verbose=None, mode='populate', config=None):
        """Reads YAML and initialize populator"""
        if not settings.configured:
            settings.configure()

        self.data = data
        self.custom_config = config or {}
        self._config = None

        self.mode = mode
        self.vars = SmartDict(data.get('vars', {}))
        self.actions = data['actions']

        self.logger = logger
        set_logger(verbose or 0)

        self.registry = SmartDict()
        self.validation_errors = []
        self.assertion_errors = []
        self.created = []
        self.found = []

        self.context = {'registry': self.registry}
        self.add_modules_to_context()
        self.context.update(self.vars)

        self.load_raw_search_rules()

    @property
    def config(self):
        """Return config dynamically because it can be overwritten by
        user in datafile or by custom populator"""
        if not self._config:
            self._config = DEFAULT_CONFIG.copy()
            self._config.update(self.custom_config)
            self._config.update(self.data.get('config', {}))
        return self._config

    @property
    def crud_actions(self):
        """Return a list of crud_actions, actions that gets `data`
        and perform nailgun crud operations so custom populators can
        overwrite this list to add new crud actions."""
        return ['create', 'update', 'delete']

    def load_raw_search_rules(self):
        """Reads default search rules then update first with
        custom populator defined rules and then user defined in datafile.
        """
        self.search_rules = RAW_SEARCH_RULES
        self.search_rules.update(self.raw_search_rules)
        self.search_rules.update(self.config.get('raw_search_rules') or {})

        self.force_raw_search = [
            entity for entity, data in self.search_rules.items()
            if data.get('_force_raw') is True
        ]

    def add_modules_to_context(self):
        """Add modules dynamically to render context"""
        modules_to_add = self.config.get('add_to_context', {})
        modules_to_add.update(REQUIRED_MODULES)
        for name, module in modules_to_add.items():
            self.context[name] = import_string(module)

    def add_to_registry(self, action_data, result):
        """Add objects to the internal registry"""
        if not action_data.get('register', action_data.get('registry')):
            return

        registry_key = Template(
            action_data.get('register', action_data.get('registry'))
        ).render(**self.context)

        if action_data.get('with_items'):
            if registry_key in self.registry:
                self.registry[registry_key].append(result)
                self.logger.info("registry: %s eppended", registry_key)
            else:
                self.registry[registry_key] = [result]
                self.logger.info("registry: %s registered", registry_key)
        else:
            self.registry[registry_key] = result
            self.logger.info("registry: %s registered", registry_key)

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
            self.logger.info(
                "search: getting entities in %s with options %s",
                model_name,
                options
            )
            search_result = model().search(**options)

        silent_errors = action_data.get('silent_errors', False)

        if not search_result:
            self.logger.error("search: returned no objects %s", action_data)
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
                        if isinstance(v['from_registry'], dict):
                            result = eval(
                                v['from_registry']['name'], None, context
                            )
                            self.resolve_result_attr(
                                data, 'from_registry', k, v, result
                            )
                        else:
                            data[k] = eval(v['from_registry'], None, context)

                    except NameError as e:
                        logger.error(str(e))
                        raise NameError(
                            "{0}: Please check if the reference "
                            "was added to the registry".format(str(e)))
                elif 'from_object' in v:
                    try:
                        if isinstance(v['from_object'], dict):
                            result = import_string(v['from_object']['name'])
                            self.resolve_result_attr(
                                data, 'from_object', k, v, result
                            )
                        else:
                            data[k] = import_string(v['from_object'])
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
        # args = v[from_where].get('args')
        # keys = v[from_where].get('keys')

        # TODO: implement this ^^^^

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

        # TODO: validate required keys marshmallow? voluptuous?
        # if action not in ('delete', 'assertion') and 'data' not
        # in action_data:
        #     raise ValueError('entity misses `data` key')

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

        - data
          Dictionary of parsed entity_data to be used to instantiate an object
          to searched without raw_query.

        - options
          if `search_options` are specified it is passed to
          `.search(**options)`

        - searchable
          Returns boolean True if model inherits from EntitySearchMixin, else
          alternative search must be implemented.

        if `search_query` is available in action_data it will be used instead
        of entity_data.
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

        rules = self.search_rules.get(action_data['model'].lower())
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
            '{0}="{1}"'.format(k, v) for k, v in search_data.items()
        ]
        raw_query = ",".join(query_items)
        return {'search': raw_query or None}

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
        ) or action_data['model'].lower() in self.force_raw_search

        if force_raw:
            options['query'] = self.build_raw_query(data, action_data)

        per_page = options.pop('per_page', None)
        if per_page:
            if 'query' in options:
                options['query']['per_page'] = per_page
            else:
                options['query'] = {'per_page': per_page}

        return options

    def get_search_result(self, model, search, unique=False,
                          silent_errors=False):
        """Perform a search"""
        if not search['searchable']:
            self.logger.error('search: %s not searchable', model.__name__)
            if silent_errors:
                return
            raise TypeError("{0} not searchable".format(model.__name__))

        result = model(**search['data']).search(**search['options'])

        options_to_log = search['options'] or {
            k: getattr(v, 'id', v) for k, v in search['data'].items()
        }

        if not result:
            self.logger.info(
                "search: %s %s returned empty result",
                model.__name__,
                options_to_log
            )
            return

        if unique:
            if len(result) > 1:
                self.logger.error(
                    "search: %s %s is not unique",
                    model.__name__,
                    options_to_log
                )
                self.logger.debug(result)
                if not silent_errors:
                    raise RuntimeError(
                        "More than 1 item returned "
                        "search is not unique"
                    )

            self.logger.info(
                "search: %s %s found unique item",
                model.__name__,
                options_to_log,
            )
            return result[0]

        self.logger.info(
            "search: %s %s found %s items",
            model.__name__,
            options_to_log,
            len(result)
        )
        return result

    def execute(self, mode=None):
        """Iterates the entities property described in YAML file
        and parses its values, variables and substitutions
        depending on `mode` execute `populate` or `validate`
        """
        mode = mode or self.mode
        for action_data in self.actions:
            action = action_data.get('action', 'create')

            if action_data.get('when'):
                if not eval(action_data.get('when'), None, self.context):
                    continue

            log_message = action_data['log_message'] = Template(
                action_data.get(
                    'log', action_data.get('register', 'executing...')
                )
            ).render(**self.context)

            getattr(self.logger, action_data.get('level', 'info').lower())(
                '%s: %s',
                action.upper() if not (
                    mode == 'validate' and action == 'create'
                ) else "VALIDATE",
                log_message
            )

            entities_list = self.render(action_data, action)
            for entity_data in entities_list:
                if action not in self.crud_actions:
                    # find the method named as action_name
                    action_name = "action_{0}".format(action.lower())
                    getattr(self, action_name)(entity_data, action_data)

                    self.context.update(self.registry)

                    # execute above method and continue to next item
                    continue

                # Executed only for crud_actions
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

    def action_unregister(self, entity_data, action_data):
        """Remove data from registry"""
        for value in entity_data['_values']:
            if self.registry.pop(value, None):
                self.logger.info("unregister: %s OK", value)
            else:
                self.logger.error("unregister: %s IS NOT REGISTERED", value)

    def action_register(self, entity_data, action_data):
        """Register arbitrary items to the registry"""
        entity_data.pop('loop_index', 0)
        for key, value in entity_data.items():
            data = action_data.copy()
            data['register'] = key
            self.add_to_registry(data, value)

    def action_assertion(self, entity_data, action_data):
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

        assertion_result = assertion_function(**data)
        if assertion_result:
            self.logger.info(
                'assertion: %s is %s to %s',
                data['value'], operator, data['other']
            )
        else:
            self.logger.error(
                'assertion: %s is NOT %s to %s',
                data['value'], operator, data['other']
            )
            self.assertion_errors.append({
                'data': data,
                'operator': operator,
                'action_data': action_data
            })
        self.add_to_registry(action_data, assertion_result)

    def action_echo(self, entity_data, action_data):
        """After message is echoed to log, check if needs print"""
        if action_data.get('print'):
            print(action_data.get('log_message'))  # noqa

    # sub class methods

    @property
    def raw_search_rules(self):
        """Subclasses of custom populators can extend this rules"""
        return {}

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
        e.g:: `def validate_organization`
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
            'entity_data': entity_data,
            'action_data': action_data
        })
