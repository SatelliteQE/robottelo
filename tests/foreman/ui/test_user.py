# -*- encoding: utf-8 -*-
"""Test class for Users UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import LANGUAGES
from robottelo.datafactory import invalid_names_list, invalid_values_list
from robottelo.decorators import run_only_on, skip_if_bug_open, stubbed
from robottelo.test import UITestCase
from robottelo.ui.factory import make_user
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from selenium.webdriver.support.select import Select


def valid_strings(len1=10):
    """Generates a list of all the input strings, (excluding html)"""
    return [
        gen_string('alpha', 5),
        gen_string('alpha', len1),
        u'{0}-{1}'.format(gen_string('alpha', 4),
                          gen_string('alpha', 4)),
        u'{0}-{1}'.format(gen_string('alpha', 4),
                          gen_string('alpha', 4)),
        u'նորօգտվող-{0}'.format(gen_string('alpha', 2)),
        u'新用戶-{0}'.format(gen_string('alpha', 2)),
        u'новогопользоват-{0}'.format(gen_string('alpha', 2)),
        u'uusikäyttäjä-{0}'.format(gen_string('alpha', 2)),
        u'νέοςχρήστης-{0}'.format(gen_string('alpha', 2)),
    ]


class User(UITestCase):
    """ Implements Users tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name

    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size

    """

    def test_positive_delete_user(self):
        """@Test: Delete a User

        @Feature: User - Delete

        @Assert: User is deleted

        """
        with Session(self.browser) as session:
            for user_name in valid_strings():
                with self.subTest(user_name):
                    make_user(session, username=user_name)
                    self.user.delete(user_name)

    @skip_if_bug_open('bugzilla', 1139616)
    def test_update_password(self):
        """@Test: Update password for a user

        @Feature: User - Update

        @Assert: User password is updated

        @BZ: 1139616

        """
        user_name = gen_string('alpha')
        new_password = gen_string('alpha')
        with Session(self.browser) as session:
            # Role 'Site' meaning 'Site Manager' here
            make_user(session, username=user_name, edit=True, roles=['Site'])
            self.user.update(user_name, password=new_password)
            self.login.logout()
            self.login.login(user_name, new_password)
            self.assertTrue(self.login.is_logged())

    def test_update_role(self):
        """@Test: Update role for a user

        @Feature: User - Update

        @Assert: User role is updated

        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role_name = entities.Role().create_json()['name']
        with Session(self.browser) as session:
            make_user(session, username=name)
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_roles'])
            element1 = self.user.wait_until_element((strategy,
                                                     value % role_name))
            self.assertIsNone(element1)
            self.user.update(name, new_roles=[role_name])
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_roles'])
            element2 = self.user.wait_until_element((strategy,
                                                     value % role_name))
            self.assertIsNotNone(element2)

    def test_positive_create_user_different_usernames(self):
        """@Test: Create User for all variations of Username

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid User name variation in [1] using
        valid First Name, Surname, Email Address, Language, authorized by

        @Assert: User is created

        """
        with Session(self.browser) as session:
            for user_name in valid_strings():
                with self.subTest(user_name):
                    make_user(session, username=user_name)
                    self.assertIsNotNone(
                        self.user.search(user_name))

    def test_positive_create_user_different_first_names(self):
        """@Test: Create User for all variations of First Name

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid First Name variation in [1] using
        valid Username, Surname, Email Address, Language, authorized by

        @Assert: User is created

        """
        with Session(self.browser) as session:
            for first_name in valid_strings():
                with self.subTest(first_name):
                    name = gen_string('alpha')
                    make_user(session, username=name, first_name=first_name)
                    element = self.user.search(name)
                    self.assertIsNotNone(element)
                    element.click()
                    self.assertEqual(
                        first_name,
                        self.user.wait_until_element(
                            locators['users.firstname']).get_attribute('value')
                    )

    def test_positive_create_user_different_surnames(self):
        """@Test: Create User for all variations of Surname

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Surname variation in [1] using
        valid User name, First Name, Email Address, Language, authorized by

        @Assert: User is created

        """
        with Session(self.browser) as session:
            for last_name in valid_strings(50):
                with self.subTest(last_name):
                    name = gen_string('alpha')
                    make_user(session, username=name, last_name=last_name)
                    element = self.user.search(name)
                    self.assertIsNotNone(element)
                    element.click()
                    self.assertEqual(
                        last_name,
                        self.user.wait_until_element(
                            locators['users.lastname']).get_attribute('value')
                    )

    @stubbed()
    def test_positive_create_user_different_emails(self):
        """@Test: Create User for all variations of Email Address

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Email Address variation in [1] using
        valid Username, First Name, Surname, Language, authorized by

        @Assert: User is created

        @Status: Manual

        """

    def test_positive_create_user_different_languages(self):
        """@Test: Create User for all variations of Language

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Language variations using
        valid Username, First Name, Surname, Email Address, authorized by

        @Assert: User is created

        """
        with Session(self.browser) as session:
            for language in LANGUAGES:
                with self.subTest(language):
                    name = gen_string('alpha')
                    make_user(session, username=name, locale=language)
                    element = self.user.search(name)
                    self.assertIsNotNone(element)
                    element.click()
                    self.assertEqual(
                        language,
                        self.user.wait_until_element(
                            locators['users.selected_lang']
                        ).get_attribute('value')
                    )

    @stubbed()
    def test_positive_create_user_internal(self):
        """@Test: Create User by choosing Authorized by - INTERNAL

        @Feature: User - Positive Create

        @Steps:
        1. Create User by choosing Authorized by - INTERNAL using
        valid Password/Verify fields

        @Assert: User is created

        @Status: Manual

        """

    def test_positive_create_user_different_pass(self):
        """@Test: Create User for all variations of Password

        @Feature: User - Positive Create

        @Steps:
        1. Create User for all valid Password variation in [1] using valid
        Username, First Name, Surname, Email Address, Language, authorized by

        @Assert: User is created

        """
        test_data = valid_strings()
        #  List is extended to test additional password data points
        test_data.extend([
            x for x in (
                u'foo@!#$^&*( ) {0}'.format(gen_string('alpha', 2)),
                u'bar+{{}}|\"?hi {0}'.format(gen_string('alpha', 2)),
            )
        ])
        with Session(self.browser) as session:
            for password in test_data:
                with self.subTest(password):
                    name = gen_string('alpha')
                    make_user(
                        session,
                        username=name,
                        password1=password,
                        password2=password,
                    )
                    self.assertIsNotNone(self.user.search(name))

    @stubbed()
    def test_positive_create_user_admin(self):
        """@Test: Create an Admin user

        @Feature: User - Positive Create

        @Assert: Admin User is created

        @Status: Manual

        """

    def test_positive_create_user_with_one_role(self):
        """@Test: Create User with one role

        @Feature: User - Positive Create

        @Steps:
        1. Create User with one role assigned to it

        @Assert: User is created

        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role = entities.Role().create()
        with Session(self.browser) as session:
            make_user(session, username=name, roles=[role.name], edit=True)
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_roles'])
            element = self.user.wait_until_element((strategy,
                                                    value % role.name))
            self.assertIsNotNone(element)

    def test_positive_create_user_with_multiple_roles(self):
        """@Test: Create User with multiple roles

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple roles assigned to it

        @Assert: User is created

        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role1 = gen_string('alpha')
        role2 = gen_string('alpha')
        for role in [role1, role2]:
            entities.Role(name=role).create()
        with Session(self.browser) as session:
            make_user(session, username=name, roles=[role1, role2],
                      edit=True)
            self.user.search(name).click()
            self.user.wait_for_ajax()
            self.user.click(tab_locators['users.tab_roles'])
            for role in [role1, role2]:
                element = self.user.wait_until_element((strategy,
                                                        value % role))
                self.assertIsNotNone(element)

    @stubbed()
    def test_positive_create_user_11(self):
        """@Test: Create User and assign all available roles to it

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all available roles assigned to it

        @Assert: User is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_user_12(self):
        """@Test: Create User with one owned host

        @Feature: User - Positive Create

        @Steps:
        1. Create User with one owned host assigned to it

        @Assert: User is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_user_13(self):
        """@Test: Create User with mutiple owned hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple owned hosts assigned to it

        @Assert: User is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_user_14(self):
        """@Test: Create User with all owned hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all owned hosts assigned to it

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_15(self):
        """@Test: Create User with one Domain host

        @Feature: User - Positive Create

        @Steps:
        1. Create User with one Domain host assigned to it

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_16(self):
        """@Test: Create User with mutiple Domain hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with multiple Domain hosts assigned to it

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_17(self):
        """@Test: Create User with all Domain hosts

        @Feature: User - Positive Create

        @Steps:
        1. Create User with all Domain hosts assigned to it

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_18(self):
        """@Test: Create User with one Compute Resource

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with one Compute Resource

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_19(self):
        """@Test: Create User with mutiple Compute Resources

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with multiple Compute Resources

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_20(self):
        """@Test: Create User with all Compute Resources

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with all Compute Resources

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_21(self):
        """@Test: Create User with one Host group

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with one Host group

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_22(self):
        """@Test: Create User with multiple Host groups

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with multiple Host groups

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_23(self):
        """@Test: Create User with all Host groups

        @Feature: User - Positive Create

        @Steps:
        1. Create User associated with all available Host groups

        @Assert: User is created

        @Status: Manual

        """

    def test_positive_create_user_with_one_org(self):
        """@Test: Create User associated to one Org

        @Feature: User - Positive Create

        @Assert: User is created

        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            make_user(
                session, username=name, organizations=[org_name], edit=True)
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_organizations'])
            element = self.user.wait_until_element((strategy,
                                                    value % org_name))
            self.assertIsNotNone(element)

    def test_positive_create_user_with_multiple_orgs(self):
        """@Test: Create User associated to multiple Orgs

        @Feature: User - Positive Create

        @Assert: User is created

        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_name1 = gen_string('alpha')
        org_name2 = gen_string('alpha')
        for org_name in [org_name1, org_name2]:
            entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            make_user(
                session,
                username=name,
                organizations=[org_name1, org_name2],
                edit=True,
            )
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_organizations'])
            for org_name in [org_name1, org_name2]:
                element = self.user.wait_until_element((strategy,
                                                        value % org_name))
                self.assertIsNotNone(element)

    @stubbed()
    def test_positive_create_user_26(self):
        """@Test: Create User associated to all available Orgs

        @Feature: User - Positive Create

        @Assert: User is created

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_create_user_27(self):
        """@Test: Create User with a new Fact filter

        @Feature: User - Positive Create

        @Steps:
        1. Create User associating it to a new Fact filter

        @Assert: User is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_user_28(self):
        """@Test: Create User in supported ldap modes

        @Feature: User - Positive Create

        @Steps:
        1. Create User in all supported ldap modes - (Active Driectory,
        IPA, Posix)

        @Assert: User is created without specifying the password

        @Status: Manual

        """

    def test_positive_create_user_with_default_org(self):
        """@Test: Create User and has default organization associated with it

        @Feature: User - Positive Create.

        @Assert: User is created with default Org selected.

        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            make_user(session, username=name, organizations=[org_name],
                      edit=True, default_org=org_name)
            self.user.search(name).click()
            session.nav.click(tab_locators['users.tab_organizations'])
            element = session.nav.wait_until_element((strategy,
                                                      value % org_name))
            self.assertIsNotNone(element)
            org_element = session.nav.find_element(
                locators['users.default_org'])
            # Fetches currently selected option in a normal select.
            option = Select(org_element).first_selected_option
            self.assertEqual(org_name, option.text)

    def test_positive_create_user_default_location(self):
        """@Test: Create User and associate a default Location.

        @Feature: User - Positive Create

        @Assert: User is created with default Location selected.

        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        loc_name = gen_string('alpha')
        entities.Location(name=loc_name).create()
        with Session(self.browser) as session:
            make_user(session, username=name, locations=[loc_name],
                      edit=True, default_loc=loc_name)
            self.user.search(name).click()
            session.nav.click(tab_locators['users.tab_locations'])
            element = session.nav.wait_until_element((strategy,
                                                      value % loc_name))
            self.assertIsNotNone(element)
            loc_element = session.nav.find_element(
                locators['users.default_loc'])
            # Fetches currently selected option in a normal select.
            option = Select(loc_element).first_selected_option
            self.assertEqual(loc_name, option.text)

    @stubbed()
    def test_negative_create_user_1(self):
        """@Test:[UI ONLY] Enter all User creation details and Cancel

        @Feature: User - Positive Create

        @Steps:
        1. Enter all valid Username, First Name, Surname, Email Address,
        Language, authorized by.
        2. Click Cancel

        @Assert: User is not created

        @Status: Manual

        """

    def test_negative_create_user_with_invalid_name(self):
        """@Test: Create User with invalid User Name

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid User names in [2]
        using valid First Name, Surname, Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        """
        with Session(self.browser) as session:
            for user_name in invalid_values_list(interface='ui'):
                with self.subTest(user_name):
                    make_user(session, username=user_name)
                    self.assertIsNotNone(
                        self.user.wait_until_element(
                            common_locators['haserror'])
                    )

    def test_negative_create_user_with_invalid_firstname(self):
        """@Test: Create User with invalid FirstName

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid First name in [2]
        using valid User name, Surname, Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        """
        with Session(self.browser) as session:
            # invalid_values_list is not used here because first name is an
            # optional field
            for first_name in invalid_names_list():
                with self.subTest(first_name):
                    make_user(
                        session,
                        username=gen_string('alpha'),
                        first_name=first_name,
                    )
                    self.assertIsNotNone(
                        self.user.wait_until_element(
                            common_locators['haserror'])
                    )

    def test_negative_create_user_with_invalid_surname(self):
        """@Test: Create User with invalid Surname

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Surname in [2]
        using valid Username, First Name Email Address, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        """
        with Session(self.browser) as session:
            # invalid_values_list is not used here because sur name is an
            # optional field
            for last_name in invalid_names_list():
                with self.subTest(last_name):
                    make_user(
                        session,
                        username=gen_string('alpha'),
                        last_name=last_name,
                    )
                    self.assertIsNotNone(
                        self.user.wait_until_element(
                            common_locators['haserror'])
                    )

    @stubbed()
    def test_negative_create_user_5(self):
        """@Test: Create User with invalid Email Address

        @Feature: User - Negative Create

        @Steps:
        1. Create User for all invalid Email Address in [2]
        using valid Username, First Name, Surname, Language, authorized by

        @Assert: User is not created. Appropriate error shown.

        @Status: Manual

        """

    def test_negative_create_user_with_blank_auth(self):
        """@Test: Create User with blank Authorized by

        @Feature: User - Negative Create

        @Steps:
        1. Create User with blank Authorized by
        using valid Username, First Name, Surname, Email Address, Language

        @Assert: User is not created. Appropriate error shown.

        """
        with Session(self.browser) as session:
            make_user(session, username=gen_string('alpha'), authorized_by='')
            error = self.user.wait_until_element(common_locators['haserror'])
            self.assertIsNotNone(error)

    def test_negative_create_user_with_wrong_pass_confirmation(self):
        """@Test: Create User with non-matching values in Password and verify

        @Feature: User - Negative Create

        @Steps:
        1. Create User with non-matching values in Password and verify
        using valid Username, First Name, Surname, Email Address, Language,
        authorized by - INTERNAL

        @Assert: User is not created. Appropriate error shown.

        """
        with Session(self.browser) as session:
            make_user(
                session,
                username=gen_string('alpha'),
                password1=gen_string('alpha'),
                password2=gen_string('alpha'),
            )
            error = self.user.wait_until_element(common_locators['haserror'])
            self.assertIsNotNone(error)

    @skip_if_bug_open('bugzilla', 1139616)
    def test_positive_update_user_username(self):
        """@Test: Update Username in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update User name for all variations in [1]

        @Assert: User is updated

        @BZ: 1139616

        """
        name = gen_string('alpha')
        password = gen_string('alpha')
        with Session(self.browser) as session:
            # Role Site meaning 'Site Manager' here
            make_user(
                session,
                username=name,
                password1=password,
                password2=password,
                edit=True,
                roles=['Site'],
            )
        for new_username in valid_strings():
            with self.subTest(new_username):
                with Session(self.browser):
                    self.user.update(name, new_username)
                    self.assertIsNotNone(
                        self.user.search(new_username))
                    self.login.logout()
                    self.login.login(new_username, password)
                    self.assertTrue(self.login.is_logged())
                    name = new_username  # for next iteration

    @stubbed()
    def test_positive_update_user_firstname(self):
        """@Test: Update Firstname in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Firstname name for all variations in [1]

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_surname(self):
        """@Test: Update Surname in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Surname for all variations in [1]

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_email(self):
        """@Test: Update Email Address in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Email Address for all variations in [1]

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_language(self):
        """@Test: Update Language in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update User with all different Language options

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_password(self):
        """@Test: Update Password/Verify fields in User

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Update Password/Verify fields

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_7(self):
        """@Test: Convert an user from an admin user to non-admin user

        @Feature: User - Positive Update

        @Steps:
        1. Create User with Administrator rights
        2. Update the User to remove Administrator rights

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_8(self):
        """@Test: Convert a user to an admin user

        @Feature: User - Positive Update

        @Steps:
        1. Create a regular (non-admin) user
        2. Update the User to add Administrator rights

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_9(self):
        """@Test: Update User with one role

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one role to the user

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_10(self):
        """@Test: Update User with multiple roles

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple roles to the user

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_11(self):
        """@Test: Update User with all roles

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all available roles to the user

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_12(self):
        """@Test: Update User with one owned host

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one host to the user

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_13(self):
        """@Test: Update User with multiple owned hosts

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple owned hosts to the user

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_14(self):
        """@Test: Update User with all owned hosts

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all available owned hosts to the user

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_15(self):
        """@Test: Update User with one Domain host

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one Domain host to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_16(self):
        """@Test: Update User with multiple Domain hosts

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple Domain hosts to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_17(self):
        """@Test: Update User with all Domain hosts

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all Domain hosts to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_18(self):
        """@Test: Update User with one Compute Resource

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one Compute Resource to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_19(self):
        """@Test: Update User with multiple Compute Resources

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple Compute Resources to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_20(self):
        """@Test: Update User with all Compute Resources

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all Compute Resources to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_21(self):
        """@Test: Update User with one Host group

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign one Host group to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_22(self):
        """@Test: Update User with multiple Host groups

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple Host groups to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_23(self):
        """@Test: Update User with all Host groups

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all available Host groups to the User

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_24(self):
        """@Test: Assign a User to an Org

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign an Org to the User

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_25(self):
        """@Test: Assign a User to multiple Orgs

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign multiple Orgs to the User

        @Assert: User is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_user_26(self):
        """@Test: Assign a User to all available Orgs

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Assign all available Orgs to the User

        @Assert: User is updated

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_user_28(self):
        """@Test: Update User with a new Fact filter

        @Feature: User - Positive Update

        @Steps:
        1. Create User
        2. Create and assign a new Fact filter to the User

        @Assert: User is update

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_user_1(self):
        """@Test: Update invalid Username in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Username for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_user_2(self):
        """@Test: Update invalid Firstname in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Firstname for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_user_3(self):
        """@Test: Update invalid Surname in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Surname for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_user_4(self):
        """@Test: Update invalid Email Address in an User

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update Email Address for all variations in [2]

        @Assert: User is not updated.  Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_user_5(self):
        """@Test: Update different values in Password and verify fields

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update the password by entering different values in Password and
        verify fields

        @Assert: User is not updated.  Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_user_6(self):
        """@Test: [UI ONLY] Attempt to update User info and Cancel

        @Feature: User - Negative Update

        @Steps:
        1. Update Current user with valid Firstname, Surname, Email Address,
        Language, Password/Verify fields
        2. Click Cancel

        @Assert: User is not updated.

        @Status: Manual

        """

    @stubbed()
    def test_positive_delete_user_2(self):
        """@Test: Delete an admin user

        @Feature: User - Positive Delete

        @Steps:
        1. Create an admin user
        2. Delete the User

        @Assert: User is deleted

        @Status: Manual

        """

    @stubbed()
    def test_negative_delete_user_1(self):
        """@Test: [UI ONLY] Attempt to delete an User and cancel

        @Feature: User - Negative Delete

        @Steps:
        1. Create a User
        2. Attempt to delete the user and click Cancel on the confirmation

        @Assert: User is not deleted

        @Status: Manual

        """

    @stubbed()
    def test_negative_delete_user_2(self):
        """@Test: Attempt to delete the last remaining admin user

        @Feature: User - Negative Delete

        @Steps:
        1. Create multiple Users and admin users
        2. Delete the users except the last admin user
        3. Attempt to delete the last admin user

        @Assert: User is not deleted

        @Status: Manual

        """

    @stubbed()
    def test_list_user_1(self):
        """@Test: List User for all variations of Username

        @Feature: User - list

        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed

        @Status: Manual

        """

    @stubbed()
    def test_list_user_2(self):
        """@Test: List User for all variations of Firstname

        @Feature: User - list

        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed

        @Status: Manual

        """

    @stubbed()
    def test_list_user_3(self):
        """@Test: List User for all variations of Surname

        @Feature: User - list

        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. List User

        @Assert: User is listed

        @Status: Manual

        """

    @stubbed()
    def test_list_user_4(self):
        """@Test: List User for all variations of Email Address

        @Feature: User - list

        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. List User

        @Assert: User is listed

        @Status: Manual

        """

    @stubbed()
    def test_list_user_5(self):
        """@Test: List User for all variations of Language

        @Feature: User - list

        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. List User

        @Assert: User is listed

        @Status: Manual

        """

    @stubbed()
    def test_search_user_1(self):
        """@Test: Search User for all variations of Username

        @Feature: User - search

        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """

    @stubbed()
    def test_search_user_2(self):
        """@Test: Search User for all variations of Firstname

        @Feature: User - search

        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """

    @stubbed()
    def test_search_user_3(self):
        """@Test: Search User for all variations of Surname

        @Feature: User - search

        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """

    @stubbed()
    def test_search_user_4(self):
        """@Test: Search User for all variations of Email Address

        @Feature: User - search

        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """

    @stubbed()
    def test_search_user_5(self):
        """@Test: Search User for all variations of Language

        @Feature: User - search

        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. Search/Find User

        @Assert: User is found

        @Status: Manual

        """

    @stubbed()
    def test_info_user_1(self):
        """@Test: Get User info for all variations of Username

        @Feature: User - info

        @Steps:
        1. Create User for all Username variations in [1] using valid
        First Name, Surname, Email Address, Language, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """

    @stubbed()
    def test_info_user_2(self):
        """@Test: Search User for all variations of Firstname

        @Feature: User - search

        @Steps:
        1. Create User for all Firstname variations in [1] using valid
        Username, Surname, Email Address, Language, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """

    @stubbed()
    def test_info_user_3(self):
        """@Test: Search User for all variations of Surname

        @Feature: User - search

        @Steps:
        1. Create User for all Surname variations in [1] using valid
        Username, First Name, Email Address, Language, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """

    @stubbed()
    def test_info_user_4(self):
        """@Test: Search User for all variations of Email Address

        @Feature: User - search

        @Steps:
        1. Create User for all Email Address variations in [1] using valid
        valid Username, First Name, Surname, Language, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """

    @stubbed()
    def test_info_user_5(self):
        """@Test: Search User for all variations of Language

        @Feature: User - search

        @Steps:
        1. Create User for all Language variations using valid
        Username, First Name, Surname, Email Address, authorized by
        2. Get info of the User

        @Assert: User info is displayed

        @Status: Manual

        """

    @stubbed()
    def test_end_to_end_user_1(self):
        """@Test: Create User and perform different operations

        @Feature: User - End to End

        @Steps:
        1. Create User
        2. Login with the new user
        3. Upload Subscriptions
        4. Provision Systems
        5. Add/Remove Users
        6. Add/Remove Orgs
        7. Delete the User

        @Assert: All actions passed

        @Status: Manual

        """

    @stubbed()
    def test_end_to_end_user_2(self):
        """@Test: Create User with no Org assigned and attempt different
        operations

        @Feature: User - End to End

        @Steps:
        1. Create User.  Do not assign any Org
        2. Login with the new user
        3. Attempt to Upload Subscriptions
        4. Attempt to Provision Systems
        5. Attempt to Add/Remove Users
        6. Attempt to Add/Remove Orgs

        @Assert: All actions failed since the User is not assigned to any Org

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_bookmark_1(self):
        """@Test: Create a bookmark with default values

        @Feature: Search bookmark - Positive Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark with default values

        @Assert: Search bookmark is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_bookmark_2(self):
        """@Test: Create a bookmark by altering the default values

        @Feature: Search bookmark - Positive Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark updating all the default values

        @Assert: Search bookmark is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_bookmark_3(self):
        """@Test: Create a bookmark in public mode

        @Feature: Search bookmark - Positive Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark in public mode

        @Assert: Search bookmark is created in public mode and is accessible
        by other users

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_bookmark_4(self):
        """@Test: Create a bookmark in private mode

        @Feature: Search bookmark - Positive Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark in private mode

        @Assert: Search bookmark is created in private mode and is not
        accessible by other users

        @Status: Manual

        """

    @stubbed()
    def test_negative_create_bookmark_1(self):
        """@Test: Create a bookmark with a blank bookmark name

        @Feature: Search bookmark - Negative Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark with a blank bookmark name

        @Assert: Search bookmark not created. Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_create_bookmark_2(self):
        """@Test: Create a bookmark with a blank bookmark query

        @Feature: Search bookmark - Negative Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark with a blank bookmark query

        @Assert: Search bookmark not created. Appropriate error shown.

        @Status: Manual

        """
