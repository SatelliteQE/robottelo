# -*- encoding: utf-8 -*-
"""Test class for Organization CLI

:Requirement: Organization

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: OrganizationsLocations

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.cleanup import capsule_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_compute_resource
from robottelo.cli.factory import make_domain
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_proxy
from robottelo.cli.factory import make_subnet
from robottelo.cli.factory import make_template
from robottelo.cli.factory import make_user
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.org import Org
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_org_names_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
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

    @classmethod
    def setUpClass(cls):
        """Create an organization."""
        super(OrganizationTestCase, cls).setUpClass()
        cls.org = make_org()

    @tier2
    def test_verify_bugzilla_1078866(self):
        """hammer organization <info,list> --help types information
        doubled

        :id: 7938bcc4-7107-40b0-bb88-6288ebec0dcd

        :BZ: 1078866, 1647323

        :expectedresults: no duplicated lines in usage message

        :CaseImportance: Low
        """
        # org list --help:
        result = Org.list({'help': True}, output_format=None)
        # get list of lines and check they all are unique
        lines = [line for line in result if line != '' and '----' not in line]
        self.assertEqual(len(set(lines)), len(lines))

        # org info --help:info returns more lines (obviously), ignore exception
        result = Org.info({'help': True}, output_format=None)

        # get list of lines and check they all are unique
        lines = [line for line in result['options']]
        self.assertEqual(len(set(lines)), len(lines))

    @tier1
    def test_positive_CRD(self):
        """Create organization with valid name, label and description

        :id: 35840da7-668e-4f78-990a-738aa688d586

        :expectedresults: organization is created with attributes

        :CaseImportance: Critical

        create read
        """
        # Create
        name = valid_org_names_list()[0]
        label = valid_labels_list()[0]
        desc = valid_data_list()[0]
        org = make_org({'name': name, 'label': label, 'description': desc})
        self.assertEqual(org['name'], name)
        self.assertEqual(org['label'], label)
        self.assertEqual(org['description'], desc)

        # List
        result = Org.list({'search': 'name=%s' % org['name']})
        self.assertTrue(len(result), 1)
        self.assertEqual(result[0]['name'], org['name'])

        # Search scoped
        for query in [
            'label = {}'.format(label),
            'description ~ {}'.format(desc[:-5]),
            'name ^ "{}"'.format(org['name']),
        ]:
            result = Org.list({'search': query})
            self.assertTrue(len(result), 1)
            self.assertEqual(result[0]['name'], org['name'])

        # Search by name and label
        result = Org.exists(search=('name', org['name']))
        self.assertEqual(org['name'], result['name'])
        result = Org.exists(search=('label', org['label']))
        self.assertEqual(org['name'], result['name'])

        # Info by name and label
        result = Org.info({'label': org['label']})
        self.assertEqual(org['id'], result['id'])
        result = Org.info({'name': org['name']})
        self.assertEqual(org['id'], result['id'])

        # Delete
        Org.delete({'id': org['id']})
        with self.assertRaises(CLIReturnCodeError):
            Org.info({'id': org['id']})

    @tier2
    def test_positive_create_with_system_admin_user(self):
        """Create organization using user with system admin role

        :id: 1482ab6e-18c7-4a62-81a2-cc969ac373fe

        :expectedresults: organization is created

        :BZ: 1644586
        """
        login = gen_string('alpha')
        password = gen_string('alpha')
        org_name = gen_string('alpha')
        make_user({'login': login, 'password': password})
        User.add_role({'login': login, 'role': 'System admin'})
        Org.with_user(username=login, password=password).create({'name': org_name})
        result = Org.info({'name': org_name})
        self.assertEqual(result['name'], org_name)

    @tier2
    @upgrade
    def test_positive_add_and_remove_subnets(self):
        """add and remove a subnet from organization

        :id: adb5310b-76c5-4aca-8220-fdf0fe605cb0

        :BZ:
            1. Add and remove subnet by name
            2. Add and remove subnet by id

        :expectedresults: Subnets are handled as expected

        :BZ: 1395229

        :CaseLevel: Integration
        """
        subnet_a = make_subnet()
        subnet_b = make_subnet()
        Org.add_subnet({'name': self.org['name'], 'subnet': subnet_a['name']})
        Org.add_subnet({'name': self.org['name'], 'subnet-id': subnet_b['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['subnets']), 2, "Failed to add subnets")
        Org.remove_subnet({'name': self.org['name'], 'subnet': subnet_a['name']})
        Org.remove_subnet({'name': self.org['name'], 'subnet-id': subnet_b['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['subnets']), 0, "Failed to remove subnets")

    @tier2
    def test_positive_add_and_remove_users(self):
        """Add and remove (admin) user to organization

        :id: c35b2e88-a65f-4eea-ba55-89cef59f30be

        :expectedresults: Users are added and removed from the org

        :steps:
            1. create and delete user by name
            2. create and delete user by id
            3. create and delete admin user by name
            4. create and delete admin user by id

        :BZ: 1395229

        :CaseLevel: Integration
        """
        user = make_user()
        admin_user = make_user({'admin': '1'})
        self.assertEqual(admin_user['admin'], 'yes')

        # add and remove user and admin user by name
        Org.add_user({'name': self.org['name'], 'user': user['login']})
        Org.add_user({'name': self.org['name'], 'user': admin_user['login']})
        org_info = Org.info({'name': self.org['name']})
        self.assertIn(user['login'], org_info['users'], "Failed to add user by name")
        self.assertIn(admin_user['login'], org_info['users'], "Failed to add admin user by name")

        Org.remove_user({'name': self.org['name'], 'user': user['login']})
        Org.remove_user({'name': self.org['name'], 'user': admin_user['login']})
        org_info = Org.info({'name': self.org['name']})
        self.assertNotIn(user['login'], org_info['users'], "Failed to remove user by name")
        self.assertNotIn(
            admin_user['login'], org_info['users'], "Failed to remove admin user by name"
        )

        # add and remove user and admin user by id
        Org.add_user({'id': self.org['id'], 'user-id': user['id']})
        Org.add_user({'id': self.org['id'], 'user-id': admin_user['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertIn(user['login'], org_info['users'], "Failed to add user by id")
        self.assertIn(admin_user['login'], org_info['users'], "Failed to add admin user by id")

        Org.remove_user({'id': self.org['id'], 'user-id': user['id']})
        Org.remove_user({'id': self.org['id'], 'user-id': admin_user['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertNotIn(user['login'], org_info['users'], "Failed to remove user by id")
        self.assertNotIn(
            admin_user['login'], org_info['users'], "Failed to remove admin user by id"
        )

    @tier2
    def test_positive_add_and_remove_hostgroups(self):
        """add and remove a hostgroup from an organization

        :id: 34e2c7c8-dc20-4709-a5a9-83c0dee9d84d

        :expectedresults: Hostgroups are handled as expected

        :BZ: 1395229

        :steps:
            1. add and remove hostgroup by name
            2. add and remove hostgroup by id

        :CaseLevel: Integration
        """
        hostgroup_a = make_hostgroup()
        hostgroup_b = make_hostgroup()
        Org.add_hostgroup({'hostgroup-id': hostgroup_a['id'], 'id': self.org['id']})
        Org.add_hostgroup({'hostgroup': hostgroup_b['name'], 'name': self.org['name']})
        org_info = Org.info({'name': self.org['name']})
        self.assertIn(hostgroup_a['name'], org_info['hostgroups'], "Failed to add hostgroup by id")
        self.assertIn(
            hostgroup_b['name'], org_info['hostgroups'], "Failed to add hostgroup by name"
        )
        Org.remove_hostgroup({'hostgroup-id': hostgroup_b['id'], 'id': self.org['id']})
        Org.remove_hostgroup({'hostgroup': hostgroup_a['name'], 'name': self.org['name']})
        org_info = Org.info({'id': self.org['id']})
        self.assertNotIn(
            hostgroup_a['name'], org_info['hostgroups'], "Failed to remove hostgroup by name"
        )
        self.assertNotIn(
            hostgroup_b['name'], org_info['hostgroups'], "Failed to remove hostgroup by id"
        )

    @skip_if_not_set('compute_resources')
    @tier2
    @upgrade
    def test_positive_add_and_remove_compresources(self):
        """Add and remove a compute resource from organization

        :id: 415c14ab-f879-4ed8-9ba7-8af4ada2e277

        :expectedresults: Compute resource are handled as expected

        :BZ: 1395229

        :steps:
            1. Add and remove compute resource by id
            2. Add and remove compute resource by name

        :CaseLevel: Integration
        """
        compute_res_a = make_compute_resource(
            {
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'url': 'qemu+ssh://root@{0}/system'.format(
                    settings.compute_resources.libvirt_hostname
                ),
            }
        )
        compute_res_b = make_compute_resource(
            {
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'url': 'qemu+ssh://root@{0}/system'.format(
                    settings.compute_resources.libvirt_hostname
                ),
            }
        )
        Org.add_compute_resource(
            {'compute-resource-id': compute_res_a['id'], 'id': self.org['id']}
        )
        Org.add_compute_resource(
            {'compute-resource': compute_res_b['name'], 'name': self.org['name']}
        )
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['compute-resources']), 2, "Failed to add compute resources")
        Org.remove_compute_resource(
            {'compute-resource-id': compute_res_a['id'], 'id': self.org['id']}
        )
        Org.remove_compute_resource(
            {'compute-resource': compute_res_b['name'], 'name': self.org['name']}
        )
        org_info = Org.info({'id': self.org['id']})
        self.assertNotIn(
            compute_res_a['name'], org_info['compute-resources'], "Failed to remove cr by id"
        )
        self.assertNotIn(
            compute_res_b['name'], org_info['compute-resources'], "Failed to remove cr by name"
        )

    @tier2
    def test_positive_add_and_remove_media(self):
        """Add and remove medium to organization

        :id: c2943a81-c8f7-44c4-926b-388055d7c290

        :expectedresults: Media are handled as expected

        :BZ: 1395229

        :steps:
            1. add and remove medium by id
            2. add and remove medium by name

        :CaseLevel: Integration
        """
        medium_a = make_medium()
        medium_b = make_medium()
        Org.add_medium({'id': self.org['id'], 'medium-id': medium_a['id']})
        Org.add_medium({'name': self.org['name'], 'medium': medium_b['name']})
        org_info = Org.info({'id': self.org['id']})
        self.assertIn(
            medium_a['name'], org_info['installation-media'], "Failed to add medium by id"
        )
        self.assertIn(
            medium_b['name'], org_info['installation-media'], "Failed to add medium by name"
        )
        Org.remove_medium({'name': self.org['name'], 'medium': medium_a['name']})
        Org.remove_medium({'id': self.org['id'], 'medium-id': medium_b['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertNotIn(
            medium_a['name'], org_info['installation-media'], "Failed to remove medium by name"
        )
        self.assertNotIn(
            medium_b['name'], org_info['installation-media'], "Failed to remove medium by id"
        )

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
        # create and remove templates by name
        name = valid_data_list()[0]

        template = make_template({'content': gen_string('alpha'), 'name': name})
        # Add config-template
        Org.add_config_template({'name': self.org['name'], 'config-template': template['name']})
        org_info = Org.info({'name': self.org['name']})
        self.assertIn(
            '{0} ({1})'.format(template['name'], template['type']),
            org_info['templates'],
            "Failed to add template by name",
        )
        # Remove config-template
        Org.remove_config_template({'config-template': template['name'], 'name': self.org['name']})
        org_info = Org.info({'name': self.org['name']})
        self.assertNotIn(
            '{0} ({1})'.format(template['name'], template['type']),
            org_info['templates'],
            "Failed to remove template by name",
        )

        # add and remove templates by id
        # Add config-template
        Org.add_config_template({'config-template-id': template['id'], 'id': self.org['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertIn(
            '{0} ({1})'.format(template['name'], template['type']),
            org_info['templates'],
            "Failed to add template by name",
        )
        # Remove config-template
        Org.remove_config_template({'config-template-id': template['id'], 'id': self.org['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertNotIn(
            '{0} ({1})'.format(template['name'], template['type']),
            org_info['templates'],
            "Failed to remove template by id",
        )

    @tier2
    def test_positive_add_and_remove_domains(self):
        """Add and remove domains to organization

        :id: 97359ffe-4ce6-4e44-9e3f-583d3fdebbc8

        :expectedresults: Domains are handled correctly

        :BZ: 1395229

        :steps:
            1. Add and remove domain by name
            2. Add and remove domain by id

        :CaseLevel: Integration
        """
        domain_a = make_domain()
        domain_b = make_domain()
        Org.add_domain({'domain-id': domain_a['id'], 'name': self.org['name']})
        Org.add_domain({'domain': domain_b['name'], 'name': self.org['name']})
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['domains']), 2, "Failed to add domains")
        self.assertIn(domain_a['name'], org_info['domains'])
        self.assertIn(domain_b['name'], org_info['domains'])
        Org.remove_domain({'domain': domain_a['name'], 'name': self.org['name']})
        Org.remove_domain({'domain-id': domain_b['id'], 'id': self.org['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['domains']), 0, "Failed to remove domains")

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
        org_id = self.org['id']
        lc_env_name = make_lifecycle_environment({'organization-id': org_id})['name']
        lc_env_attrs = {'name': lc_env_name, 'organization-id': org_id}
        # Read back information about the lifecycle environment. Verify the
        # sanity of that information.
        response = LifecycleEnvironment.list(lc_env_attrs)
        self.assertEqual(response[0]['name'], lc_env_name)
        # Delete it.
        LifecycleEnvironment.delete(lc_env_attrs)
        # We should get a zero-length response when searching for the LC env.
        response = LifecycleEnvironment.list(lc_env_attrs)
        self.assertEqual(len(response), 0)

    @run_in_one_thread
    @tier2
    @upgrade
    def test_positive_add_and_remove_capsules(self):
        """Add and remove a capsule from organization

        :id: 71af64ec-5cbb-4dd8-ba90-652e302305ec

        :expectedresults: Capsules are handled correctly

        :steps:
            1. add and remove capsule by ip
            2. add and remove capsule by name

        :CaseLevel: Integration
        """
        proxy = self._make_proxy()
        Org.add_smart_proxy({'id': self.org['id'], 'smart-proxy-id': proxy['id']})
        org_info = Org.info({'name': self.org['name']})
        self.assertIn(proxy['name'], org_info['smart-proxies'], "Failed to add capsule by id")
        Org.remove_smart_proxy({'id': self.org['id'], 'smart-proxy-id': proxy['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertNotIn(
            proxy['name'], org_info['smart-proxies'], "Failed to remove capsule by id"
        )
        Org.add_smart_proxy({'name': self.org['name'], 'smart-proxy': proxy['name']})
        org_info = Org.info({'name': self.org['name']})
        self.assertIn(proxy['name'], org_info['smart-proxies'], "Failed to add capsule by name")
        Org.remove_smart_proxy({'name': self.org['name'], 'smart-proxy': proxy['name']})
        org_info = Org.info({'name': self.org['name']})
        self.assertNotIn(proxy['name'], org_info['smart-proxies'], "Failed to add capsule by name")

    @tier2
    @upgrade
    def test_positive_add_and_remove_locations(self):
        """Add and remove a locations from organization

        :id: 37b63e5c-8fd5-439c-9540-972b597b590a

        :expectedresults: Locations are handled

        :BZ: 1395229, 1473387

        :steps:
            1. add and remove locations by name
            2. add and remove locations by id

        :CaseLevel: Integration
        """
        loc_a = make_location()
        loc_b = make_location()
        Org.add_location({'location-id': loc_a['id'], 'name': self.org['name']})
        Org.add_location({'location': loc_b['name'], 'name': self.org['name']})
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['locations']), 2, "Failed to add locations")
        self.assertIn(loc_a['name'], org_info['locations'])
        self.assertIn(loc_b['name'], org_info['locations'])
        Org.remove_location({'location-id': loc_a['id'], 'id': self.org['id']})
        Org.remove_location({'location': loc_b['name'], 'id': self.org['id']})
        org_info = Org.info({'id': self.org['id']})
        self.assertNotIn('locations', org_info, "Failed to remove locations")

    @tier1
    @upgrade
    def test_positive_add_and_remove_parameter(self):
        """Remove a parameter from organization

        :id: e4099279-4e73-4c14-9e7c-912b3787b99f

        :expectedresults: Parameter is removed from the org

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        param_new_value = gen_string('alpha')

        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['parameters']), 0)

        # Create parameter
        Org.set_parameter(
            {'name': param_name, 'value': gen_string('alpha'), 'organization-id': self.org['id']}
        )
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['parameters']), 1)

        # Update
        Org.set_parameter(
            {'name': param_name, 'value': param_new_value, 'organization': self.org['name']}
        )
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['parameters']), 1)
        self.assertEqual(param_new_value, org_info['parameters'][param_name.lower()])

        # Delete parameter
        Org.delete_parameter({'name': param_name, 'organization': self.org['name']})
        org_info = Org.info({'id': self.org['id']})
        self.assertEqual(len(org_info['parameters']), 0)
        self.assertNotIn(param_name.lower(), org_info['parameters'])

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create an organization with invalid name, but valid label and
        description

        :id: f0aecf1e-d093-4365-af85-b3650ed21318

        :expectedresults: organization is not created

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    Org.create(
                        {
                            'description': gen_string('alpha'),
                            'label': gen_string('alpha'),
                            'name': name,
                        }
                    )

    @tier1
    def test_negative_create_same_name(self):
        """Create organization with valid values, then create a new one with
        same values

        :id: 07924e1f-1eff-4bae-b0db-e41b84966bc1

        :expectedresults: organization is not created

        :CaseImportance: Critical
        """
        name = valid_org_names_list()[0]
        desc = valid_data_list()[0]
        label = valid_labels_list()[0]

        Org.create({'description': desc, 'label': label, 'name': name})
        with self.assertRaises(CLIReturnCodeError):
            Org.create({'description': desc, 'label': label, 'name': name})

    @tier1
    def test_positive_update(self):
        """Create organization and update its name and description

        :id: 66581003-f5d9-443c-8cd6-00f68087e8e9

        :expectedresults: organization name is updated

        :CaseImportance: Critical
        """
        new_name = valid_org_names_list()[0]
        new_desc = valid_data_list()[0]
        org = make_org()

        # upgrade name
        Org.update({'id': org['id'], 'new-name': new_name})
        org = Org.info({'id': org['id']})
        self.assertEqual(org['name'], new_name)

        # upgrade description
        Org.update({'description': new_desc, 'id': org['id']})
        org = Org.info({'id': org['id']})
        self.assertEqual(org['description'], new_desc)

    @tier1
    def test_negative_update_name(self):
        """Create organization then fail to update its name

        :id: 582d41b8-370d-45ed-9b7b-8096608e1324

        :expectedresults: organization name is not updated

        """
        org = make_org()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    Org.update({'id': org['id'], 'new-name': new_name})
