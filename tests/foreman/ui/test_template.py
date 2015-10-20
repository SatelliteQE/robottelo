# -*- encoding: utf-8 -*-
"""Test class for Template UI"""
from ddt import ddt, data
from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import OS_TEMPLATE_DATA_FILE, SNIPPET_DATA_FILE
from robottelo.decorators import run_only_on
from robottelo.helpers import generate_strings_list, get_data_file
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_templates
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Template(UITestCase):
    """Implements Provisioning Template tests from UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(Template, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @data(*generate_strings_list(len1=8))
    @run_only_on('sat')
    def test_positive_create_template(self, name):
        """@Test: Create new template

        @Feature: Template - Positive Create

        @Assert: New provisioning template of type 'provision'
        should be created successfully

        """
        with Session(self.browser) as session:
            make_templates(
                session,
                name=name,
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                custom_really=True,
                template_type='provision',
            )
            self.assertIsNotNone(self.template.search(name))

    @run_only_on('sat')
    def test_negative_create_template_with_too_long_name(self):
        """@Test: Template - Create a new template with 256 characters in name

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        with Session(self.browser) as session:
            make_templates(
                session,
                name=gen_string('alpha', 256),
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                custom_really=True,
                template_type='provision',
            )
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators['name_haserror']))

    @data(' ', '')
    @run_only_on('sat')
    def test_negative_create_template_with_blank_name(self, name):
        """@Test: Create a new template with blank and whitespace in name

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        with Session(self.browser) as session:
            make_templates(
                session,
                name=name,
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                custom_really=True,
                template_type='provision',
            )
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators['name_haserror']))

    @run_only_on('sat')
    def test_negative_create_template_with_same_name(self):
        """@Test: Template - Create a new template with same name

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        name = gen_string('alpha')
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(name))
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators['name_haserror']))

    @run_only_on('sat')
    def test_negative_create_template_without_type(self):
        """@Test: Template - Create a new template without selecting its type

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            with self.assertRaises(UIError) as context:
                make_templates(
                    session,
                    name=name,
                    template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                    custom_really=True,
                    template_type='',
                )
                self.assertEqual(
                    context.exception.message,
                    'Could not create template "{0}" without type'.format(name)
                )

    @run_only_on('sat')
    def test_negative_create_template_without_upload(self):
        """@Test: Template - Create a new template without uploading a template

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            with self.assertRaises(UIError) as context:
                make_templates(
                    session,
                    name=name,
                    template_path='',
                    custom_really=True,
                    template_type='PXELinux',
                )
                self.assertEqual(
                    context.exception.message,
                    'Could not create blank template "{0}"'.format(name)
                )

    @run_only_on('sat')
    def test_negative_create_template_with_too_long_audit(self):
        """@Test: Create a new template with 256 characters in audit comments

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        with Session(self.browser) as session:
            make_templates(
                session,
                name=gen_string('alpha', 16),
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                custom_really=True,
                audit_comment=gen_string('alpha', 256),
                template_type='PXELinux'
            )
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators['haserror']))

    @data(*generate_strings_list(len1=8))
    @run_only_on('sat')
    def test_positive_create_snippet_template(self, name):
        """@Test: Create new template of type snippet

        @Feature: Template - Positive Create

        @Assert: New provisioning template of type 'snippet'
        should be created successfully

        """
        with Session(self.browser) as session:
            make_templates(
                session,
                name=name,
                template_path=get_data_file(SNIPPET_DATA_FILE),
                custom_really=True,
                snippet=True,
            )
            self.assertIsNotNone(self.template.search(name))

    @data(*generate_strings_list(len1=8))
    @run_only_on('sat')
    def test_remove_template(self, template_name):
        """@Test: Remove a template

        @Feature: Template - Positive Delete

        @Assert: Template removed successfully

        """
        entities.ConfigTemplate(
            name=template_name, organization=[self.organization]).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.template.delete(template_name)

    @run_only_on('sat')
    def test_update_template(self):
        """@Test: Update template name and template type

        @Feature: Template - Positive Update

        @Assert: The template name and type should be updated successfully

        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_templates(
                session,
                name=name,
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                custom_really=True,
                template_type='provision',
            )
            self.assertIsNotNone(self.template.search(name))
            self.template.update(name, False, new_name, None, 'PXELinux')
            self.assertIsNotNone(self.template.search(new_name))

    @run_only_on('sat')
    def test_update_template_os(self):
        """@Test: Creates new template, along with two OS's
        and associate list of OS's with created template

        @Feature: Template - Positive Update

        @Assert: The template should be updated with newly created OS's
        successfully

        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        os_list = [
            entities.OperatingSystem().create().name for _ in range(2)
        ]
        with Session(self.browser) as session:
            make_templates(
                session,
                name=name,
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                custom_really=True,
                template_type='provision',
            )
            self.assertIsNotNone(self.template.search(name))
            self.template.update(name, False, new_name, new_os_list=os_list)
            self.assertIsNotNone(self.template.search(new_name))

    @run_only_on('sat')
    def test_clone_template(self):
        """@Test: Assure ability to clone a provisioning template

        @Feature: Template - Clone

        @Steps:
         1.  Go to Provisioning template UI
         2.  Choose a template and attempt to clone it

        @Assert: template is cloned

        """
        name = gen_string('alpha')
        clone_name = gen_string('alpha')
        os_list = [
            entities.OperatingSystem().create().name for _ in range(2)
        ]
        with Session(self.browser) as session:
            make_templates(
                session,
                name=name,
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                custom_really=True,
                template_type='provision',
            )
            self.assertIsNotNone(self.template.search(name))
            self.template.clone(
                name,
                custom_really=False,
                clone_name=clone_name,
                os_list=os_list,
            )
            self.assertIsNotNone(self.template.search(clone_name))
