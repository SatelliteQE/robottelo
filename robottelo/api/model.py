# -*- encoding: utf-8 -*-

"""
Module for shared model declaration, like converting to json.
"""

import copy


class ApiModelMixin(object):
    """Simple mixin, that enables conversion of a given object to json,
       expects attributes to be simple.

    """
    def __init__(self):
        """Mixin not to be instatiated"""
        raise NotImplementedError("""Simple mixin, that enables conversion of a
            given object to json,expects attributes to be simple.""")

    def to_data_structure(self):
        """Converts atributes to unicode hashmap"""
        user = {k: v for (k, v) in self.__dict__.items()}
        user = {unicode(k): (unicode(v) if type(v) is str else v)
                for (k, v) in user.items()}
        return user

    def copy(self):
        """Returns deepcopy of the self object"""
        return copy.deepcopy(self)

    def graylist(self, **kwargs):
        """Utility function for blackliting/whitelisting attributes in object.
        If argument is True,
            attribute with arguments name is added to whitelist.
        If argument is False,
            attribute with arguments name is added to blacklist.
        If whitelist is not empty,
            all atributes that aren't in whitelist are removed from object.
        All atributes that are in blacklis are removed from object.

        """
        whitelist = [k for k in kwargs if kwargs[k] is True]
        blacklist = [k for k in kwargs if kwargs[k] is False]
        if whitelist:
            for attr in self.__dict__:
                if not attr in whitelist:
                    del self.__dict__[attr]

        for attr in blacklist:
            if attr in self.__dict__:
                del self.__dict__[attr]
        return self

    def opts(self):
        """Required for automatic generating of crud tests
        Output should be a json structure to be sent to api.

        """
        raise NotImplementedError("CRUD options method not defined.")

    def result_opts(self):
        """Required for automatic generating of crud tests
        Output should be a json structure that is comparable
        with expected json result recieved from api.

        """
        return self.opts()

    def change(self):
        """Required for automatic generating update of crud test."""
        raise NotImplementedError("Change method not defined.")

