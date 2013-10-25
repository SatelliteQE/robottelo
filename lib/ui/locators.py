#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from selenium.webdriver.common.by import By

locators = {

    # Dialogs
    "dialog.yes": "//div[@class='ui-dialog-buttonset']/button[1]/span",
    "dialog.no": "//div[@class='ui-dialog-buttonset']/button[2]/span",

    # Notifications
    "notif.error": (By.XPATH, "//ul[@class='error']"),
    "notif.warn": (By.XPATH, "//ul[@class='warning']"),
    "notif.success": (By.XPATH, "//ul[@class='success']"),
    "notif.close": (By.XPATH, "//div[@class='control']"),

    # Login
    "login.username": (By.CLASS_NAME, "username"),
    "login.password": (By.CLASS_NAME, "password"),
    "login.submit": (By.NAME, "commit"),
    "login.gravatar": (By.XPATH, "//span[@class='gravatar-span']"),
    "login.user": (By.XPATH, "//span[@class='ng-binding']"),
    "login.interstitial": (By.ID, "interstitial"),
    "login.logout": (By.XPATH, "//a[contains(@href, 'logout')]"),

    # Users
    "users.new": "new",
    "users.username": "user_username",
    "users.email": "user_email",
    "users.password1": "password_field",
    "users.password2": "confirm_field",
    "users.save": "save_user",
    "users.user": "//div[@title='%s']",
    "users.remove": "//a[@class='remove_item']",
    "users.locale": "locale[locale]",

    # Menus

    ## Administer
    "menu.administer": "//nav[@class='nav admin_menu right']/ul/li/a/span[@class='ng-binding']",
    "submenu.organizations": "//ul[@class='dropdown dropdown-right dropdown-active']/li[1]/a",
    "submenu.users": "//ul[@class='dropdown dropdown-right dropdown-active']/li[2]/a",
    "submenu.roles": "//ul[@class='dropdown dropdown-right dropdown-active']/li[3]/a",
    "submenu.about": "//ul[@class='dropdown dropdown-right dropdown-active']/li[4]/a"

}
