#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from selenium.webdriver.common.by import By

locators = {

    # Dialogs
    "dialog.yes": "//div[@class='ui-dialog-buttonset']/button[1]/span",
    "dialog.no": "//div[@class='ui-dialog-buttonset']/button[2]/span",

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

    # Users
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

    # Menus

    ## Administer
    "menu.administer": (By.XPATH, "//nav[@class='nav admin_menu right']/ul/li/a/span[@class='ng-binding']"),
    "submenu.organizations": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li[1]/a"),
    "submenu.users": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li[2]/a"),
    "submenu.roles": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li[3]/a"),
    "submenu.about": (By.XPATH, "//ul[@class='dropdown dropdown-right dropdown-active']/li[4]/a"),

}
