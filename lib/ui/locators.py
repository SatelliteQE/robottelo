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
    "login.gravatar": (By.XPATH, "//span[@class='gravatar-span']"),
    "login.user": (By.XPATH, "//li[@class='dropdown']/a[@class='dropdown-toggle']"),
    "login.logout": (By.XPATH, "//a[contains(@href, 'logout')]"),

    # Users

    # Organizations
    
    #Operating system (OS)
    "operatingsys.new": (By.XPATH, "//a[contains(@href, '/operatingsystems/new')]"),
    "operatingsys.name": (By.ID, "operatingsystem_name"),
    "operatingsys.majorversion": (By.ID, "operatingsystem_major"),
    "operatingsys.minorversion": (By.ID, "operatingsystem_minor"),
    "operatingsys.family": (By.ID, "operatingsystem_family"),
    "operatingsys.submit": (By.NAME, "commit"),
    
    

    # Menus
    #TODO: Get DEV to add UNIQUE IDS to these menus

    # Dashboard
    "menu.dashboard": (By.XPATH, "//a[contains(@href='/dashboard')]"),
    # Hosts
    "menu.hosts": (By.XPATH, "//a[contains(@href='/hosts')]"),
    # Reports
    "menu.reports": (By.XPATH, "//a[contains(@href='/reports')]"),
    # Facts
    "menu.facts": (By.XPATH, "//a[contains(@href='/facts')]"),
    # Audits
    "menu.audits": (By.XPATH, "//a[contains(@href='/audits')]"),
    # Statistics
    "menu.stats": (By.XPATH, "//a[contains(@href='/statistics')]"),
    # Trends
    "menu.trends": (By.XPATH, "//a[contains(@href='/trends')]"),
    # More
    "menu.more": (By.XPATH, "//div[contains(@style,'static')]//ul[@id='menu2']/li/a"),
}
