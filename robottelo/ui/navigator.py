# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Navigator UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import menu_locators
from selenium.webdriver.common.action_chains import ActionChains


class Navigator(Base):
    """
    Quickly navigate through menus and tabs.
    """

    def __init__(self, browser):
        self.browser = browser

    def menu_click(self, top_menu_locator, sub_menu_locator,
                   tertiary_menu_locator=None, entity=None):
        menu_element = self.find_element(top_menu_locator)

        if menu_element:
            ActionChains(self.browser).move_to_element(menu_element).perform()
            submenu_element = self.wait_until_element(sub_menu_locator)
            if submenu_element and not tertiary_menu_locator:
                submenu_element.click()
            elif submenu_element and tertiary_menu_locator:
                ActionChains(self.browser).move_to_element(submenu_element).\
                    perform()
                if entity:
                    strategy = tertiary_menu_locator[0]
                    value = tertiary_menu_locator[1]
                    tertiary_element = self.\
                        wait_until_element((strategy,
                                            value % entity))
                else:
                    tertiary_element = self.\
                        wait_until_element(tertiary_menu_locator)
                if tertiary_element:
                    self.browser.execute_script("arguments[0].click();",
                                                tertiary_element)

    def go_to_dashboard(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.dashboard'],
        )

    def go_to_content_dashboard(self):
        self.menu_click(
            menu_locators['menu.monitor'],
            menu_locators['menu.content_dashboard'],
        )

    def go_to_reports(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.reports'],
        )

    def go_to_facts(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.facts'],
        )

    def go_to_statistics(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.statistics'],
        )

    def go_to_trends(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.trends'],
        )

    def go_to_audits(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.audits'],
        )

    def go_to_life_cycle_environments(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.life_cycle_environments'],
        )

    def go_to_red_hat_subscriptions(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.red_hat_subscriptions'],
        )

    def go_to_subscription_manager_applications(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.subscription_manager_applications'],
        )

    def go_to_activation_keys(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.activation_keys'],
        )

    def go_to_red_hat_repositories(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.red_hat_repositories'],
        )

    def go_to_products(self):
        self.menu_click(
            menu_locators['menu.content'], menu_locators['menu.products'],
        )

    def go_to_gpg_keys(self):
        self.menu_click(
            menu_locators['menu.content'], menu_locators['menu.gpg_keys'],
        )

    def go_to_sync_status(self):
        self.menu_click(
            menu_locators['menu.content'], menu_locators['menu.sync_status'],
        )

    def go_to_sync_plans(self):
        self.menu_click(
            menu_locators['menu.content'], menu_locators['menu.sync_plans'],
        )

    def go_to_sync_schedules(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.sync_schedules'],
        )

    def go_to_content_view_definitions(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.content_view_definitions'],
        )

    def go_to_content_search(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.content_search'],
        )

    def go_to_changeset_management(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.changeset_management'],
        )

    def go_to_changeset_history(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.changeset_history'],
        )

    def go_to_hosts(self):
        self.menu_click(
            menu_locators['menu.hosts'], menu_locators['menu.all_hosts'],
        )

    def go_to_registered_systems(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.registered_systems'],
        )

    def go_to_system_groups(self):
        self.menu_click(
            menu_locators['menu.hosts'], menu_locators['menu.system_groups'],
        )

    def go_to_operating_systems(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.operating_systems'],
        )

    def go_to_provisioning_templates(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.provisioning_templates'],
        )

    def go_to_partition_tables(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.partition_tables'],
        )

    def go_to_installation_media(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.installation_media'],
        )

    def go_to_hardware_models(self):
        self.menu_click(
            menu_locators['menu.hosts'], menu_locators['menu.hardware_models'],
        )

    def go_to_architectures(self):
        self.menu_click(
            menu_locators['menu.hosts'], menu_locators['menu.architectures'],
        )

    def go_to_host_groups(self):
        self.menu_click(
            menu_locators['menu.configure'], menu_locators['menu.host_groups'],
        )

    def go_to_global_parameters(self):
        self.menu_click(
            menu_locators['menu.configure'],
            menu_locators['menu.global_parameters'],
        )

    def go_to_environments(self):
        self.menu_click(
            menu_locators['menu.configure'],
            menu_locators['menu.environments'],
        )

    def go_to_puppet_classes(self):
        self.menu_click(
            menu_locators['menu.configure'],
            menu_locators['menu.puppet_classes'],
        )

    def go_to_smart_variables(self):
        self.menu_click(
            menu_locators['menu.configure'], menu_locators['menu.'],
        )

    def go_to_smart_proxies(self):
        self.menu_click(
            menu_locators['menu.infrastructure'],
            menu_locators['menu.smart_proxies'],
        )

    def go_to_compute_resources(self):
        self.menu_click(
            menu_locators['menu.infrastructure'],
            menu_locators['menu.compute_resources'],
        )

    def go_to_subnets(self):
        self.menu_click(
            menu_locators['menu.infrastructure'],
            menu_locators['menu.subnets'],
        )

    def go_to_domains(self):
        self.menu_click(
            menu_locators['menu.infrastructure'],
            menu_locators['menu.domains'],
        )

    def go_to_ldap_auth(self):
        self.menu_click(
            menu_locators['menu.administer'], menu_locators['menu.ldap_auth'],
        )

    def go_to_users(self):
        self.menu_click(
            menu_locators['menu.administer'], menu_locators['menu.users'],
        )

    def go_to_user_groups(self):
        self.menu_click(
            menu_locators['menu.administer'],
            menu_locators['menu.user_groups'],
        )

    def go_to_roles(self):
        self.menu_click(
            menu_locators['menu.administer'], menu_locators['menu.roles'],
        )

    def go_to_bookmarks(self):
        self.menu_click(
            menu_locators['menu.administer'], menu_locators['menu.bookmarks'],
        )

    def go_to_settings(self):
        self.menu_click(
            menu_locators['menu.administer'], menu_locators['menu.settings'],
        )

    def go_to_about(self):
        self.menu_click(
            menu_locators['menu.administer'], menu_locators['menu.about'],
        )

    def go_to_sign_out(self):
        self.menu_click(
            menu_locators['menu.account'], menu_locators['menu.sign_out'],
        )

    def go_to_my_account(self):
        self.menu_click(
            menu_locators['menu.account'], menu_locators['menu.my_account'],
        )

    def go_to_org(self):
        self.menu_click(
            menu_locators['org.any_context'], menu_locators['org.manage_org'],
        )

    def go_to_select_org(self, org):
        self.menu_click(
            menu_locators['org.any_context'],
            menu_locators['org.nav_current_org'],
            menu_locators['org.select_org'], entity=org
        )
        current_org = self.wait_until_element(menu_locators
                                              ['org.current_org']).text
        if org == str(current_org):
            return org
        else:
            raise Exception(
                "Could not select the org: '%s'" % org)
