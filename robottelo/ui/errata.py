# -*- encoding: utf-8 -*-
"""Implements Errata UI"""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Errata(Base):
    """Manipulates Errata from UI"""

    is_katello = True
    search_key = 'id'

    def navigate_to_entity(self):
        """Navigate to Errata entity page"""
        Navigator(self.browser).go_to_errata()

    def _search_locator(self):
        """Specify locator for Errata entity search procedure"""
        return locators['errata.select_name']

    def show_only_applicable(self, value=True):
        """Switch the checkbox to show either only applicable for hosts errata
        or all available for current organization errata.
        """
        self.assign_value(locators['errata.filter_applicable'], value)

    def install(self, errata_id, hostnames, only_applicable=None,
                only_installable=None, really=True, timeout=120):
        """Install errata on content host(s).

        :param errata_id: errata id, e.g. 'RHEA-2012:0055'
        :param hostnames: either content host name or a list containing all the
            content host names to apply errata on
        :param only_applicable: only show applicable errata during errata
            search
        :param only_installable: only show content hosts where the errata is
             currently installable
        :param really: bool value whether to confirm installation or not
        :param timeout: timeout in seconds for errata installation task to
            finish
        :raise: UIError if remote task finished by timeout

        :return: Returns a string containing task status
        """
        if only_applicable is not None:
            self.navigate_to_entity()
            self.show_only_applicable(only_applicable)
        self.click(self.search(errata_id))
        self.click(tab_locators['errata.tab_content_hosts'])
        if only_installable is not None:
            self.assign_value(
                locators['errata.content_hosts.installable'], only_installable)
        if not isinstance(hostnames, list):
            hostnames = [hostnames]
        # Use search only in case 1 hostname was passed. Otherwise checkboxes
        # state will be lost after each search
        if len(hostnames) == 1:
            self.assign_value(common_locators['kt_search'], hostnames[0])
            self.click(common_locators['kt_search_button'])
        for hostname in hostnames:
            self.click(locators['errata.content_hosts.ch_select'] % hostname)
        self.click(locators['errata.content_hosts.errata_apply'])
        if really:
            self.click(locators['errata.content_hosts.confirm_installation'])
        else:
            self.click(locators['errata.content_hosts.cancel_installation'])
        result = self.wait_until_element(
            locators['contenthost.remote_action_finished'],
            timeout=timeout,
        )
        if result is None:
            raise UIError('Timeout waiting for errata installation to finish')
        return result.get_attribute('type')

    def repository_search(self, errata_id, repo_name, package_name,
                          only_applicable=None):
        """Search for repository containing specific errata"""
        if only_applicable is not None:
            self.navigate_to_entity()
            self.show_only_applicable(only_applicable)
        self.click(self.search(errata_id))
        self.click(tab_locators['errata.tab_repositories'])
        self.assign_value(common_locators['kt_search'], repo_name)
        self.click(common_locators['kt_search_button'])
        return self.wait_until_element(
            locators['errata.repositories.repo_select'] %
            (repo_name, package_name)
        )

    def contenthost_search(self, errata_id, hostname, only_applicable=None,
                           only_installable=None, environment=None):
        """Search for content host applicable for installing specific errata"""
        if only_applicable is not None:
            self.navigate_to_entity()
            self.show_only_applicable(only_applicable)
        self.click(self.search(errata_id))
        self.click(tab_locators['errata.tab_content_hosts'])
        if only_installable is not None:
            self.assign_value(
                locators['errata.content_hosts.installable'], only_installable)
        if environment is not None:
            self.assign_value(
                locators['errata.content_hosts.env_filter'], environment)
        self.assign_value(common_locators['kt_search'], hostname)
        self.click(common_locators['kt_search_button'])
        return self.wait_until_element(
            locators['errata.content_hosts.ch_select'] % hostname)

    def check_errata_details(self, errata_id, parameter_list=None,
                             only_applicable=None):
        """Check whether errata detail section contains expected values or
        raise exception otherwise.
        All values should be passed in absolute correspondence to UI. For
        example, we have 'Description' or 'Checksum Type' fields, so next
        parameter list should be passed::

            [
                ['Description', 'Expected description'],
                ['CVEs', 'CVE-2014-3633 , CVE-2014-3657 , CVE-2014-7823'],
            ]

        """
        if only_applicable is not None:
            self.navigate_to_entity()
            self.show_only_applicable(only_applicable)
        self.click(self.search(errata_id))
        for parameter_name, parameter_value in parameter_list:
            param_locator = '.'.join((
                'errata',
                (parameter_name.lower()).replace(' ', '_')
            ))
            if isinstance(parameter_value, set):
                actual_text_set = set()
                if self.wait_until_element_exists(locators[param_locator]):
                    actual_text_set = {
                        element.text.strip()
                        for element in self.find_elements(
                            locators[param_locator])
                        }
                if parameter_value != actual_text_set:
                    raise UIError(
                        'Actual text set for "{0}" parameter is "{1}", but it'
                        ' is expected to be "{2}"'.format(
                            parameter_name, actual_text_set, parameter_value)
                    )
            else:
                actual_text = self.wait_until_element(
                    locators[param_locator]).text
                if parameter_value not in actual_text:
                    raise UIError(
                        'Actual text for "{0}" parameter is "{1}", but it is'
                        ' expected to have "{2}"'.format(
                            parameter_name, actual_text, parameter_value)
                    )

    def validate_table_fields(
            self, errata_id, only_applicable=None, values_list=None):
        """Check that errata table fields has appropriate values"""
        if only_applicable is not None:
            self.navigate_to_entity()
            self.show_only_applicable(only_applicable)
        self.search(errata_id)
        for value in values_list:
            self.wait_until_element(locators['errata.table_value'] % value)

    def auto_complete_search(self, errata_id, partial_id=None,
                             only_applicable=None):
        """Auto complete search by giving partial ID of errata."""
        if only_applicable is not None:
            self.navigate_to_entity()
            self.show_only_applicable(only_applicable)
        if partial_id is None:
            partial_id = errata_id[:len(errata_id)/2]
        self.assign_value(
            common_locators['kt_search'],
            self.search_key + " = " + partial_id
        )
        self.click(common_locators['auto_search'] % errata_id)
        self.click(common_locators['kt_search_button'])
        return self.wait_until_element(self._search_locator() % errata_id)
