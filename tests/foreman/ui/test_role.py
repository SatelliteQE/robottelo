# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Roles UI"""

from ddt import ddt
from fauxfactory import FauxFactory
from robottelo.common.decorators import data, bz_bug_is_open
from robottelo import entities
from robottelo.test import UITestCase
from robottelo.ui.factory import make_role
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Role(UITestCase):
    """Implements Roles tests from UI"""

    @data(
        {'name': FauxFactory.generate_string("alpha", 10)},
        {'name': FauxFactory.generate_string("numeric", 10)},
        {'name': FauxFactory.generate_string("alphanumeric", 255)},
        {'name': FauxFactory.generate_string("utf8", 10),
         u'bz-bug': 1112657},
        {'name': FauxFactory.generate_string("latin1", 10),
         u'bz-bug': 1112657},
        {'name': FauxFactory.generate_string("html", 10),
         u'bz-bug': 1112657}
    )
    def test_create_role(self, test_data):
        """@Test: Create new role

        @Feature: Role - Positive Create

        @Assert: Role is created

        """
        bug_id = test_data.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        with Session(self.browser) as session:
            make_role(session, name=test_data['name'])
            self.assertIsNotNone(self.role.search(test_data['name']))

    @data("", " ")
    def test_negative_create_role_1(self, name):
        """@Test: Create new role with blank and whitespace in name

        @Feature: Role - Negative Create

        @Assert: Role is not created

        """

        with Session(self.browser) as session:
            make_role(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @data(
        {'name': FauxFactory.generate_string("alpha", 10)},
        {'name': FauxFactory.generate_string("numeric", 10)},
        {'name': FauxFactory.generate_string("alphanumeric", 255)},
        {'name': FauxFactory.generate_string("utf8", 10),
         u'bz-bug': 1112657},
        {'name': FauxFactory.generate_string("latin1", 10),
         u'bz-bug': 1112657},
        {'name': FauxFactory.generate_string("html", 10),
         u'bz-bug': 1112657}
    )
    def test_negative_create_role_2(self, test_data):
        """@Test: Create new role with 256 characters in name

        @Feature: Role - Negative Create

        @Assert: Role is not created

        """
        bug_id = test_data.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        with Session(self.browser) as session:
            make_role(session, name=test_data['name'])
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)
            self.assertIsNone(self.role.search(test_data['name']))

    @data(
        {'name': FauxFactory.generate_string("alpha", 10)},
        {'name': FauxFactory.generate_string("numeric", 10)},
        {'name': FauxFactory.generate_string("alphanumeric", 255)},
        {'name': FauxFactory.generate_string("utf8", 10),
         u'bz-bug': 1112657},
        {'name': FauxFactory.generate_string("latin1", 10),
         u'bz-bug': 1112657},
        {'name': FauxFactory.generate_string("html", 10),
         u'bz-bug': 1112657}
    )
    def test_remove_role(self, test_data):
        """@Test: Delete an existing role

        @Feature: Role - Positive Delete

        @Assert: Role is deleted

        """
        bug_id = test_data.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        with Session(self.browser) as session:
            make_role(session, name=test_data['name'])
            self.assertIsNotNone(self.role.search(test_data['name']))
            self.role.remove(test_data['name'], True)
            self.assertIsNotNone(self.role.wait_until_element(
                common_locators["notif.success"]))
            self.assertIsNone(self.role.search(test_data['name']))

    @data(
        {'name': FauxFactory.generate_string('alpha', 10),
         'new_name': FauxFactory.generate_string('alpha', 10)},
        {'name': FauxFactory.generate_string('numeric', 10),
         'new_name': FauxFactory.generate_string('numeric', 10)},
        {'name': FauxFactory.generate_string('alphanumeric', 10),
         'new_name': FauxFactory.generate_string('alphanumeric', 10)},
        {'name': FauxFactory.generate_string('utf8', 10),
         'new_name': FauxFactory.generate_string('utf8', 10),
         u'bz-bug': 1112657},
        {'name': FauxFactory.generate_string('latin1', 10),
         'new_name': FauxFactory.generate_string('latin1', 10),
         u'bz-bug': 1112657},
        {'name': FauxFactory.generate_string('html', 10),
         'new_name': FauxFactory.generate_string('html', 10),
         u'bz-bug': 1112657},
    )
    def test_update_role_name(self, test_data):
        """@Test: Update role name

        @Feature: Role - Positive Update

        @Assert: Role is updated

        """
        bug_id = test_data.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        with Session(self.browser) as session:
            make_role(session, name=test_data['name'])
            self.assertIsNotNone(self.role.search(test_data['name']))
            self.role.update(test_data['name'], test_data['new_name'])
            self.assertIsNotNone(self.role.search(test_data['new_name']))

    def test_update_role_permission(self):
        """@Test: Update role permissions

        @Feature: Role - Positive Update

        @Assert: Role is updated

        """
        name = FauxFactory.generate_string("alpha", 8)
        resource_type = 'Architecture'
        permission_list = ['view_architectures', 'create_architectures']
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.update(name, add_permission=True,
                             resource_type=resource_type,
                             permission_list=permission_list)

    def test_update_role_org(self):
        """@Test: Update organization under selected role

        @Feature: Role - Positive Update

        @Assert: Role is updated

        """
        name = FauxFactory.generate_string("alpha", 8)
        resource_type = 'Activation Keys'
        permission_list = ['view_activation_keys']
        org_name = entities.Organization().create()['name']
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.update(name, add_permission=True,
                             resource_type=resource_type,
                             permission_list=permission_list,
                             organization=[org_name])
