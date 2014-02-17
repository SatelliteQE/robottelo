# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements different locators for UI
"""

from selenium.webdriver.common.by import By


menu_locators = {
    # Menus

    # Monitor Menu
    "menu.monitor": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='monitor_menu']"),
    "menu.dashboard": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_dashboard']")),
    "menu.content_dashboard": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@id='menu_item_content_dashboard']")),
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

    # Content Menu
    "menu.content": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='content']"),
    "menu.life_cycle_environments": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_environments']"),
    "menu.red_hat_subscriptions": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_red_hat_subscriptions']")),
    "menu.subscription_manager_applications": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_subscription_manager_applications']")),
    "menu.activation_keys": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_activation_keys']")),
    "menu.red_hat_repositories": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_redhat_provider']")),
    "menu.products": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_products']"),
    "menu.gpg_keys": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_gpg_keys']"),
    "menu.sync_status": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_sync_status']"),
    "menu.sync_plans": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_sync_plans']"),
    "menu.sync_schedules": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_sync_schedules']"),
    "menu.content_view_definitions": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_content_view_definitions']")),
    "menu.content_search": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_content_search']"),
    "menu.changeset_management": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_changeset_management']")),
    "menu.changeset_history": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_changeset_history']")),

    # Hosts Menu
    "menu.hosts": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
            "//a[@id='hosts_menu']")),
    "menu.all_hosts": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
            "//a[@id='menu_item_hosts']")),
    "menu.registered_systems": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_systems']")),
    "menu.system_groups": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_system_groups']")),
    "menu.operating_systems": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_operatingsystems']")),
    "menu.provisioning_templates": (
        By.XPATH,
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_config_templates']")),
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
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_common_parameters']")),
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
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
            "//a[@id='infrastructure_menu']")),
    "menu.smart_proxies": (
        By.XPATH,
        "//div[contains(@style,'static')]//a[@id='menu_item_smart_proxies']"),
    "menu.compute_resources": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style, 'fixed')]"
            "//a[@id='menu_item_compute_resources']")),
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
        ("//div[contains(@style,'static')]"
            "//a[@id='menu_item_auth_source_ldaps']")),
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
    "menu.account": (By.XPATH, "//a[@id='account_menu']"),
    "menu.sign_out": (By.XPATH, "//a[@id='menu_item_logout']"),
    "menu.my_account": (By.XPATH, "//a[@id='menu_item_my_account']"),

    # Orgs
    "org.any_context": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
            "//li[contains(@class,'org-switcher')]/a")),
    "org.manage_org": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
            "//a[@class='manage-menu' and contains(@href, 'organizations')]")),
    "org.nav_current_org": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
            "//li[contains(@class,'org-switcher')]"
            "//li/a[@data-toggle='dropdown']")),
    "org.current_org": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
            "//li[contains(@class,'org-switcher')]/a")),
    "org.select_org": (
        By.XPATH,
        ("//div[contains(@style,'static') or contains(@style,'fixed')]"
         "//a[@href='/organizations/clear']/../../li/a[contains(.,'%s')]"))
}

tab_locators = {

    #common
    "tab_primary": (By.XPATH, "//a[@href='#primary']"),
    #Third level UI
    "tab_org": (By.XPATH, "//a[@href='#organizations']"),

    #Operating System
    #Third level UI
    "operatingsys.tab_primary": (By.XPATH, "//a[@href='#primary']"),
    "operatingsys.tab_ptable": (By.XPATH, "//a[@href='#ptable']"),
    "operatingsys.tab_medium": (By.XPATH, "//a[@href='#media']"),
    "operatingsys.tab_templates": (By.XPATH, "//a[@href='#templates']"),
    "operatingsys.tab_parameters": (By.XPATH, "//a[@href='#params']"),

    #Host
    #Third level UI

    "host.tab_network": (By.XPATH, "//a[@href='#network']"),
    "host.tab_os": (By.XPATH, "//a[@href='#os']"),
    "host.tab_vm": (By.XPATH, "//a[@href='#compute_resource']"),
    "host.tab_params": (By.XPATH, "//a[@href='#params']"),
    "host.tab_info": (By.XPATH, "//a[@href='#info']"),

    #Provisioning Templates
    #Third level UI

    "provision.tab_type": (By.XPATH, "//a[@href='#template_type']"),
    "provision.tab_association": (By.XPATH,
                                  "//a[@href='#template_associations']"),
    "provision.tab_history": (By.XPATH, "//a[@href='#history']"),

    #Users
    #Third level UI

    "users.tab_primary": (By.XPATH, "//a[@href='#primary']"),
    "users.tab_roles": (By.XPATH, "//a[@href='#roles']"),
    "users.tab_filters": (By.XPATH, "//a[@href='#filters']")}


common_locators = {

    #common locators

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

    "entity_select": (
        By.XPATH,
        "//div[@class='ms-selectable']//span[contains(.,'%s')]"),
    "entity_deselect": (
        By.XPATH,
        "//div[@class='ms-selection']//span[contains(.,'%s')]"),
    "entity_checkbox": (
        By.XPATH,
        "//ul[@class='inputs-list']/li/label[normalize-space(.)='%s']"),

    "search": (By.ID, "search"),
    "search_button": (By.XPATH, "//button[contains(@type,'submit')]"),
    "submit": (By.NAME, "commit"),
    "filter": (By.XPATH, "//div[@id='ms-%s_ids']//input[@class='ms-filter']"),
    "parameter_tab": (By.XPATH, "//a[contains(., 'Parameters')]"),
    "add_parameter": (
        By.XPATH, "//a[contains(text(),'+ Add Parameter')]"),
    "parameter_name": (By.XPATH, "//input[@placeholder='Name']"),
    "parameter_value": (By.XPATH, "//textarea[@placeholder='Value']"),
    "parameter_remove": (
        By.XPATH, "//div/input[@value='%s']/following-sibling::span/a/i")}

locators = {

    # Login
    "login.username": (By.ID, "login_login"),
    "login.password": (By.ID, "login_password"),
    "login.gravatar": (By.XPATH, "//img[contains(@class, 'gravatar')]"),

    # Organizations
    "org.new": (
        By.XPATH,
        ("//a[@class='btn btn-success'"
            "and contains(@href, '/organizations/new')]")),
    "org.name": (By.ID, "organization_name"),
    "org.proceed_to_edit": (
        By.XPATH,
        "//a[@class='btn btn-default' and contains(@href, '/edit')]"),
    "org.org_name": (By.LINK_TEXT, "%s"),
    "org.dropdown": (
        By.XPATH,
        ("//a[normalize-space(.)='%s' and contains(@href,'organizations')]"
            "/../../td/div/a[@data-toggle='dropdown']")),
    "org.delete": (
        By.XPATH,
        "//a[@class='delete' and contains(@data-confirm, '%s')]"),

    #Operating system (OS)
    "operatingsys.new": (
        By.XPATH, "//a[contains(@href, '/operatingsystems/new')]"),
    "operatingsys.name": (By.ID, "operatingsystem_name"),
    "operatingsys.major_version": (By.ID, "operatingsystem_major"),
    "operatingsys.minor_version": (By.ID, "operatingsystem_minor"),
    "operatingsys.family": (By.ID, "operatingsystem_family"),
    "operatingsys.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "operatingsys.operatingsys_name": (By.XPATH, "//a[contains(., '%s')]"),
    "operatingsys.template": (
        By.ID,
        "operatingsystem_os_default_templates_attributes_0_config_template_id"
    ),

    #Compute Resource

    "resource.new": (
        By.XPATH, "//a[contains(@href, '/compute_resources/new')]"),
    "resource.name": (By.ID, "compute_resource_name"),
    "resource.provider_type": (
        By.XPATH,
        "//select[@id='compute_resource_provider']"),
    "resource.description": (By.ID, "compute_resource_description"),
    "resource.test_connection": (
        By.XPATH,
        "//a[contains(@data-url, '/compute_resources/test_connection')]"),
    "resource.url": (By.XPATH, "//input[@id='compute_resource_url']"),
    "resource.user": (By.ID, "compute_resource_user"),
    "resource.password": (By.ID, "compute_resource_password"),
    "resource.region": (By.ID, "compute_resource_region"),
    "resource.select_name": (
        By.XPATH,
        ("//a[contains(@href,'compute_resources')"
            "and normalize-space(.)='%s']")),
    "resource.dropdown": (By.XPATH, "//a[contains(@href,'%s')]/../../a"),
    "resource.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "resource.edit": (
        By.XPATH, "//a[contains(.,'Edit') and contains(@href,'%s')]"),

    #resource - libvirt
    "resource.libvirt_display": (By.ID, "compute_resource_display_type"),
    "resource.libvirt_console_passwd": (
        By.ID, "compute_resource_set_console_password"),

    #resource - openstack
    "resource.rhos_tenant": (By.ID, "compute_resource_tenant"),

    #Hosts

    #host.primary
    "host.new": (By.XPATH, "//a[contains(@href, '/hosts/new')]"),
    "host.name": (By.ID, "host_name"),
    "host.clone": (
        By.XPATH, "//a[contains(@href,'%s') and contains(.,'Clone')]"),
    "host.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "host.group": (By.ID, "host_hostgroup_id"),
    "host.deploy": (By.ID, "host_compute_resource_id"),
    "host.environment": (By.ID, "host_environment_id"),
    "host.dropdown": (
        By.XPATH,
        ("//a[contains(@href,'%s')]"
            "/../../a[contains(@data-toggle,'dropdown')]")),
    "host.select_name": (
        By.XPATH,
        ("//input[contains(@id,'host_ids')]"
            "/../../td[@class='ellipsis']/a[contains(@href,'%s')]")),

    #host.network
    "host.mac": (By.ID, "host_mac"),
    "host.domain": (By.ID, "host_domain_id"),
    "host.subnet": (By.ID, "host_subnet_id"),
    "host.ip": (By.ID, "host_ip"),

    #host.os
    "host.arch": (By.ID, "host_architecture_id"),
    "host.os": (By.ID, "host_operatingsystem_id"),
    "host.org": (By.ID, "host_organization_id"),
    "host.edit": (By.XPATH,
                  "//a[@class='btn btn-default' and contains(@href,'edit')]"),
    "host.puppet_ca": (By.ID, "host_puppet_ca_proxy_id"),
    "host.puppet_master": (By.ID, "host_puppet_proxy_id"),
    "host.provision": (By.ID, "host_build"),
    "host.media": (By.ID, "host_medium_id"),
    "host.ptable": (By.ID, "host_ptable_id"),
    "host.custom_ptables": (By.ID, "host_disk"),
    "host.root_pass": (By.ID, "host_root_pass"),
    "host.provision_template": (
        By.XPATH,
        "//div[contains(.,'Provisioning Templates')]/../div/a[@class='btn']"),

    #host.vm (NOTE:- visible only when selecting a compute resource)
    "host.vm_cpus": (By.ID, "host_compute_attributes_cpus"),
    "host.vm_memory": (By.ID, "host_compute_attributes_memory"),
    "host.vm_start": (By.ID, "host_compute_attributes_start"),
    "host.vm_addstorage": (
        By.XPATH, "//fieldset[@id='storage_volumes']/a"),
    "host.vm_addnic": (
        By.XPATH, "//fieldset[@id='network_interfaces']/a"),


    #Provisions

    #provision.primary
    "provision.template_new": (
        By.XPATH, "//a[contains(@href, '/config_templates/new')]"),
    "provision.template_select": (
        By.XPATH,
        ("//a[contains(@href, 'config_templates')"
            "and normalize-space(.)='%s']")),
    "provision.template_name": (
        By.ID, "config_template_name"),
    "provision.template_template": (
        By.XPATH, "//input[@id='config_template_template']"),
    "provision.template_delete": (
        By.XPATH, "//a[contains(@data-confirm, '%s')]"),

    #provision.type
    "provision.template_type": (
        By.ID, "config_template_template_kind_id"),
    "provision.template_snippet": (
        By.ID, "config_template_snippet"),

    #provision.association
    "provision.select_os": (
        By.XPATH, "//li/span[contains(., '%s')]"),
    "provision.associate_os": (
        By.XPATH,
        ("//label[@class='operatingsystem'"
            "and contains(., '%s')]/input[@type='checkbox']")),

    # Hostgroups

    "hostgroups.new": (By.XPATH, "//a[contains(@href, '/hostgroups/new')]"),
    "hostgroups.name": (By.ID, "hostgroup_name"),
    "hostgroups.parent": (By.ID, "hostgroup_parent_id"),
    "hostgroups.environment": (By.ID, "hostgroup_environment_id"),
    "hostgroups.hostgroup": (By.XPATH, "//a[contains(.,'%s')]"),
    "hostgroups.dropdown": (
        By.XPATH,
        ("//a[contains(@href,'%s')]"
            "/../../a[contains(@data-toggle,'dropdown')]")),
    "hostgroups.delete": (
        By.XPATH,
        "//a[contains(@href,'%s') and contains(@class,'delete')]"),

    #Users

    # Users.primary
    "users.new": (By.XPATH, "//a[contains(@href, '/users/new')]"),
    "users.username": (By.ID, "user_login"),
    "users.firstname": (By.ID, "user_firstname"),
    "users.lastname": (By.ID, "user_lastname"),
    "users.email": (By.ID, "user_mail"),
    "users.language": (By.ID, "user_locale"),
    "users.authorized_by": (By.ID, "user_auth_source_id"),
    "users.password": (By.ID, "user_password"),
    "users.password_confirmation": (By.ID, "user_password_confirmation"),
    "users.user": (By.XPATH, "//a[contains(., '%s')]"),
    "users.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),

    #users.roles
    "users.admin_role": (By.ID, "user_admin"),

    #User Groups
    "usergroups.new": (By.XPATH, "//a[contains(@href, '/usergroups/new')]"),
    "usergroups.name": (By.ID, "usergroup_name"),
    "usergroups.usergroup": (By.XPATH, "//a[contains(., '%s')]"),
    "usergroups.delete": (
        By.XPATH, "//a[@class='delete' and contains(@data-confirm, '%s')]"),

    #Roles
    "roles.new": (By.XPATH, "//a[contains(@href, '/roles/new')]"),
    "roles.name": (By.ID, "role_name"),
    "roles.delete": (By.XPATH,
                     "//a[@class='delete' and contains(@data-confirm, '%s')]"),
    "roles.role": (By.XPATH, "//a[contains(., '%s')]"),
    "roles.perm_filter": (By.XPATH,
                          "//input[@placeholder='Filter permissions']"),
    "roles.perm_type": (By.XPATH, "//label[contains(., '%s')]"),
    "roles.permission": (By.XPATH, "//input[@value='%s']"),

    #Architecture
    "arch.new": (By.XPATH, "//a[contains(@href, '/architectures/new')]"),
    "arch.name": (By.ID, "architecture_name"),
    "arch.delete": (By.XPATH, "//a[contains(@href, '/architectures/%s')]"),
    "arch.arch_name": (By.XPATH, "//a[contains(., '%s')]"),

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
    "domain.domain_description": (By.XPATH, "//a[contains(., '%s')]"),

    #Environment
    "env.new": (By.XPATH, "//a[contains(@href, '/environments/new')]"),
    "env.name": (By.ID, "environment_name"),
    "env.delete": (
        By.XPATH,
        "//a[contains(@href,'%s') and contains(.,'Delete')]"),
    "env.env_name": (By.XPATH, "//a[normalize-space(.)='%s']"),
    "env.dropdown": (
        By.XPATH,
        "//a[contains(@href,'%s') and contains(.,'Classes')]/../../a"),

    #Partition Table
    "ptable.new": (By.XPATH, "//a[contains(@href, '/ptables/new')]"),
    "ptable.name": (By.ID, "ptable_name"),
    "ptable.layout": (By.ID, "ptable_layout"),
    "ptable.os_family": (By.ID, "ptable_os_family"),
    "ptable.delete": (By.XPATH, "//a[contains(@data-confirm, '%s')]"),
    "ptable.ptable_name": (By.XPATH, "//a[normalize-space(.)='%s']"),

    # Subnet Page
    "subnet.new": (By.XPATH, "//a[@class='btn btn-success']"),
    "subnet.name": (By.ID, "subnet_name"),
    "subnet.network": (By.ID, "subnet_network"),
    "subnet.mask": (By.ID, "subnet_mask"),
    "subnet.display_name": (By.XPATH, "//a[contains(., '%s')]"),
    "subnet.delete": (
        By.XPATH,
        "//a[@class='delete' and contains(@data-confirm, '%s')]"),

    # Activation Keys
    "ak.new": (By.XPATH, "//button[@ui-sref='activation-keys.new']"),
    "ak.name": (By.ID, "name"),
    "ak.label": (By.ID, "label"),
    "ak.description": (By.ID, "description"),
    "ak.env": (
        By.XPATH,
        "//input[@ng-model='item.selected']/parent::label[contains(., '%s')]"),
    "ak.content_view": (By.ID, "content_view_id"),
    "ak.usage_limit_checkbox": (
        By.XPATH,
        "//input[@ng-checked='isUnlimited(activationKey)']"),
    "ak.usage_limit": (
        By.XPATH, "//input[@ng-model='activationKey.usage_limit']"),
    "ak.create": (
        By.XPATH,
        "//button[@ng-click='handleSave(); working = true']"),
    "ak.close": (
        By.XPATH,
        "//button[@ui-sref='activation-keys.index']"),
    "ak.search": (By.XPATH, "//input[@ng-model='table.searchTerm']"),
    "ak.search_button": (
        By.XPATH,
        "//button[@ng-click='table.search(table.searchTerm)']"),
    "ak.ak_name": (
        By.XPATH,
        "//tr[@row-select='activationKey']/td[2]/a[contains(., '%s')]"),
    "ak.select_ak_name": (
        By.XPATH,
        "//input[@ng-model='activationKey.selected']"),
    "ak.edit_name": (
        By.XPATH, "//form[@alch-edit-text='activationKey.name']//div/span/i"),
    "ak.edit_name_text": (
        By.XPATH,
        "//form[@alch-edit-text='activationKey.name']/div/input"),
    "ak.save_name": (
        By.XPATH,
        "//form[@alch-edit-text='activationKey.name']\
        //button[@ng-click='save()']"),
    "ak.edit_description": (
        By.XPATH,
        "//form[@alch-edit-textarea='activationKey.description']//div/span/i"),
    "ak.edit_description_text": (
        By.XPATH,
        "//form[@alch-edit-textarea='activationKey.description']\
        /div/textarea"),
    "ak.save_description": (
        By.XPATH,
        "//form[@alch-edit-textarea='activationKey.description']\
        //button[@ng-click='save()']"),
    "ak.edit_limit": (
        By.XPATH, "//div[@alch-edit-custom='activationKey.usage_limit']\
        //div/span/i"),
    "ak.save_limit": (
        By.XPATH,
        "//div[@alch-edit-custom='activationKey.usage_limit']\
        //button[@ng-click='save()']"),
    "ak.edit_content_view": (
        By.XPATH, "//form[@alch-edit-select='activationKey.content_view.name']\
        //div/span/i"),
    "ak.edit_content_view_select": (
        By.XPATH, "//form[@alch-edit-select='activationKey.content_view.name']\
        /select"),

    # Lifecycle Envionments
    "content_env.new": (
        By.XPATH, "//button[@ng-click='initiateCreatePath()']"),
    "content_env.create_initial": (
        By.XPATH, "//label[@ng-click='initiateCreateEnvironment()']"),
    "content_env.name": (By.ID, "name"),
    "content_env.label": (By.ID, "label"),
    "content_env.description": (By.ID, "description"),
    "content_env.create": (
        By.XPATH,
        "//button[@ng-click='handleSave(); working = true']"),
    "content_env.select_name": (
        By.XPATH,
        "//div[contains(., '%s')]/parent::label\
        [@ng-click='selectEnvironment(env.environment)']"),
    "content_env.remove": (
        By.XPATH,
        "//button[@ng-click='openModal()']"),
    "content_env.confirm_remove": (
        By.XPATH,
        "//div[@class='modal-dialog']//button[@ng-click='ok()']"),
    "content_env.env_link": (
        By.XPATH,
        ("//li/label/div[contains(., '%s')]"
         "/following::li/label[@ng-click='initiateCreateEnvironment()']/i")),
    "content_env.edit_name": (
        By.XPATH,
        "//div[@ng-click='edit()']/span[2]/i"),
    "content_env.edit_name_text": (
        By.XPATH,
        "//form[@alch-edit-text='workingOn.environment.name']/div/input"),
    "content_env.save_name": (
        By.XPATH,
        ("//form[@alch-edit-text='workingOn.environment.name']"
         "//button[@ng-click='save()']")),
    "content_env.edit_description": (
        By.XPATH,
        ("//form[@alch-edit-textarea='workingOn.environment.description']"
         "//div/span/i")),
    "content_env.edit_description_text": (
        By.XPATH,
        ("//form[@alch-edit-textarea='workingOn.environment.description']"
         "/div/textarea")),
    "content_env.save_description": (
        By.XPATH,
        ("//form[@alch-edit-textarea='workingOn.environment.description']"
         "//button[@ng-click='save()']")),
    }
