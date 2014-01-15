# -*- encoding: utf-8 -*-

"""
Module for mixin of basic crud methods based on api_path class method.
"""

import robottelo.api.base as base
from robottelo.common.models.fields import load_from_data, convert_to_data
from robottelo.common.models.fields import RecordField
from inspect import getmro

class ApiCrudMixin(object):
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

        if hasattr(instance,"id"):
            r = EnvironmentApi.show(instance.id)
            return r.ok
        else:
            r = cls.list(json=dict(search="name="+instance.name))
            if r.ok and len(r.json())>0:
                return True
            else:
                return False

    @classmethod
    def record_resolve(cls, instance):
        if cls != instance._meta.api_class:
            return instance._meta.api_class.record_resolve(instance)

        if hasattr(instance,"id"):
            r = cls.show(instance.id)
            if r.ok:
                nself = instance.copy()
                instance = load_from_data(nself,r.json()[cls.get_json_key()])
                return nself
            else:
                raise Exception(r.status_code, r.content)
        else:
            r = cls.list(json=dict(search="name="+instance.name))
            if r.ok:
                nself = instance.copy()
                instance = load_from_data(nself,r.json()[0][cls.get_json_key()])
                return nself
            else:
                raise Exception(r.status_code, r.content)


    @classmethod
    def record_create(cls,instance):
        if cls != instance._meta.api_class:
            return instance._meta.api_class.record_create(instance)

        #resolve ids
        data_instance = convert_to_data(instance)
        resolvable_fields = [f.name for f in instance._meta.fields if isinstance(f,RecordField) ]

        for field in resolvable_fields:
            value = instance.__dict__[field]
            if ApiCrudMixin.record_exists(value):
               value = ApiCrudMixin.record_resolve(value)
            else:
               value = ApiCrudMixin.record_create(value)
            instance.__dict__[field] = value
            instance.__dict__[field+"_id"] = value.id

        data = convert_to_data(instance)
        print data
        if hasattr(cls,"create_fields"):
           data = {name:field for name, field in data.items() if name in cls.create_fields}

        print data

        r = cls.create(json=cls.opts(data))
        if r.ok:
            nself = instance.copy()
            instance = load_from_data(nself,r.json()[cls.get_json_key()])
            return nself
        else:
            raise Exception(r.status_code, r.content)
