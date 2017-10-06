# -*- encoding: utf-8 -*-
"""Implements Org UI"""

from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator


class Org(Base):
    """Provides the CRUD functionality for Organization."""
    _entity_filter_and_locator_dct = {
        'users': {
            'filter_key': FILTER['org_user'],
            'tab_locator': tab_locators['context.tab_users']
        },
        'capsules': {
            'filter_key': FILTER['org_capsules'],
            'tab_locator': tab_locators['context.tab_capsules']
        },
        'subnets': {
            'filter_key': FILTER['org_subnet'],
            'tab_locator': tab_locators['context.tab_subnets']
        },
        'resources': {
            'filter_key': FILTER['org_resource'],
            'tab_locator': tab_locators['context.tab_resources']
        },
        'medias': {
            'filter_key': FILTER['org_media'],
            'tab_locator': tab_locators['context.tab_media']
        },
        'templates': {
            'filter_key': FILTER['org_template'],
            'tab_locator': tab_locators['context.tab_template']
        },
        'ptables': {
            'filter_key': FILTER['org_ptable'],
            'tab_locator': tab_locators['context.tab_ptable']
        },
        'domains': {
            'filter_key': FILTER['org_domain'],
            'tab_locator': tab_locators['context.tab_domains']
        },
        'envs': {
            'filter_key': FILTER['org_envs'],
            'tab_locator': tab_locators['context.tab_env']
        },
        'hostgroups': {
            'filter_key': FILTER['org_hostgroup'],
            'tab_locator': tab_locators['context.tab_hostgrps']
        },
        'locations': {
            'filter_key': FILTER['org_location'],
            'tab_locator': tab_locators['context.tab_locations']
        },
    }

    def add_entity(self, org_name, entity_type, entity_name):
        """Helper to add an entity to an existing organization.
        Return ui entity on list so it can be used on tests. If it is not None
        entity was added

        :param org_name: name of Organization
        :param entity_type: Entity's name param for self.update
        :param entity_name: Entity's name
        :return entity: ui element
        """
        kwargs = {entity_type: [entity_name]}
        self.update(org_name, select=True, **kwargs)
        self.search_and_click(org_name)
        tab_locator = self._entity_filter_and_locator_dct[entity_type][
            'tab_locator']
        self.click(tab_locator)
        return self.wait_until_element(
            common_locators['entity_deselect'] % entity_name)

    def remove_entity(self, org_name, entity_type, entity_name):
        """Helper to remove an entity from an existing organization.
        Return ui entity on list so it can be used on tests. If it is not None
        entity was removed

        :param org_name: name of Organization
        :param entity_type: Entity's name param for self.update
        :param entity_name: Entity's name
        :return entity: ui element
        """
        kwargs = {entity_type: [entity_name]}
        self.update(org_name, **kwargs)
        self.search_and_click(org_name)
        tab_locator = self._entity_filter_and_locator_dct[entity_type][
            'tab_locator']
        self.click(tab_locator)
        return self.wait_until_element(
            common_locators['entity_select'] % entity_name)

    def create_with_entity(self, org_name, entity_type, entity_name):
        """Helper function to assert Organization creation with related
        entities

        :param org_name: Organization's name to be created
        :param entity_type: one of following entities: users
        :param entity_name: Entity's name
        :return entity: element on screen if present. So assertIsNotNone can
                be used to test entity successful attachment
        """
        self.navigate_to_entity()
        kwargs = {entity_type: [entity_name]}
        self.create(org_name, **kwargs)
        self.search_and_click(org_name)
        tab_locator = self._entity_filter_and_locator_dct[entity_type][
            'tab_locator']
        self.click(tab_locator)
        return self.wait_until_element(
            common_locators['entity_deselect'] % entity_name)

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
                       new_locations=None, params=None, new_params=None,
                       select=None):
        """Configures different entities of selected organization."""
        if users or new_users:
            self.configure_entity(
                users,
                new_entity_list=new_users,
                entity_select=select,
                **self._entity_filter_and_locator_dct['users']
            )
        if capsules or new_capsules:
            self.configure_entity(
                capsules,
                new_entity_list=new_capsules,
                entity_select=select,
                **self._entity_filter_and_locator_dct['capsules'])
        if all_capsules is not None:
            self.click(tab_locators['context.tab_capsules'])
            self.assign_value(locators['org.all_capsules'], all_capsules)
        if subnets or new_subnets:
            self.configure_entity(
                subnets,
                new_entity_list=new_subnets,
                entity_select=select,
                **self._entity_filter_and_locator_dct['subnets'])
        if resources or new_resources:
            self.configure_entity(
                resources,
                new_entity_list=new_resources,
                entity_select=select,
                **self._entity_filter_and_locator_dct['resources'])
        if medias or new_medias:
            self.configure_entity(
                medias,
                new_entity_list=new_medias,
                entity_select=select,
                **self._entity_filter_and_locator_dct['medias'])
        if templates or new_templates:
            self.configure_entity(
                templates,
                new_entity_list=new_templates,
                entity_select=select,
                **self._entity_filter_and_locator_dct['templates'])
        if ptables or new_ptables:
            self.configure_entity(
                ptables,
                new_entity_list=new_ptables,
                entity_select=select,
                **self._entity_filter_and_locator_dct['ptables'])
        if domains or new_domains:
            self.configure_entity(
                domains,
                new_entity_list=new_domains,
                entity_select=select,
                **self._entity_filter_and_locator_dct['domains'])
        if envs or new_envs:
            self.configure_entity(
                envs,
                new_entity_list=new_envs,
                entity_select=select,
                **self._entity_filter_and_locator_dct['envs'])
        if hostgroups or new_hostgroups:
            self.configure_entity(
                hostgroups,
                new_entity_list=new_hostgroups,
                entity_select=select,
                **self._entity_filter_and_locator_dct['hostgroups'])
        if locations or new_locations:
            self.configure_entity(
                locations,
                new_entity_list=new_locations,
                entity_select=select,
                **self._entity_filter_and_locator_dct['locations'])
        if params or new_params:
            for param in (params or new_params):
                self.set_parameter(*param, submit=False)

    def create(self, org_name=None, label=None, desc=None, users=None,
               capsules=None, all_capsules=None, subnets=None, resources=None,
               medias=None, templates=None, ptables=None, domains=None,
               envs=None, hostgroups=None, locations=None, params=None,
               select=True):
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
                select=select, params=params,
            )
            self.click(common_locators['submit'])

    def update(self, org_name, new_name=None, users=None, capsules=None,
               all_capsules=None, subnets=None, resources=None, medias=None,
               templates=None, ptables=None, domains=None, envs=None,
               hostgroups=None, locations=None, new_locations=None,
               new_users=None, new_capsules=None, new_subnets=None,
               new_resources=None, new_medias=None, new_templates=None,
               new_ptables=None, new_domains=None, new_envs=None,
               new_hostgroups=None, select=False, new_desc=None,
               new_params=None):
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
            new_params=new_params,
            select=select,
        )
        self.click(common_locators['submit'])
