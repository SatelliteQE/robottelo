#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import random

from basecli import BaseCLI
from lib.cli.operatingsys import OperatingSys
from lib.common.helpers import generate_name


class TestOperatingSys(BaseCLI):

    def _create_os(self, name=None, major=None, minor=None):

        name = name if name else generate_name()
        major = major if major else random.randint(0, 10)
        minor = minor if minor else random.randint(0, 10)

        args = {
            'name': name,
            'major': major,
            'minor': minor,
        }

        OperatingSys().create(args)
        self.assertTrue(OperatingSys().exists(args['name']))

    def test_create_os_1(self):
        "Successfully creates a new OS."

        self._create_os()
