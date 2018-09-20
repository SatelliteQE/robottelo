# -*- encoding: utf-8 -*-
"""Implements different locators for UI"""

from selenium.webdriver.common.by import By
from .model import LocatorDict


common_locators = LocatorDict({

    # common locators

    "body": (By.CSS_SELECTOR, "body"),

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
    "alert.success_sub_form": (
        By.XPATH, "//div[contains(@bst-alert, 'success')]"),
    "alert.error_sub_form": (
        By.XPATH, "//div[contains(@bst-alert, 'danger')]"),
    "alert.close": (By.XPATH, "//button[@class='close ng-scope']"),

    "toast.list": (
        By.XPATH,
        ("//div['notifications']//"
         "div[contains(@class, 'toast-notifications-list-pf')]")),
    "toast.alert": (
        By.XPATH,
        ("//div[contains(@class, 'alert') and contains(@class, 'toast-pf')]")),
    "toast.alert.close": (
        By.XPATH,
        ("//div[contains(@class, 'alert') and contains(@class, 'toast-pf')]//"
         "button[contains(@class, 'close')]")),

    "selected_entity": (
        By.XPATH,
        ("//div[@class='ms-selection']/ul[@class='ms-list']"
         "/li[@class='ms-elem-selection ms-selected']")),
    "select_filtered_entity": (
        By.XPATH, "//table//a/span[contains(@data-original-title, '%s')]"),
    "checked_entity": (
        By.XPATH, "//input[@checked='checked']/parent::label"),
    "entity_select": (
        By.XPATH,
        ("//div[@class='ms-selectable']//"
         "li[not(contains(@style, 'display: none'))]/span[contains(.,'%s')]")),
    "entity_deselect": (
        By.XPATH,
        ("//div[@class='ms-selection']//"
         "li[not(contains(@style, 'display: none'))]/span[contains(.,'%s')]")),
    "entity_checkbox": (
        By.XPATH,
        "//label[normalize-space(.)='%s']/input[@type='checkbox']"),
    "entity_select_list": (
        By.XPATH,
        "//ul/li/div[normalize-space(.)='%s']"),
    "entity_select_list_vmware": (
        By.XPATH,
        "//ul/li/div[contains(normalize-space(.),'%s')]"),
    "select_list_search_box": (
        By.XPATH, "//div[@id='select2-drop']//input"),
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
    "table_haserror": (
        By.XPATH,
        "//tr[contains(@class,'has-error')]/td/span"),
    "common_invalid": (
        By.XPATH,
        "//input[@id='name' and contains(@class,'ng-invalid')]"),
    "common_param_error": (
        By.XPATH,
        ("//div[@id='parameters']/span[@class='help-block'"
         "and string-length(text()) > 10]")),

    "search": (By.ID, "search"),
    "clear_search": (By.XPATH, "//a[@class='autocomplete-clear']"),
    "search_no_results": (By.XPATH, "//div[text()='No entries found']"),
    "auto_search": (
        By.XPATH,
        ("//ul[contains(@class, 'ui-autocomplete') or "
         "contains(@template-url, 'autocomplete')]/li/a[contains(., '%s')]")),
    "search_button": (By.XPATH, "//button[contains(@type,'submit')]"),
    "search_dropdown": (
        By.XPATH,
        ("//button[contains(@class, 'dropdown-toggle')]"
         "[@data-toggle='dropdown']")),
    "cancel_form": (By.XPATH, "//a[text()='Cancel']"),
    "submit": (By.NAME, "commit"),
    "select_action_dropdown": (
        By.XPATH,
        "//td[descendant::*[normalize-space(.)='%s']]/"
        "following-sibling::td/div/a[@data-toggle='dropdown']"),
    "delete_button": (
        By.XPATH,
        "//a[contains(@data-confirm, '%s') and @data-method='delete']"),
    "copy_name_input": (By.XPATH, "//input[@ng-model='copyName']"),
    "copy_create_button": (By.XPATH, "//button[@ng-click='copy(copyName)']"),
    "filter": (By.XPATH,
               ("//div[@id='ms-%s_ids']"
                "//input[@class='ms-filter']")),
    "parameter_tab": (By.XPATH, "//a[contains(., 'Parameters')]"),
    "add_parameter": (
        By.XPATH, "//a[contains(text(),'+ Add Parameter')]"),
    "new_parameter_name": (
        By.XPATH, "//input[@placeholder='Name' and not(@value)]"),
    "parameter_value": (
        By.XPATH,
        ("//table[contains(@id, 'parameters')]//tr"
         "/td[input[contains(@id, 'name')][contains(@value, '%s')]]"
         "/following-sibling::td//textarea")),
    "new_parameter_value": (
        By.XPATH, "//textarea[@placeholder='Value' and not(text())]"),
    "parameter_remove": (
        By.XPATH, "//tr/td/input[@value='%s']/following::td/a"),
    "table_column_title": (By.XPATH, "//th[contains(., '%s')]/*"),
    "table_cell_link": (
        By.XPATH,
        "//table[contains(@class, 'table')]"
        "//td[contains(normalize-space(.), '%s')]"
        "/parent::tr"
        "/td[count(//thead//tr/th[.='%s']/preceding-sibling::*)+1]/a"
    ),
    "table_cell_value": (
        By.XPATH,
        "//table[contains(@class, 'table')]"
        "//td[contains(normalize-space(.), '%s')]"
        "/parent::tr"
        "/td[count(//thead//tr/th[.='%s']/preceding-sibling::*)+1]"
    ),
    "table_column_values": (
        By.XPATH,
        "//table//td/parent::tr/td[count(//thead//tr/th[contains(., '%s')]"
        "/preceding-sibling::*)+1]"
    ),
    "table_select_all_checkbox": (
        By.XPATH,
        "//table[contains(@class, 'table')]"
        "//input[@type='checkbox'and @ng-model='selection.allSelected']"
    ),

    "application_logo": (
        By.XPATH, "//img[contains(@alt, 'Header logo')]"),
    "permission_denied": (
        By.XPATH,
        "//h1[contains(.,'Permission denied')]"
    ),

    # Katello Common Locators
    "confirm_remove": (
        By.XPATH, "//button[@ng-click='ok()' or @ng-click='delete()']"),
    "create": (By.XPATH, "//button[contains(@ng-click,'Save')]"),
    "save": (
        By.XPATH, ("//button[contains(@ng-click,'save')"
                   "and not(contains(@class,'ng-hide'))]")),
    "close": (By.XPATH, "//button[@aria-label='Close']"),
    "cancel": (
        By.XPATH,
        "//button[contains(@ng-click,'cancel') and "
        "not(contains(@class,'ng-hide'))][contains(., 'Cancel')]"
    ),
    "name": (By.ID, "name"),
    "label": (By.ID, "label"),
    "description": (By.ID, "description"),
    "kt_select_action_dropdown": (
        By.XPATH,
        ("//button[contains(@ng-click, 'toggleDropdown')]"
         "[descendant::span[text()='Select Action']]")),
    "select_action": (
        By.XPATH,
        "//li/a/span[@class='ng-scope' and contains(., '%s')]"),
    "kt_search": (By.XPATH, "//input[@ng-model='table.searchTerm']"),
    "kt_clear_search": (
        By.XPATH, "//button[contains(@ng-click, 'searchCompleted = false')]"),
    "kt_search_no_results": (
        By.XPATH, "//table//span[@data-block='no-search-results-message']"),
    "kt_search_button": (
        By.XPATH,
        "//button[@ng-click='table.search(table.searchTerm)']"),
    "kt_table_search": (
        By.XPATH, "//input[@ng-model='detailsTable.searchTerm']"),
    "kt_table_search_button": (
        By.XPATH,
        "//button[@ng-click='detailsTable.search(detailsTable.searchTerm)']"),
    "kt_table_cell_value": (
        By.XPATH,
        "//table[@bst-table='table']//td[contains(normalize-space(.), '%s')]"
        "/parent::tr/td[count(//thead//tr/th[.='%s']/preceding-sibling::*)+1]"
    ),
    # Katello common Product and Repo locators
    "gpg_key": (By.ID, "gpg_key_id"),
    "all_values": (By.XPATH,
                   ("//div[contains(@class,'active')]//input[@type='checkbox'"
                    " and contains(@name, '%s')]")),
    "all_values_selection": (
        By.XPATH,
        ("//div[@class='ms-selection']//ul[@class='ms-list']/li"
         "/span[contains(.,'%s')]/..")),
    "usage_limit": (
        By.XPATH,
        "//input[contains(@ng-model, 'max')"
        "and contains(@ng-model, 'hosts')]"),
    "usage_limit_checkbox": (
        By.XPATH,
        "//input[contains(@ng-model, 'unlimited')"
        "and contains(@ng-model, 'hosts')]"),
    "invalid_limit": (
        By.XPATH,
        "//input[contains(@id, 'max') and contains(@class, 'ng-invalid')]"),
    "modal_background": (
        By.XPATH,
        "//*[@class='modal-backdrop fade in']",
    ),
    "select_repo": (By.XPATH, "//select[@ng-model='repository']"),
    "table_per_page": (
        By.XPATH, "//select[@ng-model='table.params.per_page']"),

    # ace editor
    "ace.input": (By.XPATH, "//label[contains(., 'Input') and"
                            " contains(@class, 'btn')]"),
    "ace.diff": (By.XPATH, "//label[contains(., 'Diff') and"
                           " contains(@class, 'btn')]"),
    "ace.preview": (By.XPATH, "//label[contains(., 'Preview') and"
                              " contains(@class, 'btn')]"),

    # 'Run Job' button that is accessible from Jobs and Hosts pages
    "run_job": (By.XPATH, "//a[@data-id='aid_job_invocations_new']"),

    # org environment
    "org_environment_info": (
        By.XPATH,
        '//div[@bst-alert="info"]//span[contains(., '
        '"Access to repositories is unrestricted in this organization.")]'),
})
