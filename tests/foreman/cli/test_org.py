# -*- encoding: utf-8 -*-
# pylint: disable=R0904
"""Test class for Organization CLI"""
import random

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    make_domain, make_hostgroup, make_lifecycle_environment,
    make_medium, make_org, make_proxy, make_subnet, make_template, make_user,
    make_compute_resource, CLIFactoryError)
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.org import Org
from robottelo.config import conf
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.decorators import (
    data, run_only_on, skip_if_bug_open, stubbed)
from robottelo.test import CLITestCase


def positive_create_data_1():
    """Random data for positive creation"""

    return (
        {'name': gen_string("latin1")},
        {'name': gen_string("utf8")},
        {'name': gen_string("alpha")},
        {'name': gen_string("alphanumeric")},
        {'name': gen_string("numeric")},
        {'name': gen_string("html")},
    )


# Use this when name and label must match. Labels cannot
# contain the same data type as names, so this is a bit limited
# compared to other tests.
# Label cannot contain characters other than ascii alpha numerals, '_', '-'.
def positive_create_data_2():
    """Random simpler data for positive creation"""

    return (
        {'name': gen_string("alpha")},
        {'name': gen_string("alphanumeric")},
        {'name': gen_string("numeric")},
        {'name': '{0}-{1}'.format(gen_string("alpha", 5),
                                  gen_string("alpha", 5))},
        {'name': '{0}_{1}'.format(gen_string("alpha", 5),
                                  gen_string("alpha", 5))},
    )


# Label cannot contain characters other than ascii alpha numerals, '_', '-'.
def positive_name_label_data():
    """Random data for Label tests"""

    return (
        {'name': gen_string("latin1"),
         'label': gen_string("alpha")},
        {'name': gen_string("utf8"),
         'label': gen_string("alpha")},
        {'name': gen_string("alpha"),
         'label': gen_string("alpha")},
        {'name': gen_string("alphanumeric"),
         'label': gen_string("alpha")},
        {'name': gen_string("numeric"),
         'label': gen_string("alpha")},
        {'name': gen_string("html"),
         'label': gen_string("alpha")},
    )


def positive_name_desc_data():
    """Random data for Descriptions tests"""

    return (
        {'name': gen_string("latin1"),
         'description': gen_string("latin1")},
        {'name': gen_string("utf8"),
         'description': gen_string("utf8")},
        {'name': gen_string("alpha"),
         'description': gen_string("alpha")},
        {'name': gen_string("alphanumeric"),
         'description': gen_string("alphanumeric")},
        {'name': gen_string("numeric"),
         'description': gen_string("numeric")},
        {'name': gen_string("html"),
         'description': gen_string("numeric")},
    )


def positive_name_desc_label_data():
    """Random data for Labels and Description"""

    return (
        {'name': gen_string("alpha"),
         'description': gen_string("alpha"),
         'label': gen_string("alpha")},
        {'name': gen_string("alphanumeric"),
         'description': gen_string("alphanumeric"),
         'label': gen_string("alpha")},
        {'name': gen_string("numeric"),
         'description': gen_string("numeric"),
         'label': gen_string("alpha")},
        {'name': gen_string("html"),
         'description': gen_string("numeric"),
         'label': gen_string("alpha")},
    )


@ddt
class TestOrg(CLITestCase):
    """Tests for Organizations via Hammer CLI"""

    # Tests for issues

    # This test also covers the redmine bug 4443
    @data(*positive_create_data_1())
    def test_redmine_4486(self, test_data):
        """@test: Can search for an organization by name

        @feature: Organizations

        @assert: organization is created and can be searched by name

        """
        org = make_org(test_data)
        # Can we find the new object?
        result = Org.exists(search=('name', org['name']))
        self.assertEqual(org['name'], result['name'])

    @run_only_on('sat')
    def test_remove_domain(self):
        """@Test: Check if a Domain can be removed from an Org

        @Feature: Org - Domain

        @Assert: Domain is removed from the org

        """
        org = make_org()
        domain = make_domain()
        Org.add_domain({
            'domain': domain['name'],
            'name': org['name'],
        })
        Org.remove_domain({
            'domain': domain['name'],
            'name': org['name'],
        })

    @data(*positive_create_data_1())
    def test_bugzilla_1079587(self, test_data):
        """@test: Search for an organization by label

        @feature: Organizations

        @assert: organization is created and can be searched by label

        """
        org = make_org(test_data)
        # Can we find the new object?
        result = Org.exists(search=('label', org['label']))
        self.assertEqual(org['name'], result['name'])

    def test_bugzilla_1076568_1(self):
        """@test: Delete organization by name

        @feature: Organizations

        @assert: Organization is deleted

        """
        org = make_org()
        Org.delete({'name': org['name']})
        # Can we find the object?
        with self.assertRaises(CLIReturnCodeError):
            Org.info({'id': org['id']})

    def test_bugzilla_1076568_2(self):
        """@test: Delete organization by ID

        @feature: Organizations

        @assert: Organization is deleted

        """
        org = make_org()
        Org.delete({'id': org['id']})
        # Can we find the object?
        with self.assertRaises(CLIReturnCodeError):
            Org.info({'id': org['id']})

    def test_bugzilla_1076568_3(self):
        """@test: Delete organization by label

        @feature: Organizations

        @assert: Organization is deleted

        """
        org = make_org()
        Org.delete({'label': org['label']})
        # Can we find the object?
        with self.assertRaises(CLIReturnCodeError):
            Org.info({'id': org['id']})

    def test_bugzilla_1076541(self):
        """@test: Cannot update organization name via CLI

        @feature: Organizations

        @assert: Organization name is updated

        """
        org = make_org()
        # Update the org name
        new_name = gen_string('utf8', 15)
        Org.update({
            'id': org['id'],
            'new-name': new_name,
        })
        # Fetch the org again
        org = Org.info({'id': org['id']})
        self.assertEqual(org['name'], new_name)

    def test_bugzilla_1075163(self):
        """@Test: Add --label as a valid argument to organization info command

        @Feature: Organization

        @Assert: Organization is created and info can be obtained by its label
        graciously

        """
        org = make_org()
        result = Org.info({'label': org['label']})
        self.assertEqual(org['id'], result['id'])

    def test_bugzilla_1075156(self):
        """@Test: Cannot use CLI info for organizations by name

        @Feature: Org - Positive Create

        @Assert: Organization is created and info can be obtained by its name
        graciously

        """
        org = make_org()
        result = Org.info({'name': org['name']})
        self.assertEqual(org['id'], result['id'])

    @run_only_on('sat')
    def test_bugzilla_1062295_1(self):
        """@Test: Foreman Cli : Add_Config template fails

        @Feature: Org

        @Assert: Config Template is added to the org

        """
        org = make_org()
        template = make_template()
        Org.add_config_template({
            'config-template': template['name'],
            'name': org['name'],
        })

    @run_only_on('sat')
    def test_bugzilla_1062295_2(self):
        """@Test: Foreman Cli : Add_Config template fails

        @Feature: Org

        @Assert: ConfigTemplate is removed from the org

        """
        org = make_org()
        template = make_template()
        Org.add_config_template({
            'config-template': template['name'],
            'name': org['name'],
        })
        Org.remove_config_template({
            'config-template': template['name'],
            'name': org['name'],
        })

    def test_bugzilla_1023125(self):
        """@Test: hammer-cli: trying to create duplicate org throws unhandled
        ISE

        @Feature: Org - Positive Create

        @Assert: Organization is created once and second attempt is handled
        graciously

        """
        org = make_org()
        # Create new org with the same name as before
        # should yield an exception
        with self.assertRaises(CLIFactoryError):
            make_org({'name': org['name']})

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    def test_bugzilla_1078866(self):
        """@Test: hammer organization <info,list> --help types information
        doubled

        @Feature: org info/list

        @Assert: no duplicated lines in usage message

        """
        # org list --help:
        result = Org.list({'help': True})
        # get list of lines and check they all are unique
        lines = [line['message'] for line in result]
        self.assertEqual(len(set(lines)), len(lines))

        # org info --help:info returns more lines (obviously), ignore exception
        result = Org.info({'help': True})

        # get list of lines and check they all are unique
        lines = [line for line in result['options']]
        self.assertEqual(len(set(lines)), len(lines))

    # CRUD

    @data(*positive_create_data_1())
    def test_positive_create_1(self, test_data):
        """@test: Create organization with valid name only

        @feature: Organizations

        @assert: organization is created, label is auto-generated

        """
        org = make_org(test_data)
        self.assertEqual(org['name'], test_data['name'])

    @data(*positive_create_data_2())
    def test_positive_create_2(self, test_data):
        """@test: Create organization with valid matching name and label only

        @feature: Organizations

        @assert: organization is created, label matches name

        """
        test_data['label'] = test_data['name']
        org = make_org(test_data)
        self.assertEqual(org['name'], org['label'])

    @skip_if_bug_open('bugzilla', 1142821)
    @data(*positive_name_label_data())
    def test_positive_create_3(self, test_data):
        """@test: Create organization with valid unmatching name and label only

        @feature: Organizations

        @assert: organization is created, label does not match name

        @bz: 1142821

        """
        org = make_org(test_data)
        self.assertNotEqual(org['name'], org['label'])
        self.assertEqual(org['name'], test_data['name'])
        self.assertEqual(org['label'], test_data['label'])

    @data(*positive_name_desc_data())
    def test_positive_create_4(self, test_data):
        """@test: Create organization with valid name and description only

        @feature: Organizations

        @assert: organization is created, label is auto-generated

        """
        org = make_org(test_data)
        self.assertNotEqual(org['name'], org['description'])
        self.assertEqual(org['name'], test_data['name'])
        self.assertEqual(org['description'], test_data['description'])

    @skip_if_bug_open('bugzilla', 1142821)
    @data(*positive_name_desc_data())
    def test_positive_create_5(self, test_data):
        """@test: Create organization with valid name, label and description

        @feature: Organizations

        @assert: organization is created

        @bz: 1142821

        """
        test_data['label'] = gen_string('alpha')
        org = make_org(test_data)
        self.assertEqual(org['name'], test_data['name'])
        self.assertEqual(org['description'], test_data['description'])
        self.assertEqual(org['label'], test_data['label'])

    def test_list_org(self):
        """@Test: Check if Org can be listed

        @Feature: Org - List

        @Assert: Org is listed

        """
        Org.list()

    @run_only_on('sat')
    def test_add_subnet(self):
        """@Test: Check if a subnet can be added to an Org

        @Feature: Org - Subnet

        @Assert: Subnet is added to the org

        """
        org = make_org()
        subnet = make_subnet()
        Org.add_subnet({
            'name': org['name'],
            'subnet': subnet['name'],
        })

    @run_only_on('sat')
    def test_remove_subnet(self):
        """@Test: Check if a subnet can be removed from an Org

        @Feature: Org - Subnet

        @Assert: Subnet is removed from the org

        """
        org = make_org()
        subnet = make_subnet()
        Org.add_subnet({
            'name': org['name'],
            'subnet': subnet['name'],
        })
        Org.remove_subnet({
            'name': org['name'],
            'subnet': subnet['name'],
        })

    def test_add_user(self):
        """@Test: Check if a User can be added to an Org

        @Feature: Org - User

        @Assert: User is added to the org

        """
        org = make_org()
        user = make_user()
        Org.add_user({
            'name': org['name'],
            'user-id': user['id'],
        })

    def test_remove_user(self):
        """@Test: Check if a User can be removed from an Org

        @Feature: Org - User

        @Assert: User is removed from the org

        """
        org = make_org()
        user = make_user()
        Org.add_user({
            'name': org['name'],
            'user-id': user['login'],
        })
        Org.remove_user({
            'name': org['name'],
            'user-id': user['login'],
        })

    @run_only_on('sat')
    def test_add_hostgroup(self):
        """@Test: Check if a hostgroup can be added to an Org

        @Feature: Org - Hostgroup

        @Assert: Hostgroup is added to the org

        """
        org = make_org()
        hostgroup = make_hostgroup()
        Org.add_hostgroup({
            'hostgroup': hostgroup['name'],
            'name': org['name'],
        })

    @run_only_on('sat')
    def test_remove_hostgroup(self):
        """@Test: Check if a hostgroup can be removed from an Org

        @Feature: Org - Subnet

        @Assert: Hostgroup is removed from the org

        """
        org = make_org()
        hostgroup = make_hostgroup()
        Org.add_hostgroup({
            'hostgroup': hostgroup['name'],
            'name': org['name'],
        })
        Org.remove_hostgroup({
            'hostgroup': hostgroup['name'],
            'name': org['name'],
        })

    @run_only_on('sat')
    def test_add_computeresource(self):
        """@Test: Check if a Compute Resource can be added to an Org

        @Feature: Org - Compute Resource

        @Assert: Compute Resource is added to the org

        """
        org = make_org()
        compute_res = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname'],
        })
        Org.add_compute_resource({
            'compute-resource': compute_res['name'],
            'name': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(org['compute-resources'][0], compute_res['name'])

    def test_add_compute_resource_by_id(self):
        """@Test: Check that new organization with compute resource associated
        to it can be created in the system

        @Feature: Org - Compute Resource

        @Assert: Organization with compute resource created successfully

        """
        compute_res = make_compute_resource()
        org = make_org({'compute-resource-ids': compute_res['id']})
        self.assertEqual(len(org['compute-resources']), 1)
        self.assertEqual(org['compute-resources'][0], compute_res['name'])

    def test_add_multiple_compute_resources_by_id(self):
        """@Test: Check that new organization with multiple compute resources
        associated to it can be created in the system

        @Feature: Org - Compute Resource

        @Assert: Organization with compute resources created successfully

        """
        cr_amount = random.randint(3, 5)
        resources = [make_compute_resource() for _ in range(cr_amount)]
        org = make_org({
            'compute-resource-ids':
                [resource['id'] for resource in resources],
        })
        self.assertEqual(len(org['compute-resources']), cr_amount)
        for resource in resources:
            self.assertIn(resource['name'], org['compute-resources'])

    @run_only_on('sat')
    @stubbed()
    def test_remove_computeresource(self):
        """@Test: Check if a ComputeResource can be removed from an Org

        @Feature: Org - ComputeResource

        @Assert: ComputeResource is removed from the org

        @status: manual

        """
        pass

    @run_only_on('sat')
    def test_add_medium(self):
        """@Test: Check if a Medium can be added to an Org

        @Feature: Org - Medium

        @Assert: Medium is added to the org

        """
        org = make_org()
        medium = make_medium()
        Org.add_medium({
            'name': org['name'],
            'medium': medium['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertIn(medium['name'], org['installation-media'])

    @run_only_on('sat')
    def test_remove_medium(self):
        """@Test: Check if a Medium can be removed from an Org

        @Feature: Org - Medium

        @Assert: Medium is removed from the org

        """
        org = make_org()
        medium = make_medium()
        Org.add_medium({
            'name': org['name'],
            'medium': medium['name']
        })
        Org.remove_medium({
            'name': org['name'],
            'medium': medium['name']
        })
        org = Org.info({'id': org['id']})
        self.assertNotIn(medium['name'], org['installation-media'])

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
    )
    def test_add_configtemplate(self, name):
        """@Test: Check if a Config Template can be added to an Org

        @Feature: Org - Config Template

        @Assert: Config Template is added to the org

        """
        org = make_org()
        template = make_template({
            'content': gen_string('alpha'),
            'name': name,
        })
        Org.add_config_template({
            'config-template': template['name'],
            'name': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            org['templates'],
        )

    def test_add_configtemplate_by_id(self):
        """@Test: Check that new organization with config template associated
        to it can be created in the system

        @Feature: Org - Config Template

        @Assert: Organization with config template created successfully

        """
        conf_templ = make_template()
        org = make_org({'config-template-ids': conf_templ['id']})
        self.assertIn(
            u'{0} ({1})'.format(conf_templ['name'], conf_templ['type']),
            org['templates'],
        )

    def test_add_multiple_configtemplate_by_id(self):
        """@Test: Check that new organization with multiple config templates
        associated to it can be created in the system

        @Feature: Org - Config Template

        @Assert: Organization with config templates created successfully

        """
        templates_amount = random.randint(3, 5)
        templates = [make_template() for _ in range(templates_amount)]
        org = make_org({
            'config-template-ids':
                [template['id'] for template in templates],
        })
        self.assertGreaterEqual(len(org['templates']), templates_amount)
        for template in templates:
            self.assertIn(
                u'{0} ({1})'.format(template['name'], template['type']),
                org['templates']
            )

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
    )
    def test_remove_configtemplate(self, name):
        """@Test: Check if a ConfigTemplate can be removed from an Org

        @Feature: Org - ConfigTemplate

        @Assert: ConfigTemplate is removed from the org

        """
        org = make_org()
        template = make_template({
            'content': gen_string('alpha'),
            'name': name,
        })
        # Add config-template
        Org.add_config_template({
            'name': org['name'],
            'config-template': template['name']
        })
        result = Org.info({'id': org['id']})
        self.assertIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            result['templates'],
        )
        # Remove config-template
        Org.remove_config_template({
            'config-template': template['name'],
            'name': org['name'],
        })
        result = Org.info({'id': org['id']})
        self.assertNotIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            result['templates'],
        )

    @run_only_on('sat')
    def test_add_environment(self):
        """@Test: Check if an environment can be added to an Org

        @Feature: Org - Environment

        @Assert: Environment is added to the org

        """
        # Create a lifecycle environment.
        org_id = make_org()['id']
        lc_env_name = make_lifecycle_environment(
            {'organization-id': org_id})['name']
        # Read back information about the lifecycle environment. Verify the
        # sanity of that information.
        response = LifecycleEnvironment.list({
            'name': lc_env_name,
            'organization-id': org_id,
        })
        self.assertEqual(response[0]['name'], lc_env_name)

    @run_only_on('sat')
    def test_remove_environment(self):
        """@Test: Check if an Environment can be removed from an Org

        @Feature: Org - Environment

        @Assert: Environment is removed from the org

        """
        # Create a lifecycle environment.
        org_id = make_org()['id']
        lc_env_name = make_lifecycle_environment(
            {'organization-id': org_id})['name']
        lc_env_attrs = {
            'name': lc_env_name,
            'organization-id': org_id,
        }
        # Read back information about the lifecycle environment. Verify the
        # sanity of that information.
        response = LifecycleEnvironment.list(lc_env_attrs)
        self.assertEqual(response[0]['name'], lc_env_name)
        # Delete it.
        LifecycleEnvironment.delete(lc_env_attrs)
        # We should get a zero-length response when searcing for the LC env.
        response = LifecycleEnvironment.list(lc_env_attrs)
        self.assertEqual(len(response), 0)

    @run_only_on('sat')
    @stubbed("Needs to be re-worked!")
    def test_add_smartproxy(self):
        """@Test: Check if a Smartproxy can be added to an Org

        @Feature: Org - Smartproxy

        @Assert: Smartproxy is added to the org

        """
        org = make_org()
        proxy = make_proxy()
        Org.add_smart_proxy({
            'name': org['name'],
            'smart-proxy': proxy['name'],
        })

    @run_only_on('sat')
    @stubbed("Needs to be re-worked!")
    def test_remove_smartproxy(self):
        """@Test: Check if a Smartproxy can be removed from an Org

        @Feature: Org - Smartproxy

        @Assert: Smartproxy is removed from the org

        """
        org = make_org()
        proxy = make_proxy()
        Org.add_smart_proxy({
            'name': org['name'],
            'smart-proxy': proxy['name'],
        })
        Org.remove_smart_proxy({
            'name': org['name'],
            'smart-proxy': proxy['name'],
        })

    # Negative Create

    @data({'label': gen_string('alpha'),
           'name': gen_string('alpha', 300)},
          {'label': gen_string('alpha'),
           'name': gen_string('numeric', 300)},
          {'label': gen_string('alpha'),
           'name': gen_string('alphanumeric', 300)},
          {'label': gen_string('alpha'),
           'name': gen_string('utf8', 300)},
          {'label': gen_string('alpha'),
           'name': gen_string('latin1', 300)},
          {'label': gen_string('alpha'),
           'name': gen_string('html', 300)})
    def test_negative_create_0(self, test_data):
        """@test: Create organization with valid label and description, name is
        too long

        @feature: Organizations

        @assert: organization is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            Org.create({
                'description': test_data['label'],
                'label': test_data['label'],
                'name': test_data['name'],
            })

    @data(gen_string('alpha'),
          gen_string('numeric'),
          gen_string('alphanumeric'))
    def test_negative_create_1(self, test_data):
        """@test: Create organization with valid label and description, name is
        blank

        @feature: Organizations

        @assert: organization is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            Org.create({
                'description': test_data,
                'label': test_data,
                'name': '',
            })

    @data(gen_string('alpha'),
          gen_string('numeric'),
          gen_string('alphanumeric'))
    def test_negative_create_2(self, test_data):
        """@test: Create organization with valid label and description, name is
        whitespace

        @feature: Organizations

        @assert: organization is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            Org.create({
                'description': test_data,
                'label': test_data,
                'name': ' \t',
            })

    @data(gen_string('alpha'),
          gen_string('numeric'),
          gen_string('alphanumeric'))
    def test_negative_create_3(self, test_data):
        """@test: Create organization with valid values, then create a new one
        with same values.

        @feature: Organizations

        @assert: organization is not created

        """
        Org.create({
            'description': test_data,
            'label': test_data,
            'name': test_data,
        })
        with self.assertRaises(CLIReturnCodeError):
            Org.create({
                'description': test_data,
                'label': test_data,
                'name': test_data,
            })

    # Positive Delete

    @skip_if_bug_open('bugzilla', 1076568)
    @data(*positive_name_desc_label_data())
    def test_positive_delete_1(self, test_data):
        """@test: Create organization with valid values then delete it
        by ID

        @feature: Organizations

        @assert: organization is deleted

        @BZ: 1076568

        """
        org = make_org(test_data)
        Org.delete({'id': org['id']})
        # Can we find the object?
        with self.assertRaises(CLIReturnCodeError):
            Org.info({'id': org['id']})

    @data(*positive_name_desc_label_data())
    def test_positive_delete_2(self, test_data):
        """@test: Create organization with valid values then delete it
        by label

        @feature: Organizations

        @assert: organization is deleted

        """
        org = make_org(test_data)
        Org.delete({'label': org['label']})
        # Can we find the object?
        with self.assertRaises(CLIReturnCodeError):
            Org.info({'id': org['id']})

    @data(*positive_name_desc_label_data())
    def test_positive_delete_3(self, test_data):
        """@test: Create organization with valid values then delete it
        by name

        @feature: Organizations

        @assert: organization is deleted

        """
        org = make_org(test_data)
        Org.delete({'name': org['name']})
        # Can we find the object?
        with self.assertRaises(CLIReturnCodeError):
            Org.info({'id': org['id']})

    @data({'name': gen_string("latin1")},
          {'name': gen_string("utf8")},
          {'name': gen_string("alpha")},
          {'name': gen_string("alphanumeric")},
          {'name': gen_string("numeric")},
          {'name': gen_string("html")})
    def test_positive_update_1(self, test_data):
        """@test: Create organization with valid values then update its name

        @feature: Organizations

        @assert: organization name is updated

        """
        org = make_org()
        # Update the org name
        Org.update({
            'id': org['id'],
            'new-name': test_data['name'],
        })
        # Fetch the org again
        org = Org.info({'id': org['id']})
        self.assertEqual(org['name'], test_data['name'])

    @data({'description': gen_string("latin1")},
          {'description': gen_string("utf8")},
          {'description': gen_string("alpha")},
          {'description': gen_string("alphanumeric")},
          {'description': gen_string("numeric")},
          {'description': gen_string("html")})
    def test_positive_update_3(self, test_data):
        """@test: Create organization with valid values then update its
        description

        @feature: Organizations

        @assert: organization description is updated

        """
        org = make_org()
        # Update the org name
        Org.update({
            'description': test_data['description'],
            'id': org['id'],
        })
        # Fetch the org again
        org = Org.info({'id': org['id']})
        self.assertEqual(org['description'], test_data['description'])

    @skip_if_bug_open('bugzilla', 1114136)
    @data({'description': gen_string("latin1"),
           'name': gen_string("latin1")},
          {'description': gen_string("utf8"),
           'name': gen_string("utf8")},
          {'description': gen_string("alpha"),
           'name': gen_string("alpha")},
          {'description': gen_string("alphanumeric"),
           'name': gen_string("alphanumeric")},
          {'description': gen_string("numeric"),
           'name': gen_string("numeric")},
          {'description': gen_string("html"),
           'name': gen_string("html")})
    def test_positive_update_4(self, test_data):
        """@test: Create organization with valid values then update all values

        @feature: Organizations

        @assert: organization name and description are updated

        @bz: 1114136

        """
        org = make_org()
        # Update the org name
        Org.update({
            'description': test_data['description'],
            'id': org['id'],
            'new-name': test_data['name'],
        })
        # Fetch the org again
        org = Org.info({'id': org['id']})
        self.assertEqual(org['description'], test_data['description'])
        self.assertEqual(org['name'], test_data['name'])

    # Negative Update

    @data({'name': ' '},
          {'name': gen_string('alpha', 300)},
          {'name': gen_string('numeric', 300)},
          {'name': gen_string('alphanumeric', 300)},
          {'name': gen_string('utf8', 300)},
          {'name': gen_string('latin1', 300)},
          {'name': gen_string('html', 300)})
    def test_negative_update_1(self, test_data):
        """@test: Create organization then fail to update
        its name

        @feature: Organizations

        @assert: organization name is not updated

        """
        org = make_org()
        # Update the org name
        with self.assertRaises(CLIReturnCodeError):
            Org.update({
                'id': org['id'],
                'new-name': test_data['name'],
            })

    # Miscelaneous

    @stubbed()
    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_list_key_1(self, test_data):
        """@test: Create organization and list it

        @feature: Organizations

        @assert: organization is displayed/listed

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_search_key_1(self, test_data):
        """@test: Create organization and search/find it

        @feature: Organizations

        @assert: organization can be found

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_info_key_1(self, test_data):
        """@test: Create single organization and get its info

        @feature: Organizations

        @assert: specific information for organization matches the
        creation values

        @status: manual

        """

        pass

    # Associations

    @stubbed()
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_remove_domain_1(self, test_data):
        """@test: Add a domain to an organization and remove it by organization
        name and domain name

        @feature: Organizations

        @assert: the domain is removed from the organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_remove_domain_2(self, test_data):
        """@test: Add a domain to an organization and remove it by organization
        ID and domain name

        @feature: Organizations

        @assert: the domain is removed from the organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_remove_domain_3(self, test_data):
        """@test: Add a domain to an organization and remove it by organization
        name and domain ID

        @feature: Organizations

        @assert: the domain is removed from the organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_remove_domain_4(self, test_data):
        """@test: Add a domain to an organization and remove it by organization
        ID and domain ID

        @feature: Organizations

        @assert: the domain is removed from the organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        user name is alpha
        user name is numeric
        user name is alpha_numeric
        user name is utf-8
        user name is latin1
        user name is html
    """)
    def test_remove_user_1(self, test_data):
        """@test: Create different types of users then add/remove user
        by using the organization ID

        @feature: Organizations

        @assert: User is added and then removed from organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        user name is alpha
        user name is numeric
        user name is alpha_numeric
        user name is utf-8
        user name is latin1
        user name is html
    """)
    def test_remove_user_2(self, test_data):
        """@test: Create different types of users then add/remove user
        by using the organization name

        @feature: Organizations

        @assert: The user is added then removed from the organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        user name is alpha and admin
        user name is numeric and admin
        user name is alpha_numeric and admin
        user name is utf-8 and admin
        user name is latin1 and admin
        user name is html and admin
    """)
    def test_remove_user_3(self, test_data):
        """@test: Create admin users then add user and remove it
        by using the organization name

        @feature: Organizations

        @assert: The user is added then removed from the organization

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_remove_hostgroup_1(self, test_data):
        """@test: Add a hostgroup and remove it by using the organization
        name and hostgroup name

        @feature: Organizations

        @assert: hostgroup is added to organization then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_remove_hostgroup_2(self, test_data):
        """@test: Add a hostgroup and remove it by using the organization
        ID and hostgroup name

        @feature: Organizations

        @assert: hostgroup is added to organization then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_remove_hostgroup_3(self, test_data):
        """@test: Add a hostgroup and remove it by using the organization
        name and hostgroup ID

        @feature: Organizations

        @assert: hostgroup is added to organization then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_remove_hostgroup_4(self, test_data):
        """@test: Add a hostgroup and remove it by using the organization
        ID and hostgroup ID

        @feature: Organizations

        @assert: hostgroup is added to organization then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_1(self, test_data):
        """@test: Add a smart proxy by using organization name and smartproxy name

        @feature: Organizations

        @assert: smartproxy is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_2(self, test_data):
        """@test: Add a smart proxy by using organization ID and smartproxy name

        @feature: Organizations

        @assert: smartproxy is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_3(self, test_data):
        """@test: Add a smart proxy by using organization name and smartproxy ID

        @feature: Organizations

        @assert: smartproxy is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_4(self, test_data):
        """@test: Add a smart proxy by using organization ID and smartproxy ID

        @feature: Organizations

        @assert: smartproxy is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @data(gen_string('alpha'),
          gen_string('numeric'),
          gen_string('alphanumeric'),
          gen_string('utf8'),
          gen_string('latin1'))
    def test_add_subnet_1(self, name):
        """@test: Add a subnet by using organization name and subnet name

        @feature: Organizations

        @assert: subnet is added

        """
        org = make_org()
        new_subnet = make_subnet({'name': name})
        Org.add_subnet({
            'name': org['name'],
            'subnet': new_subnet['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertIn(name, org['subnets'][0])

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_add_subnet_2(self, test_data):
        """@test: Add a subnet by using organization ID and subnet name

        @feature: Organizations

        @assert: subnet is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_add_subnet_3(self, test_data):
        """@test: Add a subnet by using organization name and subnet ID

        @feature: Organizations

        @assert: subnet is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_add_subnet_4(self, test_data):
        """@test: Add a subnet by using organization ID and subnet ID

        @feature: Organizations

        @assert: subnet is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_add_domain_1(self, test_data):
        """@test: Add a domain to an organization

        @feature: Organizations

        @assert: Domain is added to organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        user name is alpha
        user name is numeric
        user name is alpha_numeric
        user name is utf-8
        user name is latin1
        user name is html
    """)
    def test_add_user_1(self, test_data):
        """@test: Create different types of users then add user
        by using the organization ID

        @feature: Organizations

        @assert: User is added to organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        user name is alpha
        user name is numeric
        user name is alpha_numeric
        user name is utf-8
        user name is latin1
        user name is html
    """)
    def test_add_user_2(self, test_data):
        """@test: Create different types of users then add user
        by using the organization name

        @feature: Organizations

        @assert: User is added to organization

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        user name is alpha and an admin
        user name is numeric and an admin
        user name is alpha_numeric and an admin
        user name is utf-8 and an admin
        user name is latin1 and an admin
        user name is html and an admin
    """)
    def test_add_user_3(self, test_data):
        """@test: Create admin users then add user by using the organization name

        @feature: Organizations

        @assert: User is added to organization

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_add_hostgroup_1(self, test_data):
        """@test: Add a hostgroup by using the organization
        name and hostgroup name

        @feature: Organizations

        @assert: hostgroup is added to organization

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_add_hostgroup_2(self, test_data):
        """@test: Add a hostgroup by using the organization
        ID and hostgroup name

        @feature: Organizations

        @assert: hostgroup is added to organization

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_add_hostgroup_3(self, test_data):
        """@test: Add a hostgroup by using the organization
        name and hostgroup ID

        @feature: Organizations

        @assert: hostgroup is added to organization

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_add_hostgroup_4(self, test_data):
        """@test: Add a hostgroup by using the organization
        ID and hostgroup ID

        @feature: Organizations

        @assert: hostgroup is added to organization

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_remove_computeresource_1(self, test_data):
        """@test: Remove computeresource by using the organization
        name and computeresource name

        @feature: Organizations

        @assert: computeresource is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_remove_computeresource_2(self, test_data):
        """@test: Remove computeresource by using the organization
        ID and computeresource name

        @feature: Organizations

        @assert: computeresource is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_remove_computeresource_3(self, test_data):
        """@test: Remove computeresource by using the organization
        name and computeresource ID

        @feature: Organizations

        @assert: computeresource is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_remove_computeresource_4(self, test_data):
        """@test: Remove computeresource by using the organization
        ID and computeresource ID

        @feature: Organizations

        @assert: computeresource is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
        """)
    def test_remove_medium_1(self, test_data):
        """@test: Remove medium by using organization name and medium name

        @feature: Organizations

        @assert: medium is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
        """)
    def test_remove_medium_2(self, test_data):
        """@test: Remove medium by using organization ID and medium name

        @feature: Organizations

        @assert: medium is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
        """)
    def test_remove_medium_3(self, test_data):
        """@test: Remove medium by using organization name and medium ID

        @feature: Organizations

        @assert: medium is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
        """)
    def test_remove_medium_4(self, test_data):
        """@test: Remove medium by using organization ID and medium ID

        @feature: Organizations

        @assert: medium is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_remove_configtemplate_1(self, test_data):
        """@test: Remove config template

        @feature: Organizations

        @assert: configtemplate is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_remove_environment_1(self, test_data):
        """@test: Remove environment by using organization name and
        evironment name

        @feature: Organizations

        @assert: environment is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_remove_environment_2(self, test_data):
        """@test: Remove environment by using organization ID and
        evironment name

        @feature: Organizations

        @assert: environment is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_remove_environment_3(self, test_data):
        """@test: Remove environment by using organization name and
        evironment ID

        @feature: Organizations

        @assert: environment is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_remove_environment_4(self, test_data):
        """@test: Remove environment by using organization ID and
        evironment ID

        @feature: Organizations

        @assert: environment is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_1(self, test_data):
        """@test: Remove smartproxy by using organization name and smartproxy name

        @feature: Organizations

        @assert: smartproxy is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_2(self, test_data):
        """@test: Remove smartproxy by using organization ID and smartproxy name

        @feature: Organizations

        @assert: smartproxy is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_3(self, test_data):
        """@test: Remove smartproxy by using organization name and smartproxy ID

        @feature: Organizations

        @assert: smartproxy is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_4(self, test_data):
        """@test: Remove smartproxy by using organization ID and smartproxy ID

        @feature: Organizations

        @assert: smartproxy is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_add_computeresource_1(self, test_data):
        """@test: Add compute resource using the organization
        name and computeresource name

        @feature: Organizations

        @assert: computeresource is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_add_computeresource_2(self, test_data):
        """@test: Add compute resource using the organization
        ID and computeresource name

        @feature: Organizations

        @assert: computeresource is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_add_computeresource_3(self, test_data):
        """@test: Add compute resource using the organization
        name and computeresource ID

        @feature: Organizations

        @assert: computeresource is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_add_computeresource_4(self, test_data):
        """@test: Add compute resource using the organization
        ID and computeresource ID

        @feature: Organizations

        @assert: computeresource is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
    """)
    def test_add_medium_1(self, test_data):
        """@test: Add medium by using the organization name and medium name

        @feature: Organizations

        @assert: medium is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
    """)
    def test_add_medium_2(self, test_data):
        """@test: Add medium by using the organization ID and medium name

        @feature: Organizations

        @assert: medium is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
    """)
    def test_add_medium_3(self, test_data):
        """@test: Add medium by using the organization name and medium ID

        @feature: Organizations

        @assert: medium is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
    """)
    def test_add_medium_4(self, test_data):
        """@test: Add medium by using the organization ID and medium ID

        @feature: Organizations

        @assert: medium is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_add_configtemplate_1(self, test_data):
        """@test: Add config template by using organization name and
        configtemplate name

        @feature: Organizations

        @assert: configtemplate is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_add_configtemplate_2(self, test_data):
        """@test: Add config template by using organization ID and
        configtemplate name

        @feature: Organizations

        @assert: configtemplate is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_add_configtemplate_3(self, test_data):
        """@test: Add config template by using organization name and
        configtemplate ID

        @feature: Organizations

        @assert: configtemplate is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_add_configtemplate_4(self, test_data):
        """@test: Add config template by using organization ID and
        configtemplate ID

        @feature: Organizations

        @assert: configtemplate is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_add_environment_1(self, test_data):
        """@test: Add environment by using organization name and evironment name

        @feature: Organizations

        @assert: environment is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_add_environment_2(self, test_data):
        """@test: Add environment by using organization ID and evironment name

        @feature: Organizations

        @assert: environment is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_add_environment_3(self, test_data):
        """@test: Add environment by using organization name and evironment ID

        @feature: Organizations

        @assert: environment is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_add_environment_4(self, test_data):
        """@test: Add environment by using organization ID and evironment ID

        @feature: Organizations

        @assert: environment is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_remove_subnet_1(self, test_data):
        """@test: Remove subnet by using organization name and subnet name

        @feature: Organizations

        @assert: subnet is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_remove_subnet_2(self, test_data):
        """@test: Remove subnet by using organization ID and subnet name

        @feature: Organizations

        @assert: subnet is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_remove_subnet_3(self, test_data):
        """@test: Remove subnet by using organization name and subnet ID

        @feature: Organizations

        @assert: subnet is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_remove_subnet_4(self, test_data):
        """@test: Remove subnet by using organization ID and subnet ID

        @feature: Organizations

        @assert: subnet is added then removed

        @status: manual

        """

        pass
