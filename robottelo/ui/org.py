# -*- encoding: utf-8 -*-
"""Implements Org UI"""

from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator


class Org(Base):
    """Provides the CRUD functionality for Organization."""

    def navigate_to_entity(self):
        """Navigate to org entity page"""
        Navigator(self.browser).go_to_org()

    def _search_locator(self):
        """Specify locator for org entity search procedure"""
        return locators['org.org_name']

    def _configure_org(self, users=None, capsules=None, all_capsules=None,
                       subnets=None, resources=None, medias=None,
                       templates=None, ptables=None, domains=None, envs=None,
                       hostgroups=None, locations=None, new_users=None,
                       new_capsules=None, new_subnets=None, new_resources=None,
                       new_medias=None, new_templates=None, new_ptables=None,
                       new_domains=None, new_envs=None, new_hostgroups=None,
                       new_locations=None, select=None):
        """Configures different entities of selected organization."""

        loc = tab_locators

        if users or new_users:
            self.configure_entity(users, FILTER['org_user'],
                                  tab_locator=loc['context.tab_users'],
                                  new_entity_list=new_users,
                                  entity_select=select)
        if capsules or new_capsules:
            self.configure_entity(capsules, FILTER['org_capsules'],
                                  tab_locator=loc['context.tab_capsules'],
                                  new_entity_list=new_capsules,
                                  entity_select=select)
        if all_capsules is not None:
            self.click(tab_locators['context.tab_capsules'])
            self.assign_value(locators['org.all_capsules'], all_capsules)
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
        if ptables or new_ptables:
            self.configure_entity(ptables, FILTER['org_ptable'],
                                  tab_locator=loc['context.tab_ptable'],
                                  new_entity_list=new_ptables,
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

    def create(self, org_name=None, label=None, desc=None, users=None,
               capsules=None, all_capsules=None, subnets=None, resources=None,
               medias=None, templates=None, ptables=None, domains=None,
               envs=None, hostgroups=None, locations=None, select=True):
        """Create Organization in UI."""
        self.click(locators['org.new'])
        self.assign_value(locators['org.name'], org_name)
        if label:
            self.assign_value(locators['org.label'], label)
        if desc:
            self.assign_value(locators['org.desc'], desc)
        self.click(common_locators['submit'])
        edit_locator = self.wait_until_element(locators['org.proceed_to_edit'])
        if edit_locator:
            self.click(edit_locator)
            self._configure_org(
                users=users, capsules=capsules, all_capsules=all_capsules,
                subnets=subnets, resources=resources, medias=medias,
                templates=templates, ptables=ptables, domains=domains,
                envs=envs, hostgroups=hostgroups, locations=locations,
                select=select,
            )
            self.click(common_locators['submit'])

    def update(self, org_name, new_name=None, users=None, capsules=None,
               all_capsules=None, subnets=None, resources=None, medias=None,
               templates=None, ptables=None, domains=None, envs=None,
               hostgroups=None, locations=None, new_locations=None,
               new_users=None, new_capsules=None, new_subnets=None,
               new_resources=None, new_medias=None, new_templates=None,
               new_ptables=None, new_domains=None, new_envs=None,
               new_hostgroups=None, select=False, new_desc=None):
        """Update Organization in UI."""
        self.click(self.search(org_name))
        if new_name:
            self.assign_value(locators['org.name'], new_name)
        if new_desc:
            self.assign_value(locators['org.desc'], new_desc)
        self._configure_org(
            users=users, capsules=capsules,
            all_capsules=all_capsules, subnets=subnets,
            resources=resources, medias=medias,
            templates=templates, ptables=ptables,
            domains=domains, envs=envs,
            hostgroups=hostgroups,
            locations=locations,
            new_locations=new_locations,
            new_users=new_users,
            new_capsules=new_capsules,
            new_subnets=new_subnets,
            new_resources=new_resources,
            new_medias=new_medias,
            new_templates=new_templates,
            new_ptables=new_ptables,
            new_domains=new_domains,
            new_envs=new_envs,
            new_hostgroups=new_hostgroups,
            select=select,
        )
        self.click(common_locators['submit'])

    def delete(self, org_name, really=True):
        """Remove Organization in UI."""
        self.delete_entity(
            org_name,
            really,
            locators['org.delete'],
            drop_locator=locators['org.dropdown'],
        )
