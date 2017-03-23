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


:Requirement: Computeresource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

from fauxfactory import gen_string, gen_url

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.factory import make_location, make_compute_resource
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, LIBVIRT_RESOURCE_URL
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
)
from robottelo.test import CLITestCase


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
    """Random data for invalid name and url"""
    return(
        {u'name': gen_string('alphanumeric', 256)},
        {u'name': ''},
        {u'url': 'invalid url'},
        {u'url': ''},
    )


def valid_update_data():
    """Random data for valid update"""
    return(
        {u'new-name': gen_string('utf8', 255)},
        {u'new-name': gen_string('alphanumeric')},
        {u'new-name': 'white spaces %s' %
                      gen_string(str_type='alphanumeric')},
        {u'description': gen_string('utf8', 255)},
        {u'description': gen_string('alphanumeric')},
        {u'url': gen_url()},
        {u'url': 'qemu+tcp://localhost:16509/system'},
    )


def invalid_update_data():
    """Random data for invalid update"""
    return(
        {u'new-name': gen_string('utf8', 256)},
        {u'new-name': ''},
        {u'url': 'invalid url'},
        {u'url': ''},
    )


class ComputeResourceTestCase(CLITestCase):
    """ComputeResource CLI tests."""

    @classmethod
    @skip_if_not_set('compute_resources')
    def setUpClass(cls):
        super(ComputeResourceTestCase, cls).setUpClass()
        cls.current_libvirt_url = (
            LIBVIRT_RESOURCE_URL % settings.compute_resources.libvirt_hostname
        )

    # pylint: disable=no-self-use
    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create Compute Resource

        :id: 6460bcc7-d7f7-406a-aecb-b3d54d51e697

        :Assert: Compute resource is created


        :CaseLevel: Critical
        """
        ComputeResource.create({
            'name': 'cr {0}'.format(gen_string(str_type='alpha')),
            'provider': 'Libvirt',
            'url': self.current_libvirt_url,
        })

    @tier1
    @run_only_on('sat')
    def test_positive_info(self):
        """Test Compute Resource Info

        :id: f54af041-4471-4d8e-9429-45d821df0440

        :Assert: Compute resource Info is displayed


        :CaseLevel: Critical
        """
        name = gen_string('utf8')
        compute_resource = make_compute_resource({
            'name': name,
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': self.current_libvirt_url,
        })
        # factory already runs info, just check the data
        self.assertEquals(compute_resource['name'], name)

    @tier1
    @run_only_on('sat')
    def test_positive_list(self):
        """Test Compute Resource List

        :id: 11123361-ffbc-4c59-a0df-a4af3408af7a

        :Assert: Compute resource List is displayed


        :CaseLevel: Critical
        """
        comp_res = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': self.current_libvirt_url,
        })
        self.assertTrue(comp_res['name'])
        result_list = ComputeResource.list({
            'search': 'name=%s' % comp_res['name']})
        self.assertTrue(len(result_list) > 0)
        result = ComputeResource.exists(search=('name', comp_res['name']))
        self.assertTrue(result)

    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_name(self):
        """Test Compute Resource delete

        :id: 7fcc0b66-f1c1-4194-8a4b-7f04b1dd439a

        :Assert: Compute resource deleted


        :CaseLevel: Critical
        """
        comp_res = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': self.current_libvirt_url,
        })
        self.assertTrue(comp_res['name'])
        ComputeResource.delete({'name': comp_res['name']})
        result = ComputeResource.exists(search=('name', comp_res['name']))
        self.assertFalse(result)

    # Positive create

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_libvirt(self):
        """Test Compute Resource create

        :id: adc6f4f8-6420-4044-89d1-c69e0bfeeab9

        :Assert: Compute Resource created


        :CaseLevel: Critical
        """
        for options in valid_name_desc_data():
            with self.subTest(options):
                ComputeResource.create({
                    u'description': options['description'],
                    u'name': options['name'],
                    u'provider': FOREMAN_PROVIDERS['libvirt'],
                    u'url': gen_url(),
                })

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_loc(self):
        """Create Compute Resource with location

        :id: 224c7cbc-6bac-4a94-8141-d6249896f5a2

        :Assert: Compute resource is created and has location assigned


        :CaseLevel: Critical
        """
        location = make_location()
        comp_resource = make_compute_resource({'location-ids': location['id']})
        self.assertEqual(1, len(comp_resource['locations']))
        self.assertEqual(comp_resource['locations'][0], location['name'])

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_locs(self):
        """Create Compute Resource with multiple locations

        :id: f665c586-39bf-480a-a0fc-81d9e1eb7c54

        :Assert: Compute resource is created and has multiple locations
            assigned

        :CaseLevel: Critical
        """
        locations_amount = random.randint(3, 5)
        locations = [make_location() for _ in range(locations_amount)]
        comp_resource = make_compute_resource({
            'location-ids': [location['id'] for location in locations],
        })
        self.assertEqual(len(comp_resource['locations']), locations_amount)
        for location in locations:
            self.assertIn(location['name'], comp_resource['locations'])

    @tier1
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1214312)
    def test_positive_create_with_console_password(self):
        """Create Compute Resource with different values of
        set-console-password parameter

        :id: 4531b3e3-906b-4835-a6ab-3332dc9bd636

        :Assert: Compute Resource is created and set-console-password parameter
            is set

        :BZ: 1214312


        :CaseLevel: Critical
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

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_name_url(self):
        """Compute Resource negative create with invalid values

        :id: cd432ff3-b3b9-49cd-9a16-ed00d81679dd

        :Assert: Compute resource not created

        :CaseLevel: Critical
        """
        for options in invalid_create_data():
            with self.subTest(options):
                with self.assertRaises(CLIReturnCodeError):
                    ComputeResource.create({
                        u'name': options.get(
                            'name', gen_string(str_type='alphanumeric')),
                        u'provider': FOREMAN_PROVIDERS['libvirt'],
                        u'url': options.get('url', gen_url()),
                    })

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_same_name(self):
        """Compute Resource negative create with the same name

        :id: ddb5c45b-1ea3-46d0-b248-56c0388d2e4b

        :Assert: Compute resource not created


        :CaseLevel: Critical
        """
        comp_res = make_compute_resource()
        with self.assertRaises(CLIReturnCodeError):
            ComputeResource.create({
                u'name': comp_res['name'],
                u'provider': FOREMAN_PROVIDERS['libvirt'],
                u'url': gen_url(),
            })

    # Update Positive

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Compute Resource positive update

        :id: 213d7f04-4c54-4985-8ca0-d2a1a9e3b305

        :Assert: Compute Resource successfully updated


        :CaseLevel: Critical
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

    @tier1
    @run_only_on('sat')
    def test_negative_update(self):
        """Compute Resource negative update

        :id: e7aa9b39-dd01-4f65-8e89-ff5a6f4ee0e3

        :Assert: Compute Resource not updated


        :CaseLevel: Critical
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

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_console_password_and_name(self):
        """Create a compute resource with ``--set-console-password``.

        :id: 5b4c838a-0265-4c71-a73d-305fecbe508a

        :Assert: No error is returned.

        Targets BZ 1100344.


        :CaseLevel: Critical
        """
        for set_console_password in ('true', 'false'):
            with self.subTest(set_console_password):
                ComputeResource.create({
                    'name': gen_string('utf8'),
                    'provider': 'Libvirt',
                    'set-console-password': set_console_password,
                    'url': gen_url(),
                })

    @tier1
    @run_only_on('sat')
    def test_positive_update_console_password(self):
        """Update a compute resource with ``--set-console-password``.

        :id: ef09351e-dcd3-4b4f-8d3b-995e9e5873b3

        :Assert: No error is returned.

        Targets BZ 1100344.


        :CaseLevel: Critical
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
