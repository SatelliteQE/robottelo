# -*- encoding: utf-8 -*-

"""
Module for mixin of basic crud methods based on api_path class method.
"""

import robottelo.api.base as base

from robottelo.common.records.fields import RelatedField
from robottelo.common.records.fields import load_from_data, convert_to_data
from robottelo.common.records.fields import RelatedField
from robottelo.common.records.fields import ManyRelatedFields
from inspect import getmro

def resolve_or_create_record(record):
    if ApiCrud.record_exists(record):
       return ApiCrud.record_resolve(record)
    else:
       return ApiCrud.record_create_recursive(record)


def data_load_transform(instance_cls, data):
   key = instance_cls._meta.api_class.api_json_key
   if key in data:
       return data[key]
   return data

class ApiCrud(object):
    """Defines basic crud methods based on api_path class method """

    def __init__(self):
        """Mixin is not supposed to be instantiated """
        raise NotImplementedError()

    @classmethod
    def get_default_search(cls):
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
        return json[cls.get_json_key()][u'id']

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
        return {cls.get_json_key(): data}

    @classmethod
    def record_exists(cls, instance):
        if cls != instance._meta.api_class:
            return instance._meta.api_class.record_exists(instance)

        if hasattr(instance, "id"):
            r = cls.show(instance.id)
            return r.ok
        else:
            r = cls.list(json=dict(search="name="+instance.name))
            if r.ok and len(r.json()) > 0:
                return True
            else:
                return False

    @classmethod
    def record_remove(cls, instance):
        if cls != instance._meta.api_class:
            return instance._meta.api_class.record_remove(instance)

        if hasattr(instance,"id"):
            r = cls.delete(instance.id)
            return r.ok
        else:
            r = cls.list(json=dict(search="name="+instance.name))
            if r.ok and len(r.json())==1:
                cls.record_remove(cls.record_resolve(instance))
                return True
            else:
                return False

    @classmethod
    def record_resolve(cls, instance):
        if cls != instance._meta.api_class:
            return instance._meta.api_class.record_resolve(instance)

        r = None
        json = None
        if hasattr(instance,"id"):
            r = cls.show(instance.id)
            if r.ok:
                json = r.json()
        else:
            r = cls.list(json=dict(search="name="+instance.name))
            if r.ok:
                json = r.json()[0]

        if r.ok:
            ninstance = load_from_data(instance.__class__, json, data_load_transform)
            return ninstance
        else:
            raise Exception(r.status_code, r.content)

    @classmethod
    def record_resolve_recursive(cls, instance):
        if cls != instance._meta.api_class:
            return instance._meta.api_class.record_resolve_recursive(instance)
        ninstance = cls.record_resolve(instance)
        related_fields = [f for f in ninstance._meta.fields if isinstance(f, RelatedField) ]
        for f in related_fields:
            if hasattr(ninstance,(f.name + "_id")):
                related_class = f.record_class
                related_instance = related_class(CLEAN=True )
                related_instance.id = instance.__dict__[(f.name + "_id")]
                related_instance = cls.record_resolve(related_instance)
                ninstance.__dict__[f.name] = related_instance
            elif hasattr(ninstance , f.name) :
                related_instance = ninstance.__dict__[f.name]
                if isinstance(related_instance,RelatedField):
                    ninstance.__dict__[f.name] = cls.record_resolve(related_instance)
        return ninstance

    @classmethod
    def record_update(cls, instance):
        if cls != instance._meta.api_class:
            return instance._meta.api_class.record_update(instance)

        if not hasattr(instance,"id"):
            r = cls.list(json=dict(search="name="+instance.name))
            if r.ok and len(r.json())==1:
                instance.id = cls.record_resolve(instance).id
            else:
                if len(r.json())==0:
                    raise KeyError(instance.name + " not found.")
                else:
                    raise KeyError(instance.name + " not unique.")

        data = convert_to_data(instance)
        if hasattr(cls,"create_fields"):
           data = {name:field for name, field in data.items() if name in cls.create_fields}

        r = cls.update(instance.id, json=cls.opts(data))
        if r.ok:
            ninstance = load_from_data(instance.__class__, r.json(), data_load_transform)
            return ninstance
        else:
            raise Exception(r.status_code, r.content)

    @classmethod
    def record_create(cls, instance_orig):
        if cls != instance_orig._meta.api_class:
            return instance_orig._meta.api_class.record_create(instance_orig)
        instance = instance_orig.copy()

        data = convert_to_data(instance)
        if hasattr(cls,"create_fields"):
           data = {name:field for name, field in data.items() if name in cls.create_fields}


        r = cls.create(json=cls.opts(data))
        if r.ok:
            ninstance = load_from_data(instance.__class__, r.json(), data_load_transform)
            return ninstance
        else:
            raise Exception(r.status_code, r.content)

    @classmethod
    def record_create_recursive(cls, instance_orig):
        if cls != instance_orig._meta.api_class:
            return instance_orig._meta.api_class.record_create_recursive(instance_orig)
        instance = instance_orig.copy()

        #resolve ids
        related_fields = [f.name for f in instance._meta.fields if isinstance(f, RelatedField) ]

        for field in related_fields:
            value = resolve_or_create_record(instance.__dict__[field])
            instance.__dict__[field] = value
            instance.__dict__[field+"_id"] = value.id

        #resolve ManyRelated ids
        related_fields = [f.name for f in instance._meta.fields if isinstance(f, ManyRelatedFields) ]

        for field in related_fields:
            value = instance.__dict__[field]
            if type(value) == type(list()):
                values = [resolve_or_create_record(i)
                            for i in value]
                ids = [val.id for val in values]
                instance.__dict__[field] = values
                instance.__dict__[field+"_ids"] = ids


        data = convert_to_data(instance)
        if hasattr(cls,"create_fields"):
           data = {name:field for name, field in data.items() if name in cls.create_fields}


        r = cls.create(json=cls.opts(data))
        if r.ok:
            ninstance = load_from_data(instance.__class__, r.json(), data_load_transform)
            return ninstance
        else:
            raise Exception(r.status_code, r.content)
