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

    def click_menu(self, menu_name, position=1):
        script = "return document.getElementsByClassName('%s')[1];" % menu_name
        menu_element = self.browser.execute_script(script)
        menu_element.find_element_by_tag_name('a').click()

        return menu_element

    def go_to_dashboard(self):
        self.find_element(locators["menu.dashboard"]).click()
        self.click_menu("menu_tab_dashboard")

    def go_to_hosts(self):
        self.click_menu("menu_tab_hosts")

    def go_to_reports(self):
        self.click_menu("menu_tab_reports")

    def go_to_facts(self):
        self.click_menu("menu_tab_facts")

    def go_to_audits(self):
        self.click_menu("menu_tab_audits")

    def go_to_statistics(self):
        self.click_menu("menu_tab_statistics")

    def go_to_trends(self):
        self.click_menu("menu_tab_trends")

    def go_to_more(self):
        return self.click_menu("menu_tab_settings")

    def go_to_configuration(self):
        menu = self.go_to_more()
        submenu = menu.find_elements_by_xpath("//ul/li[@class='dropdown-submenu']/a")[3]
        ActionChains(self.browser).move_to_element(submenu).perform()

    def go_to_environments(self):
        self.go_to_configuration()
        self.browser.execute_script("window.location.href='/environments'")
        #self.browser.find_element_by_xpath("//a[@href='/environments']").click()

    def go_to_global_parameters(self):
        self.go_to_configuration()
        self.browser.execute_script("window.location.href='/common_parameters'")
        #self.browser.find_element_by_xpath("//a[@href='/common_parameters']").click()

    def go_to_host_groups(self):
        self.go_to_configuration()
        self.browser.execute_script("window.location.href='/hostgroups'")
        #self.browser.find_element_by_xpath("//a[@href='/hostgroups']").click()

    def go_to_puppet_classes(self):
        self.go_to_configuration()
        self.browser.execute_script("window.location.href='/puppetclasses'")
        #self.browser.find_element_by_xpath("//a[@href='/puppetclasses']").click()

    def go_to_smart_variables(self):
        self.go_to_configuration()
        self.browser.execute_script("window.location.href='/lookup_keys'")
        #self.browser.find_element_by_xpath("//a[@href='/lookup_keys']").click()

    def go_to_smart_proxies(self):
        self.go_to_configuration()
        self.browser.execute_script("window.location.href='/smart_proxies'")
        #self.browser.find_element_by_xpath("//a[@href='/smart_proxies']").click()

    def go_to_provisioning(self):
        menu = self.go_to_more()
        submenu = menu.find_elements_by_xpath("//ul/li[@class='dropdown-submenu']/a")[4]
        ActionChains(self.browser).move_to_element(submenu).perform()

    def go_to_architectures(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/architectures'")
        #self.browser.find_element_by_xpath("//a[@href='/architectures']").click()

    def go_to_compute_resources(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/compute_resources'")
        #self.browser.find_element_by_xpath("//a[@href='/compute_resources']").click()

    def go_to_domains(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/domains'")
        #self.browser.find_element_by_xpath("//a[@href='/domains']").click()

    def go_to_hardware_models(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/models'")
        #self.browser.find_element_by_xpath("//a[@href='/models']").click()

    def go_to_installation_media(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/media'")
        #self.browser.find_element_by_xpath("//a[@href='/media']").click()

    def go_to_operating_systems(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/operating_systems'")
        #self.browser.find_element_by_xpath("//a[@href='/operating_systems']").click()

    def go_to_partition_tables(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/ptables'")
        #self.browser.find_element_by_xpath("//a[@href='/ptables']").click()

    def go_to_provisioning_templates(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/config_templates'")
        #self.browser.find_element_by_xpath("//a[@href='/config_templates']").click()

    def go_to_subnets(self):
        self.go_to_provisioning()
        self.browser.execute_script("window.location.href='/subnets'")
        #self.browser.find_element_by_xpath("//a[@href='/subnets']").click()

    def go_to_users(self):
        menu = self.go_to_more()
        submenu = menu.find_elements_by_xpath("//ul/li[@class='dropdown-submenu']/a")[5]
        ActionChains(self.browser).move_to_element(submenu).perform()
