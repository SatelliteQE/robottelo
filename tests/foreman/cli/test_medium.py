# -*- encoding: utf-8 -*-
"""Test class for Medium  CLI"""

from ddt import ddt
from fauxfactory import gen_string, gen_alphanumeric
from robottelo.cli.base import CLIReturnCodeError
from robottelo.test import CLITestCase
from robottelo.decorators import data, run_only_on
from robottelo.cli.factory import make_location, make_medium, make_org, make_os
from robottelo.cli.medium import Medium

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"
OSES = [
    'Archlinux',
    'Debian',
    'Gentoo',
    'Redhat',
    'Solaris',
    'Suse',
    'Windows',
]


@run_only_on('sat')
@ddt
class TestMedium(CLITestCase):

    @data({'name': gen_string("latin1")},
          {'name': gen_string("utf8")},
          {'name': gen_string("alpha")},
          {'name': gen_string("alphanumeric")},
          {'name': gen_string("numeric")},
          {'name': gen_string("html")})
    def test_positive_create_1(self, test_data):
        """@Test: Check if Medium can be created

        @Feature: Medium - Positive Create

        @Assert: Medium is created

        """
        medium = make_medium(test_data)
        self.assertEqual(medium['name'], test_data['name'])

    def test_create_medium_with_location(self):
        """@Test: Check if medium with location can be created

        @Feature: Medium - Positive create

        @Assert: Medium is created and has new location assigned

        """
        location = make_location()
        medium = make_medium({'location-ids': location['id']})
        self.assertIn(location['name'], medium['locations'])

    def test_create_medium_with_organization(self):
        """@Test: Check if medium with organization can be created

        @Feature: Medium - Positive create

        @Assert: Medium is created and has new organization assigned

        """
        org = make_org()
        medium = make_medium({'organization-ids': org['id']})
        self.assertIn(org['name'], medium['organizations'])

    @data({'name': gen_string("latin1")},
          {'name': gen_string("utf8")},
          {'name': gen_string("alpha")},
          {'name': gen_string("alphanumeric")},
          {'name': gen_string("numeric")},
          {'name': gen_string("html")})
    def test_positive_delete_1(self, test_data):
        """@Test: Check if Medium can be deleted

        @Feature: Medium - Positive Delete

        @Assert: Medium is deleted

        """
        medium = make_medium(test_data)
        Medium.delete({'id': medium['id']})
        with self.assertRaises(CLIReturnCodeError):
            Medium.info({'id': medium['id']})

    def test_add_operatingsystem_medium(self):
        """@Test: Check if Medium can be associated with operating system

        @Feature: Medium - Add operating system

        @Assert: Operating system added

        """
        medium = make_medium()
        os = make_os()
        Medium.add_operating_system({
            'id': medium['id'],
            'operatingsystem-id': os['id'],
        })

    def test_removeoperatingsystem_medium(self):
        """@Test: Check if operating system can be removed from media

        @Feature: Medium - Remove operating system

        @Assert: Operating system removed

        """
        medium = make_medium()
        os = make_os()
        Medium.add_operating_system({
            'id': medium['id'],
            'operatingsystem-id': os['id'],
        })
        medium = Medium.info({'id': medium['id']})
        self.assertIn(os['title'], medium['operating-systems'])
        Medium.remove_operating_system({
            'id': medium['id'],
            'operatingsystem-id': os['id'],
        })
        medium = Medium.info({'id': medium['id']})
        self.assertNotIn(os['name'], medium['operating-systems'])

    def test_medium_update(self):
        """@Test: Check if medium can be updated

        @Feature: Medium - Update medium

        @Assert: Medium updated

        """
        new_name = gen_alphanumeric(6)
        medium = make_medium()
        Medium.update({
            'name': medium['name'],
            'new-name': new_name,
        })
        medium = Medium.info({'id': medium['id']})
        self.assertEqual(medium['name'], new_name)
