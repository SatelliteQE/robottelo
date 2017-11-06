# -*- encoding: utf-8 -*-
"""Implements Audit UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Audit(Base):
    """Manipulates Audit from UI"""

    def navigate_to_entity(self):
        """Navigate to Audit entity page"""
        Navigator(self.browser).go_to_audits()

    def _search_locator(self):
        """There is no locator in Audit that can be directly associated with
        search result
        """
        return None

    def filter(self, query):
        """Filter Audit logs to represent only necessary entities"""
        self.navigate_to_entity()
        self.assign_value(common_locators['search'], query)
        self.click(common_locators['search_button'])

    def get_last_entry(self):
        """Read last entity from audit logs and return its values in a
        dictionary
        """
        audit_type = self.wait_until_element(
            locators['audit.type'] % 1).text.lstrip()
        full_audit_statement = self.wait_until_element(
            locators['audit.full_statement'] % 1).text
        user_name = self.wait_until_element(locators['audit.user'] % 1).text
        entity_name = self.wait_until_element(
            locators['audit.entity_name'] % 1).text
        update_list = None
        if 'updated' or 'added' in full_audit_statement:
            update_list = self.wait_until_element(
                locators['audit.update_list'] % 1).text.split('\n')
        return {
            'type': audit_type,
            'full_statement': full_audit_statement,
            'user_name': user_name,
            'entity_name': entity_name,
            'update_list': update_list,
        }
