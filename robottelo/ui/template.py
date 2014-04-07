# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Template UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select
from robottelo.common.constants import FILTER


class Template(Base):
    """
    Provides the CRUD functionality for Templates.
    """

    def create(self, name, template_path, custom_really,
               template_type, snippet, os_list=None):
        """
        Creates a provisioning template from UI.
        """
        self.wait_until_element(locators["provision.template_new"]).click()

        if self.wait_until_element(locators["provision.template_name"]):
            self.find_element(locators
                              ["provision.template_name"]).send_keys(name)
            if template_path:
                self.wait_until_element(tab_locators["tab_primary"]).click()
                self.find_element(locators
                                  ["provision.template_template"]
                                  ).send_keys(template_path)
                self.handle_alert(custom_really)
                self.scroll_page()
            else:
                raise Exception(
                    "Could not create blank template '%s'" % name)
            if template_type:
                self.wait_until_element(tab_locators
                                        ["provision.tab_type"]).click()
                type_ele = self.find_element(locators
                                             ["provision.template_type"])
                Select(type_ele).select_by_visible_text(template_type)
            elif snippet:
                self.wait_until_element(tab_locators
                                        ["provision.tab_type"]).click()
                self.find_element(locators
                                  ["provision.template_snippet"]).click()
            else:
                raise Exception(
                    "Could not create template '%s' without type" % name)
            self.scroll_page()
            self.configure_entity(os_list, FILTER['template_os'],
                                  tab_locator=tab_locators
                                  ["provision.tab_association"])
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new provisioning template '%s'" % name)

    def search(self, name):
        """
        Searches existing template from UI
        """
        self.scroll_page()
        nav = Navigator(self.browser)
        nav.go_to_provisioning_templates()
        element = self.search_entity(name,
                                     locators["provision.template_select"])
        return element

    def update(self, name, custom_really, new_name=None,
               template_path=None, template_type=None,
               os_list=None, new_os_list=None):
        """
        Updates a given template.
        """

        element = self.search(name)

        if element:
            element.click()
            self.wait_for_ajax()
            if new_name:
                self.field_update("provision.template_name", new_name)
            if template_path:
                self.find_element(locators
                                  ["provision.template_template"]
                                  ).send_keys(template_path)
                self.handle_alert(custom_really)
            if template_type:
                self.wait_until_element(tab_locators
                                        ["provision.tab_type"]).click()
                ele = self.find_element(locators["provision.template_type"])
                Select(ele).select_by_visible_text(template_type)
            self.configure_entity(os_list, FILTER['template_os'],
                                  tab_locator=tab_locators
                                  ["provision.tab_association"],
                                  new_entity_list=new_os_list)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception("Could not update the template '%s'" % name)

    def delete(self, name, really):
        """
        Deletes a template.
        """
        self.delete_entity(name, really, locators["provision.template_select"],
                           locators["provision.template_delete"])
