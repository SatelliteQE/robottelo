# -*- encoding: utf-8 -*-
"""Implements Host Collection UI."""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class HostCollection(Base):
    """Provides the CRUD functionality for Host Collection."""
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Host Collection entity page"""
        Navigator(self.browser).go_to_host_collections()

    def _search_locator(self):
        """Specify locator for Host Collection entity search procedure"""
        return locators['hostcollection.select_name']

    def create(self, name, limit=None, description=None):
        """Creates new Host Collection from UI."""
        self.click(locators['hostcollection.new'])
        self.assign_value(common_locators['name'], name)
        if limit:
            self.set_limit(limit)
        if description:
            self.assign_value(common_locators['description'], description)
        self.click(common_locators['create'])

    def update(self, name, new_name=None, description=None, limit=None):
        """Updates an existing Host Collection."""
        self.search_and_click(name)
        if new_name:
            self.edit_entity(
                locators['hostcollection.edit_name'],
                locators['hostcollection.edit_name_text'],
                new_name,
                common_locators['save']
            )
        if description:
            self.edit_entity(
                locators['hostcollection.edit_description'],
                locators['hostcollection.edit_description_text'],
                description,
                common_locators['save']
            )
        if limit:
            self.click(locators['hostcollection.edit_limit'])
            self.set_limit(limit)
            if self.wait_until_element(common_locators['save']).is_enabled():
                self.click(common_locators['save'])
            else:
                raise ValueError(
                    'Please update content host limit with valid integer '
                    'value'
                )

    def validate_field_value(self, name, field_name, field_value):
        """Validate whether corresponding Host Collection field has expected
        value

        :param str name: Host Collection name
        :param str field_name: Field to be validated (supported fields: 'name',
            'description', 'limit')
        :param str field_value: Expected field value
        :return bool result: Return True in case field contains expected value
            and False otherwise
        """
        self.search_and_click(name)
        loc = locators['hostcollection.{0}_field'.format(field_name)]
        return self.wait_until_element(loc % field_value)

    def copy(self, name, new_name):
        """Copies an existing Host Collection entity"""
        self.search_and_click(name)
        self.perform_entity_action('Copy Host Collection')
        self.assign_value(common_locators['copy_name_input'], new_name)
        self.click(common_locators['copy_create_button'])

    def add_host(self, name, host_name):
        """Add content host to existing Host Collection entity."""
        host_name = host_name.lower()
        self.search_and_click(name)
        self.click(tab_locators['hostcollection.hosts'])
        self.click(tab_locators['hostcollection.tab_host_add'])
        loc = locators['hostcollection.select_host']
        self.click(loc % host_name)
        self.click(locators['hostcollection.add_host'])
        self.click(tab_locators['hostcollection.tab_host_remove'])
        element = self.wait_until_element(loc % host_name, timeout=8)
        if element is None:
            raise UIError("Adding host {0} is failed".format(host_name))

    def execute_bulk_package_action(self,
                                    name,
                                    action_name,
                                    action_type='package',
                                    action_value=None,
                                    action_via='katello_agent',
                                    org_name=None):
        """Execute remote package action on a host collection

        :param name: hostcollection name to remotely execute package action on
        :param action_name: remote action to execute. Can be one of 4:
            'update all', 'install', 'update', 'remove'
        :param action_type: type of package. can be one of 2:
            'package' or 'package_group'
        :param action_value: Package or package group name to remotely
            install/update/remove (depending on `action_name`)
        :param action_via: the way to perform the action. Can be one of 3:
            'katello_agent', 'remote_execution', 'remote_execution_custom'
        :param org_name: The name of the organization for context, it is an
            optional param since org can be previously selected on session
        :raise: UIError if remote task finished by timeout

        :return: Returns a string containing task status
        """

        if action_name != 'update all' and not action_value:
            raise AttributeError('package or group name is required')

        if org_name:
            Navigator(self.browser).go_to_select_org(org_name, force=False)

        self.search_and_click(name)
        self.click(locators['hostcollection.collection_actions.packages'])

        if action_value:
            type_loc = "contenthost.bulk_actions.{0}_type".format(action_type)
            self.click(locators[type_loc])
            self.assign_value(
                locators['contenthost.bulk_actions.package_name_input'],
                action_value
            )

        strategy, action_link_locator_path = locators[
            'contenthost.bulk_actions.via_{0}'.format(action_via)]
        action_link_locator_path = action_link_locator_path % action_name
        action_link_locator = (strategy, action_link_locator_path)

        strategy, value = locators['contenthost.bulk_actions.action_dropdown']
        self.click((strategy, value % action_link_locator_path))
        self.click(action_link_locator)

        result = self.wait_until_element(
            locators['contenthost.bulk_actions.remote_action_scheduled']
        )  # this alert box fades after 2 seconds

        if result is None:
            raise UIError('Timeout waiting for package action to schedule')

        self.click(locators["hostcollection.collection_actions.modal_dismiss"])

    def execute_bulk_errata_installation(self,
                                         name,
                                         errata_id,
                                         action_via='katello_agent',
                                         timeout=120,
                                         org_name=None):
        """Execute errata installation on a host collection

        :param name: host collection name to install errata on
        :param errata_id: errata id, e.g. 'RHEA-2012:0055'
        :param action_via: the way to perform the action. Can be one of 3:
            'katello_agent', 'remote_execution', 'remote_execution_custom'
        :param timeout: Timeout in seconds for errata installation task to
            finish
        :param org_name: The name of the organization for context, it is an
            optional param since org can be previously selected on session
        :raise: UIError if remote task finished by timeout

        :return: Returns a string containing task status
        """
        if org_name:
            Navigator(self.browser).go_to_select_org(org_name, force=False)

        self.click(self.search(name))
        self.click(locators['hostcollection.collection_actions.errata'])

        self.click(locators['hostcollection.errata.errata_select'] % errata_id)

        strategy, action_link_locator_path = locators[
            'contenthost.bulk_actions.errata.via_{0}'.format(action_via)]

        strategy, value = locators['contenthost.bulk_actions.action_dropdown']
        self.click((strategy, value % action_link_locator_path))
        self.click((strategy, action_link_locator_path))

        result = self.wait_until_element(
            locators['contenthost.remote_action_finished'],
            timeout=timeout,
        )
        if result is None:
            raise UIError('Timeout waiting for errata installation to finish')
        return result.get_attribute('type')

    def change_assigned_content(self, name, lce_name, cv_name, timeout=120):
        """Change assigned life cycle environment and content view of host
        collection

        :param name: the host collection name
        :param cv_name: the content view name to assign
        :param lce_name: the life cycle environment to assign
        :param timeout: Timeout in seconds for content change task to finish
        :raise: UIError if remote task finished by timeout

        :return: Returns a string containing task status
        """
        self.click(self.search(name))
        self.click(tab_locators['hostcollection.details'])
        self.click(locators['contenthost.bulk_actions.environment_content'])
        self.click(
            locators[
                'contenthost.bulk_actions.environment_checkbox'] % lce_name,
            lce_name
        )
        self.assign_value(
            locators['contenthost.bulk_actions.content_view_select'],
            cv_name
        )
        self.click(
            locators['contenthost.bulk_actions.environment_content_assign'])
        self.click(
            locators['contenthost.bulk_actions.environment_content_confirm'])
        result = self.wait_until_element(
            locators['contenthost.remote_action_finished'],
            timeout=timeout,
        )
        if result is None:
            raise UIError('Timeout waiting for content change to finish')
        return result.get_attribute('type')
