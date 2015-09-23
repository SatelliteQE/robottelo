# -*- encoding: utf-8 -*-
"""Implements Org UI"""

from robottelo.constants import FILTER
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class Org(Base):
    """Provides the CRUD functionality for Organization."""

    def _configure_org(self, users=None, proxies=None, subnets=None,
                       resources=None, medias=None, templates=None,
                       domains=None, envs=None, hostgroups=None,
                       locations=None, new_users=None, new_proxies=None,
                       new_subnets=None, new_resources=None, new_medias=None,
                       new_templates=None, new_domains=None,
                       new_envs=None, new_hostgroups=None, new_locations=None,
                       select=None):
        """Configures different entities of selected organization."""

        loc = tab_locators

        if users or new_users:
            self.configure_entity(users, FILTER['org_user'],
                                  tab_locator=loc['context.tab_users'],
                                  new_entity_list=new_users,
                                  entity_select=select)
        if proxies or new_proxies:
            self.configure_entity(proxies, FILTER['org_proxy'],
                                  tab_locator=loc['context.tab_sm_prx'],
                                  new_entity_list=new_proxies,
                                  entity_select=select)
        if subnets or new_subnets:
            self.configure_entity(subnets, FILTER['org_subnet'],
                                  tab_locator=loc['context.tab_subnets'],
                                  new_entity_list=new_subnets,
                                  entity_select=select)
        if resources or new_resources:
            self.configure_entity(resources, FILTER['org_resource'],
                                  tab_locator=loc['context.tab_resources'],
                                  new_entity_list=new_resources,
                                  entity_select=select)
        if medias or new_medias:
            self.configure_entity(medias, FILTER['org_media'],
                                  tab_locator=loc['context.tab_media'],
                                  new_entity_list=new_medias,
                                  entity_select=select)
        if templates or new_templates:
            self.configure_entity(templates, FILTER['org_template'],
                                  tab_locator=loc['context.tab_template'],
                                  new_entity_list=new_templates,
                                  entity_select=select)
        if domains or new_domains:
            self.configure_entity(domains, FILTER['org_domain'],
                                  tab_locator=loc['context.tab_domains'],
                                  new_entity_list=new_domains,
                                  entity_select=select)
        if envs or new_envs:
            self.configure_entity(envs, FILTER['org_envs'],
                                  tab_locator=loc['context.tab_env'],
                                  new_entity_list=new_envs,
                                  entity_select=select)
        if hostgroups or new_hostgroups:
            self.configure_entity(hostgroups, FILTER['org_hostgroup'],
                                  tab_locator=loc['context.tab_hostgrps'],
                                  new_entity_list=new_hostgroups,
                                  entity_select=select)
        if locations or new_locations:
            self.configure_entity(hostgroups, FILTER['org_location'],
                                  tab_locator=loc['context.tab_locations'],
                                  new_entity_list=new_locations,
                                  entity_select=select)

    def create(self, org_name=None, parent_org=None, label=None, desc=None,
               users=None, proxies=None, subnets=None, resources=None,
               medias=None, templates=None, domains=None, envs=None,
               hostgroups=None, locations=None, select=True):
        """Create Organization in UI."""
        self.click(locators['org.new'])
        if parent_org:
            type_element = self.wait_until_element(locators['org.parent'])
            Select(type_element).select_by_visible_text(parent_org)
        if self.wait_until_element(locators['org.name']):
            self.field_update('org.name', org_name)
        if label:
            self.field_update('org.label', label)
        if desc:
            self.field_update('org.desc', desc)
        self.click(common_locators['submit'])
        edit_locator = self.wait_until_element(locators['org.proceed_to_edit'])
        if edit_locator:
            edit_locator.click()
            self._configure_org(users=users, proxies=proxies,
                                subnets=subnets, resources=resources,
                                medias=medias, templates=templates,
                                domains=domains, envs=envs,
                                hostgroups=hostgroups, locations=locations,
                                select=select)
            self.click(common_locators['submit'])

    def search(self, name):
        """Searches existing Organization from UI."""
        Navigator(self.browser).go_to_org()
        return self.search_entity(name, locators['org.org_name'])

    def update(self, org_name, new_parent_org=None, new_name=None, users=None,
               proxies=None, subnets=None, resources=None, medias=None,
               templates=None, domains=None, envs=None, hostgroups=None,
               locations=None, new_locations=None,
               new_users=None, new_proxies=None, new_subnets=None,
               new_resources=None, new_medias=None, new_templates=None,
               new_domains=None, new_envs=None, new_hostgroups=None,
               select=False, new_desc=None):
        """Update Organization in UI."""
        org_object = self.search(org_name)
        self.wait_for_ajax()
        if org_object is None:
            raise UINoSuchElementError(
                'Unable to find the Organization {0}'.format(org_name))
        org_object.click()
        self.wait_for_ajax()
        if new_name:
            if self.wait_until_element(locators['org.name']):
                self.field_update('org.name', new_name)
        if new_parent_org:
            type_element = self.find_element(locators['org.parent'])
            Select(type_element).select_by_visible_text(new_parent_org)
        if new_desc:
            self.field_update('org.desc', new_desc)
        self._configure_org(
            users=users, proxies=proxies,
            subnets=subnets, resources=resources,
            medias=medias, templates=templates,
            domains=domains, envs=envs,
            hostgroups=hostgroups,
            locations=locations,
            new_locations=new_locations,
            new_users=new_users,
            new_proxies=new_proxies,
            new_subnets=new_subnets,
            new_resources=new_resources,
            new_medias=new_medias,
            new_templates=new_templates,
            new_domains=new_domains,
            new_envs=new_envs,
            new_hostgroups=new_hostgroups,
            select=select,
        )
        self.click(common_locators['submit'])

    def remove(self, org_name, really=True):
        """Remove Organization in UI."""
        Navigator(self.browser).go_to_org()
        self.delete_entity(
            org_name,
            really,
            locators['org.org_name'],
            locators['org.delete'],
            drop_locator=locators['org.dropdown'],
        )
