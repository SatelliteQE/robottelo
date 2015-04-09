# -*- encoding: utf-8 -*-
"""Test class for Template UI"""
from ddt import ddt
from fauxfactory import gen_string
from robottelo import entities
from robottelo.common.constants import OS_TEMPLATE_DATA_FILE, SNIPPET_DATA_FILE
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import get_data_file, generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_templates
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class Template(UITestCase):
    """Implements Provisioning Template tests from UI"""

    @data(*generate_strings_list(len1=8))
    def test_positive_create_template(self, name):
        """@Test: Create new template

        @Feature: Template - Positive Create

        @Assert: New provisioning template of type 'provision'
        should be created successfully

        """
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(name))

    def test_negative_create_template_1(self):
        """@Test: Template - Create a new template with 256 characters in name

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        name = gen_string("alpha", 256)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["name_haserror"]))

    @data(" ", "")
    def test_negative_create_template_2(self, name):
        """@Test: Create a new template with blank and whitespace in name

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["name_haserror"]))

    def test_negative_create_template_4(self):
        """@Test: Template - Create a new template with same name

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        name = gen_string("alpha", 16)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(name))
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["name_haserror"]))

    def test_negative_create_template_5(self):
        """@Test: Template - Create a new template without selecting its type

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        name = gen_string("alpha", 16)
        temp_type = ""
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            with self.assertRaises(Exception) as context:
                make_templates(session, name=name, template_path=template_path,
                               custom_really=True, template_type=temp_type)
            self.assertEqual(context.exception.message,
                             "Could not create template '%s'"
                             " without type" % name)

    def test_negative_create_template_6(self):
        """@Test: Template - Create a new template without uploading a template

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        name = gen_string("alpha", 16)
        temp_type = 'PXELinux'
        template_path = ""
        with Session(self.browser) as session:
            with self.assertRaises(Exception) as context:
                make_templates(session, name=name, template_path=template_path,
                               custom_really=True, template_type=temp_type)
            self.assertEqual(context.exception.message,
                             "Could not create blank template '%s'" % name)

    def test_negative_create_template_7(self):
        """@Test: Create a new template with 256 characters in audit comments

        @Feature: Template - Negative Create

        @Assert: Template is not created

        """
        name = gen_string("alpha", 16)
        audit_comment = gen_string("alpha", 256)
        temp_type = 'PXELinux'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, audit_comment=audit_comment,
                           template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["haserror"]))

    @data(*generate_strings_list(len1=8))
    def test_positive_create_snippet_template(self, name):
        """@Test: Create new template of type snippet

        @Feature: Template - Positive Create

        @Assert: New provisioning template of type 'snippet'
        should be created successfully

        """
        template_path = get_data_file(SNIPPET_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, snippet=True)
            self.assertIsNotNone(self.template.search(name))

    @skip_if_bug_open('bugzilla', 1177756)
    @data(*generate_strings_list(len1=8))
    def test_remove_template(self, template_name):
        """@Test: Remove a template

        @Feature: Template - Positive Delete

        @Assert: Template removed successfully

        @BZ: 1177756

        """
        entities.ConfigTemplate(name=template_name).create_json()
        with Session(self.browser):
            self.template.delete(template_name, True)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["notif.success"]))

    def test_update_template(self):
        """@Test: Update template name and template type

        @Feature: Template - Positive Update

        @Assert: The template name and type should be updated successfully

        """
        name = gen_string("alpha", 6)
        new_name = gen_string("alpha", 6)
        temp_type = 'provision'
        new_temp_type = 'PXELinux'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(name))
            self.template.update(name, False, new_name, None, new_temp_type)
            self.assertIsNotNone(self.template.search(new_name))

    def test_update_template_os(self):
        """@Test: Creates new template, along with two OS's
        and associate list of OS's with created template

        @Feature: Template - Positive Update

        @Assert: The template should be updated with newly created OS's
        successfully

        """
        name = gen_string("alpha", 6)
        new_name = gen_string("alpha", 6)
        temp_type = 'provision'
        os_list = [
            entities.OperatingSystem().create_json()['name'] for _ in range(2)
        ]
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(name))
            self.template.update(name, False, new_name, new_os_list=os_list)
            self.assertIsNotNone(self.template.search(new_name))

    def test_clone_template(self):
        """@Test: Assure ability to clone a provisioning template

        @Feature: Template - Clone

        @Steps:
         1.  Go to Provisioning template UI
         2.  Choose a template and attempt to clone it

        @Assert: template is cloned

        """
        name = gen_string("alpha", 6)
        clone_name = gen_string("alpha", 6)
        temp_type = 'provision'
        os_list = [
            entities.OperatingSystem().create_json()['name'] for _ in range(2)
        ]
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(name))
            self.template.clone(name, custom_really=False,
                                clone_name=clone_name, os_list=os_list)
            self.assertIsNotNone(self.template.search(clone_name))
