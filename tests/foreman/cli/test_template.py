# -*- encoding: utf-8 -*-
"""Test class for Template CLI"""

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_location,
    make_org,
    make_os,
    make_template,
)
from robottelo.cli.template import Template
from robottelo.decorators import run_only_on, tier1, tier2
from robottelo.test import CLITestCase


class TestTemplate(CLITestCase):
    """Test class for Config Template CLI."""

    @run_only_on('sat')
    @tier1
    def test_create_template_1(self):
        """@Test: Check if Template can be created

        @Feature: Template - Create

        @Assert: Template is created
        """
        name = gen_string('alpha')
        template = make_template({'name': name})
        self.assertEqual(template['name'], name)

    @run_only_on('sat')
    @tier1
    def test_update_template_1(self):
        """@Test: Check if Template can be updated

        @Feature: Template - Update

        @Assert: Template is updated
        """
        template = make_template()
        updated_name = gen_string('alpha')
        Template.update({
            'id': template['id'],
            'name': updated_name,
        })
        template = Template.info({'id': template['id']})
        self.assertEqual(updated_name, template['name'])

    @run_only_on('sat')
    @tier1
    def test_create_template_with_loc(self):
        """@Test: Check if Template with Location can be created

        @Feature: Template - Create

        @Assert: Template is created and new Location has been assigned
        """
        new_loc = make_location()
        new_template = make_template({'location-ids': new_loc['id']})
        self.assertIn(new_loc['name'], new_template['locations'])

    @run_only_on('sat')
    @tier1
    def test_create_template_locked(self):
        """@Test: Check that locked Template cannot be created

        @Feature: Template - Create

        @Assert: It is not allowed to create locked Template
        """
        with self.assertRaises(CLIFactoryError):
            make_template({
                'locked': 'true',
                'name': gen_string('alpha'),
            })

    @run_only_on('sat')
    @tier1
    def test_create_template_with_org(self):
        """@Test: Check if Template with Organization can be created

        @Feature: Template - Create

        @Assert: Template is created and new Organization has been assigned
        """
        new_org = make_org()
        new_template = make_template({
            'name': gen_string('alpha'),
            'organization-ids': new_org['id'],
        })
        self.assertIn(new_org['name'], new_template['organizations'])

    @run_only_on('sat')
    @tier2
    def test_add_operating_system_1(self):
        """@Test: Check if Template can be assigned operating system

        @Feature: Template - Add Operating System

        @Assert: Template has an operating system
        """
        new_template = make_template()
        new_os = make_os()
        Template.add_operatingsystem({
            'id': new_template['id'],
            'operatingsystem-id': new_os['id'],
        })
        new_template = Template.info({'id': new_template['id']})
        os_string = '{0} {1}.{2}'.format(
            new_os['name'], new_os['major-version'], new_os['minor-version'])
        self.assertIn(os_string, new_template['operating-systems'])

    @run_only_on('sat')
    @tier2
    def test_remove_operating_system_1(self):
        """@Test: Check if OS can be removed Template

        @Feature: Template - Remove Operating System

        @Assert: Template no longer has an operating system
        """
        template = make_template()
        new_os = make_os()
        Template.add_operatingsystem({
            'id': template['id'],
            'operatingsystem-id': new_os['id'],
        })
        template = Template.info({'id': template['id']})
        os_string = '{0} {1}.{2}'.format(
            new_os['name'], new_os['major-version'], new_os['minor-version']
        )
        self.assertIn(os_string, template['operating-systems'])
        Template.remove_operatingsystem({
            'id': template['id'],
            'operatingsystem-id': new_os['id']
        })
        template = Template.info({'id': template['id']})
        self.assertNotIn(os_string, template['operating-systems'])

    @run_only_on('sat')
    @tier1
    def test_dump_template_1(self):
        """@Test: Check if Template can be created with specific content

        @Feature: Template - Create

        @Assert: Template is created with specific content
        """
        content = gen_string('alpha')
        name = gen_string('alpha')
        template = make_template({
            'content': content,
            'name': name,
        })
        self.assertEqual(template['name'], name)
        template_content = Template.dump({'id': template['id']})
        self.assertIn(content, template_content[0])

    @run_only_on('sat')
    @tier1
    def test_delete_template_1(self):
        """@Test: Check if Template can be deleted

        @Feature: Template - Delete

        @Assert: Template is deleted
        """
        template = make_template()
        Template.delete({'id': template['id']})
        with self.assertRaises(CLIReturnCodeError):
            Template.info({'id': template['id']})
