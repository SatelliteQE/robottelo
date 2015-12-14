# -*- encoding: utf-8 -*-
# pylint: disable=no-self-use
"""Test class for Organization CLI"""
import random

from fauxfactory import gen_string
from random import randint
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    make_domain, make_hostgroup, make_lifecycle_environment,
    make_medium, make_org, make_proxy, make_subnet, make_template, make_user,
    make_compute_resource,)
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.org import Org
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
)
from robottelo.test import CLITestCase


def valid_names():
    """Random data for positive creation

    Note: The maximum allowed length of org name is 242 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)
    """
    return (
        {'name': gen_string("latin1")},
        {'name': gen_string("utf8")},
        {'name': gen_string("alpha", randint(1, 242))},
        {'name': gen_string("alphanumeric", randint(1, 242))},
        {'name': gen_string("numeric", randint(1, 242))},
        {'name': gen_string("html")},
    )


def valid_name_label_combo():
    """Random simpler data for positive creation

    Use this when name and label must match. Labels cannot contain the same
    data type as names, so this is a bit limited compared to other tests.
    Label cannot contain characters other than ascii alpha numerals, '_', '-'.
    """
    return (
        {'name': gen_string("alpha")},
        {'name': gen_string("alphanumeric")},
        {'name': gen_string("numeric")},
        {'name': '{0}-{1}'.format(gen_string("alpha", 5),
                                  gen_string("alpha", 5))},
        {'name': '{0}_{1}'.format(gen_string("alpha", 5),
                                  gen_string("alpha", 5))},
    )


def valid_names_simple():
    """Random data for alpha, numeric and alphanumeric

    Note: The maximum allowed length of org name is 242 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)
    """
    return(
        gen_string('alpha', randint(1, 242)),
        gen_string('numeric', randint(1, 242)),
        gen_string('alphanumeric', randint(1, 242))
    )


def valid_names_simple_all():
    """Random data for alpha, numeric and alphanumeric

    Note: The maximum allowed length of org name is 242 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)
    """
    return(
        gen_string('alpha', randint(1, 242)),
        gen_string('alphanumeric', randint(1, 242)),
        gen_string('numeric', randint(1, 242)),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        )


def valid_name_label():
    """Random data for Label tests

    Label cannot contain characters other than ascii alpha numerals, '_', '-'.

    Note: The maximum allowed length of org name is 242 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)
    """
    return (
        {'name': gen_string("latin1"),
         'label': gen_string("alpha")},
        {'name': gen_string("utf8"),
         'label': gen_string("alpha")},
        {'name': gen_string("alpha", randint(1, 242)),
         'label': gen_string("alpha")},
        {'name': gen_string("alphanumeric", randint(1, 242)),
         'label': gen_string("alpha")},
        {'name': gen_string("numeric", randint(1, 242)),
         'label': gen_string("alpha")},
        {'name': gen_string("html"),
         'label': gen_string("alpha")},
    )


def valid_name_desc():
    """Random data for Descriptions tests

    Note: The maximum allowed length of org name is 242 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)
    """
    return (
        {'name': gen_string("latin1"),
         'description': gen_string("latin1")},
        {'name': gen_string("utf8"),
         'description': gen_string("utf8")},
        {'name': gen_string("alpha", randint(1, 242)),
         'description': gen_string("alpha")},
        {'name': gen_string("alphanumeric", randint(1, 242)),
         'description': gen_string("alphanumeric")},
        {'name': gen_string("numeric", randint(1, 242)),
         'description': gen_string("numeric")},
        {'name': gen_string("html"),
         'description': gen_string("html")},
    )


def valid_name_desc_label():
    """Random data for Labels and Description

    Note: The maximum allowed length of org name is 242 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)
    """
    return (
        {'name': gen_string("alpha", randint(1, 242)),
         'description': gen_string("alpha"),
         'label': gen_string("alpha")},
        {'name': gen_string("alphanumeric", randint(1, 242)),
         'description': gen_string("alphanumeric"),
         'label': gen_string("alpha")},
        {'name': gen_string("numeric", randint(1, 242)),
         'description': gen_string("numeric"),
         'label': gen_string("alpha")},
        {'name': gen_string("html"),
         'description': gen_string("numeric"),
         'label': gen_string("alpha")},
    )


def invalid_name_label():
    """Random invalid name and label data"""
    return(
        {'label': gen_string('alpha'),
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
         'name': gen_string('html', 300)},
    )


def positive_desc_data():
    """Random valid data for description"""
    return(
        {'description': gen_string("latin1")},
        {'description': gen_string("utf8")},
        {'description': gen_string("alpha")},
        {'description': gen_string("alphanumeric")},
        {'description': gen_string("numeric")},
        {'description': gen_string("html")},
    )


def invalid_name_data():
    """Random invalid name data"""
    return(
        {'name': ' '},
        {'name': gen_string('alpha', 300)},
        {'name': gen_string('numeric', 300)},
        {'name': gen_string('alphanumeric', 300)},
        {'name': gen_string('utf8', 300)},
        {'name': gen_string('latin1', 300)},
        {'name': gen_string('html', 300)}
    )


class OrganizationTestCase(CLITestCase):
    """Tests for Organizations via Hammer CLI"""

    # Tests for issues

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    @tier1
    def test_verify_bugzilla_1078866(self):
        """@Test: hammer organization <info,list> --help types information
        doubled

        @Feature: Organization

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

    @tier1
    def test_positive_create_with_name(self):
        """@test: Create organization with valid name only

        @feature: Organization

        @assert: organization is created, label is auto-generated
        """
        for test_data in valid_names():
            with self.subTest(test_data):
                org = make_org(test_data)
                self.assertEqual(org['name'], test_data['name'])

    @tier1
    def test_positive_create_with_matching_name_label(self):
        """@test: Create organization with valid matching name and label only

        @feature: Organization

        @assert: organization is created, label matches name
        """
        for test_data in valid_name_label_combo():
            with self.subTest(test_data):
                test_data['label'] = test_data['name']
                org = make_org(test_data)
                self.assertEqual(org['name'], org['label'])

    @skip_if_bug_open('bugzilla', 1142821)
    @tier1
    def test_positive_create_with_unmatched_name_label(self):
        """@test: Create organization with valid unmatching name and label only

        @feature: Organization

        @assert: organization is created, label does not match name

        @bz: 1142821
        """
        for test_data in valid_name_label():
            with self.subTest(test_data):
                org = make_org(test_data)
                self.assertNotEqual(org['name'], org['label'])
                self.assertEqual(org['name'], test_data['name'])
                self.assertEqual(org['label'], test_data['label'])

    @tier1
    def test_positive_create_with_name_description(self):
        """@test: Create organization with valid name and description only

        @feature: Organization

        @assert: organization is created, label is auto-generated
        """
        for test_data in valid_name_desc():
            with self.subTest(test_data):
                org = make_org(test_data)
                self.assertNotEqual(org['name'], org['description'])
                self.assertEqual(org['name'], test_data['name'])
                self.assertEqual(org['description'], test_data['description'])

    @skip_if_bug_open('bugzilla', 1142821)
    @tier1
    def test_positive_create_with_name_label_description(self):
        """@test: Create organization with valid name, label and description

        @feature: Organization

        @assert: organization is created

        @bz: 1142821
        """
        for test_data in valid_name_desc():
            with self.subTest(test_data):
                test_data['label'] = gen_string('alpha')
                org = make_org(test_data)
                self.assertEqual(org['name'], test_data['name'])
                self.assertEqual(org['description'], test_data['description'])
                self.assertEqual(org['label'], test_data['label'])

    @tier1
    @stubbed('Needs to be improved')
    def test_positive_list(self):
        """@Test: Check if Org can be listed

        @Feature: Organization

        @Assert: Org is listed
        """
        Org.list()

    @run_only_on('sat')
    @tier2
    def test_positive_add_subnet_by_name(self):
        """@Test: Add a subnet by its name

        @Feature: Organizatiob

        @Assert: Subnet is added to the org
        """
        for name in (gen_string('alpha'), gen_string('numeric'),
                     gen_string('alphanumeric'), gen_string('utf8'),
                     gen_string('latin1')):
            with self.subTest(name):
                org = make_org()
                new_subnet = make_subnet({'name': name})
                Org.add_subnet({
                    'name': org['name'],
                    'subnet': new_subnet['name'],
                })
                org = Org.info({'id': org['id']})
                self.assertIn(name, org['subnets'][0])

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_positive_add_subnet_by_id(self):
        """@test: Add a subnet by its ID

        @feature: Organization

        @assert: Subnet is added to the org
        """
        for name in (gen_string('alpha'), gen_string('numeric'),
                     gen_string('alphanumeric'), gen_string('utf8'),
                     gen_string('latin1')):
            with self.subTest(name):
                org = make_org()
                new_subnet = make_subnet({'name': name})
                Org.add_subnet({
                    'name': org['name'],
                    'subnet-id': new_subnet['id'],
                })
                org = Org.info({'id': org['id']})
                self.assertIn(name, org['subnets'][0])

    @run_only_on('sat')
    @tier2
    def test_positive_remove_subnet_by_name(self):
        """@Test: Add a subnet and then remove it by its name

        @Feature: Organization

        @Assert: Subnet is removed from the org
        """
        org = make_org()
        subnet = make_subnet()
        Org.add_subnet({
            'name': org['name'],
            'subnet': subnet['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['subnets']), 1)
        self.assertIn(subnet['name'], org['subnets'][0])
        Org.remove_subnet({
            'name': org['name'],
            'subnet': subnet['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['subnets']), 0)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_subnet_by_id(self):
        """@Test: Remove a subnet and then remove it by its ID

        @Feature: Organization

        @Assert: Subnet is removed from the org
        """
        org = make_org()
        subnet = make_subnet()
        Org.add_subnet({
            'name': org['name'],
            'subnet': subnet['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['subnets']), 1)
        self.assertIn(subnet['name'], org['subnets'][0])
        Org.remove_subnet({
            'name': org['name'],
            'subnet-id': subnet['id'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['subnets']), 0)

    @tier2
    def test_positive_add_user_by_name(self):
        """@Test: Add an user by its name

        @Feature: Organization

        @Assert: User is added to the org
        """
        org = make_org()
        user = make_user()
        Org.add_user({
            'name': org['name'],
            'user': user['login'],
        })

    @tier2
    def test_positive_add_user_by_id(self):
        """@Test: Add an user by its ID

        @Feature: Organization

        @Assert: User is added to the org
        """
        org = make_org()
        user = make_user()
        Org.add_user({
            'name': org['name'],
            'user-id': user['id'],
        })

    @tier2
    def test_positive_remove_user_by_id(self):
        """@Test: Check if a User can be removed from an Org

        @Feature: Organization

        @Assert: User is removed from the org
        """
        org = make_org()
        user = make_user()
        Org.add_user({
            'name': org['name'],
            'user-id': user['id'],
        })

        Org.remove_user({
            'name': org['name'],
            'user-id': user['id'],
        })

    @tier2
    @stubbed()
    def test_positive_remove_user_by_name(self):
        """@test: Create different types of users then add/remove user
        by using the organization name

        @feature: Organization

        @assert: The user is added then removed from the organization

        @status: manual
        """

    @tier2
    @stubbed()
    def test_positive_remove_admin_user_by_name(self):
        """@test: Create admin users then add user and remove it
        by using the organization name

        @feature: Organization

        @assert: The user is added then removed from the organization

        @status: manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_add_hostgroup_by_name(self):
        """@Test: Add a hostgroup by its name

        @Feature: Organization

        @Assert: Hostgroup is added to the org
        """
        org = make_org()
        hostgroup = make_hostgroup()
        Org.add_hostgroup({
            'hostgroup': hostgroup['name'],
            'name': org['name'],
        })

    @run_only_on('sat')
    @tier2
    def test_positive_remove_hostgroup_by_name(self):
        """@Test: Add a hostgroup and then remove it by its name

        @Feature: Organization

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
    @tier2
    @stubbed()
    def test_positive_remove_hostgroup_by_id(self):
        """@test: Add a hostgroup and remove it by its ID

        @feature: Organization

        @assert: hostgroup is added to organization then removed

        @status: manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_add_compresource_by_name(self):
        """@Test: Add a compute resource by its name

        @Feature: Organization

        @Assert: Compute Resource is added to the org
        """
        org = make_org()
        compute_res = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" % settings.server.hostname
        })
        Org.add_compute_resource({
            'compute-resource': compute_res['name'],
            'name': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(org['compute-resources'][0], compute_res['name'])

    @tier2
    def test_positive_add_compresource_by_id(self):
        """@Test: Add a compute resource by its ID

        @Feature: Organization

        @Assert: Compute Resource is added to the org
        """
        compute_res = make_compute_resource()
        org = make_org({'compute-resource-ids': compute_res['id']})
        self.assertEqual(len(org['compute-resources']), 1)
        self.assertEqual(org['compute-resources'][0], compute_res['name'])

    @tier2
    def test_positive_add_compresources_by_id(self):
        """@Test: Add multiple compute resources by their IDs
        resources

        @Feature: Organization

        @Assert: All compute resources are added to the org
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
    def test_positive_remove_compresource_by_id(self):
        """@Test: Add a compute resource and then remove it by its ID

        @Feature: Organization

        @Assert: Compute resource is removed from the org

        @status: manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_add_medium_by_name(self):
        """@Test: Add a medium by its name

        @Feature: Organization

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
    @tier2
    def test_positive_remove_medium_by_id(self):
        """@Test: Add a compute resource and then remove it by its ID

        @Feature: Organization

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
    @tier2
    def test_positive_add_template_by_name(self):
        """@Test: Add a provisioning template by its name

        @Feature: Organization

        @Assert: Template is added to the org
        """
        for name in valid_names_simple_all():
            with self.subTest(name):
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
                    org['templates']
                )

    @tier2
    def test_positive_add_template_by_id(self):
        """@Test: Add a provisioning template by its ID

        @Feature: Organization

        @Assert: Template is added to the org
        """
        conf_templ = make_template()
        org = make_org({'config-template-ids': conf_templ['id']})
        self.assertIn(
            u'{0} ({1})'.format(conf_templ['name'], conf_templ['type']),
            org['templates']
        )

    @tier2
    def test_positive_add_templates_by_id(self):
        """@Test: Add multiple provisioning templates by their IDs

        @Feature: Organization

        @Assert: All provisioning templates are added to the org
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
    @tier2
    def test_positive_remove_template_by_name(self):
        """@Test: Add a provisioning template and then remove it by its name

        @Feature: Organization

        @Assert: Template is removed from the org
        """
        for name in valid_names_simple_all():
            with self.subTest(name):
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
    @tier2
    def test_positive_add_domain_by_name(self):
        """@test: Add a domain by its name

        @Feature: Organization

        @assert: Domain is added to organization

        @status: manual
        """
        org = make_org()
        domain = make_domain()
        Org.add_domain({
            'domain': domain['name'],
            'name': org['name'],
        })
        result = Org.info({'id': org['id']})
        self.assertEqual(len(result['domains']), 1)
        self.assertIn(domain['name'], result['domains'])

    @run_only_on('sat')
    @tier2
    def test_positive_add_domain_by_id(self):
        """@test: Add a domain by its ID

        @feature: Organization

        @assert: Domain is added to organization

        @status: manual
        """
        org = make_org()
        domain = make_domain()
        Org.add_domain({
            'domain-id': domain['id'],
            'name': org['name'],
        })
        result = Org.info({'id': org['id']})
        self.assertEqual(len(result['domains']), 1)
        self.assertIn(domain['name'], result['domains'])

    @run_only_on('sat')
    @tier2
    def test_positive_remove_domain_by_name(self):
        """@Test: Add a domain and then remove it by its name

        @Feature: Organization

        @Assert: Domain is removed from the org
        """
        org = make_org()
        domain = make_domain()
        Org.add_domain({
            'domain': domain['name'],
            'name': org['name'],
        })
        result = Org.info({'id': org['id']})
        self.assertEqual(len(result['domains']), 1)
        self.assertIn(domain['name'], result['domains'])
        Org.remove_domain({
            'domain': domain['name'],
            'name': org['name'],
        })
        result = Org.info({'id': org['id']})
        self.assertEqual(len(result['domains']), 0)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_domain_by_id(self):
        """@test: Add a domain and then remove it by its ID

        @feature: Organization

        @assert: Domain is removed from the organization
        """
        org = make_org()
        domain = make_domain()
        Org.add_domain({
            'domain-id': domain['id'],
            'name': org['name'],
        })
        result = Org.info({'id': org['id']})
        self.assertEqual(len(result['domains']), 1)
        self.assertIn(domain['name'], result['domains'])
        Org.remove_domain({
            'domain-id': domain['id'],
            'id': org['id'],
        })
        result = Org.info({'id': org['id']})
        self.assertEqual(len(result['domains']), 0)

    @run_only_on('sat')
    @tier2
    def test_positive_add_lce(self):
        """@Test: Add a lifecycle environment

        @Feature: Organization

        @Assert: Lifecycle environment is added to the org
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
    @tier2
    def test_positive_remove_lce(self):
        """@Test: Add a lifecycle environment and then remove it

        @Feature: Organization

        @Assert: Lifecycle environment is removed from the org
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
    @tier2
    @stubbed("Needs to be re-worked!")
    def test_positive_add_capsule_by_name(self):
        """@Test: Add a capsule by its name

        @Feature: Organization

        @Assert: Capsule is added to the org
        """
        org = make_org()
        proxy = make_proxy()
        Org.add_smart_proxy({
            'name': org['name'],
            'smart-proxy': proxy['name'],
        })

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_positive_add_capsule_by_id(self):
        """@test: Add a capsule by its ID

        @feature: Organization

        @assert: Capsule is added to the org

        @status: manual
        """

    @run_only_on('sat')
    @stubbed("Needs to be re-worked!")
    def test_positive_remove_capsule_by_name(self):
        """@Test: Add a capsule and then remove it by its name

        @Feature: Organization

        @Assert: Capsule is removed from the org
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

    @tier1
    def test_negative_create_name_long(self):
        """@test: Create organization with valid label and description, name is
        too long

        @feature: Organization

        @assert: organization is not created
        """
        for test_data in invalid_name_label():
            with self.subTest(test_data):
                with self.assertRaises(CLIReturnCodeError):
                    Org.create({
                        'description': test_data['label'],
                        'label': test_data['label'],
                        'name': test_data['name'],
                    })

    @tier1
    def test_negative_create_name_blank(self):
        """@test: Create organization with valid label and description, name is
        blank

        @feature: Organization

        @assert: organization is not created
        """
        for test_data in valid_names_simple():
            with self.subTest(test_data):
                with self.assertRaises(CLIReturnCodeError):
                    Org.create({
                        'description': test_data,
                        'label': test_data,
                        'name': '',
                    })

    @tier1
    def test_negative_create_name_spaces(self):
        """@test: Create organization with valid label and description, name is
        whitespace

        @feature: Organization

        @assert: organization is not created
        """
        for test_data in valid_names_simple():
            with self.subTest(test_data):
                with self.assertRaises(CLIReturnCodeError):
                    Org.create({
                        'description': test_data,
                        'label': test_data,
                        'name': ' \t',
                    })

    @tier1
    def test_negative_create_same_name(self):
        """@test: Create organization with valid values, then create a new one
        with same values.

        @feature: Organization

        @assert: organization is not created
        """
        for test_data in valid_names_simple():
            with self.subTest(test_data):
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

    @tier1
    def test_positive_delete_by_id(self):
        """@test: Create organization with valid values then delete it
        by ID

        @feature: Organization

        @assert: organization is deleted
        """
        for test_data in valid_name_desc_label():
            with self.subTest(test_data):
                org = make_org(test_data)
                Org.delete({'id': org['id']})
                # Can we find the object?
                with self.assertRaises(CLIReturnCodeError):
                    Org.info({'id': org['id']})

    @tier1
    def test_positive_delete_by_label(self):
        """@test: Create organization with valid values then delete it
        by label

        @feature: Organization

        @assert: organization is deleted
        """
        for test_data in valid_name_desc_label():
            with self.subTest(test_data):
                org = make_org(test_data)
                Org.delete({'label': org['label']})
                # Can we find the object?
                with self.assertRaises(CLIReturnCodeError):
                    Org.info({'id': org['id']})

    @tier1
    def test_positive_delete_by_name(self):
        """@test: Create organization with valid values then delete it
        by name

        @feature: Organization

        @assert: organization is deleted
        """
        for test_data in valid_name_desc_label():
            with self.subTest(test_data):
                org = make_org(test_data)
                Org.delete({'name': org['name']})
                # Can we find the object?
                with self.assertRaises(CLIReturnCodeError):
                    Org.info({'id': org['id']})

    @tier1
    def test_positive_update_name(self):
        """@test: Create organization with valid values then update its name

        @feature: Organization

        @assert: organization name is updated
        """
        for test_data in valid_names():
            with self.subTest(test_data):
                org = make_org()
                # Update the org name
                Org.update({
                    'id': org['id'],
                    'new-name': test_data['name'],
                })
                # Fetch the org again
                org = Org.info({'id': org['id']})
                self.assertEqual(org['name'], test_data['name'])

    @tier1
    def test_positive_update_description(self):
        """@test: Create organization with valid values then update its
        description

        @feature: Organization

        @assert: organization description is updated
        """
        for test_data in positive_desc_data():
            with self.subTest(test_data):
                org = make_org()
                # Update the org name
                Org.update({
                    'description': test_data['description'],
                    'id': org['id'],
                })
                # Fetch the org again
                org = Org.info({'id': org['id']})
                self.assertEqual(org['description'], test_data['description'])

    @tier1
    def test_positive_update_name_description(self):
        """@test: Create organization with valid values then update its name
        and description

        @feature: Organization

        @assert: organization name and description are updated
        """
        for test_data in valid_name_desc():
            with self.subTest(test_data):
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

    @tier1
    def test_negative_update_name(self):
        """@test: Create organization then fail to update its name

        @feature: Organization

        @assert: organization name is not updated
        """
        for test_data in invalid_name_data():
            with self.subTest(test_data):
                org = make_org()
                # Update the org name
                with self.assertRaises(CLIReturnCodeError):
                    Org.update({
                        'id': org['id'],
                        'new-name': test_data['name'],
                    })

    # This test also covers the redmine bug 4443
    @tier1
    def test_positive_search_by_name(self):
        """@test: Can search for an organization by name

        @feature: Organization

        @assert: organization is created and can be searched by name
        """
        for test_data in valid_names():
            with self.subTest(test_data):
                org = make_org(test_data)
                # Can we find the new object?
                result = Org.exists(search=('name', org['name']))
                self.assertEqual(org['name'], result['name'])

    @tier1
    def test_positive_search_by_label(self):
        """@test: Can search for an organization by name

        @feature: Organization

        @assert: organization is created and can be searched by label
        """
        for test_data in valid_names():
            with self.subTest(test_data):
                org = make_org(test_data)
                # Can we find the new object?
                result = Org.exists(search=('label', org['label']))
                self.assertEqual(org['name'], result['name'])

    @tier1
    def test_positive_info_by_label(self):
        """@Test: Get org information by its label

        @Feature: Organization

        @Assert: Organization is created and info can be obtained by its label
        graciously
        """
        org = make_org()
        result = Org.info({'label': org['label']})
        self.assertEqual(org['id'], result['id'])

    @tier1
    def test_positive_info_by_name(self):
        """@Test: Get org information by its name

        @Feature: Organization

        @Assert: Organization is created and info can be obtained by its name
        graciously
        """
        org = make_org()
        result = Org.info({'name': org['name']})
        self.assertEqual(org['id'], result['id'])
