#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base


class User(Base):

    def __init__(self):
        self.command_base = "user"

    def exists(self, login):
        """
        Search for user by login.
        """

        options = {
            "search": "login='%s'" % login,
        }

        _ret = self.list(options)

        if _ret:
            _ret = _ret[0]

        return _ret
