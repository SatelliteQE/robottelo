# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Template UI
"""

from robottelo.common.constants import OS_TEMPLATE_URL, SNIPPET_URL, \
    OS_TEMPLATE
from robottelo.common.helpers import generate_name, generate_string, \
    download_template, get_data_file
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


class Template(BaseUI):
    """
    Implements Provisioning Template tests from UI
    """

    def create_template(self, name, template_path, custom_really,
                        temp_type, snippet, os_list=None):
        """
        Method to creates new template with navigation
        """

        name = name or generate_name(6)
        temp_type = temp_type
        self.navigator.go_to_provisioning_templates()
        self.template.create(name, template_path, custom_really,
                             temp_type, snippet, os_list)
        self.assertIsNotNone(self.template.search(name))

    def test_create_template(self):
        """
        Test:
        Creates new template

        Expected Result/Assert:
        New provisioning template of type 'provision'
        should be created successfully
        """

        name = generate_name(6)
        temp_type = 'provision'
        #os_list = ["rhel 6.5", "rhel64 6.4"]
        #template_path = download_template(OS_TEMPLATE_URL)
        template_path = get_data_file(OS_TEMPLATE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_template(name, template_path, True,
                             temp_type, None)

    def test_create_snippet_template(self):
        """
        Test:
        Creates new template of type snippet

        Expected Result/Assert:
        New provisioning template of type 'snippet'
        should be created successfully
        """

        name = generate_name(6)
        template_path = download_template(SNIPPET_URL)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_template(name, template_path, True,
                             None, True)

    def test_remove_template(self):
        """
        Test:
        Creates new template and removes it

        Expected Result/Assert:
        Created template should be removed successfully
        """

        name = generate_name(6)
        temp_type = 'provision'
        template_path = download_template(OS_TEMPLATE_URL)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_template(name, template_path, True,
                             temp_type, None)
        self.template.delete(name, True)
        self.assertTrue(self.template.wait_until_element(common_locators
                                                         ["notif.success"]))
        self.assertIsNone(self.template.search(name))

    def test_update_template(self):
        """
        Test:
        Creates new template and update its name and template type

        Expected Result/Assert:
        The template name and type should be updated successfully
        """

        name = generate_name(6)
        new_name = generate_name(6)
        temp_type = 'provision'
        new_temp_type = 'PXELinux'
        template_path = download_template(OS_TEMPLATE_URL)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_template(name, template_path, True,
                             temp_type, None)
        self.template.update(name, False, new_name, None, new_temp_type)
        self.assertIsNotNone(self.template.search(new_name))

    def test_update_template_os(self):
        """
        Test:
        Creates new template, along with two OS's
        and associate list of OS's with created template

        Expected Result/Assert:
        The template should be updated with newly created OS's successfully
        """

        name = generate_name(6)
        new_name = generate_name(6)
        temp_type = 'provision'
        os_name1 = generate_name(6)
        os_name2 = generate_name(6)
        os_list = [os_name1, os_name2]
        major_version = generate_string('numeric', 1)
        template_path = download_template(OS_TEMPLATE_URL)
        self.login.login(self.katello_user, self.katello_passwd)
        for os_name in os_list:
            self.navigator.go_to_operating_systems()
            self.operatingsys.create(os_name, major_version)
            self.assertIsNotNone(self.operatingsys.search(os_name))
        self.create_template(name, template_path, True,
                             temp_type, None)
        self.template.update(name, False, new_name, new_os_list=os_list)
        self.assertIsNotNone(self.template.search(new_name))
