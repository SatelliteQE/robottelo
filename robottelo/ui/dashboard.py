# -*- encoding: utf-8 -*-
"""Implements Dashboard UI"""

from robottelo.helpers import escape_search
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Dashboard(Base):
    """Manipulates dashboard from UI"""

    def navigate_to_entity(self):
        """Navigate to Dashboard entity page and make it static"""
        Navigator(self.browser).go_to_dashboard()
        self.click(locators['dashboard.auto_refresh'])
        self.browser.refresh()
        self.wait_for_ajax()

    def _search_locator(self):
        """Specify locator for Dashboard entity search procedure"""
        # There is no element that can be clicked or directly and logically
        # associated with Dashboard entity. Total hosts count returned by
        # search seems the most closer fact to our ideology
        return locators['dashboard.hosts_total']

    def get_total_hosts_count(self):
        """Return total host count according to current organization and search
        criteria
        """
        _, count = self.wait_until_element(
            self._search_locator()).text.split(': ')
        return int(count)

    def search(self, name, search_key=None):
        """Perform search on Dashboard page"""
        self.navigate_to_entity()
        if search_key is None:
            search_string = name
        else:
            search_string = u'{0} = {1}'.format(
                search_key, escape_search(name))
        self.assign_value(common_locators['search'], search_string)
        self.click(common_locators['search_button'])
        return self.get_total_hosts_count()

    def remove_widget(self, widget_name):
        """Remove specified widget from dashboard. Name for each widget should
        be the same as on UI(e.g. 'Task Status')
        """
        self.navigate_to_entity()
        self.click(
            locators['dashboard.remove_widget'] % widget_name,
            wait_for_ajax=False
        )
        self.handle_alert(True)
        self.wait_until_element_is_not_visible(
            locators['dashboard.remove_widget'] % widget_name)

    def manage_widget(self, action_name, widget_name=None):
        """Execute specified action from Dashboard Manage dropdown"""
        self.click(locators['dashboard.manage_widget'])
        if action_name == 'Save Dashboard':
            self.click(locators['dashboard.save_dashboard'])
        elif action_name == 'Reset Dashboard':
            self.click(locators['dashboard.reset_dashboard'])
        elif action_name == 'Restore Widget':
            self.click(
                locators['dashboard.restore_widget'] % widget_name)
        elif action_name == 'Add Widget':
            self.click(
                locators['dashboard.add_widget'] % widget_name)

    def get_widget(self, widget_name):
        """Get widget element from dashboard"""
        self.navigate_to_entity()
        return self.wait_until_element(
            locators['dashboard.widget_element'] % widget_name)

    def get_hcs_host_count(self, criteria_name):
        """Get information about hosts count per specific criteria for Host
        Configuration Status widget
        """
        return int(self.wait_until_element(
            locators['dashboard.hcs.hosts_count'] % criteria_name).text)

    def validate_hcs_navigation(
            self, criteria_name, expected_search_value=None, host_name=None):
        """Find specific criteria on Host Configuration Status widget and then
        click on it. After application navigate on Hosts page, check whether
        proper search string is inherited into search box and that search is
        actually executed afterwards. Then check whether expected host is found
        and present in the list
        """
        self.navigate_to_entity()
        self.click(locators['dashboard.hcs.search_criteria'] % criteria_name)
        if self.wait_until_element(locators['host.page_title']) is None:
            raise UIError(
                'Redirection to Hosts page does not work properly')
        if expected_search_value:
            actual_value = self.wait_until_element(
                common_locators['search']).get_attribute('value')
            if actual_value != expected_search_value:
                raise UIError(
                    'Search box contains invalid data')
        if host_name:
            found_host_name = self.wait_until_element(
                locators['host.select_name'] % host_name
            ).text
            if found_host_name is None:
                raise UIError(
                    'Expected host was not found in the list')
        return True

    def get_hcc_host_percentage(self, criteria_name):
        """Get information about hosts percentage per specific criteria for
        Host Configuration Chart widget
        """
        self.navigate_to_entity()
        return self.wait_until_element(
            locators['dashboard.hcc.hosts_percentage'] % criteria_name).text

    def validate_chss_navigation(
            self, criteria_name, expected_search_value=None, host_name=None):
        """Find specific criteria on Content Host Subscription Status widget
        and then click on it. After application navigate on Content Hosts page,
        check whether proper search string is inherited into search box and
        that search is actually executed afterwards. Then check whether
        expected host is found and present in the list
        """
        self.navigate_to_entity()
        self.click(locators['dashboard.chss.search_criteria'] % criteria_name)
        if self.wait_until_element(locators['contenthost.page_title']) is None:
            raise UIError(
                'Redirection to Content Hosts page does not work properly')
        if expected_search_value:
            actual_value = self.wait_until_element(
                common_locators['kt_search']).get_attribute('value')
            if actual_value != expected_search_value:
                raise UIError(
                    'Search box contains invalid data')
        if host_name:
            found_host_name = self.wait_until_element(
                locators['contenthost.select_name'] % host_name).text
            if found_host_name is None:
                raise UIError(
                    'Expected task was not found in the list')
        return True

    def validate_task_navigation(
            self, task_state, task_result, task_name=None):
        """Find specific task by state and result on Task Status widget and
        then click on it. After application navigate on Tasks page, check
        whether proper search string is inherited into search box and that
        search is actually executed afterwards. Then check whether expected
        task is found and present in the list
        """
        expected_search_value = 'state={}&result={}'.format(
            task_state, task_result)
        self.navigate_to_entity()
        self.click(locators['dashboard.task.search_criteria'] % (
            task_state, task_result))
        if self.wait_until_element(locators['task.page_title']) is None:
            raise UIError(
                'Redirection to Tasks page does not work properly')
        if expected_search_value:
            actual_value = self.wait_until_element(
                common_locators['search']).get_attribute('value')
            if actual_value != expected_search_value:
                raise UIError(
                    'Search box contains invalid data')
        if task_name:
            found_task_name = self.wait_until_element(
                locators['task.select_name'] % task_name).text
            if found_task_name is None:
                raise UIError(
                    'Expected task was not found in the list')
        return True

    def validate_error_navigation(
            self, task_name, expected_result=None, summary_message=None):
        """Find specific task on Latest Warning/Error Tasks widget and then
        click on it. After application navigate on expected task details page,
        check whether correct result information and error message is displayed
        in summary section
        """
        self.navigate_to_entity()
        self.click(locators['dashboard.lwe_task.name'] % task_name)
        task_tab_element = self.wait_until_element(
            tab_locators['task.tab_task'])
        if task_tab_element is None:
            raise UIError(
                'Redirection to task details page does not work properly')
        self.click(task_tab_element)
        if expected_result:
            actual_result = self.wait_until_element(
                locators['task.selected.result']).text.strip()
            if actual_result != expected_result:
                raise UIError(
                    'Task finished with unexpected result')
        if summary_message:
            actual_value = self.wait_until_element(
                locators['task.selected.summary']).text

            if actual_value != summary_message:
                raise UIError(
                    'Task summary message has wrong value')
        return True

    def get_cvh_tasks_list(self, cv_name):
        """Get all tasks and their statuses for specific content view on
        Content View History widget
        """
        self.navigate_to_entity()
        elements_list = [
            element.text for element in self.find_elements(
                locators['dashboard.cvh.tasks_statuses'] % cv_name)
        ]
        # return list of task-status pairs
        return [
            elements_list[i:i + 2] for i in range(0, len(elements_list), 2)]

    def get_hc_host_count(self, hc_name):
        """Get content hosts count for specific collection for Host Collections
        widget
        """
        self.navigate_to_entity()
        return int(self.wait_until_element(
            locators['dashboard.hc.hosts_count'] % hc_name).text)

    def get_so_product_status(self, product_name):
        """Get status for specific product on Sync Overview widget"""
        self.navigate_to_entity()
        return self.wait_until_element(
            locators['dashboard.so.product_status'] % product_name).text

    def get_cst_subs_count(self, criteria_name):
        """Get subscriptions count per specific criteria for Current
        Subscription Totals widget
        """
        self.navigate_to_entity()
        return int(self.wait_until_element(
            locators['dashboard.cst.subs_count'] % criteria_name).text)
