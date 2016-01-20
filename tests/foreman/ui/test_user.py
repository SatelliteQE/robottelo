# -*- encoding: utf-8 -*-
"""Test class for Users UI"""

import random
from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import DEFAULT_ORG, LANGUAGES, ROLES
from robottelo.datafactory import (
    invalid_emails_list,
    invalid_names_list,
    invalid_values_list,
    valid_emails_list,
)
from robottelo.decorators import stubbed, tier1, tier2, tier3
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


class UserTestCase(UITestCase):
    """Implements Users tests in UI"""

    @tier1
    def test_positive_create_with_username(self):
        """Create User for all variations of Username

        @Feature: User - Positive Create

        @Assert: User is created successfully
        """
        with Session(self.browser) as session:
            for user_name in valid_strings():
                with self.subTest(user_name):
                    make_user(session, username=user_name)
                    self.assertIsNotNone(self.user.search(user_name))

    @tier1
    def test_positive_create_with_first_name(self):
        """Create User for all variations of First Name

        @Feature: User - Positive Create

        @Assert: User is created successfully
        """
        with Session(self.browser) as session:
            for first_name in valid_strings():
                with self.subTest(first_name):
                    name = gen_string('alpha')
                    make_user(session, username=name, first_name=first_name)
                    self.user.validate_user(name, 'firstname', first_name)

    @tier1
    def test_positive_create_with_surname(self):
        """Create User for all variations of Surname

        @Feature: User - Positive Create

        @Assert: User is created successfully
        """
        with Session(self.browser) as session:
            for last_name in valid_strings(50):
                with self.subTest(last_name):
                    name = gen_string('alpha')
                    make_user(session, username=name, last_name=last_name)
                    self.user.validate_user(name, 'lastname', last_name)

    @tier1
    def test_positive_create_with_email(self):
        """Create User for all variations of Email Address

        @Feature: User - Positive Create

        @Assert: User is created successfully
        """
        with Session(self.browser) as session:
            for email in valid_emails_list():
                with self.subTest(email):
                    name = gen_string('alpha')
                    make_user(session, username=name, email=email)
                    self.user.validate_user(name, 'email', email)

    @tier1
    def test_positive_create_with_language(self):
        """Create User for all variations of Language

        @Feature: User - Positive Create

        @Assert: User is created successfully
        """
        with Session(self.browser) as session:
            for language in LANGUAGES:
                with self.subTest(language):
                    name = gen_string('alpha')
                    make_user(session, username=name, locale=language)
                    self.user.validate_user(name, 'language', language, False)

    @tier1
    def test_positive_create_with_password(self):
        """Create User for all variations of Password

        @Feature: User - Positive Create

        @Assert: User is created successfully
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

    @tier1
    def test_positive_create_admin(self):
        """Create an Admin user

        @Feature: User - Positive Create

        @Assert: Admin User is created successfully
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=user_name, admin=True)
            self.assertIsNotNone(self.user.search(user_name))

    @tier1
    def test_positive_create_with_one_role(self):
        """Create User with one role

        @Feature: User - Positive Create

        @Assert: User is created successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role = entities.Role().create()
        with Session(self.browser) as session:
            make_user(session, username=name, roles=[role.name], edit=True)
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_roles'])
            element = self.user.wait_until_element(
                (strategy, value % role.name))
            self.assertIsNotNone(element)

    @tier2
    def test_positive_create_with_multiple_roles(self):
        """Create User with multiple roles

        @Feature: User - Positive Create

        @Assert: User is created successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role1 = gen_string('alpha')
        role2 = gen_string('alpha')
        for role in [role1, role2]:
            entities.Role(name=role).create()
        with Session(self.browser) as session:
            make_user(session, username=name, roles=[role1, role2], edit=True)
            self.user.search(name).click()
            self.user.wait_for_ajax()
            self.user.click(tab_locators['users.tab_roles'])
            for role in [role1, role2]:
                element = self.user.wait_until_element(
                    (strategy, value % role))
                self.assertIsNotNone(element)

    @tier2
    def test_positive_create_with_all_roles(self):
        """Create User and assign all available roles to it

        @Feature: User - Positive Create

        @Assert: User is created successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name, roles=ROLES, edit=True)
            self.user.search(name).click()
            self.user.wait_for_ajax()
            self.user.click(tab_locators['users.tab_roles'])
            for role in ROLES:
                self.assertIsNotNone(self.user.wait_until_element(
                    (strategy, value % role)))

    @tier1
    def test_positive_create_with_one_org(self):
        """Create User associated to one Org

        @Feature: User - Positive Create

        @Assert: User is created successfully
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
            element = self.user.wait_until_element(
                (strategy, value % org_name))
            self.assertIsNotNone(element)

    @tier2
    def test_positive_create_with_multiple_orgs(self):
        """Create User associated to multiple Orgs

        @Feature: User - Positive Create

        @Assert: User is created successfully
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
            for org_name in [org_name1, org_name2, DEFAULT_ORG]:
                element = self.user.wait_until_element(
                    (strategy, value % org_name))
                self.assertIsNotNone(element)

    @stubbed()
    @tier2
    def test_positive_create_in_ldap_modes(self):
        """Create User in supported ldap modes - (Active Driectory, IPA,
        Posix)

        @Feature: User - Positive Create

        @Assert: User is created without specifying the password

        @Status: Manual

        """

    @tier1
    def test_positive_create_with_default_org(self):
        """Create User and has default organization associated with it

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
            element = session.nav.wait_until_element(
                (strategy, value % org_name))
            self.assertIsNotNone(element)
            # Fetches currently selected option in a normal select.
            option = Select(session.nav.find_element(
                locators['users.default_org'])).first_selected_option
            self.assertEqual(org_name, option.text)

    @tier1
    def test_positive_create_with_default_location(self):
        """Create User and associate a default Location.

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
            element = session.nav.wait_until_element(
                (strategy, value % loc_name))
            self.assertIsNotNone(element)
            # Fetches currently selected option in a normal select.
            option = Select(session.nav.find_element(
                locators['users.default_loc'])).first_selected_option
            self.assertEqual(loc_name, option.text)

    @tier1
    def test_negative_create(self):
        """@Test:[UI ONLY] Enter all User creation details and Cancel

        @Feature: User - Positive Create

        @Assert: User is not created
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(
                session,
                username=user_name,
                first_name=gen_string('alpha'),
                last_name=gen_string('alpha'),
                email=u'{0}@example.com'.format(gen_string('numeric')),
                submit=False,
            )
            self.assertIsNone(self.user.search(user_name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create User with invalid User Name

        @Feature: User - Negative Create

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

    @tier1
    def test_negative_create_with_invalid_firstname(self):
        """Create User with invalid FirstName

        @Feature: User - Negative Create

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

    @tier1
    def test_negative_create_with_invalid_surname(self):
        """Create User with invalid Surname

        @Feature: User - Negative Create

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

    @tier1
    def test_negative_create_with_invalid_emails(self):
        """Create User with invalid Email Address

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        with Session(self.browser) as session:
            for email in invalid_emails_list():
                with self.subTest(email):
                    name = gen_string('alpha')
                    make_user(session, username=name, email=email)
                    self.assertIsNotNone(
                        self.user.wait_until_element(
                            common_locators['haserror'])
                    )

    @tier1
    def test_negative_create_with_blank_auth(self):
        """Create User with blank value for 'Authorized by' field

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        with Session(self.browser) as session:
            make_user(session, username=gen_string('alpha'), authorized_by='')
            self.assertIsNotNone(
                self.user.wait_until_element(common_locators['haserror']))

    @tier1
    def test_negative_create_with_wrong_pass_confirmation(self):
        """Create User with non-matching values in Password and verify

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        with Session(self.browser) as session:
            make_user(
                session,
                username=gen_string('alpha'),
                password1=gen_string('alpha'),
                password2=gen_string('alpha'),
            )
            self.assertIsNotNone(
                self.user.wait_until_element(common_locators['haserror']))

    @tier1
    def test_positive_update_username(self):
        """Update Username in User

        @Feature: User - Positive Update

        @Assert: User is updated successfully
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

    @tier1
    def test_positive_update_firstname(self):
        """Update first name in User

        @Feature: User - Positive Update

        @Assert: User is updated successful
        """
        first_name = gen_string('alpha')
        new_first_name = gen_string('alpha')
        username = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=username, first_name=first_name)
            self.user.update(username, first_name=new_first_name)
            self.user.validate_user(username, 'firstname', new_first_name)

    @tier1
    def test_positive_update_surname(self):
        """Update surname in User

        @Feature: User - Positive Update

        @Assert: User is updated successful
        """
        last_name = gen_string('alpha')
        new_last_name = gen_string('alpha')
        username = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=username, last_name=last_name)
            self.user.update(username, last_name=new_last_name)
            self.user.validate_user(username, 'lastname', new_last_name)

    @tier1
    def test_positive_update_email(self):
        """Update Email Address in User

        @Feature: User - Positive Update

        @Assert: User is updated successfully
        """
        email = u'{0}@example.com'.format(gen_string('alpha'))
        new_email = u'{0}@myexample.com'.format(gen_string('alpha'))
        username = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=username, email=email)
            self.user.update(username, email=new_email)
            self.user.validate_user(username, 'email', new_email)

    @tier1
    def test_positive_update_language(self):
        """Update Language in User

        @Feature: User - Positive Update

        @Assert: User is updated successfully
        """
        locale = random.choice(LANGUAGES)
        username = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=username)
            self.user.update(username, locale=locale)
            self.user.validate_user(username, 'language', locale, False)

    @tier1
    def test_positive_update_password(self):
        """Update password for a user

        @Feature: User - Update

        @Assert: User password is updated successfully

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

    @tier1
    def test_positive_update_to_non_admin(self):
        """Convert an user from an admin user to non-admin user

        @Feature: User - Positive Update

        @Assert: User is updated and has proper admin role value
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=user_name, admin=True)
            self.assertIsNotNone(self.user.search(user_name))
            self.assertFalse(
                self.user.user_admin_role_toggle(user_name, False))

    @tier1
    def test_positive_update_to_admin(self):
        """Convert a user to an admin user

        @Feature: User - Positive Update

        @Assert: User is updated and has proper admin role value
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=user_name, admin=False)
            self.assertIsNotNone(self.user.search(user_name))
            self.assertTrue(self.user.user_admin_role_toggle(user_name, True))

    @tier1
    def test_positive_update_role(self):
        """Update role for a user

        @Feature: User - Update

        @Assert: User role is updated
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role_name = entities.Role().create().name
        with Session(self.browser) as session:
            make_user(session, username=name)
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_roles'])
            self.assertIsNone(
                self.user.wait_until_element((strategy, value % role_name)))
            self.user.update(name, new_roles=[role_name])
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_roles'])
            self.assertIsNotNone(
                self.user.wait_until_element((strategy, value % role_name)))

    @tier2
    def test_positive_update_with_multiple_roles(self):
        """Update User with multiple roles

        @Feature: User - Positive Update

        @Assert: User is updated successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role_names = [
            entities.Role().create().name
            for _ in range(3)
        ]
        with Session(self.browser) as session:
            make_user(session, username=name)
            self.user.update(name, new_roles=role_names)
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_roles'])
            for role in role_names:
                self.assertIsNotNone(
                    self.user.wait_until_element((strategy, value % role)))

    @tier2
    def test_positive_update_with_all_roles(self):
        """Update User with all roles

        @Feature: User - Positive Update

        @Assert: User is updated successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            self.user.update(name, new_roles=ROLES)
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_roles'])
            for role in ROLES:
                self.assertIsNotNone(
                    self.user.wait_until_element((strategy, value % role)))

    @tier1
    def test_positive_update_org(self):
        """Assign a User to an Org

        @Feature: User - Positive Update

        @Assert: User is updated successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            make_user(session, username=name)
            self.user.update(name, new_organizations=[org_name])
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_organizations'])
            element = self.user.wait_until_element(
                (strategy, value % org_name))
            self.assertIsNotNone(element)

    @tier2
    def test_positive_update_orgs(self):
        """Assign a User to multiple Orgs

        @Feature: User - Positive Update

        @Assert: User is updated
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_names = [
            entities.Organization().create().name
            for _ in range(3)
        ]
        with Session(self.browser) as session:
            make_user(session, username=name)
            self.user.update(name, new_organizations=org_names)
            self.user.search(name).click()
            self.user.click(tab_locators['users.tab_organizations'])
            for org in org_names:
                self.assertIsNotNone(
                    self.user.wait_until_element((strategy, value % org)))

    @tier1
    def test_negative_update_username(self):
        """Update invalid Username in an User

        @Feature: User - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            for new_user_name in invalid_names_list():
                with self.subTest(new_user_name):
                    self.user.update(name, new_username=new_user_name)
                    self.assertIsNotNone(
                        self.user.wait_until_element(
                            common_locators['haserror'])
                    )

    @tier1
    def test_negative_update_firstname(self):
        """Update invalid Firstname in an User

        @Feature: User - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            for new_first_name in invalid_names_list():
                with self.subTest(new_first_name):
                    self.user.update(name, first_name=new_first_name)
                    self.assertIsNotNone(
                        self.user.wait_until_element(
                            common_locators['haserror'])
                    )

    @tier1
    def test_negative_update_surname(self):
        """Update invalid Surname in an User

        @Feature: User - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            for new_surname in invalid_names_list():
                with self.subTest(new_surname):
                    self.user.update(name, last_name=new_surname)
                    self.assertIsNotNone(
                        self.user.wait_until_element(
                            common_locators['haserror'])
                    )

    @tier1
    def test_negative_update_email(self):
        """Update invalid Email Address in an User

        @Feature: User - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            for new_email in invalid_emails_list():
                with self.subTest(new_email):
                    self.user.update(name, email=new_email)
                    self.assertIsNotNone(
                        self.user.wait_until_element(
                            common_locators['haserror'])
                    )

    @stubbed()
    @tier1
    def test_negative_update_password(self):
        """Update different values in Password and verify fields

        @Feature: User - Negative Update

        @Steps:
        1. Create User
        2. Update the password by entering different values in Password and
        verify fields

        @Assert: User is not updated.  Appropriate error shown.

        @Status: Manual
        """

    @tier1
    def test_negative_update(self):
        """[UI ONLY] Attempt to update User info and Cancel

        @Feature: User - Negative Update

        @Assert: User is not updated.
        """
        new_first_name = gen_string('alpha')
        new_last_name = gen_string('alpha')
        username = gen_string('alpha')
        new_username = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=username)
            self.user.update(
                username,
                new_username=new_username,
                first_name=new_first_name,
                last_name=new_last_name,
                submit=False,
            )
            self.assertIsNotNone(self.user.search(username))
            self.assertIsNone(self.user.search(new_username))

    @tier1
    def test_positive_delete_user(self):
        """Delete an existing User

        @Feature: User - Delete

        @Assert: User is deleted successfully
        """
        with Session(self.browser) as session:
            for user_name in valid_strings():
                with self.subTest(user_name):
                    make_user(session, username=user_name)
                    self.user.delete(user_name)

    @tier1
    def test_positive_delete_admin(self):
        """Delete an admin user

        @Feature: User - Positive Delete

        @Assert: User is deleted
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=user_name, admin=True)
            self.assertIsNotNone(self.user.search(user_name))
            self.user.delete(user_name)

    @tier1
    def test_negative_delete_user(self):
        """[UI ONLY] Attempt to delete an User and cancel

        @Feature: User - Negative Delete

        @Assert: User is not deleted
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=user_name)
            self.assertIsNotNone(self.user.search(user_name))
            self.user.delete(user_name, really=False)

    @stubbed()
    @tier2
    def test_negative_delete_last_admin(self):
        """Attempt to delete the last remaining admin user

        @Feature: User - Negative Delete

        @Steps:
        1. Create multiple Users and admin users
        2. Delete the users except the last admin user
        3. Attempt to delete the last admin user

        @Assert: User is not deleted

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_end_to_end(self):
        """Create User and perform different operations

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
    @tier3
    def test_positive_end_to_end_without_org(self):
        """Create User with no Org assigned and attempt different
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
    @tier2
    def test_positive_create_bookmark_default(self):
        """Create a bookmark with default values

        @Feature: Search bookmark - Positive Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark with default values

        @Assert: Search bookmark is created

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_create_bookmark_alter_default(self):
        """Create a bookmark by altering the default values

        @Feature: Search bookmark - Positive Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark updating all the default values

        @Assert: Search bookmark is created

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_create_bookmark_public(self):
        """Create a bookmark in public mode

        @Feature: Search bookmark - Positive Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark in public mode

        @Assert: Search bookmark is created in public mode and is accessible
        by other users

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_create_bookmark_private(self):
        """Create a bookmark in private mode

        @Feature: Search bookmark - Positive Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark in private mode

        @Assert: Search bookmark is created in private mode and is not
        accessible by other users

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_negative_create_bookmark_with_blank_name(self):
        """Create a bookmark with a blank bookmark name

        @Feature: Search bookmark - Negative Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark with a blank bookmark name

        @Assert: Search bookmark not created. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_negative_create_bookmark_with_blank_query(self):
        """Create a bookmark with a blank bookmark query

        @Feature: Search bookmark - Negative Create

        @Steps:
        1. Search for a criteria
        2. Create bookmark with a blank bookmark query

        @Assert: Search bookmark not created. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_set_timezone(self):
        """Set a new timezone for the user

        @Feature: User timezone

        @Steps:

        1.Navigate to Administer -> Users
        2.Click on the User
        3.Select the Timezone Dropdown list
        4.Try to apply some timezone

        @Assert: User should be able to change timezone

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_dashboard_shows_new_time(self):
        """Check if the Dashboard shows the time according to the new
        timezone set

        @Feature: User timezone

        @Steps:

        1.Change the timezone for a user in Administer -> Users tab
        2.Navigate to Monitor -> Dashboard
        3.The left corner displays time according to the new timezone set

        @Assert: Dashboard UI displays new time based on the new timezone

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_logfiles_shows_new_time(self):
        """Check if the logfiles reflect the new timezone set by
        the user

        @Feature: User timezone

        @Steps:

        1.Change the timezones for user in Administer -> Users Tab
        2.Try to modify content view or environment
        so that the changes are reflected in log file
        3.Check if log file shows the new timezone set

        @Assert: Logfiles display time according to changed timezone

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_mails_for_new_timezone(self):
        """Check if the mails are received according to new
        timezone set by the user

        @Feature: User timezone

        @Steps:

        1.Change the timezones for user in Administer -> Users tab
        2.Navigate to Administer -> Users tab
        3.Make sure under Email Preferences -> Mail Enabled
        4.Send daily/weekly/monthly mails

        @Assert: Emails are sent according to new timezone set

        @Status: Manual
        """
