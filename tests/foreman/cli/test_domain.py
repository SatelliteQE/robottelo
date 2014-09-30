# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Domain  CLI"""

from fauxfactory import gen_string
from robottelo.cli.domain import Domain
from robottelo.cli.factory import make_domain, CLIFactoryError
from robottelo.common.decorators import data, run_only_on
from robottelo.test import MetaCLITestCase


@run_only_on('sat')
class TestDomain(MetaCLITestCase):
    """Domain CLI tests"""

    factory = make_domain
    factory_obj = Domain

    @data(
        {u'name': 'white spaces {0}'.format(gen_string(str_type='utf8')),
         u'description': gen_string(str_type='alpha')},
        {u'name': gen_string(str_type='utf8'),
         u'description': gen_string(str_type='utf8')},
        {u'name': gen_string(str_type='numeric'),
         u'description': gen_string(str_type='numeric')},
        {u'name': gen_string(str_type='utf8', length=255),
         u'description': gen_string(str_type='utf8', length=255)},
    )
    def test_positive_create(self, options):
        """@Test: Create domain with valid name and description

        @Feature: Domain positive create

        @Assert: Domain successfully created

        """
        try:
            make_domain(options)
        except CLIFactoryError as err:
            self.fail(err)

    @data(
        {u'description': gen_string(str_type='utf8', length=256)},
        {u'dns-id': '-1'},
        {u'name': gen_string(str_type='utf8', length=256)},
    )
    def test_negative_create(self, options):
        """@Test: Create domain with invalid values

        @Feature: Domain negative create

        @Assert: Domain is not created

        """
        with self.assertRaises(CLIFactoryError):
            make_domain(options)

    @data(
        {u'name': 'white spaces {0}'.format(gen_string(str_type='utf8')),
         u'description': gen_string(str_type='alpha')},
        {u'name': gen_string(str_type='utf8'),
         u'description': gen_string(str_type='utf8')},
        {u'name': gen_string(str_type='numeric'),
         u'description': gen_string(str_type='numeric')},
        {u'name': gen_string(str_type='utf8', length=255),
         u'description': gen_string(str_type='utf8', length=255)},
    )
    def test_positive_update(self, options):
        """@Test: Update domain with valid values

        @Feature: Domain positive update

        @Assert: Domain is updated

        """
        try:
            domain = make_domain({
                u'description': gen_string(str_type='utf8')
            })
        except CLIFactoryError as err:
            self.fail(err)

        # update description
        result = Domain.update(dict(options, id=domain['id']))
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # check - domain updated
        result = Domain.info({'id': domain['id']})
        self.assertEqual(result.return_code, 0)
        for key, val in options.iteritems():
            self.assertEqual(result.stdout[key], val)

    @data(
        {u'name': ''},
        {u'name': gen_string(str_type='utf8', length=256)},
        {u'description': gen_string(str_type='utf8', length=256)},
        {u'dns-id': '-1'},
    )
    def test_negative_update(self, options):
        """@Test: Update domain with invalid values

        @Feature: Domain negative update

        @Assert: Domain is not updated

        """
        try:
            domain = make_domain()
        except CLIFactoryError as err:
            self.fail(err)

        # update description
        result = Domain.update(dict(options, id=domain['id']))
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

        # check - domain not updated
        result = Domain.info({'id': domain['id']})
        self.assertEqual(result.return_code, 0)
        for key in options.keys():
            self.assertEqual(result.stdout[key], domain[key])

    @data(
        {'name': gen_string(str_type='utf8'),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=255),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8'),
         'value': gen_string(str_type='utf8', length=255)},
        {'name': gen_string(str_type='utf8'),
         'value': ''},
    )
    def test_positive_set_parameter(self, options):
        """@Test: Domain set-parameter with valid key and value

        @Feature: Domain positive set-parameter

        @Assert: Domain parameter is set

        """
        try:
            domain = make_domain()
        except CLIFactoryError as err:
            self.fail(err)

        options['domain-id'] = domain['id']
        # set parameter
        result = Domain.set_parameter(options)
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # check - parameter set
        result = Domain.info({'id': domain['id']})
        self.assertEqual(result.return_code, 0)

        parameter = {
            # Sattelite applies lower to parameter's name
            options['name'].lower(): options['value'],
        }
        self.assertDictEqual(parameter, result.stdout['parameters'])

    @data(
        {'name': 'white spaces {0}'.format(gen_string(str_type='utf8')),
         'value': gen_string(str_type='utf8')},
        {'name': '',
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=256),
         'value': gen_string(str_type='utf8')},
    )
    def test_negative_set_parameter(self, options):
        """@Test: Domain set-parameter with invalid values

        @Feature: Domain negative set-parameter

        @Assert: Domain parameter is not set

        """
        try:
            domain = make_domain()
        except CLIFactoryError as err:
            self.fail(err)
        options['domain-id'] = domain['id']
        # set parameter
        result = Domain.set_parameter(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

        # check - parameter not set
        result = Domain.info({'id': domain['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['parameters']), 0)

    @data(
        {'name': gen_string(str_type='utf8'),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=255),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8'),
         'value': ''},
    )
    def test_positive_delete_parameter(self, options):
        """@Test: Domain delete-parameter removes parameter

        @Feature: Domain positive delete-parameter

        @Assert: Domain parameter is removed

        """
        try:
            domain = make_domain()
        except CLIFactoryError as err:
            self.fail(err)

        options['domain'] = domain['name']
        result = Domain.set_parameter(options)
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Domain.delete_parameter({
            u'name': options['name'],
            u'domain-id': domain['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # check - parameter not set
        result = Domain.info({'name': domain['name']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['parameters']), 0)
