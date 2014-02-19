# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Medium  CLI
"""

import random

from robottelo.cli.medium import Medium
from robottelo.cli.factory import make_medium
from robottelo.common.helpers import generate_name
from tests.cli.basecli import MetaCLI

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


class TestMedium(MetaCLI):

    factory = make_medium
    factory_obj = Medium

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

        self.assertTrue(Medium().exists(('name', args['name'])).stdout)

    def test_create_medium_1(self):
        """
        @Feature: Medium - Positive Create
        @Test: Check if Medium can be created
        @Assert: Medium is created
        """

        name = generate_name(6)
        self._create_medium(name)

    def test_delete_medium_1(self):
        """
        @Feature: Medium - Positive Delete
        @Test: Check if Medium can be deleted
        @Assert: Medium is deleted
        """

        name = generate_name(6)
        self._create_medium(name)

        medium = Medium().exists(('name', name)).stdout

        args = {
            'id': medium['id'],
        }

        Medium().delete(args)
        self.assertFalse(Medium().exists(('name', name)).stdout)
