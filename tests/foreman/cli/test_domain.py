# -*- encoding: utf-8 -*-
"""Test class for Domain  CLI"""
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.domain import Domain
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_domain, make_location, make_org
from robottelo.datafactory import invalid_id_list, valid_data_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import CLITestCase


def valid_create_params():
    """Returns a list of valid domain create parameters"""
    return [
        {u'name': u'white spaces {0}'.format(gen_string(str_type='utf8')),
         u'description': gen_string(str_type='alpha')},
        {u'name': gen_string(str_type='utf8'),
         u'description': gen_string(str_type='utf8')},
        {u'name': gen_string(str_type='numeric'),
         u'description': gen_string(str_type='numeric')},
        {u'name': gen_string(str_type='utf8', length=255),
         u'description': gen_string(str_type='utf8', length=255)},
    ]


def invalid_create_params():
    """Returns a list of invalid domain create parameters"""
    return [
        {u'dns-id': '-1'},
        {u'name': gen_string(str_type='utf8', length=256)},
    ]


def valid_update_params():
    """Returns a list of valid domain update parameters"""
    return [
        {u'name': u'white spaces {0}'.format(gen_string(str_type='utf8')),
         u'description': gen_string(str_type='alpha')},
        {u'name': gen_string(str_type='utf8'),
         u'description': gen_string(str_type='utf8')},
        {u'name': gen_string(str_type='numeric'),
         u'description': gen_string(str_type='numeric')},
        {u'name': gen_string(str_type='utf8', length=255),
         u'description': gen_string(str_type='utf8', length=255)},
    ]


def invalid_update_params():
    """Returns a list of invalid domain update parameters"""
    return [
        {u'name': ''},
        {u'name': gen_string(str_type='utf8', length=256)},
        {u'dns-id': '-1'},
    ]


def valid_set_params():
    """Returns a list of valid domain set parameters"""
    return [
        {'name': gen_string(str_type='utf8'),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=255),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8'),
         'value': gen_string(str_type='utf8', length=255)},
        {'name': gen_string(str_type='utf8'),
         'value': ''},
    ]


def invalid_set_params():
    """Returns a list of invalid domain set parameters"""
    return [
        {'name': u'white spaces {0}'.format(gen_string(str_type='utf8')),
         'value': gen_string(str_type='utf8')},
        {'name': '',
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=256),
         'value': gen_string(str_type='utf8')},
    ]


def valid_delete_params():
    """Returns a list of valid domain delete parameters"""
    return [
        {'name': gen_string(str_type='utf8'),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=255),
         'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8'),
         'value': ''},
    ]


class DomainTestCase(CLITestCase):
    """Domain CLI tests"""

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name_description(self):
        """Create domain with valid name and description

        @Feature: Domain positive create

        @Assert: Domain successfully created

        """
        for options in valid_create_params():
            with self.subTest(options):
                domain = make_domain(options)
                self.assertEqual(domain['name'], options['name'])
                self.assertEqual(
                    domain['description'], options['description'])

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_loc(self):
        """Check if domain with location can be created

        @Feature: Domain - Positive create

        @Assert: Domain is created and has new location assigned

        """
        location = make_location()
        domain = make_domain({'location-ids': location['id']})
        self.assertIn(location['name'], domain['locations'])

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_org(self):
        """Check if domain with organization can be created

        @Feature: Domain - Positive create

        @Assert: Domain is created and has new organization assigned

        """
        org = make_org()
        domain = make_domain({'organization-ids': org['id']})
        self.assertIn(org['name'], domain['organizations'])

    @tier1
    @run_only_on('sat')
    def test_negative_create(self):
        """Create domain with invalid values

        @Feature: Domain negative create

        @Assert: Domain is not created

        """
        for options in invalid_create_params():
            with self.subTest(options):
                with self.assertRaises(CLIFactoryError):
                    make_domain(options)

    @tier1
    @run_only_on('sat')
    def test_positive_update(self):
        """Update domain with valid values

        @Feature: Domain positive update

        @Assert: Domain is updated

        """
        domain = make_domain({
            u'description': gen_string(str_type='utf8')
        })
        for options in valid_update_params():
            with self.subTest(options):
                # update description
                Domain.update(dict(options, id=domain['id']))
                # check - domain updated
                domain = Domain.info({'id': domain['id']})
                for key, val in options.iteritems():
                    self.assertEqual(domain[key], val)

    @tier1
    @run_only_on('sat')
    def test_negative_update(self):
        """Update domain with invalid values

        @Feature: Domain negative update

        @Assert: Domain is not updated

        """
        domain = make_domain()
        for options in invalid_update_params():
            with self.subTest(options):
                with self.assertRaises(CLIReturnCodeError):
                    Domain.update(dict(options, id=domain['id']))
                # check - domain not updated
                result = Domain.info({'id': domain['id']})
                for key in options.keys():
                    self.assertEqual(result[key], domain[key])

    @tier1
    @run_only_on('sat')
    def test_positive_set_parameter(self):
        """Domain set-parameter with valid key and value

        @Feature: Domain positive set-parameter

        @Assert: Domain parameter is set

        """
        for options in valid_set_params():
            with self.subTest(options):
                domain = make_domain()
                options['domain-id'] = domain['id']
                Domain.set_parameter(options)
                domain = Domain.info({'id': domain['id']})
                parameter = {
                    # Satellite applies lower to parameter's name
                    options['name'].lower(): options['value'],
                }
                self.assertDictEqual(parameter, domain['parameters'])

    @tier1
    @run_only_on('sat')
    def test_negative_set_parameter(self):
        """Domain set-parameter with invalid values

        @Feature: Domain negative set-parameter

        @Assert: Domain parameter is not set

        """
        domain = make_domain()
        for options in invalid_set_params():
            with self.subTest(options):
                options['domain-id'] = domain['id']
                # set parameter
                with self.assertRaises(CLIReturnCodeError):
                    Domain.set_parameter(options)
                # check - parameter not set
                domain = Domain.info({'id': domain['id']})
                self.assertEqual(len(domain['parameters']), 0)

    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_id(self):
        """Create Domain with valid values then delete it
        by ID

        @feature: Domain

        @assert: Domain is deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                domain = make_domain({'name': name})
                Domain.delete({'id': domain['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Domain.info({'id': domain['id']})

    @tier1
    @run_only_on('sat')
    def test_negative_delete_by_id(self):
        """Create Domain then delete it by wrong ID

        @feature: Domain

        @assert: Domain is not deleted
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Domain.delete({'id': entity_id})

    @tier1
    @run_only_on('sat')
    def test_positive_delete_parameter(self):
        """Domain delete-parameter removes parameter

        @Feature: Domain positive delete-parameter

        @Assert: Domain parameter is removed

        """
        for options in valid_delete_params():
            with self.subTest(options):
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
