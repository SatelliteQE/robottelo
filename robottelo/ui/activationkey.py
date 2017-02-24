# -*- encoding: utf-8 -*-
"""Implements Activation keys UI."""
from robottelo.constants import DEFAULT_CV
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class ActivationKey(Base):
    """Manipulates Activation keys from UI."""
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Activation Key entity page"""
        Navigator(self.browser).go_to_activation_keys()

    def _search_locator(self):
        """Specify locator for Activation Key entity search procedure"""
        return locators['ak.ak_name']

    def create(self, name, env, limit=None, description=None,
               content_view=None):
        """Creates new activation key from UI."""
        self.click(locators['ak.new'])
        self.assign_value(common_locators['name'], name)
        if limit:
            self.set_limit(limit)
        if description:
            self.assign_value(common_locators['description'], description)
        if env:
            self.click(locators['ak.env'] % env)
        if content_view:
            self.assign_value(locators['ak.content_view'], content_view)
        else:
            self.assign_value(locators['ak.content_view'], DEFAULT_CV)
        self.click(common_locators['create'])

    def search_key_subscriptions(self, ak_name, subscription_name):
        """Fetch associated subscriptions from selected activation key"""
        self.search_and_click(ak_name)
        self.click(tab_locators['ak.subscriptions'])
        self.assign_value(
            locators['ak.subscriptions.search'], subscription_name)
        return self.wait_until_element(
            (locators['ak.get_subscription_name'] % subscription_name))

    def search_host(self, ak_name, host_name):
        """Search for host activated by selected activation key."""
        self.search_and_click(ak_name)
        self.click(tab_locators['ak.associations'])
        self.click(locators['ak.content_hosts'])
        self.assign_value(common_locators['kt_table_search'], host_name)
        self.click(common_locators['kt_table_search_button'])
        return self.wait_until_element(
            locators['ak.content_host_select'] % host_name)

    def update(self, name, new_name=None, description=None,
               limit=None, content_view=None, env=None):
        """Updates an existing activation key."""
        self.search_and_click(name)
        if new_name:
            self.edit_entity(
                locators['ak.edit_name'],
                locators['ak.edit_name_text'],
                new_name,
                locators['ak.save_name']
            )
        if description:
            self.edit_entity(
                locators['ak.edit_description'],
                locators['ak.edit_description_text'],
                description,
                locators['ak.save_description']
            )
        if limit:
            self.click(locators['ak.edit_limit'])
            self.set_limit(limit)
            if self.wait_until_element(
                    locators['ak.save_limit']).is_enabled():
                self.click(locators['ak.save_limit'])
            else:
                raise ValueError(
                    'Please update content host limit with valid integer '
                    'value'
                )
        if content_view:
            if env:
                self.click(locators['ak.env'] % env)
            # If we update the env edit button disappears, but when we update
            # only CV, then edit button appears; Following 'If' is just solving
            # this purpose and hence no else required here
            if self.wait_until_element(locators['ak.edit_content_view']):
                self.click(locators['ak.edit_content_view'])
            self.select(
                locators['ak.edit_content_view_select'], content_view)
            self.click(locators['ak.save_cv'])

    def delete(self, name, really=True):
        """Deletes an existing activation key."""
        self.delete_entity(
            name,
            really,
            locators['ak.remove'],
        )

    def associate_product(self, name, products):
        """Associate an existing product with activation key."""
        self.search_and_click(name)
        self.click(tab_locators['ak.subscriptions'])
        self.click(tab_locators['ak.subscriptions_add'])
        for product in products:
            self.click(locators['ak.select_subscription'] % product)
        self.click(locators['ak.add_selected_subscription'])

    def enable_repos(self, name, repos, enable=True):
        """Enables repository via product_content tab of the activation_key."""
        self.search_and_click(name)
        self.click(tab_locators['ak.tab_prd_content'])
        for repo in repos:
            self.click(locators['ak.prd_content.edit_repo'] % repo)
            if enable:
                self.assign_value(
                    locators['ak.prd_content.select_repo'] % repo,
                    'Override to Yes'
                )
            else:
                self.assign_value(
                    locators['ak.prd_content.select_repo'] % repo,
                    'Override to No'
                )
            self.click(common_locators['save'], ajax_timeout=60)
            # FIXME: check for the success message

    def get_attribute(self, name, locator):
        """Get the attribute of selected locator."""
        self.search_and_click(name)
        if self.wait_until_element(locator):
            return self.find_element(locator).text
        else:
            raise UIError(
                'Could not get text attribute of a given locator'
            )

    def add_host_collection(self, name, host_collection_name):
        """Associate an existing Host Collection with Activation Key."""
        # find activation key
        self.search_and_click(name)
        self.click(tab_locators['ak.host_collections'])
        self.click(tab_locators['ak.host_collections.add'])

        # select host collection
        self.click(
            tab_locators['ak.host_collections.add.select']
            % host_collection_name
        )

        # add host collection
        self.click(tab_locators['ak.host_collections.add.add_selected'])

    def remove_host_collection(self, name, host_collection_name):
        """Remove an existing Host Collection from Activation Key."""
        # find activation key
        self.search_and_click(name)
        self.click(tab_locators['ak.host_collections'])
        self.click(tab_locators['ak.host_collections.list'])
        # select host collection
        self.click(
            tab_locators['ak.host_collections.add.select']
            % host_collection_name)
        # add host collection
        self.click(
            tab_locators['ak.host_collections.list.remove_selected'])

    def fetch_associated_content_host(self, name):
        """Fetch associated content host from selected activation key."""
        self.search_and_click(name)
        self.click(tab_locators['ak.associations'])
        self.click(locators['ak.content_hosts'])
        return self.wait_until_element(locators['ak.content_host_name']).text

    def fetch_product_contents(self, name):
        """Fetch associated product content from selected activation key."""
        self.search_and_click(name)
        self.click(tab_locators['ak.tab_prd_content'])
        return [
            el.text for el
            in self.find_elements(locators['ak.product_contents'])
        ]

    def copy(self, name, new_name=None):
        """Copies an existing activation key"""
        self.search_and_click(name)
        self.edit_entity(
            locators['ak.copy'],
            locators['ak.copy_name'],
            new_name,
            locators['ak.copy_create'],
        )
