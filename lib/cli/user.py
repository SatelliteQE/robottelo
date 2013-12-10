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

        result = self.list(options)

        if result['stdout']:
            result = result['stdout'][0]
        else:
            result = []

        return result
