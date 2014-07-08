"""Standalone script that uses the robottelo.api.inspect module to generate
code suitable to help define entities in robottelo.entities module based on
the resources specified by apidoc.

"""
import os
import re
import sys
import textwrap

# check if robottelo is already in sys.path and append it if not
ROBOTTELO_PATH = os.path.realpath(
    os.path.join(os.path.dirname(__file__), os.path.pardir))
if ROBOTTELO_PATH not in sys.path:
    sys.path.append(ROBOTTELO_PATH)

from robottelo.api import inspect
from StringIO import StringIO


TAG_RE = re.compile(r'<[^>]+>')


class EntityField(object):
    """Represents a field and its type, options, description and validator.

    This class is used to generate a string representation of the field to be
    printed with the representation of ``EntityClass``.

    """
    def __init__(self, name, type_, options, description, validator):
        self.name, self.type = _get_orm_field(name, type_)
        self.options = options
        self.description = description
        self.validator = validator

    def formatted_field(self, indent=0):
        """Returns a formatted string representation of the field.

        Each line of the string will be prefixed with ``indent`` number of
        spaces.

        An example output:

        # description:  hostgroup id
        # validator: number.
        hostgroup = orm.OneToOneField(required=False, null=True)

        """
        prefix = ' ' * indent
        output = StringIO()
        if self.description:
            description = textwrap.fill(
                self.description.strip(),
                width=80,
                initial_indent='{0}# '.format(prefix),
            )
            output.write('{0}\n'.format(TAG_RE.sub('', description)))
        if self.validator:
            validator = textwrap.fill(
                self.validator,
                width=80,
                initial_indent='{0}# validator: '.format(prefix),
                subsequent_indent='{0}# '.format(prefix),
            )
            output.write('{0}\n'.format(validator))
        options = ', '.join([
            '{0}={1}'.format(key, value)
            for key, value in self.options.items()
            if value is not False  # as False is default for boolean options
        ])
        output.write('{prefix}{0} = {1}({2})\n'.format(
            self.name, self.type, options, prefix=prefix))
        field_str = output.getvalue()
        output.close()
        return field_str

    def __str__(self):
        return self.formatted_field()


class EntityClass(object):
    """Represents an entity class and is used to get a string representation
    which define a entity class for a resource.

    """
    def __init__(self, name, fields, docstring=None, meta=None):
        self.name = _get_entity_class_name(name)
        self.fields = fields
        self.docstring = docstring
        self.meta = meta

    def __str__(self):
        output = StringIO()
        output.write('class {0}(orm.Entity):\n'.format(self.name))
        if self.docstring is not None:
            output.write('"""{0}"""'.format(self.docstring))

        for field in self.fields:
            output.write(field.formatted_field(4))

        if self.meta is not None:
            output.write('\n    class Meta(object):\n')
            for meta_field, meta_value in self.meta.items():
                if isinstance(meta_value, list):
                    output.write(
                        '{prefix}{0} = (\n'.format(meta_field, prefix=' ' * 8))
                    for value in meta_value:
                        output.write(
                            '{prefix}{0}\n'.format(value, prefix=' ' * 12))
                    output.write(
                        '{prefix})\n'.format(meta_field, prefix=' ' * 8))
                else:
                    output.write('{prefix}{0} = {1}\n'.format(
                        meta_field, meta_value, prefix=' ' * 8))

        class_str = output.getvalue()
        output.close()
        return class_str


def _get_entity_class_name(name):
    """Converts a resource ``name`` to a Python class name"""
    return ''.join([part.capitalize() for part in name.split('_')])


def _get_orm_field(name, type_):
    """Returns a string representation for an orm field accordingly ``name``
    and ``type`` parameters

    """
    if name.endswith('_id'):
        name = name[:-3]
        type_ = 'orm.OneToOneField'

    if name.endswith('_ids'):
        name = name[:-4]
        type_ = 'orm.OneToManyField'

    if type_ == 'array':
        type_ = 'orm.ListField'

    if type_ == 'numeric':
        type_ = 'orm.IntegerField'

    if type_ == 'string':
        type_ = 'orm.StringField'

    return name, type_


def _get_fields(params, fields=None):
    """Recursive function that will return a list of ``EntityField`` instances

    :return: A list of ``EntityField`` instances
    :rtype: list

    """
    if fields is None:
        fields = []

    for field in params:
        if 'params' in field:
            _get_fields(field['params'], fields)
        elif field['expected_type'] != 'hash':
            fields.append(EntityField(
                field['name'],
                field['expected_type'],
                {
                    'required': field['required'],
                    'null': field['allow_nil'],
                },
                field['description'],
                field['validator'],
            ))

    return fields


def _get_meta(resource):
    """Returns a ``dict`` that maps resource's meta fields and its values

    If no meta information is found, returns ``None``.

    """
    if resource.get('apis') is not None:
        meta = {}
        meta['api_path'] = [
            "'{0[api_url]}',  # {0[short_description]}".format(api)
            for api in resource['apis']
        ]
        return meta
    else:
        return None


def main():
    """Inpects the API create info and output the generated entities classes"""
    create_info = inspect.get_resource_create_info()
    resource_names = sorted(create_info)
    entities_classes = []

    for resource_name in resource_names:
        resource = create_info[resource_name]
        entities_classes.append(str(
            EntityClass(
                resource_name,
                _get_fields(resource['params']),
                meta=_get_meta(resource),
            )
        ))

    print '\n\n'.join(entities_classes),


if __name__ == '__main__':
    main()
