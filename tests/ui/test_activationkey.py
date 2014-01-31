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
        1. Create Activation key for all valid Activation Key name variation
        in [1] using valid Description, Environment, Content View, Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')

    def test_positive_create_org_2(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Description
        @Steps:
        1. Create Activation key for all valid Description variation in [1]
        using valid Name, Environment, Content View and Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')

    def test_positive_create_org_3(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Environments
        @Steps:
        1. Create Activation key for all valid Environments in [1]
        using valid Name, Description, Content View and Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')

    def test_positive_create_org_4(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Content Views
        @Steps:
        1. Create Activation key for all valid Content views in [1]
        using valid Name, Description, Environment and Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')

    def test_positive_create_org_5(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of System Groups
        @Steps:
        1. Create Activation key for all valid System Groups in [1]
        using valid Name, Description, Environment, Content View, Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')

    def test_positive_create_org_6(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with default Usage limit (Unlimited)
        @Steps:
        1. Create Activation key with default Usage Limit (Unlimited)
        using valid Name, Description, Environment and Content View
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')

    def test_positive_create_org_7(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with finite Usage limit
        @Steps:
        1. Create Activation key with finite Usage Limit (Not Unlimited)
        using valid Name, Description, Environment and Content View
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')

    def test_positive_create_org_8(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with minimal input parameters
        @Steps:
        1. Create Activation key by entering Activation Key Name alone
        leaving Description, Content View and Usage Limit as default values
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail('Test not implemented')
