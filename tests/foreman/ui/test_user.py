# -*- encoding: utf-8 -*-
"""Test class for Users UI

:Requirement: User

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import random
from fauxfactory import gen_string
from nailgun import entities
from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    LANGUAGES,
    LDAP_ATTR,
    LDAP_SERVER_TYPE,
    ROLES,
    TIMEZONES,
)
from robottelo.datafactory import (
    filtered_datapoint,
    invalid_emails_list,
    invalid_names_list,
    invalid_values_list,
    valid_data_list,
    valid_emails_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_user,
    make_usergroup,
    set_context,
)
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from robozilla.decorators import skip_if_bug_open


@filtered_datapoint
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

    @classmethod
    def setUpClass(cls):
        super(UserTestCase, cls).setUpClass()
        # Check whether necessary plug-ins are installed for server instance
        result = ssh.command(
            'rpm -qa | grep rubygem-foreman_remote_execution'
        )
        if result.return_code != 0:
            ROLES.remove('Remote Execution Manager')
            ROLES.remove('Remote Execution User')

    @tier1
    def test_positive_create_with_username(self):
        """Create User for all variations of Username

        :id: 2acc8c7d-cb14-4eda-98f9-fb379950f2f5

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for user_name in valid_strings():
                with self.subTest(user_name):
                    make_user(session, username=user_name)
                    self.assertIsNotNone(self.user.search(user_name))

    @tier1
    def test_positive_create_with_first_name(self):
        """Create User for all variations of First Name

        :id: dd398cd6-821e-4b0e-a111-22d5a6eeafd8

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for first_name in valid_strings():
                with self.subTest(first_name):
                    name = gen_string('alpha')
                    make_user(session, username=name, first_name=first_name)
                    self.user.validate_user(name, 'firstname', first_name)

    @tier1
    def test_positive_create_with_surname(self):
        """Create User for all variations of Surname

        :id: 0a2dc093-0cd1-41eb-99cd-79935c74563f

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for last_name in valid_strings(50):
                with self.subTest(last_name):
                    name = gen_string('alpha')
                    make_user(session, username=name, last_name=last_name)
                    self.user.validate_user(name, 'lastname', last_name)

    @tier1
    def test_positive_create_with_email(self):
        """Create User for all variations of Email Address

        :id: 1c6c0f50-401c-4b7d-9795-97a1be3806f8

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for email in valid_emails_list():
                with self.subTest(email):
                    name = gen_string('alpha')
                    make_user(session, username=name, email=email)
                    self.user.validate_user(name, 'email', email)

    @tier1
    def test_positive_create_with_description(self):
        """Create User for all variations of Description

        :id: eebeb6d3-c99f-4dc2-991c-0e8268187110

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for description in valid_data_list():
                with self.subTest(description):
                    name = gen_string('alpha')
                    make_user(session, username=name, description=description)
                    self.user.validate_user(
                        name, 'description', description, False
                    )

    @tier1
    def test_positive_create_with_language(self):
        """Create User for all variations of Language

        :id: 1c5581a8-79ae-40a6-8052-f47be2d4c5eb

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for language in LANGUAGES:
                with self.subTest(language):
                    name = gen_string('alpha')
                    make_user(session, username=name, locale=language)
                    self.user.validate_user(name, 'language', language, False)

    @tier1
    def test_positive_create_with_password(self):
        """Create User for all variations of Password

        :id: 83d6efe0-7526-465c-9c97-5673c7736fc4

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        test_data = valid_strings()
        extra_passwords = (
            u'foo@!#$^&*( ) {0}'.format(gen_string('alpha', 2)),
            u'bar+{{}}|\"?hi {0}'.format(gen_string('alpha', 2)),
        )
        test_data.extend(extra_passwords)
        with Session(self) as session:
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
    @upgrade
    def test_positive_create_admin(self):
        """Create an Admin user

        :id: 9bf56045-1026-435c-bf4c-623e160582d5

        :expectedresults: Admin User is created successfully

        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=user_name, admin=True)
            self.assertIsNotNone(self.user.search(user_name))

    @tier1
    def test_positive_create_with_one_role(self):
        """Create User with one role

        :id: 6d6c795e-8b46-4f0f-84e1-f7e22add6173

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        role = entities.Role().create()
        with Session(self) as session:
            make_user(session, username=name, roles=[role.name], edit=True)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_roles'])
            element = self.user.wait_until_element(
                common_locators['entity_deselect'] % role.name)
            self.assertIsNotNone(element)

    @tier1
    def test_positive_create_with_one_org(self):
        """Create User associated to one Org

        :id: 830bc5fc-e773-466c-9b38-4f33a2c1d05e

        :expectedresults: User is created successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self) as session:
            make_user(
                session, username=name, organizations=[org_name], edit=True)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_organizations'])
            element = self.user.wait_until_element(
                common_locators['entity_deselect'] % org_name)
            self.assertIsNotNone(element)

    @tier1
    def test_positive_create_with_default_org(self):
        """Create User and has default organization associated with it

        :id: 3d51dead-9053-427d-8292-c42e87ed6289

        :expectedresults: User is created with default Org selected.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self) as session:
            make_user(session, username=name, organizations=[org_name],
                      edit=True, default_org=org_name)
            self.user.search_and_click(name)
            self.user.click(tab_locators['users.tab_organizations'])
            element = session.nav.wait_until_element(
                common_locators['entity_deselect'] % org_name)
            self.assertIsNotNone(element)
            # Check that default organization value was really chosen
            self.assertEqual(org_name, session.nav.find_element(
                locators['users.default_org_value']).text)

    @tier1
    def test_positive_create_with_default_location(self):
        """Create User and associate a default Location.

        :id: 952a0be5-d393-49a2-8fd9-f6dfcc31f762

        :expectedresults: User is created with default Location selected.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        loc_name = gen_string('alpha')
        entities.Location(name=loc_name).create()
        with Session(self) as session:
            make_user(session, username=name, locations=[loc_name],
                      edit=True, default_loc=loc_name)
            self.user.search_and_click(name)
            self.user.click(tab_locators['users.tab_locations'])
            element = session.nav.wait_until_element(
                common_locators['entity_deselect'] % loc_name)
            self.assertIsNotNone(element)
            # Check that default location value was really chosen
            self.assertEqual(loc_name, session.nav.find_element(
                locators['users.default_loc_value']).text)

    @tier1
    def test_negative_create(self):
        """Enter all User creation details and Cancel

        :id: 2774be2f-303e-498f-8072-80462f33c52e

        :expectedresults: User is not created

        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 31bbe350-0275-4aaf-99ec-3f77bfd4ba00

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for user_name in invalid_values_list(interface='ui'):
                with self.subTest(user_name):
                    make_user(session, username=user_name)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_create_with_invalid_firstname(self):
        """Create User with invalid FirstName

        :id: 21525bf2-4de9-43f0-8c92-b2fad1fdc944

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            # invalid_values_list is not used here because first name is an
            # optional field
            for first_name in invalid_names_list():
                with self.subTest(first_name):
                    make_user(
                        session,
                        username=gen_string('alpha'),
                        first_name=first_name,
                    )
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_create_with_invalid_surname(self):
        """Create User with invalid Surname

        :id: 47d9e8be-3b29-4a56-85d7-898145b5b034

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            # invalid_values_list is not used here because sur name is an
            # optional field
            for last_name in invalid_names_list():
                with self.subTest(last_name):
                    make_user(
                        session,
                        username=gen_string('alpha'),
                        last_name=last_name,
                    )
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_create_with_invalid_emails(self):
        """Create User with invalid Email Address

        :id: 36511b82-e070-41ea-81fa-6e29faa9da1c

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for email in invalid_emails_list():
                with self.subTest(email):
                    name = gen_string('alpha')
                    make_user(session, username=name, email=email)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_create_with_blank_auth(self):
        """Create User with blank value for 'Authorized by' field

        :id: 68f670ed-ac6e-4052-889c-6671d659e510

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_user(session, username=gen_string('alpha'), authorized_by='')
            self.assertIsNotNone(
                self.user.wait_until_element(common_locators['haserror']))

    @tier1
    def test_negative_create_with_wrong_pass_confirmation(self):
        """Create User with non-matching values in Password and verify

        :id: f818e5fc-b378-4bc7-afa8-18b23ee05053

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_user(
                session,
                username=gen_string('alpha'),
                password1=gen_string('alpha'),
                password2=gen_string('alpha'),
            )
            self.assertIsNotNone(
                self.user.wait_until_element(common_locators['haserror']))

    @tier1
    def test_positive_search_by_usergroup(self):
        """Create few users and assign them to usergroup. Perform search for
        users by usergroup they are assigned to

        :id: dceebf68-8d82-4214-9829-350830a78cdd

        :expectedresults: Necessary users can be found and no error raised

        :BZ: 1395667

        :CaseImportance: Critical
        """
        group_name = gen_string('alpha')
        org = entities.Organization().create()
        # Create new users
        user_names = [
            entities.User(organization=[org]).create().login
            for _ in range(2)
        ]
        with Session(self) as session:
            make_usergroup(
                session,
                name=group_name,
                users=user_names,
                org=org.name,
            )
            for user_name in user_names:
                self.assertIsNotNone(
                    self.user.search(
                        user_name,
                        _raw_query='usergroup = {}'.format(group_name)
                    )
                )
                self.assertIsNone(
                    self.user.wait_until_element(
                        common_locators['haserror'], timeout=3)
                )

    @tier1
    def test_positive_update_username(self):
        """Update Username in User

        :id: 4ecb2816-9bef-4089-86a0-02d7d065cdb1

        :expectedresults: User is updated successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        password = gen_string('alpha')
        with Session(self) as session:
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
                with Session(self):
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

        :id: 03ef8a7f-2bf1-4314-b0cd-a7a6acfc17ea

        :expectedresults: User is updated successful

        :CaseImportance: Critical
        """
        first_name = gen_string('alpha')
        new_first_name = gen_string('alpha')
        username = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=username, first_name=first_name)
            self.user.update(username, first_name=new_first_name)
            self.user.validate_user(username, 'firstname', new_first_name)

    @tier1
    def test_positive_update_surname(self):
        """Update surname in User

        :id: 0326d221-28b0-4a6b-934e-b67ee6c9f696

        :expectedresults: User is updated successful

        :CaseImportance: Critical
        """
        last_name = gen_string('alpha')
        new_last_name = gen_string('alpha')
        username = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=username, last_name=last_name)
            self.user.update(username, last_name=new_last_name)
            self.user.validate_user(username, 'lastname', new_last_name)

    @tier1
    def test_positive_update_email(self):
        """Update Email Address in User

        :id: e48314b7-2a49-48ec-896d-af7bf427b1c4

        :expectedresults: User is updated successfully

        :CaseImportance: Critical
        """
        email = u'{0}@example.com'.format(gen_string('alpha'))
        new_email = u'{0}@myexample.com'.format(gen_string('alpha'))
        username = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=username, email=email)
            self.user.update(username, email=new_email)
            self.user.validate_user(username, 'email', new_email)

    @tier1
    def test_positive_update_description(self):
        """Update Description in User

        :id: f08ee305-0e0b-4df0-82d9-d10edcfa66c0

        :expectedresults: User is updated successfully

        :CaseImportance: Critical
        """
        username = gen_string('alpha')
        description = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=username, description=description)
            for new_description in valid_data_list():
                with self.subTest(new_description):
                    self.user.update(username, description=new_description)
                    self.user.validate_user(
                        username, 'description', new_description, False
                    )

    @tier1
    def test_positive_update_language(self):
        """Update Language in User

        :id: 64b6a90e-0d4c-4a55-a4bd-7347010e39f2

        :expectedresults: User is updated successfully

        :CaseImportance: Critical
        """
        locale = random.choice(list(LANGUAGES.keys()))
        username = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=username)
            self.user.update(username, locale=locale)
            self.user.validate_user(username, 'language', locale, False)

    @tier1
    @upgrade
    def test_positive_update_password(self):
        """Update password for a user

        :id: db57c3bc-4fae-4ee7-bf6d-8e0bcc7fd55c

        :expectedresults: User password is updated successfully


        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        new_password = gen_string('alpha')
        with Session(self) as session:
            # Role 'Site' meaning 'Site Manager' here
            make_user(session, username=user_name, edit=True, roles=['Site'])
            self.user.update(
                user_name,
                new_password=new_password,
                password_confirmation=new_password,
            )
            self.login.logout()
            self.login.login(user_name, new_password)
            self.assertTrue(self.login.is_logged())

    @tier1
    def test_positive_update_to_non_admin(self):
        """Convert an user from an admin user to non-admin user

        :id: b41cbcf8-d819-4daa-b217-a4812541dca3

        :expectedresults: User is updated and has proper admin role value

        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=user_name, admin=True)
            self.assertIsNotNone(self.user.search(user_name))
            self.assertFalse(
                self.user.user_admin_role_toggle(user_name, False))

    @tier1
    def test_positive_update_to_admin(self):
        """Convert a user to an admin user

        :id: d3cdda62-1384-4b49-97a3-0c66764583bb

        :expectedresults: User is updated and has proper admin role value

        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=user_name, admin=False)
            self.assertIsNotNone(self.user.search(user_name))
            self.assertTrue(self.user.user_admin_role_toggle(user_name, True))

    @tier1
    def test_positive_update_role(self):
        """Update role for a user

        :id: 2a13529c-3863-403b-a319-9569ca1287cb

        :expectedresults: User role is updated

        :CaseImportance: Critical
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role_name = entities.Role().create().name
        with Session(self) as session:
            make_user(session, username=name)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_roles'])
            self.assertIsNone(
                self.user.wait_until_element((strategy, value % role_name)))
            self.user.update(name, new_roles=[role_name])
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_roles'])
            self.assertIsNotNone(
                self.user.wait_until_element((strategy, value % role_name)))

    @tier1
    def test_positive_update_org(self):
        """Assign a User to an Org

        :id: d891e54b-76bf-4537-8eb9-c3f8832e4c2c

        :expectedresults: User is updated successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self) as session:
            make_user(session, username=name)
            self.user.update(name, new_organizations=[org_name])
            self.user.search_and_click(name)
            self.user.click(tab_locators['users.tab_organizations'])
            element = self.user.wait_until_element(
                common_locators['entity_deselect'] % org_name)
            self.assertIsNotNone(element)

    @tier1
    def test_negative_update_username(self):
        """Update invalid Username in an User

        :id: 7019461e-13c6-4761-b3e9-4df81abcd0f9

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=name)
            for new_user_name in invalid_names_list():
                with self.subTest(new_user_name):
                    self.user.update(name, new_username=new_user_name)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_update_firstname(self):
        """Update invalid Firstname in an User

        :id: 1e3945d1-5b47-45ca-aff9-3ddd44688e6b

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=name)
            for new_first_name in invalid_names_list():
                with self.subTest(new_first_name):
                    self.user.update(name, first_name=new_first_name)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_update_surname(self):
        """Update invalid Surname in an User

        :id: 14033c1f-4c7e-4ee5-8ffc-76c4dd672cc1

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=name)
            for new_surname in invalid_names_list():
                with self.subTest(new_surname):
                    self.user.update(name, last_name=new_surname)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_update_email(self):
        """Update invalid Email Address in an User

        :id: 6aec3816-16ca-487a-b0f1-a5c1fbc3e0a3

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=name)
            for new_email in invalid_emails_list():
                with self.subTest(new_email):
                    self.user.update(name, email=new_email)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_update_password(self):
        """Update different values in Password and verify fields

        :id: ab4a5dbf-70c2-4adc-b948-bc350329e166

        :Steps:
            1. Create User
            2. Update the password by entering different values in Password and
                verify fields

        :expectedresults: User is not updated.  Appropriate error shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=name)
            self.user.update(
                name,
                new_password=gen_string('alphanumeric'),
                password_confirmation=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.user.wait_until_element(
                common_locators['haserror']))

    @tier1
    def test_negative_update_password_empty_confirmation(self):
        """Update user password without providing confirmation value

        :id: c2b569c9-8120-4125-8bfe-61324a881395

        :Steps:
            1. Create User
            2. Update the password by entering value only in Password field

        :expectedresults: User is not updated.  Appropriate error shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=name)
            self.user.update(
                name,
                new_password=gen_string('alphanumeric'),
                password_confirmation='',
            )
            self.assertIsNotNone(self.user.wait_until_element(
                common_locators['haserror']))

    @tier1
    def test_negative_update(self):
        """[UI ONLY] Attempt to update User info and Cancel

        :id: 56c8ea13-4add-4a51-8428-9d9f9ddde33e

        :expectedresults: User is not updated.

        :CaseImportance: Critical
        """
        new_first_name = gen_string('alpha')
        new_last_name = gen_string('alpha')
        username = gen_string('alpha')
        new_username = gen_string('alpha')
        with Session(self) as session:
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
    @upgrade
    def test_positive_delete_user(self):
        """Delete an existing User

        :id: 49534eda-f8ea-404e-9714-a8d0d2210979

        :expectedresults: User is deleted successfully

        :CaseImportance: Critical
        """
        user_name = gen_string('alphanumeric')
        with Session(self) as session:
            make_user(session, username=user_name)
            self.user.delete(user_name)

    @tier1
    @upgrade
    def test_positive_delete_admin(self):
        """Delete an admin user

        :id: afda171a-b464-461f-93ce-96d770935200

        :expectedresults: User is deleted

        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=user_name, admin=True)
            self.assertIsNotNone(self.user.search(user_name))
            self.user.delete(user_name)

    @tier1
    def test_negative_delete_user(self):
        """[UI ONLY] Attempt to delete an User and cancel

        :id: 43aed0c0-a3c3-4044-addc-910dc29e4f37

        :expectedresults: User is not deleted

        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        with Session(self) as session:
            make_user(session, username=user_name)
            self.assertIsNotNone(self.user.search(user_name))
            self.user.delete(user_name, really=False)

    @tier1
    def test_positive_set_timezone(self):
        """Set a new timezone for the user

        :id: 3219c245-2914-4412-8df1-72e041a58a9f

        :Steps:

            1. Navigate to Administer -> Users
            2. Click on the User
            3. Select the Timezone Dropdown list
            4. Try to apply some timezone

        :expectedresults: User should be able to change timezone

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for timezone in TIMEZONES:
                with self.subTest(timezone):
                    name = gen_string('alpha')
                    make_user(session, username=name, timezone=timezone)
                    self.user.validate_user(name, 'timezone', timezone, False)

    @stubbed()
    @tier1
    def test_positive_dashboard_shows_new_time(self):
        """Check if the Dashboard shows the time according to the new
        timezone set

        :id: c2d80855-631c-46f6-8950-c296df8c0cbe

        :Steps:

            1. Change the timezone for a user in Administer -> Users tab
            2. Navigate to Monitor -> Dashboard
            3. The left corner displays time according to the new timezone set

        :expectedresults: Dashboard UI displays new time based on the new
            timezone

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier2
    def test_positive_logfiles_shows_new_time(self):
        """Check if the logfiles reflect the new timezone set by
        the user

        :id: b687182b-9d4f-4ff4-9f19-1b6ae3c126ad

        :Steps:

            1. Change the timezones for user in Administer -> Users Tab
            2. Try to modify content view or environment so that the changes
               are reflected in log file
            3. Check if log file shows the new timezone set

        :expectedresults: Logfiles display time according to changed timezone

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_mails_for_new_timezone(self):
        """Check if the mails are received according to new
        timezone set by the user

        :id: ab34dd9d-4fc1-43f1-b40a-b0ebf0802887

        :Steps:

            1. Change the timezones for user in Administer -> Users tab
            2. Navigate to Administer -> Users tab
            3. Make sure under Email Preferences -> Mail Enabled
            4. Send daily/weekly/monthly mails

        :expectedresults: Emails are sent according to new timezone set

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_positive_parameters_tab_access_with_edit_params(self):
        """Check if non admin users with edit_params permission can access
        parameters tab on organization details screen

        :id: 086ea8bf-2219-425e-acf4-d2ba59a77ee9

        :BZ: 1354572

        :Steps:

            1. Create a Role in Administer -> Roles
            2. On Role creation set Resource type to Parameters
            3. On Role creation add permission edit_params
            4. On Role creation set Resource type to Organization
            5. On Role creation add permissions edit_organizations and
                view_organizations
            6. Create a non admin user in Administer -> Users
            7. Add previous role to this user
            8. Login with previous user credentials
            9. Go to Organization -> Manage Organizations
            10. Choose Default Organization
            11. Assert "Parameters" tab is present

        :expectedresults: Parameters tab visible to users with edit_params
            permission

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_parameters_tab_access_without_edit_params(self):
        """Check if non admin users without edit_params permission can not
        access parameters tab on organization details screen

        :id: eac65b64-16d4-4df5-8402-e58ddb31050d

        :BZ: 1354572

        :Steps:

            1. Create a Role in Administer -> Roles
            2. On Role creation set Resource type to Organization
            3. On Role creation add permissions edit_organizations and
                view_organizations
            4. Create a non admin user in Administer -> Users
            5. Add previous role to this user
            6. Login with previous user credentials
            7. Go to Organization -> Manage Organizations
            8. Choose Default Organization
            9. Assert "Parameters" tab is not present

        :expectedresults: Parameters tab not visible to users with no
            edit_params permission

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """


@run_in_one_thread
class ActiveDirectoryUserTestCase(UITestCase):
    """Implements Active Directory feature tests for user in UI."""

    @classmethod
    @skip_if_not_set('ldap')
    def setUpClass(cls):  # noqa
        super(ActiveDirectoryUserTestCase, cls).setUpClass()
        cls.ldap_user_name = settings.ldap.username
        cls.ldap_user_passwd = settings.ldap.password
        cls.base_dn = settings.ldap.basedn
        cls.group_base_dn = settings.ldap.grpbasedn
        cls.ldap_hostname = settings.ldap.hostname
        cls.usergroup_name = gen_string('alpha')

        authsource_attrs = entities.AuthSourceLDAP(
            onthefly_register=True,
            account=cls.ldap_user_name,
            account_password=cls.ldap_user_passwd,
            base_dn=cls.base_dn,
            groups_base=cls.group_base_dn,
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login_ad'],
            server_type=LDAP_SERVER_TYPE['API']['ad'],
            attr_mail=LDAP_ATTR['mail'],
            name=gen_string('alpha'),
            host=cls.ldap_hostname,
            tls=False,
            port='389',
        ).create()
        cls.ldap_server_name = authsource_attrs.name

    def check_external_user(self):
        """Check whether external user is active and reachable. That
        operation also add that user into application system for internal
        configuration procedures
        """
        with Session(self, self.ldap_user_name, self.ldap_user_passwd):
            self.assertIsNotNone(self.login.wait_until_element(
                locators['login.loggedin'] % self.ldap_user_name
            ))

    def tearDown(self):
        with Session(self) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            if self.user.search(self.ldap_user_name):
                self.user.delete(self.ldap_user_name)
        super(ActiveDirectoryUserTestCase, self).tearDown()


class SshKeyInUserTestCase(UITestCase):
    """Implements the SSH Key in User Tests"""

    @stubbed()
    @tier2
    def test_positive_ssh_key_tab_presence(self):
        """SSH keys tab presence in User details page

        :id: a0c77cc1-0484-4290-b4b3-87ab3d0bde56

        :steps:

            1. Go to Administer -> Users
            2. Attempt to create new user form Super admin
            3. Verify SSH Keys tab in user details page

        :expectedresults: New user details page should have a tab of SSH Keys
        """

    @stubbed()
    @tier2
    def test_positive_ssh_key_tab_presence_Super_Admin(self):
        """SSH keys tab presence in Super Admin details page

        :id: 72dc8c6e-3627-436a-adf3-f32d09b2f1c7

        :steps:

            1. Go to Administer -> Users
            2. Edit Super Admin user details page
            3. Verify SSH Keys tab in Super Admin user details page

        :expectedresults: Super Admin user details page should have a tab of
            SSH Keys
        """

    @stubbed()
    @tier1
    @skip_if_bug_open('bugzilla', 1465389)
    def test_positive_create_ssh_key(self):
        """SSH Key can be added while creating a new user

        :id: e608f1b2-2ca4-4c32-8a70-47bed63e8b09

        :steps:

            1. Go to Administer -> Users
            2. Attempt to create new user with all the details
            3. Add SSH Key in SSH Keys tab before saving the user
            4. Save the new User

        :expectedresults: New user should be added with SSH key
        """

    @stubbed()
    @tier1
    def test_positive_create_ssh_key_super_admin(self):
        """SSH Key can be added to Super Admin user details page

        :id: 31388483-35f5-4828-82e9-9305a76e712d

        :steps:

            1. Go to Administer -> Users
            2. Edit Super Admin user details page
            3. Add SSH Key in SSH Keys tab
            4. Save the changes of Super Admin user

        :expectedresults: Super Admin should be saved with SSH key
        """

    @stubbed()
    @tier1
    @skip_if_bug_open('bugzilla', 1465389)
    def test_positive_create_multiple_ssh_keys(self):
        """Multiple SSH Keys can be added while creating a new user

        :id: 6552194f-63ff-4a6e-9784-5b3dc1772fd5

        :steps:

            1. Go to Administer -> Users
            2. Attempt to create new user with all the details
            3. Add multiple SSH Keys in SSH Keys tab before saving the user
            4. Save the new User

        :expectedresults: New user should be added with multiple SSH keys
        """

    @stubbed()
    @tier1
    def test_positive_create_multiple_ssh_keys_super_admin(self):
        """Multiple SSH Keys can be added to Super admin user details page

        :id: 267cea76-0b75-4b37-a04f-dc3659cab409

        :steps:

                1. Go to Administer -> Users
                2. Edit Super Admin user details page
                3. Add multiple SSH Keys in SSH Keys tab
                4. Save the changes of Super Admin user

        :expectedresults: Super Admin should be saved with multiple SSH keys
        """

    @stubbed()
    @tier1
    def test_negative_create_ssh_key(self):
        """Invalid ssh key can not be added in User details page

        :id: a815cd8b-142e-4743-b95a-c922def193f6

        :steps:

            1. Go to Administer -> Users
            2. Attempt to create new user with all the details
            3. Attempt to add invalid string as SSH Key in SSH Keys tab
                before saving the user

        :expectedresults: Invalid SSH key should not be added in user details
            page
        """

    @stubbed()
    @tier1
    def test_negative_create_invalid_ssh_key(self):
        """"Invalid SSH key can not be added to user and corresponding error
        notification displays

        :id: ea613925-75a0-421c-b02b-e61ce2fe0d84

        :steps:

            1. Go to Administer -> Users
            2. Attempt to create new user with all the details
            3. Attempt to add invalid string as SSH Key in SSH Keys tab
                before saving the user. e.g blabla

        :expectedresults:

            1. SSH Key should not be added to user
            2. Satellite should show 'Fingerprint could not be generated'
                error notification
        """

    @stubbed()
    @tier1
    def test_negative_create_too_long_length_ssh_key(self):
        """SSH key with too long length can not be added to user and
        corresponding error notification displays

        :id: 2a3bb547-a073-4de6-85a7-20ace85992a2

        :steps:

            1. Go to Administer -> Users
            2. Attempt to create new user with all the details
            3. Attempt to add invalid length of SSH Key in SSH Keys tab
                before saving the user

        :expectedresults:

            1. SSH Key should not be added to user
            2. Satellite should show 'Length could not be calculated'
                error notification
        """

    @stubbed()
    @tier3
    def test_positive_ssh_key_to_pxe_discovered_host(self):
        """Satellite automatically adds SSH key of user to the provisioned host
        that is discovered with PXE

        :id: 86598125-6ca1-4147-920f-b5e2e9ad8ccd

        :steps:

            1. Create User with valid ssh-key
            2. Configure Satellite with DHCP, DNS and TFTP
            3. Enable foreman plugin discovery
            4. Install and enable discovery service plugin.
            5. Update PXELinux global default template with satellite
                capsule url and ONTIMEOUT to discovery
            6. Build the PXE default template from Hosts -> Provisioning
                templates
            7. Update Satellite Kickstart Default provisioning template,
                inherit 'create_users' snippet
            8. Create Host Group to provision the host
            9. Boot a blank bare metal host in a network
            10. Wait for successful Discovery Status on bare metal host
            11. In Hosts -> Discovered Hosts, find the above discovered
                host
            12. Choose to provision and choose name, taxonomies and
                Hostgroup
            13. Check IP, MAC fields and Primary, Managed, Provision
                options assigned automatically in Host -> Interface tab
            14. Check Host -> Operating System details populated
                automatically
            15. Resolve PXELinux details page- 'kickstart default PXELinux'
                and provision Template - 'Satellite Kickstart Default'
            16. Submit these changes for provisioning and wait for
                provisioning to complete.
            17. Attempt to ssh access the provisioned host from satellite
                server

        :expectedresults:

            1. User should be able to password-less access to provisioned
                host
            2. Satellite should automatically add SSH key to provisioned
                host
        """

    @stubbed()
    @tier3
    def test_positive_ssh_key_to_pxeless_provisioned_host(self):
        """Satellite automatically adds SSH key of user to the PXELess
        provisioned host

        :id: edbbafbd-5a82-4f27-ab93-2aa88d3a3353

        :steps:

            1. Create User with valid ssh-key
            2. Configure Satellite with DHCP and DNS
            3. Update Satellite Kickstart Default provisioning template,
                inherit 'create_users' snippet
            4. Create Host Group to provision the host
            5. Attempt to create a new host from Hosts -> New Host
            6. Choose name, taxonomies and Hostgroup
            7. Check IP, Primary, Managed, Provision
                options assigned automatically in Host -> Interface tab
            8. Enter the bare metal host mac in interface tab
            9. Check Host -> Operating System details populated
                automatically
            10. Resolve bootdisk template-'Boot disk iPXE - host',
                kexec template='Discovery Red Hat kexec' and
                provision Template - 'Satellite Kickstart Default'.
            11. Submit these changes
            12. After creating this host entry, Download the Generic boot disk
                from this host -> boot disk -> Generic Image
            13. Flash the Generic boot disk in some bootable device
            14. Boot the Provisionable host from above media device
            15. Wait for host to connect to Satellite, start installation,
                finish installation, post installation configurations
            16. Attempt to ssh access the provisioned host from satellite
                server

        :expectedresults:

            1. User should be able to password-less access to provisioned
                host
            2. Satellite should automatically add SSH key to provisioned host
        """

    @stubbed()
    @tier3
    def test_positive_ssh_key_to_pxeless_discovered_host(self):
        """Satellite automatically adds SSH key of user to the provisioned
         host that is discovered with PXELess

        :id: a3a7fcd8-9efd-4863-ac81-48c1a2cdb61b

        :steps:

            1. Create User with valid ssh-key
            2. Configure Satellite with DHCP, DNS and TFTP
            3. Update Satellite Kickstart Default provisioning template,
                inherit 'create_users' snippet
            4. Create Host Group to provision the host
            5. Enable foreman plugin discovery through satellite installer
            6. Install and enable discovery service plugin
            7. Flash the discovery ISO in some bootable device
            8. Boot the provisionable host from bootable device
            9. In host, Choose Discovery with DHCP
            10. Choose primary network interface that connects to the satelite
            11. Provide integrated capsule/external capsule server url
            12. Set connection type to Proxy
            13. Dont provide any custom facts
            14. Wait for satellite to discover the host in Hosts -> Discovered
                Hosts
            15. Choose to provision and choose name, taxonomies and Hostgroup
            16. Check IP, MAC fields and Primary, Managed, Provision
                options assigned automatically in Host -> Interface tab
            17. Check Host -> Operating System details populated
                automatically
            18. Resolve kexec Template- 'Discovery Red Hat kexec' and
                provision Template - 'Satellite Kickstart Default'.
            19. Submit these changes for provisioning and wait for
                provisioning to complete.
            20. Attempt to ssh access the provisioned host from satellite
                server

        :expectedresults:

            1. User should be able to password-less access to provisioned
                host
            2. Satellite should automatically add SSH key to provisioned host
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_ssh_key_in_network_based_provisioned_host(self):
        """Satellite automatically adds SSH key of user onto the host
        provisioned using network based method

        :id: ff2efc2a-02d0-4e2e-90d4-be2562fe384e

        :steps:

            1. Create User with valid ssh-key
            2. Configure Satellite with DHCP, DNS
            3. Create libvirt/RHEVM/VMWare Compute Resource on satellite
            4. Create suitable compute profile for choosed CR
            5. Update Satellite Kickstart Default provisioning template,
                inherit 'create_users' snippet
            6. Create Host Group for provisioning the host
            7. Attempt to create a new host from Hosts -> New Host
            8. Choose name, taxonomies and Hostgroup
            9. Select choosed(in step 2) CR in 'deploy on' option
            10. Check IP value amd Primary, Managed, Provision
                options assigned automatically in Host -> Interface tab
            11. Leave MAC Address blank to be assigned by CR
            12. Check Host -> Operating System details populated
                automatically, also choose Network Based provisioning
            13. Choose appropriate Virtual Machine details
            14. Submit these changes for provisioning and wait for provisioning
                to complete
            15. Attempt to ssh access the provisioned host from satellite
                server

        :expectedresults:

            1. User should be able to password-less access to provisioned
                host
            2. Satellite should automatically add SSH key to provisioned host
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_ssh_key_in_image_based_provisioned_host(self):
        """Satellite automatically adds SSH key of user onto the host
        provisioned using image based method

        :id: 470f7142-c805-43c3-b0cc-02bd380f098b

        :steps:

            1. Create User with valid ssh-key
            2. Configure Satellite with DHCP, DNS
            3. Create EC2/Openstack/VMware/libvirt/RHEV Compute Resource on
                satellite
            4. Create suitable compute profile for choosed CR
            5. Update Satellite Kickstart Default Finish provisioning template,
                inherit 'create_users' snippet
            6. Create Host Group for provisioning the host
            7. Attempt to create a new host from Hosts -> New Host
            8. Choose name, taxonomies and Hostgroup
            9. Select choosed(in step 2) CR in 'deploy on' option
            10. Check IP value amd Primary, Managed, Provision
                options assigned automatically in Host -> Interface tab
            11. Leave MAC Address blank to be assigned by CR
            12. Check Host -> Operating System details populated
                automatically, also choose Image Based provisioning
            13. Choose appropriate Virtual Machine details
            14. Submit these changes for provisioning and wait for provisioning
                to complete
            15. Attempt to ssh access the provisioned host from satellite
                server

        :expectedresults:

            1. User should be able to password-less access to provisioned
                host
            2. Satellite should automatically add SSH key to provisioned host
        """

    @stubbed()
    @tier3
    def test_negative_invalid_ssh_key_access_to_provisioned_host(self):
        """ Satellite user cannot password-less access with invalid ssh key

        :id: 13f2d109-d15e-4fee-ae49-7ce3b27efd17

        :steps:

            1. Create user with ssh public key which doesnt matches the private
                key of user(i.e Wrong public key)
            2. Update Satellite Kickstart Default template, inherit
                'create_users' snippet
            3. Provision a host on libvirt CR with above user
            4. Attempt to ssh access the provisioned host from satellite sever

        :expectedresults: User should not be able to password-less access to
            provisioned host having wrong non matching publc key
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_multiple_key_types_access_to_provisioned_host(self):
        """ Satellite automatically adds supported multiple type of SSH key of
        user onto the host provisioned

        :id: 1532df12-e0a5-4da6-9e28-5d2eba98f0af

        :steps:
            1. Create user with any type of ssh key, type includes
                rsa, dsa, ed25519, ecdsa
            2. Update Satellite Kickstart Default template, inherit
                'create_users' snippet
            3. Provision a host on libvirt CR with above user
            4. Attempt to ssh access the provisioned host from satellite sever

        :expectedresults:

            1. User should be able to password-less access to provisioned
                host using any supported type of ssh keys
            2. Satellite should automatically add any supported type of SSH key
                to provisioned host
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_delete_ssh_key(self):
        """Satellite Admin can delete ssh key from user

        :id: e4df559d-3f01-4dfb-a847-ae5f7d91ef90

        :steps:

            1. Go to Administer -> Users
            2. Attempt to create new user with all the details
            3. Add SSH Key in SSH Keys tab before saving the user
            4. Save the new User
            5. Edit the user created above and delete the ssh-key from user

        :expectedresults: SSH key should be deleted from user
        """
