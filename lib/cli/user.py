#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.base import Base


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

        if _ret['stdout']:
            _ret = _ret['stdout'][0]
        else:
            _ret = []

        return _ret
