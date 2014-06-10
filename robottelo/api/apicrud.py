# -*- encoding: utf-8 -*-

"""
Module for mixin of basic crud methods based on api_path class method.
"""

import robottelo.api.base as base

from robottelo.common.helpers import sleep_for_seconds
from robottelo.common.records import ManyRelatedField, RelatedField


def response_string(result):
    return "%s \n %s" % (
        result.status_code,
        result.content,
        )


class ApiException(Exception):

    def __init__(self, message, entity=None, request=None):
        super(ApiException, self).__init__(self, message)
        self.entity = entity
        self.request = request

    def __str__(self):
        out = self.message

        if self.entity is not None:
            out = "%s : %s" % (
                out, self.entity)

        if self.request is not None:
            out = "%s \n\n python: %s \n\n bash: %s \n\n %s" % (
                out,
                self.request.request_command,
                self.request.curl_command,
                response_string(self.request))
        return out


def load_from_data(cls, data, transform):
    """Loads instance attributes from a data dictionary"""

    instance = cls(blank_record=True)
    related = dict(
        (field.name, field) for field in instance._meta.fields
        if isinstance(field, RelatedField)
        )
    data = transform(cls, data)
    for key, value in data.items():
        if key in related and isinstance(value, dict):
            related_class = related[key].record_class
            related_instance = load_from_data(related_class, value, transform)
            instance[key] = related_instance
        elif isinstance(value, basestring):
            instance[key] = value
        else:
            instance[key] = value
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


def resolve_or_create_record(record, user=None):
    """On recieving record, that has api_class implemented,
    it checks if it exists and if not, creates it.
    """
    if ApiCrud.record_exists(record, user=user):
        return ApiCrud.record_resolve(record, user=user)
    else:
        return ApiCrud.record_create_recursive(record, user=user)


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
    update_fields = []

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
    def list_path_args(cls, _path=None):
        """Lists all path arguments

        >>> class TestApi(ApiCrud):
        ...     api_path = "/api/org/:org.label/test/:id"
        ...
        >>> TestApi.list_path_args()
        ['org.label','id']
        """
        path = cls.get_api_path()
        if _path is not None:
            path = _path
        return [
            s[1:] for s in path.split('/') if s.startswith(":")
        ]

    @classmethod
    def search_dict(cls, instance):
        return dict(search="name=%s" % instance.name)

    @classmethod
    def parse_path_arg(cls, path, args):
        """Method parsing the api_path for extra arguments

        >>> class TestApi(ApiCrud):
        ...     api_path = "/api/org/:org.label/test/:id"
        ...
        >>> TestApi.parse_path_arg({'org.label':"org123","id":"456"})
        '/api/org/org123/test/456'
        """
        path_args = cls.list_path_args(path)
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

        path = cls.parse_path_arg(cls.get_api_path(), kwargs)
        if hasattr(cls, 'api_path_get'):
            path = cls.parse_path_arg(
                cls.api_path_get, kwargs)  # pylint: disable=E1101
        return base.get(path=path, **kwargs)

    @classmethod
    def show(cls, uid, **kwargs):
        """Read method,
        args are forwarded to underlying requests.get call,
        id is required

        """
        path = cls.parse_path_arg(cls.get_api_path(), kwargs)
        if hasattr(cls, 'api_path_get'):
            path = cls.parse_path_arg(
                cls.api_path_get, kwargs)  # pylint: disable=E1101
        path = "{0}/{1}".format(path, uid)
        return base.get(path=path, **kwargs)

    @classmethod
    def create(cls, **kwargs):
        """Create method,
        args are forwarded to underlying requests.post call,
        json arg is usually necessary

        """
        path = cls.parse_path_arg(cls.get_api_path(), kwargs)

        return base.post(path=path, **kwargs)

    @classmethod
    def update(cls, uid, **kwargs):
        """Update method,
        args are forwarded to underlying requests.put call,
        id is required,
        json arg is usually necessary

        """
        path = cls.parse_path_arg(cls.get_api_path(), kwargs)
        if hasattr(cls, 'api_path_put'):
            path = cls.parse_path_arg(
                cls.api_path_put, kwargs)  # pylint: disable=E1101
        path = "{0}/{1}".format(path, uid)
        return base.put(path=path, **kwargs)

    @classmethod
    def delete(cls, uid, **kwargs):
        """Remove method,
        args are forwarded to underlying requests.put call,
        id is required,
        json arg is usually necessary

        """
        path = cls.parse_path_arg(cls.get_api_path(), kwargs)
        if hasattr(cls, 'api_path_delete'):
            path = cls.parse_path_arg(
                cls.api_path_delete, kwargs)  # pylint: disable=E1101
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
    def record_exists(cls, instance, user=None):
        """Checks if record is resolveable."""
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_exists(instance, user=user)

        path_args = dict(
            (k, resolve_path_arg(k, instance)) for k in cls.list_path_args()
        )

        if "id" in instance:
            res = cls.show(instance.id, user=user, **path_args)
            return res.ok
        else:
            try:
                res = cls.list(
                    json=cls.search_dict(instance),
                    user=user,
                    **path_args)
            except NameError:
                return False

            # TODO better separete kattelo and formam api
            if res.ok:
                if "results" in res.json():
                    return len(res.json()["results"]) > 0
                return len(res.json()) > 0
            else:
                return False

    @classmethod
    def record_remove(cls, instance, user=None):
        """Removes record by its id, or name"""
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_remove(instance, user=user)

        path_args = dict(
            (k, resolve_path_arg(k, instance)) for k in cls.list_path_args()
            )

        if "id" in instance:
            res = cls.delete(instance.id, user=user, **path_args)
            if res.ok:
                return True
            else:
                raise ApiException(
                    "Unable to remove", instance,
                    res)
            return res.ok
        else:
            res = cls.list(
                json=cls.search_dict(instance),
                user=user,
                **path_args)
            if res.ok and len(res.json()) == 1:
                res = cls.record_remove(
                    cls.record_resolve(instance, user=user),
                    user=user)
                return True
            else:
                raise ApiException(
                    "Unable to remove", instance, res)

    @classmethod
    def record_resolve(cls, instance, user=None):
        """Gets information by records id, or name
        and parses it into new record
        """
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_resolve(instance, user=user)

        path_args = dict(
            (k, resolve_path_arg(k, instance)) for k in cls.list_path_args()
            )

        res = None
        json = None
        if "id" in instance:
            res = cls.show(instance.id, user=user, **path_args)
            if res.ok:
                json = res.json()
        else:
            res = cls.list(
                json=cls.search_dict(instance),
                user=user,
                **path_args)

            if res.ok:
                # TODO better separete kattelo and formam api
                if "results" in res.json():
                    json = res.json()["results"][0]
                else:
                    json = res.json()[0]

        if res.ok and json:
            ninstance = load_from_data(
                type(instance),
                json,
                data_load_transform
                )
            return ninstance
        else:
            raise ApiException(
                "Couldn't resolve record", instance, res)

    @classmethod
    def record_list(cls, instance, user=None):
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_list(instance, user=user)

        path_args = dict(
            (k, resolve_path_arg(k, instance)) for k in cls.list_path_args()
            )

        counting_response = cls.list(user=user, **path_args)
        if counting_response.ok:
            count = int(counting_response.json()["total"])
            if count > 0:
                listing_response = cls.list(
                    json=dict(per_page=count),
                    user=user, **path_args)
                if listing_response.ok:
                    return [
                        load_from_data(
                            instance.__class__, js, default_data_transform
                        ) for js in listing_response.json()["results"]
                    ]

    @classmethod
    def record_resolve_recursive(cls, instance, user=None):
        """Gets infromation about record,
        including all of its related fields
        """
        if cls != instance._meta.api_class:
            return instance._meta.api_class.record_resolve_recursive(
                instance, user=user)
        ninstance = cls.record_resolve(instance, user=user)
        related_fields = ninstance._meta.fields.items(cls=RelatedField)
        for fld in related_fields:
            if fld.name + "_id" in ninstance:
                related_class = fld.record_class
                related = related_class(
                    blank_record=True,
                    id=ninstance[(fld.name + "_id")]
                    )
                ninstance[fld.name] = cls.record_resolve(related, user=user)
            elif fld.name in ninstance:
                related = ninstance[fld.name]
                if isinstance(related, RelatedField):
                    resolved = cls.record_resolve(related, user=user)
                    ninstance[fld.name] = resolved
        return ninstance

    @classmethod
    def record_update(cls, instance, user=None):
        """Updates the record, doesn't touch related fields
        """
        if cls != instance._meta.api_class:
            api = instance._meta.api_class
            return api.record_update(instance, user=user)

        path_args = dict(
            (k, resolve_path_arg(k, instance)) for k in cls.list_path_args()
            )

        if "id" not in instance:
            res = cls.list(json=dict(search="name="+instance.name), user=user)
            if res.ok and len(res.json()) == 1:
                instance.id = cls.record_resolve(
                    instance,
                    user=user,
                    **path_args).id
            else:
                if len(res.json()) == 0:
                    raise KeyError(instance.name + " not found.")
                else:
                    raise KeyError(instance.name + " not unique.")

        update_fields_list = (
            cls.create_fields
            if cls.update_fields == []
            else cls.update_fields)

        data = dict(
            (name, field) for name, field in instance.items()
            if update_fields_list is []
            or name in update_fields_list
            )

        res = cls.update(
            instance.id,
            json=cls.opts(data),
            user=user,
            **path_args)
        if res.ok:
            ninstance = load_from_data(
                instance.__class__,
                res.json(),
                data_load_transform)
            return ninstance
        else:
            raise ApiException(
                "Couldn't update record", instance, res)

    @classmethod
    def record_create(cls, instance_orig, user=None):
        """Creates the record, doesn't touch related fields
        """
        if cls != instance_orig._meta.api_class:
            api = instance_orig._meta.api_class
            return api.record_create(instance_orig, user=user)
        instance = instance_orig.copy()

        path_args = dict(
            (k, resolve_path_arg(k, instance)) for k in cls.list_path_args()
            )

        data = dict(
            (name, field) for name, field in instance.items()
            if cls.create_fields == [] or name in cls.create_fields
            )

        res = cls.create(json=cls.opts(data), user=user, **path_args)
        if res.ok:
            ninstance = load_from_data(
                type(instance),
                res.json(),
                data_load_transform)
            return ninstance
        else:
            raise ApiException(
                "Couldn't create record", instance, res)

    @classmethod
    def record_create_dependencies(cls, instance_orig, user=None):
        """Ensures that all related fields of the record do exist
            resolves them and adds their ids to instance.
        """
        if cls != instance_orig._meta.api_class:
            api = instance_orig._meta.api_class
            return api.record_create_dependencies(instance_orig, user=user)
        instance = instance_orig.copy()

        # resolve ids
        related_fields = instance._meta.fields.keys(cls=RelatedField)

        for field in related_fields:
            value = resolve_or_create_record(instance[field], user=user)
            instance[field] = value
            instance[field+"_id"] = value.id

        # resolve ManyRelated ids
        related_fields = instance._meta.fields.keys(cls=ManyRelatedField)

        for field in related_fields:
            value = instance[field]
            if type(value) == type(list()):
                values = [
                    resolve_or_create_record(i, user=user)
                    for i in value
                    ]
                ids = [val.id for val in values]
                instance[field] = values
                instance[field+"_ids"] = ids
        return instance

    @classmethod
    def record_create_recursive(cls, instance_orig, user=None):
        """Creates the record, even related fields
        """
        if cls != instance_orig._meta.api_class:
            api = instance_orig._meta.api_class
            return api.record_create_recursive(instance_orig, user=user)
        res_instance = cls.record_create_dependencies(instance_orig, user=user)
        return cls.record_create(res_instance, user=user)


class Task(object):
    """Class for polling api tasks"""
    def __init__(self, json):
        self.json = json

    def refresh(self):
        """Reloads task data"""
        task_id = self.json["id"]
        response = base.get(path="/foreman_tasks/api/tasks/{}".format(task_id))
        self.json = response.json()

    def poll(self, delay, timeout):
        """Busy wait for task to complete"""
        current = 0
        finished = False
        while (not finished) and current < timeout:
            sleep_for_seconds(delay)
            current += delay
            self.refresh()
            finished = (self.json["result"] != 'pending')

    def result(self):
        return self.json["result"]
