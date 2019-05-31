# -*- encoding: utf-8 -*-
"""Test class for Location CLI

:Requirement: Location

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from random import randint
from robottelo.cleanup import capsule_cleanup, location_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_compute_resource,
    make_domain,
    make_environment,
    make_hostgroup,
    make_location,
    make_medium,
    make_proxy,
    make_subnet,
    make_template,
    make_user,
)
from robottelo.cli.location import Location
from robottelo.datafactory import filtered_datapoint, invalid_values_list
from robottelo.decorators import (
    skip_if_bug_open,
    run_in_one_thread,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import CLITestCase


@filtered_datapoint
def valid_loc_data_list():
    """List of valid data for input testing.

    Note: The maximum allowed length of location name is 246 only.  This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)

    """
    return [
        gen_string('alphanumeric', randint(1, 246)),
        gen_string('alpha', randint(1, 246)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 246)),
        gen_string('numeric', randint(1, 246)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', randint(1, 85)),
    ]


class LocationTestCase(CLITestCase):
    """Tests for Location via Hammer CLI"""
    # TODO Add coverage for realms as soon as they're supported

    def _make_proxy(self, options=None):
        """Create a Proxy and register the cleanup function"""
        proxy = make_proxy(options=options)
        # Add capsule to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])
        return proxy

    @tier1
    def test_positive_create_with_name(self):
        """Try to create location using different value types as a name

        :id: 76a90b92-296c-4b5a-9c81-183ff71937e2

        :expectedresults: Location is created successfully and has proper name


        :CaseImportance: Critical
        """
        for name in valid_loc_data_list():
            with self.subTest(name):
                loc = make_location({'name': name})
                self.assertEqual(loc['name'], name)

    @skip_if_bug_open('bugzilla', 1233612)
    @tier1
    def test_positive_create_with_description(self):
        """Create new location with custom description

        :id: e1844d9d-ec4a-44b3-9743-e932cc70020d

        :expectedresults: Location created successfully and has expected and
            correct description

        :CaseImportance: Critical
        """
        description = gen_string('utf8')
        loc = make_location({'description': description})
        self.assertEqual(loc['description'], description)

    @tier1
    def test_positive_create_with_user_by_id(self):
        """Create new location with assigned user to it. Use user id as
        a parameter

        :id: 96dd25bf-8535-41a5-ba63-60a2b52487b8

        :expectedresults: Location created successfully and has correct user
            assigned to it with expected login name

        :CaseImportance: Critical
        """
        user = make_user()
        loc = make_location({'user-ids': user['id']})
        self.assertEqual(loc['users'][0], user['login'])

    @tier1
    @upgrade
    def test_positive_create_with_user_by_name(self):
        """Create new location with assigned user to it. Use user login
        as a parameter

        :id: ed65dfd2-00b6-4ec9-9da0-1956d8a5cf5d

        :expectedresults: Location created successfully and has correct user
            assigned to it with expected login name

        :CaseImportance: Critical
        """
        user = make_user()
        loc = make_location({'users': user['login']})
        self.assertEqual(loc['users'][0], user['login'])

    @tier1
    @upgrade
    def test_positive_create_with_compresource_by_id(self):
        """Create new location with compute resource assigned to it. Use
        compute resource id as a parameter

        :id: 49c72f7d-08b7-4dd3-af7f-5b97889a4583

        :expectedresults: Location created successfully and has correct compute
            resource assigned to it

        :CaseImportance: Critical
        """
        comp_resource = make_compute_resource()
        loc = make_location({'compute-resource-ids': comp_resource['id']})
        self.assertEqual(loc['compute-resources'][0], comp_resource['name'])

    @tier1
    def test_positive_create_with_compresource_by_name(self):
        """Create new location with compute resource assigned to it. Use
        compute resource name as a parameter

        :id: a849c847-bc18-4d87-a47b-43975090f509

        :expectedresults: Location created successfully and has correct compute
            resource assigned to it

        :CaseImportance: Critical
        """
        comp_resource = make_compute_resource()
        loc = make_location({'compute-resources': comp_resource['name']})
        self.assertEqual(loc['compute-resources'][0], comp_resource['name'])

    @tier1
    @upgrade
    def test_positive_create_with_template_by_id(self):
        """Create new location with config template assigned to it. Use
        config template id as a parameter

        :id: 1ae669e3-479a-427a-ac97-0878667c3dce

        :expectedresults: Location created successfully and list of config
            templates assigned to that location should contain expected one

        :CaseImportance: Critical
        """
        template = make_template()
        loc = make_location({'config-template-ids': template['id']})
        self.assertGreaterEqual(len(loc['templates']), 1)
        self.assertIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            loc['templates']
        )

    @tier1
    def test_positive_create_with_template_by_name(self):
        """Create new location with config template assigned to it. Use
        config template name as a parameter

        :id: a523bf4e-dc90-4f15-ae79-5246d0568fa5

        :expectedresults: Location created successfully and list of config
            templates assigned to that location should contain expected one

        :CaseImportance: Critical
        """
        template = make_template()
        loc = make_location({'config-templates': template['name']})
        self.assertGreaterEqual(len(loc['templates']), 1)
        self.assertIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            loc['templates']
        )

    @tier1
    @upgrade
    def test_positive_create_with_domain_by_id(self):
        """Create new location with assigned domain to it. Use domain id
        as a parameter

        :id: 54507b72-93ea-471e-bfd5-857c44b6abed

        :expectedresults: Location created successfully and has correct and
            expected domain assigned to it

        :CaseImportance: Critical
        """
        domain = make_domain()
        loc = make_location({'domain-ids': domain['id']})
        self.assertEqual(loc['domains'][0], domain['name'])

    @tier1
    def test_positive_create_with_domain_by_name(self):
        """Create new location with assigned domain to it. Use domain
        name as a parameter

        :id: 06426c06-744d-44cf-bbba-449ef1f62659

        :expectedresults: Location created successfully and has correct and
            expected domain assigned to it

        :CaseImportance: Critical
        """
        domain = make_domain()
        loc = make_location({'domains': domain['name']})
        self.assertEqual(loc['domains'][0], domain['name'])

    @tier1
    def test_positive_create_with_subnet_by_id(self):
        """Create new location with assigned subnet to it. Use subnet id
        as a parameter

        :id: cef956bd-7c78-49f8-917a-f344fadf217a

        :expectedresults: Location created successfully and has correct subnet
            with expected network address assigned to it

        :CaseImportance: Critical
        """
        subnet = make_subnet()
        loc = make_location({'subnet-ids': subnet['id']})
        self.assertIn(subnet['name'], loc['subnets'][0])
        self.assertIn(subnet['network-addr'], loc['subnets'][0])

    @tier1
    @upgrade
    def test_positive_create_with_subnet_by_name(self):
        """Create new location with assigned subnet to it. Use subnet
        name as a parameter

        :id: efe2fce4-ecd9-4765-8d77-dff776a1ba13

        :expectedresults: Location created successfully and has correct subnet
            with expected network address assigned to it

        :CaseImportance: Critical
        """
        subnet = make_subnet()
        loc = make_location({'subnets': subnet['name']})
        self.assertIn(subnet['name'], loc['subnets'][0])
        self.assertIn(subnet['network-addr'], loc['subnets'][0])

    @tier1
    def test_positive_create_with_environment_by_id(self):
        """Create new location with assigned environment to it. Use
        environment id as a parameter

        :id: cd38b895-57f7-4d07-aa4b-7299a69ec203

        :expectedresults: Location created successfully and has correct and
            expected environment assigned to it

        :CaseImportance: Critical
        """
        env = make_environment()
        loc = make_location({'environment-ids': env['id']})
        self.assertEqual(loc['environments'][0], env['name'])

    @tier1
    @upgrade
    def test_positive_create_with_environment_by_name(self):
        """Create new location with assigned environment to it. Use
        environment name as a parameter

        :id: 3c9a47b5-798b-4f41-a9dc-219ad43b6fdf

        :expectedresults: Location created successfully and has correct and
            expected environment assigned to it

        :CaseImportance: Critical
        """
        env = make_environment()
        loc = make_location({'environments': env['name']})
        self.assertEqual(loc['environments'][0], env['name'])

    @tier1
    def test_positive_create_with_hostgroup_by_id(self):
        """Create new location with assigned host group to it. Use host
        group id as a parameter

        :id: d4421f79-72ea-4d68-8ae7-aedd2b32dfe9

        :expectedresults: Location created successfully and has correct and
            expected host group assigned to it

        :CaseImportance: Critical
        """
        host_group = make_hostgroup()
        loc = make_location({'hostgroup-ids': host_group['id']})
        self.assertEqual(loc['hostgroups'][0], host_group['name'])

    @tier1
    @upgrade
    def test_positive_create_with_hostgroup_by_name(self):
        """Create new location with assigned host group to it. Use host
        group name as a parameter

        :id: 7b465d98-efcc-4c49-b45b-b51c26d5010d

        :expectedresults: Location created successfully and has correct and
            expected host group assigned to it

        :CaseImportance: Critical
        """
        host_group = make_hostgroup()
        loc = make_location({'hostgroups': host_group['name']})
        self.assertEqual(loc['hostgroups'][0], host_group['name'])

    @skip_if_bug_open('bugzilla', 1234287)
    @tier1
    @upgrade
    def test_positive_create_with_medium(self):
        """Create new location with assigned media to it.

        :id: 72d71056-6bf7-4af0-95d4-828709e1efba

        :expectedresults: Location created successfully and has correct and
            expected media assigned to it

        :CaseImportance: Critical
        """
        medium = make_medium()
        loc = make_location({'medium-ids': medium['id']})
        self.assertGreater(len(loc['installation-media']), 0)
        self.assertEqual(loc['installation-media'][0], medium['name'])

    @tier1
    def test_positive_create_with_parent(self):
        """Create new location with parent location specified

        :id: 49b34733-103a-4fee-818b-6a3386253af1

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location created successfully and has correct and
            expected parent location set

        :CaseImportance: High
        """
        parent_loc = make_location()
        loc = make_location({'parent-id': parent_loc['id']})
        self.assertEqual(loc['parent'], parent_loc['name'])

    @tier1
    @upgrade
    def test_positive_create_with_environments_by_id(self):
        """Basically, verifying that location with multiple entities
        assigned to it by id can be created in the system. Environments were
        chosen for that purpose.

        :id: eac6bfe2-1ead-4784-b9a8-d21b1f10d8d2

        :expectedresults: Location created successfully and has correct
            environments assigned to it

        :CaseImportance: Critical
        """
        envs_amount = randint(3, 5)
        envs = [make_environment() for _ in range(envs_amount)]
        loc = make_location({'environment-ids': [env['id'] for env in envs]})
        self.assertEqual(len(loc['environments']), envs_amount)
        for env in envs:
            self.assertIn(env['name'], loc['environments'])

    @tier1
    @upgrade
    def test_positive_create_with_domains_by_name(self):
        """Basically, verifying that location with multiple entities
        assigned to it by name can be created in the system. Domains were
        chosen for that purpose.

        :id: 71e581ef-0950-4cc7-8671-6fddfd06e378

        :expectedresults: Location created successfully and has correct domains
            assigned to it

        :CaseImportance: Critical
        """
        domains_amount = randint(3, 5)
        domains = [make_domain() for _ in range(domains_amount)]
        loc = make_location({
            'domains': [domain['name'] for domain in domains],
        })
        self.assertEqual(len(loc['domains']), domains_amount)
        for domain in domains:
            self.assertIn(domain['name'], loc['domains'])

    @tier1
    def test_negative_create_with_name(self):
        """Try to create location using invalid names only

        :id: 2dfe8ff0-e84a-42c0-a480-0f8345ee66d0

        :expectedresults: Location is not created


        :CaseImportance: Critical
        """
        for invalid_name in invalid_values_list():
            with self.subTest(invalid_name):
                with self.assertRaises(CLIFactoryError):
                    make_location({'name': invalid_name})

    @tier1
    def test_negative_create_with_same_name(self):
        """Try to create location using same name twice

        :id: 4fbaea41-9775-40a2-85a5-4dc05cc95134

        :expectedresults: Second location is not created


        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        loc = make_location({'name': name})
        self.assertEqual(loc['name'], name)
        with self.assertRaises(CLIFactoryError):
            make_location({'name': name})

    @tier1
    def test_negative_create_with_compresource_by_id(self):
        """Try to create new location with incorrect compute resource
        assigned to it. Use compute resource id as a parameter

        :id: 83115ace-9340-44cd-9e47-5585b267d7ed

        :expectedresults: Location is not created


        :CaseImportance: Critical
        """
        with self.assertRaises(CLIFactoryError):
            make_location({'compute-resource-ids': gen_string('numeric', 6)})

    @tier1
    def test_negative_create_with_user_by_name(self):
        """Try to create new location with incorrect user assigned to it
        Use user login as a parameter

        :id: fa892edf-8c42-44dc-8f36-bed50798b59b

        :expectedresults: Location is not created


        :CaseImportance: Critical
        """
        with self.assertRaises(CLIFactoryError):
            make_location({'users': gen_string('utf8', 80)})

    @tier1
    def test_positive_update_with_name(self):
        """Try to update location using different value types as a name

        :id: 09fa55a5-c688-4bd3-94df-8ab7a2ccda84

        :expectedresults: Location is updated successfully and has proper and
            expected name

        :CaseImportance: Critical
        """
        loc = make_location()
        for new_name in valid_loc_data_list():
            with self.subTest(new_name):
                Location.update({
                    'id': loc['id'],
                    'new-name': new_name,
                })
                loc = Location.info({'id': loc['id']})
                self.assertEqual(loc['name'], new_name)

    @tier1
    def test_positive_update_with_user_by_id(self):
        """Create new location with assigned user to it. Try to update
        that location and change assigned user on another one. Use user id as a
        parameter

        :id: 123a8a28-f81d-439a-82d0-5c3d814d1a25

        :expectedresults: Location is updated successfully and has correct user
            assigned to it

        :CaseImportance: Critical
        """
        user = [make_user() for _ in range(2)]
        loc = make_location({'user-ids': user[0]['id']})
        self.assertEqual(loc['users'][0], user[0]['login'])
        Location.update({
            'id': loc['id'],
            'user-ids': user[1]['id'],
        })
        loc = Location.info({'id': loc['id']})
        self.assertEqual(loc['users'][0], user[1]['login'])

    @tier1
    def test_positive_update_with_subnet_by_name(self):
        """Create new location with assigned subnet to it. Try to update
        that location and change assigned subnet on another one. Use subnet
        name as a parameter

        :id: 2bb2ec4a-2423-46a8-8772-a263823640df

        :expectedresults: Location is updated successfully and has correct
            subnet with expected network address assigned to it

        :CaseImportance: Critical
        """
        subnet = [make_subnet() for _ in range(2)]
        loc = make_location({'subnets': subnet[0]['name']})
        self.assertIn(subnet[0]['name'], loc['subnets'][0])
        self.assertIn(subnet[0]['network-addr'], loc['subnets'][0])
        Location.update({
            'id': loc['id'],
            'subnets': subnet[1]['name'],
        })
        loc = Location.info({'id': loc['id']})
        self.assertIn(subnet[1]['name'], loc['subnets'][0])
        self.assertIn(subnet[1]['network-addr'], loc['subnets'][0])

    @tier1
    def test_positive_update_from_compresources_to_compresource(self):
        """Create location with multiple (not less than three) compute
        resources assigned to it. Try to update location and overwrite all
        compute resources with a new single compute resource. Use compute
        resource id as a parameter

        :id: 3a547413-53dc-4305-84e9-8db7a6bed3b2

        :expectedresults: Location updated successfully and has correct compute
            resource assigned to it

        :CaseImportance: Critical
        """
        resources_amount = randint(3, 5)
        resources = [make_compute_resource() for _ in range(resources_amount)]
        loc = make_location({
            'compute-resource-ids': [resource['id'] for resource in resources],
        })
        self.assertEqual(len(loc['compute-resources']), resources_amount)
        for resource in resources:
            self.assertIn(resource['name'], loc['compute-resources'])

        new_resource = make_compute_resource()
        Location.update({
            'compute-resource-ids': new_resource['id'],
            'id': loc['id'],
        })

        loc = Location.info({'id': loc['id']})
        self.assertEqual(len(loc['compute-resources']), 1)
        self.assertEqual(loc['compute-resources'][0], new_resource['name'])

    @tier1
    def test_positive_update_from_hostgroups_to_hostgroups(self):
        """Create location with multiple (three) host groups assigned to
        it. Try to update location and overwrite all host groups by new
        multiple (two) host groups. Use host groups name as a parameter

        :id: e53504d0-8328-485c-bc8c-36ea9a2ad3e1

        :expectedresults: Location updated successfully and has correct and
            expected host groups assigned to it

        :CaseImportance: Critical
        """
        host_groups = [make_hostgroup() for _ in range(3)]
        loc = make_location({
            'hostgroups': [hg['name'] for hg in host_groups],
        })
        self.assertEqual(len(loc['hostgroups']), 3)
        for host_group in host_groups:
            self.assertIn(host_group['name'], loc['hostgroups'])
        new_host_groups = [make_hostgroup() for _ in range(2)]
        Location.update({
            'hostgroups': [hg['name'] for hg in new_host_groups],
            'id': loc['id'],
        })
        loc = Location.info({'id': loc['id']})
        self.assertEqual(len(loc['hostgroups']), 2)
        for host_group in new_host_groups:
            self.assertIn(host_group['name'], loc['hostgroups'])

    @tier1
    def test_negative_update_with_name(self):
        """Try to update location using invalid names only

        :id: a41abf03-61ca-4201-8a80-7062a6196851

        :expectedresults: Location is not updated


        :CaseImportance: Critical
        """
        for invalid_name in invalid_values_list():
            with self.subTest(invalid_name):
                loc = make_location()
                with self.assertRaises(CLIReturnCodeError):
                    Location.update({
                        'id': loc['id'],
                        'new-name': invalid_name,
                    })

    @tier1
    def test_negative_update_with_domain_by_id(self):
        """Try to update existing location with incorrect domain. Use
        domain id as a parameter

        :id: ec49ea4d-754a-4958-8180-f61eb6d8cede

        :expectedresults: Location is not updated


        :CaseImportance: Critical
        """
        loc = make_location()
        with self.assertRaises(CLIReturnCodeError):
            Location.update({
                'domain-ids': gen_string('numeric', 6),
                'id': loc['id'],
            })

    @tier1
    def test_negative_update_with_template_by_name(self):
        """Try to update existing location with incorrect config
        template. Use template name as a parameter

        :id: 937730ff-bb46-437b-bfc7-915045d1782c

        :expectedresults: Location is not updated


        :CaseImportance: Critical
        """
        loc = make_location()
        with self.assertRaises(CLIReturnCodeError):
            Location.update({
                'config-templates': gen_string('utf8', 80),
                'id': loc['id'],
            })

    @skip_if_bug_open('bugzilla', 1398695)
    @run_in_one_thread
    @tier2
    def test_positive_add_capsule_by_name(self):
        """Add a capsule to location by its name

        :id: 32b1e969-a1a8-4d65-bde9-a825ab542b1d

        :expectedresults: Capsule is added to the org

        :CaseLevel: Integration
        """
        loc = make_location()
        proxy = self._make_proxy()
        self.addCleanup(location_cleanup, loc['id'])

        Location.add_smart_proxy({
            'name': loc['name'],
            'smart-proxy': proxy['name'],
        })
        loc = Location.info({'name': loc['name']})
        self.assertIn(proxy['name'], loc['smart-proxies'])

    @run_in_one_thread
    @tier2
    @skip_if_bug_open('bugzilla', 1398695)
    def test_positive_add_capsule_by_id(self):
        """Add a capsule to location by its ID

        :id: 15e3c1e6-4fa3-4965-8808-a9ba01d1c050

        :expectedresults: Capsule is added to the org

        :CaseLevel: Integration
        """
        loc = make_location()
        proxy = self._make_proxy()
        self.addCleanup(location_cleanup, loc['id'])

        Location.add_smart_proxy({
            'name': loc['name'],
            'smart-proxy-id': proxy['id'],
        })
        loc = Location.info({'name': loc['name']})
        self.assertIn(proxy['name'], loc['smart-proxies'])

    @run_in_one_thread
    @tier2
    @skip_if_bug_open('bugzilla', 1398695)
    def test_positive_remove_capsule_by_id(self):
        """Remove a capsule from organization by its id

        :id: 98681f4f-a5e2-44f6-8879-d23ad90b4c59

        :expectedresults: Capsule is removed from the org

        :CaseLevel: Integration
        """
        loc = make_location()
        proxy = self._make_proxy()
        self.addCleanup(location_cleanup, loc['id'])

        Location.add_smart_proxy({
            'id': loc['id'],
            'smart-proxy-id': proxy['id'],
        })
        Location.remove_smart_proxy({
            'id': loc['id'],
            'smart-proxy-id': proxy['id'],
        })
        loc = Location.info({'id': loc['id']})
        self.assertNotIn(proxy['name'], loc['smart-proxies'])

    @run_in_one_thread
    @tier2
    @skip_if_bug_open('bugzilla', 1398695)
    def test_positive_remove_capsule_by_name(self):
        """Remove a capsule from organization by its name

        :id: 91dcafbe-5f52-48af-b5c7-9319b2929f5a

        :expectedresults: Capsule is removed from the org

        :CaseLevel: Integration
        """
        loc = make_location()
        proxy = self._make_proxy()
        self.addCleanup(location_cleanup, loc['id'])

        Location.add_smart_proxy({
            'name': loc['name'],
            'smart-proxy': proxy['name'],
        })
        Location.remove_smart_proxy({
            'name': loc['name'],
            'smart-proxy': proxy['name'],
        })
        loc = Location.info({'name': loc['name']})
        self.assertNotIn(proxy['name'], loc['smart-proxies'])

    @tier1
    @upgrade
    def test_positive_delete_by_name(self):
        """Try to delete location using name of that location as a
        parameter. Use different value types for testing.

        :id: b44e56e4-00f0-4b7c-bef6-48b10c7b2b59

        :expectedresults: Location is deleted successfully


        :CaseImportance: Critical
        """
        for name in valid_loc_data_list():
            with self.subTest(name):
                loc = make_location({'name': name})
                self.assertEqual(loc['name'], name)
                Location.delete({'name': loc['name']})
                with self.assertRaises(CLIReturnCodeError):
                    Location.info({'id': loc['id']})

    @tier1
    def test_positive_delete_by_id(self):
        """Try to delete location using id of that location as a
        parameter

        :id: 71e394e3-85e6-456d-b03d-6787db9059aa

        :expectedresults: Location is deleted successfully


        :CaseImportance: Critical
        """
        loc = make_location()
        Location.delete({'id': loc['id']})
        with self.assertRaises(CLIReturnCodeError):
            Location.info({'id': loc['id']})

    @tier1
    def test_positive_add_parameter_by_loc_name(self):
        """Add a parameter to location

        :id: d4c2f27d-7c16-4296-9da6-2e7135bfb6ad

        :expectedresults: Parameter is added to the location

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        location = make_location()
        Location.set_parameter({
            'name': param_name,
            'value': param_value,
            'location': location['name'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 1)
        self.assertEqual(
            param_value, location['parameters'][param_name.lower()])

    @tier1
    def test_positive_add_parameter_by_loc_id(self):
        """Add a parameter to location

        :id: 61b564f2-a42a-48de-833d-bec3a127d0f5

        :expectedresults: Parameter is added to the location

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        location = make_location()
        Location.set_parameter({
            'name': param_name,
            'value': param_value,
            'location-id': location['id'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 1)
        self.assertEqual(
            param_value, location['parameters'][param_name.lower()])

    @tier1
    def test_positive_update_parameter(self):
        """Update a parameter associated with location

        :id: 7b61fa71-0203-4709-9abd-9bb51ce6c19f

        :expectedresults: Parameter is updated

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        param_new_value = gen_string('alpha')
        location = make_location()
        # Create parameter
        Location.set_parameter({
            'name': param_name,
            'value': gen_string('alpha'),
            'location': location['name'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 1)
        Location.set_parameter({
            'name': param_name,
            'value': param_new_value,
            'location': location['name'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 1)
        self.assertEqual(
            param_new_value, location['parameters'][param_name.lower()])

    @tier1
    def test_positive_update_parent(self):
        """Update location's parent location

        :id: 34522d1a-1190-48d8-9285-fc9a9bcf6c6a

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location was updated successfully

        :CaseImportance: High
        """
        parent_loc = make_location()
        loc = make_location({'parent-id': parent_loc['id']})
        new_parent_loc = make_location()
        Location.update({
            'id': loc['id'],
            'parent-id': new_parent_loc['id'],
        })
        loc = Location.info({'id': loc['id']})
        self.assertEqual(loc['parent'], new_parent_loc['name'])

    @tier1
    def test_negative_update_parent_with_child(self):
        """Attempt to set child location as a parent

        :id: fd4cb1cf-377f-4b48-b7f4-d4f6ca56f544

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location was not updated

        :CaseImportance: High
        """
        parent_loc = make_location()
        loc = make_location({'parent-id': parent_loc['id']})
        with self.assertRaises(CLIReturnCodeError):
            Location.update({
                'id': parent_loc['id'],
                'parent-id': loc['id'],
            })
        parent_loc = Location.info({'id': parent_loc['id']})
        self.assertIsNone(parent_loc.get('parent'))

    @tier1
    def test_negative_update_parent_with_self(self):
        """Attempt to set a location as its own parent

        :id: 26e07124-9043-4597-8513-7147135a8426

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location was not updated

        :CaseImportance: High
        """
        parent_loc = make_location()
        loc = make_location({'parent-id': parent_loc['id']})
        with self.assertRaises(CLIReturnCodeError):
            Location.update({
                'id': loc['id'],
                'parent-id': loc['id'],
            })
        loc = Location.info({'id': loc['id']})
        self.assertEqual(loc['parent'], parent_loc['name'])

    @tier1
    @upgrade
    def test_positive_remove_parameter_by_loc_name(self):
        """Remove a parameter from location

        :id: 97fda466-1894-431e-bc76-3b1c7643522f

        :expectedresults: Parameter is removed from the location

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        location = make_location()
        Location.set_parameter({
            'name': param_name,
            'value': gen_string('alpha'),
            'location': location['name'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 1)
        Location.delete_parameter({
            'name': param_name,
            'location': location['name'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 0)
        self.assertNotIn(param_name.lower(), location['parameters'])

    @tier1
    def test_positive_remove_parameter_by_loc_id(self):
        """Remove a parameter from location

        :id: 13836073-3e39-4d3e-b4b4-e87619c28bae

        :expectedresults: Parameter is removed from the location

        :CaseImportance: Critical
        """
        param_name = gen_string('alpha')
        location = make_location()
        Location.set_parameter({
            'name': param_name,
            'value': gen_string('alpha'),
            'location-id': location['id'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 1)
        Location.delete_parameter({
            'name': param_name,
            'location-id': location['id'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 0)
        self.assertNotIn(param_name.lower(), location['parameters'])
