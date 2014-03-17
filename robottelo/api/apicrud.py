# -*- encoding: utf-8 -*-

"""
Module for mixin of basic crud methods based on api_path class method.
"""

import robottelo.api.base as base

from robottelo.common.records import ManyRelatedField, RelatedField


class ApiException(Exception):
    pass


def load_from_data(cls, data, transform):
    """Loads instance attributes from a data dictionary"""

    instance = cls(blank_record=True)
    related = {
        field.name: field for field in instance._meta.fields
        if isinstance(field, RelatedField)
        }
    data = transform(cls, data)
    for k, v in data.items():
        if k in related and type(v) is dict:
            related_class = related[k].record_class
            related_instance = load_from_data(related_class, v, transform)
            instance[k] = related_instance
        elif isinstance(v, basestring):
            instance[k] = v
        else:
            instance[k] = v
    return instance


def resolve_path_arg(arg, data):
    """Required to add support for path arguments taking from related fields,
    simple traversal based on the arg string of the data structure.

    >>> resolve_path_arg("org.env.label",{"name":"asd","env":{"label":"env0"}})
    "env0"

    """
    if "." in arg:
        arg_path = arg.split(".", 1)
        return resolve_path_arg(
            arg_path[1],
            data[arg_path[0]])
    return data[arg]


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


def default_data_transform(instance_cls, data):
    return data


class ApiCrud(object):
    """Defines basic crud methods based on api_path class method """

    def __init__(self):
        """Mixin is not supposed to be instantiated """
        raise NotImplementedError()

    # Either true, or list of fields to filter by
    create_fields = True

    @classmethod
    def get_api_path(cls):
        """Stores the path to api entry point,
        allows for automatic param definition, i.e.:

        /api/compute_resources/:compute_resource_id/images

        will require compute_resource_id to be supplied in each crud call

        """

        if hasattr(cls, 'api_path'):
            return cls.api_path  # pylint: disable=E1101

        raise NotImplementedError("Api path needs to be defined")

    @classmethod
    def get_json_key(cls):
        """Stores the path to api entry point,
        allows for automatic param definition, i.e.:

        /api/compute_resources/:compute_resource_id/images

        will require compute_resource_id to be supplied in each crud call

        """

        if hasattr(cls, 'api_json_key'):
            return cls.api_json_key  # pylint: disable=E1101

        raise NotImplementedError("Api path needs to be defined")

    @classmethod
    def id_from_json(cls, json):
        """Required for automatic generating of crud tests"""
        try:
            return json[cls.get_json_key()][u'id']
        except NotImplementedError:
            return json[u'id']

    @classmethod
    def list_path_args(cls):
        """Lists all path arguments

        >>> class TestApi(ApiCrud):
        ...     api_path = "/api/org/:org.label/test/:id"
        ...
        >>> TestApi.list_path_args()
        ['org.label','id']
        """
        path = cls.get_api_path()
        return [
            s[1:] for s in path.split('/') if s.startswith(":")
        ]

    @classmethod
    def parse_path_arg(cls, args):
        """Method parsing the api_path for extra arguments

        >>> class TestApi(ApiCrud):
        ...     api_path = "/api/org/:org.label/test/:id"
        ...
        >>> TestApi.parse_path_arg({'org.label':"org123","id":"456"})
        '/api/org/org123/test/456'
        """
        path_args = cls.list_path_args()
        path = cls.get_api_path()
        for arg in path_args:
            if arg in args:
                path = path.replace(":{0}".format(arg), str(args[arg]))
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

        if "id" in instance:
            res = cls.show(instance.id)
            return res.ok
        else:
            try:
                res = cls.list(json=dict(search="name="+instance.name))
            except NameError:
                return False

            #TODO better separete kattelo and formam api
            if res.ok:
                if "results" in res.json():
                    return len(res.json()["results"]) > 0
                return len(res.json()) > 0
            else:
                return False

    @classmethod
    def record_remove(cls, instance):
        """Removes record by its id, or name"""
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_remove(instance)

        if "id" in instance:
            res = cls.delete(instance.id)
            if res.ok:
                return True
            else:
                raise ApiException("Unable to remove", instance)
            return res.ok
        else:
            res = cls.list(json=dict(search="name="+instance.name))
            if res.ok and len(res.json()) == 1:
                res = cls.record_remove(cls.record_resolve(instance))
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

        if not cls.record_exists(instance):
            raise ApiException("Record doesn't exist")

        res = None
        json = None
        if "id" in instance:
            res = cls.show(instance.id)
            if res.ok:
                json = res.json()
        else:
            res = cls.list(json=dict(search="name="+instance.name))
            if res.ok:
                #TODO better separete kattelo and formam api
                if "results" in res.json():
                    json = res.json()["results"][0]
                else:
                    json = res.json()[0]

        if res.ok and json:
            ninstance = load_from_data(
                instance.__class__,
                json,
                data_load_transform
                )
            return ninstance
        else:
            raise ApiException("Couldn't resolve record", instance)

    @classmethod
    def record_list(cls, instance):
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_list(instance)
        counting_response = cls.list()
        if counting_response.ok:
            count = int(counting_response.json()["total"])
            if count > 0:
                listing_response = cls.list(json=dict(per_page=count))
                if listing_response.ok:
                    return [load_from_data(
                        instance.__class__,
                        js,
                        default_data_transform
                        ) for js in listing_response.json()["results"]
                        ]

    @classmethod
    def record_resolve_recursive(cls, instance):
        """Gets infromation about record,
        including all of its related fields
        """
        if cls != instance._meta.api_class:
            return instance._meta.api_class \
                .record_resolve_recursive(instance)
        ninstance = cls.record_resolve(instance)
        related_fields = ninstance._meta.fields.items(cls=RelatedField)
        for fld in related_fields:
            if fld.name + "_id" in ninstance:
                related_class = fld.record_class
                related = related_class(
                    blank_record=True,
                    id=ninstance[(fld.name + "_id")]
                    )
                ninstance[fld.name] = cls.record_resolve(related)
            elif fld.name in ninstance:
                related = ninstance[fld.name]
                if isinstance(related, RelatedField):
                    resolved = cls.record_resolve(related)
                    ninstance[fld.name] = resolved
        return ninstance

    @classmethod
    def record_update(cls, instance):
        """Updates the record, doesn't touch related fields
        """
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_update(instance)

        if not "id" in instance:
            res = cls.list(json=dict(search="name="+instance.name))
            if res.ok and len(res.json()) == 1:
                instance.id = cls.record_resolve(instance).id
            else:
                if len(res.json()) == 0:
                    raise KeyError(instance.name + " not found.")
                else:
                    raise KeyError(instance.name + " not unique.")

        data = {
            name: field for name, field in instance.items()
            if cls.create_fields is []
            or name in cls.create_fields
            }

        res = cls.update(instance.id, json=cls.opts(data))
        if res.ok:
            ninstance = load_from_data(
                instance.__class__,
                res.json(),
                data_load_transform)
            return ninstance
        else:
            raise ApiException("Couldn't update record", instance)

    @classmethod
    def record_create(cls, instance_orig):
        """Creates the record, doesn't touch related fields
        """
        if cls != instance_orig._meta.api_class:
            api = instance_orig._meta.api_class
            return api.record_create(instance_orig)
        instance = instance_orig.copy()

        path_args = {
            k: resolve_path_arg(k, instance) for k in cls.list_path_args()
            }

        data = {
            name: field for name, field in instance.items()
            if cls.create_fields == [] or name in cls.create_fields
            }

        res = cls.create(json=cls.opts(data), **path_args)
        if res.ok:
            ninstance = load_from_data(
                instance.__class__,
                res.json(),
                data_load_transform)
            return ninstance
        else:
            raise ApiException("Couldn't create record", instance)

    @classmethod
    def record_create_dependencies(cls, instance_orig):
        """Ensures that all related fields of the record do exist
        resolves them and adds their ids to instance.
        """
        if cls != instance_orig._meta.api_class:
            api = instance_orig._meta.api_class
            return api.record_create_dependencies(instance_orig)
        instance = instance_orig.copy()

        #resolve ids
        related_fields = instance._meta.fields.keys(cls=RelatedField)

        for field in related_fields:
            value = resolve_or_create_record(instance[field])
            instance[field] = value
            instance[field+"_id"] = value.id

        #resolve ManyRelated ids
        related_fields = instance._meta.fields.keys(cls=ManyRelatedField)

        for field in related_fields:
            value = instance[field]
            if type(value) == type(list()):
                values = [
                    resolve_or_create_record(i)
                    for i in value
                    ]
                ids = [val.id for val in values]
                instance[field] = values
                instance[field+"_ids"] = ids
        return instance

    @classmethod
    def record_create_recursive(cls, instance_orig):
        """Creates the record, even related fields
        """
        if cls != instance_orig._meta.api_class:
            api = instance_orig._meta.api_class
            return api.record_create_recursive(instance_orig)
        res_instance = cls.record_create_dependencies(instance_orig)
        return cls.record_create(res_instance)
