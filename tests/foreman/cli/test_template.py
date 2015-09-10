# -*- encoding: utf-8 -*-
"""Test class for Template CLI"""

from fauxfactory import gen_string
from robottelo.cli.factory import (
    CLIFactoryError,
    make_location,
    make_org,
    make_os,
    make_template
)
from robottelo.cli.template import Template
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestTemplate(CLITestCase):
    """Test class for Config Template CLI."""

    def test_create_template_1(self):
        """@Test: Check if Template can be created

        @Feature: Template - Create

        @Assert: Template is created

        """
        name = gen_string("alpha")

        try:
            new_obj = make_template({
                'name': name,
                'content': gen_string("alpha"),
            })
        except CLIFactoryError as e:
            self.fail(e)

        self.assertEqual(new_obj['name'], name)

    def test_update_template_1(self):
        """@Test: Check if Template can be updated

        @Feature: Template - Update

        @Assert: Template is updated

        """
        name = gen_string("alpha")

        try:
            new_obj = make_template({
                'name': name,
                'content': gen_string("alpha"),
            })
        except CLIFactoryError as e:
            self.fail(e)

        updated_name = gen_string("alpha")
        result = Template.update({'id': new_obj['id'], 'name': updated_name})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Template.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(updated_name, result.stdout['name'])

    def test_create_template_with_location(self):
        """@Test: Check if Template with Location can be created

        @Feature: Template - Create

        @Assert: Template is created and new Location has been assigned

        """
        try:
            new_loc = make_location()
            new_template = make_template({
                'name': gen_string('alpha'),
                'location-ids': new_loc['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertIn(new_loc['name'], new_template['locations'])

    def test_create_template_locked(self):
        """@Test: Check that locked Template cannot be created

        @Feature: Template - Create

        @Assert: It is not allowed to create locked Template

        """
        with self.assertRaises(CLIFactoryError):
            make_template({
                'name': gen_string('alpha'),
                'locked': 'true',
            })

    def test_create_template_with_organization(self):
        """@Test: Check if Template with Organization can be created

        @Feature: Template - Create

        @Assert: Template is created and new Organization has been assigned

        """
        try:
            new_org = make_org()
            new_template = make_template({
                'name': gen_string('alpha'),
                'organization-ids': new_org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertIn(new_org['name'], new_template['organizations'])

    def test_add_operating_system_1(self):
        """@Test: Check if Template can be assigned operating system

        @Feature: Template - Add Operating System

        @Assert: Template has an operating system

        """

        content = gen_string("alpha")
        name = gen_string("alpha")

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

    def test_remove_operating_system_1(self):
        """@Test: Check if OS can be removed Template

        @Feature: Template - Remove Operating System

        @Assert: Template no longer has an operating system

        """

        content = gen_string("alpha")
        name = gen_string("alpha")

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
        content = gen_string('alpha')
        name = gen_string('alpha')

        template = make_template({
            'name': name,
            'content': content,
        })

        self.assertEqual(template['name'], name)
        template_content = Template.dump({'id': template['id']})
        self.assertIn(content, template_content.stdout[0])

    @skip_if_bug_open('bugzilla', 1096333)
    def test_delete_template_1(self):
        """@Test: Check if Template can be deleted

        @Feature: Template - Delete

        @Assert: Template is deleted

        @BZ: 1096333

        """
        name = gen_string('alpha')

        new_obj = make_template({
            'name': name,
            'content': gen_string('alpha'),
        })

        result = Template.delete({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Template.info({'id': new_obj['id']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)
