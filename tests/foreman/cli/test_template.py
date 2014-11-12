# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Template CLI"""

from fauxfactory import gen_string
from robottelo.cli.factory import CLIFactoryError, make_template, make_os
from robottelo.cli.template import Template
from robottelo.common.decorators import run_only_on, skip_if_bug_open
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestTemplate(CLITestCase):
    """Test class for Config Template CLI."""

    def test_create_template_1(self):
        """@Test: Check if Template can be created

        @Feature: Template - Create

        @Assert: Template is created

        """

        content = gen_string("alpha", 10)
        name = gen_string("alpha", 10)

        try:
            new_obj = make_template(
                {
                    'name': name,
                    'content': content,
                }
            )
        except CLIFactoryError as e:
            self.fail(e)

        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])

    def test_update_template_1(self):
        """@Test: Check if Template can be updated

        @Feature: Template - Update

        @Assert: Template is updated

        """

        content = gen_string("alpha", 10)
        name = gen_string("alpha", 10)

        try:
            new_obj = make_template(
                {
                    'name': name,
                    'content': content,
                }
            )
        except CLIFactoryError as e:
            self.fail(e)

        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])

        updated_name = gen_string("alpha", 10)
        Template.update({'id': new_obj['id'], 'name': updated_name})
        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(updated_name, result.stdout['name'])

    @skip_if_bug_open('redmine', 8376)
    def test_add_operating_system_1(self):
        """@Test: Check if Template can be assigned operating system

        @Feature: Template - Add Operating System

        @Assert: Template has an operating system

        """

        content = gen_string("alpha", 10)
        name = gen_string("alpha", 10)

        try:
            new_template = make_template({
                'name': name,
                'content': content,
            })
            new_os = make_os()
        except CLIFactoryError as err:
            self.fail(err)

        result = Template.add_operatingsystem({
            "id": new_template["id"],
            "operatingsystem-id": new_os["id"],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Template.info({'id': new_template['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        os_string = '{0} {1}.{2}'.format(
            new_os['name'], new_os['major-version'], new_os['minor-version']
        )
        self.assertIn(os_string, result.stdout['operating-systems'])

    @skip_if_bug_open('redmine', 8376)
    def test_remove_operating_system_1(self):
        """@Test: Check if OS can be removed Template

        @Feature: Template - Remove Operating System

        @Assert: Template no longer has an operating system

        """

        content = gen_string("alpha", 10)
        name = gen_string("alpha", 10)

        try:
            new_obj = make_template(
                {
                    'name': name,
                    'content': content,
                }
            )
            new_os = make_os()
        except CLIFactoryError as e:
            self.fail(e)

        result = Template.add_operatingsystem(
            {
                "id": new_obj["id"],
                "operatingsystem-id": new_os["id"]
            }
        )
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        os_string = '{0} {1}.{2}'.format(
            new_os['name'], new_os['major-version'], new_os['minor-version']
        )
        self.assertIn(os_string, result.stdout['operating-systems'])

        result = Template.remove_operatingsystem({
            "id": new_obj["id"],
            "operatingsystem-id": new_os["id"]
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        os_string = '{0} {1}.{2}'.format(
            new_os['name'], new_os['major-version'], new_os['minor-version']
        )
        self.assertNotIn(os_string, result.stdout['operating-systems'])

    def test_dump_template_1(self):
        """@Test: Check if Template can be created with specific content

        @Feature: Template - Create

        @Assert: Template is created with specific content

        """

        content = gen_string("alpha", 10)
        name = gen_string("alpha", 10)

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

    @skip_if_bug_open('bugzilla', 1096333)
    def test_delete_template_1(self):
        """@Test: Check if Template can be deleted

        @Feature: Template - Delete

        @Assert: Template is deleted

        @BZ: 1096333

        """

        content = gen_string("alpha", 10)
        name = gen_string("alpha", 10)

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
