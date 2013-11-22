#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import locators
from selenium.webdriver.common.action_chains import ActionChains


class Navigator(Base):
    """
    Quickly navigate through menus and tabs.
    """

    def __init__(self, browser):
        self.browser = browser

    def more_menu_move_to(self, menu_name):
        menu_element = self.browser.find_element_by_xpath("//div[contains(@style,'static')]//ul[@id='menu2']//a[normalize-space(.)='{0}']".format(menu_name))
        ActionChains(self.browser).move_to_element(menu_element).perform()
        return menu_element

    def more_menu_click(self, menu_name):
        menu_element = self.browser.find_element_by_xpath("//div[contains(@style,'static')]//ul[@id='menu2']//a[normalize-space(.)='{0}']".format(menu_name))
        ActionChains(self.browser).move_to_element(menu_element).perform()
        menu_element.click()

    def click_menu(self, menu_name):
        menu_element = self.browser.find_element_by_xpath("//div[contains(@style,'static')]//a[normalize-space(.)='{0}']".format(menu_name)).click()
        return menu_element

    def go_to_more(self):
        self.find_element(locators["menu.more"]).click()
        self.wait_for_ajax()

    def go_to_dashboard(self):
        self.click_menu("Dashboard")

    def go_to_hosts(self):
        self.click_menu("Hosts")

    def go_to_reports(self):
        self.click_menu("Reports")

    def go_to_facts(self):
        self.click_menu("Facts")

    def go_to_audits(self):
        self.click_menu("Audits")

    def go_to_statistics(self):
        self.click_menu("Statistics")

    def go_to_trends(self):
        self.click_menu("Trends")

    def go_to_configuration(self):
        self.more_menu_move_to('Configuration')
        self.more_menu_move_to('Environments')
        self.wait_for_ajax()

    def go_to_environments(self):
        self.go_to_configuration()
        self.more_menu_click('Environments')

    def go_to_global_parameters(self):
        self.go_to_configuration()
        self.more_menu_click('Global Parameters')

    def go_to_host_groups(self):
        self.go_to_configuration()
        self.more_menu_click('Host Groups')

    def go_to_puppet_classes(self):
        self.go_to_configuration()
        self.more_menu_click('Puppet Classes')

    def go_to_smart_variables(self):
        self.go_to_configuration()
        self.more_menu_click('Smart Variables')

    def go_to_smart_proxies(self):
        self.go_to_configuration()
        self.more_menu_click('Smart Proxies')

    def go_to_provisioning(self):
        self.more_menu_move_to('Provisioning')
        self.wait_for_ajax()
        self.more_menu_move_to('Architectures')
        self.wait_for_ajax()

    def go_to_architectures(self):
        self.go_to_provisioning()
        self.more_menu_click('Architectures')
        self.wait_for_ajax()

    def go_to_compute_resources(self):
        self.go_to_provisioning()
        self.more_menu_click('Compute Resources')

    def go_to_domains(self):
        self.go_to_provisioning()
        self.more_menu_click('Domains')

    def go_to_hardware_models(self):
        self.go_to_provisioning()
        self.more_menu_click('Hardware Models')

    def go_to_installation_media(self):
        self.go_to_provisioning()
        self.more_menu_click('Installation Media')

    def go_to_operating_systems(self):
        self.go_to_provisioning()
        self.more_menu_click('Operating Systems')

    def go_to_partition_tables(self):
        self.go_to_provisioning()
        self.more_menu_click('Partition Tables')

    def go_to_provisioning_templates(self):
        self.go_to_provisioning()
        self.more_menu_click('Provisioning Templates')

    def go_to_subnets(self):
        self.go_to_provisioning()
        self.more_menu_click('Subnets')

    def go_to_users_menu(self):
        self.go_to_more()
        self.more_menu_move_to('Users')
        self.more_menu_move_to('LDAP Authentication')
        self.wait_for_ajax()

    def go_to_ldap_authentication(self):
        self.go_to_users_menu()
        self.more_menu_click('LDAP Authentication')

    def go_to_users(self):
        self.go_to_users_menu()
        self.more_menu_click('Users')

    def go_to_user_groups(self):
        self.go_to_users_menu()
        self.more_menu_click('User Groups')

    def go_to_roles(self):
        self.go_to_users_menu()
        self.more_menu_click('Roles')
