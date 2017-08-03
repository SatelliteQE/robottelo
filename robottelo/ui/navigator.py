# -*- encoding: utf-8 -*-
"""Implements Navigator UI."""
from robottelo.decorators import bz_bug_is_open
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
        # 1328627 - as the number of subs increases, dashboard page gets slower
        wait_timeout = 12
        if bz_bug_is_open(1328627):
            wait_timeout = 40
        self.wait_until_element_is_not_visible(
            menu_locators['navbar.spinner'],
            timeout=wait_timeout
        )
        self.wait_for_ajax()

    def go_to_dashboard(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.dashboard'],
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

    def go_to_jobs(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.jobs'],
        )

    def go_to_tasks(self):
        self.menu_click(
            menu_locators['menu.monitor'], menu_locators['menu.tasks'],
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

    def go_to_content_views(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.content_views'],
        )

    def go_to_errata(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.errata'],
        )

    def go_to_packages(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.packages'],
        )

    def go_to_puppet_modules(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.puppet_modules'],
        )

    def go_to_docker_tags(self):
        self.menu_click(
            menu_locators['menu.content'],
            menu_locators['menu.docker_tags'],
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

    def go_to_job_templates(self):
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.job_templates'],
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

    def go_to_smart_class_parameters(self):
        self.menu_click(
            menu_locators['menu.configure'],
            menu_locators['menu.smart_class_parameters'],
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

    def go_to_oscap_tailoringfile(self):
        """Navigates to Oscap Tailoring File"""
        self.menu_click(
            menu_locators['menu.hosts'],
            menu_locators['menu.oscap_tailoringfile'],
        )

    def go_to_select_org(self, org, force=True):
        """Selects the specified organization.

        :param str org: The organization to select.
        :param force: Force navigation to org even if org is already selected
        :return: Returns the organization.
        :rtype: str

        """

        # if force=False and org is already the current selected, do nothing.
        if not force and self.find_element(
                menu_locators['menu.current_text']).text == org:
            self.logger.debug(
                u'%s is already the org in the context', org)
            return

        self.logger.debug(u'Selecting Organization: %s', org)
        strategy, value = menu_locators['org.select_org']
        self.menu_click(
            menu_locators['menu.any_context'],
            menu_locators['org.nav_current_org'],
            (strategy, value % (org, org)),
        )
        self.perform_action_chain_move(menu_locators['menu.current_text'])
        org_dropdown = org
        if len(org) > 30:
            org_dropdown = org[:27] + '...'
        if self.wait_until_element(
                menu_locators['menu.fetch_org']).text != org_dropdown:
            raise UIError(u'Error Selecting Organization: %s' % org)
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
        self.logger.debug(u'Selecting Location: %s', loc)
        strategy, value = menu_locators['loc.select_loc']
        self.menu_click(
            menu_locators['menu.any_context'],
            menu_locators['loc.nav_current_loc'],
            (strategy, value % (loc, loc)),
        )
        self.perform_action_chain_move(menu_locators['menu.current_text'])
        loc_dropdown = loc
        if len(loc) > 30:
            loc_dropdown = loc[:27] + '...'
        if self.wait_until_element(
                menu_locators['menu.fetch_loc']).text != loc_dropdown:
            raise UIError(u'Error Selecting Location: %s' % loc)
        # close dropdown
        self.click(menu_locators['menu.current_text'])
        # get to left corner of the browser instance to not have impact on
        # further actions
        self.perform_action_chain_move_by_offset(-150, -150)
        return loc
