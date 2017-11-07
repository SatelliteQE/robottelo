# -*- encoding: utf-8 -*-
"""Implements Open Scap Policy for UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class OpenScapPolicy(Base):
    """Manipulates OpenScap Policy from UI"""

    def navigate_to_entity(self):
        """Navigate to OpenScap Policy entity page"""
        Navigator(self.browser).go_to_oscap_policy()

    def _search_locator(self):
        """Specify locator for OpenScap Policy entity search procedure"""
        return locators['oscap.select_policy']

    def create(self, name, desc=None, content=None, profile=None,
               tailoring=None, tailoring_profile=None, period=None,
               period_value=None, org=None, loc=None, host_group=None):
        """Creates new Openscap policy from UI"""
        self.click(locators['oscap.new_policy'])
        if not self.wait_until_element(locators['oscap.name_policy']):
            raise UIError(u'Could not create new policy {0}'.format(name))
        self.assign_value(locators['oscap.name_policy'], name)
        if desc:
            self.assign_value(locators['oscap.desc_policy'], desc)
        self.click(common_locators['submit'])
        if self.wait_until_element(common_locators['haserror']):
            return
        if content:
            self.select(locators['oscap.content_policy'], content)
        if profile:
            self.select(locators['oscap.profile_policy'], profile)
        if tailoring:
            self.select(locators['oscap.tailoring_file_policy'], tailoring)
        if tailoring_profile:
            self.select(locators['oscap.tailoring_profile_policy'],
                        tailoring_profile)
        self.click(common_locators['submit'])
        self.select(locators['oscap.period_policy'], period)
        if period == 'Weekly':
            self.select(locators['oscap.weekday_policy'], period_value)
        elif period == 'Monthly':
            self.select(
                locators['oscap.dayofmonth_policy'], period_value)
        else:
            self.assign_value(
                locators['oscap.custom_policy'], period_value)
        self.click(common_locators['submit'])
        if loc:
            self.configure_entity([loc], FILTER['policy_loc'])
        self.click(common_locators['submit'])
        if org:
            self.configure_entity([org], FILTER['policy_org'])
        self.click(common_locators['submit'])
        if host_group:
            self.configure_entity([host_group], FILTER['policy_hgrp'])
        self.click(common_locators['submit'])

    def update(self, name, new_name, new_desc=None, content=None, profile=None,
               period=None, period_value=None, org=None, loc=None,
               host_group=None):
        """Updates existing Oscap Policy from UI"""
        element = self.search(name)
        if not element:
            raise UIError('Could not find oscap policy {0}'.format(name))
        self.click(locators['oscap.dropdown_policy'] % name)
        self.click(locators['oscap.edit_policy'] % name, waiter_timeout=60)
        if new_name:
            self.assign_value(locators['oscap.name_policy'], new_name)
        if new_desc:
            self.assign_value(locators['oscap.desc_policy'], new_desc)
        if content or profile:
            self.click(tab_locators['oscap.content'])
            if content:
                self.select(locators['oscap.content_policy'], content)
            if profile:
                self.select(locators['oscap.profile_policy'], profile)
        if period or period_value:
            self.click(tab_locators['oscap.schedule'])
            self.select(locators['oscap.period_policy'], period)
            if period == 'Weekly':
                self.select(locators['oscap.weekday_policy'], period_value)
            elif period == 'Monthly':
                self.assign_value(
                    locators['oscap.dayofmonth_policy'], period_value)
            else:
                self.assign_value(
                    locators['oscap.custom_policy'], period_value)
        if loc:
            self.click(tab_locators['tab_loc'])
            self.configure_entity([loc], FILTER['policy_loc'])
        if org:
            self.click(tab_locators['tab_org'])
            self.configure_entity([org], FILTER['policy_org'])
        if host_group:
            self.click(tab_locators['context.tab_hostgrps'])
            self.configure_entity([host_group], FILTER['policy_hgrp'])
        self.click(common_locators['submit'])
