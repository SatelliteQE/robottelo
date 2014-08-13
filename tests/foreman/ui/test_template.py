# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Template UI
"""
from ddt import ddt
from robottelo.common.constants import OS_TEMPLATE_DATA_FILE, SNIPPET_DATA_FILE
from robottelo.common.decorators import data
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import (generate_string, get_data_file,
                                      generate_strings_list)
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc, make_templates,
                                  make_os)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Template(UITestCase):
    """
    Implements Provisioning Template tests from UI
    """

    org_name = None
    loc_name = None

    def setUp(self):
        super(Template, self).setUp()
        #  Make sure to use the Class' org_name instance
        if (Template.org_name is None and Template.loc_name is None):
            Template.org_name = generate_string("alpha", 8)
            Template.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Template.org_name)
                make_loc(session, name=Template.loc_name)

    @data(*generate_strings_list())
    def test_positive_create_template(self, name):
        """
        @Test: Create new template
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

    @skip_if_bug_open('bugzilla', 1121521)
    def test_negative_create_template_1(self):
        """
        @Test: Template - Create a new template with 256 characters in name
        @Feature: Template - Negative Create
        @Assert: Template is not created
        @BZ: 1121521
        """

        name = generate_string("alpha", 256)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["name_haserror"]))
            self.assertIsNone(self.template.search(name))

    def test_negative_create_template_2(self):
        """
        @Test: Template - Create a new template with whitespace
        @Feature: Template - Negative Create
        @Assert: Template is not created
        """
        name = " "
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["name_haserror"]))
            self.assertIsNone(self.template.search(name))

    def test_negative_create_template_3(self):
        """
        @Test: Template - Create a new template with blank name
        @Feature: Template - Negative Create
        @Assert: Template is not created
        """
        name = ""
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["name_haserror"]))
            self.assertIsNone(self.template.search(name))

    def test_negative_create_template_4(self):
        """
        @Test: Template - Create a new template with same name
        @Feature: Template - Negative Create
        @Assert: Template is not created
        """
        name = generate_string("alpha", 16)
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
        """
        @Test: Template - Create a new template without selecting its type
        @Feature: Template - Negative Create
        @Assert: Template is not created
        """
        name = generate_string("alpha", 16)
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
        """
        @Test: Template - Create a new template without uploading a template
        @Feature: Template - Negative Create
        @Assert: Template is not created
        """
        name = generate_string("alpha", 16)
        temp_type = 'PXELinux'
        template_path = ""
        with Session(self.browser) as session:
            with self.assertRaises(Exception) as context:
                make_templates(session, name=name, template_path=template_path,
                               custom_really=True, template_type=temp_type)
            self.assertEqual(context.exception.message,
                             "Could not create blank template '%s'" % name)

    def test_negative_create_template_7(self):
        """
        @Test: Create a new template with 256 characters in audit comments
        @Feature: Template - Negative Create
        @Assert: Template is not created
        """
        name = generate_string("alpha", 16)
        audit_comment = generate_string("alpha", 256)
        temp_type = 'PXELinux'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, audit_comment=audit_comment,
                           template_type=temp_type)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["alert.error"]))
            self.assertIsNone(self.template.search(name))

    def test_positive_create_snippet_template(self):
        """
        @Test: Create new template of type snippet
        @Feature: Template - Positive Create
        @Assert: New provisioning template of type 'snippet'
        should be created successfully
        """

        name = generate_string("alpha", 6)
        template_path = get_data_file(SNIPPET_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, snippet=True)
            self.assertIsNotNone(self.template.search(name))

    def test_remove_template(self):
        """
        @Test: Remove a template
        @Feature: Template - Positive Delete
        @Assert: Template removed successfully
        """

        name = generate_string("alpha", 6)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(name))
            self.template.delete(name, True)
            self.assertIsNotNone(self.template.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.template.search(name))

    def test_update_template(self):
        """
        @Test: Update template name and template type
        @Feature: Template - Positive Update
        @Assert: The template name and type should be updated successfully
        """

        name = generate_string("alpha", 6)
        new_name = generate_string("alpha", 6)
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
        """
        @Test: Creates new template, along with two OS's
        and associate list of OS's with created template
        @Feature: Template - Positive Update
        @Assert: The template should be updated with newly created OS's
        successfully
        """
        name = generate_string("alpha", 6)
        new_name = generate_string("alpha", 6)
        temp_type = 'provision'
        os_name1 = generate_string("alpha", 6)
        os_name2 = generate_string("alpha", 6)
        os_list = [os_name1, os_name2]
        major_version = generate_string('numeric', 1)
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            for os_name in os_list:
                make_os(session, name=os_name,
                        major_version=major_version)
                self.assertIsNotNone(self.operatingsys.search(os_name))
            make_templates(session, name=name, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(name))
            self.template.update(name, False, new_name, new_os_list=os_list)
            self.assertIsNotNone(self.template.search(new_name))
