# -*- encoding: utf-8 -*-
"""Test class for Users UI

@Requirement: User

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

import random
from fauxfactory import gen_string
from nailgun import entities
from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ORG,
    LANGUAGES,
    LDAP_ATTR,
    LDAP_SERVER_TYPE,
    ROLES,
    TIMEZONES,
)
from robottelo.datafactory import (
    datacheck,
    invalid_emails_list,
    invalid_names_list,
    invalid_values_list,
    valid_emails_list,
)
from robottelo.decorators import (
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_user, set_context
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@datacheck
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

        @id: 2acc8c7d-cb14-4eda-98f9-fb379950f2f5

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

        @id: dd398cd6-821e-4b0e-a111-22d5a6eeafd8

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

        @id: 0a2dc093-0cd1-41eb-99cd-79935c74563f

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

        @id: 1c6c0f50-401c-4b7d-9795-97a1be3806f8

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

        @id: 1c5581a8-79ae-40a6-8052-f47be2d4c5eb

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

        @id: 83d6efe0-7526-465c-9c97-5673c7736fc4

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

        @id: 9bf56045-1026-435c-bf4c-623e160582d5

        @Assert: Admin User is created successfully
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=user_name, admin=True)
            self.assertIsNotNone(self.user.search(user_name))

    @tier1
    def test_positive_create_with_one_role(self):
        """Create User with one role

        @id: 6d6c795e-8b46-4f0f-84e1-f7e22add6173

        @Assert: User is created successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role = entities.Role().create()
        with Session(self.browser) as session:
            make_user(session, username=name, roles=[role.name], edit=True)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_roles'])
            element = self.user.wait_until_element(
                (strategy, value % role.name))
            self.assertIsNotNone(element)

    @tier2
    def test_positive_create_with_multiple_roles(self):
        """Create User with multiple roles

        @id: d3cc4434-25ca-4465-8878-42495390c17b

        @Assert: User is created successfully

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role1 = gen_string('alpha')
        role2 = gen_string('alpha')
        for role in [role1, role2]:
            entities.Role(name=role).create()
        with Session(self.browser) as session:
            make_user(session, username=name, roles=[role1, role2], edit=True)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_roles'])
            for role in [role1, role2]:
                element = self.user.wait_until_element(
                    (strategy, value % role))
                self.assertIsNotNone(element)

    @tier2
    def test_positive_create_with_all_roles(self):
        """Create User and assign all available roles to it

        @id: 814593ca-1566-45ea-9eff-e880183b1ee3

        @Assert: User is created successfully

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name, roles=ROLES, edit=True)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_roles'])
            for role in ROLES:
                self.assertIsNotNone(self.user.wait_until_element(
                    (strategy, value % role)))

    @tier1
    def test_positive_create_with_one_org(self):
        """Create User associated to one Org

        @id: 830bc5fc-e773-466c-9b38-4f33a2c1d05e

        @Assert: User is created successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            make_user(
                session, username=name, organizations=[org_name], edit=True)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_organizations'])
            element = self.user.wait_until_element(
                (strategy, value % org_name))
            self.assertIsNotNone(element)

    @tier2
    def test_positive_create_with_multiple_orgs(self):
        """Create User associated to multiple Orgs

        @id: d74c0284-3995-4a4a-8746-00858282bf5d

        @Assert: User is created successfully

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_name1 = gen_string('alpha')
        org_name2 = gen_string('alpha')
        for org_name in [org_name1, org_name2]:
            entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            set_context(session, org=DEFAULT_ORG)
            make_user(
                session,
                username=name,
                organizations=[org_name1, org_name2],
                edit=True,
            )
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_organizations'])
            for org_name in [org_name1, org_name2, DEFAULT_ORG]:
                element = self.user.wait_until_element(
                    (strategy, value % org_name))
                self.assertIsNotNone(element)

    @tier1
    def test_positive_create_with_default_org(self):
        """Create User and has default organization associated with it

        @id: 3d51dead-9053-427d-8292-c42e87ed6289

        @Assert: User is created with default Org selected.
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            make_user(session, username=name, organizations=[org_name],
                      edit=True, default_org=org_name)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_organizations'])
            element = session.nav.wait_until_element(
                (strategy, value % org_name))
            self.assertIsNotNone(element)
            # Check that default organization value was really chosen
            self.assertEqual(org_name, session.nav.find_element(
                locators['users.default_org_value']).text)

    @tier1
    def test_positive_create_with_default_location(self):
        """Create User and associate a default Location.

        @id: 952a0be5-d393-49a2-8fd9-f6dfcc31f762

        @Assert: User is created with default Location selected.
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        loc_name = gen_string('alpha')
        entities.Location(name=loc_name).create()
        with Session(self.browser) as session:
            make_user(session, username=name, locations=[loc_name],
                      edit=True, default_loc=loc_name)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_locations'])
            element = session.nav.wait_until_element(
                (strategy, value % loc_name))
            self.assertIsNotNone(element)
            # Check that default location value was really chosen
            self.assertEqual(loc_name, session.nav.find_element(
                locators['users.default_loc_value']).text)

    @tier1
    def test_negative_create(self):
        """Enter all User creation details and Cancel

        @id: 2774be2f-303e-498f-8072-80462f33c52e

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

        @id: 31bbe350-0275-4aaf-99ec-3f77bfd4ba00

        @Assert: User is not created. Appropriate error shown.
        """
        with Session(self.browser) as session:
            for user_name in invalid_values_list(interface='ui'):
                with self.subTest(user_name):
                    make_user(session, username=user_name)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_create_with_invalid_firstname(self):
        """Create User with invalid FirstName

        @id: 21525bf2-4de9-43f0-8c92-b2fad1fdc944

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
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_create_with_invalid_surname(self):
        """Create User with invalid Surname

        @id: 47d9e8be-3b29-4a56-85d7-898145b5b034

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
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_create_with_invalid_emails(self):
        """Create User with invalid Email Address

        @id: 36511b82-e070-41ea-81fa-6e29faa9da1c

        @Assert: User is not created. Appropriate error shown.
        """
        with Session(self.browser) as session:
            for email in invalid_emails_list():
                with self.subTest(email):
                    name = gen_string('alpha')
                    make_user(session, username=name, email=email)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_create_with_blank_auth(self):
        """Create User with blank value for 'Authorized by' field

        @id: 68f670ed-ac6e-4052-889c-6671d659e510

        @Assert: User is not created. Appropriate error shown.
        """
        with Session(self.browser) as session:
            make_user(session, username=gen_string('alpha'), authorized_by='')
            self.assertIsNotNone(
                self.user.wait_until_element(common_locators['haserror']))

    @tier1
    def test_negative_create_with_wrong_pass_confirmation(self):
        """Create User with non-matching values in Password and verify

        @id: f818e5fc-b378-4bc7-afa8-18b23ee05053

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

        @id: 4ecb2816-9bef-4089-86a0-02d7d065cdb1

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

        @id: 03ef8a7f-2bf1-4314-b0cd-a7a6acfc17ea

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

        @id: 0326d221-28b0-4a6b-934e-b67ee6c9f696

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

        @id: e48314b7-2a49-48ec-896d-af7bf427b1c4

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

        @id: 64b6a90e-0d4c-4a55-a4bd-7347010e39f2

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

        @id: db57c3bc-4fae-4ee7-bf6d-8e0bcc7fd55c

        @Assert: User password is updated successfully

        """
        user_name = gen_string('alpha')
        new_password = gen_string('alpha')
        with Session(self.browser) as session:
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

        @id: b41cbcf8-d819-4daa-b217-a4812541dca3

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

        @id: d3cdda62-1384-4b49-97a3-0c66764583bb

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

        @id: 2a13529c-3863-403b-a319-9569ca1287cb

        @Assert: User role is updated
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        role_name = entities.Role().create().name
        with Session(self.browser) as session:
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

    @tier2
    def test_positive_update_with_multiple_roles(self):
        """Update User with multiple roles

        @id: 127fb368-09fd-4f10-8319-566a1bcb5cd2

        @Assert: User is updated successfully

        @CaseLevel: Integration
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
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_roles'])
            for role in role_names:
                self.assertIsNotNone(
                    self.user.wait_until_element((strategy, value % role)))

    @tier2
    def test_positive_update_with_all_roles(self):
        """Update User with all roles

        @id: cd7a9cfb-a700-45f2-a11d-bba6be3c810d

        @Assert: User is updated successfully

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            self.user.update(name, new_roles=ROLES)
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_roles'])
            for role in ROLES:
                self.assertIsNotNone(
                    self.user.wait_until_element((strategy, value % role)))

    @tier1
    def test_positive_update_org(self):
        """Assign a User to an Org

        @id: d891e54b-76bf-4537-8eb9-c3f8832e4c2c

        @Assert: User is updated successfully
        """
        strategy, value = common_locators['entity_deselect']
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            make_user(session, username=name)
            self.user.update(name, new_organizations=[org_name])
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_organizations'])
            element = self.user.wait_until_element(
                (strategy, value % org_name))
            self.assertIsNotNone(element)

    @tier2
    def test_positive_update_orgs(self):
        """Assign a User to multiple Orgs

        @id: a207188d-1ad1-4ff1-9906-bae1d91104fd

        @Assert: User is updated

        @CaseLevel: Integration
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
            self.user.click(self.user.search(name))
            self.user.click(tab_locators['users.tab_organizations'])
            for org in org_names:
                self.assertIsNotNone(
                    self.user.wait_until_element((strategy, value % org)))

    @tier1
    def test_negative_update_username(self):
        """Update invalid Username in an User

        @id: 7019461e-13c6-4761-b3e9-4df81abcd0f9

        @Assert: User is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            for new_user_name in invalid_names_list():
                with self.subTest(new_user_name):
                    self.user.update(name, new_username=new_user_name)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_update_firstname(self):
        """Update invalid Firstname in an User

        @id: 1e3945d1-5b47-45ca-aff9-3ddd44688e6b

        @Assert: User is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            for new_first_name in invalid_names_list():
                with self.subTest(new_first_name):
                    self.user.update(name, first_name=new_first_name)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_update_surname(self):
        """Update invalid Surname in an User

        @id: 14033c1f-4c7e-4ee5-8ffc-76c4dd672cc1

        @Assert: User is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            for new_surname in invalid_names_list():
                with self.subTest(new_surname):
                    self.user.update(name, last_name=new_surname)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_update_email(self):
        """Update invalid Email Address in an User

        @id: 6aec3816-16ca-487a-b0f1-a5c1fbc3e0a3

        @Assert: User is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=name)
            for new_email in invalid_emails_list():
                with self.subTest(new_email):
                    self.user.update(name, email=new_email)
                    self.assertIsNotNone(self.user.wait_until_element(
                        common_locators['haserror']))

    @tier1
    def test_negative_update_password(self):
        """Update different values in Password and verify fields

        @id: ab4a5dbf-70c2-4adc-b948-bc350329e166

        @Steps:
        1. Create User
        2. Update the password by entering different values in Password and
        verify fields

        @Assert: User is not updated.  Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
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

        @id: c2b569c9-8120-4125-8bfe-61324a881395

        @Steps:
        1. Create User
        2. Update the password by entering value only in Password field

        @Assert: User is not updated.  Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
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

        @id: 56c8ea13-4add-4a51-8428-9d9f9ddde33e

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

        @id: 49534eda-f8ea-404e-9714-a8d0d2210979

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

        @id: afda171a-b464-461f-93ce-96d770935200

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

        @id: 43aed0c0-a3c3-4044-addc-910dc29e4f37

        @Assert: User is not deleted
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(session, username=user_name)
            self.assertIsNotNone(self.user.search(user_name))
            self.user.delete(user_name, really=False)

    @stubbed()
    @tier3
    def test_positive_end_to_end(self):
        """Create User and perform different operations

        @id: 57f7054e-2865-4ab8-bc2b-e300a8dacee5

        @Steps:
        1. Create User
        2. Login with the new user
        3. Upload Subscriptions
        4. Provision Systems
        5. Add/Remove Users
        6. Add/Remove Orgs
        7. Delete the User

        @Assert: All actions passed

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_end_to_end_without_org(self):
        """Create User with no Org assigned and attempt different
        operations

        @id: 36b6d667-59cc-4442-aa40-c029bdb2b534

        @Steps:
        1. Create User.  Do not assign any Org
        2. Login with the new user
        3. Attempt to Upload Subscriptions
        4. Attempt to Provision Systems
        5. Attempt to Add/Remove Users
        6. Attempt to Add/Remove Orgs

        @Assert: All actions failed since the User is not assigned to any Org

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @tier1
    def test_positive_set_timezone(self):
        """Set a new timezone for the user

        @id: 3219c245-2914-4412-8df1-72e041a58a9f

        @Steps:

        1.Navigate to Administer -> Users
        2.Click on the User
        3.Select the Timezone Dropdown list
        4.Try to apply some timezone

        @Assert: User should be able to change timezone
        """
        with Session(self.browser) as session:
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

        @id: c2d80855-631c-46f6-8950-c296df8c0cbe

        @Steps:

        1.Change the timezone for a user in Administer -> Users tab
        2.Navigate to Monitor -> Dashboard
        3.The left corner displays time according to the new timezone set

        @Assert: Dashboard UI displays new time based on the new timezone

        @caseautomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_logfiles_shows_new_time(self):
        """Check if the logfiles reflect the new timezone set by
        the user

        @id: b687182b-9d4f-4ff4-9f19-1b6ae3c126ad

        @Steps:

        1.Change the timezones for user in Administer -> Users Tab
        2.Try to modify content view or environment
        so that the changes are reflected in log file
        3.Check if log file shows the new timezone set

        @Assert: Logfiles display time according to changed timezone

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_mails_for_new_timezone(self):
        """Check if the mails are received according to new
        timezone set by the user

        @id: ab34dd9d-4fc1-43f1-b40a-b0ebf0802887

        @Steps:

        1.Change the timezones for user in Administer -> Users tab
        2.Navigate to Administer -> Users tab
        3.Make sure under Email Preferences -> Mail Enabled
        4.Send daily/weekly/monthly mails

        @Assert: Emails are sent according to new timezone set

        @caseautomation: notautomated

        @CaseLevel: Integration
        """


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

    @tier2
    def test_positive_create_in_ldap_mode(self):
        """Create User in ldap mode

        @id: 0668b2ca-831e-4568-94fb-80e45dd7d001

        @Assert: User is created without specifying the password

        @CaseLevel: Integration
        """
        user_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_user(
                session,
                username=user_name,
                authorized_by='LDAP-' + self.ldap_server_name,
                password1='',
                password2='',
            )
            self.assertIsNotNone(self.user.search(user_name))
