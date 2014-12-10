# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Activation keys UI
"""

from robottelo.common.helpers import escape_search
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators, tab_locators
from selenium.webdriver.support.select import Select


class ActivationKey(Base):
    """
    Manipulates Activation keys from UI
    """

    def set_limit(self, limit):
        """
        Sets the finite limit of activation key
        """
        limit_checkbox_locator = locators["ak.usage_limit_checkbox"]
        if limit == 'Unlimited':
            self.find_element(limit_checkbox_locator).click()
        else:
            self.find_element(limit_checkbox_locator).click()
            self.field_update("ak.usage_limit", limit)

    def create(self, name, env, limit=None, description=None,
               content_view=None):
        """
        Creates new activation key from UI
        """

        self.wait_for_ajax()
        self.wait_until_element(locators["ak.new"]).click()

        if self.wait_until_element(common_locators["name"]):
            self.text_field_update(common_locators["name"], name)
            self.wait_for_ajax()
            if limit:
                self.set_limit(limit)
                self.wait_for_ajax()
            if description:
                self.text_field_update(common_locators
                                       ["description"], description)
            if env:
                strategy = locators["ak.env"][0]
                value = locators["ak.env"][1]
                element = self.wait_until_element((strategy, value % env))
                if element:
                    element.click()
                    self.wait_for_ajax()
            else:
                raise Exception(
                    "Could not create new activation key '%s', \
                    without env" % name)
            if content_view:
                Select(self.find_element
                       (locators["ak.content_view"]
                        )).select_by_visible_text(content_view)
            else:
                Select(self.find_element
                       (locators["ak.content_view"]
                        )).select_by_value("0")
            self.wait_until_element(common_locators["create"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new activation key '%s'" % name)

    def search_key(self, element_name):
        """
        Uses the search box to locate an element from a list of elements.
        """

        element = None

        searchbox = self.wait_until_element(common_locators["kt_search"])

        if searchbox:
            searchbox.clear()
            searchbox.send_keys(escape_search(element_name))
            self.wait_for_ajax()
            self.find_element(common_locators["kt_search_button"]).click()
            strategy = locators["ak.ak_name"][0]
            value = locators["ak.ak_name"][1]
            element = self.wait_until_element((strategy, value % element_name))
        return element

    def update(self, name, new_name=None, description=None,
               limit=None, content_view=None, env=None):
        """
        Updates an existing activation key
        """

        element = self.search_key(name)

        if element:
            element.click()
            self.wait_for_ajax()
            if new_name:
                self.edit_entity("ak.edit_name", "ak.edit_name_text",
                                 new_name, "ak.save_name")
            if description:
                self.edit_entity("ak.edit_description",
                                 "ak.edit_description_text",
                                 description, "ak.save_description")
            if limit:
                self.find_element(locators["ak.edit_limit"]).click()
                self.set_limit(limit)
                if self.wait_until_element(locators["ak.save_limit"]
                                           ).is_enabled():
                    self.find_element(locators["ak.save_limit"]).click()
                else:
                    raise ValueError(
                        "Please update content host "
                        "limit with valid integer value")
            if content_view:
                if env:
                    strategy = locators["ak.env"][0]
                    value = locators["ak.env"][1]
                    element = self.wait_until_element((strategy, value % env))
                    if element:
                        element.click()
                        self.wait_for_ajax()
                    else:
                        raise Exception(
                            "Couldn't find the given env '%s'" % env)
                # We need to select the CV, if we update the env and in this,
                # case edit button disappears, but when we update only CV, then
                # edit button appears; Following 'If' is just solving this
                # purpose and hence no else required here
                if self.wait_until_element(locators["ak.edit_content_view"]):
                    self.find_element(locators["ak.edit_content_view"]).click()
                    self.wait_for_ajax()
                Select(self.find_element
                       (locators["ak.edit_content_view_select"]
                        )).select_by_visible_text(content_view)
                self.find_element(locators["ak.save_cv"]).click()
                self.wait_for_ajax()
        else:
            raise Exception("Could not update the activation key '%s'" % name)

    def delete(self, name, really):
        """
        Deletes an existing activation key
        """

        element = self.search_key(name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.wait_until_element(locators["ak.remove"]).click()
            self.wait_for_ajax()
            if really:
                self.wait_until_element(common_locators["confirm_remove"]
                                        ).click()
            else:
                self.wait_until_element(locators["ak.cancel"]).click()

    def associate_product(self, name, products):
        """
        associate an existing product with activation key
        """

        element = self.search_key(name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.wait_until_element(tab_locators["ak.subscriptions"]).click()
            self.wait_until_element(tab_locators
                                    ["ak.subscriptions_add"]).click()
            self.wait_for_ajax()
            strategy, value = locators["ak.select_subscription"]
            for product in products:
                element = self.wait_until_element((strategy, value % product))
                if element:
                    element.click()
                    self.wait_for_ajax()
                else:
                    raise Exception(
                        "Couldn't find the product '%s'"
                        "subscription" % product)
            self.wait_until_element(locators
                                    ["ak.add_selected_subscription"]).click()
        else:
            raise Exception(
                "Couldn't find the selected activation key '%s'" % name)

    def enable_repos(self, name, repos, enable=True):
        """Enables repository via product_content tab of the activation_key."""

        element = self.search_key(name)
        strategy, value = locators["ak.prd_content.edit_repo"]
        strategy1, value1 = locators["ak.prd_content.select_repo"]
        if element is None:
            raise UINoSuchElementError(
                "Couldn't find the selected activation key {0}".format(name))
        element.click()
        self.wait_for_ajax()
        self.wait_until_element(tab_locators["ak.tab_prd_content"]).click()
        self.wait_for_ajax()
        for repo in repos:
            repo_edit = self.wait_until_element((strategy, value % repo))
            if repo_edit is None:
                raise Exception("Couldn't find the repo: {0}".format(repo))
            repo_edit.click()
            self.wait_for_ajax()
            repo_select = self.wait_until_element((strategy1, value1 % repo))
            if enable:
                Select(repo_select).select_by_visible_text("Override to Yes")
            else:
                Select(repo_select).select_by_visible_text("Override to No")
            self.wait_until_element(common_locators['save']).click()
            self.wait_for_ajax()

    def get_attribute(self, name, locator):
        """
        Get the attribute of selected locator
        """

        element = self.search_key(name)

        if element:
            element.click()
            self.wait_for_ajax()
            if self.wait_until_element(locator):
                result = self.find_element(locator).text
                return result
            else:
                raise Exception(
                    "Couldn't get text attribute of a given locator")
        else:
            raise Exception(
                "Couldn't find the selected activation key '%s'" % name)

    def add_host_collection(self, name, host_collection_name):
        """
        Associate an existing Host Collection with Activation Key
        """

        # find activation key
        activation_key = self.search_key(name)
        if activation_key:
            activation_key.click()
            self.wait_for_ajax()

            self.wait_until_element(
                tab_locators["ak.host_collections"]).click()
            self.wait_for_ajax()

            self.wait_until_element(
                tab_locators["ak.host_collections.add"]).click()
            self.wait_for_ajax()

            # select host collection
            strategy, value = tab_locators["ak.host_collections.add.select"]
            host_collection = self.wait_until_element((
                strategy, value % host_collection_name))
            if host_collection:
                host_collection.click()

                # add host collection
                add_btn = self.wait_until_element(
                    tab_locators["ak.host_collections.add.add_selected"])
                add_btn.click()
                self.wait_for_ajax()
            else:
                raise UINoSuchElementError("Couldn't find host collection '%s'"
                                           % host_collection_name)
        else:
            raise UINoSuchElementError("Couldn't find activation key '%s'" %
                                       name)

    def fetch_associated_content_host(self, name):
        """
        Fetch associated content host from selected activation key
        """

        # find activation key
        activation_key = self.search_key(name)
        if not activation_key:
            raise UINoSuchElementError(
                'Could not find activation key {0}'.format(name))
        activation_key.click()
        self.wait_for_ajax()
        self.wait_until_element(tab_locators["ak.associations"]).click()
        self.wait_for_ajax()
        self.wait_until_element(locators["ak.content_hosts"]).click()
        self.wait_for_ajax()
        if self.wait_until_element(locators["ak.content_host_name"]):
            result = self.find_element(locators["ak.content_host_name"]).text
            return result
        else:
            raise UINoSuchElementError(
                "Couldn't get text attribute of content host locator")
