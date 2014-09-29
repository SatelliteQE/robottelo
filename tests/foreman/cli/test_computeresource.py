# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
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
from fauxfactory import gen_string
from robottelo import orm
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

    @classmethod
    def setUpClass(cls):
        CLITestCase.setUpClass()
        cls.compute_res_updates = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']})['name']

    def test_create(self):
        """@Test: Create Compute Resource

        @Feature: Compute Resource - Positive Create

        @Assert: Compute reource is created

        """
        name = orm.StringField(str_type=('alpha',)).get_value()
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
            tuple_search=('name', result_create['name'])).stdout
        self.assertTrue(
            stdout,
            "ComputeResource list - exists name")

    @data(
        {'description': "updated: compute resource"},
        {'url': "qemu+tcp://localhost:16509/system"},
        {
            'provider': FOREMAN_PROVIDERS['ovirt'],
            'description': 'updated to Ovirt',
            'url': "https://localhost:443/api",
            'user': 'admin@internal',
            'password': "secret"
        }
    )
    def test_update(self, option_dict):
        """@Test: Test Compute Resource Update

        @Feature: Compute Resource - Update

        @Assert: Compute resource List is updated

        """
        options = {}
        options['name'] = self.compute_res_updates
        for option in option_dict:
            options[option] = option_dict[option]
        result_update = ComputeResource.update(options)
        self.assertEquals(result_update.return_code, 0,
                          "ComputeResource update - exit code")

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
            tuple_search=('name', result_create['name'])).stdout
        self.assertFalse(
            stdout,
            "ComputeResource list - does not exist name")

    # Positive create

    @data(
        {u'name': orm.StringField(str_type=('numeric',)).get_value(),
         u'description': orm.StringField(str_type=('numeric',)).get_value()},
        {u'name': gen_string('alphanumeric', 255),
         u'description': orm.StringField(
             str_type=('alphanumeric',)).get_value()},
        {u'name': orm.StringField(str_type=('alphanumeric',)).get_value(),
         u'description': gen_string('alphanumeric', 255)},
        {u'name': orm.StringField(str_type=('utf8',)).get_value(),
         u'description': orm.StringField(str_type=('utf8',)).get_value()},
        {u'name': '<html>%s</html>' %
                  orm.StringField(str_type=('alpha',)).get_value(),
         u'description': '<html>%s</html>' %
                         orm.StringField(str_type=('alpha',)).get_value()},
        {u'name': "%s[]@#$%%^&*(),./?\"{}><|''" %
                  orm.StringField(str_type=('utf8',)).get_value(),
         u'description': "%s[]@#$%%^&*(),./?\"{}><|''" %
                         orm.StringField(str_type=('alpha',)).get_value()},
    )
    def test_create_positive_libvirt(self, options):
        """@Test: Test Compute Resource create

        @Feature: Compute Resource positive create

        @Assert: Compute Resource created

        """
        result = ComputeResource.create({
            u'name': options['name'],
            u'url': orm.URLField().get_value(),
            u'provider': FOREMAN_PROVIDERS['libvirt'],
            u'description': options['description']
        })

        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

    # Negative create

    @data(
        {u'name': gen_string('alphanumeric', 256)},
        {u'description': gen_string('alphanumeric', 256)},
        {u'name': 'white %s spaces' %
                  orm.StringField(str_type=('alphanumeric',)).get_value()},
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
                'name', orm.StringField(str_type=('alphanumeric',)).get_value()
            ),
            u'url': options.get('url', orm.URLField().get_value()),
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
            u'url': orm.URLField().get_value()
        })
        self.assertNotEquals(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    # Update Positive

    @data(
        {u'new-name': gen_string('utf8', 255)},
        {u'new-name': orm.StringField(str_type=('alphanumeric',)).get_value()},
        {u'description': gen_string('utf8', 255)},
        {u'description': orm.StringField(
            str_type=('alphanumeric',)).get_value()},
        {u'url': orm.URLField().get_value()},
    )
    def test_update_positive(self, options):
        """@Test: Compute Resource positive update

        @Feature: Compute Resource update

        @Assert: Compute Resource successfully updated

        """
        comp_res = make_compute_resource()

        # update Compute Resource
        result = ComputeResource.update(
            dict({'name': comp_res['name']}, **options))
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        comp_res['name'] = options.get('new-name', comp_res['name'])
        comp_res.update(options)
        # check updated values
        result = ComputeResource.info({'id': comp_res['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['description'],
                         comp_res['description'])
        self.assertEqual(result.stdout['name'], comp_res['name'])
        self.assertEqual(result.stdout['provider'].lower(),
                         comp_res['provider'].lower())
        self.assertEqual(result.stdout['url'], comp_res['url'])

    # Update Negative

    @data(
        {u'new-name': gen_string('utf8', 256)},
        {u'new-name': 'white spaces %s' %
                      orm.StringField(str_type=('alphanumeric',)).get_value()},
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
