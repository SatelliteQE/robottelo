# -*- encoding: utf-8 -*-
"""Implements Navigator UI."""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import menu_locators


class Navigator(Base):
    """Quickly navigate through menus and tabs."""

    def menu_click(self, top_menu_locator, sub_menu_locator,
                   tertiary_menu_locator=None):
        self.perform_action_chain_move(top_menu_locator)
        if not tertiary_menu_locator:
            self.click(sub_menu_locator, scroll=False)
        else:
            self.perform_action_chain_move(sub_menu_locator)
            tertiary_element = self.wait_until_element(
                tertiary_menu_locator)
            self.browser.execute_script(
                "arguments[0].click();",
                tertiary_element,
            )
        self.browser.refresh()
        self.wait_for_ajax()

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

    def go_to_content_views(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.content_views'],
        )

    def go_to_content_search(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.content_search'],
        )

    def go_to_all_containers(self):
        self.menu_click(
            menu_locators['menu.containers'],
            menu_locators['menu.all_containers'],
        )

    def go_to_new_container(self):
        self.menu_click(
            menu_locators['menu.containers'],
            menu_locators['menu.new_container'],
        )

    def go_to_registries(self):
        self.menu_click(
            menu_locators['menu.containers'],
            menu_locators['menu.registries'],
        )

    def go_to_hosts(self):
        self.menu_click(
            menu_locators['menu.hosts'], menu_locators['menu.all_hosts'],
        )

    def go_to_discovered_hosts(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.discovered_hosts'],
        )

    def go_to_content_hosts(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.content_hosts'],
        )

    def go_to_host_collections(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.host_collections'],
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

    def go_to_discovery_rules(self):
        self.menu_click(
            menu_locators['menu.configure'],
            menu_locators['menu.discovery_rules'],
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
            menu_locators['menu.configure'],
            menu_locators['menu.smart_variables'],
        )

    def go_to_config_groups(self):
        self.menu_click(
            menu_locators['menu.configure'],
            menu_locators['menu.configure_groups']
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

    def go_to_compute_profiles(self):
        self.menu_click(
            menu_locators['menu.infrastructure'],
            menu_locators['menu.compute_profiles'],
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
            menu_locators['menu.any_context'], menu_locators['org.manage_org'],
        )

    def go_to_loc(self):
        self.menu_click(
            menu_locators['menu.any_context'], menu_locators['loc.manage_loc'],
        )

    def go_to_logout(self):
        self.menu_click(
            menu_locators['menu.account'], menu_locators['menu.sign_out'],
        )

    def go_to_insights_overview(self):
        """Navigates to Red Hat Access Insights Overview"""
        self.menu_click(
            menu_locators['menu.insights'],
            menu_locators['insights.overview']
        )

    def go_to_insights_rules(self):
        """Navigates to Red Hat Access Insights Rules"""
        self.menu_click(
            menu_locators['menu.insights'],
            menu_locators['insights.rules'],
        )

    def go_to_insights_systems(self):
        """ Navigates to Red Hat Access Insights Systems"""
        self.menu_click(
            menu_locators['menu.insights'],
            menu_locators['insights.systems'],
        )

    def go_to_insights_manage(self):
        """ Navigates to Red Hat Access Insights Manage Systems"""
        self.menu_click(
            menu_locators['menu.insights'],
            menu_locators['insights.manage'],
        )

    def go_to_oscap_policy(self):
        """ Navigates to Oscap Policy"""
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.oscap_policy'],
        )

    def go_to_oscap_content(self):
        """Navigates to Oscap Content"""
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.oscap_content'],
        )

    def go_to_oscap_reports(self):
        """Navigates to Oscap Reports"""
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.oscap_reports'],
        )

    def go_to_select_org(self, org):
        """Selects the specified organization.

        :param str org: The organization to select.
        :return: Returns the organization.
        :rtype: str

        """
        strategy, value = menu_locators['org.select_org']
        self.menu_click(
            menu_locators['menu.any_context'],
            menu_locators['org.nav_current_org'],
            (strategy, value % org),
        )
        self.perform_action_chain_move(menu_locators['menu.current_text'])
        if self.wait_until_element(
                menu_locators['menu.fetch_org']).text != org:
            raise UIError(
                u'Could not select the organization: {0}'.format(org)
            )
        # close dropdown
        self.click(menu_locators['menu.current_text'])
        # get to left corner of the browser instance to not have impact on
        # further actions
        self.perform_action_chain_move_by_offset(-150, -150)
        return org

    def go_to_select_loc(self, loc):
        """Selects the specified location.

        :param str loc: The location to select.
        :return: Returns the location.
        :rtype: str

        """
        strategy, value = menu_locators['loc.select_loc']
        self.menu_click(
            menu_locators['menu.any_context'],
            menu_locators['loc.nav_current_loc'],
            (strategy, value % loc),
        )
        self.perform_action_chain_move(menu_locators['menu.current_text'])
        if self.wait_until_element(
                menu_locators['menu.fetch_loc']).text != loc:
            raise UIError(
                u'Could not select the location: {0}'.format(loc)
            )
        # close dropdown
        self.click(menu_locators['menu.current_text'])
        # get to left corner of the browser instance to not have impact on
        # further actions
        self.perform_action_chain_move_by_offset(-150, -150)
        return loc
