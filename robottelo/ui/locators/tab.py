# -*- encoding: utf-8 -*-
"""Implements different locators for UI"""

from selenium.webdriver.common.by import By
from .model import LocatorDict


tab_locators = LocatorDict({

    # common
    "tab_primary": (By.XPATH, "//a[@href='#primary']"),
    # Third level UI
    "tab_loc": (By.XPATH, "//a[@href='#locations']"),
    "tab_org": (By.XPATH, "//a[@href='#organizations']"),

    # Operating System
    # Third level UI
    "operatingsys.tab_primary": (By.XPATH, "//a[@href='#primary']"),
    "operatingsys.tab_ptable": (By.XPATH, "//a[@href='#ptable']"),
    "operatingsys.tab_medium": (By.XPATH, "//a[@href='#media']"),
    "operatingsys.tab_templates": (By.XPATH, "//a[@href='#templates']"),
    "operatingsys.tab_parameters": (By.XPATH, "//a[@href='#params']"),
    "operatingsys.tab_provision_bootdisk": (
        By.XPATH, ".//*[@id='host_provision_method_bootdisk']"),
    "operatingsys.tab_provision_network": (
        By.XPATH, ".//*[@id='host_provision_method_build']"),
    "operatingsys.tab_provision_image": (
        By.XPATH, ".//*[@id='host_provision_method_image']"),

    # Host
    # Third level UI

    "host.tab_host": (By.XPATH, "//a[@href='#primary']"),
    "host.tab_puppet_classes": (By.XPATH, "//a[@href='#puppet_klasses']"),
    "host.tab_interfaces": (By.XPATH, "//a[@href='#network']"),
    "host.tab_operating_system": (
        By.XPATH, ("//form[@id='new_host' or contains(@id,'edit_host')]"
                   "//a[@href='#os']")),
    "host.tab_virtual_machine": (
        By.XPATH, ("//form[@id='new_host' or contains(@id,'edit_host')]"
                   "//a[@href='#compute_resource']")),
    "host.tab_params": (By.XPATH, "//a[@href='#params']"),
    "host.tab_additional_information": (By.XPATH, "//a[@href='#info']"),

    # Hostgroup
    # Third level UI

    "hostgroup.tab_host_group": (By.XPATH, "//a[@href='#primary']"),
    "hostgroup.tab_ansible_roles": (By.XPATH, "//a[@href='#ansible_roles']"),
    "hostgroup.tab_puppet_classes": (By.XPATH, "//a[@href='#puppet_klasses']"),
    "hostgroup.tab_network": (By.XPATH, "//a[@href='#network']"),
    "hostgroup.tab_operating_system": (By.XPATH, ("//a[@href='#os']")),
    "hostgroup.tab_parameters": (By.XPATH, "//a[@href='#params']"),
    "hostgroup.tab_locations": (By.XPATH, "//a[@href='#locations']"),
    "hostgroup.tab_organizations": (By.XPATH, "//a[@href='#organizations']"),
    "hostgroup.tab_activation_keys": (
        By.XPATH, "//a[@href='#activation_keys']"),

    # Provisioning Templates
    # Third level UI

    "provision.tab_type": (By.XPATH, "//a[@href='#template_type']"),
    "provision.tab_association": (By.XPATH,
                                  "//a[@href='#template_associations']"),
    "provision.tab_history": (By.XPATH, "//a[@href='#history']"),
    "provision.tab_locations": (By.XPATH, "//a[@href='#locations']"),
    "provision.tab_organizations": (By.XPATH, "//a[@href='#organizations']"),

    # Job Templates
    # Third level UI

    "job.tab_job": (By.XPATH, "//a[@href='#template_job']"),
    "job.tab_type": (By.XPATH, "//a[@href='#template_type']"),
    "job.tab_history": (By.XPATH, "//a[@href='#history']"),

    # Users
    # Third level UI

    "users.tab_primary": (By.XPATH, "//a[@href='#primary']"),
    "users.tab_roles": (By.XPATH, "//a[@href='#roles']"),
    "users.tab_locations": (By.XPATH, "//a[@href='#locations']"),
    "users.tab_organizations": (By.XPATH, "//a[@href='#organizations']"),
    "users.tab_filters": (By.XPATH, "//a[@href='#filters']"),

    "prd.tab_details": (
        By.XPATH, ("//a[@class='ng-scope'"
                   " and contains(@ui-sref,'product.info')]")),
    "prd.tab_repos": (
        By.XPATH, "//a[@class='ng-scope'"
                  "and contains(@ui-sref,'product.repositories')]"),
    "prd.tab_tasks": (
        By.XPATH, ("//a[@class='ng-scope'"
                   " and contains(@ui-sref, 'product.tasks')]")),

    # For Orgs and Locations
    "context.tab_users": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'users')]"),
    "context.tab_capsules": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'smart_proxies')]"),
    "context.tab_subnets": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'subnets')]"),
    "context.tab_resources": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'resources')]"),
    "context.tab_media": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'media')]"),
    "context.tab_template": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'provisioning_templates')]"
    ),
    "context.tab_ptable": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'ptables')]"),
    "context.tab_domains": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'domains')]"),
    "context.tab_env": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'environments')]"),
    "context.tab_hostgrps": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'hostgroups')]"),
    "context.tab_locations": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'locations')]"),
    "context.tab_organizations": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'organizations')]"),
    "context.tab_parameters": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href,'params')]"),

    # Roles
    # Second level UI
    "roles.tab_role": (By.XPATH, "//a[@href='#primary']"),
    "roles.tab_filters": (By.XPATH, "//a[@href='#filters']"),
    # Third level UI
    "roles.tab_filter": (
        By.XPATH, "//a[@href='#primary']"),
    "roles.tab_org": (
        By.XPATH, "//a[@href='#organizations']"),
    "roles.tab_location": (
        By.XPATH, "//a[@href='#locations']"),

    # GPG key
    # Third level UI
    "gpgkey.tab_details": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'info')]"),
    "gpgkey.tab_products": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'products')]"),
    "gpgkey.tab_repos": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href,'repositories')]"),

    # Lifecycle Environments
    # Third level UI
    "lce.tab_details": (
        By.XPATH, "//a[contains(@ui-sref, 'environment.details')]"),
    "lce.tab_contentview": (
        By.XPATH, "//a[contains(@href, 'content-views')]"),
    "lce.tab_yum_repos": (
        By.XPATH, "//a[contains(@href, 'repositories')]"),
    "lce.tab_errata": (
        By.XPATH, "//a[contains(@ng-href, 'errata')]"),
    "lce.tab_packages": (
        By.XPATH, "//a[contains(@ng-href, 'packages')]"),
    "lce.tab_puppet_modules": (
        By.XPATH, "//a[contains(@ng-href, 'puppet-modules')]"),

    # Content Views
    # Third level UI
    "contentviews.tab_details": (
        By.XPATH, "//a[@ui-sref='content-view.info']"),
    "contentviews.tab_versions": (
        By.XPATH,
        "//a[@class='ng-scope' and "
        "contains(@ui-sref, 'content-view.versions')]"),
    "contentviews.tab_yum_content": (
        By.XPATH, "//ul/li/a[@class='dropdown-toggle']"
                  "/i[preceding-sibling::span[contains(., 'Yum Content')]]"),
    "contentviews.tab_docker_content": (
        By.XPATH,
        "//ul/li/a[@class='dropdown-toggle']"
        "/i[preceding-sibling::span[contains(., 'Docker Content')]]"),
    "contentviews.tab_content_views": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'content-views')]"),
    "contentviews.tab_file_repositories": (
        By.XPATH,
        "//a[@ui-sref='content-view.repositories.file.list']"),
    "contentviews.tab_puppet_modules": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'puppet_modules')]"),
    "contentviews.tab_ostree_content": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href, 'ostree')]"),
    "contentviews.tab_history": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href, 'history')]"),
    "contentviews.tab_tasks": (
        By.XPATH, "//a[@class='ng-scope' and contains(@href, 'tasks')]"),
    "contentviews.tab_repo_add": (
        By.XPATH,
        "//a[contains(@href, 'repositories') and "
        "contains(@ui-sref, 'available')]"),
    "contentviews.tab_repo_remove": (
        By.XPATH,
        ("//a[contains(@href, 'repositories') and contains(@ui-sref, 'list')]"
         "/span[@class='ng-scope' and contains(., 'List/Remove')]")),
    "contentviews.tab_cv_add": (
        By.XPATH,
        "//a[contains(@ui-sref, 'content-views.available')]"),
    "contentviews.tab_cv_remove": (
        By.XPATH, "//a[contains(@ui-sref, 'content-views.list')]"),
    "contentviews.tab_pkg_group_add": (
        By.XPATH, "//a[contains(@ui-sref, 'package_group.available')]"),
    "contentviews.tab_pkg_group_remove": (
        By.XPATH, "//a[contains(@ui-sref, 'package_group.list')]"),
    "contentviews.tab_add": (
        By.XPATH, "//a[contains(@ui-sref, 'available')]"),
    "contentviews.tab_remove": (
        By.XPATH, "//a[contains(@ui-sref, 'list')]"),
    # Fourth level UI
    "contentviews.tab_filter_affected_repos": (
        By.XPATH,
        "//a[contains(@ui-sref, 'content-view.yum.filter.rpm.repositories')]"),
    "contentviews.tab_version_packages": (
        By.XPATH,
        "//a[contains(@ui-sref, 'content-view.version.packages')]"),
    "contentviews.tab_version_errata": (
        By.XPATH,
        "//a[contains(@ui-sref, 'content-view.version.errata')]"),
    "contentviews.tab_version_puppet_modules": (
        By.XPATH,
        "//a[contains(@ui-sref, "
        "'content-view.version.puppet-modules')]"),

    # Content Hosts
    # Third level UI
    "contenthost.tab_details": (
        By.XPATH, "//a[@class='ng-scope' and contains(@ui-sref, 'info')]"),
    "contenthost.tab_provisioning_details": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href,'provisioning')]"),
    "contenthost.tab_provisioning_details_host_link": (
        By.XPATH,
        "//span[@class='info-value']/a[contains(@href,'hosts')]"),
    "contenthost.tab_subscriptions": (
        By.XPATH,
        ("//li[@class='dropdown' and contains(@ng-class, "
         "'content-host.subscriptions.list')]/a")),
    "contenthost.tab_subscriptions_subscriptions": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href,'subscriptions')]"),
    "contenthost.tab_packages": (
        By.XPATH,
        "//li[@class='dropdown' and contains(@ng-class,'packages')]/a"),
    "contenthost.tab_packages.installed": (
        By.XPATH,
        "//li/a[contains(@ui-sref,'packages.installed')]"),
    "contenthost.tab_packages.applicable": (
        By.XPATH,
        "//li/a[contains(@ui-sref,'packages.applicable')]"),
    "contenthost.tab_packages.actions": (
        By.XPATH,
        "//li/a[contains(@ui-sref,'packages.actions')]"),
    "contenthost.tab_errata": (
        By.XPATH,
        "//a[@class='ng-scope' and contains(@href,'errata')]"),
    # Fourth level UI
    "contenthost.list_subscriptions": (
        By.XPATH,
        ("//a[contains(@ui-sref,'subscriptions.list')]"
         "/span[@class='ng-scope']")),
    "contenthost.add_subscription": (
        By.XPATH,
        ("//a[contains(@ui-sref,'subscriptions.add')]"
         "/span[@class='ng-scope']")),

    # Errata
    "errata.tab_content_hosts": (
        By.XPATH, "//a[@ui-sref='erratum.content-hosts']"),
    "errata.tab_repositories": (
        By.XPATH, "//a[@ui-sref='erratum.repositories']"),

    # Sync Plans
    # Third level UI
    "sp.tab_details": (
        By.XPATH, "//a[@class='ng-scope' and contains(@ui-sref,'info')]"),
    "sp.tab_products": (
        By.XPATH, "//a[@class='ng-scope' and contains(@ui-sref,'products')]"),
    # Fourth level UI
    "sp.list_prd": (
        By.XPATH, "//a[contains(@ui-sref,'list')]/span[@class='ng-scope']"),
    "sp.add_prd": (
        By.XPATH, "//a[contains(@ui-sref,'add')]/span[@class='ng-scope']"),

    # Activation Keys
    # Third level UI
    "ak.details": (
        By.XPATH, "//a[contains(@href, 'info')]"),
    "ak.subscriptions": (
        By.XPATH, "//a[contains(@href, 'subscriptions')]/span"),
    "ak.subscriptions_add": (
        By.XPATH, "//a[contains(@ui-sref, 'subscriptions.add')]"),
    "ak.subscriptions_remove": (
        By.XPATH, "//a[contains(@ui-sref, 'subscriptions.list')]"),
    "ak.host_collections": (
        By.XPATH, "//a[contains(@href, 'host-collections')]"),
    "ak.host_collections.add": (
        By.XPATH, "//a[contains(@ui-sref, 'host-collections.add')]"),
    "ak.host_collections.add.select": (
        By.XPATH,
        "//tr/td/a[contains(., '%s')]"
        "/parent::*/parent::*"
        "/td/input[@ng-model='hostCollection.selected']"),
    "ak.host_collections.add.add_selected": (
        By.XPATH, "//button[@ng-click='addHostCollections()']"),
    "ak.host_collections.list": (
        By.XPATH, "//a[contains(@ui-sref, 'host-collections.list')]"),
    "ak.host_collections.list.remove_selected": (
        By.XPATH, "//button[@ng-click='removeHostCollections()']"),
    "ak.associations": (
        By.XPATH, "//ul/li[@class='dropdown']/a"),
    "ak.tab_repository_sets": (
        By.XPATH, "//a[@ui-sref='activation-key.products']/span/span"),

    # Manifest / subscriptions
    "manifest.tab_rpms": (
        By.XPATH,
        "//div[@id='content_tabs']/ul/li/a[contains(@href, 'rpms')]"),
    "manifest.tab_kickstarts": (
        By.XPATH,
        "//div[@id='content_tabs']/ul/li/a[contains(@href, 'kickstarts')]"),
    "manifest.tab_isos": (
        By.XPATH,
        "//div[@id='content_tabs']/ul/li/a[contains(@href, 'isos')]"),
    "manifest.tab_ostree": (
        By.XPATH,
        "//div[@id='content_tabs']/ul/li/a[contains(@href, 'ostree')]"),
    "subs.tab_details": (
        By.XPATH, "//a[contains(@ui-sref,'manifest.details')]"),
    "subs.tab_import_history": (
        By.XPATH, "//a[contains(@ui-sref,'manifest.history')]"),
    "subs.sub.tab_details": (
        By.XPATH, "//a[contains(@ui-sref,'subscription.info')]"),
    "subs.sub.product_content": (
        By.XPATH, "//a[contains(@ui-sref,'subscription.products')]"),

    # Oscap Policy
    "oscap.content": (
        By.XPATH, "//a[@href='#scap_content']"),
    "oscap.schedule": (
        By.XPATH, "//a[contains(@href, 'scap_schedule')]"),

    # Subnet
    "subnet.tab_domain": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'domains')]"),

    # Settings
    "settings.tab_general": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'General')]"),
    "settings.tab_auth": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Auth')]"),
    "settings.tab_bootdisk": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Bootdisk')]"),
    "settings.tab_puppet": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Puppet')]"),
    "settings.tab_discovered": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Discovered')]"),
    "settings.tab_content": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Content')]"),
    "settings.tab_foremantasks": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href, 'ForemanTasks')]"),
    "settings.tab_provisioning": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href, 'Provisioning')]"),
    "settings.tab_email": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'Email')]"),

    "puppetclass.parameters": (
        By.XPATH, "//a[contains(@href,'class_param')]"),

    # LDAP Authentication
    "ldapserver.tab_account": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'account')]"),
    "ldapserver.tab_attributes": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'attributes')]"),

    # UserGroups
    "usergroups.tab_roles": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'roles')]"),
    "usergroups.tab_external": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'external')]"),

    # Host Collections
    "hostcollection.details": (
        By.XPATH, "//a[contains(@href, 'info')]/span"),
    "hostcollection.hosts": (
        By.XPATH, "//a[contains(@href, 'hosts')]/span"),
    "hostcollection.tab_host_add": (
        By.XPATH,
        "//a[contains(@href, 'add-hosts') and "
        "contains(@ui-sref, 'host-collection.hosts.add')]"),
    "hostcollection.tab_host_remove": (
        By.XPATH,
        "//a[contains(@href, 'hosts') and "
        "contains(@ui-sref, 'host-collection.hosts.list')]"),
    "hostcollection.collection_actions": (
        By.XPATH, "//a[contains(@href, 'actions')]/span"),

    # Compute resources
    "resource.tab_containers": (
        By.XPATH, "//a[@data-toggle='tab' and contains(@href, 'vms')]"),
    "resource.tab_virtual_machines": (By.XPATH, "//a[contains(@href, 'vms')]"),
    "resource.tab_images": (By.XPATH, "//a[.='Images']"),
    "resource.tab_compute_profiles": (
        By.XPATH, "//a[@data-toggle='tab' and @href='#compute_profiles']"),

    # Puppet Class
    "puppet_class.tab_smart_parameter": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href, 'smart_class_param')]"),
    "puppet_class.tab_smart_variable": (
        By.XPATH,
        "//a[@data-toggle='tab' and contains(@href, 'smart_vars')]"),

    # Packages
    "package.tab_details": (
        By.XPATH, "//a[contains(@href, 'info')]/span"),
    "package.tab_files": (
        By.XPATH, "//a[contains(@href, 'files')]/span"),
    "package.tab_dependencies": (
        By.XPATH, "//a[contains(@href, 'dependencies')]/span"),

    # Puppet Module
    "puppet_module.tab_details": (
        By.XPATH, "//a[contains(@href, 'info')]/span"),
    "puppet_module.tab_library_repositories": (
        By.XPATH, "//a[contains(@href, 'repositories')]/span"),
    "puppet_module.tab_content_views": (
        By.XPATH, "//a[contains(@href, 'content_views')]/span"),

    # Task
    "task.tab_task": (
        By.XPATH, "//a[@data-toggle='tab' and @href='#primary']"),
})
