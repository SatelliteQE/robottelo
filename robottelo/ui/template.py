# -*- encoding: utf-8 -*-
"""Implements Template UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Template(Base):
    """Provides the CRUD functionality for Templates."""

    def navigate_to_entity(self):
        """Navigate to Template entity page"""
        Navigator(self.browser).go_to_provisioning_templates()

    def _search_locator(self):
        """Specify locator for Template entity search procedure"""
        return locators['provision.template_select']

    def create(self, name, template_path, custom_really=None,
               audit_comment=None, template_type=None, snippet=None,
               os_list=None):
        """Creates a provisioning template from UI."""
        self.click(locators['provision.template_new'])
        self.assign_value(locators['provision.template_name'], name)
        self.click(tab_locators['tab_primary'])
        self.wait_until_element(
            locators['provision.template_template']
        ).send_keys(template_path)
        self.handle_alert(custom_really)
        self.scroll_page()
        if audit_comment:
            self.assign_value(
                locators['provision.audit_comment'], audit_comment)
        if template_type:
            self.click(tab_locators['provision.tab_type'])
            self.select(locators['provision.template_type'], template_type)
        elif snippet:
            self.click(tab_locators['provision.tab_type'])
            self.click(locators['provision.template_snippet'])
        else:
            raise UIError(
                u'Could not create template "{0}" without type'.format(name)
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
        self.search_and_click(name)
        if new_name:
            self.assign_value(locators['provision.template_name'], new_name)
        if template_path:
            self.wait_until_element(
                locators['provision.template_template']
            ).send_keys(template_path)
            self.handle_alert(custom_really)
        if template_type:
            self.click(tab_locators['provision.tab_type'])
            self.select(locators['provision.template_type'], template_type)
        if clone:
            self.click(locators['provision.template_clone'])
            self.assign_value(locators['provision.template_name'], new_name)
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
        self.click(locators['provision.template_clone'])
        if self.wait_until_element(
                locators['provision.template_name']) is None:
            raise UINoSuchElementError(
                u'Could not clone provisioning template "{0}"'
                .format(name)
            )
        self.assign_value(locators['provision.template_name'], clone_name)
        if template_path:
            self.find_element(
                locators['provision.template_template']
            ).send_keys(template_path)
            self.handle_alert(custom_really)
        if template_type:
            self.click(tab_locators['provision.tab_type'])
            self.select(locators['provision.template_type'], template_type)
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
            drop_locator=locators['provision.template_dropdown'],
        )
