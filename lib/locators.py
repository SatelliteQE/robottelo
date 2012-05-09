#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# Administration

ADMIN_TAB = "//li[@id='admin']/a"

# Organizations

ENV = "//a[contains(@class, 'subpanel_element')]/div[contains(.,'%s')]"
ENV_NAME_FIELD = "//form[@id='new_subpanel']/fieldset/div/input"
ENV_REMOVE_LINK = "//div[@id='subpanel']/div/div[2]/div/a"
ENV_SAVE_BUTTON = "//form[@id='new_subpanel']/div[2]/input"
HEADER_ORGANIZATIONS = "//li[@id='organizations']/a"
NEW_ENV_BUTTON = "//div[contains(@class, 'button subpanel_element')]"
NEW_ORG = "//div[@id='organization_%s']/div"
NEW_ORG_LINK = "//div[@id='list-title']/header/a"
ORG = "//a[contains(., '%s')]"
ORGANIZATIONS_SELECTOR = "//a[@id='switcherButton']/div"
ORGS_LIST_LINK = "//li[@id='org_list']/a"
ORG_NAME = "//form[@id='new_organization']/fieldset/div[2]/input"
ORG_REMOVE_LINK = "//div[@id='panel']/div/div[2]/div/a"
ORG_SUBMIT = "//form[@id='new_organization']/div[2]/div/input"
PRIOR_ENV_LIST = "//form[@id='new_subpanel']/fieldset[3]/div/select"

# Content

CUSTOM_PROVIDERS = 'custom_providers'
ENABLE_REPOS_TAB = "//div[@id='tabs']/nav/ul/li[2]/a"
FILTERS = 'filters'
GPG = 'gpg'
HEADER_CONTENT_MANAGEMENT = "//li[@id='content']/a"
MANIFEST_FILE_FIELD = "//form[@id='upload_manifest']/div[2]/input"
MANIFEST_FORCE_CHECKBOX = "//div[@id='force_checkbox']/input"
MANIFEST_SAVE_BUTTON = "//div[@id='upload_button']/a"
NEW_PRODUCT_BUTTON = "//div[@class='button subpanel_element']"
PRODUCT = ".//li/div/div"
PRODUCTS = "//div[@id='products']/ul[contains(@class, 'clear fl')]"
PRODUCT_DESCRIPTION_FIELD = "//input[@id='product_description_field']"
PRODUCT_ID = ".//li/div[@class='grid_7 editable subpanel_element']"
PRODUCT_NAME_FIELD = "//input[@id='product_name_field']"
PRODUCT_REMOVE_LINK = "//a[@class='remove_item'][contains(@href, 'products/%s')]"
PRODUCT_SAVE_BUTTON = "//input[@class='fr subpanel_create']"
PROVIDER = "//li[@id='%s']/a"
PROVIDERS = "//div[@id='list']/section/div"
PROVIDER_BY_TITLE = "//div[@title='%s']"
PROVIDER_DESCRIPTION_FIELD = "//input[@id='provider_save']"
PROVIDER_NAME_FIELD = "//input[@id='provider_description']"
PROVIDER_REMOVE_LINK = "//a[contains(@href, 'providers/%s')]"
PROVIDER_SAVE_BUTTON = "//input[@id='provider_save']"
REDHAT_PROVIDERS = 'redhat_providers'
RHEL_PRODUCT = "//tr/td[contains(., '%s')]"
RHEL_PRODUCT_ARCH = "//tr[@id='%s-%s-%s']/td/span"
RHEL_PRODUCT_ID = "//tr[contains(., '%s')]"
RHEL_PRODUCT_REPO = "//tr[contains(@class, 'child-of-%s-%s-%s')]/td[contains(., '%s')]/input"
RHEL_PRODUCT_VERSION = "//tr[@id='%s-%s']/td/span"
SUBSCRIPTIONS = "//table[@id='redhatSubscriptionTable']/tbody/tr"
SUB_HEADER_CONTENT_PROVIDER = "//li[@id='providers']/a"


# Dialogs
YES_BUTTON = "//button[@type='button']"
