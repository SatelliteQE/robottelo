# -*- encoding: utf-8 -*-
"""Implements Open Scap Policy for UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator


class OpenScapPolicy(Base):
    """Manipulates OpenScap Policy from UI"""

    def navigate_to_entity(self):
        """Navigate to OpenScap Policy entity page"""
        Navigator(self.browser).go_to_oscap_policy()

    def _search_locator(self):
        """Specify locator for OpenScap Policy entity search procedure"""
        return locators['oscap.select_policy']

    def create(self, name, desc=None, content=None, profile=None, period=None,
               period_value=None, org=None, loc=None, host_group=None):
        """Creates new Openscap policy from UI"""
        self.click(locators['oscap.new_policy'])
        if not self.wait_until_element(locators['oscap.name_policy']):
            raise UIError(u'Could not create new policy {0}'.format(name))
        self.text_field_update(locators['oscap.name_policy'], name)
        if desc:
            self.text_field_update(locators['oscap.desc_policy'], desc)
        self.click(common_locators['submit'])
        if content:
            self.select(locators['oscap.content_policy'], content)
        if profile:
            self.select(locators['oscap.profile_policy'], profile)
        self.click(common_locators['submit'])
        self.select(locators['oscap.period_policy'], period)
        if period == 'Weekly':
            self.select(locators['oscap.weekday_policy'], period_value)
        elif period == 'Monthly':
            self.text_field_update(
                locators['oscap.dayofmonth_policy'], period_value)
        else:
            self.text_field_update(
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

    def delete(self, name, really=True):
        """Delete existing oscap policy from UI"""
        self.delete_entity(
            name,
            really,
            locators['oscap.delete_policy'],
            locators['oscap.dropdown_policy'],
        )
