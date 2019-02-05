# -*- encoding: utf-8 -*-
# pylint: disable=no-self-use
"""Test class for Organization CLI

:Requirement: Organization

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random
import unicodedata

from fauxfactory import gen_string
from itertools import cycle
from robottelo.cleanup import capsule_cleanup, org_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    make_compute_resource,
    make_domain,
    make_hostgroup,
    make_lifecycle_environment,
    make_location,
    make_medium,
    make_org,
    make_proxy,
    make_subnet,
    make_template,
    make_user,
)
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.org import Org
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.datafactory import (
    filtered_datapoint,
    invalid_values_list,
    valid_data_list,
    valid_org_names_list,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import CLITestCase


@filtered_datapoint
def valid_labels_list():
    """Random simpler data for positive creation

    Use this when name and label must match. Labels cannot contain the same
    data type as names, so this is a bit limited compared to other tests.
    Label cannot contain characters other than ascii alpha numerals, '_', '-'.
    """
    return [
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        '{0}-{1}'.format(gen_string('alpha', 5), gen_string('alpha', 5)),
        '{0}_{1}'.format(gen_string('alpha', 5), gen_string('alpha', 5)),
    ]


class OrganizationTestCase(CLITestCase):
    """Tests for Organizations via Hammer CLI"""

    def _make_proxy(self, options=None):
        """Create a Proxy and register the cleanup function"""
        proxy = make_proxy(options=options)
        # Add capsule to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])
        return proxy

    # Tests for issues

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    @tier1
    def test_verify_bugzilla_1078866(self):
        """hammer organization <info,list> --help types information
        doubled

        :id: 7938bcc4-7107-40b0-bb88-6288ebec0dcd

        :bz: 1078866, 1647323

        :expectedresults: no duplicated lines in usage message

        :CaseImportance: Critical
        """
        # org list --help:
        result = Org.list({'help': True}, output_format=None)
        # get list of lines and check they all are unique
        lines = [line for line in result if line != '']
        self.assertEqual(len(set(lines)), len(lines))

        # org info --help:info returns more lines (obviously), ignore exception
        result = Org.info({'help': True}, output_format=None)

        # get list of lines and check they all are unique
        lines = [line for line in result['options']]
        self.assertEqual(len(set(lines)), len(lines))

    @tier1
    def test_positive_create_with_name(self):
        """Create organization with valid name only

        :id: 35840da7-668e-4f78-990a-738aa688d586

        :expectedresults: organization is created and has appropriate name

        :CaseImportance: Critical
        """
        for name in valid_org_names_list():
            with self.subTest(name):
                org = make_org({'name': name})
                self.assertEqual(org['name'], name)

    @tier1
    def test_positive_create_with_matching_name_label(self):
        """Create organization with valid matching name and label only

        :id: aea551de-145b-4894-b4fb-65878ff1f101

        :expectedresults: organization is created, label matches name

        :CaseImportance: Critical
        """
        for test_data in valid_labels_list():
            with self.subTest(test_data):
                org = make_org({
                    'label': test_data,
                    'name': test_data,
                })
                self.assertEqual(org['name'], org['label'])

    @tier1
    def test_positive_create_with_unmatched_name_label(self):
        """Create organization with valid unmatching name and label only

        :id: a4730b09-1bd7-4b00-a7ee-76080a916ea8

        :expectedresults: organization is created, label does not match name

        :CaseImportance: Critical
        """
        for name in valid_org_names_list():
            with self.subTest(name):
                label = gen_string('alpha')
                org = make_org({
                    'label': label,
                    'name': name,
                })
                self.assertNotEqual(org['name'], org['label'])
                self.assertEqual(org['name'], name)
                self.assertEqual(org['label'], label)

    @tier1
    def test_positive_create_with_name_description(self):
        """Create organization with valid name and description only

        :id: b28c95ba-918e-47fe-8681-61e05b8fe2ea

        :expectedresults: organization is created

        :CaseImportance: Critical
        """
        for name, desc in zip(valid_org_names_list(), valid_data_list()):
            with self.subTest(name + desc):
                org = make_org({
                    'description': desc,
                    'name': name,
                })
                self.assertEqual(org['name'], name)
                self.assertEqual(org['description'], desc)

    @tier1
    @upgrade
    def test_positive_create_with_name_label_description(self):
        """Create organization with valid name, label and description

        :id: 9a1f70f6-fb5f-4b23-9f7e-b0973fbbba30

        :expectedresults: organization is created

        :CaseImportance: Critical
        """
        for description in valid_data_list():
            with self.subTest(description):
                label = gen_string('alpha')
                name = gen_string('alpha')
                org = make_org({
                    'description': description,
                    'label': label,
                    'name': name,
                })
                self.assertEqual(org['description'], description)
                self.assertEqual(org['label'], label)
                self.assertEqual(org['name'], name)

    @tier1
    def test_positive_list(self):
        """Check if Org can be listed

        :id: bdd26bb3-e3d2-4a5c-8be7-fb12c1114ccc

        :expectedresults: Org is listed

        :CaseImportance: Critical
        """
        org = make_org()
        result_list = Org.list({'search': 'name=%s' % org['name']})
        self.assertTrue(len(result_list) > 0)
        self.assertEqual(result_list[0]['name'], org['name'])

    @tier1
    def test_positive_search_scoped(self):
        """Check if scoped search work properly for organization entity

        :id: d66ebe1d-aba1-4042-87e4-7de8ea0f8fc8

        :customerscenario: true

        :expectedresults: Necessary organization is listed

        :BZ: 1259374

        :CaseImportance: High
        """
        label = gen_string('alpha')
        desc = gen_string('alpha', 15)
        org = make_org({'label': label, 'description': desc})
        for query in [
            'label = {}'.format(label),
            'description ~ {}'.format(desc[:-5]),
            'name ^ "{}"'.format(org['name']),
        ]:
            result_list = Org.list({'search': query})
            self.assertTrue(len(result_list), 1)
            self.assertEqual(result_list[0]['name'], org['name'])

    @tier2
    @upgrade
    def test_positive_add_and_remove_subnets(self):
        """add and remove a subnet from organization

        :id: adb5310b-76c5-4aca-8220-fdf0fe605cb0

        :bz:
            1. Add and remove subnet by name
            2. Add and remove subnet by id

        :expectedresults: Subnets are handled as expected

        :bz: 1395229

        :CaseLevel: Integration
        """
        org = make_org()
        subnet_a = make_subnet()
        subnet_b = make_subnet()
        Org.add_subnet({
            'name': org['name'],
            'subnet': subnet_a['name'],
        })
        Org.add_subnet({
            'name': org['name'],
            'subnet-id': subnet_b['id'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertEqual(len(org_info['subnets']), 2,
                         "Failed to add subnets")
        Org.remove_subnet({
            'name': org['name'],
            'subnet': subnet_a['name'],
        })
        Org.remove_subnet({
            'name': org['name'],
            'subnet-id': subnet_b['id'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertEqual(len(org_info['subnets']), 0,
                         "Failed to remove subnets")

    @tier2
    def test_positive_add_and_remove_users(self):
        """Add and remove (admi) user to organization

        :id: c35b2e88-a65f-4eea-ba55-89cef59f30be

        :expectedresults: Users are added and removed from the org

        :steps:
            1. create and delete user by name
            2. create and delete user by id
            3. create and delete admin user by name
            4. create and delete admin user by id

        :bz: 1395229

        :CaseLevel: Integration
        """
        org = make_org()
        user = make_user()
        admin_user = make_user({'admin': '1'})
        self.assertEqual(admin_user['admin'], 'yes')

        # add and remove user and admin user by name
        Org.add_user({
            'name': org['name'],
            'user': user['login'],
        })
        Org.add_user({
            'name': org['name'],
            'user': admin_user['login'],
        })
        org_info = Org.info({'name': org['name']})
        self.assertIn(user['login'], org_info['users'],
                      "Failed to add user by name")
        self.assertIn(admin_user['login'], org_info['users'],
                      "Failed to add admin user by name")
        if not bz_bug_is_open(1395229):
            Org.remove_user({
                'name': org['name'],
                'user': user['login'],
            })
            Org.remove_user({
                'name': org['name'],
                'user': admin_user['login'],
            })
            org_info = Org.info({'name': org['name']})
            self.assertNotIn(user['login'], org_info['users'],
                             "Failed to remove user by name")
            self.assertNotIn(admin_user['login'], org_info['users'],
                             "Failed to remove admin user by name")

        # add and remove user and admin user by id
        Org.add_user({
            'id': org['id'],
            'user-id': user['id'],
        })
        Org.add_user({
            'id': org['id'],
            'user-id': admin_user['id'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertIn(user['login'], org_info['users'],
                      "Failed to add user by id")
        self.assertIn(admin_user['login'], org_info['users'],
                      "Failed to add admin user by id")
        if not bz_bug_is_open(1395229):
            Org.remove_user({
                'id': org['id'],
                'user-id': user['id'],
            })
            Org.remove_user({
                'id': org['id'],
                'user-id': admin_user['id'],
            })
            org_info = Org.info({'id': org['id']})
            self.assertNotIn(user['login'], org_info['users'],
                             "Failed to remove user by id")
            self.assertNotIn(admin_user['login'], org_info['users'],
                             "Failed to remove admin user by id")

    @tier2
    def test_positive_add_and_remove_hostgroups(self):
        """add and remove a hostgroup from an organization

        :id: 34e2c7c8-dc20-4709-a5a9-83c0dee9d84d

        :expectedresults: Hostgroups are handled as expected

        :bz: 1395229

        :steps:
            1. add and remove hostgroup by name
            2. add and remove hostgroup by id

        :CaseLevel: Integration
        """
        org = make_org()
        hostgroup_a = make_hostgroup()
        hostgroup_b = make_hostgroup()
        Org.add_hostgroup({
            'hostgroup-id': hostgroup_a['id'],
            'id': org['id'],
        })
        Org.add_hostgroup({
            'hostgroup': hostgroup_b['name'],
            'name': org['name'],
        })
        org_info = Org.info({'name': org['name']})
        self.assertIn(hostgroup_a['name'], org_info['hostgroups'],
                      "Failed to add hostgroup by id")
        self.assertIn(hostgroup_b['name'], org_info['hostgroups'],
                      "Failed to add hostgroup by name")
        Org.remove_hostgroup({
            'hostgroup-id': hostgroup_b['id'],
            'id': org['id'],
        })
        Org.remove_hostgroup({
            'hostgroup': hostgroup_a['name'],
            'name': org['name'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertNotIn(hostgroup_a['name'], org_info['hostgroups'],
                         "Failed to remove hostgroup by name")
        self.assertNotIn(hostgroup_b['name'], org_info['hostgroups'],
                         "Failed to remove hostgroup by id")

    @skip_if_not_set('compute_resources')
    @skip_if_bug_open('bugzilla', 1395229)
    @tier2
    @upgrade
    def test_positive_add_and_remove_compresources(self):
        """amd and remove a compute resource from organization

        :id: 415c14ab-f879-4ed8-9ba7-8af4ada2e277

        :expectedresults: Compute resource are handled as expected

        :bz: 1395229

        :steps:
            1. Add and remove compute resource by id
            2. Add and remove compute resource by name

        :CaseLevel: Integration
        """
        org = make_org()
        compute_res_a = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': u'qemu+ssh://root@{0}/system'.format(
                settings.compute_resources.libvirt_hostname
            )
        })
        compute_res_b = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': u'qemu+ssh://root@{0}/system'.format(
                settings.compute_resources.libvirt_hostname
            )
        })
        Org.add_compute_resource({
            'compute-resource-id': compute_res_a['id'],
            'id': org['id'],
        })
        Org.add_compute_resource({
            'compute-resource': compute_res_b['name'],
            'name': org['name'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertEqual(len(org_info['compute-resources']), 2,
                         "Failed to add compute resources")
        Org.remove_compute_resource({
            'compute-resource-id': compute_res_a['id'],
            'id': org['id'],
        })
        Org.remove_compute_resource({
            'compute-resource': compute_res_b['name'],
            'name': org['name'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertNotIn(
            compute_res_a['name'],
            org_info['compute-resources'],
            "Failed to remove cr by id"
        )
        self.assertNotIn(
            compute_res_b['name'],
            org_info['compute-resources'],
            "Failed to remove cr by name"
        )

    @run_only_on('sat')
    @tier2
    def test_positive_add_and_remove_media(self):
        """Add and remove medium to organization

        :id: c2943a81-c8f7-44c4-926b-388055d7c290

        :expectedresults: Media are handled as expected

        :bz: 1395229

        :steps:
            1. add and remove medium by id
            2. add and remove medium by name

        :CaseLevel: Integration
        """
        org = make_org()
        medium_a = make_medium()
        medium_b = make_medium()
        Org.add_medium({
            'id': org['id'],
            'medium-id': medium_a['id'],
        })
        Org.add_medium({
            'name': org['name'],
            'medium': medium_b['name'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertIn(medium_a['name'], org_info['installation-media'],
                      "Failed to add medium by id")
        self.assertIn(medium_b['name'], org_info['installation-media'],
                      "Failed to add medium by name")
        Org.remove_medium({
            'name': org['name'],
            'medium': medium_a['name'],
        })
        Org.remove_medium({
            'id': org['id'],
            'medium-id': medium_b['id'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertNotIn(medium_a['name'], org_info['installation-media'],
                         "Failed to remove medium by name")
        self.assertNotIn(medium_b['name'], org_info['installation-media'],
                         "Failed to remove medium by id")

    @run_only_on('sat')
    @tier2
    def test_positive_add_and_remove_templates(self):
        """Add and remove provisioning templates to organization

        :id: bd46a192-488f-4da0-bf47-1f370ae5f55c

        :expectedresults: Templates are handled as expected

        :steps:
            1. Add and remove template by id
            2. Add and remove template by name

        :CaseLevel: Integration
        """
        org = make_org()

        # create and remove templates by name
        for name in valid_data_list():
            with self.subTest(name):
                org = make_org()
                template = make_template({
                    'content': gen_string('alpha'),
                    'name': name,
                })
                # Add config-template
                Org.add_config_template({
                    'name': org['name'],
                    'config-template': template['name'],
                })
                org_info = Org.info({'name': org['name']})
                self.assertIn(
                    u'{0} ({1})'. format(template['name'], template['type']),
                    org_info['templates'],
                    "Failed to add template by name"
                )
                # Remove config-template
                Org.remove_config_template({
                    'config-template': template['name'],
                    'name': org['name'],
                })
                org_info = Org.info({'name': org['name']})
                self.assertNotIn(
                    u'{0} ({1})'. format(template['name'], template['type']),
                    org_info['templates'],
                    "Failed to remove template by name"
                )

        # create and remove templates by id
        template = make_template({'content': gen_string('alpha')})
        # Add config-template
        Org.add_config_template({
            'config-template-id': template['id'],
            'id': org['id'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            org_info['templates'],
            "Failed to add template by name"
        )
        # Remove config-template
        Org.remove_config_template({
            'config-template-id': template['id'],
            'id': org['id'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertNotIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            org_info['templates'],
            "Failed to remove template by id"
        )

    @tier2
    def test_positive_add_and_remove_domains(self):
        """Add and remove domains to organization

        :id: 97359ffe-4ce6-4e44-9e3f-583d3fdebbc8

        :expectedresults: Domains are handled correctly

        :bz: 1395229

        :steps:
            1. Add and remove domain by name
            2. Add and remove domain by id

        :CaseLevel: Integration
        """
        org = make_org()
        domain_a = make_domain()
        domain_b = make_domain()
        Org.add_domain({
            'domain-id': domain_a['id'],
            'name': org['name'],
        })
        Org.add_domain({
            'domain': domain_b['name'],
            'name': org['name'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertEqual(len(org_info['domains']), 2,
                         "Failed to add domains")
        self.assertIn(domain_a['name'], org_info['domains'])
        self.assertIn(domain_b['name'], org_info['domains'])
        Org.remove_domain({
            'domain': domain_a['name'],
            'name': org['name'],
        })
        Org.remove_domain({
            'domain-id': domain_b['id'],
            'id': org['id'],
        })
        org_info = Org.info({'id': org['id']})
        self.assertEqual(len(org_info['domains']), 0,
                         "Failed to remove domains")

    @tier2
    @upgrade
    def test_positive_add_and_remove_lce(self):
        """Remove a lifecycle environment from organization

        :id: bfa9198e-6078-4f10-b79a-3d7f51b835fd

        :expectedresults: Lifecycle environment is handled as expected

        :steps:
            1. create and add lce to org
            2. remove lce from org

        :CaseLevel: Integration
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
        # We should get a zero-length response when searching for the LC env.
        response = LifecycleEnvironment.list(lc_env_attrs)
        self.assertEqual(len(response), 0)

    @run_only_on('sat')
    @run_in_one_thread
    @tier2
    def test_positive_add_capsule_by_name(self):
        """Add a capsule to organization by its name

        :id: dbf9dd74-3b9e-4124-9468-b0eb978897df

        :expectedresults: Capsule is added to the org

        :CaseLevel: Integration
        """
        org = make_org()
        proxy = self._make_proxy()
        self.addCleanup(org_cleanup, org['id'])

        Org.add_smart_proxy({
            'name': org['name'],
            'smart-proxy': proxy['name'],
        })
        org = Org.info({'name': org['name']})
        self.assertIn(proxy['name'], org['smart-proxies'])

    @run_only_on('sat')
    @run_in_one_thread
    @tier2
    def test_positive_add_capsule_by_id(self):
        """Add a capsule to organization by its ID

        :id: 0a64ebbe-d357-4ca8-b19e-86ea0963dc71

        :expectedresults: Capsule is added to the org

        :CaseLevel: Integration
        """
        org = make_org()
        proxy = self._make_proxy()
        self.addCleanup(org_cleanup, org['id'])

        Org.add_smart_proxy({
            'name': org['name'],
            'smart-proxy-id': proxy['id'],
        })
        org = Org.info({'name': org['name']})
        self.assertIn(proxy['name'], org['smart-proxies'])

    @run_only_on('sat')
    @run_in_one_thread
    @tier2
    @upgrade
    def test_positive_remove_capsule_by_id(self):
        """Remove a capsule from organization by its id

        :id: 71af64ec-5cbb-4dd8-ba90-652e302305ec

        :expectedresults: Capsule is removed from the org

        :CaseLevel: Integration
        """
        org = make_org()
        proxy = self._make_proxy()
        self.addCleanup(org_cleanup, org['id'])

        Org.add_smart_proxy({
            'id': org['id'],
            'smart-proxy-id': proxy['id'],
        })
        Org.remove_smart_proxy({
            'id': org['id'],
            'smart-proxy-id': proxy['id'],
        })
        org = Org.info({'id': org['id']})
        self.assertNotIn(proxy['name'], org['smart-proxies'])

    @run_only_on('sat')
    @run_in_one_thread
    @tier2
    def test_positive_remove_capsule_by_name(self):
        """Remove a capsule from organization by its name

        :id: f56eaf46-fef5-4b52-819f-e30e61f0ec4a

        :expectedresults: Capsule is removed from the org

        :CaseLevel: Integration
        """
        org = make_org()
        proxy = self._make_proxy()
        self.addCleanup(org_cleanup, org['id'])

        Org.add_smart_proxy({
            'name': org['name'],
            'smart-proxy': proxy['name'],
        })
        Org.remove_smart_proxy({
            'name': org['name'],
            'smart-proxy': proxy['name'],
        })
        org = Org.info({'name': org['name']})
        self.assertNotIn(proxy['name'], org['smart-proxies'])

    @run_only_on('sat')
    @tier2
    def test_positive_add_location_by_id(self):
        """Add a location to organization by its id

        :id: 83848f18-2cca-457c-af57-e6249386c81c

        :expectedresults: Location is added to the org

        :CaseLevel: Integration
        """
        org = make_org()
        loc = make_location()
        Org.add_location({
            'location-id': loc['id'],
            'name': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['locations']), 1)
        self.assertIn(loc['name'], org['locations'])

    @run_only_on('sat')
    @tier2
    def test_positive_add_location_by_name(self):
        """Add a location to organization by its name

        :id: f39522e8-5280-429e-b954-79153c2c73c2

        :expectedresults: Location is added to the org

        :CaseLevel: Integration
        """
        org = make_org()
        loc = make_location()
        Org.add_location({
            'location': loc['name'],
            'name': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['locations']), 1)
        self.assertIn(loc['name'], org['locations'])

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1395229)
    @skip_if_bug_open('bugzilla', 1473387)
    @tier2
    @upgrade
    def test_positive_remove_location_by_id(self):
        """Remove a location from organization by its id

        :id: 37b63e5c-8fd5-439c-9540-972b597b590a

        :expectedresults: Location is removed from the org

        :BZ: 1395229, 1473387

        :CaseLevel: Integration
        """
        org = make_org()
        loc = make_location()
        Org.add_location({
            'location-id': loc['id'],
            'name': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['locations']), 1)
        self.assertIn(loc['name'], org['locations'])
        Org.remove_location({
            'location-id': loc['id'],
            'id': org['id'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['locations']), 0)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1395229)
    @skip_if_bug_open('bugzilla', 1473387)
    @tier2
    def test_positive_remove_location_by_name(self):
        """Remove a location from organization by its name

        :id: 35770afa-1623-448c-af4f-a702851063db

        :expectedresults: Location is removed from the org

        :BZ: 1395229, 1473387

        :CaseLevel: Integration
        """
        org = make_org()
        loc = make_location()
        Org.add_location({
            'location': loc['name'],
            'name': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['locations']), 1)
        self.assertIn(loc['name'], org['locations'])
        Org.remove_location({
            'location': loc['name'],
            'id': org['id'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['locations']), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_add_parameter_by_org_name(self):
        """Add a parameter to organization

        :id: b0b59650-5718-45e2-8724-151dc52b1486

        :expectedresults: Parameter is added to the org

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        org = make_org()
        Org.set_parameter({
            'name': param_name,
            'value': param_value,
            'organization': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['parameters']), 1)
        self.assertEqual(param_value, org['parameters'][param_name.lower()])

    @run_only_on('sat')
    @tier1
    def test_positive_add_parameter_by_org_id(self):
        """Add a parameter to organization

        :id: bb76f67e-5329-4777-b563-3fe4ebffc9ce

        :expectedresults: Parameter is added to the org

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        org = make_org()
        Org.set_parameter({
            'name': param_name,
            'value': param_value,
            'organization-id': org['id'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['parameters']), 1)
        self.assertEqual(param_value, org['parameters'][param_name.lower()])

    @run_only_on('sat')
    @tier1
    def test_positive_update_parameter(self):
        """Update a parameter associated with organization

        :id: 4a7ed165-a0c5-4ba6-833a-5a1b3ee47ace

        :expectedresults: Parameter is updated

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        param_new_value = gen_string('alpha')
        org = make_org()
        # Create parameter
        Org.set_parameter({
            'name': param_name,
            'value': gen_string('alpha'),
            'organization': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['parameters']), 1)
        Org.set_parameter({
            'name': param_name,
            'value': param_new_value,
            'organization': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['parameters']), 1)
        self.assertEqual(
            param_new_value, org['parameters'][param_name.lower()])

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_remove_parameter_by_org_name(self):
        """Remove a parameter from organization

        :id: e4099279-4e73-4c14-9e7c-912b3787b99f

        :expectedresults: Parameter is removed from the org

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        org = make_org()
        Org.set_parameter({
            'name': param_name,
            'value': gen_string('alpha'),
            'organization': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['parameters']), 1)
        Org.delete_parameter({
            'name': param_name,
            'organization': org['name'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['parameters']), 0)
        self.assertNotIn(param_name.lower(), org['parameters'])

    @run_only_on('sat')
    @tier1
    def test_positive_remove_parameter_by_org_id(self):
        """Remove a parameter from organization

        :id: 9b0e7c5c-32cd-4428-8798-3469599c9b05

        :expectedresults: Parameter is removed from the org

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        org = make_org()
        Org.set_parameter({
            'name': param_name,
            'value': gen_string('alpha'),
            'organization-id': org['id'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['parameters']), 1)
        Org.delete_parameter({
            'name': param_name,
            'organization-id': org['id'],
        })
        org = Org.info({'id': org['id']})
        self.assertEqual(len(org['parameters']), 0)
        self.assertNotIn(param_name.lower(), org['parameters'])

    # Negative Create

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create an organization with invalid name, but valid label and
        description

        :id: f0aecf1e-d093-4365-af85-b3650ed21318

        :expectedresults: organization is not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    Org.create({
                        'description': gen_string('alpha'),
                        'label': gen_string('alpha'),
                        'name': name,
                    })

    @tier1
    def test_negative_create_same_name(self):
        """Create organization with valid values, then create a new one with
        same values

        :id: 07924e1f-1eff-4bae-b0db-e41b84966bc1

        :expectedresults: organization is not created

        :CaseImportance: Critical
        """
        for desc, name, label in zip(
                valid_data_list(),
                valid_org_names_list(),
                cycle(valid_labels_list()),
        ):
            with self.subTest(desc + name + label):
                Org.create({
                    'description': desc,
                    'label': label,
                    'name': name,
                })
                with self.assertRaises(CLIReturnCodeError):
                    Org.create({
                        'description': desc,
                        'label': label,
                        'name': name,
                    })

    # Positive Delete

    @tier1
    @run_in_one_thread
    @upgrade
    def test_positive_delete_by_id(self):
        """Delete an organization by ID

        :id: b1f5d246-2b12-4302-9824-00d3561f8699

        :expectedresults: organization is deleted

        :CaseImportance: Critical
        """
        org = make_org()
        Org.delete({'id': org['id']})
        # Can we find the object?
        with self.assertRaises(CLIReturnCodeError):
            Org.info({'id': org['id']})

    @tier1
    def test_positive_delete_by_label(self):
        """Delete an organization by label

        :id: 5624f318-ce10-4eaa-815b-0d6ec1e6b438

        :expectedresults: organization is deleted

        :CaseImportance: Critical
        """
        for label in valid_labels_list():
            with self.subTest(label):
                org = make_org({'label': label})
                Org.delete({'label': org['label']})
                # Can we find the object?
                with self.assertRaises(CLIReturnCodeError):
                    Org.info({'id': org['id']})

    @tier1
    def test_positive_delete_by_name(self):
        """Delete an organization by name

        :id: c2787b85-fa87-4aaf-bee4-4695249dd5d8

        :expectedresults: organization is deleted

        :CaseImportance: Critical
        """
        for name in valid_org_names_list():
            with self.subTest(name):
                org = make_org({'name': name})
                Org.delete({'name': org['name']})
                # Can we find the object?
                with self.assertRaises(CLIReturnCodeError):
                    Org.info({'id': org['id']})

    @tier1
    def test_positive_update_name(self):
        """Create organization with valid values then update its name

        :id: 66581003-f5d9-443c-8cd6-00f68087e8e9

        :expectedresults: organization name is updated

        :CaseImportance: Critical
        """
        for new_name in valid_org_names_list():
            with self.subTest(new_name):
                org = make_org()
                # Update the org name
                Org.update({
                    'id': org['id'],
                    'new-name': new_name,
                })
                # Fetch the org again
                org = Org.info({'id': org['id']})
                self.assertEqual(org['name'], new_name)

    @tier1
    def test_positive_update_description(self):
        """Create organization with valid values then update its description

        :id: c5cb0d68-10dd-48ee-8d56-83be8b33d729

        :expectedresults: organization description is updated

        :CaseImportance: Critical
        """
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                org = make_org()
                # Update the org name
                Org.update({
                    'description': new_desc,
                    'id': org['id'],
                })
                # Fetch the org again
                org = Org.info({'id': org['id']})
                self.assertEqual(org['description'], new_desc)

    @tier1
    def test_positive_update_name_description(self):
        """Create organization with valid values then update its name and
        description

        :id: 42635526-fb10-4811-8fe7-1d4c218a056e

        :expectedresults: organization name and description are updated

        :CaseImportance: Critical
        """
        for new_name, new_desc in zip(
                valid_org_names_list(), valid_data_list()):
            with self.subTest(new_name + new_desc):
                org = make_org()
                # Update the org name
                Org.update({
                    'description': new_desc,
                    'id': org['id'],
                    'new-name': new_name,
                })
                # Fetch the org again
                org = Org.info({'id': org['id']})
                self.assertEqual(org['description'], new_desc)
                self.assertEqual(org['name'], new_name)

    # Negative Update

    @tier1
    def test_negative_update_name(self):
        """Create organization then fail to update its name

        :id: 582d41b8-370d-45ed-9b7b-8096608e1324

        :expectedresults: organization name is not updated

        :CaseImportance: Critical
        """
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                org = make_org()
                # Update the org name
                with self.assertRaises(CLIReturnCodeError):
                    Org.update({
                        'id': org['id'],
                        'new-name': new_name,
                    })

    # This test also covers the redmine bug 4443
    @tier1
    def test_positive_search_by_name(self):
        """Can search for an organization by name

        :id: 4279972b-180d-40ce-944f-47a1940af25d

        :expectedresults: organization is created and can be searched by name

        :CaseImportance: Critical
        """
        for name in valid_org_names_list():
            with self.subTest(name):
                org = make_org({'name': name})
                # Can we find the new object?
                result = Org.exists(search=('name', org['name']))
                self.assertEqual(org['name'], result['name'])

    @tier1
    def test_positive_search_by_label(self):
        """Can search for an organization by name

        :id: 0e5a23fa-86d2-4114-be39-0e6228c76f19

        :expectedresults: organization is created and can be searched by label

        :CaseImportance: Critical
        """
        for name in valid_org_names_list():
            with self.subTest(name):
                org = make_org({'name': name})
                # Can we find the new object?
                result = Org.exists(search=('label', org['label']))
                self.assertEqual(org['name'], result['name'])

    @tier1
    def test_positive_info_by_label(self):
        """Get org information by its label

        :id: 02328b67-5d24-4873-b716-113eee3ff67b

        :expectedresults: Organization is created and info can be obtained by
            its label graciously

        :CaseImportance: Critical
        """
        org = make_org()
        result = Org.info({'label': org['label']})
        self.assertEqual(org['id'], result['id'])

    @tier1
    def test_positive_info_by_name(self):
        """Get org information by its name

        :id: cf971026-26a4-428f-b560-bb14e5324207

        :expectedresults: Organization is created and info can be obtained by
            its name graciously

        :CaseImportance: Critical
        """
        org = make_org()
        result = Org.info({'name': org['name']})
        self.assertEqual(org['id'], result['id'])

    @tier1
    def test_positive_multibyte_latin1_org_names(self):
        """Hammer Multibyte and Latin-1 Org names break list pagination

        :id: 4fa0afe7-6d0a-4c3e-a0fc-4ecb95c50fc9

        :BZ: 1418412

        :expectedresults: Multibyte and latin1 names need to be
            displayed with consistent spacing
        """
        org_names = [
            gen_string('alpha', random.randint(1, 30)),
            gen_string('latin1', random.randint(1, 30)),
            u'大傻瓜-{0}'.format(gen_string('alpha', 5)),
            u'你好你-{0}'.format(gen_string('alpha', 5)),
            u'jalapeño-{0}'.format(gen_string('alpha', 5)),
            u'организация-{0}'.format(gen_string('alpha', 5)),
        ]
        for org in org_names:
            make_org({'name': org})
        org_list_lines = [
            line.strip() for line in Org.list(output_format='table') if line]
        self.assertGreaterEqual(len(org_list_lines), len(org_names))
        org_names_lines = [
            line
            for line in org_list_lines
            if any(name in line for name in org_names)
        ]
        self.assertEqual(len(org_names_lines), len(org_names))
        for org_str in org_names_lines:
            width = sum(
                1 if unicodedata.east_asian_width(char)
                in ["Na", "N", "A", "H"]
                else 2 for char in org_str
            )
            self.assertEqual(len(org_names_lines[0]), width)
