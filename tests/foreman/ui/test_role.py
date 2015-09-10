# -*- encoding: utf-8 -*-
"""Test class for Roles UI"""

from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import bz_bug_is_open, data
from robottelo.test import UITestCase
from robottelo.ui.factory import make_role
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Role(UITestCase):
    """Implements Roles tests from UI"""

    @data(
        {'name': gen_string('alpha')},
        {'name': gen_string('numeric')},
        {'name': gen_string('alphanumeric')},
        {'name': gen_string('utf8'),
         u'bz-bug': 1112657},
        {'name': gen_string('latin1'),
         u'bz-bug': 1112657},
        {'name': gen_string('html'),
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

    @data('', ' ')
    def test_negative_create_role_1(self, name):
        """@Test: Create new role with blank and whitespace in name

        @Feature: Role - Negative Create

        @Assert: Role is not created

        """

        with Session(self.browser) as session:
            make_role(session, name=name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @data(
        {'name': gen_string('alpha', 256)},
        {'name': gen_string('numeric', 256)},
        {'name': gen_string('alphanumeric', 256)},
        {'name': gen_string('utf8', 256),
         u'bz-bug': 1112657},
        {'name': gen_string('latin1', 256),
         u'bz-bug': 1112657},
        {'name': gen_string('html', 256),
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
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @data(
        {'name': gen_string('alpha')},
        {'name': gen_string('numeric')},
        {'name': gen_string('alphanumeric')},
        {'name': gen_string('utf8'),
         u'bz-bug': 1112657},
        {'name': gen_string('latin1'),
         u'bz-bug': 1112657},
        {'name': gen_string('html'),
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
            self.role.remove(test_data['name'])
            self.assertIsNone(self.role.search(test_data['name']))

    @data(
        {'name': gen_string('alpha'),
         'new_name': gen_string('alpha')},
        {'name': gen_string('numeric'),
         'new_name': gen_string('numeric')},
        {'name': gen_string('alphanumeric'),
         'new_name': gen_string('alphanumeric')},
        {'name': gen_string('utf8'),
         'new_name': gen_string('utf8'),
         u'bz-bug': 1112657},
        {'name': gen_string('latin1'),
         'new_name': gen_string('latin1'),
         u'bz-bug': 1112657},
        {'name': gen_string('html'),
         'new_name': gen_string('html'),
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
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.update(
                name,
                add_permission=True,
                resource_type='Architecture',
                permission_list=['view_architectures', 'create_architectures'],
            )

    def test_update_role_org(self):
        """@Test: Update organization under selected role

        @Feature: Role - Positive Update

        @Assert: Role is updated

        """
        name = gen_string('alpha')
        org = entities.Organization().create()
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.update(
                name,
                add_permission=True,
                resource_type='Activation Keys',
                permission_list=['view_activation_keys'],
                organization=[org.name],
            )
