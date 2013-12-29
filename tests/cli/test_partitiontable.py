# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Partition table CLI
"""

import os
import random

from basecli import BaseCLI
from robottelo.cli.base import Base
from robottelo.cli.partitiontable import PartitionTable
from robottelo.common import ssh
from robottelo.common.helpers import generate_name
from tempfile import mkstemp

# TODO: Move this to a common location
OSES = [
    'Archlinux',
    'Debian',
    'Gentoo',
    'Redhat',
    'Solaris',
    'Suse',
    'Windows',
]


class TestPartitionTable(BaseCLI):

    def _create_ptable(self, layout=None, name=None, os_family=None,
                       content=''):

        if not layout:
            (file_handle, layout) = mkstemp(text=True)
            os.chmod(layout, 0700)
            with open(layout, "w") as ptable:
                ptable.write(content)

        args = {
            'file': "/tmp/%s" % generate_name(),
            'name': name or generate_name(),
            'os-family': os_family or OSES[random.randint(0, len(OSES) - 1)],
        }

        # Upload file to server
        ssh.upload_file(local_file=layout, remote_file=args['file'])

        PartitionTable().create(args)

        self.assertTrue(PartitionTable().exists(('name', args['name'])))

    def test_create_ptable_1(self):
        "Successfully creates a new ptable"

        content = "Fake ptable"
        name = generate_name(6)
        self._create_ptable(name=name, content=content)

    def test_dump_ptable_1(self):
        "Creates partition table with specific content."

        content = "Fake ptable"
        name = generate_name(6)
        self._create_ptable(name=name, content=content)

        ptable = PartitionTable().exists(('name', name))

        args = {
            'id': ptable['Id'],
        }

        ptable_content = PartitionTable().dump(args)

        self.assertTrue(content in ptable_content.stdout[0])

    def test_delete_medium_1(self):
        "Creates and immediately deletes medium."

        content = "Fake ptable"
        name = generate_name(6)
        self._create_ptable(name=name, content=content)

        ptable = PartitionTable().exists(('name', name))

        args = {
            'id': ptable['Id'],
        }

        PartitionTable().delete(args)
        self.assertFalse(PartitionTable().exists(('name', name)))
