# -*- encoding: utf-8 -*-
"""Usage::

    hammer compute_resource [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a compute resource.
    info                          Show an compute resource.
    list                          List all compute resources.
    update                        Update a compute resource.
    delete                        Delete a compute resource.
    image                         View and manage compute resource's images

"""
import random

from fauxfactory import gen_string, gen_url
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.factory import make_location, make_compute_resource
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.test import CLITestCase

LIBVIRT_URL = 'qemu+tcp://{}:16509/system'.format(settings.server.hostname)


def valid_name_desc_data():
    """Random data for valid name and description"""
    return(
        {u'name': gen_string('numeric'),
         u'description': gen_string('numeric')},
        {u'name': gen_string('alphanumeric', 255),
         u'description': gen_string('alphanumeric')},
        {u'name': gen_string('alphanumeric'),
         u'description': gen_string('alphanumeric', 255)},
        {u'name': gen_string('utf8'),
         u'description': gen_string('utf8')},
        {u'name': u'<html>{0}</html>'.format(
            gen_string('alpha')),
         u'description': u'<html>{0}</html>'.format(
             gen_string('alpha'))},
        {u'name': u"{0}[]@#$%^&*(),./?\\\"{{}}><|''".format(
            gen_string('utf8')),
         u'description': u"{0}[]@#$%^&*(),./?\\\"{{}}><|''".format(
             gen_string('alpha'))},
    )


def invalid_create_data():
    """Random data for invalid name, description and url"""
    return(
        {u'name': gen_string('alphanumeric', 256)},
        {u'description': gen_string('alphanumeric', 256)},
        {u'name': 'white %s spaces' %
                  gen_string(str_type='alphanumeric')},
        {u'name': ''},
        {u'url': 'invalid url'},
        {u'url': ''},
    )


def valid_update_data():
    """Random data for valid update"""
    return(
        {u'new-name': gen_string('utf8', 255)},
        {u'new-name': gen_string('alphanumeric')},
        {u'description': gen_string('utf8', 255)},
        {u'description': gen_string('alphanumeric')},
        {u'url': gen_url()},
        {u'url': 'qemu+tcp://localhost:16509/system'},
    )


def invalid_update_data():
    """Random data for invalid update"""
    return(
        {u'new-name': gen_string('utf8', 256)},
        {u'new-name': 'white spaces %s' %
                      gen_string(str_type='alphanumeric')},
        {u'new-name': ''},
        {u'description': gen_string('utf8', 256)},
        {u'url': 'invalid url'},
        {u'url': ''},
    )


@run_only_on('sat')
class TestComputeResource(CLITestCase):
    """ComputeResource CLI tests."""

    def test_create(self):
        """@Test: Create Compute Resource

        @Feature: Compute Resource - Positive Create

        @Assert: Compute resource is created

        """
        ComputeResource.create({
            'name': gen_string(str_type='alpha'),
            'provider': 'Libvirt',
            'url': LIBVIRT_URL,
        })

    def test_info(self):
        """@Test: Test Compute Resource Info

        @Feature: Compute Resource - Info

        @Assert: Compute resource Info is displayed

        """
        name = gen_string('utf8')
        compute_resource = make_compute_resource({
            'name': name,
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': LIBVIRT_URL,
        })
        # factory already runs info, just check the data
        self.assertEquals(compute_resource['name'], name)

    def test_list(self):
        """@Test: Test Compute Resource List

        @Feature: Compute Resource - List

        @Assert: Compute resource List is displayed

        """
        comp_res = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': LIBVIRT_URL,
        })
        self.assertTrue(comp_res['name'])
        result_list = ComputeResource.list({
            'search': 'name=%s' % comp_res['name']})
        self.assertTrue(len(result_list) > 0)
        result = ComputeResource.exists(search=('name', comp_res['name']))
        self.assertTrue(result)

    def test_delete(self):
        """@Test: Test Compute Resource delete

        @Feature: Compute Resource - Delete

        @Assert: Compute resource deleted

        """
        comp_res = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': LIBVIRT_URL,
        })
        self.assertTrue(comp_res['name'])
        ComputeResource.delete({'name': comp_res['name']})
        result = ComputeResource.exists(search=('name', comp_res['name']))
        self.assertFalse(result)

    # Positive create

    def test_create_positive_libvirt(self):
        """@Test: Test Compute Resource create

        @Feature: Compute Resource positive create

        @Assert: Compute Resource created

        """
        for options in valid_name_desc_data():
            with self.subTest(options):
                ComputeResource.create({
                    u'description': options['description'],
                    u'name': options['name'],
                    u'provider': FOREMAN_PROVIDERS['libvirt'],
                    u'url': gen_url(),
                })

    def test_create_cr_with_location(self):
        """@Test: Create Compute Resource with location

        @Feature: Compute Resource - Location Create

        @Assert: Compute resource is created and has location assigned

        """
        location = make_location()
        comp_resource = make_compute_resource({'location-ids': location['id']})
        self.assertEqual(1, len(comp_resource['locations']))
        self.assertEqual(comp_resource['locations'][0], location['name'])

    def test_create_cr_with_locations(self):
        """@Test: Create Compute Resource with multiple locations

        @Feature: Compute Resource - Location Create

        @Assert: Compute resource is created and has multiple locations
        assigned

        """
        locations_amount = random.randint(3, 5)
        locations = [make_location() for _ in range(locations_amount)]
        comp_resource = make_compute_resource({
            'location-ids': [location['id'] for location in locations],
        })
        self.assertEqual(len(comp_resource['locations']), locations_amount)
        for location in locations:
            self.assertIn(location['name'], comp_resource['locations'])

    @skip_if_bug_open('bugzilla', 1214312)
    def test_create_cr_with_consolepwd(self):
        """@Test: Create Compute Resource with different values of
        set-console-password parameter

        @Feature: Compute Resource - Set Console Password

        @Assert: Compute Resource is created and set-console-password
        parameter is set

        @BZ: 1214312

        """
        for console_password in (u'True', u'Yes', 1, u'False', u'No', 0):
            with self.subTest(console_password):
                comp_resource = make_compute_resource({
                    u'provider': FOREMAN_PROVIDERS['libvirt'],
                    u'set-console-password': console_password,
                    u'url': gen_url(),
                })
                result = ComputeResource.info({'id': comp_resource['id']})
                if console_password in (u'True', u'Yes', 1):
                    self.assertEqual(result['set-console-password'], u'true')
                else:
                    self.assertEqual(result['set-console-password'], u'false')

    # Negative create

    def test_create_negative_1(self):
        """@Test: Compute Resource negative create with invalid values

        @Feature: Compute Resource create

        @Assert: Compute resource not created

        """
        for options in invalid_create_data():
            with self.subTest(options):
                with self.assertRaises(CLIReturnCodeError):
                    ComputeResource.create({
                        u'description': options.get('description', ''),
                        u'name': options.get(
                            'name', gen_string(str_type='alphanumeric')),
                        u'provider': FOREMAN_PROVIDERS['libvirt'],
                        u'url': options.get('url', gen_url()),
                    })

    def test_create_negative_2(self):
        """@Test: Compute Resource negative create with the same name

        @Feature: Compute Resource create

        @Assert: Compute resource not created

        """
        comp_res = make_compute_resource()
        with self.assertRaises(CLIReturnCodeError):
            ComputeResource.create({
                u'name': comp_res['name'],
                u'provider': FOREMAN_PROVIDERS['libvirt'],
                u'url': gen_url(),
            })

    # Update Positive

    def test_update_positive(self):
        """@Test: Compute Resource positive update

        @Feature: Compute Resource update

        @Assert: Compute Resource successfully updated

        """
        for options in valid_update_data():
            with self.subTest(options):
                comp_res = make_compute_resource()
                options.update({'name': comp_res['name']})
                # update Compute Resource
                ComputeResource.update(options)
                # check updated values
                result = ComputeResource.info({'id': comp_res['id']})
                self.assertEqual(
                    result['description'],
                    options.get('description', comp_res['description'])
                )
                self.assertEqual(
                    result['name'],
                    options.get('new-name', comp_res['name'])
                )
                self.assertEqual(
                    result['url'],
                    options.get('url', comp_res['url'])
                )
                self.assertEqual(
                    result['provider'].lower(),
                    comp_res['provider'].lower()
                )

    # Update Negative

    def test_update_negative(self):
        """@Test: Compute Resource negative update

        @Feature: Compute Resource update

        @Assert: Compute Resource not updated

        """
        for options in invalid_update_data():
            with self.subTest(options):
                comp_res = make_compute_resource()
                with self.assertRaises(CLIReturnCodeError):
                    ComputeResource.update(
                        dict({'name': comp_res['name']}, **options))
                result = ComputeResource.info({'id': comp_res['id']})
                # check attributes have not changed
                self.assertEqual(result['name'], comp_res['name'])
                options.pop('new-name', None)
                for key in options.keys():
                    self.assertEqual(comp_res[key], result[key])

    def test_set_console_password_v1(self):
        """@Test: Create a compute resource with ``--set-console-password``.

        @Feature: Compute Resource

        @Assert: No error is returned.

        Targets BZ 1100344.

        """
        for set_console_password in ('true', 'false'):
            with self.subTest(set_console_password):
                ComputeResource.create({
                    'name': gen_string('utf8'),
                    'provider': 'Libvirt',
                    'set-console-password': set_console_password,
                    'url': gen_url(),
                })

    def test_set_console_password_v2(self):
        """@Test: Update a compute resource with ``--set-console-password``.

        @Feature: Compute Resource

        @Assert: No error is returned.

        Targets BZ 1100344.

        """
        cr_name = gen_string('utf8')
        ComputeResource.create({
            'name': cr_name,
            'provider': 'Libvirt',
            'url': gen_url(),
        })
        for set_console_password in ('true', 'false'):
            with self.subTest(set_console_password):
                ComputeResource.update({
                    'name': cr_name,
                    'set-console-password': set_console_password,
                })
