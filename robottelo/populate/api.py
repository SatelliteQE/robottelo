"""Implements API populator"""
from robottelo.populate.base import BasePopulator
from nailgun import entities
from requests.exceptions import HTTPError


class APIPopulator(BasePopulator):
    """Populates system using API/Nailgun"""

    def populate(self, entity_data, raw_entity, search_data):
        """Populates the System using Nailgun
        threats and logs Exceptions
        takes care of adding valid entity to the registry
        """
        print "SEARCH", search_data

        model = getattr(entities, raw_entity['model'])

        try:
            # 1) check if entity already exists
            search_result = model().search(**search_data)
            if search_result:
                if len(search_result) > 1:
                    self.logger.info(search_result)
                    raise RuntimeError(
                        "More than 1 item returned "
                        "validate_fields query is not unique"
                    )
                # existent entity should be unique, so it is the first
                # item in search_result
                result = search_result[0]
            else:
                result = model(**entity_data).create()
        except HTTPError as e:
            self.logger.error(str(e))
            if hasattr(e, 'response'):
                self.logger.info(e.response.content)
        else:
            self.add_to_registry(raw_entity, result)
