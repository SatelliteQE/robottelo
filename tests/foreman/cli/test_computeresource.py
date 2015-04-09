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
from ddt import ddt
from fauxfactory import gen_string, gen_url
from robottelo.cli.computeresource import ComputeResource
from robottelo.common import conf
from robottelo.common.decorators import data, run_only_on
from robottelo.cli.factory import make_compute_resource
from robottelo.common.constants import FOREMAN_PROVIDERS
from robottelo.test import CLITestCase


@run_only_on('sat')
@ddt
class TestComputeResource(CLITestCase):
    """ComputeResource CLI tests."""

    def test_create(self):
        """@Test: Create Compute Resource

        @Feature: Compute Resource - Positive Create

        @Assert: Compute reource is created

        """
        name = gen_string(str_type='alpha')
        result = ComputeResource.create({
            'name': name,
            'provider': 'Libvirt',
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']
        })
        self.assertEquals(result.return_code, 0,
                          "ComputeResource create - exit code")

    def test_info(self):
        """@Test: Test Compute Resource Info

        @Feature: Compute Resource - Info

        @Assert: Compute resource Info is displayed

        """
        result_create = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']})
        self.assertTrue(result_create['name'],
                        "ComputeResource create - has name")
        result_info = ComputeResource.info({'name': result_create['name']})
        self.assertEquals(result_info.return_code, 0,
                          "ComputeResource info - exit code")
        self.assertEquals(result_info.stdout['name'], result_create['name'],
                          "ComputeResource info - check name")

    def test_list(self):
        """@Test: Test Compute Resource List

        @Feature: Compute Resource - List

        @Assert: Compute resource List is displayed

        """
        result_create = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']})
        self.assertTrue(result_create['name'],
                        "ComputeResource create - has name")
        result_list = ComputeResource.list({'search': "name=%s" %
                                            result_create['name']})
        self.assertEquals(result_list.return_code, 0,
                          "ComputeResource list - exit code")
        self.assertTrue(len(result_list.stdout) > 0,
                        "ComputeResource list - stdout has results")
        stdout = ComputeResource.exists(
            search=('name', result_create['name'])).stdout
        self.assertTrue(
            stdout,
            "ComputeResource list - exists name")

    def test_delete(self):
        """@Test: Test Compute Resource delete

        @Feature: Compute Resource - Delete

        @Assert: Compute resource deleted

        """
        result_create = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']})
        self.assertTrue(result_create['name'],
                        "ComputeResource create - has name")
        result_delete = ComputeResource.delete(
            {'name': result_create['name']})
        self.assertEquals(
            result_delete.return_code, 0,
            "ComputeResource delete - exit code")
        stdout = ComputeResource.exists(
            search=('name', result_create['name'])).stdout
        self.assertFalse(
            stdout,
            "ComputeResource list - does not exist name")

    # Positive create

    @data(
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
    def test_create_positive_libvirt(self, options):
        """@Test: Test Compute Resource create

        @Feature: Compute Resource positive create

        @Assert: Compute Resource created

        """
        result = ComputeResource.create({
            u'name': options['name'],
            u'url': gen_url(),
            u'provider': FOREMAN_PROVIDERS['libvirt'],
            u'description': options['description'],
        })

        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

    # Negative create

    @data(
        {u'name': gen_string('alphanumeric', 256)},
        {u'description': gen_string('alphanumeric', 256)},
        {u'name': 'white %s spaces' %
                  gen_string(str_type='alphanumeric')},
        {u'name': ''},
        {u'url': 'invalid url'},
        {u'url': ''},
    )
    def test_create_negative_1(self, options):
        """@Test: Compute Resource negative create with invalid values

        @Feature: Compute Resource create

        @Assert: Compute resource not created

        """
        result = ComputeResource.create({
            u'name': options.get(
                'name', gen_string(str_type='alphanumeric')
            ),
            u'url': options.get('url', gen_url()),
            u'provider': FOREMAN_PROVIDERS['libvirt'],
            u'description': options.get('description', '')
        })

        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_create_negative_2(self):
        """@Test: Compute Resource negative create with the same name

        @Feature: Compute Resource create

        @Assert: Compute resource not created

        """
        comp_res = make_compute_resource()

        result = ComputeResource.create({
            u'name': comp_res['name'],
            u'provider': FOREMAN_PROVIDERS['libvirt'],
            u'url': gen_url()
        })
        self.assertNotEquals(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    # Update Positive

    @data(
        {u'new-name': gen_string('utf8', 255)},
        {u'new-name': gen_string('alphanumeric')},
        {u'description': gen_string('utf8', 255)},
        {u'description': gen_string('alphanumeric')},
        {u'url': gen_url()},
        {u'url': 'qemu+tcp://localhost:16509/system'},
    )
    def test_update_positive(self, options):
        """@Test: Compute Resource positive update

        @Feature: Compute Resource update

        @Assert: Compute Resource successfully updated

        """
        comp_res = make_compute_resource()
        options.update({
            'name': comp_res['name'],
        })

        # update Compute Resource
        result = ComputeResource.update(options)
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # check updated values
        result = ComputeResource.info({'id': comp_res['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['description'],
            options.get('description', comp_res['description'])
        )
        self.assertEqual(
            result.stdout['name'],
            options.get('new-name', comp_res['name'])
        )
        self.assertEqual(
            result.stdout['url'],
            options.get('url', comp_res['url'])
        )
        self.assertEqual(
            result.stdout['provider'].lower(), comp_res['provider'].lower())

    # Update Negative

    @data(
        {u'new-name': gen_string('utf8', 256)},
        {u'new-name': 'white spaces %s' %
                      gen_string(str_type='alphanumeric')},
        {u'new-name': ''},
        {u'description': gen_string('utf8', 256)},
        {u'url': 'invalid url'},
        {u'url': ''},
    )
    def test_update_negative(self, options):
        """@Test: Compute Resource negative update

        @Feature: Compute Resource update

        @Assert: Compute Resource not updated

        """
        comp_res = make_compute_resource()

        result = ComputeResource.update(
            dict({'name': comp_res['name']}, **options))

        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

        result = ComputeResource.info({'id': comp_res['id']})
        self.assertEqual(result.return_code, 0)
        # check attributes have not changed
        self.assertEqual(result.stdout['name'], comp_res['name'])
        options.pop('new-name', None)
        for key in options.keys():
            self.assertEqual(comp_res[key], result.stdout[key])

    @data('true', 'false')
    def test_set_console_password_v1(self, set_console_password):
        """@Test: Create a compute resource with ``--set-console-password``.

        @Feature: Compute Resource

        @Assert: No error is returned.

        Targets BZ 1100344.

        """
        name = gen_string('utf8')
        result = ComputeResource.create({
            'name': name,
            'provider': 'Libvirt',
            'set-console-password': set_console_password,
            'url': gen_url(),
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

    @data('true', 'false')
    def test_set_console_password_v2(self, set_console_password):
        """@Test: Update a compute resource with ``--set-console-password``.

        @Feature: Compute Resource

        @Assert: No error is returned.

        Targets BZ 1100344.

        """
        name = gen_string('utf8')
        result = ComputeResource.create({
            'name': name,
            'provider': 'Libvirt',
            'url': gen_url(),
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ComputeResource.update({
            'name': name,
            'set-console-password': set_console_password,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
