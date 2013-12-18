# -*- encoding: utf-8 -*-
import robottelo.api.base as base

class ApiCrudMixin:
    """Defines basic crud methods based on api_path class method """
    @classmethod
    def api_path(cls):
        """Stores the path to api entry point,
        allows for automatic param definition, i.e.:

        /api/compute_resources/:compute_resource_id/images

        will require compute_resource_id to be supplied in each crud call

        """
        raise NotImplementedError("Api path needs to be defined")

    @classmethod
    def id_from_json(cls, json):
        """Required for automatic generating of crud tests"""
        raise NotImplementedError("Api path needs to be defined")

    @classmethod
    def parse_path_arg(cls, args):
        """Method parsing the api_path for extra arguments"""
        path = cls.api_path()
        path_args = [s[1:]
                        for s in path.split('/')
                        if s.startswith(":")]
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


