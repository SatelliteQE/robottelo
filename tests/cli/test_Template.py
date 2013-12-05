#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import os
import random

from basecli import BaseCLI
from lib.cli.base import Base
from lib.common.helpers import generate_name
from tempfile import mkstemp

# TODO: Move this to a common location
TEMPLATE_TYPES = [
    'PXELinux',
    'gPXE',
    'provision',
    'finish',
    'script',
    'PXEGrub',
    'snippet',
]


class Template(BaseCLI):

    def _create_template(self, template=None, template_type=None, name=None,
                         audit_comment=None, operatingsystem_ids=None,
                         content=None):

        if not template:
            (file_handle, layout) = mkstemp(text=True)
            os.chmod(layout, 0700)
            with open(layout, "w") as ptable:
                ptable.write(content)

        args = {
            'file': "/tmp/%s" % generate_name(),
            'name': name or generate_name(),
            'type': template_type or TEMPLATE_TYPES[random.randint(
                0, len(TEMPLATE_TYPES) - 1)],
            'audit-comment': audit_comment,
            'operatingsystem-ids': operatingsystem_ids,
        }

        # Upload file to server
        Base.upload_file(local_file=layout, remote_file=args['file'])

        self.template.create(args)

        self.assertTrue(self.template.exists(args['name']))

    def test_create_template_1(self):
        "Successfully creates a new template"

        content = generate_name()
        name = generate_name(6)
        self._create_template(name=name, content=content)

    def test_dump_template_1(self):
        "Creates template with specific content."

        content = generate_name()
        name = generate_name(6)
        self._create_template(name=name, content=content)

        template = self.template.exists(name)

        args = {
            'id': template['Id'],
        }

        template_content = self.template.dump(args)
        self.assertTrue(content in template_content)

    def test_delete_medium_1(self):
        "Creates and immediately deletes template."

        content = generate_name()
        name = generate_name(6)
        self._create_template(name=name, content=content)

        template = self.template.exists(name)

        args = {
            'id': template['Id'],
        }

        self.template.delete(args)
        self.assertFalse(self.template.exists(name))
