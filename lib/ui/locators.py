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

    #TODO: Get DEV to add UNIQUE IDS to these menus

    # Dashboard
    "menu.dashboard": (By.XPATH, "//nav[@class='nav left']/ul/li[1]/a/span"),
    # Content
    "menu.content": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/a/span"),
    ## Subscriptions
    "menu.subscriptions": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[1]/a/span"),
    ### Red Hat Subscriptions
    "menu.redhatsubs": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[1]/ul/li[1]/a"),
    ### Subscription Management Applications
    "menu.distributors": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[1]/ul/li[2]/a"),
    ### Activation Keys
    "menu.actkeys": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[1]/ul/li[3]/a"),
    ### Import History
    "menu.importhistory": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[1]/ul/li[4]/a"),
    ## Repositories
    "menu.repos": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[2]/a/span"),
    ## Red Hat Repos
    "menu.redhatrepos": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[2]/ul/li[1]/a"),
    ## Products
    "menu.products": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[2]/ul/li[2]/a"),
    ## GPG Keys
    "menu.gpgkeys": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[2]/ul/li[3]/a"),
    ## Synchronization
    "menu.sync": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[3]/a/span"),
    ### Sync Status
    "menu.syncstatus": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[3]/ul/li[1]/a"),
    ### Sync Plans
    "menu.syncplans": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[3]/ul/li[2]/a"),
    ### Sync Schedule
    "menu.syncschedule": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[3]/ul/li[3]/a"),
    ## Content View Definitions
    "menu.contentview": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[4]/a/span"),
    ## Content Search
    "menu.contentsearch": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[5]/a/span"),
    ## Changesets
    "menu.changesets": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[6]/a/span"),
    ### Changeset Management
    "menu.changesetmanage": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[6]/ul/li[1]/a"),
    ### Changeset History
    "menu.changesethistory": (By.XPATH, "//nav[@class='nav left']/ul/li[2]/ul/li[6]/ul/li[2]/a"),
    ## Systems
    "menu.systems": (By.XPATH, "//nav[@class='nav left']/ul/li[3]/a/span"),
    ### All Systems
    "menu.systemsall": (By.XPATH, "//nav[@class='nav left']/ul/li[3]/ul/li[1]/a"),
    ### System Groups
    "menu.systemgroups": (By.XPATH, "//nav[@class='nav left']/ul/li[3]/ul/li[2]/a"),
    ## Administer
    "menu.administer": (By.XPATH, "//nav[@class='nav admin_menu right']/ul/li/a/span"),
    ### Organizations
    "menu.organizations": (By.XPATH, "//ul/li/a[contains(@href,'/organizations')]"),
    ### Users
    "menu.users": (By.XPATH, "//ul/li/a[contains(@href,'/users')]"),
    ### Roles
    "menu.roles": (By.XPATH, "//ul/li/a[contains(@href,'/roles')]"),
    ### About
    "menu.about": (By.XPATH, "//ul/li/a[contains(@href,'/about')]"),
    ### Reports
    "menu.reports": (By.XPATH, "//ul/li/a[contains(@href,'/filters')]")

}
