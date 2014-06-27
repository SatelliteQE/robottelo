# -*- encoding: utf-8 -*-

"""
Module for Domain api and record implementation
"""


from robottelo.api.apicrud import ApiCrud
from robottelo.common import records


class PermissionApi(ApiCrud):
    """ Implementation of api for foreman domains
    """
    api_path = "/api/v2/permissions"
    create_fields = ["name"]

    @classmethod
    def search_dict(cls, instance):
        return dict(name=instance.name)


class Permission(records.Record):
    """ Implementation of foreman domains record
    """

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = PermissionApi


class PermissionList(object):
    def __init__(self, suffix=None, **kwargs):
        if suffix:
            kwargs.setdefault("resolve", Permission(name="view_%s" % suffix))
            kwargs.setdefault("create", Permission(name="create_%s" % suffix))
            kwargs.setdefault("update", Permission(name="edit_%s" % suffix))
            kwargs.setdefault("remove", Permission(name="destroy_%s" % suffix))

        self.__dict__ = kwargs

    def __getitem__(self, key):
        if key in self.keys():
            return self.__dict__[key]
        else:
            raise KeyError("Key %s was not found in record" % key)

    def __delitem__(self, key):
        if key in self.keys():
            del self.__dict__[key]
        else:
            raise KeyError("Key %s was not found in record" % key)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        return key in self.keys()

    def keys(self):
        """Adding dict functionality to records
        """
        return [k for k, v in self.__dict__.items()
                if not k.startswith("_") and k != ""]

    def items(self):
        """Adding dict functionality to records
        """
        return [(k, v) for k, v in self.__dict__.items()
                if not k.startswith("_") and k != ""]
