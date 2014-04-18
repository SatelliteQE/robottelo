# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Template CLI
"""

from robottelo.cli.factory import make_template
from robottelo.cli.template import Template
from robottelo.common.decorators import redminebug
from robottelo.common.helpers import generate_string
from tests.foreman.cli.basecli import BaseCLI


@redminebug('4560')
class TestTemplate(BaseCLI):
    """
    Test class for Config Template CLI.
    """

    def test_create_template_1(self):
        """
        @Test: Check if Template can be created
        @Feature: Template - Create
        @Assert: Template is created
        """

        content = generate_string("alpha", 10)
        name = generate_string("alpha", 10)

        new_obj = make_template(
            {
                'name': name,
                'content': content,
            }
        )

        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])

    def test_dump_template_1(self):
        """
        @Test: Check if Template can be created with specific content
        @Feature: Template - Create
        @Assert: Template is created with specific content
        """

        content = generate_string("alpha", 10)
        name = generate_string("alpha", 10)

        new_obj = make_template(
            {
                'name': name,
                'content': content,
            }
        )

        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])

        template_content = Template.dump({'id': new_obj['id']})
        self.assertIn(content, template_content.stdout[0])

    def test_delete_template_1(self):
        """
        @Test: Check if Template can be deleted
        @Feature: Template - Delete
        @Assert: Template is deleted
        """

        content = generate_string("alpha", 10)
        name = generate_string("alpha", 10)

        new_obj = make_template(
            {
                'name': name,
                'content': content,
            }
        )

        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])

        Template.delete({'id': new_obj['id']})

        result = Template.info({'id': new_obj['id']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)
