# -*- encoding: utf-8 -*-
"""Implements Jobs UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Job(Base):
    """Provides the basic functionality for Jobs."""

    def navigate_to_entity(self):
        """Navigate to Jobs entity page"""
        Navigator(self.browser).go_to_jobs()

    def _search_locator(self):
        """Specify locator for Jobs entity search procedure"""
        return locators['job_invocation.select']

    def run(self, job_category=None, job_template=None,
            bookmark=None, search_query=None, options_list=None,
            schedule=None, schedule_options=None, result='succeeded'):
        """Run job against specified host

        :param job_category: Specify category of job. Choose 'Miscellaneous'
            category for new custom job templates
        :param job_template: Specify template name (e.g.
            'Run Command - SSH Default')
        :param bookmark: Specify predefined bookmark (e.g. 'active' or 'error')
        :param search_query: Add criteria to find proper host for job to be run
            against (e.g. 'name = hostname')
        :param options_list: List of commands to be executed on the host
            [{'name': 'command', 'value': 'ls'}]
            [
            {'name': 'action', 'value': 'install'},
            {'name': 'package', 'value': 'zsh'}
            ]
            [{'name': 'errata', 'value': 'patch_01'}]
        :param schedule: Specify schedule type ('immediate', 'future' or
            'recurring')
        :param schedule_options: List of parameters to specify schedule options
            [
            {'name': 'start_at', 'value': '2016-08-01 16:25'},
            {'name': 'start_before', 'value': '2016-08-01 18:25'},
            ]
            [
            {'name': 'repeats', 'value': 'weekly'},
            {'name': 'repeats_n_times', 'value': '10'},
            ]
        :param result: Specify expected result for current job execution
            procedure (e.g. 'failed' or 'succeeded')
        :return: Returns whether job is finished with expected state or not
        """
        self.click(common_locators['run_job'])
        if job_category:
            self.assign_value(
                locators['job_invocation.job_category'], job_category)
        if job_template:
            self.assign_value(
                locators['job_invocation.job_template'], job_template)
        if bookmark:
            self.assign_value(locators['job_invocation.bookmark'], bookmark)
        if search_query:
            self.assign_value(locators['job_invocation.query'], search_query)
        if options_list:
            for option in options_list:
                self.assign_value(
                    locators['job_invocation.' + option['name']],
                    option['value']
                )
        if schedule:
            self.click(locators['job_invocation.schedule_type'] % schedule)
        if schedule_options:
            for option in schedule_options:
                self.assign_value(
                    locators['job_invocation.schedule.' + option['name']],
                    option['value']
                )
        self.click(common_locators['submit'])
        # It will be hard to return state and perform verification on test
        # level as we have to wait for specific state due existence of
        # intermediate states (like 'pending')
        if self.wait_until_element(
                locators['job_invocation.status'] % result, 180) is not None:
            return True
        else:
            return False
