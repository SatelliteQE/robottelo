#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from robottelo.cli.architecture import Architecture
from robottelo.common.helpers import generate_name


class TestArchitecture(BaseCLI):

    def _create_arch(self, name=None, operating_system_id=None):

        args = {
            'name': name or generate_name(),
            #TODO: if operating_system_id is None then fetch
            # list of available OSes from system.
            'operatingsystem-ids': operating_system_id or "1",
        }

        Architecture().create(args)

        self.assertTrue(Architecture().exists(('name', args['name'])))

    def test_create_architecture_1(self):
        """Successfully creates a new architecture"""

        name = generate_name(6)
        self._create_arch(name)

    def test_delete_architecture_1(self):
        """Creates and immediately deletes architecture."""

        name = generate_name(6)
        self._create_arch(name)

        arch = Architecture().exists(('name', name))

        args = {
            'id': arch['Id'],
        }

        Architecture().delete(args)
        self.assertFalse(Architecture().exists(('name', name)))
