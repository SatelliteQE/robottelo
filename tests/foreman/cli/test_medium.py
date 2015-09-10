# -*- encoding: utf-8 -*-
"""Test class for Medium  CLI"""

from ddt import ddt
from fauxfactory import gen_string, gen_alphanumeric
from robottelo.cli.factory import CLIFactoryError
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
        new_obj = make_medium(test_data)
        self.assertEqual(new_obj['name'], test_data['name'])

    def test_create_medium_with_location(self):
        """@Test: Check if medium with location can be created

        @Feature: Medium - Positive create

        @Assert: Medium is created and has new location assigned

        """
        try:
            location = make_location()
            medium = make_medium({
                'name': gen_string("alpha"),
                'location-ids': location['id']
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertIn(
            location['name'],
            medium['locations'],
            "Location wasn't assigned to medium"
        )

    def test_create_medium_with_organization(self):
        """@Test: Check if medium with organization can be created

        @Feature: Medium - Positive create

        @Assert: Medium is created and has new organization assigned

        """
        try:
            org = make_org()
            medium = make_medium({
                'name': gen_string("alpha"),
                'organization-ids': org['id']
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertIn(
            org['name'],
            medium['organizations'],
            "Organization wasn't assigned to medium"
        )

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
        new_obj = make_medium(test_data)

        return_value = Medium.delete({'id': new_obj['id']})
        self.assertEqual(return_value.return_code, 0, "Deletion failed")
        self.assertEqual(
            len(return_value.stderr), 0, "There should not be an error here")

        # Can we find the object?
        result = Medium.info({'id': new_obj['id']})
        self.assertNotEqual(
            result.return_code, 0, "Medium should be deleted")
        self.assertGreater(len(result.stderr), 0,
                           "There should be an exception here")
        self.assertEqual(
            len(result.stdout), 0, "Output should be blank.")

    def test_addoperatingsystem_medium(self):
        """@Test: Check if Medium can be associated with operating system

        @Feature: Medium - Add operating system

        @Assert: Operating system added

        """
        try:
            medium = make_medium({'name': gen_alphanumeric(6)})
            os = make_os()
        except CLIFactoryError as err:
            self.fail(err)

        args = {
            'id': medium['id'],
            'operatingsystem-id': os['id'],
        }

        result = Medium().add_operating_system(args)
        self.assertEqual(result.return_code, 0,
                         "Could not associate the operating system to media")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

    def test_removeoperatingsystem_medium(self):
        """@Test: Check if operating system can be removed from media

        @Feature: Medium - Remove operating system

        @Assert: Operating system removed

        """
        try:
            medium = make_medium({'name': gen_alphanumeric(6)})
            os = make_os()
        except CLIFactoryError as err:
            self.fail(err)

        args = {
            'id': medium['id'],
            'operatingsystem-id': os['id'],
        }

        result = Medium().add_operating_system(args)
        self.assertEqual(result.return_code, 0,
                         "Could not associate the operating system to media")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        result = Medium().info({'id': medium['id']})
        self.assertIn(os['title'],
                      result.stdout['operating-systems'],
                      "Operating system is not added to the media")

        result = Medium().remove_operating_system(args)
        self.assertEqual(result.return_code, 0,
                         "Removed the operating system from media")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        result = Medium().info({'id': medium['id']})
        self.assertNotIn(os['name'],
                         result.stdout['operating-systems'],
                         "Operating system is not removed from the media")

    def test_medium_update(self):
        """@Test: Check if medium can be updated

        @Feature: Medium - Update medium

        @Assert: Medium updated

        """
        new_name = gen_alphanumeric(6)
        try:
            medium = make_medium({'name': gen_alphanumeric(6)})
        except CLIFactoryError as e:
            self.fail(e)

        args = {
            'name': medium['name'],
            'new-name': new_name,
        }

        result = Medium().update(args)
        self.assertEqual(result.return_code, 0,
                         "Could not update media")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

        result = Medium().info({'id': medium['id']})
        self.assertEqual(result.stdout['name'], new_name,
                         "Medium name was not updated")
