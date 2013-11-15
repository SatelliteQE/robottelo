#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import locators


class Navigator(Base):
    """
    Quickly navigate through menus and tabs.
    """

    def __init__(self, browser):
        self.browser = browser

    def go_to_organization(self, org_name='ACME_Corporation'):
        #TODO: most likely will have to handle scrolling down of list
        self.find_element(locators["menu.orgselector"]).click()
        self.wait_until_element((locators["org.selected"][0], locators["org.selected"][1] % org_name)).click()

    def go_to_dashboard(self):
        self.find_element(locators["menu.dashboard"]).click()

    def go_to_subscriptions(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.subscriptions"]).click()
        self.find_element(locators["menu.redhatsubs"]).click()

    def go_to_distributors(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.subscriptions"]).click()
        self.find_element(locators["menu.distributors"]).click()

    def go_to_activation_keys(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.subscriptions"]).click()
        self.find_element(locators["menu.actkeys"]).click()

    def go_to_import_history(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.subscriptions"]).click()
        self.find_element(locators["menu.importhistory"]).click()

    def go_to_repositories(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.repos"]).click()
        self.find_element(locators["menu.redhatrepos"]).click()

    def go_to_products(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.repos"]).click()
        self.find_element(locators["menu.products"]).click()

    def go_to_gpg_keys(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.repos"]).click()
        self.find_element(locators["menu.gpgkeys"]).click()

    def go_to_sync_status(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.sync"]).click()
        self.find_element(locators["menu.syncstatus"]).click()

    def go_to_sync_plans(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.sync"]).click()
        self.find_element(locators["menu.syncplans"]).click()

    def go_to_sync_schedule(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.sync"]).click()
        self.find_element(locators["menu.syncschedule"]).click()

    def go_to_content_views(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.contentview"]).click()

    def go_to_content_search(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.contentsearch"]).click()

    def go_to_changesets_management(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.changesets"]).click()
        self.find_element(locators["menu.changesetsmanage"]).click()

    def go_to_changesets_history(self):
        self.find_element(locators["menu.content"]).click()
        self.find_element(locators["menu.changesets"]).click()
        self.find_element(locators["menu.changesetshistory"]).click()

    def go_to_systems_all(self):
        self.find_element(locators["menu.systems"]).click()
        self.find_element(locators["menu.systemsall"]).click()

    def go_to_system_groups(self):
        self.find_element(locators["menu.systems"]).click()
        self.find_element(locators["menu.systemgroups"]).click()

    def go_to_organizations(self):
        self.find_element(locators["menu.administer"]).click()
        self.find_element(locators["menu.organizations"]).click()

    def go_to_users(self):
        self.find_element(locators["menu.administer"]).click()
        self.find_element(locators["menu.users"]).click()

    def go_to_roles(self):
        self.find_element(locators["menu.administer"]).click()
        self.find_element(locators["menu.roles"]).click()

    def go_to_about(self):
        self.find_element(locators["menu.administer"]).click()
        self.find_element(locators["menu.about"]).click()
