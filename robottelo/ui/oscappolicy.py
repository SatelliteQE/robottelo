# -*- encoding: utf-8 -*-
"""Implements Open Scap Policy for UI."""
from robottelo.ui.base import Base, UIError
from robottelo.common.constants import FILTER
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator


class OpenScapPolicy(Base):
    """Manipulates OpenScap Policy from UI"""

    def create(self, name, desc=None, content=None, profile=None, period=None,
               weekday=None, org=None, loc=None, host_group=None):
        """Creates new Openscap policy from UI"""
        self.click(locators['oscap.new_policy'])
        if not self.wait_until_element(locators['oscap.name_policy']):
            raise UIError(u'Could not create new policy {0}'.format(name))
        self.text_field_update(locators['oscap.name_policy'], name)
        if desc:
            self.text_field_update(locators['oscap.desc_policy'], desc)
        self.click(common_locators['submit'])
        self.select(locators['oscap.content_policy'], content)
        self.select(locators['oscap.profile_policy'], profile)
        self.click(common_locators['submit'])
        self.select(locators['oscap.period_policy'], period)
        self.select(locators['oscap.weekday_policy'], weekday)
        self.click(common_locators['submit'])
        if loc:
            self.configure_entity([loc], FILTER['policy_loc'])
        self.click(common_locators['submit'])
        if org:
            self.configure_entity([org], FILTER['policy_org'])
        self.click(common_locators['submit'])
        self.configure_entity([host_group], FILTER['policy_hgrp'])
        self.click(common_locators['submit'])

    def search(self, name):
        """Searches existing oscap policy from UI"""
        self.wait_for_ajax()
        Navigator(self.browser).go_to_oscap_policy()
        strategy, value = common_locators['search']
        return self.wait_until_element((strategy, value % name))

    def delete(self, name, really=True):
        """Delete existing oscap policy from UI"""
        Navigator(self.browser).go_to_oscap_policy()
        strategy, value = locators['oscap.delete_policy']
        self.wait_until_element((strategy, value % name)).click()
        self.handle_alert(really)
