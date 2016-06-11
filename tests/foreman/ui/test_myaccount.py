# -*- encoding: utf-8 -*-
"""Test class for Users UI

@Requirement: Myaccount

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import stubbed, tier1
from robottelo.test import UITestCase


class MyAccountTestCase(UITestCase):
    """Implements Users tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name

    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size

    """

    @stubbed()
    @tier1
    def test_positive_update_firstname(self):
        """Update Firstname in My Account

        @id: d5e617e6-ff61-451b-9e82-dd14e7348de6

        @Steps:
        1. Update current User with all variations of Firstname in [1]

        @Assert: Current User is updated

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_update_surname(self):
        """Update Surname in My Account

        @id: 755c1acc-901b-40de-8bdc-1eace9713ed7

        @Steps:
        1. Update current User with all variations of Surname in [1]

        @Assert: Current User is updated

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_update_email(self):
        """Update Email Address in My Account

        @id: 1c535b77-36d8-44d1-aaf0-07e0ca4eeb28

        @Steps:
        1. Update current User with all variations of Email Address in [1]

        @Assert: Current User is updated

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_update_language(self):
        """Update Language in My Account

        @id: 87604475-3a8e-4cb1-ace4-ea874b1d9e72

        @Steps:
        1. Update current User with all different Language options

        @Assert: Current User is updated

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_update_password(self):
        """Update Password/Verify fields in My Account

        @id: 3ab5d347-e02a-4d34-aec0-970419525268

        @Steps:
        1. Update Password/Verify fields with all variations in [1]

        @Assert: User is updated

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_update_firstname(self):
        """Update My Account with invalid FirstName

        @id: 3b6250a5-437c-4540-8e95-32a915776f7f

        @Steps:
        1. Update Current user with all variations of FirstName in [2]

        @Assert: User is not updated. Appropriate error shown.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_update_surname(self):
        """Update My Account with invalid Surname

        @id: 97c9ae7b-73d8-4896-bff1-f701d2b53776

        @Steps:
        1. Update Current user with all variations of Surname in [2]

        @Assert: User is not updated. Appropriate error shown.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_update_email(self):
        """Update My Account with invalid Email Address

        @id: 06ace1c7-9a0e-4a0d-9b42-a5b510d697e1

        @Steps:
        1. Update Current user with all variations of Email Address in [2]

        @Assert: User is not updated. Appropriate error shown.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_update_password(self):
        """Update My Account with invalid Password/Verify fields

        @id: 09739b2e-8717-4104-a9c8-3377227599f0

        @Steps:
        1. Update Current user with all variations of Password/Verify fields
        in [2]

        @Assert: User is not updated. Appropriate error shown.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_update_password_mismatch(self):
        """Update My Account with non-matching values in Password and
        verify fields

        @id: b729ade7-ee69-4c43-a576-10be38f5c5fa

        @Steps:
        1. Update Current user with non-matching values in Password and verify
        fields

        @Assert: User is not updated. Appropriate error shown.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_update(self):
        """[UI ONLY] Attempt to update all info in My Accounts page and
        Cancel

        @id: 3867c4c3-b458-4d7b-a6c9-f2e65604e994

        @Steps:
        1. Update Current user with valid Firstname, Surname, Email Address,
        Language, Password/Verify fields
        2. Click Cancel

        @Assert: User is not updated.

        @caseautomation: notautomated
        """
