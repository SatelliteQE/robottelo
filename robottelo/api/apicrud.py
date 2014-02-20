# -*- encoding: utf-8 -*-

"""
Module for mixin of basic crud methods based on api_path class method.
"""

import robottelo.api.base as base

from robottelo.common.records import ManyRelatedField, RelatedField


def convert_to_data(instance):
    """Converts an instance to a data dictionary"""

    return {k: v for k, v in instance.__dict__.items()
            if (not k.startswith("_") and k != "")}


def load_from_data(cls, data, transform):
    """Loads instance attributes from a data dictionary"""
    instance = cls(CLEAN=True)
    related = {
        field.name: field for field in instance._meta.fields
        if isinstance(field, RelatedField)
        }
    data = transform(cls, data)
    for k, v in data.items():
        if k in related:
            related_class = related[k].record_class
            related_instance = load_from_data(related_class, v, transform)
            instance.__dict__[k] = related_instance
        else:
            instance.__dict__[k] = v
    return instance


def resolve_or_create_record(record):
    """On recieving record, that has api_class implemented,
    it checks if it exists and if not, creates it.
    """
    if ApiCrud.record_exists(record):
        return ApiCrud.record_resolve(record)
    else:
        return ApiCrud.record_create_recursive(record)


def data_load_transform(instance_cls, data):
    """Wraper to strip redundant keys from json """
    try:
        key = instance_cls._meta.api_class.get_json_key()
        if key in data:
            return data[key]
        return data
    except NotImplementedError:
        return data


class ApiCrud(object):
    """Defines basic crud methods based on api_path class method """

    def __init__(self):
        """Mixin is not supposed to be instantiated """
        raise NotImplementedError()

    @classmethod
    def get_default_search(cls):
        """Returns search key to be used in exists and resolve functions """
        if hasattr(cls, 'default_search'):
            return cls.default_search
        return "name"

    @classmethod
    def get_api_path(cls):
        """Stores the path to api entry point,
        allows for automatic param definition, i.e.:

        /api/compute_resources/:compute_resource_id/images

        will require compute_resource_id to be supplied in each crud call

        """

        if hasattr(cls, 'api_path'):
            return cls.api_path

        raise NotImplementedError("Api path needs to be defined")

    @classmethod
    def get_json_key(cls):
        """Stores the path to api entry point,
        allows for automatic param definition, i.e.:

        /api/compute_resources/:compute_resource_id/images

        will require compute_resource_id to be supplied in each crud call

        """

        if hasattr(cls, 'api_json_key'):
            return cls.api_json_key

        raise NotImplementedError("Api path needs to be defined")

    @classmethod
    def id_from_json(cls, json):
        """Required for automatic generating of crud tests"""
        try:
            return json[cls.get_json_key()][u'id']
        except NotImplementedError:
            return json[u'id']

    @classmethod
    def parse_path_arg(cls, args):
        """Method parsing the api_path for extra arguments"""
        path = cls.get_api_path()
        path_args = [
            s[1:] for s in path.split('/') if s.startswith(":")
        ]
        for arg in path_args:
            if arg in args:
                path = path.replace(":{0}/".format(arg), args[arg])
                del args[arg]
            else:
                raise NameError("Expecting {0} as an argument.".format(arg))
        return path

    @classmethod
    def list(cls, **kwargs):
        """"Query method,
        args are forwarded to underlying requests.get call

        """
        path = cls.parse_path_arg(kwargs)
        return base.get(path=path, **kwargs)

    @classmethod
    def show(cls, uid, **kwargs):
        """Read method,
        args are forwarded to underlying requests.get call,
        id is required

        """
        path = cls.parse_path_arg(kwargs)
        path = "{0}/{1}".format(path, uid)
        return base.get(path=path, **kwargs)

    @classmethod
    def create(cls, **kwargs):
        """Create method,
        args are forwarded to underlying requests.post call,
        json arg is usually necessary

        """
        path = cls.parse_path_arg(kwargs)
        return base.post(path=path, **kwargs)

    @classmethod
    def update(cls, uid, **kwargs):
        """Update method,
        args are forwarded to underlying requests.put call,
        id is required,
        json arg is usually necessary

        """
        path = cls.parse_path_arg(kwargs)
        path = "{0}/{1}".format(path, uid)
        return base.put(path=path, **kwargs)

    @classmethod
    def delete(cls, uid, **kwargs):
        """Remove method,
        args are forwarded to underlying requests.put call,
        id is required,
        json arg is usually necessary

        """
        path = cls.parse_path_arg(kwargs)
        path = "{0}/{1}".format(path, uid)
        return base.delete(path=path, **kwargs)

    @classmethod
    def opts(cls, data):
        """Adds redundant keys for passing as a json into rest functions"""
        try:
            return {cls.get_json_key(): data}
        except NotImplementedError:
            return data

    @classmethod
    def record_exists(cls, instance):
        """Checks if record is resolveable."""
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_exists(instance)

        if hasattr(instance, "id"):
            res = cls.show(instance.id)
            return res.ok
        else:
            res = cls.list(json=dict(search="name="+instance.name))
            if res.ok and len(res.json()) > 0:
                return True
            else:
                return False

    @classmethod
    def record_remove(cls, instance):
        """Removes record by its id, or name"""
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_remove(instance)

        if hasattr(instance, "id"):
            res = cls.delete(instance.id)
            return res.ok
        else:
            res = cls.list(json=dict(search="name="+instance.name))
            if res.ok and len(res.json()) == 1:
                cls.record_remove(cls.record_resolve(instance))
                return True
            else:
                return False

    @classmethod
    def record_resolve(cls, instance):
        """Gets information by records id, or name
        and parses it into new record
        """
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_resolve(instance)

        res = None
        json = None
        if hasattr(instance, "id"):
            res = cls.show(instance.id)
            if res.ok:
                json = res.json()
        else:
            res = cls.list(json=dict(search="name="+instance.name))
            if res.ok:
                json = res.json()[0]

        if res.ok:
            ninstance = load_from_data(
                instance.__class__,
                json,
                data_load_transform
                )
            return ninstance
        else:
            raise Exception(res.status_code,
                            res.content,
                            res.request.url,
                            res.request.body)

    @classmethod
    def record_resolve_recursive(cls, instance):
        """Gets infromation about record,
        including all of its related fields
        """
        if cls != instance._meta.api_class:
            return instance._meta.api_class \
                .record_resolve_recursive(instance)
        ninstance = cls.record_resolve(instance)
        related_fields = [
            f for f in ninstance._meta.fields
            if isinstance(f, RelatedField)
            ]
        for fld in related_fields:
            if hasattr(ninstance, (fld.name + "_id")):
                related_class = fld.record_class
                related = related_class(CLEAN=True)
                related.id = instance.__dict__[(fld.name + "_id")]
                related = cls.record_resolve(related)
                ninstance.__dict__[fld.name] = related
            elif hasattr(ninstance, fld.name):
                related = ninstance.__dict__[fld.name]
                if isinstance(related, RelatedField):
                    resolved = cls.record_resolve(related)

                    ninstance.__dict__[fld.name] = resolved
        return ninstance

    @classmethod
    def record_update(cls, instance):
        """Updates the record, doesn't touch related fields
        """
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_update(instance)

        if not hasattr(instance, "id"):
            res = cls.list(json=dict(search="name="+instance.name))
            if res.ok and len(res.json()) == 1:
                instance.id = cls.record_resolve(instance).id
            else:
                if len(res.json()) == 0:
                    raise KeyError(instance.name + " not found.")
                else:
                    raise KeyError(instance.name + " not unique.")

        data = convert_to_data(instance)
        if hasattr(cls, "create_fields"):
            data = {
                name: field for name, field in data.items()
                if name in cls.create_fields
                }

        res = cls.update(instance.id, json=cls.opts(data))
        if res.ok:
            ninstance = load_from_data(
                instance.__class__,
                res.json(),
                data_load_transform)
            return ninstance
        else:
            raise Exception(
                res.status_code,
                res.content,
                res.request.url,
                res.request.body)

    @classmethod
    def record_create(cls, instance_orig):
        """Creates the record, doesn't touch related fields
        """
        if cls != instance_orig._meta.api_class:
            api = instance_orig._meta.api_class
            return api.record_create(instance_orig)
        instance = instance_orig.copy()

        data = convert_to_data(instance)
        if hasattr(cls, "create_fields"):
            data = {
                name: field for name, field in data.items()
                if name in cls.create_fields
                }

        res = cls.create(json=cls.opts(data))
        if res.ok:
            ninstance = load_from_data(
                instance.__class__,
                res.json(),
                data_load_transform)
            return ninstance
        else:
            raise Exception(
                res.status_code,
                res.content,
                res.request.url,
                res.request.body)

    @classmethod
    def record_create_recursive(cls, instance_orig):
        """Creates the record, even related accounts
        """
        if cls != instance_orig._meta.api_class:
            api = instance_orig._meta.api_class
            return api.record_create_recursive(instance_orig)
        instance = instance_orig.copy()

        #resolve ids
        related_fields = [
            fld.name for fld in instance._meta.fields
            if isinstance(fld, RelatedField)
            ]

        for field in related_fields:
            value = resolve_or_create_record(instance.__dict__[field])
            instance.__dict__[field] = value
            instance.__dict__[field+"_id"] = value.id

        #resolve ManyRelated ids
        related_fields = [
            fld.name for fld in instance._meta.fields
            if isinstance(fld, ManyRelatedField)
            ]

        for field in related_fields:
            value = instance.__dict__[field]
            if type(value) == type(list()):
                values = [
                    resolve_or_create_record(i)
                    for i in value
                    ]
                ids = [val.id for val in values]
                instance.__dict__[field] = values
                instance.__dict__[field+"_ids"] = ids

        data = convert_to_data(instance)
        if hasattr(cls, "create_fields"):
            data = {
                name: field for name, field in data.items()
                if name in cls.create_fields
                }

        res = cls.create(json=cls.opts(data))
        if res.ok:
            ninstance = load_from_data(
                instance.__class__,
                res.json(),
                data_load_transform)
            return ninstance
        else:
            raise Exception(
                res.status_code,
                res.content,
                res.request.url,
                res.request.body)
