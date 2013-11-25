#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.common.helpers import generate_name
from lib.common.helpers import generate_string


class Architecture(BaseCLI):

    def _create_arch(self, name=None, operating_system_id=None):

        name = name or generate_name()
        #TODO: if operating_system_id is None then fetch
        # list of available OSes from system.
        operating_system_id = operating_system_id or "1"

        self.arch.create(
            name, operating_system_id)

        self.assertTrue(self.arch.exists(name))

    def test_create_architecture_1(self):
        "Successfully creates a new architecture"

        name = generate_name(6)
        self._create_arch(name)

    def test_delete_architecture_1(self):
        "Creates and immediately deletes architecture."

        name = generate_name(6)
        self._create_arch(name)

        arch = self.arch.architecture(name)
        self.arch.delete(arch['Id'])
        self.assertFalse(self.arch.exists(name))
