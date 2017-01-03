# coding: utf-8
"""Implements API populator using Nailgun"""
from nailgun import entities
from nailgun.entity_mixins import EntitySearchMixin
from requests.exceptions import HTTPError
from robottelo.populate.base import BasePopulator


class APIPopulator(BasePopulator):
    """Populates system using API/Nailgun"""

    def populate(self, entity_data, action_data, search, action):
        """Populates the System using Nailgun
        based on value provided in `action` argument gets the
        proper CRUD method to execute dynamically
        """
        model = getattr(entities, action_data['model'])
        silent_errors = action_data.get('silent_errors', False)

        try:
            # self.create|update|delete
            result = getattr(self, action)(
                entity_data, action_data, search, model, silent_errors
            )
        except HTTPError as e:
            self.logger.error(str(e))
            if hasattr(e, 'response'):
                self.logger.info(e.response.content)
        except Exception:
            if silent_errors:
                return
            raise
        else:
            self.add_to_registry(action_data, result)

    def create(self, entity_data, action_data, search, model, silent_errors):
        """Creates new entity if does not exists or get existing
        entity and return Entity object"""
        result = self.get_search_result(
            model, search, unique=True, silent_errors=silent_errors
        )
        if result:
            self.total_existing += 1
        else:
            result = model(**entity_data).create()
            self.total_created += 1
        return result

    def update(self, entity_data, action_data, search, model, silent_errors):
        """Updates an existing entity"""

        search_data = action_data.get('search_query')
        entity_id = action_data.get('id')

        if not entity_id and not search_data:
            raise RuntimeError("update: missing id or search_query")

        if not entity_id:
            search_result = self.get_search_result(
                model, search, unique=True, silent_errors=silent_errors
            )
            if not search_result:
                raise RuntimeError("update: Cannot find entity")

            entity_id = search_result.id

        entity = model(id=entity_id, **entity_data)
        entity.update(entity_data.keys())
        return entity

    def delete(self, entity_data, action_data, search, model, silent_errors):
        """Deletes an existing entity"""

        search_data = action_data.get('search_query')
        entity_id = action_data.get('id')

        if not entity_id and not search_data:
            raise RuntimeError("delete: missing id or search_query")

        if not entity_id:
            search_result = self.get_search_result(
                model, search, unique=True, silent_errors=silent_errors
            )
            if not search_result:
                raise RuntimeError("delete: Cannot find entity")

            entity_id = search_result.id

        # currently only works based on a single id
        # should iterate all results and delete one by one?
        model(id=entity_id).delete()

    def validate(self, entity_data, action_data, search, action):
        """Based on action fields or using action_data['search_query']
        searches the system and validates the existence of all entities
        """
        silent_errors = action_data.get('silent_errors', False)
        if action not in ['create', 'assertion'] or action_data.get(
                'skip_validation'):
            # validate only create and assertion crud actions
            return

        model = getattr(entities, action_data['model'])

        if not issubclass(model, EntitySearchMixin):
            raise TypeError("{0} not searchable".format(model))

        try:
            # 1) check if entity exists
            result = self.get_search_result(
                model, search, unique=True, silent_errors=silent_errors
            )
            if result:
                self.total_existing += 1
            else:
                result = None
        except HTTPError as e:
            error_message = str(e)
            if hasattr(e, 'response'):
                error_message += e.response.content
            self.logger.error(error_message)
            self.validation_errors.append({
                'search': search,
                'message': error_message,
                'entity_data':  entity_data,
                'action_data': action_data
            })
        else:
            if result:
                self.add_to_registry(action_data, result)
            else:
                # should add None to registry, else references fail
                self.add_to_registry(action_data, None)
                self.validation_errors.append({
                    'search': search,
                    'message': 'entity does not exist in the system',
                    'entity_data':  entity_data,
                    'action_data': action_data
                })
