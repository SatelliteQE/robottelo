"""Factories for building and creating Foreman entities.

Each class in this module is a factory for creating a single type of entity.
For example, :class:`robottelo.factories.ModelFactory` is a factory for
building and creating "Model" entities and
:class:`robottelo.factories.HostFactory` is a factory for building and creating
"Host" entities.

For examples of factory usage, see :mod:`tests.foreman.api.test_model_v2`.

"""
from robottelo import entities, orm
from robottelo.factory import Factory, field_is_required


class HostFactory(Factory):
    """Factory for a "Host" entity."""
    def _get_path(self):
        """Return a path for creating a "Host" entity."""
        return 'api/v2/hosts'

    def _get_fields(self):
        """Return a "Host" entity's field names and values."""
        return {'name': orm.StringField().get_value()}

    def _get_field_names(self, fmt):
        """Return alternate field names for a "Host"."""
        if fmt == 'api':
            return (('name', 'host[name]'),)
        return tuple()


class ModelFactory(Factory):
    """Factory for a "Model" entity."""
    def _get_path(self):
        """Return a path for creating a "Model" entity."""
        return 'api/v2/models'

    def _get_fields(self):
        """Return a "Model" entity's field names and values."""
        values = {}
        for name, field in entities.Model.get_fields().items():
            if field_is_required(field):
                values[name] = field.get_value()
        return values

    def _get_field_names(self, fmt):
        """Return alternate field names for a "Model"."""
        if fmt == 'api':
            return entities.Model.Meta.api_names
        return tuple()

    def _unpack_response(self, response):
        """Unpack the server's response after creating an entity."""
        return response['model']


class OrganizationFactory(Factory):
    """Factory for a "Organization" entity."""
    def _get_path(self):
        """Return a path for creating an "Organization" entity."""
        return 'api/v2/organizations'

    def _get_fields(self):
        """Return an "Organization" entity's field names and values."""
        return {'name': orm.StringField().get_value()}


class ProductFactory(Factory):
    """Factory for a "Product" entity."""
    def _get_path(self):
        """Return a path for creating a "Product" entity."""
        return 'api/v2/products'

    def _get_fields(self):
        """Return a "Product" entity's field names and values."""
        return {
            'name': orm.StringField().get_value(),
            'organization_id': OrganizationFactory(),
        }
