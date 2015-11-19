# -*- encoding: utf-8 -*-
"""Implements Template UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class Template(Base):
    """Provides the CRUD functionality for Templates."""

    def navigate_to_entity(self):
        """Navigate to Template entity page"""
        Navigator(self.browser).go_to_provisioning_templates()

    def _search_locator(self):
        """Specify locator for Template entity search procedure"""
        return locators['provision.template_select']

    def create(self, name, template_path=None, custom_really=None,
               audit_comment=None, template_type=None, snippet=None,
               os_list=None):
        """Creates a provisioning template from UI."""
        self.click(locators['provision.template_new'])
        if self.wait_until_element(
                locators['provision.template_name']) is None:
            raise UINoSuchElementError(
                'Could not create new provisioning template "{0}"'
                .format(name)
            )
        self.find_element(locators['provision.template_name']).send_keys(name)
        if not template_path:
            raise UIError(
                'Could not create blank template "{0}"'.format(name)
            )
        self.click(tab_locators['tab_primary'])
        self.find_element(
            locators['provision.template_template']
        ).send_keys(template_path)
        self.handle_alert(custom_really)
        self.scroll_page()
        if audit_comment:
            self.find_element(
                locators['provision.audit_comment']
            ).send_keys(audit_comment)
        if template_type:
            self.click(tab_locators['provision.tab_type'])
            type_element = self.find_element(
                locators['provision.template_type'])
            Select(type_element).select_by_visible_text(template_type)
        elif snippet:
            self.click(tab_locators['provision.tab_type'])
            self.click(locators['provision.template_snippet'])
        else:
            raise UIError(
                'Could not create template "{0}" without type'.format(name)
            )
        self.scroll_page()
        self.configure_entity(
            os_list,
            FILTER['template_os'],
            tab_locator=tab_locators['provision.tab_association'])
        self.click(common_locators['submit'])

    def update(self, name, custom_really=None, new_name=None,
               template_path=None, template_type=None,
               os_list=None, new_os_list=None, clone=False):
        """Updates a given template."""
        element = self.search(name)
        if element is None:
            raise UIError(
                'Could not update the template "{0}"'.format(name)
            )
        element.click()
        self.wait_for_ajax()
        if new_name:
            self.field_update('provision.template_name', new_name)
        if template_path:
            self.find_element(
                locators['provision.template_template']
            ).send_keys(template_path)
            self.handle_alert(custom_really)
        if template_type:
            self.click(tab_locators['provision.tab_type'])
            element = self.find_element(locators['provision.template_type'])
            Select(element).select_by_visible_text(template_type)
        if clone:
            self.click(locators['provision.template_clone'])
            self.field_update('provision.template_name', new_name)
        self.configure_entity(
            os_list,
            FILTER['template_os'],
            tab_locator=tab_locators['provision.tab_association'],
            new_entity_list=new_os_list
        )
        self.click(common_locators['submit'])

    def clone(self, name, custom_really=None, clone_name=None,
              template_path=None, template_type=None,
              os_list=None):
        """Clones a given template."""
        self.search(name)
        clone = self.wait_until_element(locators['provision.template_clone'])
        if clone is None:
            raise UINoSuchElementError(
                'Could not locate the clone button for template "{0}"'
                .format(name)
            )
        clone.click()
        self.wait_for_ajax()
        self.field_update('provision.template_name', clone_name)
        if template_path:
            self.find_element(
                locators['provision.template_template']
            ).send_keys(template_path)
            self.handle_alert(custom_really)
        if template_type:
            self.click(tab_locators['provision.tab_type'])
            element = self.find_element(
                locators['provision.template_type'])
            Select(element).select_by_visible_text(template_type)
        self.configure_entity(
            os_list,
            FILTER['template_os'],
            tab_locator=tab_locators['provision.tab_association']
        )
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Deletes a template."""
        self.delete_entity(
            name,
            really,
            locators['provision.template_delete'],
            locators['provision.template_dropdown'],
        )
