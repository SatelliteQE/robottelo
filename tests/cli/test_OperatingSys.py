#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import random

from basecli import BaseCLI
from lib.common.helpers import generate_name


class OperatingSys(BaseCLI):

    def _create_os(self, name=None, major=None, minor=None):

        args = {
            'name': name or generate_name(),
            'major': major or random.randint(0, 10),
            'minor': minor or random.randint(0, 10),
        }

        self.os.create(args)
        self.assertTrue(self.os.exists(args['name']))

    def test_create_os_1(self):
        "Successfully creates a new OS."

        self._create_os()
