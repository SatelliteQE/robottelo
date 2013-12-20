#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Navigator UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.common.action_chains import ActionChains


class Navigator(Base):
    """
    Quickly navigate through menus and tabs.
    """

    def __init__(self, browser):
        self.browser = browser

    def menu_click(self, top_menu_locator, sub_menu_locator):
        #import epdb; epdb.st()
        menu_element = self.find_element(top_menu_locator)

        if menu_element:
            ActionChains(self.browser).move_to_element(menu_element).perform()
            submenu_element = self.find_element(sub_menu_locator)
            if submenu_element:
                submenu_element.click()

    def go_to_dashboard(self):
        self.menu_click(
            locators['menu.monitor'], locators['menu.dashboard'],
        )

    def go_to_reports(self):
        self.menu_click(
            locators['menu.monitor'], locators['menu.reports'],
        )

    def go_to_facts(self):
        self.menu_click(
            locators['menu.monitor'], locators['menu.facts'],
        )

    def go_to_statistics(self):
        self.menu_click(
            locators['menu.monitor'], locators['menu.statistics'],
        )

    def go_to_trends(self):
        self.menu_click(
            locators['menu.monitor'], locators['menu.trends'],
        )

    def go_to_audits(self):
        self.menu_click(
            locators['menu.monitor'], locators['menu.audits'],
        )

    def go_to_hosts(self):
        self.menu_click(
            locators['menu.hosts'], locators['menu.all_hosts'],
        )

    def go_to_operating_systems(self):
        self.menu_click(
            locators['menu.hosts'], locators['menu.operating_systems'],
        )

    def go_to_provisioning_templates(self):
        self.menu_click(
            locators['menu.hosts'], locators['menu.provisioning_templates'],
        )

    def go_to_partition_tables(self):
        self.menu_click(
            locators['menu.hosts'], locators['menu.partition_tables'],
        )

    def go_to_installation_media(self):
        self.menu_click(
            locators['menu.hosts'], locators['menu.installation_media'],
        )

    def go_to_hardware_models(self):
        self.menu_click(
            locators['menu.hosts'], locators['menu.hardware_models'],
        )

    def go_to_architectures(self):
        self.menu_click(
            locators['menu.hosts'], locators['menu.architectures'],
        )

    def go_to_host_groups(self):
        self.menu_click(
            locators['menu.configure'], locators['menu.host_groups'],
        )

    def go_to_global_parameters(self):
        self.menu_click(
            locators['menu.configure'], locators['menu.global_parameters'],
        )

    def go_to_environments(self):
        self.menu_click(
            locators['menu.configure'], locators['menu.environments'],
        )

    def go_to_puppet_classes(self):
        self.menu_click(
            locators['menu.configure'], locators['menu.puppet_classes'],
        )

    def go_to_smart_variables(self):
        self.menu_click(
            locators['menu.configure'], locators['menu.'],
        )

    def go_to_smart_proxies(self):
        self.menu_click(
            locators['menu.infrastructure'], locators['menu.smart_proxies'],
        )

    def go_to_compute_resources(self):
        self.menu_click(
            locators['menu.infrastructure'],
            locators['menu.compute_resources'],
        )

    def go_to_subnets(self):
        self.menu_click(
            locators['menu.infrastructure'], locators['menu.subnets'],
        )

    def go_to_domains(self):
        self.menu_click(
            locators['menu.infrastructure'], locators['menu.domains'],
        )

    def go_to_ldap_auth(self):
        self.menu_click(
            locators['menu.administer'], locators['menu.ldap_auth'],
        )

    def go_to_users(self):
        self.menu_click(
            locators['menu.administer'], locators['menu.users'],
        )

    def go_to_user_groups(self):
        self.menu_click(
            locators['menu.administer'], locators['menu.user_groups'],
        )

    def go_to_roles(self):
        self.menu_click(
            locators['menu.administer'], locators['menu.roles'],
        )

    def go_to_bookmarks(self):
        self.menu_click(
            locators['menu.administer'], locators['menu.bookmarks'],
        )

    def go_to_settings(self):
        self.menu_click(
            locators['menu.administer'], locators['menu.settings'],
        )

    def go_to_about(self):
        self.menu_click(
            locators['menu.administer'], locators['menu.about'],
        )

    def go_to_sign_out(self):
        self.menu_click(
            locators['menu.account'], locators['menu.sign_out'],
        )

    def go_to_my_account(self):
        self.menu_click(
            locators['menu.account'], locators['menu.my_account'],
        )
