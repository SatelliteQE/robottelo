# -*- encoding: utf-8 -*-
import copy

class ApiModelMixin:
    """Simple mixin, that enables conversion of a given object to json"""
    def to_json(self, whitelist=[], blacklist=[]):
        """Converts atributs to unicode hashmap"""
        user = {k:v for (k, v) in self.__dict__.items()}
        if whitelist:
            user = {k:v for (k, v) in user.items()
                     if k in whitelist}
        user = {k:v for (k, v) in user.items()
                 if not k in blacklist}
        user = {unicode(k):(unicode(v) if type(v) is str else v)
                for (k, v) in user.items()}
        return user

    def copy(self):
        return copy.deepcopy(self)

    def graylist(self, **kwargs):
        whitelist = [k for k in kwargs if kwargs[k] == True]
        blacklist = [k for k in kwargs if kwargs[k] == False]
        if whitelist:
            for attr in self.__dict__:
                if not attr in whitelist:
                    del self.__dict__[attr]

        for attr in blacklist:
            if attr in self.__dict__:
                del self.__dict__[attr]
        return self
