# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Activation key UI
"""

from tests.ui.baseui import BaseUI


class ActivationKey(BaseUI):
    """
    Implements Activation key tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name
    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size
    """

    def test_positive_create_org_1(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Activation key name
        @Steps:
             1.  Create Activation key (for valid name variation in [1]
             with valid Description, Environment, Content View and Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')

    def test_positive_create_org_2(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Description
        @Steps:
             1.  Create Activation key (For valid Description variation in [1]
             with valid Name, Environment, Content View and Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')
