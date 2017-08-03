# -*- encoding: utf-8 -*-
"""Implements different locators for UI"""

from selenium.webdriver.common.by import By
from .model import LocatorDict

NAVBAR_PATH = (
    '//div[contains(@class,"navbar-inner") and '
    'not(contains(@style, "display"))]'
)

MENU_CONTAINER_PATH = NAVBAR_PATH + '//ul[@id="menu"]'
ADM_MENU_CONTAINER_PATH = NAVBAR_PATH + '//ul[@id="menu2"]'


menu_locators = LocatorDict({
    # Menus
    # Navbar
    "navbar.spinner": (By.XPATH, ("//div[@id='turbolinks-progress']")),

    # Monitor Menu
    "menu.monitor": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='monitor_menu']")),
    "menu.dashboard": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_dashboard']")),
    "menu.reports": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_reports']")),
    "menu.facts": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_fact_values']")),
    "menu.statistics": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_statistics']")),
    "menu.trends": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_trends']")),
    "menu.audits": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_audits']")),
    "menu.jobs": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_job_invocations']")),
    "menu.tasks": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_tasks']")),

    # Content Menu
    "menu.content": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='content_menu']")),
    "menu.life_cycle_environments": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_environments']")),
    "menu.red_hat_subscriptions": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_red_hat_subscriptions']")),
    "menu.activation_keys": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_activation_keys']")),
    "menu.red_hat_repositories": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_redhat_provider']")),
    "menu.products": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_products']")),
    "menu.gpg_keys": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_gpg_keys']")),
    "menu.sync_status": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_sync_status']")),
    "menu.sync_plans": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_sync_plans']")),
    "menu.content_views": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_content_views']")),
    "menu.errata": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_errata']")),
    "menu.packages": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_packages']")),
    "menu.puppet_modules": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_puppet_modules']")),
    "menu.docker_tags": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_docker_tags']")),

    # Containers Menu
    "menu.containers": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='containers_menu']")),
    "menu.all_containers": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_containers']")),
    "menu.new_container": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_new_container']")),
    "menu.registries": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_registries']")),

    # Hosts Menu
    "menu.hosts": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='hosts_menu']")),
    "menu.all_hosts": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_hosts']")),
    "menu.discovered_hosts": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_discovered_hosts']")),
    "menu.content_hosts": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_content_hosts']")),
    "menu.host_collections": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@id='menu_item_host_collections']")),
    "menu.operating_systems": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_operatingsystems']")),
    "menu.provisioning_templates": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@id='menu_item_provisioning_templates']")),
    "menu.partition_tables": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_partition_tables']")),
    "menu.job_templates": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_job_templates']")),
    "menu.installation_media": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_media']")),
    "menu.hardware_models": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_models']")),
    "menu.architectures": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_architectures']")),
    "menu.oscap_policy": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_compliance_policies']")),
    "menu.oscap_content": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_compliance_contents']")),
    "menu.oscap_reports": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_compliance_reports']")),
    "menu.oscap_tailoringfile": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_compliance_files']")),

    # Configure Menu
    "menu.configure": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='configure_menu']")),
    "menu.host_groups": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_hostgroups']")),
    "menu.discovery_rules": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_discovery_rules']")),
    "menu.global_parameters": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_common_parameters']")),
    "menu.environments": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//li[contains(@class,'menu_tab_environments')]"
         "/a[@id='menu_item_environments']")),
    "menu.puppet_classes": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_puppetclasses']")),
    "menu.smart_variables": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_variable_lookup_keys']")),
    "menu.smart_class_parameters": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@id='menu_item_puppetclass_lookup_keys']")),
    "menu.configure_groups": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_config_groups']")),

    # Infrastructure Menu
    "menu.infrastructure": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='infrastructure_menu']")),
    "menu.smart_proxies": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_smart_proxies']")),
    "menu.compute_resources": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_compute_resources']")),
    "menu.compute_profiles": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_compute_profiles']")),
    "menu.subnets": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_subnets']")),
    "menu.domains": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='menu_item_domains']")),

    # Access Insights menu
    "menu.insights": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@id='redhat_access_top_menu']")),
    "insights.overview": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//a[@href='/redhat_access/insights']")),
    "insights.rules": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@href='/redhat_access/insights/rules/']")),
    "insights.systems": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@href='/redhat_access/insights/systems/']")),
    "insights.manage": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@href='/redhat_access/insights/manage']")),


    # Administer Menu
    "menu.administer": (
        By.XPATH,
        (ADM_MENU_CONTAINER_PATH + "//a[@id='administer_menu']")),
    "menu.ldap_auth": (
        By.XPATH,
        (ADM_MENU_CONTAINER_PATH + "//a[@id='menu_item_auth_source_ldaps']")),
    "menu.users": (
        By.XPATH,
        (ADM_MENU_CONTAINER_PATH + "//a[@id='menu_item_users']")),
    "menu.user_groups": (
        By.XPATH,
        (ADM_MENU_CONTAINER_PATH + "//a[@id='menu_item_usergroups']")),
    "menu.roles": (
        By.XPATH,
        (ADM_MENU_CONTAINER_PATH + "//a[@id='menu_item_roles']")),
    "menu.bookmarks": (
        By.XPATH,
        (ADM_MENU_CONTAINER_PATH + "//a[@id='menu_item_bookmarks']")),
    "menu.settings": (
        By.XPATH,
        (ADM_MENU_CONTAINER_PATH + "//a[@id='menu_item_settings']")),
    "menu.about": (
        By.XPATH,
        (ADM_MENU_CONTAINER_PATH + "//a[@id='menu_item_about_index']")),

    # Account Menu
    "menu.account": (By.XPATH, "//a[@id='account_menu']"),
    "menu.sign_out": (By.XPATH, "//a[@id='menu_item_logout']"),
    "menu.my_account": (By.XPATH, "//a[@id='menu_item_my_account']"),

    # Common Locators for Orgs and Locations
    "menu.any_context": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//li[contains(@class,'org-switcher')]/a")),
    # Updated to current_text as the fetched text can also be org+loc
    "menu.current_text": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//li[contains(@class,'org-switcher')]/a")),
    "menu.fetch_org": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//li[contains(@class, 'org-menu')]/a")),
    "menu.fetch_loc": (
        By.XPATH,
        (MENU_CONTAINER_PATH + "//li[contains(@class, 'loc-menu')]/a")),

    # Orgs
    "org.manage_org": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@class='manage-menu' and contains(@href, 'organizations')]")),
    "org.nav_current_org": (
        By.XPATH,
        ("(" + MENU_CONTAINER_PATH +
         "//li[contains(@class,'org-switcher')]"
         "//li/a[@data-toggle='dropdown'])[1]")),
    "org.select_org": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@href='/organizations/clear']/../../li/a[contains(.,'%s')]|"
         "//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/organizations/clear']/../../li/a"
         "/span[contains(@data-original-title, '%s')]")),

    # Locations
    "loc.manage_loc": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@class='manage-menu' and contains(@href, 'locations')]")),
    "loc.nav_current_loc": (
        By.XPATH,
        ("(" + MENU_CONTAINER_PATH +
         "//li[contains(@class,'org-switcher')]"
         "//li/a[@data-toggle='dropdown'])[2]")),
    "loc.select_loc": (
        By.XPATH,
        (MENU_CONTAINER_PATH +
         "//a[@href='/locations/clear']/../../li/a[contains(.,'%s')]|"
         "//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/locations/clear']/../../li/a"
         "/span[contains(@data-original-title, '%s')]"))
})
