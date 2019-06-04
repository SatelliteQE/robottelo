# -*- encoding: utf-8 -*-
"""Test class for Domain  CLI

:Requirement: Domain

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.domain import Domain
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_domain, make_location, make_org
from robottelo.datafactory import (
    filtered_datapoint, invalid_id_list, valid_data_list
)
from robottelo.decorators import (
    bz_bug_is_open,
    tier1,
    tier2,
    upgrade,
)
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
    if not bz_bug_is_open(1398392):
        params.append({u'dns-id': '-1'})
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
    if not bz_bug_is_open(1398392):
        params.append({u'dns-id': '-1'})
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
    def test_positive_create_with_name_description(self):
        """Create domain with valid name and description

        :id: 018740bf-1551-4162-b88e-4d4905af097b

        :expectedresults: Domain successfully created


        :CaseImportance: Critical
        """
        for options in valid_create_params():
            with self.subTest(options):
                domain = make_domain(options)
                self.assertEqual(domain['name'], options['name'])
                self.assertEqual(
                    domain['description'], options['description'])

    @tier1
    def test_positive_create_with_loc(self):
        """Check if domain with location can be created

        :id: 033cc37d-0189-4b88-94cf-97a96839197a

        :expectedresults: Domain is created and has new location assigned


        :CaseImportance: Critical
        """
        location = make_location()
        domain = make_domain({'location-ids': location['id']})
        self.assertIn(location['name'], domain['locations'])

    @tier1
    def test_positive_create_with_org(self):
        """Check if domain with organization can be created

        :id: f4dfef1b-9b2a-49b8-ade5-031da29e7f6a

        :expectedresults: Domain is created and has new organization assigned


        :CaseImportance: Critical
        """
        org = make_org()
        domain = make_domain({'organization-ids': org['id']})
        self.assertIn(org['name'], domain['organizations'])

    @tier1
    def test_negative_create(self):
        """Create domain with invalid values

        :id: 6d3aec19-75dc-41ca-89af-fef0ca37082d

        :expectedresults: Domain is not created


        :CaseImportance: Critical
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

    @tier1
    def test_positive_update(self):
        """Update domain with valid values

        :id: 9da3cc96-c146-4f82-bb25-b237a367ba91

        :expectedresults: Domain is updated


        :CaseImportance: Critical
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
                for key, val in options.items():
                    self.assertEqual(domain[key], val)

    @tier1
    def test_negative_update(self):
        """Update domain with invalid values

        :id: 9fc708dc-20f9-4d7c-af53-863826462981

        :expectedresults: Domain is not updated


        :CaseImportance: Critical
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
    def test_positive_set_parameter(self):
        """Domain set-parameter with valid key and value

        :id: 62fea9f7-95e2-47f7-bf4b-415ea6fd72f8

        :expectedresults: Domain parameter is set


        :CaseImportance: Critical
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
    def test_negative_set_parameter(self):
        """Domain set-parameter with invalid values

        :id: 991fb849-83be-48f4-a12b-81eabb2bd8d3

        :expectedresults: Domain parameter is not set


        :CaseImportance: Critical
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
    def test_positive_delete_by_id(self):
        """Create Domain with valid values then delete it
        by ID

        :id: b50a5daa-67f8-4ecd-8e03-2a3c492d3c25

        :expectedresults: Domain is deleted

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                domain = make_domain({'name': name})
                Domain.delete({'id': domain['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Domain.info({'id': domain['id']})

    @tier1
    def test_negative_delete_by_id(self):
        """Create Domain then delete it by wrong ID

        :id: 0e4ef107-f006-4433-abc3-f872613e0b91

        :expectedresults: Domain is not deleted

        :CaseImportance: Critical
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Domain.delete({'id': entity_id})

    @tier1
    @upgrade
    def test_positive_delete_parameter(self):
        """Domain delete-parameter removes parameter

        :id: 481afe1c-0b9e-435f-a581-159d9619291c

        :expectedresults: Domain parameter is removed


        :CaseImportance: Critical
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
