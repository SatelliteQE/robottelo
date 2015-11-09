# -*- encoding: utf-8 -*-
"""Implements different locators for UI"""

import collections
import logging

from selenium.webdriver.common.by import By


LOGGER = logging.getLogger(__name__)


class LocatorDict(collections.Mapping):
    """This class will log every time an item is selected

    The constructor accepts a dictionary or keyword arguments like the
    built-in ``dict``::

        >>> dict({'a': 'b'})
        {'a': 'b'}
        >>> dict(a='b')
        {'a': 'b'}

    """
    def __init__(self, *args, **kwargs):
        self.store = dict(*args, **kwargs)

    def __getitem__(self, key):
        item = self.store[key]
        LOGGER.debug(
            'Accessing locator "%s" by %s: "%s"', key, item[0], item[1]
        )
        return item

    def __len__(self):
        return len(self.store)

    def __iter__(self):
        return iter(self.store)


menu_locators = LocatorDict({
    # Menus

    # Monitor Menu
    "menu.monitor": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='monitor_menu']")),
    "menu.dashboard": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_dashboard']")),
    "menu.content_dashboard": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_content_dashboard']")),
    "menu.reports": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_reports']")),
    "menu.facts": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_fact_values']")),
    "menu.statistics": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_statistics']")),
    "menu.trends": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_trends']")),
    "menu.audits": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_audits']")),

    # Content Menu
    "menu.content": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='content_menu']")),
    "menu.life_cycle_environments": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_environments']")),
    "menu.red_hat_subscriptions": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_red_hat_subscriptions']")),
    "menu.subscription_manager_applications": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_subscription_manager_applications']")),
    "menu.activation_keys": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_activation_keys']")),
    "menu.red_hat_repositories": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_redhat_provider']")),
    "menu.products": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_products']")),
    "menu.gpg_keys": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_gpg_keys']")),
    "menu.sync_status": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_sync_status']")),
    "menu.sync_plans": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_sync_plans']")),
    "menu.content_views": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_content_views']")),
    "menu.sync_schedules": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "/a[@id='menu_item_sync_schedules']")),
    "menu.content_search": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_content_search']")),

    # Containers Menu
    "menu.containers": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='containers_menu']")),
    "menu.all_containers": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_containers']")),
    "menu.new_container": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_new_container']")),
    "menu.registries": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_registries']")),

    # Hosts Menu
    "menu.hosts": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='hosts_menu']")),
    "menu.all_hosts": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_hosts']")),
    "menu.discovered_hosts": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_discovered_hosts']")),
    "menu.content_hosts": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_content_hosts']")),
    "menu.host_collections": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_host_collections']")),
    "menu.operating_systems": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_operatingsystems']")),
    "menu.provisioning_templates": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_config_templates']")),
    "menu.partition_tables": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_ptables']")),
    "menu.installation_media": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_media']")),
    "menu.hardware_models": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_models']")),
    "menu.architectures": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_architectures']")),
    "menu.oscap_policy": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_compliance_policies']")),
    "menu.oscap_content": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_compliance_contents']")),
    "menu.oscap_reports": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_compliance_reports']")),

    # Configure Menu
    "menu.configure": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='configure_menu']")),
    "menu.host_groups": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_hostgroups']")),
    "menu.discovery_rules": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_discovery_rules']")),
    "menu.global_parameters": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_common_parameters']")),
    "menu.environments": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//li[contains(@class,'menu_tab_environments')]"
         "/a[@id='menu_item_environments']")),
    "menu.puppet_classes": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_puppetclasses']")),
    "menu.smart_variables": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_lookup_keys']")),
    "menu.configure_groups": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_config_groups']")),

    # Infrastructure Menu
    "menu.infrastructure": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='infrastructure_menu']")),
    "menu.smart_proxies": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_smart_proxies']")),
    "menu.compute_resources": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_compute_resources']")),
    "menu.compute_profiles": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_compute_profiles']")),
    "menu.subnets": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_subnets']")),
    "menu.domains": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_domains']")),

    # Access Insights menu
    "menu.insights": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='redhat_access_top_menu']")),
    "insights.overview": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/redhat_access/insights']")),
    "insights.rules": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/redhat_access/insights/rules/']")),
    "insights.systems": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/redhat_access/insights/systems/']")),
    "insights.manage": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/redhat_access/insights/manage']")),


    # Administer Menu
    "menu.administer": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='administer_menu']")),
    "menu.ldap_auth": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_auth_source_ldaps']")),
    "menu.users": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_users']")),
    "menu.user_groups": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_usergroups']")),
    "menu.roles": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_roles']")),
    "menu.bookmarks": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_bookmarks']")),
    "menu.settings": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_settings']")),
    "menu.about": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//a[@id='menu_item_about_index']")),

    # Account Menu
    "menu.account": (By.XPATH, "//a[@id='account_menu']"),
    "menu.sign_out": (By.XPATH, "//a[@id='menu_item_logout']"),
    "menu.my_account": (By.XPATH, "//a[@id='menu_item_my_account']"),

    # Common Locators for Orgs and Locations
    "menu.any_context": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//li[contains(@class,'org-switcher')]/a")),
    # Updated to current_text as the fetched text can also be org+loc
    "menu.current_text": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//li[contains(@class,'org-switcher')]/a")),
    "menu.fetch_org": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//li[contains(@class, 'org-menu')]/a")),
    "menu.fetch_loc": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
         "//li[contains(@class, 'loc-menu')]/a")),

    # Orgs
    "org.manage_org": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@class='manage-menu' and contains(@href, 'organizations')]")),
    "org.nav_current_org": (
        By.XPATH,
        ("(//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//li[contains(@class,'org-switcher')]"
         "//li/a[@data-toggle='dropdown'])[1]")),
    "org.select_org": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/organizations/clear']/../../li/a[contains(.,'%s')]")),

    # Locations
    "loc.manage_loc": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@class='manage-menu' and contains(@href, 'locations')]")),
    "loc.nav_current_loc": (
        By.XPATH,
        ("(//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//li[contains(@class,'org-switcher')]"
         "//li/a[@data-toggle='dropdown'])[2]")),
    "loc.select_loc": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/locations/clear']/../../li/a[contains(.,'%s')]"))
})

tab_locators = LocatorDict({

    # common
    "tab_primary": (By.XPATH, "//a[@href='#primary']"),
    # Third level UI
    "tab_loc": (By.XPATH, "//a[@href='#locations']"),
    "tab_org": (By.XPATH, "//a[@href='#organizations']"),

    # Operating System
    # Third level UI
    "operatingsys.tab_primary": (By.XPATH, "//a[@href='#primary']"),
    "operatingsys.tab_ptable": (By.XPATH, "//a[@href='#ptable']"),
    "operatingsys.tab_medium": (By.XPATH, "//a[@href='#media']"),
    "operatingsys.tab_templates": (By.XPATH, "//a[@href='#templates']"),
    "operatingsys.tab_parameters": (By.XPATH, "//a[@href='#params']"),

    # Host
    # Third level UI

    "host.tab_puppet": (By.XPATH, "//a[@href='#puppet_klasses']"),
    "host.tab_network": (By.XPATH, "//a[@href='#network']"),
    "host.tab_os": (By.XPATH, "//form[@id='new_host']//a[@href='#os']"),
    "host.tab_vm": (
        By.XPATH, "//form[@id='new_host']//a[@href='#compute_resource']"),
    "host.tab_params": (By.XPATH, "//a[@href='#params']"),
    "host.tab_info": (By.XPATH, "//a[@href='#info']"),

    # Provisioning Templates
    # Third level UI

    "provision.tab_type": (By.XPATH, "//a[@href='#template_type']"),
    "provision.tab_association": (By.XPATH,
                                  "//a[@href='#template_associations']"),
    "provision.tab_history": (By.XPATH, "//a[@href='#history']"),

    # Users
    # Third level UI

    "users.tab_primary": (By.XPATH, "//a[@href='#primary']"),
    "users.tab_roles": (By.XPATH, "//a[@href='#roles']"),
    "users.tab_locations": (By.XPATH, "//a[@href='#locations']"),
    "users.tab_organizations": (By.XPATH, "//a[@href='#organizations']"),
    "users.tab_filters": (By.XPATH, "//a[@href='#filters']"),

    "prd.tab_details": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'info')]"),
    "prd.tab_repos": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'repositories')]"),
    "prd.tab_tasks": (
        By.XPATH, ("//a[@class='ng-scope' and contains(@href,'tasks')"
                   " and contains(@ui-sref, 'products')]")),

    # For Orgs and Locations
    "context.tab_users": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'users')]"),
    "context.tab_sm_prx": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'smart_proxies')]"),
    "context.tab_subnets": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'subnets')]"),
    "context.tab_resources": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'resources')]"),
    "context.tab_media": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'media')]"),
    "context.tab_template": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'template')]"),
    "context.tab_domains": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'domains')]"),
    "context.tab_env": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'environments')]"),
    "context.tab_hostgrps": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'hostgroups')]"),
    "context.tab_locations": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'locations')]"),
    "context.tab_organizations": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'organizations')]"),
    "context.tab_parameters": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'params')]"),

    # Roles
    # Third level UI
    "roles.tab_filter": (
        By.XPATH, "//a[@href='#primary']"),
    "roles.tab_org": (
        By.XPATH, "//a[@href='#organizations']"),

    # GPG key
    # Third level UI
    "gpgkey.tab_details": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'info')]"),
    "gpgkey.tab_products": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'products')]"),
    "gpgkey.tab_repos": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'repositories')]"),

    # Content Views
    # Third level UI
    "contentviews.tab_details": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'info')]"),
    "contentviews.tab_versions": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@ui-sref, 'details.versions')]"),
    "contentviews.tab_content": (
        By.XPATH, "//ul/li/a[@class='dropdown-toggle']/i"),
    "contentviews.tab_content_views": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'content-views')]"),
    "contentviews.tab_puppet_modules": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'puppet_modules')]"),
    "contentviews.tab_docker_content": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'docker')]"),
    "contentviews.tab_history": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href, 'history')]"),
    "contentviews.tab_tasks": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href, 'tasks')]"),
    "contentviews.tab_repo_add": (
        By.XPATH,
        "//a[contains(@href, 'repositories') and "
        "contains(@ui-sref, 'available')]"),
    "contentviews.tab_repo_remove": (
        By.XPATH,
        ("//a[contains(@href, 'repositories') and contains(@ui-sref, 'list')]"
         "/span[@class='ng-scope' and contains(., 'List/Remove')]")),
    "contentviews.tab_cv_add": (
        By.XPATH,
        "//a[contains(@ui-sref, 'content-views.available')]"),
    "contentviews.tab_cv_remove": (
        By.XPATH, "//a[contains(@ui-sref, 'content-views.list')]"),
    "contentviews.tab_pkg_group_add": (
        By.XPATH, "//a[contains(@ui-sref, 'package_group.available')]"),
    "contentviews.tab_pkg_group_remove": (
        By.XPATH, "//a[contains(@ui-sref, 'package_group.list')]"),
    "contentviews.tab_add": (
        By.XPATH, "//a[contains(@ui-sref, 'available')]"),
    "contentviews.tab_remove": (
        By.XPATH, "//a[contains(@ui-sref, 'list')]"),

    # Sync Plans
    # Third level UI
    "sp.tab_details": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'info')]"),
    "sp.tab_products": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'products')]"),
    # Fourth level UI
    "sp.list_prd": (
        By.XPATH, "//a[contains(@ui-sref,'list')]/span[@class='ng-scope']"),
    "sp.add_prd": (
        By.XPATH, "//a[contains(@ui-sref,'add')]/span[@class='ng-scope']"),

    # Activation Keys
    # Third level UI
    "ak.details": (
        By.XPATH, "//a[contains(@href, 'info')]"),
    "ak.subscriptions": (
        By.XPATH, "//a[contains(@href, 'subscriptions')]/span"),
    "ak.subscriptions_add": (
        By.XPATH, "//a[contains(@ui-sref, 'subscriptions.add')]"),
    "ak.subscriptions_remove": (
        By.XPATH, "//a[contains(@ui-sref, 'subscriptions.list')]"),
    "ak.host_collections": (
        By.XPATH, "//a[contains(@href, 'host-collections')]"),
    "ak.host_collections.add": (
        By.XPATH, "//a[contains(@ui-sref, 'host-collections.add')]"),
    "ak.host_collections.add.select": (
        By.XPATH,
        "//tr/td/a[contains(., '%s')]"
        "/parent::*/parent::*"
        "/td/input[@ng-model='hostCollection.selected']"),
    "ak.host_collections.add.add_selected": (
        By.XPATH, "//button[@ng-click='addHostCollections()']"),
    "ak.host_collections.list": (
        By.XPATH, "//a[contains(@ui-sref, 'host-collections.list')]"),
    "ak.associations": (
        By.XPATH, "//ul/li[@class='dropdown']/a"),
    "ak.tab_prd_content": (
        By.XPATH, "//a[contains(@ui-sref, 'details.products')]/span/span"),

    # Manifest / subscriptions
    "subs.tab_details": (
        By.XPATH, "//a[contains(@ui-sref,'manifest.details')]"),
    "subs.import_history": (
        By.XPATH, "//a[contains(@ui-sref,'manifest.history')]"),

    # Subnet
    "subnet.tab_domain": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'domains')]"),

    # Settings
    "settings.tab_general": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'General')]"),
    "settings.tab_auth": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Auth')]"),
    "settings.tab_bootdisk": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Bootdisk')]"),
    "settings.tab_puppet": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Puppet')]"),
    "settings.tab_discovered": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Discovered')]"),
    "settings.tab_foremantasks": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href, 'ForemanTasks')]"),
    "settings.tab_provisioning": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href, 'Provisioning')]"),
    "puppetclass.parameters": (
        By.XPATH, "//a[contains(@href,'class_param')]"),

    # LDAP Authentication
    "ldapserver.tab_account": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'account')]"),
    "ldapserver.tab_attributes": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'attributes')]"),

    # UserGroups
    "usergroups.tab_roles": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'roles')]"),
    "usergroups.tab_external": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'external')]"),
})

common_locators = LocatorDict({

    # common locators

    # Notifications
    "notif.error": (
        By.XPATH, "//div[contains(@class, 'jnotify-notification-error')]"),
    "notif.warning": (
        By.XPATH, "//div[contains(@class, 'jnotify-notification-warning')]"),
    "notif.success": (
        By.XPATH, "//div[contains(@class, 'jnotify-notification-success')]"),
    "notif.close": (
        By.XPATH, "//a[@class='jnotify-close']"),

    "alert.success": (
        By.XPATH, "//div[contains(@class, 'alert-success')]"),
    "alert.error": (
        By.XPATH, "//div[contains(@class, 'alert-danger')]"),

    "selected_entity": (
        By.XPATH,
        ("//div[@class='ms-selection']/ul[@class='ms-list']"
         "/li[@class='ms-elem-selection ms-selected']")),
    "select_filtered_entity": (
        By.XPATH, "//a/span[contains(@data-original-title, '%s')]"),
    "checked_entity": (
        By.XPATH, "//input[@checked='checked']/parent::label"),
    "entity_select": (
        By.XPATH,
        "//div[@class='ms-selectable']//span[contains(.,'%s')]"),
    "entity_deselect": (
        By.XPATH,
        "//div[@class='ms-selection']//span[contains(.,'%s')]"),
    "entity_checkbox": (
        By.XPATH,
        "//label[normalize-space(.)='%s']/input[@type='checkbox']"),
    "name_haserror": (
        By.XPATH,
        ("//label[@for='name']/../../"
         "div[contains(@class,'has-error')]")),
    "haserror": (
        By.XPATH,
        "//div[contains(@class,'has-error')]"),
    "common_haserror": (
        By.XPATH,
        ("//span[@class='help-block']/ul/"
         "li[contains(@ng-repeat,'error.messages')]")),
    "common_invalid": (
        By.XPATH,
        "//input[@id='name' and contains(@class,'ng-invalid')]"),
    "common_param_error": (
        By.XPATH,
        "//div[@class='fields']/span[@class='help-block']"),

    "cv_filter": (
        By.XPATH, "//input[@ng-model='filterTerm']"),
    "search": (By.ID, "search"),
    "auto_search": (By.XPATH, "//ul[@id='ui-id-1']/li/a[contains(., '%s')]"),
    "search_button": (By.XPATH, "//button[contains(@type,'submit')]"),
    "submit": (By.NAME, "commit"),
    "filter": (By.XPATH,
               ("//div[@id='ms-%s_ids']"
                "//input[contains(@class,'ms-filter')]")),
    "parameter_tab": (By.XPATH, "//a[contains(., 'Parameters')]"),
    "add_parameter": (
        By.XPATH, "//a[contains(text(),'+ Add Parameter')]"),
    "parameter_name": (
        By.XPATH, "//input[@placeholder='Name' and not(@value)]"),
    "parameter_value": (
        By.XPATH, "//textarea[@placeholder='Value' and not(text())]"),
    "parameter_remove": (
        By.XPATH, "//tr/td/input[@value='%s']/following::td/span/a/i"),

    # Katello Common Locators
    "confirm_remove": (By.XPATH, "//button[contains(@ng-click,'ok')]"),
    "create": (By.XPATH, "//button[contains(@ng-click,'Save')]"),
    "save": (
        By.XPATH, ("//button[contains(@ng-click,'save')"
                   "and not(contains(@class,'ng-hide'))]")),
    "cancel": (By.XPATH, "//button[contains(@ng-click,'Cancel')]"),
    "name": (By.ID, "name"),
    "label": (By.ID, "label"),
    "description": (By.ID, "description"),
    "kt_search": (By.XPATH, "//input[@ng-model='table.searchTerm']"),
    "kt_search_button": (
        By.XPATH,
        "//button[@ng-click='table.search(table.searchTerm)']"),
    # Katello common Product and Repo locators
    "gpg_key": (By.ID, "gpg_key_id"),
    "all_values": (By.XPATH,
                   ("//div[contains(@class,'active')]//input[@type='checkbox'"
                    " and contains(@name, '%s')]")),
    "all_values_selection": (
        By.XPATH,
        ("//div[@class='ms-selection']//ul[@class='ms-list']/li"
         "/span[contains(.,'%s')]/.."))
})

locators = LocatorDict({

    # Locations
    "location.new": (By.XPATH, "//a[@data-id='aid_locations_new']"),
    "location.parent": (By.ID, "location_parent_id"),
    "location.name": (By.ID, "location_name"),
    "location.assign_all": (
        By.XPATH, "//a[contains(@data-id,'assign_all_hosts')]"),
    "location.proceed_to_edit": (
        By.XPATH,
        "//a[@class='btn btn-default' and contains(@href, '/edit')]"),
    "location.select_name": (
        By.XPATH,
        "//a[contains(@href,'locations')]/span[contains(.,'%s')]"),
    "location.delete": (
        By.XPATH,
        "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "location.dropdown": (
        By.XPATH,
        ("//a[normalize-space(.)='%s' and contains(@href,'locations')]"
         "/../../td/div/a[@data-toggle='dropdown']")),


    # Login
    "login.username": (By.ID, "login_login"),
    "login.password": (By.ID, "login_password"),
    "login.gravatar": (By.XPATH, "//img[contains(@class, 'avatar')]"),
    "login.loggedin": (
        By.XPATH,
        "//a[@id='account_menu' and contains(., '%s')]"),

    # Organizations
    "org.new": (
        By.XPATH,
        ("//a[contains(@href, '/organizations/new')]")),
    "org.name": (By.ID, "organization_name"),
    "org.parent": (By.ID, "organization_parent_id"),
    "org.label": (By.ID, "organization_label"),
    "org.desc": (By.ID, "organization_description"),
    "org.cert": (By.ID, "download_debug_cert_key"),
    "org.proceed_to_edit": (
        By.XPATH,
        "//a[@class='btn btn-default' and contains(@href, '/edit')]"),
    # By.XPATH works also with latin1 and html chars, so removed By.LINK_TEXT
    "org.org_name": (
        By.XPATH,
        "//a[contains(@href,'organizations')]/span[contains(.,'%s')]"),
    "org.dropdown": (
        By.XPATH,
        ("//a[normalize-space(.)='%s' and contains(@href,'organizations')]"
            "/../../td/div/a[@data-toggle='dropdown']")),
    "org.delete": (
        By.XPATH,
        "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "org.name_value": (
        By.XPATH,
        "//input[@id='organization_name' and @value='%s']"),
    "org.label_value": (
        By.XPATH,
        "//input[@id='organization_label' and @value='%s']"),

    # Trends
    "trend.new": (By.XPATH, "//a[contains(@href, '/trends/new')]"),
    "trend.type": (By.ID, "trend_trendable_type"),
    "trend.trendable": (By.ID, "trend_trendable_id"),
    "trend.name": (By.ID, "trend_name"),
    "trend.trend_name": (By.XPATH, "//a[text()='%s']"),
    "trend.edit": (
        By.XPATH,
        "//a[contains(@href,'%s') and contains(.,'Edit')]"),
    "trend.edit_entity": (By.XPATH, "//td[contains(., '%s')]/../td[2]/input"),
    "trend.dropdown": (
        By.XPATH,
        "//a[contains(@href,'%s') and contains(.,'Edit')]/../../a"),
    "trend.delete": (
        By.XPATH,
        "//a[contains(@href,'%s') and contains(.,'Delete')]"),

    # Operating system (OS)
    "operatingsys.new": (
        By.XPATH, "//a[contains(@href, '/operatingsystems/new')]"),
    "operatingsys.name": (By.ID, "operatingsystem_name"),
    "operatingsys.major_version": (By.ID, "operatingsystem_major"),
    "operatingsys.minor_version": (By.ID, "operatingsystem_minor"),
    "operatingsys.description": (By.ID, "operatingsystem_description"),
    "operatingsys.family": (By.ID, "operatingsystem_family"),
    "operatingsys.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "operatingsys.operatingsys_name": (By.XPATH, "//a[contains(., '%s')]"),
    "operatingsys.template": (
        By.ID,
        "operatingsystem_os_default_templates_attributes_0_config_template_id"
    ),

    # Compute Profile
    "profile.select_name": (
        By.XPATH,
        ("//a[contains(@href,'compute_profiles')"
            "and normalize-space(.)='%s']")),
    "profile.resource_name": (
        By.XPATH,
        ("//a[contains(@href,'compute_resources')"
            "and normalize-space(.)='%s']")),
    "profile.resource_form": (By.XPATH, "//form[@id='new_compute_attribute']"),

    # Compute Resource
    # Some locator values can be duplicated. That was performed more because of
    # bad application design rather than wrong test automation implementation.
    # Also, that will prevent unnecessary confusion in all these provider type
    # fields and much easier maintenance in case of any changes to DOM
    "resource.new": (
        By.XPATH, "//a[contains(@href, '/compute_resources/new')]"),
    "resource.name": (By.ID, "compute_resource_name"),
    "resource.provider_type": (
        By.XPATH, "//select[@id='compute_resource_provider']"),
    "resource.description": (By.ID, "compute_resource_description"),
    "resource.url": (By.XPATH, "//input[@id='compute_resource_url']"),
    "resource.display_type": (By.ID, "compute_resource_display_type"),
    "resource.console_passwords": (
        By.ID, "compute_resource_set_console_password"),
    "resource.test_connection": (
        By.XPATH,
        "//a[contains(@data-url, '/compute_resources/test_connection')]"),
    "resource.username": (By.ID, "compute_resource_user"),
    "resource.password": (By.ID, "compute_resource_password"),
    "resource.datacenter": (By.XPATH, "//select[@id='compute_resource_uuid']"),
    "resource.datacenter.button": (
        By.XPATH,
        "//a[contains(@data-url, '/compute_resources/test_connection')]"),
    "resource.quota_id": (
        By.XPATH, "//select[@id='compute_resource_ovirt_quota']"),
    "resource.x509_certification_authorities": (
        By.ID, "compute_resource_public_key"),
    "resource.access_key": (By.ID, "compute_resource_user"),
    "resource.secret_key": (By.ID, "compute_resource_password"),
    "resource.region": (By.ID, "compute_resource_region"),
    "resource.region.button": (
        By.XPATH,
        "//a[contains(@data-url, '/compute_resources/test_connection')]"),
    "resource.vcenterserver": (By.ID, "compute_resource_server"),
    "resource.tenant": (By.ID, "compute_resource_tenant"),
    "resource.tenant.button": (
        By.XPATH,
        "//a[contains(@data-url, '/compute_resources/test_connection')]"),
    "resource.api_key": (By.ID, "compute_resource_password"),
    "resource.google_project_id": (By.ID, "compute_resource_project"),
    "resource.client_email": (By.ID, "compute_resource_email"),
    "resource.certificate_path": (By.ID, "compute_resource_key_path"),
    "resource.zone": (By.XPATH, "//select[@id='compute_resource_zone']"),
    "resource.zone.button": (
        By.XPATH,
        "//a[contains(@data-url, '/compute_resources/test_connection')]"),
    "resource.email": (By.ID, "compute_resource_email"),
    "resource.select_name": (
        By.XPATH,
        ("//a[contains(@href,'compute_resources')"
            "and normalize-space(.)='%s']")),
    "resource.dropdown": (
        By.XPATH,
        ("//td/a[contains(., '%s')]"
         "/following::td/div/a[@data-toggle='dropdown']")),
    "resource.delete": (
        By.XPATH,
        ("//td/a[contains(., '%s')]"
         "/following::td/div/ul/li/a[@class='delete']")),
    "resource.edit": (
        By.XPATH, "//a[contains(@data-id,'edit') and contains(@href,'%s')]"),

    # Hosts

    # host.primary
    "host.new": (By.XPATH, "//a[contains(@href, '/hosts/new') and "
                           "contains(@class, 'btn')]"),
    "host.name": (By.ID, "host_name"),
    "host.clone": (
        By.XPATH, "//a[contains(@href,'%s') and contains(.,'Clone')]"),
    "host.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "host.group": (By.ID, "host_hostgroup_id"),
    "host.deploy": (By.ID, "host_compute_resource_id"),
    "host.environment": (By.ID, "host_environment_id"),
    "host.dropdown": (
        By.XPATH,
        ("//a[contains(@href,'%s')]"
         "/../../a[contains(@data-toggle,'dropdown')]")),
    "host.select_name": (
        By.XPATH,
        ("//input[contains(@id,'host_ids')]"
         "/../../td[@class='ellipsis']/a[contains(@href,'%s')]")),
    "host.lifecycle_env": (By.ID, "host_lifecycle_environment_id"),
    "host.cv": (By.ID, "host_content_view_id"),
    "host.reset_puppetenv": (By.ID, "reset_puppet_environment"),

    # host.network
    "host.mac": (By.ID, "host_mac"),
    "host.domain": (By.ID, "host_domain_id"),
    "host.subnet": (By.ID, "host_subnet_id"),
    "host.ip": (By.ID, "host_ip"),

    # host.os
    "host.arch": (By.ID, "host_architecture_id"),
    "host.os": (By.ID, "host_operatingsystem_id"),
    "host.org": (By.ID, "host_organization_id"),
    "host.loc": (By.ID, "host_location_id"),
    "host.edit": (By.XPATH,
                  "//a[@class='btn btn-default' and contains(@href,'edit')]"),
    "host.puppet_ca": (By.ID, "host_puppet_ca_proxy_id"),
    "host.puppet_master": (By.ID, "host_puppet_proxy_id"),
    "host.provision": (By.ID, "host_build"),
    "host.media": (By.ID, "host_medium_id"),
    "host.ptable": (By.ID, "host_ptable_id"),
    "host.custom_ptables": (By.ID, "host_disk"),
    "host.root_pass": (By.ID, "host_root_pass"),
    "host.provision_template": (
        By.XPATH,
        "//div[contains(.,'Provisioning Templates')]/../div/a[@class='btn']"),

    # host.vm (NOTE:- visible only when selecting a compute resource)
    "host.vm_cpus": (By.ID, "host_compute_attributes_cpus"),
    "host.vm_memory": (By.ID, "host_compute_attributes_memory"),
    "host.network_type": (
        By.ID, "host_compute_attributes_nics_attributes_0_type"),
    "host.network": (By.ID, "host_compute_attributes_nics_attributes_0_type"),
    "host.vm_start": (By.ID, "host_compute_attributes_start"),
    "host.vm_addstorage": (
        By.XPATH, "//fieldset[@id='storage_volumes']/a"),
    "host.vm_addnic": (
        By.XPATH, "//fieldset[@id='network_interfaces']/a"),

    # Host 'Select Action'/'Bulk Action.'
    "host.checkbox": (
        By.XPATH,
        "//span[contains(@data-original-title, '%s')]/../../../td/input"),
    "host.select_action": (
        By.XPATH,
        "//div[@id='submit_multiple']/a[contains(@class, 'dropdown-toggle')]"),
    "host.assign_org": (
        By.XPATH, "//a[contains(@href, 'select_multiple_organization')]"),
    "host.fix_mismatch": (By.ID, "organization_optimistic_import_yes"),
    "host.select_org": (By.ID, "organization_id"),
    "host.bulk_submit": (
        By.XPATH,
        ("//form[contains(@action, 'multiple')]/../../../"
         "div/button[contains(@class,'primary')]")),
    "host.select_puppetmodule":
        (By.XPATH, "//a[contains(.,'%s')]/i[contains(@class, 'glyphicon')]"),
    "host.select_puppetclass": (
        By.XPATH,
        ("//span[contains(.,'%s')]"
         "/a[not(contains(@data-original-title, '::'))]")),

    # Provisions

    # provision.primary
    "provision.template_new": (
        By.XPATH, "//a[contains(@href, '/config_templates/new')]"),
    "provision.template_select": (
        By.XPATH,
        ("//a[contains(@href, 'config_templates')"
            "and normalize-space(.)='%s']")),
    "provision.template_name": (
        By.ID, "config_template_name"),
    "provision.audit_comment": (
        By.ID, "config_template_audit_comment"),
    "provision.template_template": (
        By.XPATH, "//input[@id='config_template_template']"),
    "provision.template_delete": (
        By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "provision.template_dropdown": (
        By.XPATH,
        ("//td/a[normalize-space(.)='%s']"
         "/following::td/div/a[@data-toggle='dropdown']")),
    "provision.template_clone": (
        By.XPATH, "//a[contains(@href,'clone')]"),

    # provision.type
    "provision.template_type": (
        By.ID, "config_template_template_kind_id"),
    "provision.template_snippet": (
        By.ID, "config_template_snippet"),

    # provision.association
    "provision.select_os": (
        By.XPATH, "//li/span[contains(., '%s')]"),
    "provision.associate_os": (
        By.XPATH,
        ("//label[@class='operatingsystem'"
            "and contains(., '%s')]/input[@type='checkbox']")),

    # Hostgroups

    "hostgroups.new": (By.XPATH, "//a[contains(@href, '/hostgroups/new')]"),
    "hostgroups.name": (By.ID, "hostgroup_name"),
    "hostgroups.parent": (By.ID, "hostgroup_parent_id"),
    "hostgroups.environment": (By.ID, "hostgroup_environment_id"),
    "hostgroups.hostgroup": (By.XPATH, "//a[contains(.,'%s')]"),
    "hostgroups.dropdown": (
        By.XPATH,
        ("//td/a/span[contains(., '%s')]"
         "/following::td/div/a[@data-toggle='dropdown']")),
    "hostgroups.delete": (
        By.XPATH,
        ("//td/a/span[contains(., '%s')]"
         "/following::td/div/ul/li[2]/a[@class='delete']")),
    "hostgroups.content_source": (
        By.ID, "hostgroup_content_source_id"),
    "hostgroups.puppet_ca": (
        By.ID, "hostgroup_puppet_ca_proxy_id"),
    "hostgroups.puppet_master": (
        By.ID, "hostgroup_puppet_proxy_id"),

    # Users

    # Users.primary
    "users.new": (By.XPATH, "//a[contains(@href, '/users/new')]"),
    "users.username": (By.ID, "user_login"),
    "users.firstname": (By.ID, "user_firstname"),
    "users.lastname": (By.ID, "user_lastname"),
    "users.email": (By.ID, "user_mail"),
    "users.language": (By.ID, "user_locale"),
    "users.selected_lang": (
        By.XPATH, ("//select[@id='user_locale']"
                   "/option[@selected='selected']")),
    "users.authorized_by": (By.ID, "user_auth_source_id"),
    "users.password": (By.ID, "user_password"),
    "users.password_confirmation": (By.ID, "user_password_confirmation"),
    "users.user": (By.XPATH, "//a[contains(., '%s')]"),
    "users.default_org": (By.ID, "user_default_organization_id"),
    "users.default_loc": (By.ID, "user_default_location_id"),
    "users.delete": (
        By.XPATH,
        ("//td/a[contains(., '%s')]"
         "/following::td/a[@class='delete']")),

    # users.roles
    "users.admin_role": (By.ID, "user_admin"),

    # User Groups
    "usergroups.new": (By.XPATH, "//a[contains(@href, '/usergroups/new')]"),
    "usergroups.name": (By.ID, "usergroup_name"),
    "usergroups.usergroup": (By.XPATH, "//a[contains(., '%s')]"),
    "usergroups.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "usergroups.admin": (
        By.ID, "usergroup_admin"),
    "usergroups.addexternal_usergrp": (
        By.XPATH, "//a[@data-association='external_usergroups']"),
    "usergroups.ext_usergroup_name": (
        By.XPATH,
        ("//input[not(contains(@id, 'new_external_usergroups')) and "
         "contains(@name, 'name') and contains(@id, "
         "'external_usergroups_attributes_new')]")),
    "usergroups.ext_authsource_id": (
        By.XPATH,
        ("//select[not(contains(@id, 'new_external_usergroups')) and "
         "contains(@name, 'auth_source_id') and contains(@id, "
         "'external_usergroups_attributes_new')]")),

    # Roles
    "roles.new": (By.XPATH, "//a[contains(@href, '/roles/new')]"),
    "roles.name": (By.ID, "role_name"),
    "roles.dropdown": (
        By.XPATH,
        ("//td/span/a[normalize-space(.)='%s']"
         "/following::td/div/a[@data-toggle='dropdown']")),
    "roles.delete": (By.XPATH,
                     "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "roles.add_permission": (
        By.XPATH, "//a[@data-id='aid_filters_new']"),
    "roles.select_resource_type": (
        By.ID, "filter_resource_type"),
    "roles.role": (By.XPATH, "//a[contains(., '%s')]"),
    "roles.perm_filter": (By.XPATH,
                          "//input[@placeholder='Filter permissions']"),
    "roles.perm_type": (By.XPATH, "//label[contains(., '%s')]"),
    "roles.permission": (By.XPATH, "//input[@value='%s']"),

    # Architecture
    "arch.new": (By.XPATH, "//a[contains(@href, '/architectures/new')]"),
    "arch.name": (By.ID, "architecture_name"),
    "arch.delete": (
        By.XPATH,
        "//a[contains(@data-confirm, '%s') and @class='delete']"),
    "arch.arch_name": (By.XPATH, "//a[contains(., '%s')]"),

    # Medium
    "medium.new": (By.XPATH, "//a[contains(@href, '/media/new')]"),
    "medium.name": (By.ID, "medium_name"),
    "medium.path": (By.ID, "medium_path"),
    "medium.os_family": (By.ID, "medium_os_family"),
    "medium.delete": (By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "medium.medium_name": (By.XPATH, "//a[contains(., '%s')]"),

    # Domain
    "domain.new": (By.XPATH, "//a[contains(@href, '/domains/new')]"),
    "domain.name": (By.ID, "domain_name"),
    "domain.description": (By.ID, "domain_fullname"),
    "domain.dns_proxy": (By.ID, "domain_dns_id"),
    "domain.delete": (By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "domain.domain_description": (By.XPATH, "//a[contains(., '%s')]"),

    # Environment
    "env.new": (By.XPATH, "//a[contains(@href, '/environments/new')]"),
    "env.name": (By.ID, "environment_name"),
    "env.delete": (
        By.XPATH,
        "//a[contains(@href,'%s') and contains(.,'Delete')]"),
    "env.env_name": (By.XPATH, "//a[normalize-space(.)='%s']"),
    "env.dropdown": (
        By.XPATH,
        "//a[contains(@href,'%s') and contains(.,'Classes')]/../../a"),

    # Partition Table
    "ptable.new": (By.XPATH, "//a[contains(@href, '/ptables/new')]"),
    "ptable.name": (By.ID, "ptable_name"),
    "ptable.layout": (By.ID, "ptable_layout"),
    "ptable.os_family": (By.ID, "ptable_os_family"),
    "ptable.delete": (By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "ptable.ptable_name": (By.XPATH, "//a[normalize-space(.)='%s']"),

    # Subnet Page
    "subnet.new": (By.XPATH, "//a[@class='btn btn-success']"),
    "subnet.name": (By.ID, "subnet_name"),
    "subnet.network": (By.ID, "subnet_network"),
    "subnet.mask": (By.ID, "subnet_mask"),
    "subnet.gateway": (By.ID, "subnet_gateway"),
    "subnet.primarydns": (By.ID, "subnet_dns_primary"),
    "subnet.secondarydns": (By.ID, "subnet_dns_secondary"),
    "subnet.display_name": (By.XPATH, "//a[contains(., '%s')]"),
    "subnet.delete": (
        By.XPATH,
        "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "subnet.proxies_tab": (By.XPATH, "//a[@href='#proxies']"),
    "subnet.network_haserror": (
        By.XPATH,
        ("//label[@for='network']/../../"
         "div[contains(@class,'has-error')]")),
    "subnet.mask_haserror": (
        By.XPATH,
        ("//label[@for='mask']/../../"
         "div[contains(@class,'has-error')]")),
    "subnet.gateway_haserror": (
        By.XPATH,
        ("//label[@for='gateway']/../../"
         "div[contains(@class,'has-error')]")),
    "subnet.dnsprimary_haserror": (
        By.XPATH,
        ("//label[@for='dns_primary']/../../"
         "div[contains(@class,'has-error')]")),
    "subnet.dnssecondary_haserror": (
        By.XPATH,
        ("//label[@for='dns_secondary']/../../"
         "div[contains(@class,'has-error')]")),

    # Products
    "prd.new": (By.XPATH, "//button[contains(@ui-sref,'products.new')]"),
    "prd.bulk_actions": (
        By.XPATH, "//button[contains(@ui-sref,'products.bulk-actions')]"),
    "prd.repo_discovery": (
        By.XPATH, "//button[contains(@ui-sref,'products.discovery')]"),
    "prd.new_provider": (
        By.XPATH, ("//a[@class='ng-scope' and "
                   "@ui-sref='products.new.provider']")),
    "prd.provider": (By.ID, "provider_id"),
    "prd.sync_plan": (By.ID, "sync_plan_id"),
    "prd.new_sync_plan": (
        By.XPATH, "//a[@ui-sref='products.new.sync-plan']"),
    "prd.close": (
        By.XPATH, "//button[@ui-sref='products.index']"),
    "prd.remove": (
        By.XPATH,
        "//button[contains(@ng-hide,'product.readonly')]"),
    "prd.select_checkbox": (
        By.XPATH, ("//a[@class='ng-binding' and contains(.,'%s')]"
                   "/../../td/input[contains(@ng-model,'product')]")),
    "prd.select": (
        By.XPATH, "//a[@class='ng-binding' and contains(.,'%s')]"),
    "prd.sync_interval": (By.ID, "interval"),
    "prd.sync_startdate": (By.ID, "startDate"),
    "prd.sync_hrs": (By.XPATH, "//input[@ng-model='hours']"),
    "prd.sync_mins": (By.XPATH, "//input[@ng-model='minutes']"),
    "prd.gpg_key_edit": (
        By.XPATH, "//form[@selector='product.gpg_key_id']//i"),
    "prd.gpg_key_update": (By.XPATH, ("//form[@selector='product.gpg_key_id']"
                                      "/div/select")),
    "prd.gpg_key": (By.XPATH, ("//form[@selector='product.gpg_key_id']"
                               "//div/span")),
    "prd.name_edit": (By.XPATH, ("//form[@bst-edit-text='product.name']"
                                 "//i[contains(@class,'fa-edit')]")),
    "prd.name_update": (By.XPATH, ("//form[@bst-edit-text='product.name']"
                                   "/div/input")),
    "prd.desc_edit": (
        By.XPATH, ("//form[@bst-edit-textarea='product.description']"
                   "//i[contains(@class,'icon-edit')]")),
    "prd.desc_update": (
        By.XPATH, ("//form[@bst-edit-textarea='product.description']"
                   "/div/textarea")),
    "prd.sync_plan_edit": (
        By.XPATH, ("//form[@selector='product.sync_plan_id']"
                   "//i[contains(@class,'icon-edit')]")),
    "prd.sync_plan_update": (
        By.XPATH, ("//form[@selector='product.sync_plan_id']"
                   "/div/select")),
    # Puppet Classes
    "puppetclass.new": (
        By.XPATH, "//a[@data-id='aid_puppetclasses_new']"),
    "puppetclass.name": (
        By.ID, "puppetclass_name"),
    "puppetclass.environments": (
        By.ID, "puppetclass_environments"),
    "puppetclass.select_name": (
        By.XPATH, ("//a[contains(@href, 'puppetclasses')"
                   " and contains(.,'%s')]")),
    "puppetclass.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "puppetclass.import": (
        By.XPATH, "//a[contains(@href,'import')]"),
    "puppetclass.environment_default_check": (
        By.XPATH, "//input[contains(@id,'KT_Default_Organization_Library')]"),
    "puppetclass.update": (
        By.XPATH, "//input[@value='Update']"),
    "puppetclass.paramfilter": (
        By.XPATH, "//input[contains(@placeholder,'Filter')]"),
    "puppetclass.param_description": (
        By.XPATH, "//textarea[contains(@id,'description')]"),
    "puppetclass.cancel": (
        By.XPATH, "//a[@class='btn btn-default']"),
    # Repository
    "repo.new": (By.XPATH, "//button[contains(@ui-sref,'repositories.new')]"),
    "repo.type": (By.ID, "content_type"),
    "repo.url": (By.ID, "url"),
    "repo.upstream_name": (By.ID, "docker_upstream_name"),
    "repo.checksum": (By.ID, "checksum_type"),
    "repo.via_http": (By.ID, "unprotected"),
    "repo.search": (By.XPATH, "//input[@ng-model='repositorySearch']"),
    "repo.remove": (
        By.XPATH, "//button[contains(@ng-show, 'canRemove')]"),
    "repo.sync_now": (
        By.XPATH, "//button[contains(@ng-click, 'syncSelectedRepositories')]"),
    "repo.select_checkbox": (
        By.XPATH, ("//a[@class='ng-binding' and contains(.,'%s')]"
                   "/../../td/input[contains(@ng-model,'repository')]")),
    "repo.select": (
        By.XPATH, "//a[@class='ng-binding' and contains(.,'%s')]"),
    "repo.select_event": (
        By.XPATH, "//a[contains(., 'Synchronize') and contains(., '%s')]"),
    "repo.result_event": (
        By.XPATH, ("//span[@class='ng-scope' and contains(., 'Result')]"
                   "/../../span[contains(@class, 'info-value')]")),
    "repo.repo_discover": (
        By.XPATH, "//button[@ui-sref='products.discovery.scan']"),
    "repo.discover_url": (By.XPATH, "//input[@type='url']"),
    "repo.discover_button": (By.XPATH, "//button[@type='submit']"),
    "repo.discovered_url_checkbox": (
        By.XPATH, ("//table[@bst-table='discoveryTable']"
                   "//td[contains(., '%s')]"
                   "/../td/input[@type='checkbox']")),
    "repo.cancel_discover": (
        By.XPATH, "//button[@ng-show='discovery.pending']"),
    "repo.create_selected": (
        By.XPATH, "//button[@ng-click='setupSelected()']"),
    "repo.create": (By.XPATH, "//button[@ng-click='createRepos()']"),
    "repo.existing_product": (
        By.XPATH, "//input[@type='radio' and @value='false']"),
    "repo.select_exist_product": (
        By.XPATH, "//select[@ng-model='createRepoChoices.existingProductId']"),
    "repo.new_product": (
        By.XPATH, "//input[@type='radio' and @value='true']"),
    "repo.new_product_name": (
        By.XPATH, "//input[@ng-model='createRepoChoices.product.name']"),
    "repo.gpgkey_in_discover": (
        By.XPATH,
        "//select[@ng-model='createRepoChoices.product.gpg_key_id']"),
    "repo.new_discover_name": (
        By.XPATH, "//input[@ng-model='repo.name']"),
    "repo.name_edit": (
        By.XPATH, ("//form[@bst-edit-text='repository.name']"
                   "//i[contains(@class,'fa-edit')]")),
    "repo.name_update": (
        By.XPATH, "//form[@bst-edit-text='repository.name']/div/input"),
    "repo.url_edit": (
        By.XPATH, ("//form[@bst-edit-text='repository.url']"
                   "//i[contains(@class,'fa-edit')]")),
    "repo.url_update": (
        By.XPATH, "//form[@bst-edit-text='repository.url']/div/input"),
    "repo.via_http_edit": (
        By.XPATH, ("//form[@bst-edit-checkbox='repository.unprotected']"
                   "//i[contains(@class,'fa-edit')]")),
    "repo.via_http_toggle": (
        By.XPATH, ("//form[@bst-edit-checkbox='repository.unprotected']"
                   "/div/input")),
    "repo.gpg_key_edit": (
        By.XPATH, "//form[@selector='repository.gpg_key_id']//i"),
    "repo.gpg_key_update": (
        By.XPATH, "//form[@selector='repository.gpg_key_id']/div/select"),
    "repo.gpg_key": (
        By.XPATH, ("//form[@selector='repository.gpg_key_id']"
                   "//div/span")),
    "repo.checksum_edit": (
        By.XPATH, ("//form[@selector='repository.checksum_type']"
                   "/div/div/span/i[contains(@class,'fa-edit')]")),
    "repo.checksum_update": (
        By.XPATH, "//form[@selector='repository.checksum_type']/div/select"),
    "repo.upstream_edit": (
        By.XPATH, ("//form[@bst-edit-text='repository.docker_upstream_name']"
                   "//i[contains(@class,'fa-edit')]")),
    "repo.upstream_update": (
        By.XPATH, ("//form[@bst-edit-text='repository.docker_upstream_name']"
                   "/div/input")),
    "repo.fetch_url": (
        By.XPATH, ("//form[@bst-edit-text='repository.url']"
                   "/div[@class='bst-edit']"
                   "/div/span[contains(@class,'editable-value')]")),
    "repo.fetch_gpgkey": (
        By.XPATH, ("//form[@selector='repository.gpg_key_id']"
                   "/div[@class='bst-edit']/div/span[2]")),
    "repo.fetch_checksum": (
        By.XPATH, ("//form[@selector='repository.checksum_type']"
                   "/div/div/span[contains(@class,'value')]")),
    "repo.fetch_upstream": (
        By.XPATH, ("//form[@bst-edit-text='repository.docker_upstream_name']"
                   "/div[@class='bst-edit']/div/span[2]")),
    "repo.result_spinner": (
        By.XPATH,
        "//i[@ng-show='task.pending' and contains(@class, 'icon-spinner')]"),
    # Activation Keys

    "ak.new": (By.XPATH, "//button[@ui-sref='activation-keys.new']"),
    "ak.env": (
        By.XPATH,
        "//input[@ng-model='item.selected']/parent::label[contains(., '%s')]"),
    "ak.selected_env": (
        By.XPATH,
        ("//input[@ng-model='item.selected']"
         "/parent::label[contains(@class, 'active')]")),
    "ak.content_view": (By.ID, "content_view_id"),
    "ak.usage_limit_checkbox": (
        By.XPATH,
        "//input[@ng-model='activationKey.unlimited_content_hosts']"),
    "ak.usage_limit": (
        By.XPATH, "//input[@ng-model='activationKey.max_content_hosts']"),
    "ak.invalid_limit": (
        By.XPATH,
        "//input[@id='max_content_hosts' and contains(@class, 'ng-invalid')]"),
    "ak.close": (
        By.XPATH,
        "//button[@ui-sref='activation-keys.index']"),
    "ak.ak_name": (
        By.XPATH,
        "//tr/td/a[contains(., '%s')]"),
    "ak.select_ak_name": (
        By.XPATH,
        "//input[@ng-model='activationKey.selected']"),
    "ak.edit_name": (
        By.XPATH, "//form[@bst-edit-text='activationKey.name']//div/span/i"),
    "ak.edit_name_text": (
        By.XPATH,
        "//form[@bst-edit-text='activationKey.name']/div/input"),
    "ak.save_name": (
        By.XPATH,
        ("//form[@bst-edit-text='activationKey.name']"
         "//button[@ng-click='save()']")),
    "ak.edit_description": (
        By.XPATH,
        "//form[@bst-edit-textarea='activationKey.description']//div/span/i"),
    "ak.edit_description_text": (
        By.XPATH,
        ("//form[@bst-edit-textarea='activationKey.description']"
         "/div/textarea")),
    "ak.save_description": (
        By.XPATH,
        ("//form[@bst-edit-textarea='activationKey.description']"
         "//button[@ng-click='save()']")),
    "ak.edit_limit": (
        By.XPATH,
        ("//div[@bst-edit-custom='activationKey.max_content_hosts']"
         "//div/span/i")),
    "ak.save_limit": (
        By.XPATH,
        ("//div[@bst-edit-custom='activationKey.max_content_hosts']"
         "//button[@ng-click='save()']")),
    "ak.edit_content_view": (
        By.XPATH,
        ("//form[@bst-edit-select='activationKey.content_view.name']"
         "//div//span/i")),
    "ak.edit_content_view_select": (
        By.XPATH,
        ("//form[@bst-edit-select='activationKey.content_view.name']"
         "/div/select")),
    "ak.remove": (
        By.XPATH, "//button[@ng-click='openModal()']"),
    "ak.copy": (
        By.XPATH, "//button[@ng-click='showCopy = true']"),
    "ak.copy_name": (
        By.XPATH, "//input[@ng-model='copyName']"),
    "ak.copy_create": (
        By.XPATH, "//button[@ng-click='copy(copyName)']"),
    "ak.cancel": (
        By.XPATH, ("//div[@class='modal-dialog']"
                   "//button[@ng-click='cancel()']")),
    "ak.save_cv": (
        By.XPATH,
        ("//form[@bst-edit-select='activationKey.content_view.name']"
         "//button[@ng-click='save()']")),
    "ak.select_subscription": (
        By.XPATH,
        ("//tr/td/a[contains(., '%s')]"
         "/following::tr[@row-select='subscription']"
         "/td/input[@ng-model='subscription.selected']")),
    "ak.add_selected_subscription": (
        By.XPATH, "//button[@ng-click='addSelected()']"),
    "ak.get_subscription_name": (
        By.XPATH,
        "//tr[@ng-repeat-start='(name, subscriptions) in "
        "groupedSubscriptions']/td/a[contains(., '%s')]"),
    "ak.selected_cv": (
        By.XPATH,
        ("//form[@bst-edit-select='activationKey.content_view.name']"
         "//div[@class='bst-edit']/div/span[2]")),
    "ak.content_hosts": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'content-hosts')]"),
    "ak.content_host_name": (
        By.XPATH,
        "//tr[@ng-repeat='contentHost in contentHosts']/td/a"),
    "ak.prd_content.edit_repo": (
        By.XPATH,
        ("//u[contains(.,'%s')]/../..//i[contains(@class,'fa-edit')]")),
    "ak.prd_content.select_repo": (
        By.XPATH,
        "//u[contains(.,'%s')]/../../div/form/div/select"),
    "ak.subscriptions.search": (
        By.XPATH,
        "//input[@ng-model='subscriptionsTable.searchTerm']"),
    "ak.subscriptions.search_button": (
        By.XPATH,
        "//button[@ng-click='subscriptionsTable."
        "search(subscriptionsTable.searchTerm)']"),

    # Sync Status
    "sync.prd_expander": (
        By.XPATH, "//span[@class='expander']/../../td[contains(.,'%s')]"),
    "sync.repo_checkbox": (
        By.XPATH, ("//label[@class='fl' and contains(.,'%s')]/../"
                   "input[@type='checkbox']")),
    "sync.sync_now": (
        By.ID, "sync_button"),
    "sync.fetch_result": (
        By.XPATH, "//label[contains(.,'%s')]/../../td[@class='result']/span"),
    "sync.cancel": (
        By.XPATH, ("//label[contains(.,'%s')]/../../td[@class='result']"
                   "/span/a[@class='cancel_sync']")),
    "sync.verarch_expander": (
        By.XPATH, ("//tr[contains(@class,'collapsed')]/td[contains(.,'%s')]"
                   "/span[@class='expander']")),

    # Sync Plans
    "sp.new": (By.XPATH, "//button[@ui-sref='sync-plans.new']"),
    "sp.select": (
        By.XPATH,
        "//a[contains(@href,'info') and contains(.,'%s')]"),
    "sp.prd_select": (
        By.XPATH,
        ("//a[contains(@ui-sref,'info') and contains(.,'%s')]"
         "/../../td/input[contains(@ng-model,'product')]")),
    "sp.interval": (By.ID, "interval"),
    "sp.start_date": (By.ID, "startDate"),
    "sp.start_hour": (By.XPATH, "//input[@ng-model='hours']"),
    "sp.start_minutes": (By.XPATH, "//input[@ng-model='minutes']"),
    "sp.remove": (By.XPATH, "//button[contains(@ng-click,'openModal')]"),
    "sp.name_edit": (
        By.XPATH,
        ("//form[@bst-edit-text='syncPlan.name']"
         "//i[contains(@class,'fa-edit')]")),
    "sp.name_update": (
        By.XPATH,
        ("//form[@bst-edit-text='syncPlan.name']"
         "/div/input")),
    "sp.desc_edit": (
        By.XPATH,
        ("//form[@bst-edit-textarea='syncPlan.description']"
         "//i[contains(@class,'fa-edit')]")),
    "sp.desc_update": (
        By.XPATH,
        ("//form[@bst-edit-textarea='syncPlan.description']"
         "/div/input")),
    "sp.sync_interval_edit": (
        By.XPATH,
        ("//form[@bst-edit-select='syncPlan.interval']"
         "//i[contains(@class,'fa-edit')]")),
    "sp.sync_interval_update": (
        By.XPATH,
        ("//form[@bst-edit-select='syncPlan.interval']"
         "/div/select")),
    "sp.add_selected": (
        By.XPATH, "//button[contains(@ng-click, 'addProducts')]"),
    "sp.remove_selected": (
        By.XPATH, "//button[contains(@ng-click, 'removeProducts')]"),
    "sp.fetch_interval": (
        By.XPATH,
        ("//form[@bst-edit-select='syncPlan.interval']"
         "/div[@class='bst-edit']/div/"
         "span[contains(@class,'editable-value')]")),
    "sp.fetch_startdate": (
        By.XPATH,
        ("//span[contains(.,'Start Date')]/../"
         "div/form/div[2]/div/span[contains(@class,'editable')]")),

    # Enable RH Repos expander
    "rh.prd_expander": (
        By.XPATH, ("//div[@id='ui-tabs-1']//td[contains(.,'%s')]"
                   "/span[@class='expander']")),
    "rh.reposet_expander": (
        By.XPATH, ("//span[@class='expander_area' and contains(.,'%s')]"
                   "/span")),
    "rh.reposet_checkbox": (
        By.XPATH, ("//span[@class='expander_area' and contains(.,'%s')]"
                   "/../../td/input[@class='repo_set_enable']")),
    "rh.repo_checkbox": (
        By.XPATH, ("//table[@class='repo_table']//td[contains(.,'%s')]"
                   "/../td/label/input[@class='repo_enable']")),
    "rh.reposet_spinner": (
        By.XPATH, ("//span[@class='expander_area' and contains(.,'%s')]"
                   "/../../td/img[@alt='Spinner']")),
    "rh.repo_spinner": (
        By.XPATH, ("//table[@class='repo_table']//td[contains(.,'%s')]"
                   "/../td/label/img[@alt='Spinner']")),

    # Lifecycle Envionments
    "content_env.new": (
        By.XPATH, "//a[contains(@ui-sref, 'environments.new')]"),
    "content_env.create_initial": (
        By.XPATH, "//label[@ng-click='initiateCreateEnvironment()']"),
    "content_env.select_name": (
        By.XPATH, ("//a[contains(@ui-sref, 'environment.details')"
                   " and contains(.,'%s')]")),
    "content_env.remove": (
        By.XPATH,
        "//button[contains(@ng-click,'remove')]"),
    "content_env.env_link": (
        By.XPATH,
        ("//a[contains(@ui-sref, 'environment.details') and contains(.,'%s')]"
         "/../../../../../div/div/a[contains(@href, 'new')]")),
    "content_env.edit_name": (
        By.XPATH,
        ("//form[@bst-edit-text='environment.name']"
         "//i[contains(@class,'fa-edit')]")),
    "content_env.edit_name_text": (
        By.XPATH,
        "//form[@bst-edit-text='environment.name']/div/input"),
    "content_env.edit_name_text.save": (
        By.XPATH,
        "//form[@bst-edit-text='environment.name']//button"),
    "content_env.edit_description": (
        By.XPATH,
        ("//form[@bst-edit-textarea='environment.description']"
         "//i[contains(@class,'fa-edit')]")),
    "content_env.edit_description_textarea": (
        By.XPATH,
        ("//form[@bst-edit-textarea='environment.description']"
         "/div/textarea")),
    "content_env.edit_description_textarea.save": (
        By.XPATH,
        "//form[@bst-edit-textarea='environment.description']//button"),

    # GPG Key
    "gpgkey.new": (By.XPATH, "//button[@ui-sref='gpgKeys.new']"),
    "gpgkey.upload": (By.XPATH, "//input[@type='radio'and @value='upload']"),
    "gpgkey.content": (
        By.XPATH, "//textarea[@placeholder='Paste contents...']"),
    "gpgkey.file_path": (
        By.XPATH, "//input[@type='file']"),
    "gpgkey.key_name": (
        By.XPATH,
        "//tr[@ng-repeat='gpgKey in table.rows']/td/a[contains(., '%s')]"),
    "gpgkey.remove": (
        By.XPATH, "//button[@ng-click='openModal()']"),
    "gpgkey.edit_name": (
        By.XPATH, "//form[@bst-edit-text='gpgKey.name']//div/span/i"),
    "gpgkey.new_form": (By.XPATH, "//form[contains(@name,'gpgKeyForm')]"),
    "gpgkey.edit_name_text": (
        By.XPATH,
        "//form[@bst-edit-text='gpgKey.name']/div/input"),
    "gpgkey.save_name": (
        By.XPATH,
        ("//form[@bst-edit-text='gpgKey.name']"
         "//button[@ng-click='save()']")),
    "gpgkey.upload_button": (
        By.XPATH, "//button[@ng-click='progress.uploading = true']"),
    "gpgkey.product_repo_search": (
        By.XPATH,
        ("//input[@placeholder='Filter' and contains(@ng-model, 'Search']")),
    "gpgkey.product_repo": (
        By.XPATH, "//td/a[contains(@href, 'repositories')]"),

    # Content views
    "contentviews.new": (By.XPATH, "//a[@ui-sref='content-views.new']"),
    "contentviews.composite": (By.ID, "composite"),
    "contentviews.key_name": (
        By.XPATH,
        "//tr[contains(@ng-repeat, 'contentView')]"
        "/td/a[contains(., '%s')]"),
    "contentviews.edit_name": (
        By.XPATH, "//form[@bst-edit-text='contentView.name']//div/span/i"),
    "contentviews.edit_name_text": (
        By.XPATH,
        "//form[@bst-edit-text='contentView.name']/div/input"),
    "contentviews.save_name": (
        By.XPATH,
        ("//form[@bst-edit-text='contentView.name']"
         "//button[@ng-click='save()']")),
    "contentviews.edit_description": (
        By.XPATH,
        "//form[@bst-edit-textarea='contentView.description']//div/span/i"),
    "contentviews.edit_description_text": (
        By.XPATH,
        ("//form[@bst-edit-textarea='contentView.description']"
         "/div/textarea")),
    "contentviews.save_description": (
        By.XPATH,
        ("//form[@bst-edit-textarea='contentView.description']"
         "//button[@ng-click='save()']")),
    "contentviews.has_error": (
        By.XPATH, "//div[contains(@class, 'has-error') and "
                  "contains(@class, 'form-group')]"),
    "contentviews.remove": (
        By.XPATH, "//button[@ui-sref='content-views.details.deletion']"),
    "contentviews.remove_ver": (
        By.XPATH, ("//td/a[contains(., '%s')]/following::td/"
                   "button[contains(@ui-sref, 'version-deletion')]")),
    "contentviews.remove_cv": (
        By.XPATH, "//button[@ng-click='removeContentViews()']"),
    "contentviews.remove_cv_version": (
        By.XPATH, "//a[contains(@ui-sref, 'version-deletion')]/button"),
    "contentviews.completely_remove_checkbox": (
        By.XPATH, "//span/input[contains(@ng-model, 'deleteArchive')]"),
    "contentviews.next_button": (
        By.XPATH, "//button[@ng-click='processSelection()']"),
    "contentviews.affected_button": (
        By.XPATH, "//button[contains(@ng-show, '!show')]"),
    "contentviews.change_env": (
        By.XPATH,
        "//input[@ng-model='item.selected']/parent::label[contains(., '%s')]"),
    "contentviews.change_cv": (
        By.XPATH, "//select[@ng-model='selectedContentViewId']"),
    "contentviews.confirm_remove_ver": (
        By.XPATH, "//button[@ng-click='performDeletion()']"),
    "contentviews.confirm_remove": (
        By.XPATH, "//button[@ng-click='delete()']"),
    "contentviews.version_name": (
        By.XPATH, "//td/a[contains(., '%s')]"),
    "contentviews.success_rm_alert": (
        By.XPATH,
        ("//div[contains(@class, 'alert-success')]"
         "/div/span[contains(., 'Successfully removed')]")),
    "contentviews.publish": (
        By.XPATH, "//a[contains(@href, 'publish')]/span"),
    "contentviews.publish_comment": (By.ID, "comment"),
    "contentviews.publish_progress": (
        By.XPATH,
        ("//tr/td[contains(., '%s')]"
         "/following::td/a/div[@class='progress progress-striped active']")),
    "contentviews.ver_label": (
        By.XPATH, "//div[@label='Version']/label"),
    "contentviews.ver_num": (
        By.XPATH, "//div[@class='col-sm-5 input']/span/span"),
    "contentviews.content_repo": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'repositories')]"),
    "contentviews.repo_name": (
        By.XPATH,
        "//a[@class='ng-binding' and contains(@ui-sref,'repositories.info')]"),
    "contentviews.select_repo": (
        By.XPATH,
        ("//div[@bst-table='repositoriesTable']"
         "//td[contains(normalize-space(.), '%s')]"
         "/preceding-sibling::td[@class='row-select']"
         "/input[@type='checkbox']")),
    "contentviews.add_repo": (
        By.XPATH,
        "//button[contains(@ng-show, 'available') and "
        "contains(@ng-click, 'addRepositories')]"),
    "contentviews.remove_repo": (
        By.XPATH,
        "//button[contains(@ng-show, 'list') and "
        "contains(@ng-click, 'removeRepositories')]"),
    "contentviews.repo_search": (
        By.XPATH, "//input[@ng-model='repositorySearch']"),
    "contentviews.promote_button": (
        By.XPATH,
        ("//table[@bst-table='table']//tr/td[contains(., '%s')]"
         "/following-sibling::td[@class='col-sm-2']/button")),
    "contentviews.env_to_promote": (
        By.XPATH,
        "//input[@ng-model='item.selected']/parent::label[contains(., '%s')]"),
    "contentviews.promote_version": (
        By.XPATH, "//button[@ng-click='verifySelection()']"),
    "contentview.version_filter": (
        By.XPATH, "//input[@ng-model='filterTerm' and @placeholder='Filter']"),
    "contentviews.add_module": (
        By.XPATH,
        ("//div[@data-block='actions']"
         "/button[@ui-sref='content-views.details.puppet-modules.names']")),
    "contentviews.select_module": (
        By.XPATH,
        ("//tr/td[contains(., '%s')]/following-sibling::td"
         "/button[@ng-click='selectVersion(item.module_name)']")),
    "contentviews.select_module_ver": (
        By.XPATH,
        ("//tr/td[contains(., '%s')]/following-sibling::td"
         "/button[@ng-click='selectVersion(item)']")),
    "contentviews.get_module_name": (
        By.XPATH, "//div[@data-block='table']//td[contains(., '%s')]"),
    "contentviews.select_cv": (
        By.XPATH,
        ("//div[@bst-table='detailsTable']"
         "//tr[contains(@row-select, 'contentView')]"
         "//td[contains(normalize-space(.), '%s')]"
         "/preceding-sibling::td[@class='row-select']"
         "/input[@type='checkbox']")),
    "contentviews.add_cv": (
        By.XPATH, "//button[@ng-click='addContentViews()']"),
    "contentviews.remove_cv": (
        By.XPATH, "//button[@ng-click='removeContentViews()']"),
    "contentviews.cv_filter": (
        By.XPATH, "//input[@ng-model='contentViewVersionFilter']"),
    "contentviews.content_filters": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href, 'filters')]"),
    "contentviews.new_filter": (
        By.XPATH, "//button[contains(@ui-sref, 'filters.new')]"),
    "contentviews.content_type": (By.ID, "type"),
    "contentviews.type": (By.ID, "inclusion"),
    "contentviews.select_filter_checkbox": (
        By.XPATH,
        ("//tr[@row-select='filter']"
         "//td[contains(normalize-space(.), '%s')]"
         "/preceding-sibling::td[@class='row-select']"
         "/input[@type='checkbox']")),
    "contentviews.remove_filter": (
        By.XPATH, "//button[@ng-click='removeFilters()']"),
    "contentviews.select_filter_name": (
        By.XPATH, "//div[@data-block='table']//td/a[contains(., '%s')]"),
    "contentviews.input_pkg_name": (
        By.XPATH, "//input[@ng-model='rule.name']"),
    "contentviews.select_pkg_version": (
        By.XPATH, "//select[@ng-model='rule.type']"),
    "contentviews.add_pkg_button": (
        By.XPATH, "//button[@ng-click='addRule(rule, filter)']"),
    "contentviews.equal_value": (
        By.XPATH, "//input[@ng-model='rule.version']"),
    "contentviews.greater_min_value": (
        By.XPATH, "//input[@ng-model='rule.min_version']"),
    "contentviews.less_max_value": (
        By.XPATH, "//input[@ng-model='rule.max_version']"),
    "contentviews.select_pkg_checkbox": (
        By.XPATH,
        ("//tr[@row-select='rule']"
         "//td[contains(normalize-space(.), '%s')]"
         "/preceding-sibling::td[@class='row-select']"
         "/input[@type='checkbox']")),
    "contentviews.remove_packages": (
        By.XPATH, "//button[@ng-click='removeRules(filter)']"),
    "contentviews.affected_repos": (
        By.XPATH,
        "//a[contains(@ui-sref, 'filters.details.rpm.repositories')]"),
    "contentviews.show_repos": (
        By.XPATH, "//input[@ng-model='showRepos']"),
    "contentviews.select_pkg_group_checkbox": (
        By.XPATH,
        ("//tr[@row-select='packageGroup']"
         "//td[contains(normalize-space(.), '%s')]"
         "/preceding-sibling::td[@class='row-select']"
         "/input[@type='checkbox']")),
    "contentviews.add_pkg_group": (
        By.XPATH, "//button[@ng-click='addPackageGroups(filter)']"),
    "contentviews.remove_pkg_group": (
        By.XPATH, "//button[@ng-click='removePackageGroups(filter)']"),
    "contentviews.select_errata_checkbox": (
        By.XPATH,
        ("//tr[@row-select='errata']"
         "//td[contains(normalize-space(.), '%s')]"
         "/preceding-sibling::td[@class='row-select']"
         "/input[@type='checkbox']")),
    "contentviews.add_errata": (
        By.XPATH, "//button[@ng-click='addErrata(filter)']"),
    "contentviews.remove_errata": (
        By.XPATH, "//button[@ng-click='removeErrata(filter)']"),
    "contentviews.search_filters": (
        By.XPATH,
        ("//div[@data-block='search']"
         "//input[@ng-model='detailsTable.searchTerm']")),
    "contentviews.search_button": (
        By.XPATH, "//button[contains(@ng-click, 'detailsTable.search')]"),
    "contentviews.filter_name": (
        By.XPATH, "//tr[@row-select='filter']/td[2]/a[contains(., '%s')]"),
    "contentviews.copy": (
        By.XPATH, "//a[@ng-click='showCopy = true']"),
    "contentviews.copy_name": (
        By.XPATH, "//input[@ng-model='copyName']"),
    "contentviews.copy_create": (
        By.XPATH, "//button[@ng-click='copy(copyName)']"),
    "contentviews.yum_repositories": (
        By.XPATH, "//a[@class='ng-scope' and contains(@ui-sref,'yum.list')]"),

    # Content Search
    "contentsearch.open_filter_dropdown": (
        By.XPATH,
        "//div[@id='content_chzn']/a/div"),
    "contentsearch.select_filter": (
        By.XPATH,
        "//fieldset[@id='content_selector']/div/div/div/ul/li[text()='%s']"),
    "contentsearch.content_views": (
        By.XPATH,
        "//input[@id='view_auto_complete']"),
    "contentsearch.products": (
        By.XPATH,
        "//input[@id='product_auto_complete']"),
    "contentsearch.repositories": (
        By.XPATH,
        "//input[@id='repo_auto_complete']"),
    "contentsearch.add_content_views_filter": (
        By.XPATH,
        "//div[@id='view_autocomplete_list']/a"),
    "contentsearch.add_products_filter": (
        By.XPATH,
        "//div[@id='product_autocomplete_list']/a"),
    "contentsearch.repositories_auto_radio": (
        By.XPATH,
        "//input[@id='repos_auto_complete_radio']"),
    "contentsearch.repositories_search_radio": (
        By.XPATH,
        "//input[@id='repos_search_radio']"),
    "contentsearch.add_repositories_filter": (
        By.XPATH,
        "//div[@id='repo_autocomplete_list']/a"),
    "contentsearch.autocomplete_field": (
        By.XPATH,
        "//ul[contains(@class, 'ui-autocomplete')]/li/a[contains(., '%s')]"),
    "contentsearch.repositories_search": (
        By.XPATH,
        "//input[@id='repo_search_input']"),
    "contentsearch.packages_search": (
        By.XPATH,
        "//div[@id='package_search']/input[@id='search']"),
    "contentsearch.puppet_modules_search": (
        By.XPATH,
        "//div[@id='puppet_modules_search']/input[@id='search']"),
    "contentsearch.search": (
        By.ID, "browse_button"),
    "contentsearch.result_entity": (
        By.XPATH,
        "//article[@id='comparison_grid']//span[contains(., '%s')]"),
    "contentsearch.result_entity_open_list": (
        By.XPATH,
        "//article[@id='comparison_grid']//span[contains(., '%s')]/../"
        "i[contains(@class, 'right')]"),
    "contentsearch.open_view_dropdown": (
        By.XPATH,
        "//div[@id='right_select']/div/a/div"),
    "contentsearch.select_view": (
        By.XPATH,
        "//div[@id='right_select']/div/div/ul/li[text()='%s']"),


    # System Groups
    "system-groups.new": (
        By.XPATH, "//button[@ui-sref='system-groups.new.form']"),
    "system-groups.name": (By.ID, "name"),
    "system-groups.description": (By.ID, "description"),
    "system-groups.unlimited": (By.NAME, "limit"),
    "system-groups.limit": (By.ID, "max_systems"),

    "system-groups.remove": (
        By.XPATH, "//button[@ng-disabled='!group.permissions.deletable']"),
    "system-groups.confirm_remove": (
        By.XPATH, "//button[@ng-click='ok()']"),

    "system-groups.search": (
        By.XPATH, "//a[contains(@href,'system-groups') and contains(.,'%s')]"),

    "system-groups.update_name": (
        By.XPATH, "//form[@bst-edit-text='group.name']//div/span/i"),
    "system-groups.update_name_field": (
        By.XPATH, "//form[@bst-edit-text='group.name']/div/input"),
    "system-groups.update_name_save": (
        By.XPATH, "//form[@bst-edit-text='group.name']"
                  "//button[@ng-click='save()']"),

    "system-groups.update_description": (
        By.XPATH, "//form[@bst-edit-textarea='group.description']"
                  "//div/span/i"),
    "system-groups.update_description_field": (
        By.XPATH, "//form[@bst-edit-textarea='group.description']"
                  "//div/textarea"),
    "system-groups.update_description_save": (
        By.XPATH, "//form[@bst-edit-textarea='group.description']"
                  "//button[@ng-click='save()']"),

    "system-groups.update_limit": (
        By.XPATH, "//div[@bst-edit-custom='group.max_systems']//div/span/i"),
    "system-groups.update_limit_checkbox": (
        By.XPATH, "//div[@bst-edit-custom='group.max_systems']"
                  "//div/input[@type='checkbox']"),
    "system-groups.update_limit_field": (
        By.XPATH, "//div[@bst-edit-custom='group.max_systems']"
                  "//div/input[@type='number']"),
    "system-groups.update_limit_save": (
        By.XPATH, "//div[@bst-edit-custom='group.max_systems']"
                  "//button[@ng-click='save()']"),

    # Manifests / subscriptions
    "subs.select": (
        By.XPATH, ("//tr[contains(@ng-repeat-start, 'groupedSubscriptions') "
                   "and contains(., '%s')]/following-sibling::tr[1]/td/"
                   "a[contains(@href, '/info')]")),
    "subs.delete_manifest": (
        By.XPATH, "//button[contains(@ng-click,'deleteManifest')]"),
    "subs.refresh_manifest": (
        By.XPATH, "//button[contains(@ng-click,'refreshManifest')]"),
    "subs.manage_manifest": (
        By.XPATH, "//button[contains(@ui-sref,'manifest.import')]"),
    "subs.repo_url_edit": (
        By.XPATH, ("//form[contains(@bst-edit-text,'redhat_repository_url')]"
                   "//i[contains(@class,'icon-edit')]")),
    "subs.file_path": (
        By.XPATH, ("//input[@name='content']")),
    "subs.upload": (
        By.XPATH, ("//div[@class='form-group']"
                   "/button[contains(@class, 'primary')]")),
    "subs.repo_url_update": (
        By.XPATH, ("//form[contains(@bst-edit-text,'redhat_repository_url')]"
                   "//div/input")),
    "subs.manifest_exists": (
        By.XPATH, "//a[contains(@href,'distributors')]"),
    "subs.subscription_search": (
        By.XPATH,
        "//input[@class='form-control ng-scope ng-pristine ng-valid']"),

    # Settings
    "settings.param": (
        By.XPATH, "//tr/td[contains(., '%s')]"),
    "settings.edit_param": (
        By.XPATH,
        ("//tr/td[contains(., '%s')]"
         "/../td[@class='setting_value']"
         "/span[contains(@class, 'editable')]")),
    "settings.select_value": (
        By.XPATH,
        ("//select[@name='setting[value]']")),
    "settings.input_value": (
        By.XPATH,
        ("//input[@name='setting[value]']")),
    "settings.save": (
        By.XPATH,
        ("//td[@class='setting_value']"
         "/span/form/button[@type='submit']")),

    # Config Groups
    "config_groups.new": (
        By.XPATH, "//a[@data-id='aid_config_groups_new']"),
    "config_groups.name": (
        By.XPATH, "//input[@id='config_group_name']"),
    "config_groups.select_name": (
        By.XPATH, "//a[contains(.,'%s') and contains(@href, 'edit')]"),
    "config_groups.dropdown": (
        By.XPATH,
        ("//td/a[normalize-space(.)='%s']"
         "/following::td/div/a[@data-toggle='dropdown']")),
    "config_groups.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),

    # Hardware Models
    "hwmodels.new": (
        By.XPATH, "//a[@data-id='aid_models_new']"),
    "hwmodels.name": (
        By.XPATH, "//input[@id='model_name']"),
    "hwmodels.model": (
        By.XPATH, "//input[@id='model_hardware_model']"),
    "hwmodels.vclass": (
        By.XPATH, "//input[@id='model_vendor_class']"),
    "hwmodels.info": (
        By.XPATH, "//textarea[@id='model_info']"),
    "hwmodels.select_name": (
        By.XPATH, "//a[contains(@href,'models') and contains(.,'%s')]"),
    "hwmodels.delete": (
        By.XPATH, ("//a[contains(@data-confirm,'%s')"
                   " and @class='delete']")),
    # Discovery Rules
    "discoveryrules.new": (
        By.XPATH, "//a[@data-id='aid_discovery_rules_new']"),
    "discoveryrules.name": (
        By.XPATH, "//input[@id='discovery_rule_name']"),
    "discoveryrules.search": (
        By.XPATH, "//input[@id='search']"),
    "discoveryrules.hostgroup": (
        By.ID, "discovery_rule_hostgroup_id"),
    "discoveryrules.hostname": (
        By.ID, "discovery_rule_hostname"),
    "discoveryrules.host_limit": (
        By.ID, "discovery_rule_max_count"),
    "discoveryrules.priority": (
        By.ID, "discovery_rule_priority"),
    "discoveryrules.enabled": (
        By.ID, "discovery_rule_enabled"),
    "discoveryrules.rule_name": (
        By.XPATH, ("//a[contains(@href, 'discovery_rules')"
                   " and contains(., '%s')]")),
    "discoveryrules.rule_delete": (
        By.XPATH, "//a[contains(@data-confirm, '%s') and @class='delete']"),

    # Discovered Hosts
    "discoveredhosts.hostname": (
        By.XPATH, ("//a[contains(@href, 'discovered_hosts')"
                   " and contains(., '%s')]")),
    "discoveredhosts.dropdown": (
        By.XPATH, ("//a[contains(@href,'%s')]"
                   "/following::a[@data-toggle='dropdown']")),
    "discoveredhosts.delete": (
        By.XPATH, ("//a[@class='delete' and contains(@data-confirm, '%s')]")),

    # LDAP Authentication
    "ldapsource.new": (
        By.XPATH, "//a[@href='/auth_source_ldaps/new']"),
    "ldapserver.name": (
        By.ID, "auth_source_ldap_name"),
    "ldapserver.server": (
        By.ID, "auth_source_ldap_host"),
    "ldapserver.ldaps": (
        By.ID, "auth_source_ldap_tls"),
    "ldapserver.port": (
        By.ID, "auth_source_ldap_port"),
    "ldapserver.server_type": (
        By.ID, "auth_source_ldap_server_type"),
    "ldapserver.loginname": (
        By.ID, "auth_source_ldap_attr_login"),
    "ldapserver.firstname": (
        By.ID, "auth_source_ldap_attr_firstname"),
    "ldapserver.surname": (
        By.ID, "auth_source_ldap_attr_lastname"),
    "ldapserver.mail": (
        By.ID, "auth_source_ldap_attr_mail"),
    "ldapserver.photo": (
        By.ID, "auth_source_ldap_attr_photo"),
    "ldapserver.acc_user": (
        By.ID, "auth_source_ldap_account"),
    "ldapserver.acc_passwd": (
        By.ID, "auth_source_ldap_account_password"),
    "ldapserver.basedn": (
        By.ID, "auth_source_ldap_base_dn"),
    "ldapserver.group_basedn": (
        By.ID, "auth_source_ldap_groups_base"),
    "ldapserver.ldap_filter": (
        By.ID, "auth_source_ldap_ldap_filter"),
    "ldapserver.otf_register": (
        By.ID, "auth_source_ldap_onthefly_register"),
    "ldapserver.ldap_delete": (
        By.XPATH, "//a[@data-confirm='Delete %s?']"),
    "ldapserver.ldap_servername": (
        By.XPATH,
        ("//span[contains(.,'%s') or "
         "contains(@data-original-title, '%s')]/../../a")),
    "ldapserver.refresh": (
        By.XPATH,
        ("//td[contains(.,'foobargroup')]/../td/"
         "a[contains(@data-id, 'refresh')]")),

    # Red Hat Access Insights locators
    "insights.registered_systems": (
        By.XPATH,
        ("//div[@class='system-summary']/p")),
    "insights.org_selection_msg": (
        By.ID, "content"),
    "insights.unregister_system": (
        By.XPATH, (
            "//td[contains(*,'%s')]/../td/a[@class='fa fa-close blacklist' "
            "and contains(@title,'Unregister System')]")),
    "insights.unregister_button": (
        By.XPATH, (
            "//div[@class='sweet-alert showSweetAlert visible']//"
            "button[@class='confirm']")),
    "insights.no_systems_element": (
        By.XPATH, (
            "//div[@class='text-center']//h4")
        ),

    # OpenScap locators
    # Scap Content
    "oscap.content_search": (
        By.XPATH, "//input[contains(@data-url, 'auto_complete_search')]"),
    "oscap.content_edit": (
        By.XPATH, "//td[contains(.,'%s')]/../td/div/span/a"),
    "oscap.content_dropdown": (
        By.XPATH,
        ("//td[contains(.,'%s')]/following-sibling::td/div/"
         "a[@data-toggle='dropdown']")),
    "oscap.content_download": (
        By.XPATH,
        ("//td[contains(.,'%s')]/../td/div/ul/li/"
         "a[contains(@data-id, 'compliance_scap_contents') "
         "and not(contains(@class, 'delete'))]")),
    "oscap.content_delete": (
        By.XPATH,
        ("//td[contains(.,'%s')]/../td/div/ul/li/"
         "a[contains(@data-id, 'compliance_scap_contents') "
         "and contains(@class, 'delete')]")),
    "oscap.content_select": (
        By.XPATH,
        "//div[@id='content']//td[contains(.,'%s')]"),

    # oscap policy
    "oscap.new_policy": (
        By.XPATH,
        ("//a[contains(@class, 'btn') and "
         "contains(@data-id, 'compliance_policies_new')]")),
    "oscap.select_policy": (
        By.XPATH,
        "//a[contains(@href,'policies') and contains(.,'%s')]"),
    "oscap.delete_policy": (
        By.XPATH,
        ("//a[contains(@href,'policies') and contains(.,'%s')]/../../"
         "td/div/ul/li/a[@class='delete']")),
    "oscap.edit_policy": (
        By.XPATH,
        ("//a[contains(@href,'policies') and contains(.,'%s')]"
         "/../../td/div/ul/li/a[contains(@href,'edit')]")),
    "oscap.dropdown_policy": (
        By.XPATH,
        ("//a[contains(@href,'policies') and contains(.,'%s')]"
         "/../../td/div/a/i")),
    "oscap.name_policy": (By.ID, "policy_name"),
    "oscap.desc_policy": (By.ID, "policy_description"),
    "oscap.content_policy": (By.ID, "policy_scap_content_id"),
    "oscap.profile_policy": (By.ID, "policy_scap_content_profile_id"),
    "oscap.period_policy": (By.ID, "policy_period"),
    "oscap.weekday_policy": (By.ID, "policy_weekday"),
    "oscap.dayofmonth_policy": (By.ID, "policy_day_of_month"),
    "oscap.custom_policy": (By.ID, "policy_cron_line"),

    # oscap reports
    "oscap.report_select": (
        By.XPATH, "//span[contains(@data-original-title, '%s')]"),

    # Registries
    "registry.new": (By.XPATH, "//a[contains(@href, '/registries/new')]"),
    "registry.name": (By.ID, "docker_registry_name"),
    "registry.url": (By.ID, "docker_registry_url"),
    "registry.description": (By.ID, "docker_registry_description"),
    "registry.username": (By.ID, "docker_registry_username"),
    "registry.password": (By.ID, "docker_registry_password"),
    "registry.delete": (
        By.XPATH,
        "//a[contains(@data-confirm, '%s') and @class='delete']"),
    "registry.select_name": (
        By.XPATH, ("//a[contains(@href, 'registries')"
                   " and contains(.,'%s')]")),
    # Containers
    "container.new": (By.XPATH, "//a[contains(@href, '/containers/new')]"),
    "container.resource_name": (
        By.XPATH,
        "//select[contains(@id, 'preliminary_compute_resource_id')]"),
    "container.next_section": (By.ID, "next"),
    "container.content_view_tab": (By.ID, "katello_tab"),
    "container.content_view_tab_next": (By.ID, "next_katello"),
    "container.docker_hub_tab": (By.ID, "hub_tab"),
    "container.docker_hub_tab_next": (By.ID, "next_hub"),
    "container.external_registry_tab": (By.ID, "registry_tab"),
    "container.external_registry_tab_next": (By.ID, "next_registry"),
    "container.lifecycle_environment": (
        By.XPATH, "//select[@id='kt_environment_id']"),
    "container.content_view": (By.XPATH, "//select[@id='content_view_id']"),
    "container.repository": (By.XPATH, "//select[@id='repository_id']"),
    "container.tag": (By.XPATH, "//select[@id='tag_id']"),
    "container.capsule": (By.XPATH, "//select[@id='capsule_id']"),
    "container.docker_hub_tag": (
        By.ID, "hub_docker_container_wizard_states_image_tag"),
    "container.name": (
        By.ID, "docker_container_wizard_states_configuration_name"),
    "container.command": (
        By.ID, "docker_container_wizard_states_configuration_command"),
    "container.entrypoint": (
        By.ID, "docker_container_wizard_states_configuration_entrypoint"),
    "container.cpu_sets": (
        By.ID, "docker_container_wizard_states_configuration_cpu_set"),
    "container.cpu_shares": (
        By.ID, "docker_container_wizard_states_configuration_cpu_shares"),
    "container.memory": (
        By.ID, "docker_container_wizard_states_configuration_memory"),
    "container.tty": (
        By.ID, "docker_container_wizard_states_environment_tty"),
    "container.attach_stdin": (
        By.ID, "docker_container_wizard_states_environment_attach_stdin"),
    "container.attach_stdout": (
        By.ID, "docker_container_wizard_states_environment_attach_stdout"),
    "container.attach_stderr": (
        By.ID, "docker_container_wizard_states_environment_attach_stderr"),
    "container.run": (By.ID, "start_on_create"),
    "container.created_container_name": (
        By.XPATH, "//table[@id='properties_table']//td[contains(., '%s')]"),
    "container.resource_search_tab": (By.XPATH, "//a[contains(., '%s')]"),
    "container.search_filter": (
        By.XPATH,
        "//div[@class='tab-content']/div[contains(@class, 'active')]//"
        "input[contains(@aria-controls, 'DataTables_Table')]"),
    "container.search_entity": (
        By.XPATH,
        "//div[@class='tab-content']/div[contains(@class, 'active')]//"
        "td[@id='%s']/a"),
    "container.delete": (By.XPATH, "//a[contains(@class, 'delete')]"),
    "container.power_on": (
        By.XPATH,
        "//div[@class='tab-content']/div[contains(@class, 'active')]//"
        "td[@id='%s']/../td/div/a[contains(., 'Power  On')]"),
    "container.power_off": (
        By.XPATH,
        "//div[@class='tab-content']/div[contains(@class, 'active')]//"
        "td[@id='%s']/../td/div/a[contains(., 'Power  Off')]"),
    "container.power_status": (
        By.XPATH,
        "//div[@class='tab-content']/div[contains(@class, 'active')]//"
        "td[@id='%s']/../td/span[contains(@class, 'label-')]"),
})
