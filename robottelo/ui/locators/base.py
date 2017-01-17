# -*- encoding: utf-8 -*-
"""Implements different locators for UI"""

from selenium.webdriver.common.by import By
from .model import LocatorDict


locators = LocatorDict({

    # Bookmarks
    "bookmark.select_name": (
        By.XPATH,
        ("//td[following-sibling::td[text()='%s']]"
         "/a[span[contains(.,'%s')]]")),
    "bookmark.new": (
        By.XPATH,
        ("//ul[contains(@class, 'dropdown-menu')]"
         "[contains(@class, 'pull-right')]/li"
         "/a[contains(@ng-click, 'add()') or contains(@id, 'bookmark')]")),
    "bookmark.name": (By.XPATH, "//input[@id='name' or @id='bookmark_name']"),
    "bookmark.query": (
        By.XPATH,
        ("//*[(@id='query' and @name='query') or "  # can be input or textarea
         "(@id='bookmark_query' and @name='bookmark[query]')]")),
    "bookmark.public": (
        By.XPATH,
        "//input[@type='checkbox'][@id='public' or @id='bookmark_public']"),
    "bookmark.create": (
        By.XPATH,
        ("//button[(contains(@class, 'btn-primary') and @type='button') or "
         "(contains(@class, 'btn-danger') and @ng-click='ok()')]")),
    "bookmark.select_long_name": (
        By.XPATH,
        ("//td[following-sibling::td[text()='%s']]"
         "/a[span[@data-original-title='%s']]")),
    "bookmark.delete": (
        By.XPATH,
        "//a[@class='delete' and contains(@data-confirm, '%s')]"),

    # Locations
    "location.new": (By.XPATH, "//a[@data-id='aid_locations_new']"),
    "location.parent": (
        By.XPATH,
        ("//div[contains(@id, 'location_parent_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "location.name": (By.ID, "location_name"),
    "location.assign_all": (
        By.XPATH, "//a[contains(@data-id,'assign_all_hosts')]"),
    "location.proceed_to_edit": (
        By.XPATH,
        "//a[@class='btn btn-default' and contains(@href, '/edit')]"),
    "location.select_name": (
        By.XPATH,
        "//td/a[contains(@href,'locations')]/span[contains(.,'%s')]"),
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
        "//td/a[contains(@href,'organizations')]/span[contains(.,'%s')]"),
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
    "trend.type": (
        By.XPATH,
        ("//div[contains(@id, 'trend_trendable_type')]/a"
         "/span[contains(@class, 'arrow')]")),
    "trend.trendable": (
        By.XPATH,
        ("//div[contains(@id, 'trend_trendable_id')]/a"
         "/span[contains(@class, 'arrow')]")),
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

    # Jobs invocation

    "job_invocation.select": (
        By.XPATH,
        ("//a[contains(@href, 'job_invocations')"
            "and normalize-space(.)='%s']")),
    "job_invocation.job_category": (
        By.XPATH,
        ("//div[contains(@id, 'job_category')]/a"
         "/span[contains(@class, 'arrow')]")),
    "job_invocation.job_template": (
        By.XPATH,
        ("//div[contains(@id, 'providers_SSH_job_template_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "job_invocation.bookmark": (
        By.XPATH,
        ("//div[contains(@id, 'targeting_bookmark_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "job_invocation.query": (
        By.XPATH, "//textarea[@id='targeting_search_query']"),
    "job_invocation.command": (By.XPATH, "//textarea[@id='command']"),
    "job_invocation.errata": (By.XPATH, "//textarea[@id='errata']"),
    "job_invocation.package": (By.XPATH, "//textarea[@id='package']"),
    "job_invocation.puppet_options": (
        By.XPATH, "//textarea[@id='puppet_options']"),
    "job_invocation.service": (By.XPATH, "//textarea[@id='service']"),
    "job_invocation.action": (
        By.XPATH,
        "//div[contains(@id, 'action')]/a/span[contains(@class, 'arrow')]"),
    "job_invocation.schedule_type": (
        By.XPATH,
        "//input[contains(@id, 'triggering_mode') and @value='%s']"),
    "job_invocation.schedule.start_at": (
        By.XPATH, "//input[@id='triggering_start_at_raw']"),
    "job_invocation.schedule.start_before": (
        By.XPATH, "//input[@id='triggering_start_before_raw']"),
    "job_invocation.schedule.repeats": (
        By.XPATH,
        ("//div[contains(@id, 'input_type_selector')]/a"
         "/span[contains(@class, 'arrow')]")),
    "job_invocation.schedule.repeats_n_times": (
        By.XPATH, "//input[@id='triggering_max_iteration']"),
    "job_invocation.title": (
        By.XPATH, "//div[@id='content']/div/h1"),
    "job_invocation.refresh": (By.XPATH, "//a[@*='Refresh this page']"),
    "job_invocation.rerun": (By.XPATH, "//a[@*='Rerun the job']"),
    "job_invocation.rerun_failed": (
        By.XPATH, "//a[@*='Rerun on failed hosts']"),
    "job_invocation.job_task": (
        By.XPATH, "//a[@*='See the last task details']"),
    "job_invocation.cancel": (By.XPATH, "//a[@*='Try to cancel the job']"),
    "job_invocation.status": (
        By.XPATH, "//div[@id='status' and @data-title='%s']"),


    # Operating system (OS)
    "operatingsys.new": (
        By.XPATH, "//a[contains(@href, '/operatingsystems/new')]"),
    "operatingsys.name": (By.ID, "operatingsystem_name"),
    "operatingsys.major_version": (By.ID, "operatingsystem_major"),
    "operatingsys.minor_version": (By.ID, "operatingsystem_minor"),
    "operatingsys.description": (By.ID, "operatingsystem_description"),
    "operatingsys.family": (
        By.XPATH,
        ("//div[contains(@id, 'operatingsystem_family')]/a"
         "/span[contains(@class, 'arrow')]")),
    "operatingsys.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "operatingsys.operatingsys_name": (By.XPATH, "//a[contains(., '%s')]"),
    "operatingsys.template": (
        By.XPATH,
        ("//div[contains(@id, 'operatingsystem_os_default_templates_attributes"
         "_0_provisioning_template_id')]/a/span[contains(@class, 'arrow')]")),
    "operatingsys.fetch_family": (
        By.XPATH,
        ("//div[contains(@id, 'operatingsystem_family')]/a"
         "/span[contains(@class, 'chosen')]")),
    "operatingsys.fetch_template": (
        By.XPATH,
        ("//div[contains(@id, 'operatingsystem_os_default_templates_attributes"
         "_0_provisioning_template_id')]/a/span[contains(@class, 'chosen')]")),

    # Compute Profile
    "profile.new": (
        By.XPATH, "//a[contains(@href, '/compute_profiles/new')]"),
    "profile.name": (By.ID, "compute_profile_name"),
    "profile.select_name": (
        By.XPATH,
        ("//a[contains(@href,'compute_profiles')"
            "and normalize-space(.)='%s']")),
    "profile.dropdown": (
        By.XPATH,
        ("//td/a[contains(., '%s')]"
         "/following::td/div/a[@data-toggle='dropdown']")),
    "profile.rename": (
        By.XPATH,
        ("//td/a[contains(., '%s')]"
         "/following::td/div/span/a[text()='Rename']")),
    "profile.delete": (
        By.XPATH,
        ("//td/a[contains(., '%s')]"
         "/following::td/div/ul/li/a[@class='delete']")),
    "profile.resource_name": (
        By.XPATH,
        ("//a[contains(@href,'compute_resources')"
            "and normalize-space(.)='%s']")),
    "profile.resource_form": (By.XPATH, "//form[@id='new_compute_attribute']"),

    # Compute Resource
    "resource.new": (
        By.XPATH, "//a[contains(@href, '/compute_resources/new')]"),
    "resource.name": (By.ID, "compute_resource_name"),
    "resource.provider_type": (By.ID, "s2id_compute_resource_provider"),
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
    "resource.datacenter": (
        By.XPATH,
        ("//div[contains(@id, 's2id_compute_resource_uuid')]"
         "/a/span[contains(@class, 'arrow')]")),
    "resource.datacenter_vsphere": (
        By.XPATH, "//select[@id='compute_resource_datacenter']"),
    "resource.datacenter.button": (
        By.XPATH,
        "//a[contains(@data-url, '/compute_resources/test_connection')]"),
    "resource.datacenter_vsphere.button": (
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
    "resource.filter_containers": (
        By.XPATH, "//div[contains(@id, 'filter')]//input[@type='text']"),
    "resource.select_container": (
        By.XPATH,
        ("//a[contains(@href, 'compute_resources/') and "
         "contains(@href, 'vms/') and contains(., '%s')]")),
    "resource.get_by_name": (
        By.XPATH,
        "//a[not(contains(@href, 'search')) and contains(@href, '%s')]"),

    # Locators under compute-resources vm tab.
    "resource.search_filter": (
        By.XPATH,
        "//div[@class='tab-content']/div[contains(@class, 'active')]//"
        "input[contains(@aria-controls, 'DataTables_Table')]"),
    "resource.power_status": (
        By.XPATH,
        ".//*[@id='DataTables_Table_0']/tbody/tr/td[4]/span"),
    "resource.vm_power_button": (
        By.XPATH,
        "//a[contains(@href,'power')]"),
    "resource.vm_delete_button_dropdown": (
        By.XPATH,
        ("//a[contains(@href,'power') and contains(@data-confirm, '%s')]"
         "/../a[@data-toggle='dropdown']")),
    "resource.vm_delete_button": (
        By.XPATH,
        ("//a[contains(@href,'power') and contains(@data-confirm, '%s')]"
         "/../ul/li/a[contains(.,'Delete')]")),
    "resource.vm_list": (
        By.XPATH,
        "//div[@id='vms']//tbody/tr/td/a"),

    # Locators under compute-resources image tab.
    "resource.image_add": (By.XPATH, "//a[.='New Image']"),
    "resource.image_name": (By.XPATH, "//input[@id='image_name']"),
    "resource.image_operatingsystem": (
        By.XPATH, "//div[@id='s2id_image_operatingsystem_id']"
        "/a/span[contains(@class, 'arrow')]"),
    "resource.image_architecture": (
        By.XPATH, "//div[@id='s2id_image_architecture_id']"
        "/a/span[contains(@class, 'arrow')]"),
    "resource.image_username": (By.ID, "image_username"),
    "resource.image_password": (By.ID, "image_password"),
    "resource.image_uuid": (
        By.XPATH,
        "//div[@id='s2id_image_uuid']/a/span[contains(@class, 'arrow')]"),
    "resource.image_submit": (
        By.XPATH, "//input[@data-id='aid_create_image']"),
    "resource.image_list": (
        By.XPATH,
        "//div[@id='images_list']//tbody/tr/td[1]"),

    # Content Hosts
    "contenthost.select_name": (
        By.XPATH,
        "//a[contains(@href, 'content_hosts') and contains(.,'%s')]"),
    "contenthost.select_errata_counts": (
        By.XPATH,
        ("//a[contains(@href, 'content_hosts') and contains(.,'%s')]/../"
         "following-sibling::td/a[contains(@href, 'errata')]//"
         "span[@class='errata-count']")),
    "contenthost.details_page_errata_counts": (
        By.XPATH, "//a[contains(@href, 'errata') and @class='ng-binding']"),
    "contenthost.errata_counts_icon": (By.XPATH, "i"),
    "contenthost.edit_name": (
        By.XPATH, "//form[@bst-edit-text='host.name']//div/span/i"),
    "contenthost.edit_name_text": (
        By.XPATH,
        "//form[@bst-edit-text='host.name']/div/input"),
    "contenthost.save_name": (
        By.XPATH,
        "//form[@bst-edit-text='host.name']//button[@ng-click='save()']"),
    "contenthost.unregister": (
        By.XPATH, "//button[@ng-disabled='host.deleting']"),
    "contenthost.confirm_deletion": (
        By.XPATH,
        ("//input[@type='radio' and @ng-model='host.unregisterDelete' and "
         "@ng-value='true']")),
    "contenthost.subscription_active": (
        By.XPATH,
        ("//td[a[contains(@href, 'content_hosts') and contains(.,'%s')]]"
         "/following-sibling::td/span[contains(@ng-class, "
         "'host.subscription_status') and  contains(@class, 'green')]")),
    "contenthost.subscription_not_active": (
        By.XPATH,
        ("//td[a[contains(@href, 'content_hosts') and contains(.,'%s')]]"
         "/following-sibling::td/span[contains(@ng-class, "
         "'host.subscription_status') and  contains(@class, 'red')]")),
    "contenthost.subscription_select": (
        By.XPATH,
        ("//tr[//a[contains(@href,'info') and contains(.,'%s')]]"
         "/following-sibling::tr[1]/td/input[@type='checkbox']")),
    "contenthost.errata_select": (
        By.XPATH,
        ("//tr[td/a[@ng-click='transitionToErratum(erratum)' and "
         "contains(.,'%s')]]/td/input[@type='checkbox']")),
    "contenthost.errata_environment_select": (
        By.XPATH,
        ("//select[@ng-model='selectedErrataOption']/"
         "option[contains(text(), '%s')]")),
    "contenthost.errata_apply": (
        By.XPATH,
        ("//button[contains(@ng-click, 'openModal()') and "
         "contains(@ng-hide, 'edit_hosts')]")),
    "contenthost.confirm_errata": (By.XPATH, "//button[@ng-click='ok()']"),
    "contenthost.add_selected": (
        By.XPATH, "//button[contains(@ng-click, 'addSelected()')]"),
    "contenthost.remove_selected": (
        By.XPATH, "//button[contains(@ng-click, 'removeSelected()')]"),
    "contenthost.remote_actions": (
        By.XPATH, "//select[@name='remote_action']"),
    "contenthost.package_name_input": (
        By.XPATH,
        "//input[@type='text' and contains(@ng-model, 'packageAction')]"),
    "contenthost.perform_remote_action": (
        By.XPATH,
        ("//form[@ng-submit='performPackageAction()']"
         "//button[contains(@class, 'ng-scope')]")),
    "contenthost.remote_action_finished": (
        By.XPATH,
        ("//div[contains(@class, 'progress') and "
         "@value='task.progressbar.value' and "
         "div[contains(@style, '100%')]]")),
    "contenthost.package_search_box": (
        By.XPATH, "//input[@ng-model='detailsTable.searchTerm']"),
    "contenthost.package_search_button": (
        By.XPATH, "//button[contains(@ng-click, 'detailsTable.search')]"),
    "contenthost.package_search_name": (
        By.XPATH,
        ("//tr[@class='ng-scope' and @row-select='package']"
         "/td[contains(@class, 'ng-scope') and contains(., '%s')]")),

    # Content Host - Bulk Actions

    # %s action names: 'update all', 'install', 'update', 'remove'
    "contenthost.bulk_actions.via_katello_agent": (
        By.XPATH,
        ("//a[contains(@ng-click, \"performViaKatelloAgent"
         "('%s', content)\")]")),
    "contenthost.bulk_actions.via_remote_execution": (
        By.XPATH,
        ("//a[contains(@ng-click, \"performViaRemoteExecution"
         "('%s', false)\")]")),
    "contenthost.bulk_actions.via_remote_execution_custom": (
        By.XPATH,
        ("//a[contains(@ng-click, \"performViaRemoteExecution"
         "('%s', true)\")]")),

    # errata
    "contenthost.bulk_actions.errata.via_katello_agent": (
        By.XPATH,
        "//a[contains(@ng-click, 'installErrataViaKatelloAgent()')]"),
    "contenthost.bulk_actions.errata.via_remote_execution": (
        By.XPATH,
        "//a[contains(@ng-click, 'installErrataViaRemoteExecution(false)')]"),
    "contenthost.bulk_actions.errata.via_remote_execution_custom": (
        By.XPATH,
        "//a[contains(@ng-click, 'installErrataViaRemoteExecution(false)')]"),

    "contenthost.bulk_actions.package_type": (By.ID, "package"),
    "contenthost.bulk_actions.package_group_type": (By.ID, "package_group"),
    "contenthost.bulk_actions.package_name_input": (
        By.XPATH,
        "//input[@type='text' and contains(@ng-model, 'content.content')]"),

    "contenthost.bulk_actions.action_dropdown": (
        By.XPATH,
        "%s/../../../button[contains(@data-toggle,'dropdown')]"),

    "contenthost.bulk_actions.remote_action_scheduled": (
        By.XPATH, '//div[@bst-alert="success"]'),

    # Hosts

    # Default tab (Host)
    "host.new": (By.XPATH, "//a[contains(@href, '/hosts/new') and "
                           "contains(@class, 'btn')]"),
    "host.clone": (
        By.XPATH, "//a[contains(@href,'%s') and contains(.,'Clone')]"),
    "host.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "host.dropdown": (
        By.XPATH,
        ("//a[contains(@href,'%s')]"
         "/../../a[contains(@data-toggle,'dropdown')]")),
    "host.edit": (By.XPATH,
                  "//a[@class='btn btn-default' and contains(@href,'edit')]"),
    "host.select_name": (
        By.XPATH,
        ("//input[contains(@id,'host_ids')]"
         "/../../td[@class='ellipsis']/a[contains(@href,'%s')]")),
    "host.yaml_button": (By.XPATH, "//a[text()='YAML' and "
                                   "contains(@class, 'btn')]"),
    "host.yaml_output": (By.XPATH, "//pre"),
    "host.name": (By.ID, "host_name"),
    "host.organization": (
        By.XPATH,
        ("//div[contains(@id, 'host_organization_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.location": (
        By.XPATH,
        ("//div[contains(@id, 'host_location_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.host_group": (
        By.XPATH,
        ("//div[contains(@id, 'host_hostgroup_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.deploy_on": (
        By.XPATH,
        ("//div[contains(@id, 'host_compute_resource_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.lifecycle_environment": (
        By.XPATH,
        ("//div[contains(@id, 'host_lifecycle_environment_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.content_view": (
        By.XPATH,
        ("//div[contains(@id, 'host_content_view_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.puppet_environment": (
        By.XPATH,
        ("//div[contains(@id, 'host_environment_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.reset_puppet_environment": (By.ID, "reset_puppet_environment"),
    "host.content_source": (
        By.XPATH,
        ("//div[contains(@id, 'host_content_source')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.puppet_ca": (
        By.XPATH,
        ("//div[contains(@id, 'host_puppet_ca_proxy')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.puppet_master": (
        By.XPATH,
        ("//div[contains(@id, 'host_puppet_proxy')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.openscap_proxy": (
        By.XPATH,
        ("//div[contains(@id, 'host_openscap_proxy')]/a"
         "/span[contains(@class, 'arrow')]")),

    # host.puppet_classes
    "host.select_puppetmodule": (
        By.XPATH, "//a[contains(.,'%s')]/span[contains(@class, 'glyphicon')]"),
    "host.select_puppetclass": (
        By.XPATH,
        ("//span[contains(.,'%s')]"
         "/a[not(contains(@data-original-title, '::'))]")),

    # host.interface
    "host.edit_default_interface": (
        By.XPATH,
        "//table[@id='interfaceList']/tbody/tr[1]/td"
        "/button[contains(@class, 'showModal')]"),
    "host.interface_type": (
        By.XPATH,
        "//div[@id='interfaceModal']//select[contains(@id, '_type')]"),
    "host.interface_mac_address": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_mac')]"),
    "host.interface_device_identifier": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_identifier')]"),
    "host.interface_dns_name": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_name')]"),
    "host.interface_domain": (
        By.XPATH,
        "//div[@id='interfaceModal']//select[contains(@id, '_domain_id')]"),
    "host.interface_subnet": (
        By.XPATH,
        "//div[@id='interfaceModal']//select[contains(@id, '_subnet_id')]"),
    "host.interface_ip_address": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_ip')]"),
    "host.interface_managed": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_managed')]"),
    "host.interface_primary": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_primary')]"),
    "host.interface_provision": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_provision')]"),
    "host.interface_remote_execution": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_execution')]"),
    "host.interface_virtual_nic": (
        By.XPATH,
        "//div[@id='interfaceModal']//input[contains(@id, '_virtual')]"),
    "host.interface_network_type": (
        By.XPATH,
        ("//div[@id='interfaceModal']"
         "//select[contains(@id, '_compute_attributes_type')]")),
    "host.interface_network": (
        By.XPATH,
        ("//div[@id='interfaceModal']"
         "//*[contains(@id, '_compute_attributes_bridge')]")),
    "host.nic_type": (
        By.XPATH,
        ("//div[@id='interfaceModal']"
         "//select[contains(@id, '_compute_attributes_model')]")),
    "host.save_interface": (
        By.XPATH,
        "//button[contains(@onclick, 'save_interface_modal()')]"),

    # host.os
    "host.architecture": (
        By.XPATH,
        ("//div[contains(@id, 'host_architecture_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.operating_system": (
        By.XPATH,
        ("//div[contains(@id, 'host_operatingsystem_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.build_mode": (By.ID, "host_build"),
    "host.media": (
        By.XPATH,
        ("//div[contains(@id, 'host_medium_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.partition_table": (
        By.XPATH,
        ("//div[contains(@id, 'host_ptable_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.custom_partition_table": (By.ID, "host_disk"),
    "host.root_password": (By.ID, "host_root_pass"),
    "host.provisioning_templates": (
        By.XPATH,
        "//div[contains(.,'Provisioning Templates')]/../div/a[@class='btn']"),

    # host.parameters
    "host.add_new_host_parameter": (
        By.XPATH, "//a[contains(., 'Add Parameter')]"),
    "host.host_parameter_name": (
        By.XPATH,
        "(//input[contains(@id, '_name') "
        "and contains(@name, 'parameters')])[%i]"),
    "host.host_parameter_value": (
        By.XPATH,
        "(//textarea[contains(@id, '_value') "
        "and contains(@name, 'parameters')])[%i]"),
    "host.smart_variable_value": (
        By.XPATH,
        "//*[ancestor::tr//td[contains(., '%s')] and @data-property='value']"),
    "host.smart_variable_override": (
        By.XPATH,
        "//a[ancestor::tr//td[contains(., '%s')] and @data-tag='override']"
    ),
    "host.smart_variable_unhide": (
        By.XPATH,
        "//a[ancestor::tr//td[contains(., '%s')] and "
        "@data-original-title='Unhide this value']"
    ),
    "host.smart_variable_hide": (
        By.XPATH,
        "//a[ancestor::tr//td[contains(., '%s')] and "
        "@data-original-title='Hide this value']"
    ),
    "host.smart_variable_puppet_class": (
        By.XPATH, "//td[contains(., '%s')]//ancestor::tbody/tr[1]/td[1]"),
    "host.override_error": (By.CSS_SELECTOR, "input:invalid[value='%s']"),

    # host.vm (NOTE:- visible only when selecting a compute resource)
    "host.cpus": (
        By.XPATH,
        ("//div[contains(@id, 'host_compute_attributes_cpus')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.memory": (
        By.XPATH,
        ("//div[contains(@id, 'host_compute_attributes_memory')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.vm_start": (By.ID, "host_compute_attributes_start"),
    "host.vm_addstorage": (
        By.XPATH, "//fieldset[@id='storage_volumes']/a"),

    # host.additional_information
    "host.owned_by": (
        By.XPATH,
        ("//div[contains(@id, 'host_is_owned_by')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.enabled": (By.ID, "host_enabled"),
    "host.hardware_model": (
        By.XPATH,
        ("//div[contains(@id, 'host_model_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "host.comment": (By.ID, "host_comment"),

    # Host 'Select Action'/'Bulk Action.'
    "host.checkbox": (
        By.XPATH,
        "//a[contains(@href, '%s')]/../../td/input[@type='checkbox']"),
    "host.select_action_list": (
        By.XPATH,
        "//div[@id='submit_multiple']/a[contains(@class, 'dropdown-toggle')]"),
    "host.select_action": (By.XPATH, "//li/a[text()='%s']"),
    "host.fix_mismatch": (By.ID, "organization_optimistic_import_yes"),
    "host.select_org": (By.ID, "organization_id"),
    "host.bulk_submit": (
        By.XPATH,
        ("//form[contains(@action, 'multiple')]/../../../"
         "div/button[contains(@class,'primary')]")),

    # Provisions

    # provision.primary
    "provision.template_new": (
        By.XPATH, "//a[contains(@href, '/provisioning_templates/new')]"),
    "provision.template_select": (
        By.XPATH,
        ("//a[contains(@href, 'provisioning_templates')"
            "and normalize-space(.)='%s']")),
    "provision.template_name": (
        By.ID, "provisioning_template_name"),
    "provision.audit_comment": (
        By.ID, "provisioning_template_audit_comment"),
    "provision.template_template": (
        By.XPATH, "//input[@id='template_file']"),
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
        By.XPATH,
        ("//div[contains(@id, 'provisioning_template_template_kind_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "provision.template_snippet": (
        By.ID, "provisioning_template_snippet"),

    # provision.association
    "provision.select_os": (
        By.XPATH, "//li/span[contains(., '%s')]"),
    "provision.associate_os": (
        By.XPATH,
        ("//label[@class='operatingsystem'"
            "and contains(., '%s')]/input[@type='checkbox']")),

    # Job templates
    "job.template_new": (
        By.XPATH, "//a[contains(@href, '/job_templates/new')]"),
    "job.template_select": (
        By.XPATH,
        ("//a[contains(@href, 'job_templates')"
            "and normalize-space(.)='%s']")),
    "job.template_name": (By.ID, "job_template_name"),
    "job.template_file": (By.XPATH, "//input[@id='template_file']"),
    "job.template_input": (By.XPATH, "//div[contains(@class, 'ace_editor')]"),
    "job.template_default": (By.XPATH, "//input[@id='job_template_default']"),
    "job.audit_comment": (
        By.XPATH, "//input[@id='job_template_audit_comment']"),
    "job.job_category": (
        By.XPATH, "//input[@name='job_template[job_category]']"),
    "job.description_format": (
        By.XPATH, "//input[@id='job_template_description_format']"),
    "job.provider_type": (
        By.XPATH,
        ("//div[contains(@id, 'job_template_provider_type')]/a"
         "/span[contains(@class, 'arrow')]")),
    "job.effective_user_value": (
        By.XPATH,
        "//input[@id='job_template_effective_user_attributes_value']"),
    "job.current_user": (
        By.XPATH,
        "//input[@id='job_template_effective_user_attributes_current_user']"),
    "job.effective_user_overridable": (
        By.XPATH,
        "//input[@id='job_template_effective_user_attributes_overridable']"),
    "job.template_snippet": (By.XPATH, "//input[@id='job_template_snippet']"),
    "job.template_delete": (
        By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "job.template_dropdown": (
        By.XPATH,
        ("//td/a[normalize-space(.)='%s']"
         "/following::td/div/a[@data-toggle='dropdown']")),
    "job.template_clone": (
        By.XPATH, "//a[contains(@href,'clone_template')]"),
    "job.add_new_input": (By.XPATH, "//a[text()='+ Add Input']"),
    "job.input_name": (
        By.XPATH, "(//input[contains(@name, '[template_inputs_attributes]') "
                  "and contains(@name, '[name]')])[last()]"),
    "job.input_required": (
        By.XPATH, "(//input[contains(@name, '[template_inputs_attributes]') "
                  "and contains(@name, '[required]')])[last()]"),
    "job.input_input_type": (
        By.XPATH, "(//select[contains(@name, '[template_inputs_attributes]') "
                  "and contains(@name, '[input_type]')])[last()]"),
    "job.input_advanced": (
        By.XPATH, "(//input[contains(@name, '[template_inputs_attributes]') "
                  "and contains(@name, '[advanced]')])[last()]"),
    "job.input_options": (
        By.XPATH, "(//textarea[contains(@name, '[template_inputs_attributes]')"
                  " and contains(@name, '[options]')])[last()]"),
    "job.input_description": (
        By.XPATH, "(//textarea[contains(@name, '[template_inputs_attributes]')"
                  " and contains(@name, '[description]')])[last()]"),


    # Hostgroups

    "hostgroups.new": (By.XPATH, "//a[contains(@href, '/hostgroups/new')]"),
    "hostgroups.name": (By.ID, "hostgroup_name"),
    "hostgroups.environment": (
        By.XPATH,
        ("//div[contains(@id, 'hostgroup_lifecycle_environment')]/a"
         "/span[contains(@class, 'arrow')]")),
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
        By.XPATH,
        ("//div[contains(@id, 'hostgroup_content_source')]/a"
         "/span[contains(@class, 'arrow')]")),
    "hostgroups.puppet_ca": (
        By.XPATH,
        ("//div[contains(@id, 'hostgroup_puppet_ca_proxy_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "hostgroups.puppet_master": (
        By.XPATH,
        ("//div[contains(@id, 'hostgroup_puppet_proxy')]/a"
         "/span[contains(@class, 'arrow')]")),
    "hostgroups.oscap_capsule": (
        By.XPATH,
        ("//div[contains(@id, 'hostgroup_openscap_proxy_id')]/a"
         "/span[contains(@class, 'arrow')]")),

    # Users

    # Users.primary
    "users.new": (By.XPATH, "//a[contains(@href, '/users/new')]"),
    "users.username": (By.ID, "user_login"),
    "users.firstname": (By.ID, "user_firstname"),
    "users.lastname": (By.ID, "user_lastname"),
    "users.email": (By.ID, "user_mail"),
    "users.language": (
        By.XPATH,
        ("//div[contains(@id, 'user_locale')]/a"
         "/span[contains(@class, 'chosen')]")),
    "users.language_dropdown": (
        By.XPATH,
        ("//div[contains(@id, 'user_locale')]/a"
         "/span[contains(@class, 'arrow')]")),
    "users.timezone": (
        By.XPATH,
        ("//div[contains(@id, 'user_timezone')]/a"
         "/span[contains(@class, 'chosen')]")),
    "users.timezone_dropdown": (
        By.XPATH,
        ("//div[contains(@id, 'user_timezone')]/a"
         "/span[contains(@class, 'arrow')]")),
    "users.selected_lang": (
        By.XPATH, ("//select[@id='user_locale']"
                   "/option[@selected='selected']")),
    "users.authorized_by": (
        By.XPATH,
        ("//div[contains(@id, 'user_auth_source_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "users.password": (By.ID, "user_password"),
    "users.password_confirmation": (By.ID, "user_password_confirmation"),
    "users.user": (By.XPATH, "//a[contains(., '%s')]"),
    "users.table_value": (By.XPATH, "//td[contains(., '%s')]"),
    "users.default_org": (
        By.XPATH,
        ("//div[contains(@id, 'user_default_organization_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "users.default_org_value": (
        By.XPATH,
        ("//div[contains(@id, 'user_default_organization_id')]/a"
         "/span[contains(@class, 'chosen')]")),
    "users.default_loc": (
        By.XPATH,
        ("//div[contains(@id, 'user_default_location_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "users.default_loc_value": (
        By.XPATH,
        ("//div[contains(@id, 'user_default_location_id')]/a"
         "/span[contains(@id, 'chosen')]")),
    "users.delete": (
        By.XPATH,
        ("//td/a[contains(., '%s')]"
         "/following::td/span/a[@class='delete']")),

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
        ("//div[contains(@id, 'auth_source_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "usergroups.ext_refresh": (
        By.XPATH,
        ("//td[contains(.,'%s')]/../td/"
         "a[contains(@data-id, 'refresh')]")),
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
        By.XPATH,
        ("//div[contains(@id, 'filter_resource_type')]/a"
         "/span[contains(@class, 'arrow')]")),
    "roles.override": (By.ID, "override_taxonomy_checkbox"),
    "roles.unlimited": (By.ID, "filter_unlimited"),
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
    "medium.os_family": (
        By.XPATH,
        ("//div[contains(@id, 'medium_os_family')]/a"
         "/span[contains(@class, 'arrow')]")),
    "medium.delete": (By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "medium.medium_name": (By.XPATH, "//a[contains(., '%s')]"),

    # Domain
    "domain.new": (By.XPATH, "//a[contains(@href, '/domains/new')]"),
    "domain.name": (By.ID, "domain_name"),
    "domain.description": (By.ID, "domain_fullname"),
    "domain.dns_proxy": (
        By.XPATH,
        ("//div[contains(@id, 'domain_dns_id')]/a"
         "/span[contains(@class, 'arrow')]")),
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
    "ptable.default_template": (By.XPATH, "//input[@id='ptable_default']"),
    "ptable.snippet": (By.XPATH, "//input[@id='ptable_snippet']"),
    "ptable.layout_template": (By.XPATH, "//input[@id='template_file']"),
    "ptable.audit_comment": (
        By.XPATH, "//textarea[@id='ptable_audit_comment']"),
    "ptable.os_family": (
        By.XPATH,
        ("//div[contains(@id, 'ptable_os_family')]/a"
         "/span[contains(@class, 'arrow')]")),
    "ptable.delete": (By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "ptable.ptable_name": (By.XPATH, "//a[normalize-space(.)='%s']"),
    "ptable.dropdown": (
        By.XPATH,
        ("//td/a[normalize-space(.)='%s']"
         "/following::td/div/a[@data-toggle='dropdown']")),

    # Subnet Page
    "subnet.new": (By.XPATH, "//a[contains(@href, '/subnets/new')]"),
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
    "prd.remove": (By.XPATH, "//button[contains(., 'Remove Product')]"),
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
                   "//i[contains(@class,'fa-edit')]")),
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
        By.XPATH, "//input[contains(@placeholder,'Filter by name')]"),
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
    "repo.search": (By.XPATH, "//input[@ng-model='detailsTable.searchTerm']"),
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
    "repo.discover_url": (By.XPATH, "//input[@ng-model='discovery.url']"),
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
    "repo.download_policy_edit": (
        By.XPATH, "//form[@selector='repository.download_policy']//i"),
    "repo.download_policy_update": (
        By.XPATH, "//form[@selector='repository.download_policy']/div/select"),
    "repo.download_policy": (By.ID, "download_policy"),
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
    "repo.fetch_download_policy": (
        By.XPATH, ("//form[@selector='repository.download_policy']"
                   "/div[@class='bst-edit']/div/span[2]")),
    "repo.fetch_checksum": (
        By.XPATH, ("//form[@selector='repository.checksum_type']"
                   "/div/div/span[contains(@class,'value')]")),
    "repo.fetch_upstream": (
        By.XPATH, ("//form[@bst-edit-text='repository.docker_upstream_name']"
                   "/div[@class='bst-edit']/div/span[2]")),
    "repo.fetch_packages": (
        By.XPATH, "//td[span[text()='Packages']]/following-sibling::td",
    ),
    "repo.fetch_errata": (
        By.XPATH, "//td[span[text()='Errata']]/following-sibling::td",
    ),
    "repo.fetch_package_groups": (
        By.XPATH, "//td[span[text()='Package Groups']]/following-sibling::td",
    ),
    "repo.fetch_puppet_modules": (
        By.XPATH, "//td[span[text()='Puppet Modules']]/following-sibling::td",
    ),
    "repo.result_spinner": (
        By.XPATH,
        "//i[@ng-show='task.pending' and contains(@class, 'icon-spinner')]"),
    "repo.manage_content": (
        By.XPATH,
        "//button[contains(@ui-sref,"
        " 'products.details.repositories.manage-content')"
        " and not(contains(@class, 'ng-hide'))]"),
    "repo.content.packages": (By.XPATH, "//tr[@row-select='package']"),
    "repo.content.puppet_modules": (By.XPATH, "//tr[@row-select='item']"),
    "repo.upload.file_path": (By.XPATH, ("//input[@name='content[]']")),
    "repo.upload": (By.XPATH, ("//button[@upload-submit]")),
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
        "//div[@bst-edit-custom='activationKey.max_hosts']//div/span/i"),
    "ak.save_limit": (
        By.XPATH,
        ("//div[@bst-edit-custom='activationKey.max_hosts']"
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
        By.XPATH, "//tr/td/a[contains(., '%s')]"),
    "ak.selected_cv": (
        By.XPATH,
        ("//form[@bst-edit-select='activationKey.content_view.name']"
         "//div[@class='bst-edit']/div/span[2]")),
    "ak.content_hosts": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'content-hosts')]"),
    "ak.content_host_name": (
        By.XPATH,
        "//tr[@ng-controller='ContentHostStatusController']/td/a"),
    "ak.content_host_select": (
        By.XPATH,
        ("//tr[@ng-controller='ContentHostStatusController']/td"
         "/a[contains(., '%s')]")),
    "ak.prd_content.edit_repo": (
        By.XPATH,
        "//u[contains(.,'%s')]/../..//i[contains(@class,'fa-edit')]"),
    "ak.prd_content.select_repo": (
        By.XPATH,
        "//u[contains(.,'%s')]/../../div/form/div/select"),
    "ak.subscriptions.search": (
        By.XPATH,
        "//input[@ng-model='subscriptionSearch']"),

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
    "rh.rpms_prd_expander": (
        By.XPATH, ("//div[@id='ui-tabs-1']//td[contains(.,'%s')]"
                   "/span[@class='expander']")),
    "rh.kickstarts_prd_expander": (
        By.XPATH, ("//div[@id='ui-tabs-2']//td[contains(.,'%s')]"
                   "/span[@class='expander']")),
    "rh.isos_prd_expander": (
        By.XPATH, ("//div[@id='ui-tabs-6']//td[contains(.,'%s')]"
                   "/span[@class='expander']")),
    "rh.ostree_prd_expander": (
        By.XPATH, ("//div[@id='ui-tabs-7']//td[contains(.,'%s')]"
                   "/span[@class='expander']")),
    "rh.reposet_expander": (
        By.XPATH, ("//span[contains(@class, 'expander_area') and "
                   "contains(.,'%s')]/span")),
    "rh.reposet_checkbox": (
        By.XPATH, ("//span[contains(@class, 'expander_area') and "
                   "contains(.,'%s')]"
                   "/../../td/input[@class='repo_set_enable']")),
    "rh.repo_checkbox": (
        By.XPATH, ("//table[@class='repo_table']//td[contains(.,'%s')]"
                   "/../td/label/input[@class='repo_enable']")),
    "rh.reposet_spinner": (
        By.XPATH, ("//span[contains(@class, 'expander_area') and "
                   "contains(.,'%s')]/../../td/img[@alt='Spinner']")),
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
    "content_env.table": (
        By.XPATH,
        "//table[contains(@class,'environment-table')]"),

    # GPG Key
    "gpgkey.new": (By.XPATH, "//button[@ui-sref='gpg-keys.new']"),
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
        By.XPATH,
        "//button[contains(@ng-click, 'content-views.details.deletion')]"),
    "contentviews.remove_ver": (
        By.XPATH, ("//td/a[contains(., '%s')]/following::td/"
                   "button[contains(@ng-click, 'version-deletion')]")),
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
    "contentviews.version_name": (
        By.XPATH, "//td/a[contains(., '%s')]"),
    "contentviews.version_environments": (
        By.XPATH,
        "//table[@bst-table='table']//tr/td[contains(., '%s')]/"
        "following-sibling::td/ul/li[@ng-repeat='environment in"
        " version.environments']"),
    "contentviews.success_rm_alert": (
        By.XPATH,
        ("//div[contains(@class, 'alert-success')]"
         "/div/span[contains(., 'Successfully removed')]")),
    "contentviews.publish": (
        By.XPATH, "//button[contains(@ng-click, 'details.publish')]"),
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
         "/button[@ng-click='selectVersion(item.name)']")),
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
    "contentviews.packages": (
        By.XPATH,
        "//tr[@row-select='rule']/td/input[@ng-model='rule.name']"
    ),
    "contentviews.package_checkbox": (
        By.XPATH,
        ("../preceding-sibling::td[@class='row-select']"
         "/input[@type='checkbox']")),
    "contentviews.package_edit": (
        By.XPATH,
        ("../following-sibling::td/button[contains(@class, 'btn') and "
         "contains(@ng-click, 'rule.editMode = true')]")),
    "contentviews.package_version_type": (
        By.XPATH,
        "../following-sibling::td/span/select[@ng-model='rule.type']"),
    "contentviews.package_version_value": (
        By.XPATH,
        "../following-sibling::td/span/span/input[@ng-model='rule.version']"),
    "contentviews.package_save": (
        By.XPATH,
        ("../following-sibling::td/div/"
         "button[contains(@ng-click, 'handleSave')]")),
    "contentviews.remove_packages": (
        By.XPATH, "//button[@ng-click='removeRules(filter)']"),
    "contentviews.affected_repos_radio": (
        By.XPATH,
        ("//input[@type='radio' and @ng-model='showRepos' and "
         "@ng-value='true']")),
    "contentviews.affected_repos_checkboxes": (
        By.XPATH,
        "//input[@type='checkbox' and @ng-model='repository.selected']"),
    "contentviews.affected_repo_checkbox": (
        By.XPATH,
        ("//input[@type='checkbox' and @ng-model='repository.selected']"
         "[../following-sibling::td/a[contains(normalize-space(.), '%s')]]")),
    "contentviews.filter_update_repos": (
        By.XPATH, "//button[@ng-click='updateRepositories()']"),
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
    "contentviews.erratum_type_checkbox": (
        By.XPATH, "//input[@ng-model='types.%s']"),
    "contentviews.erratum_date_type": (
        By.XPATH, "//input[@type='radio' and @value='%s']"),
    "contentviews.calendar_date_input": (
        By.XPATH, "//input[@ng-model='rule.%s']"),
    "contentviews.calendar_date_button": (
        By.XPATH, "//input[@ng-model='rule.%s']/.."
                  "//li/button[@ng-click='isOpen = false']"),
    "contentviews.save_erratum": (
        By.XPATH, "//button[contains(@ng-click, 'handleSave()')]"),
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
    "contentviews.table_filter": (
        By.XPATH, "//input[@ng-model='filterTerm']"),
    "contentviews.filter_name": (
        By.XPATH, "//tr[@row-select='filter']/td[2]/a[contains(., '%s')]"),
    "contentviews.copy": (
        By.XPATH, "//button[@ng-click='showCopy = true']"),
    "contentviews.copy_name": (
        By.XPATH, "//input[@ng-model='copyName']"),
    "contentviews.copy_create": (
        By.XPATH, "//button[@ng-click='copy(copyName)']"),
    "contentviews.yum_repositories": (
        By.XPATH, "//a[@class='ng-scope' and contains(@ui-sref,'yum.list')]"),
    "contentviews.version.package_name": (
        By.XPATH,
        ("//div[@bst-table='detailsTable']//tr[contains(@class, 'ng-scope')]"
         "/td[1][contains(., '%s')]")),
    "contentviews.version.package_version": (
        By.XPATH,
        ("//div[@bst-table='detailsTable']//tr[contains(@class, 'ng-scope')]"
         "/td[2][contains(., '%s')]")),

    # Packages
    "package.rpm_name": (By.XPATH, "//a[contains(., '%s')]"),
    "package.description": (By.XPATH, "//span[text()='Description']/../.."
                                      "/span[contains(@class, 'info-value')]"),
    "package.summary": (By.XPATH, "//span[text()='Summary']/../.."
                                  "/span[contains(@class, 'info-value')]"),
    "package.group": (By.XPATH, "//span[text()='Group']/../.."
                                "/span[contains(@class, 'info-value')]"),
    "package.license": (By.XPATH, "//span[text()='License']/../.."
                                  "/span[contains(@class, 'info-value')]"),
    "package.url": (By.XPATH, "//span[text()='Url']/../.."
                              "/span[contains(@class, 'info-value')]"),
    "package.size": (By.XPATH, "//span[text()='Size']/../.."
                               "/span[contains(@class, 'info-value')]"),
    "package.filename": (By.XPATH, "//span[text()='Filename']/../.."
                                   "/span[contains(@class, 'info-value')]"),
    "package.checksum": (By.XPATH, "//span[text()='Checksum']/../.."
                                   "/span[contains(@class, 'info-value')]"),
    "package.checksum_type": (
        By.XPATH, "//span[text()='Checksum Type']/../.."
                  "/span[contains(@class, 'info-value')]"),
    "package.source_rpm": (
        By.XPATH, "//span[text()='Source RPM']/../.."
                  "/span[contains(@class, 'info-value')]"),
    "package.build_host": (
        By.XPATH, "//span[text()='Build Host']/../.."
                  "/span[contains(@class, 'info-value')]"),
    "package.build_time": (
        By.XPATH, "//span[text()='Build Time']/../.."
                  "/span[contains(@class, 'info-value')]"),
    "package.content_file": (By.XPATH, "//div[contains(., '%s')]"),

    # Puppet Module
    "puppet.module_name": (By.XPATH, "//a[contains(., '%s')]"),
    "puppet.author": (
        By.XPATH, "//span[text()='Author']/../"
                  "following-sibling::span[contains(@class, 'info-value')][1]"
    ),
    "puppet.version": (
        By.XPATH, "//span[text()='Version']/../"
                  "following-sibling::span[contains(@class, 'info-value')][1]"
    ),
    "puppet.source": (
        By.XPATH, "//span[text()='Source']/../"
                  "following-sibling::span[contains(@class, 'info-value')][1]"
    ),
    "puppet.project_page": (
        By.XPATH, "//span[text()='Project Page']/../"
                  "following-sibling::span[contains(@class, 'info-value')][1]/"
                  "a"
    ),
    "puppet.license": (
        By.XPATH, "//span[text()='License']/../"
                  "following-sibling::span[contains(@class, 'info-value')][1]"
    ),
    "puppet.description": (
        By.XPATH, "//span[text()='Description']/../"
                  "following-sibling::p[contains(@class, 'info-paragraph')][1]"
    ),
    "puppet.summary": (
        By.XPATH, "//span[text()='Summary']/../"
                  "following-sibling::p[contains(@class, 'info-paragraph')][1]"
    ),

    # System Groups
    "system-groups.new": (
        By.XPATH, "//button[@ui-sref='system-groups.new.form']"),
    "system-groups.name": (By.ID, "name"),
    "system-groups.description": (By.ID, "description"),
    "system-groups.unlimited": (By.NAME, "limit"),
    "system-groups.limit": (By.ID, "max_systems"),

    "system-groups.remove": (
        By.XPATH, "//button[@ng-disabled='!group.permissions.deletable']"),

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
        ("//td[span[contains(@data-original-title, '%s')]]/"
         "following-sibling::td[@class='setting_value']/"
         "span[contains(@class, 'editable')]")),
    "settings.edit_value": (
        By.XPATH,
        "//td[@class='setting_value']//form//"
        "*[contains(@class, 'input-sm') or contains(@class, 'input-large')]"),
    "settings.save": (
        By.XPATH,
        "//td[@class='setting_value']//form//button[@type='submit']"),

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
    "discoveryrules.disabled_name": (
        By.XPATH, "//a[@disabled='disabled']/span[contains(., '%s')]"),
    "discoveryrules.name": (
        By.XPATH, "//input[@id='discovery_rule_name']"),
    "discoveryrules.search": (
        By.XPATH, "//input[@id='search']"),
    "discoveryrules.hostgroup_dropdown": (
        By.XPATH,
        ("//div[contains(@id, 'discovery_rule_hostgroup_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "discoveryrules.hostgroup": (
        By.XPATH,
        ("//div[contains(@id, 'discovery_rule_hostgroup_id')]/a"
         "/span[contains(@class, 'chosen')]")),
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
    "discoveryrules.dropdown": (
        By.XPATH,
        ("//td/a[normalize-space(.)='%s']"
         "/following::td/div/a[@data-toggle='dropdown']")),

    # Discovered Hosts
    "discoveredhosts.hostname": (
        By.XPATH, ("//a[contains(@href, 'discovered_hosts')"
                   " and contains(., '%s')]")),
    "discoveredhosts.dropdown": (
        By.XPATH, ("//a[contains(@href,'%s')]"
                   "/following::a[@data-toggle='dropdown']")),
    "discoveredhosts.refresh_facts": (
        By.XPATH, ("//a[contains(@href,'%s') and "
                   "contains(@data-id,'refresh_facts')]")),
    "discoveredhosts.reboot": (
        By.XPATH, ("//a[contains(@href,'%s') and "
                   "contains(@data-id,'reboot')]")),
    "discoveredhosts.auto_provision": (
        By.XPATH, ("//a[contains(@href,'%s') and "
                   "contains(@data-id,'auto_provision')]")),
    "discoveredhosts.delete": (
        By.XPATH, ("//a[@class='delete' and contains(@data-confirm, '%s')]")),
    "discoveredhosts.delete_from_facts": (
        By.XPATH, ("//a[contains(@href,'%s') and contains(.,'Delete')]")),
    "discoveredhosts.select_all": (By.ID, "check_all"),
    "discoveredhosts.fetch_ip": (
        By.XPATH, ("//td/span/a[contains(@href, '%s')]/following::td[2]")),
    "discoveredhosts.select_host": (
        By.XPATH, ("//a[contains(@href, '%s')]/../../../td/"
                   "input[@type='checkbox']")),
    "discoveredhosts.select_action": (
        By.XPATH, ("//div[@id='submit_multiple']/a[@data-toggle='dropdown']")),
    "discoveredhosts.select_action_facts": (
        By.XPATH, ("//div[@id='title_action']//a[@data-toggle='dropdown']")),
    "discoveredhosts.provision_from_facts": (
        By.XPATH, ("//div[@id='title_action']//ul/li"
                   "/a[contains(., 'Provision')]")),
    "discoveredhosts.multi_delete": (
        By.XPATH, ("//a[contains(@onclick, "
                   "'/discovered_hosts/multiple_destroy')]")),
    "discoveredhosts.auto_provision_all": (
        By.XPATH, ("//div[@id='submit_multiple']"
                   "/following::a[contains(@href, 'auto_provision_all')]")),
    "discoveredhosts.assign_org": (
        By.XPATH, ("//a[contains(@onclick, "
                   "'/discovered_hosts/select_multiple_organization')]")),
    "discoveredhosts.assign_loc": (
        By.XPATH, ("//a[contains(@onclick, "
                   "'/discovered_hosts/select_multiple_location')]")),
    "discoveredhosts.select_org": (
        By.XPATH, ("//select[@id='organization_id']")),
    "discoveredhosts.select_loc": (By.XPATH, "//select[@id='location_id']"),
    "discoveredhosts.fetch_interfaces": (
        By.XPATH, ("//div[@id='content']/table/tbody/tr[2]/"
                   "td[contains(.,'eth')]")),
    "discoveredhosts.fetch_fact": (
        By.XPATH, ("//div[@id='content']/table/tbody/tr[2]"
                   "/td[contains(.,'%s')]")),
    "discoveredhosts.fetch_bios": (
        By.XPATH, ("//div[@id='content']/table/tbody/tr[2]"
                   "/td[contains(.,'bios')]")),
    "discoveredhosts.fetch_custom_fact": (
        By.XPATH, ("//div[@id='content']/table/tbody/tr[2]/"
                   "td[contains(.,'some')]")),
    "discoveredhosts.bulk_submit_button": (
        By.XPATH, ("//div[@id='confirmation-modal']"
                   "//div[@class='modal-footer']/button[2]")),
    "discoveredhosts.provision": (
        By.XPATH, ("//td/span/a[contains(@href, '%s')]/following::td/div[2]"
                   "/span/a[contains(.,'Provision')]")),
    "discoveredhosts.select_modal_hostgroup": (
        By.ID, "s2id_host_hostgroup_id"),
    "discoveredhosts.select_modal_org": (
        By.ID, "s2id_host_organization_id"),
    "discoveredhosts.select_modal_loc": (
        By.ID, "s2id_host_location_id"),
    "discoverehosts.select_choices": (
        By.XPATH, ("/li[contains(@class, 'select2-result')]"
                   "/div[contains(., '%s')]")),
    "discoveredhosts.quick_create_button": (
        By.XPATH, ("//input[@value='Quick create']")),
    "discoveredhosts.create_host_button": (
        By.XPATH, ("//input[@value='Create host']")),

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
        By.XPATH,
        ("//div[contains(@id, 'auth_source_ldap_server_type')]/a"
         "/span[contains(@class, 'arrow')]")),
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
    "oscap.upload_content": (
        By.XPATH, "//a[@data-id='aid_compliance_scap_contents_new']"),
    "oscap.content_search": (
        By.XPATH, "//input[contains(@data-url, 'auto_complete_search')]"),
    "oscap.content_edit": (
        By.XPATH,
        ("//td[contains(.,'%s')]/../td/div/span/a")),
    "oscap.content_dropdown": (
        By.XPATH,
        ("//td[contains(.,'%s')]/following-sibling::td/div/"
         "a[@data-toggle='dropdown']")),
    "oscap.content_path": (
        By.ID, "scap_content_scap_file"),
    "oscap.content_download": (
        By.XPATH,
        ("//td[contains(.,'%s')]/../td/div/ul/li/"
         "a[contains(@data-id, 'compliance_scap_contents') "
         "and not(contains(@class, 'delete'))]")),
    "oscap.content_title": (
        By.ID, "scap_content_title"),
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
         "/../../td/div/a/span")),
    "oscap.name_policy": (By.ID, "policy_name"),
    "oscap.desc_policy": (By.ID, "policy_description"),
    "oscap.content_policy": (
        By.XPATH,
        ("//div[contains(@id, 'policy_scap_content_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "oscap.profile_policy": (
        By.XPATH,
        ("//div[contains(@id, 'policy_scap_content_profile_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "oscap.period_policy": (
        By.XPATH,
        ("//div[contains(@id, 'policy_period')]/a"
         "/span[contains(@class, 'arrow')]")),
    "oscap.weekday_policy": (
        By.XPATH,
        ("//div[contains(@id, 'policy_weekday')]/a"
         "/span[contains(@class, 'arrow')]")),
    "oscap.dayofmonth_policy": (
        By.XPATH,
        ("//div[contains(@id, 'policy_day_of_month')]/a"
         "/span[contains(@class, 'arrow')]")),
    "oscap.custom_policy": (By.ID, "policy_cron_line"),

    # oscap reports
    "oscap.report_select": (By.XPATH, "//a[normalize-space(.)='%s']"),

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
        ("//div[contains(@id, 'preliminary_compute_resource_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "container.next_section": (By.ID, "next"),
    "container.content_view_tab": (By.ID, "katello_tab"),
    "container.content_view_tab_next": (By.ID, "next_katello"),
    "container.docker_hub_tab": (By.ID, "hub_tab"),
    "container.docker_hub_tab_next": (By.ID, "next_hub"),
    "container.external_registry_tab": (By.ID, "registry_tab"),
    "container.external_registry_tab_next": (By.ID, "next_registry"),
    "container.lifecycle_environment": (
        By.XPATH,
        ("//div[contains(@id, 'kt_environment_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "container.content_view": (
        By.XPATH,
        ("//div[contains(@id, 'content_view_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "container.repository": (
        By.XPATH,
        ("//div[contains(@id, 'repository_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "container.tag": (
        By.XPATH,
        ("//div[contains(@id, 'tag_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "container.capsule": (
        By.XPATH,
        ("//div[contains(@id, 'capsule_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "container.docker_hub_tag": (
        By.ID, "hub_docker_container_wizard_states_image_tag"),
    "container.registry.registry": (
        By.XPATH,
        ("//div[contains(@id, 'image_registry_id')]/a"
         "/span[contains(@class, 'arrow')]")),
    "container.registry.search": (
        By.ID,
        "registry_docker_container_wizard_states_image_repository_name"),
    "container.registry.tag": (
        By.ID, "registry_docker_container_wizard_states_image_tag"),
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

    # Docker Tags
    "dockertag.select_name": (
        By.XPATH,
        ("//td[contains(., '%s') and following-sibling::td[contains(., '%s')] "
         "and following-sibling::td[contains(., '%s')]]/a")),

    # Host Collections
    "hostcollection.new": (
        By.XPATH, "//button[@ui-sref='host-collections.new.form']"),
    "hostcollection.select_name": (
        By.XPATH,
        "//tr[contains(@ng-repeat, 'hostCollection')]"
        "/td/a[contains(., '%s')]"),
    "hostcollection.edit_name": (
        By.XPATH, "//form[@bst-edit-text='hostCollection.name']//div/span/i"),
    "hostcollection.edit_name_text": (
        By.XPATH,
        "//form[@bst-edit-text='hostCollection.name']/div/input"),
    "hostcollection.save_name": (
        By.XPATH,
        ("//form[@bst-edit-text='hostCollection.name']"
         "//button[@ng-click='save()']")),
    "hostcollection.name_field": (
        By.XPATH,
        "//form[@bst-edit-text='hostCollection.name']//div"
        "/span[contains(., '%s')]"),
    "hostcollection.edit_description": (
        By.XPATH,
        "//form[@bst-edit-textarea='hostCollection.description']//div/span/i"),
    "hostcollection.edit_description_text": (
        By.XPATH,
        ("//form[@bst-edit-textarea='hostCollection.description']"
         "/div/textarea")),
    "hostcollection.save_description": (
        By.XPATH,
        ("//form[@bst-edit-textarea='hostCollection.description']"
         "//button[@ng-click='save()']")),
    "hostcollection.description_field": (
        By.XPATH,
        "//form[@bst-edit-textarea='hostCollection.description']//div"
        "/span[contains(., '%s')]"),
    "hostcollection.edit_limit": (
        By.XPATH,
        ("//div[@bst-edit-custom='hostCollection.max_hosts']"
         "//div/span/i")),
    "hostcollection.save_limit": (
        By.XPATH,
        ("//div[@bst-edit-custom='hostCollection.max_hosts']"
         "//button[@ng-click='save()']")),
    "hostcollection.limit_field": (
        By.XPATH,
        "//div[@bst-edit-custom='hostCollection.max_hosts']"
        "//span[text()='%s']"),
    "hostcollection.remove": (
        By.XPATH, "//button[@ng-click='openModal()']"),
    "hostcollection.copy": (
        By.XPATH, "//button[@ng-click='showCopy = true']"),
    "hostcollection.copy_name": (By.ID, "copy_name"),
    "hostcollection.copy_create": (
        By.XPATH, "//button[@ng-click='copy(copyName)']"),
    "hostcollection.select_host": (
        By.XPATH,
        ("//div[contains(@bst-table, 'detailsTable')]"
         "//td[contains(normalize-space(.), '%s')]"
         "/preceding-sibling::td[@class='row-select']"
         "/input[@type='checkbox']")),
    "hostcollection.add_host": (
        By.XPATH,
        "//button[contains(@ng-click, 'addSelected')]"),
    "hostcollection.collection_actions.packages": (
        By.XPATH,
        ("//li[@bst-feature-flag='remote_actions']"
         "//a[contains(@href, 'packages')]")),
    "hostcollection.collection_actions.errata": (
        By.XPATH,
        ("//li[@bst-feature-flag='remote_actions']"
         "//a[contains(@href, 'errata')]")),
    "hostcollection.errata.errata_select": (
        By.XPATH,
        ("//tr[td/a[@ng-click='transitionToErrata(erratum)' and "
         "contains(.,'%s')]]/td/input[@type='checkbox']")),
    "hostcollection.errata.errata_apply": (
        By.XPATH, "//button[contains(@ng-click, 'showConfirmDialog()')]"),
    "hostcollection.errata.confirm_installation": (
        By.XPATH, "//button[contains(@ng-click, 'installErrata()')]"),
    "hostcollection.errata.cancel_installation": (
        By.XPATH,
        "//button[contains(@ng-click, 'detailsTable.working = false')]"),

    # Errata
    "errata.filter_applicable": (
        By.XPATH, "//input[@ng-model='showApplicable']"),
    "errata.select_name": (By.XPATH, "//a[contains(., '%s')]"),
    "errata.content_hosts.installable": (
        By.XPATH, "//input[@ng-model='restrictInstallable']"),
    "errata.content_hosts.env_filter": (
        By.XPATH, "//select[@ng-model='environmentFilter']"),
    "errata.content_hosts.ch_select": (
        By.XPATH, "//tr[td/a[contains(.,'%s')]]/td/input[@type='checkbox']"),
    "errata.content_hosts.errata_apply": (
        By.XPATH,
        ("//button[contains(@class, 'btn-primary') and "
         "contains(@ng-disabled, 'detailsTable')]")),
    "errata.content_hosts.confirm_installation": (
        By.XPATH,
        "//button[contains(@class, 'btn-primary') and @type='submit']"),
    "errata.content_hosts.cancel_installation": (
        By.XPATH, "//button[@ng-click='transitionBack()']"),
    "errata.repositories.repo_select": (
        By.XPATH,
        ("//a[contains(@href, 'repositories') and contains(., '%s')]"
         "[../following-sibling::td/a[contains(@ui-sref, 'products.details') "
         "and contains(., '%s')]]")),
    "errata.advisory": (
        By.XPATH,
        "//span[text()='Advisory']/../../span[contains(@class, 'info-value')]"
    ),
    "errata.cves": (
        By.XPATH,
        "//span[text()='CVEs']/../../span[contains(@class, 'info-value')]"),
    "errata.type": (
        By.XPATH,
        "//span[text()='Type']/../../span[contains(@class, 'info-value')]"
    ),
    "errata.severity": (
        By.XPATH,
        "//span[text()='Severity']/../../span[contains(@class, 'info-value')]"
    ),
    "errata.issued": (
        By.XPATH,
        "//span[text()='Issued']/../../span[contains(@class, 'info-value')]"
    ),
    "errata.last_updated_on": (
        By.XPATH,
        "//span[text()='Last Updated On']/../.."
        "/span[contains(@class, 'info-value')]"),
    "errata.reboot_suggested": (
        By.XPATH,
        "//span[text()='Reboot Suggested?']/../.."
        "/span[contains(@class, 'info-value')]"),
    "errata.topic": (
        By.XPATH,
        "//span[text()='Topic']/.."
        "/following-sibling::p[contains(@class, 'info-paragraph')][1]"
    ),
    "errata.description": (
        By.XPATH,
        "//span[text()='Description']/.."
        "/following-sibling::p[contains(@class, 'info-paragraph')][1]"
    ),
    "errata.solution": (
        By.XPATH,
        "//span[text()='Solution']/.."
        "/following-sibling::p[contains(@class, 'info-paragraph')][1]"
    ),
    "errata.affected_packages": (
        By.XPATH,
        "//span[text()='Affected Packages']/.."
        "/following-sibling::ul[1]/li/a[contains(., '%s')]"
    ),
    "errata.table_value": (
        By.XPATH, "//td[contains(normalize-space(.), '%s')]"),


    # Smart Variable
    "smart_variable.new": (By.XPATH, "//a[contains(., '+ Add Variable')]"),
    "smart_variable.select_name": (By.XPATH, "//a[contains(., '%s')]"),
    "smart_variable.key": (
        By.XPATH,
        "//input[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@name, '[key]')]"),
    "smart_variable.description": (
        By.XPATH,
        "//textarea[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@name, '[description]')]"),
    "smart_variable.puppet_class": (
        By.XPATH,
        "//div[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@id, 'puppetclass')]/a"
        "/span[contains(@class, 'arrow')]"),
    "smart_variable.key_type": (
        By.XPATH,
        "//select[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@name, '[key_type]')]"),
    "smart_variable.default_value": (
        By.XPATH,
        "//textarea[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@name, '[default_value]')]"),
    "smart_variable.hidden_value": (
        By.XPATH,
        "//input[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@id, 'hidden_value')]"),
    "smart_variable.optional_expander": (
        By.XPATH,
        "//h2[(ancestor::div[@class='tab-pane fields active'] or "
        "ancestor::form[contains(@id, 'edit_variable')]) and "
        "contains(@data-target, 'input_validators')]"),
    "smart_variable.validator_type": (
        By.XPATH,
        "//select[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@name, '[validator_type]')]"
    ),
    "smart_variable.validator_rule": (
        By.XPATH,
        "//input[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@name, '[validator_rule]')]"
    ),
    "smart_variable.matcher_priority": (
        By.XPATH,
        "//textarea[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@name, 'variable_')) and contains(@name, '[path]')]"
    ),
    "smart_variable.merge_overrides": (
        By.XPATH,
        "//input[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@id, 'merge_override')]"),
    "smart_variable.merge_default": (
        By.XPATH,
        "//input[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@id, 'merge_default')]"),
    "smart_variable.avoid_duplicates": (
        By.XPATH,
        "//input[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@id, 'avoid_duplicates')]"),
    "smart_variable.add_matcher": (
        By.XPATH,
        "//a[(ancestor::div[@class='tab-pane fields active'] or "
        "ancestor::form[contains(@id, 'edit_variable')]) and "
        "contains(@data-original-title, 'new matcher')]"
    ),
    "smart_variable.matcher_attribute_type": (
        By.XPATH,
        "(//select[(ancestor::div[@class='tab-pane fields active'] or "
        "ancestor::form[contains(@id, 'edit_variable')]) and "
        "contains(@class, 'matcher_key')])[%i]"
    ),
    "smart_variable.matcher_attribute_value": (
        By.XPATH,
        "(//input[(ancestor::div[@class='tab-pane fields active'] or "
        "ancestor::form[contains(@id, 'edit_variable')]) and "
        "contains(@class, 'matcher_value')])[%i]"
    ),
    "smart_variable.matcher_value": (
        By.XPATH,
        "(//textarea[(ancestor::div[@class='tab-pane fields active'] or "
        "contains(@id, 'variable_')) and contains(@name, '[value]')])[%i]"
    ),
    "smart_variable.matcher_error": (By.XPATH, "//tr[@class='has-error']"),
    "smart_variable.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "smart_variable.table_value": (By.XPATH, "//td[contains(., '%s')]"),
})
