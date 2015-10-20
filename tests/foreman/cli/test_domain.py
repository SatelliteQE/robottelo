# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Domain  CLI"""
from ddt import data
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.domain import Domain
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_domain, make_location, make_org
from robottelo.decorators import run_only_on
from robottelo.test import MetaCLITestCase


class TestDomain(MetaCLITestCase):
    """Domain CLI tests"""

    factory = make_domain
    factory_obj = Domain

    @data(
        {u'name': u'white spaces {0}'.format(gen_string(str_type='utf8')),
         u'description': gen_string(str_type='alpha')},
        {u'name': gen_string(str_type='utf8'),
         u'description': gen_string(str_type='utf8')},
        {u'name': gen_string(str_type='numeric'),
         u'description': gen_string(str_type='numeric')},
        {u'name': gen_string(str_type='utf8', length=255),
         u'description': gen_string(str_type='utf8', length=255)},
    )
    @run_only_on('sat')
    def test_positive_create(self, options):
        """@Test: Create domain with valid name and description

        @Feature: Domain positive create

        @Assert: Domain successfully created

        """
        domain = make_domain(options)
        self.assertEqual(domain['name'], options['name'])
        self.assertEqual(domain['description'], options['description'])

    @run_only_on('sat')
    def test_create_domain_with_location(self):
        """@Test: Check if domain with location can be created

        @Feature: Domain - Positive create

        @Assert: Domain is created and has new location assigned

        """
        location = make_location()
        domain = make_domain({'location-ids': location['id']})
        self.assertIn(location['name'], domain['locations'])

    @run_only_on('sat')
    def test_create_domain_with_organization(self):
        """@Test: Check if domain with organization can be created

        @Feature: Domain - Positive create

        @Assert: Domain is created and has new organization assigned

        """
        org = make_org()
        domain = make_domain({'organization-ids': org['id']})
        self.assertIn(org['name'], domain['organizations'])

    @data(
        {u'description': gen_string(str_type='utf8', length=256)},
        {u'dns-id': '-1'},
        {u'name': gen_string(str_type='utf8', length=256)},
    )
    @run_only_on('sat')
    def test_negative_create(self, options):
        """@Test: Create domain with invalid values

        @Feature: Domain negative create

        @Assert: Domain is not created

        """
        with self.assertRaises(CLIFactoryError):
            make_domain(options)

    @data(
        {u'name': u'white spaces {0}'.format(gen_string(str_type='utf8')),
         u'description': gen_string(str_type='alpha')},
        {u'name': gen_string(str_type='utf8'),
         u'description': gen_string(str_type='utf8')},
        {u'name': gen_string(str_type='numeric'),
         u'description': gen_string(str_type='numeric')},
        {u'name': gen_string(str_type='utf8', length=255),
         u'description': gen_string(str_type='utf8', length=255)},
    )
    @run_only_on('sat')
    def test_positive_update(self, options):
        """@Test: Update domain with valid values

        @Feature: Domain positive update

        @Assert: Domain is updated

        """
        domain = make_domain({
            u'description': gen_string(str_type='utf8')
        })
        # update description
        Domain.update(dict(options, id=domain['id']))
        # check - domain updated
        domain = Domain.info({'id': domain['id']})
        for key, val in options.iteritems():
            self.assertEqual(domain[key], val)

    @data(
        {u'name': ''},
        {u'name': gen_string(str_type='utf8', length=256)},
        {u'description': gen_string(str_type='utf8', length=256)},
        {u'dns-id': '-1'},
    )
    @run_only_on('sat')
    def test_negative_update(self, options):
        """@Test: Update domain with invalid values

        @Feature: Domain negative update

        @Assert: Domain is not updated

        """
        domain = make_domain()
        # update description
        with self.assertRaises(CLIReturnCodeError):
            Domain.update(dict(options, id=domain['id']))
        # check - domain not updated
        result = Domain.info({'id': domain['id']})
        for key in options.keys():
            self.assertEqual(result[key], domain[key])

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
    @run_only_on('sat')
    def test_positive_set_parameter(self, options):
        """@Test: Domain set-parameter with valid key and value

        @Feature: Domain positive set-parameter

        @Assert: Domain parameter is set

        """
        domain = make_domain()
        options['domain-id'] = domain['id']
        # set parameter
        Domain.set_parameter(options)
        # check - parameter set
        domain = Domain.info({'id': domain['id']})
        parameter = {
            # Sattelite applies lower to parameter's name
            options['name'].lower(): options['value'],
        }
        self.assertDictEqual(parameter, domain['parameters'])

    @data(
        {'name': u'white spaces {0}'.format(gen_string(str_type='utf8')),
         'value': gen_string(str_type='utf8')},
        {'name': '',
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=256),
         'value': gen_string(str_type='utf8')},
    )
    @run_only_on('sat')
    def test_negative_set_parameter(self, options):
        """@Test: Domain set-parameter with invalid values

        @Feature: Domain negative set-parameter

        @Assert: Domain parameter is not set

        """
        domain = make_domain()
        options['domain-id'] = domain['id']
        # set parameter
        with self.assertRaises(CLIReturnCodeError):
            Domain.set_parameter(options)
        # check - parameter not set
        domain = Domain.info({'id': domain['id']})
        self.assertEqual(len(domain['parameters']), 0)

    @data(
        {'name': gen_string(str_type='utf8'),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=255),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8'),
         'value': ''},
    )
    @run_only_on('sat')
    def test_positive_delete_parameter(self, options):
        """@Test: Domain delete-parameter removes parameter

        @Feature: Domain positive delete-parameter

        @Assert: Domain parameter is removed

        """
        domain = make_domain()
        options['domain'] = domain['name']
        Domain.set_parameter(options)
        Domain.delete_parameter({
            u'name': options['name'],
            u'domain-id': domain['id'],
        })
        # check - parameter not set
        domain = Domain.info({'name': domain['name']})
        self.assertEqual(len(domain['parameters']), 0)
