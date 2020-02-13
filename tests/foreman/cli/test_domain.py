# -*- encoding: utf-8 -*-
"""Test class for Domain  CLI

:Requirement: Domain

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.domain import Domain
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_domain
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_id_list
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


@filtered_datapoint
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


@filtered_datapoint
def invalid_create_params():
    """Returns a list of invalid domain create parameters"""
    params = [
        {u'name': gen_string(str_type='utf8', length=256)},
    ]
    return params


@filtered_datapoint
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


@filtered_datapoint
def invalid_update_params():
    """Returns a list of invalid domain update parameters"""
    params = [
        {u'name': ''},
        {u'name': gen_string(str_type='utf8', length=256)},
    ]
    return params


@filtered_datapoint
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


@filtered_datapoint
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


@filtered_datapoint
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
    @upgrade
    def test_positive_create_update_delete_domain(self):
        """Create domain, update and delete domain and set parameters

        :id: 018740bf-1551-4162-b88e-4d4905af097b

        :expectedresults: Domain successfully created, updated and deleted


        :CaseImportance: Critical
        """
        options = valid_create_params()[0]
        location = make_location()
        org = make_org()
        domain = make_domain({
            u'name': options['name'],
            u'description': options['description'],
            u'location-ids': location['id'],
            u'organization-ids': org['id']
            })
        self.assertEqual(domain['name'], options['name'])
        self.assertEqual(domain['description'], options['description'])
        self.assertIn(location['name'], domain['locations'])
        self.assertIn(org['name'], domain['organizations'])

        # set parameter
        parameter_options = valid_set_params()[0]
        parameter_options['domain-id'] = domain['id']
        Domain.set_parameter(parameter_options)
        domain = Domain.info({'id': domain['id']})
        parameter = {
            # Satellite applies lower to parameter's name
            parameter_options['name'].lower(): parameter_options['value'],
        }
        self.assertDictEqual(parameter, domain['parameters'])

        # update domain
        options = valid_update_params()[0]
        Domain.update(dict(options, id=domain['id']))
        # check - domain updated
        domain = Domain.info({'id': domain['id']})
        for key, val in options.items():
            self.assertEqual(domain[key], val)

        # delete parameter
        Domain.delete_parameter({
            u'name': parameter_options['name'],
            u'domain-id': domain['id'],
        })
        # check - parameter not set
        domain = Domain.info({'name': domain['name']})
        self.assertEqual(len(domain['parameters']), 0)

        # delete domain
        Domain.delete({'id': domain['id']})
        with self.assertRaises(CLIReturnCodeError):
            Domain.info({'id': domain['id']})

    @tier2
    def test_negative_create(self):
        """Create domain with invalid values

        :id: 6d3aec19-75dc-41ca-89af-fef0ca37082d

        :expectedresults: Domain is not created


        :CaseImportance: Medium
        """
        for options in invalid_create_params():
            with self.subTest(options):
                with self.assertRaises(CLIFactoryError):
                    make_domain(options)

    @tier2
    def test_negative_create_with_invalid_dns_id(self):
        """Attempt to register a domain with invalid id

        :id: 4aa52167-368a-41ad-87b7-41d468ad41a8

        :expectedresults: Error is raised and user friendly message returned

        :BZ: 1398392

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        with self.assertRaises(CLIFactoryError) as context:
            make_domain({
                'name': gen_string('alpha'),
                'dns-id': -1,
            })
        valid_messages = ['Invalid smart-proxy id', 'Invalid capsule id']
        exception_string = str(context.exception)
        messages = [
            message
            for message in valid_messages
            if message in exception_string
        ]
        self.assertGreater(len(messages), 0)

    @tier2
    def test_negative_update(self):
        """Update domain with invalid values

        :id: 9fc708dc-20f9-4d7c-af53-863826462981

        :expectedresults: Domain is not updated


        :CaseImportance: Medium
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

    @tier2
    def test_negative_set_parameter(self):
        """Domain set-parameter with invalid values

        :id: 991fb849-83be-48f4-a12b-81eabb2bd8d3

        :expectedresults: Domain parameter is not set


        :CaseImportance: Low
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

    @tier2
    def test_negative_delete_by_id(self):
        """Create Domain then delete it by wrong ID

        :id: 0e4ef107-f006-4433-abc3-f872613e0b91

        :expectedresults: Domain is not deleted

        :CaseImportance: Medium
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Domain.delete({'id': entity_id})
