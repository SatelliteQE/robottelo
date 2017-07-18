# -*- encoding: utf-8 -*-
"""Test class for UserGroup UI

:Requirement: Usergroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_names_list
from robottelo.decorators import tier1, tier2
from robottelo.test import UITestCase
from robottelo.ui.factory import make_usergroup
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session


class UserGroupTestCase(UITestCase):
    """Implements UserGroup tests from UI"""

    @classmethod
    def setUpClass(cls):
        super(UserGroupTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create new Usergroup using different names

        :id: 43e70c8d-455e-4da8-9c69-ab80dae2a0bc

        :expectedresults: Usergroup is created successfully

        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        # Create a new user
        entities.User(
            login=user_name,
            password=gen_string('alpha'),
            organization=[self.organization],
        ).create()
        with Session(self.browser) as session:
            for group_name in generate_strings_list():
                with self.subTest(group_name):
                    make_usergroup(
                        session,
                        name=group_name,
                        users=[user_name],
                        org=self.organization.name,
                    )
                    self.assertIsNotNone(self.usergroup.search(group_name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create a new UserGroup with invalid names

        :id: 2c67dcd6-89b7-4a04-8528-d1f1f2c4530d

        :expectedresults: Usergroup is not created

        :CaseImportance: Critical
        """
        with Session(self.browser) as session:
            for group_name in invalid_names_list():
                with self.subTest(group_name):
                    make_usergroup(
                        session, org=self.organization.name, name=group_name)
                    self.assertIsNotNone(self.usergroup.wait_until_element(
                        common_locators['name_haserror']))
                    self.assertIsNone(self.usergroup.search(group_name))

    @tier1
    def test_negative_create_with_same_name(self):
        """Create a new UserGroup with same name

        :id: 5dafa0d4-e2a2-4ac0-926d-fa57d56bbe0b

        :expectedresults: Usergroup cannot be created with existing name

        :CaseImportance: Critical
        """
        group_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.assertIsNotNone(self.usergroup.search(group_name))
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.assertIsNotNone(self.usergroup.wait_until_element(
                common_locators['name_haserror']))

    @tier1
    def test_positive_delete_empty(self):
        """Delete an empty Usergroup

        :id: ca82f84b-bc5a-4f7d-b70d-9ee3e1b0fffa

        :expectedresults: Usergroup is deleted

        :CaseImportance: Critical
        """
        with Session(self.browser) as session:
            for group_name in generate_strings_list():
                with self.subTest(group_name):
                    make_usergroup(
                        session, org=self.organization.name, name=group_name)
                    self.usergroup.delete(group_name)

    @tier2
    def test_positive_delete_with_user(self):
        """Delete an Usergroup that contains a user

        :id: 2bda3db5-f54f-412f-831f-8e005631f271

        :expectedresults: Usergroup is deleted but not the added user

        :CaseLevel: Integration
        """
        user_name = gen_string('alpha')
        group_name = gen_string('utf8')
        # Create a new user
        entities.User(
            login=user_name,
            password=gen_string('alpha'),
            organization=[self.organization],
        ).create()

        with Session(self.browser) as session:
            make_usergroup(
                session,
                name=group_name,
                users=[user_name],
                org=self.organization.name,
            )
            self.usergroup.delete(group_name)
            self.assertIsNotNone(self.user.search(user_name))

    @tier1
    def test_positive_update_name(self):
        """Update usergroup with new name

        :id: 2f49ab7c-2f11-48c0-99c2-448fc86b5ad2

        :expectedresults: Usergroup is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_usergroup(session, name=name)
            self.assertIsNotNone(self.usergroup.search(name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.usergroup.update(name, new_name)
                    self.assertIsNotNone(self.usergroup.search(new_name))
                    name = new_name  # for next iteration

    @tier1
    def test_positive_update_user(self):
        """Update usergroup with new user

        :id: 5fdb1c36-196d-4ba5-898d-40f484b81090

        :expectedresults: Usergroup is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        user_name = gen_string('alpha')
        # Create a new user
        entities.User(
            login=user_name,
            password=gen_string('alpha'),
            organization=[self.organization],
        ).create()
        with Session(self.browser) as session:
            make_usergroup(session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.usergroup.search(name))
            self.usergroup.update(name, users=[user_name])
            self.assertIsNotNone(self.usergroup.search(name))

    @tier1
    def test_positive_update_org_with_admin_perms(self):
        """Add non-admin user to a usergroup with administrative privileges and
        make sure user can update his organizations

        :id: 13d50901-d94a-4ede-a134-d7b5e84c9a2c

        :BZ: 1390833

        :expectedresults: user can update his assigned organizations
        """
        new_org = entities.Organization().create()
        password = gen_string('alpha')
        user = entities.User(
            admin=False,
            default_organization=self.organization,
            password=password,
            organization=[self.organization],
        ).create()
        group_name = gen_string('alpha')
        # Create a usergroup with admin permissions and associate the user
        with Session(self.browser) as session:
            make_usergroup(
                session, name=group_name, org=self.organization.name)
            self.assertIsNotNone(self.usergroup.search(group_name))
            self.usergroup.update(
                group_name, users=[user.login], roles=['admin'])
            self.assertIsNotNone(self.usergroup.search(group_name))
        # Login as the user and assign new organization
        with Session(self.browser, user=user.login, password=password):
            self.user.update(
                user.login,
                new_organizations=[new_org.name],
            )
            # Make sure both organizations are assigned
            self.user.click(self.user.search(user.login))
            self.user.click(tab_locators['users.tab_organizations'])
            for org in (self.organization.name, new_org.name):
                self.assertIsNotNone(
                    self.user.wait_until_element(
                        common_locators['entity_deselect'] % org)
                )
