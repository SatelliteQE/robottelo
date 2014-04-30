# -*- encoding: utf-8 -*-

"""
Implements Content Views UI
"""

from robottelo.common.helpers import escape_search
from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from selenium.webdriver.support.select import Select


class ContentViews(Base):
    """
    Manipulates Content Views from UI
    """

    def create(self, name, label=None, description=None, is_composite=False):
        """Creates a content view"""

        self.wait_until_element(locators["contentviews.new"]).click()

        if self.wait_until_element(common_locators["name"]):
            self.find_element(common_locators
                              ["name"]).send_keys(name)
            timeout = 60 if len(name) > 50 else 30
            self.wait_for_ajax(timeout)

            if label is not None:
                self.find_element(common_locators["label"]).send_keys(label)

            if description is not None:
                self.find_element(
                    common_locators["description"]).send_keys(description)

            if is_composite:
                self.find_element(
                    locators["contentviews.composite"]).click()

            self.wait_for_ajax()
            self.wait_until_element(common_locators["create"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new content view '%s'" % name)

    def search(self, element_name):
        """Uses the search box to locate an element from a list of elements """

        element = None
        strategy = locators["contentviews.key_name"][0]
        value = locators["contentviews.key_name"][1]
        searchbox = self.wait_until_element(common_locators["kt_search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(escape_search(element_name))
            self.find_element(common_locators["kt_search_button"]).click()
            self.wait_for_ajax()
            element = self.wait_until_element((strategy, value % element_name))
            return element

    def update(self, name, new_name=None, new_description=None):
        """Updates an existing content view"""

        element = self.search(name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.find_element(tab_locators['contentviews.info']).click()

            if new_name:
                self.edit_entity(
                    "contentviews.edit_name",
                    "contentviews.edit_name_text", new_name,
                    "contentviews.save_name")
                self.wait_for_ajax()

            if new_description:
                self.edit_entity(
                    "contentviews.edit_description",
                    "contentviews.edit_description_text", new_description,
                    "contentviews.save_description")
                self.wait_for_ajax()
        else:
            raise Exception("Could not update the content view '%s'" % name)

    def add_remove_repos(self, cv_name, repo_names, add_repo=True):
        """
        Add or Remove repository to/from selected content-view.

        When 'add_repo' Flag is set then add_repository will be performed,
        otherwise remove_repository
        """

        element = self.search(cv_name)

        if element:
            element.click()
            self.find_element(tab_locators["contentviews.tab_content"]).click()
            self.find_element(locators["contentviews.content_repo"]).click()
            self.wait_for_ajax()
            if add_repo:
                self.find_element(tab_locators
                                  ["contentviews.tab_repo_add"]).click()
            else:
                self.find_element(tab_locators
                                  ["contentviews.tab_repo_remove"]).click()
            strategy, value = locators["contentviews.select_repo"]
            for repo_name in repo_names:
                self.text_field_update(locators
                                       ["contentviews.repo_search"],
                                       repo_name)
                element = self.wait_until_element((strategy,
                                                   value % repo_name))
                if element:
                    element.click()
                    self.wait_for_ajax()
                    if add_repo:
                        self.wait_until_element(locators
                                                ["contentviews.add_repo"]
                                                ).click()
                    else:
                        self.wait_until_element(locators
                                                ["contentviews.remove_repo"]
                                                ).click()
                else:
                    raise Exception(
                        "Couldn't find repo '%s'"
                        "to add into CV" % repo_name)
        else:
            raise Exception(
                "Couldn't find the selected CV '%s'" % cv_name)

    def check_progress_bar_status(self, version):
        """
        Checks the status of progress bar while publishing and
        promoting the CV to next environment
        """

        strategy, value = locators["contentviews.publish_progress"]
        check_progress = self.wait_until_element((strategy,
                                                  value % version))
        while check_progress:
            check_progress = self.wait_until_element((strategy,
                                                      value % version))

    def publish(self, cv_name, comment=None):
        """
        Publishes to create new version of CV and
        promotes the contents to 'Library' environment
        """

        element = self.search(cv_name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.wait_until_element(locators["contentviews.publish"]).click()
            version_label = self.wait_until_element(locators
                                                    ["contentviews.ver_label"])
            version_number = self.wait_until_element(locators
                                                     ["contentviews.ver_num"])
            # To fetch the publish version e.g. "Version 1"
            version = '%s %s' % (version_label.text, version_number.text)
            if comment:
                self.find_element(locators
                                  ["contentviews.publish_comment"]
                                  ).send_keys(comment)
            self.wait_until_element(common_locators["create"]).click()
            self.wait_for_ajax()
            self.check_progress_bar_status(version)
            return version
        else:
            raise Exception(
                "Couldn't find the selected CV '%s'" % cv_name)

    def promote(self, cv_name, version, env):
        """
        Promotes the selected version of content-view
        to given environment
        """

        element = self.search(cv_name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.wait_until_element(tab_locators
                                    ["contentviews.tab_versions"]).click()
            self.wait_for_ajax()
            strategy, value = locators["contentviews.promote_button"]
            element = self.wait_until_element((strategy, value % version))
            if element:
                element.click()
                self.wait_for_ajax()
                strategy, value = locators["contentviews.env_to_promote"]
                env_element = self.wait_until_element((strategy, value % env))
                if env_element:
                    env_element.click()
                    self.wait_until_element(locators
                                            ["contentviews.promote_version"]
                                            ).click()
                    self.check_progress_bar_status(version)
                else:
                    raise Exception(
                        "Could not find env '%s' to promote CV" % env)
            else:
                raise Exception(
                    "Could not find the published version '%s'" % version)
        else:
            raise Exception(
                "Couldn't find the selected CV '%s'" % cv_name)

    def add_puppet_module(self, cv_name, module_name, filter_term):
        """
        Add puppet module to selected view either by its author name
        or by its version
        Filter_term can be used to filter the module by 'author'
        or by 'version'
        """

        element = self.search(cv_name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.wait_until_element(tab_locators
                                    ["contentviews.tab_puppet_modules"]
                                    ).click()
            self.wait_until_element(locators
                                    ["contentviews.add_module"]).click()
            self.wait_for_ajax()
            self.text_field_update(common_locators["cv_filter"], module_name)
            strategy, value = locators["contentviews.select_module"]
            element = self.wait_until_element((strategy, value % module_name))
            if element:
                element.click()
                self.wait_for_ajax()
                self.text_field_update(common_locators
                                       ["cv_filter"], filter_term)
                strategy, value = locators["contentviews.select_module_ver"]
                element = self.wait_until_element((strategy,
                                                   value % filter_term))
                if element:
                    element.click()
                    self.wait_for_ajax()
                else:
                    raise Exception(
                        "Couldn't find the selected version '%s'\
                         of puppet module '%s'" % (filter_term, module_name))
                self.text_field_update(common_locators
                                       ["cv_filter"], module_name)
                strategy, value = locators["contentviews.get_module_name"]
                element = self.wait_until_element((strategy,
                                                   value % module_name))
                return element
            else:
                raise Exception(
                    "Couldn't find the given puppet module '%s'" % module_name)
        else:
            raise Exception(
                "Couldn't find the selected CV '%s'" % cv_name)

    def add_remove_cv(self, composite_cv, cv_names, is_add=True):
        """
        Add or Remove content-views to/from selected composite view.

        When 'is_add' Flag is set then add_contentView will be performed,
        otherwise remove_contentView
        """

        element = self.search(composite_cv)

        if element:
            element.click()
            self.wait_for_ajax()
            self.find_element(tab_locators
                              ["contentviews.tab_content_views"]).click()
            self.wait_for_ajax()
            if is_add:
                self.find_element(tab_locators
                                  ["contentviews.tab_cv_add"]).click()
            else:
                self.find_element(tab_locators
                                  ["contentviews.tab_cv_remove"]).click()
            strategy, value = locators["contentviews.select_cv"]
            for cv_name in cv_names:
                element = self.wait_until_element((strategy,
                                                   value % cv_name))
                if element:
                    element.click()
                    self.wait_for_ajax()
                    if is_add:
                        self.wait_until_element(locators
                                                ["contentviews.add_cv"]
                                                ).click()
                    else:
                        self.wait_until_element(locators
                                                ["contentviews.remove_cv"]
                                                ).click()
                else:
                    raise Exception(
                        "Couldn't find content-view '%s'"
                        "to add into composite view" % cv_name)
        else:
            raise Exception(
                "Couldn't find the selected CV '%s'" % composite_cv)

    def add_filter(self, cv_name, filter_name,
                   content_type, filter_type, description=None):
        """
        Creates content-view filter of given 'type'(include/exclude) and
        'content-type'(package/package-group/errata)
        """

        element = self.search(cv_name)

        if element:
            element.click()
            self.find_element(tab_locators["contentviews.tab_content"]).click()
            self.wait_until_element(locators
                                    ["contentviews.content_filters"]).click()
            self.wait_until_element(locators
                                    ["contentviews.new_filter"]).click()
            if self.wait_until_element(common_locators["name"]):
                self.find_element(common_locators["name"]
                                  ).send_keys(filter_name)
                if content_type:
                    Select(self.find_element
                           (locators
                            ["contentviews.content_type"]
                            )).select_by_visible_text(content_type)
                else:
                    raise Exception(
                        "Couldn't create filter without content type")
                if filter_type:
                    Select(self.find_element
                           (locators
                            ["contentviews.type"]
                            )).select_by_visible_text(filter_type)
                else:
                    raise Exception(
                        "Couldn't create filter without"
                        "specifying filter type")
                if description:
                    self.find_element(common_locators
                                      ["description"]
                                      ).send_keys(description)
                self.wait_until_element(common_locators["create"]).click()
                self.wait_for_ajax()
            else:
                raise Exception(
                    "Could not create filter without name")
        else:
            raise Exception(
                "couldn't find the content view '%s'" % cv_name)
