#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from selenium.webdriver.common.by import By

locators = {

    # Dialogs
    "dialog.yes": (By.XPATH, "//div[@class='ui-dialog-buttonset']/button[1]/span"),
    "dialog.no": (By.XPATH, "//div[@class='ui-dialog-buttonset']/button[2]/span"),

    # Notifications
    "notif.error": (By.XPATH, "//div[contains(@class, 'jnotify-notification-error')]"),
    "notif.warn": (By.XPATH, "//div[contains(@class, 'jnotify-notification-warning')]"),
    "notif.success": (By.XPATH, "//div[contains(@class, 'jnotify-notification-success')]"),
    "notif.close": (By.XPATH, "//a[@class='jnotify-close']"),

    # Login
    "login.username": (By.CLASS_NAME, "username"),
    "login.password": (By.CLASS_NAME, "password"),
    "login.submit": (By.NAME, "commit"),
    "login.gravatar": (By.XPATH, "//span[@class='gravatar-span']"),
    "login.user": (By.XPATH, "//span[@class='ng-binding']"),
    "login.interstitial": (By.ID, "interstitial"),
    "login.logout": (By.XPATH, "//a[contains(@href, 'logout')]"),
    "login.selectOrg": (By.XPATH, "//a[@class='org-link' and contains(., '%s')]"),
    "login.forgotUserName": (By.ID, "username_link"),
    "login.forgotUserNameEmail": (By.ID, "email"),
    "login.forgotUserNameSubmit": (By.XPATH, "//input[@class='button primary'][@value='Send Login']"),
    "login.forgotPassword": (By.ID, "password_reset"),

    # Users
    "users.search": (By.ID, "search"),
    "users.new": (By.ID, "new"),
    "users.username": (By.ID, "user_username"),
    "users.email": (By.ID, "user_email"),
    "users.password1": (By.ID, "password_field"),
    "users.password2": (By.ID, "confirm_field"),
    "users.save": (By.ID, "save_user"),
    "users.save_password": (By.ID, "save_password"),
    "users.user": (By.XPATH, "//div[@title='%s']"),
    "users.remove": (By.XPATH, "//a[@class='remove_item']"),
    "users.locale": (By.ID, "locale_locale"),

    # Organizations
    "orgs.search": (By.ID, "search"),
    "orgs.new": (By.ID, "new"),
    "orgs.name": (By.ID, "organization_name"),
    "orgs.label": (By.ID, "organization_label"),
    "orgs.description": (By.ID, "organization_description"),
    "orgs.env_name": (By.ID, "environment_name"),
    "orgs.env_label": (By.ID, "environment_label"),
    "orgs.env_description": (By.ID, "environment_description"),
    "orgs.save": (By.NAME, "commit"),
    "orgs.remove": (By.XPATH, "//a[@class='remove_item']"),
    "orgs.org": (By.XPATH, "//div[@title='%s']"),

    # Organization Details
    "orgs.details_secion": (By.XPATH, "//li[@id='organization_details']/a"),
    "org.name": (By.NAME, "organization[name]"),
    "org.description": (By.NAME, "organization[description]"),
    "org.sla": (By.NAME, "organization[service_level]"),

    # Organization Defaults
    "orgs.default_info_section": (By.XPATH, "//li[@id='organization_default_info']/a"),
    # Organization System Default Info
    "org.system_default_link": (By.XPATH, "//li[@id='org_system_default_info']/a"),
    # Organization Distributor Default Info
    "org.distributor_default_link": (By.XPATH, "//li[@id='org_distributor_default_info']/a"),

    "org.default_keyname_field": (By.ID, "new_default_info_keyname"),
    "org.default_keyname_save": (By.ID, "add_default_info_button"),
    "org.default_keyname_apply": (By.ID, "apply_default_info_button"),
    "org.default_keyname_remove": (By.XPATH, "//input[@data-id='default_info_%s']"),

    # Organization History
    "orgs.history_section": (By.XPATH, "//li[@id='organization_history']/a"),

    # Menus

    ## Administer
    "menu.administer": (By.XPATH, "//nav[@class='nav admin_menu right']/ul/li/a/span[@class='ng-binding']"),
    "submenu.organizations": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li/a[contains(@href,'/organizations')]"),
    "submenu.users": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li/a[contains(@href,'/users')]"),
    "submenu.roles": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li/a[contains(@href,'/roles')]"),
    "submenu.about": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li/a[contains(@href,'/about')]"),
    "submenu.reports": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li/a[contains(@href,'/filters')]")

}
