#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from selenium.webdriver.common.by import By

locators = {

    # Notifications
    "notif.error": (
        By.XPATH, "//div[contains(@class, 'jnotify-notification-error')]"),
    "notif.warning": (
        By.XPATH, "//div[contains(@class, 'jnotify-notification-warning')]"),
    "notif.success": (
        By.XPATH, "//div[contains(@class, 'jnotify-notification-success')]"),
    "notif.close": (
        By.XPATH, "//a[@class='jnotify-close']"),

    # Login
    "login.username": (By.ID, "login_login"),
    "login.password": (By.ID, "login_password"),
    "login.submit": (By.NAME, "commit"),
    "login.gravatar": (By.XPATH, "//img[contains(@class, 'gravatar')]"),

    # Organizations
    
    #Operating system (OS)
    "operatingsys.new": (By.XPATH, "//a[contains(@href, '/operatingsystems/new')]"),
    "operatingsys.name": (By.ID, "operatingsystem_name"),
    "operatingsys.major_version": (By.ID, "operatingsystem_major"),
    "operatingsys.minor_version": (By.ID, "operatingsystem_minor"),
    "operatingsys.family": (By.ID, "operatingsystem_family"),
    "operatingsys.delete": (By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "operatingsys.submit": (By.NAME, "commit"),

    # Hostgroups

    "hostgroups.new": (By.XPATH, "//a[contains(@href, '/hostgroups/new')]"),
    "hostgroups.name": (By.ID, "hostgroup_name"),
    "hostgroups.parent": (By.ID, "hostgroup_parent_id"),
    "hostgroups.environment": (By.ID, "hostgroup_environment_id"),
    "hostgroups.hostgroup": (By.XPATH, "//a[contains(., '%s')]"),
    "hostgroups.dropdown": (By.XPATH, "//a[contains(@href,'%s') and contains(.,'Nest')]/../../a"),
    "hostgroups.delete": (By.XPATH, "//a[contains(@href,'%s') and contains(.,'Delete')]"),

    # Users

    "users.new": (By.XPATH, "//a[contains(@href, '/users/new')]"),
    "users.username" : (By.ID, "user_login"),
    "users.firstname" : (By.ID, "user_firstname"),
    "users.lastname" : (By.ID, "user_lastname"),
    "users.email" : (By.ID, "user_mail"),
    "users.language" : (By.ID, "user_locale"),
    "users.authorized_by" : (By.ID, "user_auth_source_id"),
    "users.password" : (By.ID, "user_password"),
    "users.password_confirmation" : (By.ID, "user_password_confirmation"),
    "users.user" : (By.XPATH, "//a[contains(., '%s')]"),
    "users.delete": (By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),

    #common locators
    "search": (By.ID, "search"),
    "submit": (By.NAME, "commit"),
 
    #Architecture
    "arch.new": (By.XPATH, "//a[contains(@href, '/architectures/new')]"),
    "arch.name": (By.ID, "architecture_name"),
    "arch.submit": (By.NAME, "commit"),
    "arch.delete": (By.XPATH, "//a[contains(@href, '/architectures/%s')]"),
    "arch.arch_name": (By.XPATH, "//a[contains(., '%s')]"),
    "arch.os_name": (By.XPATH, "//label[@class='operatingsystem' and contains(., '%s')]"),
    
    #Medium
    "medium.new": (By.XPATH, "//a[contains(@href, '/media/new')]"),
    "medium.name": (By.ID, "medium_name"),
    "medium.path": (By.ID, "medium_path"),
    "medium.os_family": (By.ID, "medium_os_family"),
    "medium.delete": (By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "medium.medium_name": (By.XPATH, "//a[contains(., '%s')]"),
    
    #Domain
    "domain.new": (By.XPATH, "//a[contains(@href, '/domains/new')]"),
    "domain.name": (By.ID, "domain_name"),
    "domain.description": (By.ID, "domain_fullname"),
    "domain.dns_proxy": (By.ID, "domain_dns_id"),
    "domain.delete": (By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "domain.parameter_tab": (By.XPATH, "//a[contains(., 'Parameters')]"),
    "domain.add_parameter": (By.XPATH, "//a[contains(text(),'+ Add Parameter')]"),
    "domain.parameter_name": (By.XPATH, "//input[@placeholder='Name']"),
    "domain.parameter_value": (By.XPATH, "//textarea[@placeholder='Value']"),
    "domain.parameter_remove": (By.XPATH, "//div/input[@value='%s']/following-sibling::span/a/i"),
    "domain.domain_description": (By.XPATH, "//a[contains(., '%s')]"),

    #Environment
    "env.new": (By.XPATH, "//a[contains(@href, '/environments/new')]"),
    "env.name": (By.ID, "environment_name"),
    "env.delete": (By.XPATH, "//a[contains(@href,'%s') and contains(.,'Delete')]"),
    "env.env_name": (By.XPATH, "//a[normalize-space(.)='%s']"),
    "env.dropdown": (By.XPATH, "//a[contains(@href,'%s') and contains(.,'Classes')]/../../a"),

    # Menus

    # Monitor Menu
    "menu.monitor": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='monitor_menu']"),
    "menu.dashboard": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_dashboard']"),
    "menu.reports": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_reports']"),
    "menu.facts": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_fact_values']"),
    "menu.statistics": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_statistics']"),
    "menu.trends": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_trends']"),
    "menu.audits": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_audits']"),

    # Hosts Menu
    "menu.hosts": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='hosts_menu']"),
    "menu.all_hosts": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_hosts']"),
    "menu.operating_systems": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_operatingsystems']"),
    "menu.provisioning_templates": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_config_templates']"),
    "menu.partition_tables": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_ptables']"),
    "menu.installation_media": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_media']"),
    "menu.hardware_models": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_models']"),
    "menu.architectures": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_architectures']"),

    # Configure Menu
    "menu.configure": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='configure_menu']"),
    "menu.host_groups": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_hostgroups']"),
    "menu.global_parameters": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_common_parameters']"),
    "menu.environments": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_environments']"),
    "menu.puppet_classes": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_puppetclasses']"),
    "menu.smart_variables": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_lookup_keys']"),

    # Infrastructure Menu
    "menu.infrastructure": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='infrastructure_menu']"),
    "menu.smart_proxies": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_smart_proxies']"),
    "menu.compute_resources": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_compute_resources']"),
    "menu.subnets": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_subnets']"),
    "menu.domains": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_domains']"),

    # Administer Menu
    "menu.administer": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='administer_menu']"),
    "menu.ldap_auth": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_auth_source_ldaps']"),
    "menu.users": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_users']"),
    "menu.user_groups": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_usergroups']"),
    "menu.roles": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_roles']"),
    "menu.bookmarks": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_bookmarks']"),
    "menu.settings": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_settings']"),
    "menu.about": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_about_index']"),

    # Account Menu
    "menu.account": (
        By.XPATH,
        "//a[@id='account_menu']"),
    "menu.sign_out": (
        By.XPATH,
        "//a[@id='menu_item_logout']"),
    "menu.my_account": (
        By.XPATH,
        "//a[@id='menu_item_my_account']"),

}
