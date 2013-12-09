#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import random

from basecli import BaseCLI
from lib.cli.medium import Medium
from lib.common.helpers import generate_name

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"
OSES = [
    'Archlinux',
    'Debian',
    'Gentoo',
    'Redhat',
    'Solaris',
    'Suse',
    'Windows',
]


class TestMedium(BaseCLI):

    def _create_medium(self, name=None, path=None, os_family=None,
                       operating_system_id=None):

        args = {
            'name': name or generate_name(),
            'path': path or URL % generate_name(5),
            'os-family': os_family or OSES[random.randint(0, len(OSES) - 1)],
            #TODO: if operating_system_id is None then fetch
            # list of available OSes from system.
            'operatingsystem-ids': operating_system_id or "1",
        }

        Medium().create(args)

        self.assertTrue(Medium().exists(args['name']))

    def test_create_medium_1(self):
        "Successfully creates a new medium"

        name = generate_name(6)
        self._create_medium(name)

    def test_delete_medium_1(self):
        "Creates and immediately deletes medium."

        name = generate_name(6)
        self._create_medium(name)

        medium = Medium().exists(name)

        args = {
            'id': medium['Id'],
        }

        Medium().delete(args)
        self.assertFalse(Medium().exists(name))
