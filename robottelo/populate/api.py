
from robottelo.populate.base import BasePopulator
from nailgun import entities


class APIPopulator(BasePopulator):
    """Populates system using API/Nailgun"""

    def populate(self):
        """reads the list of entities and populates the
        system"""

        for raw_entity in self.entities:
            entities_list = self.render_entities(raw_entity)
            for entity_data in entities_list:
                model_name = raw_entity['model'].lower()
                method = getattr(self, 'populate_{0}'.format(model_name), None)
                if method:
                    result = method(**entity_data)
                else:
                    result = getattr(
                        entities, raw_entity['model']
                    )(**entity_data).create()

                self.add_to_registry(raw_entity, result)
