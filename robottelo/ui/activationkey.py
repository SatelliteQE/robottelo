# -*- encoding: utf-8 -*-
"""Implements Activation keys UI."""
from robottelo.constants import DEFAULT_CV
from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators, tab_locators
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

        if self.wait_until_element(common_locators['name']):
            self.text_field_update(common_locators['name'], name)
            if limit:
                self.set_limit(limit)
            if description:
                self.text_field_update(
                    common_locators['description'], description)
            if env:
                strategy, value = locators['ak.env']
                self.click((strategy, value % env))
            else:
                raise UIError(
                    'Could not create new activation key "{0}", without env'
                    .format(name)
                )
            if content_view:
                self.select(locators['ak.content_view'], content_view)
            else:
                self.select(locators['ak.content_view'], DEFAULT_CV)
            self.click(common_locators['create'])
        else:
            raise UIError(
                'Could not create new activation key "{0}"'.format(name)
            )

    def search_key_subscriptions(self, ak_name, subscription_name):
        """Fetch associated subscriptions from selected activation key"""
        self.click(self.search(ak_name))
        self.click(tab_locators['ak.subscriptions'])
        self.text_field_update(
            locators['ak.subscriptions.search'], subscription_name)
        strategy, value = locators['ak.get_subscription_name']
        element = self.wait_until_element(
            (strategy, value % subscription_name))
        return element

    def update(self, name, new_name=None, description=None,
               limit=None, content_view=None, env=None):
        """Updates an existing activation key."""
        self.click(self.search(name))
        if new_name:
            self.edit_entity(locators['ak.edit_name'],
                             locators['ak.edit_name_text'],
                             new_name, locators['ak.save_name'])
        if description:
            self.edit_entity(locators['ak.edit_description'],
                             locators['ak.edit_description_text'],
                             description, locators['ak.save_description'])
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
                strategy, value = locators['ak.env']
                self.click((strategy, value % env))
            # We need to select the CV, if we update the env and in this,
            # case edit button disappears, but when we update only CV, then
            # edit button appears; Following 'If' is just solving this
            # purpose and hence no else required here
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
        self.click(self.search(name))
        self.click(tab_locators['ak.subscriptions'])
        self.click(tab_locators['ak.subscriptions_add'])
        strategy, value = locators['ak.select_subscription']
        for product in products:
            self.click((strategy, value % product))
        self.click(locators['ak.add_selected_subscription'])

    def enable_repos(self, name, repos, enable=True):
        """Enables repository via product_content tab of the activation_key."""
        element = self.search(name)
        strategy, value = locators['ak.prd_content.edit_repo']
        strategy1, value1 = locators['ak.prd_content.select_repo']
        if element is None:
            raise UINoSuchElementError(
                "Couldn't find the selected activation key {0}".format(name))
        element.click()
        self.wait_for_ajax()
        self.click(tab_locators['ak.tab_prd_content'])
        for repo in repos:
            self.click((strategy, value % repo))
            if enable:
                self.select((strategy1, value1 % repo), 'Override to Yes')
            else:
                self.select((strategy1, value1 % repo), 'Override to No')
            self.click(common_locators['save'], ajax_timeout=60)
            # FIXME: check for the success message

    def get_attribute(self, name, locator):
        """Get the attribute of selected locator."""
        self.click(self.search(name))
        if self.wait_until_element(locator):
            result = self.find_element(locator).text
            return result
        else:
            raise UIError(
                'Could not get text attribute of a given locator'
            )

    def add_host_collection(self, name, host_collection_name):
        """Associate an existing Host Collection with Activation Key."""
        # find activation key
        activation_key = self.search(name)
        if activation_key:
            activation_key.click()
            self.wait_for_ajax()
            self.click(tab_locators['ak.host_collections'])
            self.click(tab_locators['ak.host_collections.add'])

            # select host collection
            strategy, value = tab_locators['ak.host_collections.add.select']
            self.click((strategy, value % host_collection_name))

            # add host collection
            self.click(tab_locators['ak.host_collections.add.add_selected'])
        else:
            raise UINoSuchElementError(
                "Couldn't find activation key '{0}'".format(name))

    def remove_host_collection(self, name, host_collection_name):
        """Remove an existing Host Collection from Activation Key."""
        # find activation key
        self.search_and_click(name)
        self.click(tab_locators['ak.host_collections'])
        self.click(tab_locators['ak.host_collections.list'])
        # select host collection
        strategy, value = tab_locators['ak.host_collections.add.select']
        self.click((strategy, value % host_collection_name))
        # add host collection
        self.click(
            tab_locators['ak.host_collections.list.remove_selected'])

    def fetch_associated_content_host(self, name):
        """Fetch associated content host from selected activation key."""
        self.click(self.search(name))
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
        self.click(self.search(name))
        self.edit_entity(
            locators['ak.copy'],
            locators['ak.copy_name'],
            new_name,
            locators['ak.copy_create'],
        )
