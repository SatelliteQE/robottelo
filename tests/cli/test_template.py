#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import random

from os import chmod
from robottelo.cli.template import Template
from robottelo.common import ssh
from robottelo.common.constants import TEMPLATE_TYPES
from robottelo.common.helpers import generate_name
from tests.cli.basecli import BaseCLI
from tempfile import mkstemp


class TestTemplate(BaseCLI):

    def _create_template(self, template=None, template_type=None, name=None,
                         audit_comment=None, operatingsystem_ids=None,
                         content=None):

        if not template:
            (file_handle, layout) = mkstemp(text=True)
            chmod(layout, 0700)
            with open(layout, "w") as ptable:
                ptable.write(content)

        args = {
            'file': "/tmp/%s" % generate_name(),
            'name': name or generate_name(),
            'type': template_type or random.choice(TEMPLATE_TYPES),
            'audit-comment': audit_comment,
            'operatingsystem-ids': operatingsystem_ids,
        }

        # Upload file to server
        ssh.upload_file(local_file=layout, remote_file=args['file'])

        Template().create(args)

        self.assertTrue(Template().exists(('name', args['name'])))

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

        template = Template().exists(('name', name))

        args = {
            'id': template['Id'],
        }

        template_content = Template().dump(args)
        self.assertTrue(content in template_content.stdout[0])

    def test_delete_medium_1(self):
        "Creates and immediately deletes template."

        content = generate_name()
        name = generate_name(6)
        self._create_template(name=name, content=content)

        template = Template().exists(('name', name))

        args = {
            'id': template['Id'],
        }

        Template().delete(args)
        self.assertFalse(Template().exists(('name', name)))
